import panel as pn
import pandas as pd
import random
from pathlib import Path

# Enable Panel extensions
pn.extension('tabulator')

def load_datasets():
    """Load all datasets"""
    data_dir = Path(__file__).parent.parent.parent.parent / 'data'
    
    # Load evaluation results
    evaluation_results = pd.read_csv(data_dir / 'safeguard_evaluation_results.csv')
    
    # Load non-adversarial datasets
    benign_prompts = pd.read_csv(data_dir / 'benign_non-adversarial.csv')
    borderline_prompts = pd.read_csv(data_dir / 'borderline_non-adversarial.csv')
    harmful_prompts = pd.read_csv(data_dir / 'harmful_non-adversarial.csv')
    
    # Load jailbreak datasets
    benign_jailbreaks = pd.read_csv(data_dir / 'benign_jailbreaks.csv')
    borderline_jailbreaks = pd.read_csv(data_dir / 'borderline_jailbreaks.csv')
    harmful_jailbreaks = pd.read_csv(data_dir / 'harmful_jailbreaks.csv')
    
    return {
        'evaluation_results': evaluation_results,
        'datasets': {
            'Harmful': {
                'Non-Adversarial': harmful_prompts,
                'Adversarial': harmful_jailbreaks
            },
            'Borderline': {
                'Non-Adversarial': borderline_prompts,
                'Adversarial': borderline_jailbreaks
            },
            'Benign': {
                'Non-Adversarial': benign_prompts,
                'Adversarial': benign_jailbreaks
            }
        }
    }

def get_detection_probability(evaluation_results, safeguard_name, dataset_type, content_type):
    """Get detection probability based on dataset type and safeguard"""
    if content_type == 'Non-Adversarial':
        column_name = f"{dataset_type.lower()}_non-adversarial"
    else:
        column_name = f"{dataset_type.lower()}_jailbreaks"
    return evaluation_results[evaluation_results['safeguard'] == safeguard_name][column_name].iloc[0]

def get_detection_result(evaluation_results, safeguard_name, dataset_type, content_type):
    """Simulate detection with actual probabilities"""
    prob = get_detection_probability(evaluation_results, safeguard_name, dataset_type, content_type)
    return random.random() < prob

def create_prompt_card(row, dataset_type, content_type, safeguard, evaluation_results):
    """Create a card-like display for a prompt"""
    card = pn.Column(width=800)
    
    # Header with goal
    card.append(pn.pane.Markdown(f"### {row['Goal']}"))
    
    # Detection status
    if safeguard == "All Safeguards":
        detection_results = {
            name: get_detection_result(evaluation_results, name, dataset_type, content_type)
            for name in evaluation_results['safeguard']
        }
        status_row = pn.Row()
        for name, result in detection_results.items():
            status = "✅" if result else "❌"
            color = "success" if result else "danger"
            status_row.append(pn.pane.Alert(f"{status} {name}", alert_type=color))
        card.append(status_row)
    else:
        detected = get_detection_result(evaluation_results, safeguard, dataset_type, content_type)
        status = "✅" if detected else "❌"
        color = "success" if detected else "danger"
        card.append(pn.pane.Alert(f"{status} {safeguard}", alert_type=color))
    
    # Content display
    if content_type == "Non-Adversarial" and 'Behavior' in row:
        card.append(pn.pane.Markdown("**Expected Behavior:**"))
        card.append(pn.pane.Markdown(f"_{row['Behavior']}_"))
    elif content_type == "Adversarial":
        card.append(pn.pane.Markdown("**Jailbreak Attempt:**"))
        if 'Jailbreak' in row:
            card.append(pn.pane.Markdown(f"_{row['Jailbreak']}_"))
        elif 'Attack' in row:
            card.append(pn.pane.Markdown(f"_{row['Attack']}_"))
    
    # Category if available
    if 'Category' in row:
        card.append(pn.pane.Markdown(f"**Category:** `{row['Category']}`"))
    
    card.append(pn.pane.Markdown("---"))
    return card

