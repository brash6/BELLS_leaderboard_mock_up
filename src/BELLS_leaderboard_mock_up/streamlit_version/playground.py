import streamlit as st
import pandas as pd
import random
import os
from pathlib import Path

@st.cache_data
def load_data():
    """Cache the data loading"""
    data_dir = Path(__file__).parent.parent.parent.parent / 'data'
    non_adversarial = pd.read_csv(data_dir / 'non_adversarial_prompts.csv')
    adversarial = pd.read_csv(data_dir / 'adversarial_prompts.csv')
    return non_adversarial, adversarial

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
    
    📋 **Legend:**
    - ✅ Content detected/blocked by safeguard
    - ❌ Content allowed by safeguard
    
    Use the filters below to customize your exploration! 🔍
    """)
    
    st.markdown("---")
    
    # Load data
    non_adversarial_df, adversarial_df = load_data()
    
    # Create columns for filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        harm_level = st.radio(
            "Harm Level",
            ["harmful", "borderline", "benign"],
            horizontal=True
        )
    
    with col2:
        content_type = st.radio(
            "Content Type",
            ["Non-Adversarial", "Adversarial"],
            horizontal=True,
            help="Non-Adversarial: Direct prompts | Adversarial: Jailbreak attempts"
        )
    
    # Add warning for adversarial content
    if content_type == "Adversarial":
        st.warning("""
            ⚠️ **Note**: These are examples of adversarial prompts that attempt to bypass safeguards.
            They are shown for educational and research purposes only.
        """)
    
    # Safeguard selection
    with col3:
        safeguards = ["All Safeguards", "lakera_guard", "prompt_guard", "langkit", "nemo", "llm_guard"]
        safeguard = st.selectbox(
            "Select Safeguard",
            safeguards,
            format_func=lambda x: x.replace("_", " ").title() if x != "All Safeguards" else x
        )
    
    # Get current dataset based on selection
    current_df = adversarial_df if content_type == "Adversarial" else non_adversarial_df
    current_df = current_df[current_df['harm_level'] == harm_level.lower()]
    
    # Category filter
    with col4:
        categories = ['All'] + sorted(current_df['category'].unique().tolist())
        selected_category = st.selectbox("Category Filter", categories)
        
        if selected_category != 'All':
            current_df = current_df[current_df['category'] == selected_category]
    
    # Add search functionality
    search_query = st.text_input(
        "🔍 Search prompts...", 
        placeholder="e.g., 'hack' or 'scam'",
        help="Search through questions and prompts"
    )
    
    # Filter based on search
    if search_query:
        if content_type == "Adversarial":
            mask = (current_df['question'].str.contains(search_query, case=False, na=False) |
                   current_df['jailbreak_prompt'].str.contains(search_query, case=False, na=False))
        else:
            mask = current_df['question'].str.contains(search_query, case=False, na=False)
        current_df = current_df[mask]
    
    st.markdown("---")
    
    # Display statistics
    total_count = len(current_df)
    
    if safeguard == "All Safeguards":
        cols = st.columns(len(safeguards[1:]) + 1)
        cols[0].metric("Total Prompts", total_count)
        for i, sg in enumerate(safeguards[1:], 1):
            detected = current_df[sg].sum()
            cols[i].metric(
                label=sg.replace("_", " ").title(),
                value=f"{(detected/total_count*100):.1f}%",
                help=f"{detected}/{total_count}"
            )
    else:
        col1, col2, col3 = st.columns(3)
        detected = current_df[safeguard].sum()
        col1.metric("Total Prompts", total_count)
        col2.metric("Detected", detected)
        col3.metric("Detection Rate", f"{(detected/total_count*100):.1f}%")
    
    st.markdown("---")
    
    # Display prompts
    for _, row in current_df.iterrows():
        cols = st.columns([3, 1])
        with cols[0]:
            st.markdown(f"### {row['question']}")
        
        # Display detection results
        with cols[1]:
            if safeguard == "All Safeguards":
                for sg in safeguards[1:]:
                    if row[sg]:
                        st.success(f"✅ {sg.replace('_', ' ').title()}")
                    else:
                        st.error(f"❌ {sg.replace('_', ' ').title()}")
            else:
                if row[safeguard]:
                    st.success(f"✅ {safeguard.replace('_', ' ').title()}")
                else:
                    st.error(f"❌ {safeguard.replace('_', ' ').title()}")
        
        # Display jailbreak prompt for adversarial content
        if content_type == "Adversarial":
            st.markdown("**Jailbreak Attempt:**")
            with st.expander("Show jailbreak prompt"):
                st.markdown(f"_{row['jailbreak_prompt']}_")
                st.markdown(f"**Type:** `{row['jailbreak_type']}`")
                st.markdown(f"**Source:** `{row['jailbreak_source']}`")
        
        # Display metadata
        st.markdown(f"**Category:** `{row['category']}`")
        st.markdown(f"**Source:** `{row['source']}`")
        
        st.markdown("---")

if __name__ == "__main__":
    playground_ui() 