import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

from BELLS_leaderboard_mock_up.recommender import recommendation_ui
from BELLS_leaderboard_mock_up.playground import playground_ui

# Read the CSV file
@st.cache_data
def load_data():
    data_dir = Path(__file__).parent.parent.parent / 'data'
    df = pd.read_csv(data_dir / 'safeguard_evaluation_results.csv')
    return df

# Get the path for images
def get_image_path():
    return Path(__file__).parent.parent.parent / 'images' / 'adv_harm_matrix.png'

def main():
    # Add navigation in sidebar
    page = st.sidebar.radio(
        "Navigation",
        ["Leaderboard", "Recommendation", "Playground"]
    )
    
    if page == "Leaderboard":
        st.title("BELLS Leaderboard")

        st.write("""The rise of large language models (LLMs) has been accompanied by the emergence of vulnerabilities, 
                   such as jailbreaks and prompt injections, which exploit these systems to bypass constraints and induce harmful 
                   or unintended behaviors. In response, safeguards have been developed to monitor inputs and outputs, aiming to detect 
                   and mitigate these vulnerabilities. These safeguards, while promising, require robust evaluation frameworks to assess 
                   their effectiveness and generalizability.
                   This leaderboard provides a comprehensive evaluation of various input-output safeguards against jailbreak attempts. 
                   Using a diverse set of datasets and metrics, it benchmarks their detection capabilities and false positive rates among 
                   a wide range of prompts and use cases.""")
        
        # Add accurate dataset explanation section
        st.info("""
        **Benchmark Datasets**
        
        This evaluation uses a combination of datasets to assess safeguard effectiveness:
        
        1. **JailbreakBench (JBB-Behaviors)**:
           - 100 harmful prompts across different harm categories
           - 100 original "benign" prompts, which were further categorized into:
             * Benign prompts (~50)
             * Borderline prompts (~50) after careful content review
        
        2. **Jailbreak Templates**:
           - 80 narrative-based jailbreak templates from "rubend18/ChatGPT-Jailbreak-Prompts"
           - Used to generate combinations with prompts of varying harmfulness levels
        
        The benchmark evaluates all combinations of jailbreak templates with prompts across 
        different harmfulness categories (as illustrated in the adversariality vs. harmfulness matrix), 
        providing a comprehensive assessment of safeguard effectiveness against both direct harmful 
        content and jailbreak attempts.
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
        image_path = get_image_path()
        st.image(str(image_path), caption="Evaluation Matrix: Adversariality vs. Harmfulness")
        
        st.markdown("""
        **Evaluation Framework**
        
        The evaluation matrix above illustrates how safeguards are assessed across two key dimensions:
        
        1. **Adversariality** (Y-axis):
           - **Adversarial**: Prompts using jailbreak templates
           - **Vanilla**: Direct prompts without jailbreak attempts
        
        2. **Harmfulness** (X-axis):
           - Increasing harmfulness from left to right
           - **Moral line**: Separates ethically acceptable from questionable content
           - **Legal line**: Separates legal from illegal content
        
        **Key Metrics**:
        - **TPR_adv**: True Positive Rate for adversarial (jailbreak) prompts
        - **TPR_van**: True Positive Rate for vanilla (direct) prompts
        - **FPR**: False Positive Rate on benign prompts
        - **Adversarial Sensitivity**: Measures effectiveness against jailbreak attempts
        - **Moral Frontier**: Evaluates accuracy in identifying ethically questionable content
        
        **BELLS Score**:
        The overall effectiveness is measured by the BELLS score:
        ```
        BELLS score = (TPR_adv + TPR_van + (1 - FPR)) / 3
        ```
        This balanced metric combines detection rates for both adversarial and vanilla prompts while penalizing false positives.
        """)
        
        # Replace old radar chart with new metrics
        categories = ['Harmful Jailbreaks', 'Direct Harmful', 'Benign Accuracy']
        fig = go.Figure()
        
        for safeguard in df['safeguard']:
            values = df[df['safeguard'] == safeguard][['harmful_jailbreaks', 'harmful_vanilla', 'benign_vanilla']].values.flatten().tolist()
            # Convert benign prompts detection to accuracy (1 - false positive rate)
            values[2] = 1 - values[2]
            values.append(values[0])  # Complete the circle
            
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories + [categories[0]],
                name=safeguard
            ))
        
        fig.update_layout(
            polar=dict(radialaxis=dict(range=[0, 1])),
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
        
        # Create scatter plot comparing benign jailbreaks vs benign_vanilla
        fig_fp = px.scatter(df, 
                           x='benign_jailbreaks',
                           y='benign_vanilla',
                           text='safeguard',
                           title='False Positive Rate Comparison',
                           labels={
                               'benign_jailbreaks': 'Benign Jailbreak Detection Rate',
                               'benign_vanilla': 'False Positive Rate on Benign Prompts'
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

        # Create DataFrame for sensitivity comparison
        sensitivity_df = df[['safeguard', 'borderline_vanilla', 'benign_jailbreaks']].copy()
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
        st.dataframe(df, use_container_width=True)

    elif page == "Recommendation":
        recommendation_ui()
        
    else:  # page == "Playground"
        playground_ui()

if __name__ == "__main__":
    main()