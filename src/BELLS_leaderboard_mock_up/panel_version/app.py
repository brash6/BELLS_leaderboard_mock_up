import panel as pn
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

from recommender import recommendation_ui
from playground import playground_ui

# Enable Panel extensions
pn.extension('plotly', 'tabulator')

# Read the CSV file
def load_data():
    data_dir = Path(__file__).parent.parent.parent.parent / 'data'
    df = pd.read_csv(data_dir / 'safeguard_evaluation_results.csv')
    return df

def create_leaderboard():
    df = load_data()
    
    # Introduction text
    intro = pn.pane.Markdown("""
    # BELLS Leaderboard
    
    The rise of large language models (LLMs) has been accompanied by the emergence of vulnerabilities, 
    such as jailbreaks and prompt injections, which exploit these systems to bypass constraints and induce harmful 
    or unintended behaviors. In response, safeguards have been developed to monitor inputs and outputs, aiming to detect 
    and mitigate these vulnerabilities. These safeguards, while promising, require robust evaluation frameworks to assess 
    their effectiveness and generalizability.
    """)
    
    # Add disclaimer
    disclaimer = pn.pane.Alert("""
    ⚠️ DISCLAIMER: All evaluation results shown are simulated for demonstration purposes only and do not 
    reflect actual performance of the safeguards.
    """, alert_type='danger')
    
    # Dataset explanation
    dataset_info = pn.pane.Alert("""
    **Benchmark Datasets**
    
    This evaluation uses a combination of datasets to assess safeguard effectiveness:
    
    1. **JailbreakBench (JBB-Behaviors)**:
       - 100 harmful prompts across different harm categories
       - 100 original "benign" prompts, which were further categorized into:
         * Benign prompts (~50)
         * Borderline prompts (~50) after careful content review
    
    2. **Jailbreak Templates**:
       - 80 narrative-based jailbreak templates
       - Used to generate combinations with prompts of varying harmfulness levels
    """, alert_type='info')
    
    # Update safeguards section with links
    safeguards_info = pn.pane.Markdown("""
    ### Popular Safeguards
    
    Several leading safeguards are evaluated in this benchmark:

    - **[Lakera Guard](https://www.lakera.ai/)**: Industry-leading content filtering API
    - **[NVIDIA NeMo Guardrails](https://github.com/NVIDIA/NeMo-Guardrails)**: Open-source framework for LLM safety
    - **[LLM Guard](https://llm-guard.com/)**: Comprehensive open-source safety toolkit  
    - **[Langkit](https://github.com/whylabs/langkit)**: Lightweight content filtering solution
    - **[Prompt Guard](https://www.llama.com/docs/model-cards-and-prompt-formats/prompt-guard/)**: Specialized jailbreak detection system
    """)
    
    # BELLS Score plot
    df_sorted = df.sort_values('BELLS_score', ascending=False)
    bells_plot = px.bar(df_sorted,
                       x='safeguard',
                       y='BELLS_score',
                       title='BELLS Score by Safeguard')
    bells_plot.update_traces(marker_color='rgb(55, 83, 109)')
    
    # Analysis text
    bells_analysis = pn.pane.Markdown("""
    ### Analysis: BELLS Score Breakdown
    - Lakera leads with highest BELLS score (0.91)
    - LLM Guard shows strong performance (0.86)
    - All safeguards maintain scores above 0.71
    - Clear performance gap between top and bottom performers
    """)
    
    # False Positive Analysis
    fp_plot = px.scatter(df, 
                        x='benign_jailbreaks',
                        y='benign_non-adversarial',
                        text='safeguard',
                        title='False Positive Rate Comparison',
                        labels={
                            'benign_jailbreaks': 'Benign Jailbreak Detection Rate',
                            'benign_non-adversarial': 'False Positive Rate on Benign Prompts'
                        })
    fp_plot.update_traces(textposition='top center')
    fp_plot.add_shape(type='line',
                      x0=0, y0=0,
                      x1=1, y1=1,
                      line=dict(color='red', dash='dash'))
    
    fp_analysis = pn.pane.Markdown("""
    ### Analysis: False Positive Insights
    - Langkit & LLM Guard show lowest FPR on benign prompts (2%)
    - NeMo demonstrates balanced FPR (2.6%)
    - Prompt Guard has highest benign jailbreak detection (12.7%)
    - Lakera maintains good balance between metrics
    """)
    
    # Harm Categories Analysis
    harm_categories = ['Harassment/Discrimination', 'Malware/Hacking', 'Physical_harm', 
                      'Privacy', 'Expert_advice', 'Government_decision_making']
    
    harm_data = df[['safeguard'] + harm_categories].melt(
        id_vars=['safeguard'],
        var_name='Category',
        value_name='Score'
    )
    
    harm_plot = px.bar(harm_data,
                       x='safeguard',
                       y='Score',
                       color='Category',
                       title='Performance Across Harm Categories',
                       barmode='group')
    
    harm_analysis = pn.pane.Markdown("""
    ### Analysis: Harm Category Breakdown
    - Malware/Hacking: Lakera leads with 98% detection
    - Physical harm: LLM Guard & Lakera tie at 98%
    - Expert advice: consistently lowest scores (<51%)
    - Privacy: challenging for all models (51-61%)
    """)
    
    # Raw data table with tabulator
    raw_data = pn.widgets.Tabulator(df, pagination='remote', page_size=10)
    
    # Create template
    template = pn.template.FastListTemplate(
        title='BELLS Leaderboard',
        sidebar=[],
        main=[
            pn.Tabs(
                ('Leaderboard', pn.Column(
                    intro,
                    disclaimer,  # Add disclaimer
                    dataset_info,
                    safeguards_info,  # Add safeguards section
                    pn.pane.Plotly(bells_plot),
                    bells_analysis,
                    pn.pane.Plotly(fp_plot),
                    fp_analysis,
                    pn.pane.Plotly(harm_plot),
                    harm_analysis,
                    pn.pane.Markdown("### Raw Data"),
                    raw_data
                )),
                ('Recommendation', recommendation_ui()),
                ('Playground', playground_ui())
            )
        ]
    )
    
    return template

# Create and serve the application
template = create_leaderboard()
template.servable() 