import streamlit as st
import pandas as pd
import random
import os
from pathlib import Path

@st.cache_data
def get_example_prompts():
    """Cache the random examples so they don't change on slider interaction"""
    data_dir = Path(__file__).parent.parent.parent / 'data'
    borderline_prompts = pd.read_csv(data_dir / 'borderline_non-adversarial.csv')
    return borderline_prompts.sample(n=3)

def playground_ui():
    st.title("Data Playground")
    
    st.markdown("""
    Welcome to the BELLS Data Playground! 🎮

    This interactive environment allows you to explore how different safeguards perform against various types of prompts. 
    You can:
    - Compare different safeguards' detection capabilities
    - Test various prompt categories (Harmful, Borderline, Benign)
    - Explore both direct prompts and adversarial attempts
    - Filter by specific harm categories
    - Search through our comprehensive prompt database
    
    Each prompt shows real-time detection results based on our evaluation data, helping you understand 
    how safeguards perform in different scenarios.
    
    📋 **Legend:**
    - ✅ Content detected/blocked by safeguard
    - ❌ Content allowed by safeguard
    
    Use the filters below to customize your exploration! 🔍
    """)
    
    st.markdown("---")
    
    # Get the data directory path
    data_dir = Path(__file__).parent.parent.parent / 'data'
    
    # Load datasets with correct paths
    harmful_prompts = pd.read_csv(data_dir / 'harmful_non-adversarial.csv')
    borderline_prompts = pd.read_csv(data_dir / 'borderline_non-adversarial.csv') 
    benign_prompts = pd.read_csv(data_dir / 'benign_non-adversarial.csv')
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
            ["Non-Adversarial", "Adversarial"],
            horizontal=True,
            help="Non-Adversarial: Direct prompts | Adversarial: Jailbreak attempts"
        )
        
    # Add warning for adversarial content with dataset links
    if content_type == "Adversarial":
        st.warning("""
            ⚠️ **Note**: The adversarial datasets contain thousands of entries. 
            For readability, only a sample of 40 attempts is shown below.
            
            Complete datasets available on GitHub:
            - [Benign Adversarial Dataset](https://github.com/brash6/BELLS_leaderboard_mock_up/blob/main/data/benign_jailbreaks.csv)
            - [Borderline Adversarial Dataset](https://github.com/brash6/BELLS_leaderboard_mock_up/blob/main/data/borderline_jailbreaks.csv)
            - [Harmful Adversarial Dataset](https://github.com/brash6/BELLS_leaderboard_mock_up/blob/main/data/harmful_jailbreaks.csv)
        """)
    
    # Safeguard selection without arrows
    with col3:
        safeguard = st.selectbox(
            "Select Safeguard",
            ["All Safeguards"] + evaluation_results['safeguard'].tolist(),
            label_visibility="visible"
        )
    
    # Get appropriate dataset based on selection
    datasets = {
        'Harmful': {
            'Non-Adversarial': harmful_prompts, 
            'Adversarial': harmful_jailbreaks.sample(n=40)
        },
        'Borderline': {
            'Non-Adversarial': borderline_prompts, 
            'Adversarial': borderline_jailbreaks.sample(n=40)
        },
        'Benign': {
            'Non-Adversarial': benign_prompts, 
            'Adversarial': benign_jailbreaks.sample(n=40)
        }
    }
    
    current_dataset = datasets[dataset_type][content_type]
    
    # Category filter
    with col4:
        if 'Category' in current_dataset.columns:
            categories = ['All'] + sorted(current_dataset['Category'].unique().tolist())
            selected_category = st.selectbox("Category Filter", categories)
            
            if selected_category != 'All':
                current_dataset = current_dataset[current_dataset['Category'] == selected_category]
    
    # Add search functionality with example
    search_query = st.text_input(
        "🔍 Search prompts...", 
        placeholder="e.g., 'generate code' or 'financial advice'",
        help="Search through prompt goals and descriptions"
    )
    
    # Filter based on search
    if search_query:
        current_dataset = current_dataset[
            current_dataset['Goal'].str.contains(search_query, case=False, na=False)
        ]
    
    # Get detection probability based on dataset type and safeguard
    def get_detection_probability(safeguard_name, dataset_type, content_type):
        if content_type == 'Non-Adversarial':
            column_name = f"{dataset_type.lower()}_non-adversarial"
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
        cols[0].metric(
            label="Total Prompts",
            value=total_count
        )
        for i, (name, count) in enumerate(detected_counts.items(), 1):
            cols[i].metric(
                label=f"{name}",
                value=f"{(count/total_count*100):.1f}%",
                help=f"{count}/{total_count}"
            )
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric(
            label="Total Prompts",
            value=total_count
        )
        col2.metric(
            label="Detected",
            value=detected_count
        )
        col3.metric(
            label="Detection Rate",
            value=f"{(detected_count/total_count*100):.1f}%"
        )
    
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
        
        # Content display
        if content_type == "Non-Adversarial" and 'Behavior' in row:
            st.markdown("**Expected Behavior:**")
            st.markdown(f"_{row['Behavior']}_")
        elif content_type == "Adversarial":  # Changed this condition
            st.markdown("**Jailbreak Attempt:**")
            with st.expander("Show jailbreak prompt"):
                if 'Jailbreak' in row:
                    st.markdown(f"_{row['Jailbreak']}_")
                elif 'Attack' in row:  # Fallback for alternative column name
                    st.markdown(f"_{row['Attack']}_")
        
        # Footer with metadata
        if 'Category' in row:
            st.markdown(f"**Category:** `{row['Category']}`")
        
        st.markdown("---")

if __name__ == "__main__":
    playground_ui() 