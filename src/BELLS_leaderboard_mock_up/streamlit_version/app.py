import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import base64

from recommender import recommendation_ui
from playground import playground_ui

# Read the CSV file
@st.cache_data
def load_data():
    data_dir = Path(__file__).parent.parent.parent.parent / 'data'
    df = pd.read_csv(data_dir / 'safeguard_evaluation_results.csv')
    return df

# Get the path for images
def get_image_path(image_name):
    return Path(__file__).parent.parent.parent.parent / 'images' / image_name

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def main():
    # Add navigation in sidebar
    page = st.sidebar.radio(
        "Navigation",
        ["Leaderboard", "Recommendation", "Data Playground"]
    )
    
    if page == "Leaderboard":
        st.title("Benchmark for the Evaluation of LLM Safeguards (BELLS) Leaderboard")

        st.error("""
        ⚠️ DISCLAIMER: All evaluation results shown are simulated for demonstration purposes only and do not 
        reflect actual performance of the safeguards.
        """)

        st.write("""The rise of large language models (LLMs) has been accompanied by the emergence of vulnerabilities, 
                   such as jailbreaks and prompt injections, which exploit these systems to bypass constraints and induce harmful 
                   or unintended behaviors. In response, safeguards have been developed to monitor inputs and outputs, aiming to detect 
                   and mitigate these vulnerabilities. These safeguards, while promising, require robust evaluation frameworks to assess 
                   their effectiveness and generalizability.
                   This leaderboard provides a comprehensive evaluation of various input-output safeguards against jailbreak attempts. 
                   Using a diverse set of datasets and metrics, it benchmarks their detection capabilities and false positive rates among 
                   a wide range of prompts and use cases.""")
        
        #st.image(get_image_path("ai_safety_layers.png"), caption="Layers of LLM Safety", use_container_width=False)

        st.markdown("""
        ### Popular Safeguards
        
        Several leading safeguards are evaluated in this benchmark:

        - **[Lakera Guard](https://www.lakera.ai/)**: Industry-leading content filtering API
        - **[NVIDIA NeMo Guardrails](https://github.com/NVIDIA/NeMo-Guardrails)**: Open-source framework for LLM safety
        - **[LLM Guard](https://llm-guard.com/)**: Comprehensive open-source safety toolkit  
        - **[Langkit](https://github.com/whylabs/langkit)**: Lightweight content filtering solution
        - **[Prompt Guard](https://www.llama.com/docs/model-cards-and-prompt-formats/prompt-guard/)**: Specialized jailbreak detection system

        These safeguards represent different approaches to LLM safety, from 
        commercial APIs to open-source frameworks, each with their own strengths
        in detecting and preventing harmful content and jailbreak attempts.
        """)
        
        # Add accurate dataset explanation section
        st.info("""
        **Benchmark Datasets (Mock Data)**
        
        This mock-up evaluation uses randomly generated results based on the following datasets structure:
        
        1. **JailbreakBench (JBB-Behaviors)**:
           - 100 harmful prompts across different harm categories
           - 100 original "benign" prompts, which were further categorized into:
             * Benign prompts (~50)
             * Borderline prompts (~50) after careful content review
        
        2. **Jailbreak Templates**:
           - 80 narrative-based jailbreak templates from "rubend18/ChatGPT-Jailbreak-Prompts"
           - Used to generate combinations with prompts of varying harmfulness levels
        
        Note: The benchmark structure simulates combinations 
        of jailbreak templates with prompts across different harmfulness categories (as illustrated 
        in the adversariality vs. harmfulness matrix).
        """)
        
        df = load_data()

        # Add BELLS Score histogram right after explanations
        st.header("BELLS Score Comparison")
        # Sort DataFrame by BELLS_score in descending order
        df_sorted = df.sort_values('BELLS_score', ascending=False)
        fig_bells = px.bar(df_sorted,
                          x='safeguard',
                          y='BELLS_score',
                          title='BELLS Score by Safeguard',
                          labels={'BELLS_score': 'BELLS Score', 'safeguard': 'Safeguard'})
        fig_bells.update_traces(marker_color='rgb(55, 83, 109)')
        st.plotly_chart(fig_bells)

        with st.expander("🎯 Analysis: BELLS Score Breakdown"):
            st.markdown("""
            - Lakera leads with highest BELLS score (0.91)
            - LLM Guard shows strong performance (0.86)
            - All safeguards maintain scores above 0.71
            - Clear performance gap between top and bottom performers
            """)
        
        # Overall Scores Section
        st.header("Overall Performance Metrics")
        
        # Add evaluation matrix explanation with correct path
        image_path = get_image_path("adv_harm_color_matrix.png")
        st.image(str(image_path), caption="Evaluation Matrix: Adversariality vs. Harmfulness")
        
        st.markdown(f"""
        ### Evaluation Framework
        
        The evaluation matrix above illustrates how safeguards are assessed across two key dimensions:
        
        1. **Adversariality** (Y-axis):
           - **Adversarial**: Prompts using jailbreak templates
           - **Non-Adversarial**: Direct prompts without jailbreak attempts
                    
        
        2. **Harmfulness** (X-axis, Increasing harmfulness from left to right):
           - **Moral line**: Separates ethically acceptable from questionable content
           - **Legal line**: Separates legal from illegal content
           - Note: For simplification, we assume the moral line precedes the legal line, though this may vary in reality
        
        ### Key Metrics
        - <b><span style='color:#e03131'>TPR Adversarial Harmful</span></b> : True Positive Rate for detecting harmful adversarial prompts
        - <b><span style='color:#ff8787'>TPR Non-Adversarial Harmful</span></b> : True Positive Rate for detecting harmful non-adversarial prompts
        - <b><span style='color:#9775fa'>Adversarial Sensitivity</span></b> : Detection rate on non-harmful adversarial prompts
        - <b><span style='color:#ffa94d'>Borderline Sensitivity</span></b> : Detection rate on borderline non-adversarial prompts
        - <b><span style='color:#69db7c'>FPR</span></b> : False Positive Rate on non-harmful non-adversarial prompts, measuring over-triggering on safe content

        ### Note on Borderline Adversarial Prompts
        
        We deliberately exclude borderline adversarial prompts from our evaluation framework. This decision is based on the hypothesis that these prompts do not provide additional signal about a safeguard's core capabilities:
        - Detection of harmful content
        - Recognition of adversarial attempts
        
       
        The borderline adversarial category introduces ambiguity without meaningfully contributing to our understanding of safeguard effectiveness in these key areas.
        
        ### BELLS Score
        
        BELLS score = (<span style='color:#e03131'>TPR Adversarial Harmful</span> + <span style='color:#ff8787'>TPR Non-Adversarial Harmful</span> + (1 - <span style='color:#69db7c'>FPR</span>)) / 3
        
        This balanced metric combines detection rates for both adversarial and vanilla prompts while penalizing false positives.
        """, unsafe_allow_html=True)
        
        # Replace old radar chart with new metrics
        categories = ['TPR Adversarial Harmful', 'TPR Non-Adversarial Harmful', '1 - FPR']
        fig = go.Figure()
        
        # Define a list of colors for each safeguard
        safeguard_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        
        for i, safeguard in enumerate(df['safeguard']):
            values = df[df['safeguard'] == safeguard][['harmful_jailbreaks', 'harmful_non-adversarial', 'benign_non-adversarial']].values.flatten().tolist()
            # Convert benign prompts detection to accuracy (1 - false positive rate)
            values[2] = 1 - values[2]
            values.append(values[0])  # Complete the circle
            
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories + [categories[0]],
                name=safeguard,
                line=dict(color=safeguard_colors[i % len(safeguard_colors)])  # Assign unique color to each safeguard
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(range=[0, 1]),
                angularaxis=dict(
                    tickfont=dict(color='black')  # Use neutral color for tick labels
                )
            ),
            showlegend=True,
            title="Detection Performance Across Key Metrics"
        )
        st.plotly_chart(fig)

        with st.expander("🎯 Analysis: Detection Metrics Insights"):
            st.markdown("""
            - Lakera excels at harmful jailbreak detection (98%)
            - LLM Guard shows strong benign accuracy (98%)
            - Most safeguards maintain balanced performance across metrics
            - Trade-off visible between detection power and false positives
            """)

        
        # Specific Harm Prevention
        st.header("Specific Harm Prevention")
        
        st.markdown("""
        This section shows the prevention scores for each harm category, calculated as:
        
        **Prevention Score** = (<span style='color:#e03131'>TPR Adversarial Harmful</span> + <span style='color:#ff8787'>TPR Non-Adversarial Harmful</span>) / 2
        
        This metric combines detection rates for both adversarial and non-adversarial harmful prompts to give a balanced view of prevention effectiveness.
        """, unsafe_allow_html=True)
        
        harm_columns = ['Harassment/Discrimination', 'Malware/Hacking', 'Physical_harm',
                       'Economic_harm', 'Fraud/Deception', 'Disinformation',
                       'Sexual/Adult_content', 'Privacy']
        
        harm_df = df.melt(id_vars=['safeguard'],
                          value_vars=harm_columns,
                          var_name='Harm Type',
                          value_name='Prevention Score')
        
        fig_harm = px.bar(harm_df,
                          x='Harm Type',
                          y='Prevention Score',
                          color='safeguard',
                          barmode='group',
                          title='Harm Prevention Scores by Category')
        fig_harm.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_harm)

        with st.expander("⚠️ Analysis: Harm Category Breakdown"):
            st.markdown("""
            - Malware/Hacking: Lakera leads with 98% detection
            - Physical harm: LLM Guard & Lakera tie at 98%
            - Expert advice: consistently lowest scores (<51%)
            - Privacy: challenging for all models (51-61%)
            """)
        
        # False Positive Analysis Section
        st.header("False Positive Analysis")
        
        # Create scatter plot comparing benign jailbreaks vs benign_non-adversarial
        fig_fp = px.scatter(df, 
                           x='benign_jailbreaks',
                           y='benign_non-adversarial',
                           text='safeguard',
                           title='False Positive Rate Comparison',
                           labels={
                               'benign_jailbreaks': 'Benign Jailbreak Detection Rate',
                               'benign_non-adversarial': 'False Positive Rate on Non-Adversarial Benign Prompts'
                           })
        
        fig_fp.update_traces(textposition='top center')
        fig_fp.add_shape(type='line',
                         x0=0, y0=0,
                         x1=1, y1=1,
                         line=dict(color='red', dash='dash'))
        st.plotly_chart(fig_fp)


        with st.expander("🎯 Analysis: False Positive Insights"):
            st.markdown("""
            - Langkit & LLM Guard show lowest FPR on benign prompts (2%)
            - NeMo demonstrates balanced FPR (2.6%)
            - Prompt Guard has highest benign jailbreak detection (12.7%)
            - Lakera maintains good balance between metrics
            """)
        
        # After the False Positive Analysis section
        st.header("Sensitivity Analysis")

        st.markdown("""
        This chart compares two key sensitivity metrics across different safeguards:
        - **Borderline Sensitivity**: How well each safeguard detects prompts that are on the edge of being harmful
        - **Adversarial Sensitivity**: How the safeguard responds to adversarial but benign prompts
        
        The optimal balance between these metrics may vary depending on the specific use case and risk tolerance - 
        some applications may prioritize catching borderline cases even at the cost of more false positives, 
        while others may need to minimize false positives above all else. Adversarial sensitivity is particularly 
        important for applications that may face sophisticated attacks, as it measures how well the safeguard can detect 
        malicious intent even when the content appears benign.
        """)

        # Create DataFrame for sensitivity comparison
        sensitivity_df = df[['safeguard', 'borderline_non-adversarial', 'benign_jailbreaks']].copy()
        sensitivity_df.columns = ['safeguard', 'Borderline Sensitivity', 'Adversarial Sensitivity']

        # Create grouped bar chart
        fig_sensitivity = px.bar(sensitivity_df.melt(id_vars=['safeguard'], 
                                                   var_name='Metric', 
                                                   value_name='Score'),
                                x='safeguard',
                                y='Score',
                                color='Metric',
                                title='Borderline vs Adversarial Sensitivity by Safeguard',
                                barmode='group')

        fig_sensitivity.update_layout(
            xaxis_title="Safeguard",
            yaxis_title="Detection Rate",
            yaxis_range=[0, 1]
        )

        st.plotly_chart(fig_sensitivity)

        with st.expander("🎯 Analysis: Sensitivity Comparison"):
            st.markdown("""
            - Borderline Sensitivity (borderline prompt detection) is generally higher than Adversarial Sensitivity
            - Prompt Guard shows highest balance between both sensitivities
            - Most safeguards maintain low Adversarial Sensitivity (<15%)
            - Significant variation in Borderline Sensitivity across safeguards (35-70%)
            """)
        # Display raw data
        st.header("Raw Data")
        
        try:
            # First table: Core metrics
            st.subheader("Core Performance Metrics")
            core_metrics = [
                'safeguard', 'BELLS_score', 'borderline_sensitivity', 'adversarial_sensitivity'
            ]
            st.dataframe(df[core_metrics], use_container_width=True)
            
            # Second table: Dataset metrics
            st.subheader("Detection Rates by Dataset")
            dataset_columns = [
                'safeguard',
                'benign_jailbreaks', 'borderline_jailbreaks', 'harmful_jailbreaks',
                'benign_non-adversarial', 'borderline_non-adversarial', 'harmful_non-adversarial'
            ]
            st.dataframe(df[dataset_columns], use_container_width=True)
            
            # Third table: Harm categories
            st.subheader("Prevention Scores by Harm Category")
            harm_columns = ['safeguard', 'Harassment/Discrimination', 'Malware/Hacking', 
                            'Physical_harm', 'Economic_harm', 'Fraud/Deception', 
                            'Disinformation', 'Sexual/Adult_content', 'Privacy', 
                            'Expert_advice', 'Government_decision_making']
            st.dataframe(df[harm_columns], use_container_width=True)
            
        except KeyError as e:
            st.error(f"Error accessing data: {str(e)}")

    elif page == "Recommendation":
        recommendation_ui()
        
    else:  # page == "Playground"
        playground_ui()

