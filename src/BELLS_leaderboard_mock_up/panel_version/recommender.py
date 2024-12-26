import panel as pn
import pandas as pd
from anthropic import Anthropic
from pathlib import Path
from dotenv import load_dotenv
from BELLS_leaderboard_mock_up.config import load_config

# Enable Panel extensions
pn.extension()

# Load environment variables
load_dotenv()

def load_evaluation_data():
    data_dir = Path(__file__).parent.parent.parent.parent / 'data'
    return pd.read_csv(data_dir / 'safeguard_evaluation_results.csv')

def get_example_prompts():
    """Cache the random examples so they don't change on slider interaction"""
    data_dir = Path(__file__).parent.parent.parent.parent / 'data'
    borderline_prompts = pd.read_csv(data_dir / 'borderline_non-adversarial.csv')
    return borderline_prompts.sample(n=3)

def generate_recommendation(user_preferences, evaluation_data):
    # Load config to get API key
    config = load_config()
    client = Anthropic(api_key=config['anthropic_api_key'])
    
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

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1000,
        system=[
            {
                "type": "text",
                "text": "You are an expert advisor for LLM safeguards. Based on the following evaluation data and user preferences, recommend the most suitable safeguard(s).",
                "cache_control": {"type": "ephemeral"}
            }
        ],
        messages=[{
            "role": "user",
            "content": prompt
        }],
        cache=True
    )
    return response.content[0].text

def recommendation_ui():
    # Title and introduction
    title = pn.pane.Markdown("""
    # Safeguard Recommendation System 🛡️
    
    Welcome to the BELLS Safeguard Recommendation System!
    
    This tool will help you find the most suitable safeguard(s) based on your specific needs and constraints.
    Please answer the following questions about your system and requirements to receive personalized recommendations.
    """)
    
    # System Configuration
    system_type = pn.widgets.RadioButtonGroup(
        name='System Access Type',
        options=["Black Box API", "Direct Access"],
        value="Black Box API",
        button_type='success'
    )
    
    system_help = pn.pane.Markdown("""
    **Help:** Choose your system access type:
    - Black Box API: You only have API access (e.g., OpenAI API, Claude API)
    - Direct Access: You have access to the model weights or deployment infrastructure
    """)
    
    # Use Case Assessment with help text as separate markdown
    interaction_help = pn.pane.Markdown("Select all types of interactions that apply to your use case")
    interaction_types = pn.widgets.MultiChoice(
        name='Interaction Types',
        options=["General chat/conversation", "Content generation", "Code generation", 
                "Data analysis", "Expert advice", "Customer service"],
        value=[]
    )
    
    user_help = pn.pane.Markdown("Select all user types that will have access to your system")
    user_types = pn.widgets.MultiChoice(
        name='User Types',
        options=["General public", "Authenticated users only", "Internal employees", 
                "Technical users", "Students/Educational"],
        value=[]
    )
    
    # Security Preferences
    example_prompts = get_example_prompts()
    examples_md = pn.pane.Markdown("**Would you allow your system to answer these types of borderline questions?**")
    examples_display = pn.Column()
    for idx, prompt in example_prompts.iterrows():
        examples_display.append(pn.pane.Markdown(f"""
        > **Example {idx+1}:** {prompt['Goal']}  
        > *Category: {prompt['Category']}*
        """))
    
    conservativeness_help = pn.pane.Markdown("""
    Based on the examples above:
    - Level 1: Minimal filtering (high risk tolerance)
    - Level 3: Balanced approach
    - Level 5: Maximum security (very conservative)
    """)
    conservativeness = pn.widgets.IntSlider(
        name='Conservativeness Level',
        start=1,
        end=5,
        value=3,
        step=1
    )
    
    primary_concerns_help = pn.pane.Markdown("Select your main security priorities")
    primary_concerns = pn.widgets.MultiChoice(
        name='Primary Security Concerns',
        options=["Regulatory Compliance", "IP Protection", "Content Safety", 
                "Misinformation Prevention", "Privacy Protection"],
        value=[]
    )
    
    # Operational Requirements
    operational_note = pn.pane.Alert("""Note that this is a mock-up demonstration using an LLM to generate recommendations based on your inputs and 
               simulated evaluation results. In a production system, the recommendations would be based on real-world performance data and 
               more sophisticated matching algorithms.""", alert_type='warning')
    
    request_volume_help = pn.pane.Markdown("""
    Affects performance and scaling requirements:
    - Low: Suitable for basic API implementations
    - Medium: May require optimization
    - High: Needs enterprise-grade solutions
    """)
    request_volume = pn.widgets.Select(
        name='Expected Request Volume',
        options=["Low (<1k/day)", "Medium (1k-10k/day)", "High (>10k/day)"],
        value="Low (<1k/day)"
    )
    
    risk_level_help = pn.pane.Markdown("""
    Likelihood of receiving adversarial/jailbreak attempts:
    - Very Low: General purpose, low-risk applications
    - Medium: Public-facing applications
    - High: Applications likely to face adversarial attempts
    """)
    risk_level = pn.widgets.Select(
        name='Expected Risk Level',
        options=["Very Low (<1%)", "Low (1-5%)", "Medium (5-15%)", "High (>15%)"],
        value="Low (1-5%)"
    )
    
    fpr_tolerance_help = pn.pane.Markdown("""
    How much over-filtering can your application accept:
    - Very Low: Critical applications where blocking valid content is costly
    - Medium: Balance between security and usability
    - High: Security is priority over occasional false positives
    """)
    fpr_tolerance = pn.widgets.Select(
        name='False Positive Tolerance',
        options=["Very Low", "Low", "Medium", "High"],
        value="Low"
    )
    
    # Recommendation display
    recommendation_text = pn.pane.Markdown("")
    loading_indicator = pn.indicators.LoadingSpinner(value=False, size=50)
    
    def update_recommendation(event):
        loading_indicator.value = True
        try:
            user_preferences = {
                "system_type": system_type.value,
                "interaction_types": interaction_types.value,
                "user_types": user_types.value,
                "conservativeness": conservativeness.value,
                "primary_concerns": primary_concerns.value,
                "request_volume": request_volume.value,
                "jailbreak_proportion": risk_level.value,
                "fpr_tolerance": fpr_tolerance.value
            }
            
            evaluation_data = load_evaluation_data()
            recommendation = generate_recommendation(user_preferences, evaluation_data)
            recommendation_text.object = recommendation
        finally:
            loading_indicator.value = False
    
    get_recommendation_button = pn.widgets.Button(
        name='Get Recommendation',
        button_type='primary'
    )
    get_recommendation_button.on_click(update_recommendation)
    
    # Layout with help text next to widgets
    return pn.Column(
        title,
        pn.pane.Markdown("## System Configuration"),
        pn.Row(system_type, system_help),
        pn.pane.Markdown("## Use Case Assessment"),
        pn.Row(interaction_types, interaction_help),
        pn.Row(user_types, user_help),
        pn.pane.Markdown("## Security Preferences"),
        examples_md,
        examples_display,
        pn.Row(conservativeness, conservativeness_help),
        pn.Row(primary_concerns, primary_concerns_help),
        pn.pane.Markdown("## Operational Requirements"),
        operational_note,
        pn.Row(request_volume, request_volume_help),
        pn.Row(risk_level, risk_level_help),
        pn.Row(fpr_tolerance, fpr_tolerance_help),
        pn.Row(get_recommendation_button, loading_indicator),
        recommendation_text,
        sizing_mode='stretch_width'
    )

if __name__ == "__main__":
    recommendation_ui()