def update_display(harm_level, content_type, safeguard, search_query, category_filter, datasets, evaluation_results):
    """Update the display based on current selections"""
    current_dataset = datasets[harm_level][content_type]
    
    # Apply category filter
    if category_filter != 'All' and 'Category' in current_dataset.columns:
        current_dataset = current_dataset[current_dataset['Category'] == category_filter]
    
    # Apply search filter
    if search_query:
        current_dataset = current_dataset[
            current_dataset['Goal'].str.contains(search_query, case=False, na=False)
        ]
    
    # Calculate statistics
    total_count = len(current_dataset)
    stats = pn.Column()
    
    if safeguard == "All Safeguards":
        detected_counts = {
            name: sum([get_detection_result(evaluation_results, name, harm_level, content_type) 
                      for _ in range(total_count)])
            for name in evaluation_results['safeguard']
        }
        
        # Display stats in a grid
        stats_grid = pn.GridBox(ncols=len(evaluation_results) + 1)
        stats_grid.append(
            pn.indicators.Number(
                name='Total Prompts',
                value=total_count,
                format='{value}',
                font_size='24px'
            )
        )
        for name, count in detected_counts.items():
            stats_grid.append(
                pn.indicators.Number(
                    name=name,
                    value=count/total_count*100,
                    format='{value:.1f}%',
                    font_size='24px'
                )
            )
        stats.append(stats_grid)
    else:
        detected_count = sum([get_detection_result(evaluation_results, safeguard, harm_level, content_type) 
                            for _ in range(total_count)])
        stats_row = pn.Row(
            pn.indicators.Number(
                name='Total Prompts',
                value=total_count,
                format='{value}',
                font_size='24px'
            ),
            pn.indicators.Number(
                name='Detected',
                value=detected_count,
                format='{value}',
                font_size='24px'
            ),
            pn.indicators.Number(
                name='Detection Rate',
                value=detected_count/total_count*100,
                format='{value:.1f}%',
                font_size='24px'
            )
        )
        stats.append(stats_row)
    
    # Create cards for each prompt
    cards = pn.Column()
    for _, row in current_dataset.iterrows():
        cards.append(create_prompt_card(row, harm_level, content_type, safeguard, evaluation_results))
    
    return pn.Column(stats, cards)

def playground_ui():
    # Load all datasets at the start
    all_data = load_datasets()
    datasets = all_data['datasets']
    evaluation_results = all_data['evaluation_results']
    
    # Title and introduction
    title = pn.pane.Markdown("""
    # Data Playground 🎮
    
    Welcome to the BELLS Data Playground!

    This interactive environment allows you to explore how different safeguards perform against various types of prompts. 
    You can:
    - Compare different safeguards' detection capabilities
    - Test various prompt categories (Harmful, Borderline, Benign)
    - Explore both direct prompts and adversarial attempts
    - Filter by specific harm categories
    - Search through our comprehensive prompt database
    """)
    
    # Legend
    legend = pn.pane.Markdown("""
    📋 **Legend:**
    - ✅ Content detected/blocked by safeguard
    - ❌ Content allowed by safeguard
    """)
    
    # Controls
    harm_level = pn.widgets.RadioButtonGroup(
        name='Dataset Type',
        options=['Harmful', 'Borderline', 'Benign'],
        value='Benign',
        button_type='success'
    )
    
    content_type = pn.widgets.RadioButtonGroup(
        name='Content Type',
        options=['Non-Adversarial', 'Adversarial'],
        value='Non-Adversarial',
        button_type='primary'
    )
    
    safeguard = pn.widgets.Select(
        name='Select Safeguard',
        options=["All Safeguards"] + evaluation_results['safeguard'].tolist()
    )
    
    search = pn.widgets.TextInput(
        name='🔍 Search prompts...',
        placeholder="e.g., 'generate code' or 'financial advice'"
    )
    
    # Category filter
    category_filter = pn.widgets.Select(
        name='Category Filter',
        options=['All'],
        value='All'
    )
    
    # Jailbreak alert
    jailbreak_alert = pn.pane.Alert("""
        ⚠️ **Note**: The adversarial datasets contain thousands of entries. 
        For readability, only a sample of 40 attempts is shown below.
        
        Complete datasets available on GitHub:
        - [Benign Adversarial Dataset](https://github.com/brash6/BELLS_leaderboard_mock_up/blob/main/data/benign_jailbreaks.csv)
        - [Borderline Adversarial Dataset](https://github.com/brash6/BELLS_leaderboard_mock_up/blob/main/data/borderline_jailbreaks.csv)
        - [Harmful Adversarial Dataset](https://github.com/brash6/BELLS_leaderboard_mock_up/blob/main/data/harmful_jailbreaks.csv)
    """, alert_type='warning')
    
    # Dynamic display area
    display_area = pn.Column()
    
    def update(event=None):
        # Update category options based on current dataset
        current_dataset = datasets[harm_level.value][content_type.value]
        if 'Category' in current_dataset.columns:
            category_filter.options = ['All'] + sorted(current_dataset['Category'].unique().tolist())
        
        # Update jailbreak alert visibility
        jailbreak_alert.visible = content_type.value == 'Adversarial'
        
        # Update display
        display_area[:] = [update_display(
            harm_level.value,
            content_type.value,
            safeguard.value,
            search.value,
            category_filter.value,
            datasets,
            evaluation_results
        )]
    
    # Set up event handlers
    harm_level.param.watch(update, 'value')
    content_type.param.watch(update, 'value')
    safeguard.param.watch(update, 'value')
    search.param.watch(update, 'value')
    category_filter.param.watch(update, 'value')
    
    # Controls layout
    controls = pn.Row(
        pn.Column(pn.pane.Markdown("### Dataset Type"), harm_level),
        pn.Column(pn.pane.Markdown("### Content Type"), content_type),
        pn.Column(pn.pane.Markdown("### Safeguard"), safeguard),
        pn.Column(pn.pane.Markdown("### Category"), category_filter)
    )
    
    # Initial update
    update()
    
    # Final layout
    return pn.Column(
        title,
        legend,
        controls,
        search,
        jailbreak_alert,
        display_area,
        sizing_mode='stretch_width'
    ) 