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
    - System Access Type: {user_preferences['system_type']}
    - Interaction Types: {user_preferences['interaction_types']}
    - User Types: {user_preferences['user_types']}
    - Conservativeness Level: {user_preferences['conservativeness']}
    - Primary Concerns: {user_preferences['primary_concerns']}
    - Expected Request Volume: {user_preferences['request_volume']}
    - Expected Risk Level: {user_preferences['jailbreak_proportion']}
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
    borderline_prompts = pd.read_csv(data_dir / 'borderline_non-adversarial.csv')
    return borderline_prompts.sample(n=3)

def recommendation_ui():
    st.title("Safeguard Recommendation System")
    
    st.markdown("""
    Welcome to the BELLS Safeguard Recommendation System! 🛡️

    This tool will help you find the most suitable safeguard(s) based on your specific needs and constraints.
    Please answer the following questions about your system and requirements to receive personalized recommendations.
    """)
    
    st.markdown("---")
    
    # System Configuration with better explanation
    st.subheader("System Configuration")
    col1, col2 = st.columns(2)
    with col1:
        system_type = st.radio(
            "What type of system access do you have?",
            ["Black Box API", "Direct Access"],
            help="""Choose your system access type:
            - Black Box API: You only have API access (e.g., OpenAI API, Claude API)
            - Direct Access: You have access to the model weights or deployment infrastructure"""
        )
    with col2:
        rag_enabled = st.radio(
            "Will you use Retrieval Augmented Generation (RAG)?",
            ["Yes", "No"],
            help="Select whether your system will use RAG to enhance responses with external knowledge"
        )
    
    # Use Case Questions instead of RAG
    st.subheader("Use Case Assessment")
    
    interaction_types = st.multiselect(
        "What types of interactions will your system handle?",
        ["General chat/conversation", "Content generation", "Code generation", 
         "Data analysis", "Expert advice", "Customer service"],
        help="Select all types of interactions that apply to your use case"
    )
    
    user_types = st.multiselect(
        "What types of users will interact with your system?",
        ["General public", "Authenticated users only", "Internal employees", 
         "Technical users", "Students/Educational"],
        help="Select all user types that will have access to your system"
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
        "Conservativeness Level",
        1, 5, 3,
        help="""Based on the examples above:
        - Level 1: Minimal filtering (high risk tolerance)
        - Level 3: Balanced approach
        - Level 5: Maximum security (very conservative)"""
    )
    
    primary_concerns = st.multiselect(
        "Primary Security Concerns",
        ["Regulatory Compliance", "IP Protection", "Content Safety", 
         "Misinformation Prevention", "Privacy Protection"],
        help="Select your main security priorities"
    )
    
    # Operational Requirements with detailed explanations
    st.subheader("Operational Requirements")
    
    st.markdown("""
    These parameters help us recommend safeguards that match your operational needs.
    """)

    st.warning("""Note that this is a mock-up demonstration using an LLM to generate recommendations based on your inputs and 
               simulated evaluation results. In a production system, the recommendations would be based on real-world performance data and 
               more sophisticated matching algorithms.""")
    
    request_volume = st.select_slider(
        "Expected Request Volume",
        options=["Low (<1k/day)", "Medium (1k-10k/day)", "High (>10k/day)"],
        help="""Affects performance and scaling requirements:
        - Low: Suitable for basic API implementations
        - Medium: May require optimization
        - High: Needs enterprise-grade solutions"""
    )
    
    risk_level = st.select_slider(
        "Expected Risk Level",
        options=["Very Low (<1%)", "Low (1-5%)", "Medium (5-15%)", "High (>15%)"],
        help="""Likelihood of receiving adversarial/jailbreak attempts:
        - Very Low: General purpose, low-risk applications
        - Medium: Public-facing applications
        - High: Applications likely to face adversarial attempts"""
    )
    
    fpr_tolerance = st.select_slider(
        "False Positive Tolerance",
        options=["Very Low", "Low", "Medium", "High"],
        help="""How much over-filtering can your application accept:
        - Very Low: Critical applications where blocking valid content is costly
        - Medium: Balance between security and usability
        - High: Security is priority over occasional false positives"""
    )
    
    # Generate Recommendation with loading indicator
    if st.button("Get Recommendation"):
        with st.spinner('Analyzing your requirements and generating recommendations...'):
            user_preferences = {
                "system_type": system_type,
                "interaction_types": interaction_types,
                "user_types": user_types,
                "conservativeness": conservativeness,
                "primary_concerns": primary_concerns,
                "request_volume": request_volume,
                "jailbreak_proportion": risk_level,
                "fpr_tolerance": fpr_tolerance
            }
            
            evaluation_data = load_evaluation_data()
            recommendation = generate_recommendation(user_preferences, evaluation_data)
            
            st.markdown("### Recommendation")
            st.markdown(recommendation)

if __name__ == "__main__":
    recommendation_ui() 