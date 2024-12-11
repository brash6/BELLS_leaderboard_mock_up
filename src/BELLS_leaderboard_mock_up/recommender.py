import streamlit as st
import pandas as pd
from openai import OpenAI
import os
from pathlib import Path
from dotenv import load_dotenv
from BELLS_leaderboard_mock_up.config import load_config


# Load environment variables from .env file
load_dotenv()

def load_evaluation_data():
    data_dir = Path(__file__).parent.parent.parent / 'data'
    return pd.read_csv(data_dir / 'safeguard_evaluation_results.csv')

def generate_recommendation(user_preferences, evaluation_data):
    # Load config to get API key
    config = load_config()
    client = OpenAI(api_key=config['openai_api_key'])
    
    # Convert evaluation data to a string format
    data_context = evaluation_data.to_string()
    
    prompt = f"""You are an expert advisor for LLM safeguards. Based on the following evaluation data and user preferences, 
    recommend the most suitable safeguard(s).

    EVALUATION DATA:
    {data_context}

    USER PREFERENCES:
    - System Type: {user_preferences['system_type']}
    - RAG Usage: {user_preferences['rag_usage']}
    - Conservativeness Level: {user_preferences['conservativeness']}
    - Primary Concerns: {user_preferences['primary_concerns']}
    - Expected Request Volume: {user_preferences['request_volume']}
    - Expected Jailbreak Proportion: {user_preferences['jailbreak_proportion']}
    - False Positive Tolerance: {user_preferences['fpr_tolerance']}

    Please provide:
    1. Top recommended safeguard(s)
    2. Justification based on the evaluation metrics
    3. Important considerations or limitations
    4. Alternative options if applicable

    Format your response in markdown."""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    
    return response.choices[0].message.content

@st.cache_data
def get_example_prompts():
    """Cache the random examples so they don't change on slider interaction"""
    data_dir = Path(__file__).parent.parent.parent / 'data'
    borderline_prompts = pd.read_csv(data_dir / 'borderline_vanilla.csv')
    return borderline_prompts.sample(n=3)

def recommendation_ui():
    st.title("Safeguard Recommendation System")
    
    st.markdown("""
    Welcome to the BELLS Safeguard Recommendation System! 🛡️

    Choosing the right safeguard for your LLM system can be challenging. This tool will help you find 
    the most suitable safeguard(s) based on your specific needs and constraints.
    
    Simply answer a few questions about your system and requirements, and we'll provide personalized 
    recommendations based on our comprehensive evaluation data.
    
    Let's get started! 🚀
    """)
    
    st.markdown("---")
    
    # System Configuration
    st.subheader("System Configuration")
    system_type = st.radio(
        "System Type",
        ["Black Box", "White Box"],
        help="Black box systems only access inputs/outputs, while white box systems can access model internals"
    )
    
    rag_usage = st.radio(
        "RAG Implementation",
        ["Yes", "No"],
        help="Whether your system uses Retrieval-Augmented Generation"
    )
    
    # Security Preferences with example prompts
    st.subheader("Security Preferences")
    
    # Get fixed examples
    example_prompts = get_example_prompts()
    
    st.markdown("**Conservativeness Level**")
    st.markdown("Would you allow your system to answer these types of borderline questions?")
    
    for idx, prompt in example_prompts.iterrows():
        st.markdown(f"""
        > **Example {idx+1}:** {prompt['Goal']}  
        > *Category: {prompt['Category']}*
        """)
    
    conservativeness = st.slider(
        "Conservativeness Level (1: Allow all, 5: Block all such content)",
        1, 5, 3,
        help="Based on the examples above, how conservative should your system be?"
    )
    
    primary_concerns = st.multiselect(
        "Primary Security Concerns",
        ["Regulatory Compliance", "IP Protection", "Content Safety", 
         "Misinformation Prevention", "Privacy Protection"],
        help="Select your main security priorities"
    )
    
    # Operational Requirements
    st.subheader("Operational Requirements")
    request_volume = st.select_slider(
        "Expected Request Volume",
        options=["Low (<1k/day)", "Medium (1k-10k/day)", "High (>10k/day)"]
    )
    
    jailbreak_proportion = st.select_slider(
        "Expected Jailbreak Proportion",
        options=["Very Low (<1%)", "Low (1-5%)", "Medium (5-15%)", "High (>15%)"]
    )
    
    fpr_tolerance = st.select_slider(
        "False Positive Tolerance",
        options=["Very Low", "Low", "Medium", "High"],
        help="How tolerant is your system to false positives?"
    )
    
    # Generate Recommendation
    if st.button("Get Recommendation"):
        user_preferences = {
            "system_type": system_type,
            "rag_usage": rag_usage,
            "conservativeness": conservativeness,
            "primary_concerns": primary_concerns,
            "request_volume": request_volume,
            "jailbreak_proportion": jailbreak_proportion,
            "fpr_tolerance": fpr_tolerance
        }
        
        evaluation_data = load_evaluation_data()
        recommendation = generate_recommendation(user_preferences, evaluation_data)
        
        st.markdown("### Recommendation")
        st.markdown(recommendation)

if __name__ == "__main__":
    recommendation_ui() 