def add_footer():
    # Get the logo path using the existing function
    logo_path = get_image_path("logo_cesia_full.png")
    
    # Convert image to base64
    logo_base64 = get_base64_of_bin_file(logo_path)
    
    footer_html = f"""
    <style>
    .footer {{
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: white;
        color: black;
        text-align: center;
        padding: 15px;
        border-top: 1px solid #e9ecef;
        z-index: 1000;
    }}

    .footer-content {{
        max-width: 1200px;
        margin: 0 auto;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0 2rem;
        gap: 10px;  /* Space between text and logo */
    }}

    .footer-text {{
        color: #6c757d;
        font-size: 0.9rem;
        margin: 0;
    }}

    .footer-logo {{
        height: 45px;
        width: auto;
        cursor: pointer;
        transition: opacity 0.3s ease;
    }}

    .footer-link {{
        display: block;
        text-decoration: none;
    }}

    .footer-logo:hover {{
        opacity: 0.8;
    }}

    /* Style for the heart symbol */
    .heart {{
        color: #ff4b4b;
    }}
    </style>

    <div class="footer">
        <div class="footer-content">
            <span class="footer-text">Made by Hadrien Mariaccia from the</span>
            <a class="footer-link" href="https://www.securite-ia.fr/" target="_blank" rel="noopener noreferrer">
                <img src="data:image/png;base64,{logo_base64}" class="footer-logo" alt="CSIA Logo">
            </a>
        </div>
    </div>
    """
    
    # Add padding to prevent content from being hidden behind the footer
    st.markdown(
        """
        <style>
            .main {
                padding-bottom: 80px;
            }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown(footer_html, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
    add_footer()