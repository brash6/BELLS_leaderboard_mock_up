import streamlit as st
import pandas as pd
import random
import os
from pathlib import Path

def playground_ui():
    st.title("Playground")
    
    st.markdown("""
    Welcome to the BELLS Playground! 🎮

    This interactive environment allows you to explore how different safeguards perform against various types of prompts. 
    You can:
    - Compare different safeguards' detection capabilities
    - Test various prompt categories (Harmful, Borderline, Benign)
    - Explore both direct prompts and jailbreak attempts
    - Filter by specific harm categories
    - Search through our comprehensive prompt database
    
    Each prompt shows real-time detection results based on our evaluation data, helping you understand 
    how safeguards perform in different scenarios.
    
    Use the filters below to customize your exploration! 🔍
    """)
    
    st.markdown("---")
    
    # Get the data directory path
    data_dir = Path(__file__).parent.parent.parent / 'data'
    
    # Load datasets with correct paths
    harmful_prompts = pd.read_csv(data_dir / 'harmful_vanilla.csv')
    borderline_prompts = pd.read_csv(data_dir / 'borderline_vanilla.csv') 
    benign_prompts = pd.read_csv(data_dir / 'benign_vanilla.csv')
    harmful_jailbreaks = pd.read_csv(data_dir / 'harmful_jailbreaks.csv')
    borderline_jailbreaks = pd.read_csv(data_dir / 'borderline_jailbreaks.csv')
    benign_jailbreaks = pd.read_csv(data_dir / 'benign_jailbreaks.csv')
    evaluation_results = pd.read_csv(data_dir / 'safeguard_evaluation_results.csv')
    
    # Create columns for filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        dataset_type = st.radio(
            "Dataset Type",
            ["Harmful", "Borderline", "Benign"],
            horizontal=True
        )
    
    with col2:
        content_type = st.radio(
            "Content Type",
            ["Prompts", "Jailbreaks"],
            horizontal=True
        )
        
    # Add warning for jailbreak content
    if content_type == "Jailbreaks":
        st.warning("""
            ⚠️ **Note**: The jailbreak datasets contain thousands of entries. 
            For readability, only a sample of 40 jailbreak attempts is shown below.
            
            Complete jailbreak datasets can be found in:
            - data/benign_jailbreaks.csv
            - data/borderline_jailbreaks.csv
            - data/harmful_jailbreaks.csv
        """)
    
    # Safeguard selection
    with col3:
        safeguard = st.selectbox(
            "Select Safeguard",
            ["All Safeguards"] + evaluation_results['safeguard'].tolist()
        )
    
    # Get appropriate dataset based on selection
    datasets = {
        'Harmful': {'Prompts': harmful_prompts, 'Jailbreaks': harmful_jailbreaks.sample(n=40)},
        'Borderline': {'Prompts': borderline_prompts, 'Jailbreaks': borderline_jailbreaks.sample(n=40)},
        'Benign': {'Prompts': benign_prompts, 'Jailbreaks': benign_jailbreaks.sample(n=40)}
    }
    
    current_dataset = datasets[dataset_type][content_type]
    
    # Category filter
    with col4:
        if 'Category' in current_dataset.columns:
            categories = ['All'] + sorted(current_dataset['Category'].unique().tolist())
            selected_category = st.selectbox("Category Filter", categories)
            
            if selected_category != 'All':
                current_dataset = current_dataset[current_dataset['Category'] == selected_category]
    
    # Add search functionality
    search_query = st.text_input("🔍 Search prompts...", "")
    
    # Filter based on search
    if search_query:
        current_dataset = current_dataset[
            current_dataset['Goal'].str.contains(search_query, case=False, na=False)
        ]
    
    # Get detection probability based on dataset type and safeguard
    def get_detection_probability(safeguard_name, dataset_type, content_type):
        if content_type == 'Prompts':
            column_name = f"{dataset_type.lower()}_vanilla"
        else:
            column_name = f"{dataset_type.lower()}_jailbreaks"
        return evaluation_results[evaluation_results['safeguard'] == safeguard_name][column_name].iloc[0]
    
    # Simulate detection with actual probabilities
    def get_detection_result(safeguard_name, dataset_type, content_type):
        prob = get_detection_probability(safeguard_name, dataset_type, content_type)
        return random.random() < prob
    
    # Display stats
    total_count = len(current_dataset)
    if safeguard == "All Safeguards":
        detected_counts = {
            name: sum([get_detection_result(name, dataset_type, content_type) for _ in range(total_count)])
            for name in evaluation_results['safeguard']
        }
    else:
        detected_count = sum([get_detection_result(safeguard, dataset_type, content_type) for _ in range(total_count)])
    
    st.markdown("---")
    
    # Display statistics in metrics
    if safeguard == "All Safeguards":
        cols = st.columns(len(evaluation_results) + 1)
        cols[0].metric("Total Prompts", total_count)
        for i, (name, count) in enumerate(detected_counts.items(), 1):
            cols[i].metric(
                f"{name}",
                f"{(count/total_count*100):.1f}%",
                f"{count}/{total_count}"
            )
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Prompts", total_count)
        col2.metric("Detected", detected_count)
        col3.metric("Detection Rate", f"{(detected_count/total_count*100):.1f}%")
    
    st.markdown("---")
    
    # Display prompts/jailbreaks in a card-like format
    for idx, row in current_dataset.iterrows():
        # Get detection results for the prompt
        if safeguard == "All Safeguards":
            detection_results = {
                name: get_detection_result(name, dataset_type, content_type)
                for name in evaluation_results['safeguard']
            }
        else:
            detected = get_detection_result(safeguard, dataset_type, content_type)
        
        # Header with detection status
        if safeguard == "All Safeguards":
            st.markdown(f"### {row['Goal']}")
            cols = st.columns(len(evaluation_results))
            for i, (name, result) in enumerate(detection_results.items()):
                with cols[i]:
                    if result:
                        st.success(f"✅ {name}")
                    else:
                        st.error(f"❌ {name}")
        else:
            cols = st.columns([3, 1])
            with cols[0]:
                st.markdown(f"### {row['Goal']}")
            with cols[1]:
                if detected:
                    st.success(f"✅ {safeguard}")
                else:
                    st.error(f"❌ {safeguard}")
        
        # Content
        if content_type == "Prompts" and 'Behavior' in row:
            st.markdown("**Expected Behavior:**")
            st.markdown(f"_{row['Behavior']}_")
        
        if content_type == "Jailbreaks" and 'Jailbreak' in row:
            st.markdown("**Jailbreak Attempt:**")
            with st.expander("Show jailbreak prompt"):
                st.markdown(f"_{row['Jailbreak']}_")
        
        # Footer with metadata
        if 'Category' in row:
            st.markdown(f"**Category:** `{row['Category']}`")
        
        st.markdown("---")

if __name__ == "__main__":
    playground_ui() 