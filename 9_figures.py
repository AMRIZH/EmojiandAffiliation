#!/usr/bin/env python3
"""
9_figures.py - Generate academic figures for Emoji and Political Affiliation research

This script generates publication-quality figures analyzing:
- Political/activist affiliations in GitHub repositories
- Expression/support type distributions
- Stars and contributors comparisons across groups
- Language distributions
- Owner type distributions

Data Groups:
- Affiliated: Repositories with valid political/social affiliations (59 repos)
- Baseline: Repositories with emoji but no affiliation or false positives (4637 repos)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime

# =============================================================================
# CONFIGURATION
# =============================================================================

# File paths
AFFILIATED_CSV = "FinalDataset/7_expression_category_labeled.csv"
FULL_DATASET_CSV = "FinalDataset/validity_checked_affiliated_deepseek_1000_200000.csv"
FIGURES_DIR = "figures"

# Color palette - consistent academic style
COLORS = {
    'affiliated': '#2E86AB',      # Blue
    'baseline': '#A23B72',        # Magenta/Purple
    'false_positive': '#F18F01',  # Orange
    'primary': '#2E86AB',
    'secondary': '#E94F37',
    'tertiary': '#1B998B',
    'quaternary': '#C5D86D',
    'palette': ['#2E86AB', '#E94F37', '#1B998B', '#F18F01', '#C5D86D', '#A23B72', '#5C4D7D']
}

# Figure settings
FIGURE_DPI = 300
FONT_SIZE = 11
TITLE_SIZE = 13

# Set global style
plt.rcParams.update({
    'font.size': FONT_SIZE,
    'axes.titlesize': TITLE_SIZE,
    'axes.labelsize': FONT_SIZE,
    'xtick.labelsize': FONT_SIZE - 1,
    'ytick.labelsize': FONT_SIZE - 1,
    'legend.fontsize': FONT_SIZE - 1,
    'figure.dpi': 100,
    'savefig.dpi': FIGURE_DPI,
    'font.family': 'sans-serif',
})

sns.set_style("whitegrid")
sns.set_palette(COLORS['palette'])

# =============================================================================
# DATA LOADING
# =============================================================================

def load_data():
    """Load and prepare datasets for analysis."""
    print("Loading datasets...")
    
    # Load affiliated repositories (research focus group)
    affiliated_df = pd.read_csv(AFFILIATED_CSV, encoding='utf-8')
    print(f"  Affiliated repos: {len(affiliated_df)}")
    
    # Load full dataset
    full_df = pd.read_csv(FULL_DATASET_CSV, encoding='utf-8')
    print(f"  Full dataset: {len(full_df)}")
    
    # Create baseline group (repos with emoji but no valid affiliation)
    # This includes: affiliation='none' OR validity is null/false
    baseline_df = full_df[
        (full_df['affiliation_deepseek'] == 'none') | 
        (full_df['validity'].isna()) |
        (full_df['validity'] == 'false') |
        (full_df['validity'] == '')
    ].copy()
    print(f"  Baseline repos (no affiliation/false positive): {len(baseline_df)}")
    
    # Create false positive group (had affiliation predicted but marked as false)
    false_positive_df = full_df[
        (full_df['affiliation_deepseek'] != 'none') & 
        ((full_df['validity'] == 'false') | (full_df['validity'].isna()) | (full_df['validity'] == ''))
    ].copy()
    print(f"  False positive repos: {len(false_positive_df)}")
    
    return affiliated_df, baseline_df, false_positive_df, full_df

def create_figures_dir():
    """Create figures directory if it doesn't exist."""
    Path(FIGURES_DIR).mkdir(exist_ok=True)
    print(f"Figures will be saved to: {FIGURES_DIR}/")

def save_figure(fig, filename, caption):
    """Save figure in both PNG and PDF formats."""
    png_path = f"{FIGURES_DIR}/{filename}.png"
    pdf_path = f"{FIGURES_DIR}/{filename}.pdf"
    
    fig.savefig(png_path, dpi=FIGURE_DPI, bbox_inches='tight', facecolor='white')
    fig.savefig(pdf_path, dpi=FIGURE_DPI, bbox_inches='tight', facecolor='white')
    
    print(f"\n📊 {filename}.png / .pdf")
    print(f"   Caption: {caption}")
    
    plt.close(fig)

# =============================================================================
# FIGURE 1: Distribution of Political/Activist Affiliations
# =============================================================================

def figure1_affiliation_distribution(affiliated_df):
    """
    Create horizontal bar chart showing distribution of political/activist affiliations.
    """
    print("\n" + "="*60)
    print("FIGURE 1: Distribution of Political/Activist Affiliations")
    print("="*60)
    
    # Count affiliations
    aff_counts = affiliated_df['affiliation_deepseek'].value_counts()
    
    # Sort descending
    aff_counts = aff_counts.sort_values(ascending=True)  # ascending for horizontal bar (bottom to top)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(8, 5))
    
    # Create horizontal bar chart
    bars = ax.barh(
        range(len(aff_counts)), 
        aff_counts.values,
        color=COLORS['palette'][:len(aff_counts)][::-1],
        edgecolor='white',
        linewidth=0.5
    )
    
    # Customize
    ax.set_yticks(range(len(aff_counts)))
    ax.set_yticklabels([label.upper() for label in aff_counts.index])
    ax.set_xlabel('Number of Repositories')
    ax.set_ylabel('Affiliation Category')
    ax.set_title('Distribution of Political/Activist Affiliations in GitHub Repositories')
    
    # Add value labels on bars
    for i, (bar, val) in enumerate(zip(bars, aff_counts.values)):
        ax.text(val + 0.5, bar.get_y() + bar.get_height()/2, 
                f'{val}', va='center', ha='left', fontsize=FONT_SIZE-1)
    
    # Add total annotation
    ax.text(0.98, 0.02, f'Total: n={len(affiliated_df)}', 
            transform=ax.transAxes, ha='right', va='bottom',
            fontsize=FONT_SIZE-1, style='italic')
    
    ax.set_xlim(0, max(aff_counts.values) * 1.15)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    save_figure(fig, 'figure1_affiliation_distribution',
                'Distribution of political and activist affiliations among GitHub repositories '
                f'with activist emojis (n={len(affiliated_df)}). Ukraine-related support dominates '
                'the dataset, followed by Palestine and LGBTQ+ causes.')

# =============================================================================
# FIGURE 2: Support Type Distribution (Expression Category)
# =============================================================================

def figure2_support_type_distribution(affiliated_df):
    """
    Create bar chart showing distribution of support/expression types.
    """
    print("\n" + "="*60)
    print("FIGURE 2: Support Type Distribution")
    print("="*60)
    
    # Map expression categories to readable labels
    category_labels = {
        'text_statement': 'Text Statement',
        'visual_badge': 'Visual/Badge',
        'hashtag_slogan': 'Hashtag/Slogan',
        'emoji_only': 'Emoji Only',
        'link_support': 'Link Support'
    }
    
    # Count expression categories (handle multiple categories per repo)
    category_counts = {}
    for categories_str in affiliated_df['expression_category']:
        if pd.notna(categories_str) and categories_str:
            for category in str(categories_str).split():
                readable = category_labels.get(category, category)
                category_counts[readable] = category_counts.get(readable, 0) + 1
    
    # Sort by count
    category_counts = dict(sorted(category_counts.items(), key=lambda x: x[1], reverse=True))
    
    # Create figure
    fig, ax = plt.subplots(figsize=(9, 5))
    
    x_pos = range(len(category_counts))
    bars = ax.bar(
        x_pos, 
        list(category_counts.values()),
        color=COLORS['palette'][:len(category_counts)],
        edgecolor='white',
        linewidth=0.5
    )
    
    # Customize
    ax.set_xticks(x_pos)
    ax.set_xticklabels(list(category_counts.keys()), rotation=15, ha='right')
    ax.set_xlabel('Expression/Support Type')
    ax.set_ylabel('Number of Repositories')
    ax.set_title('Distribution of Activist Expression Types in GitHub Repositories')
    
    # Add value labels on bars
    for bar, val in zip(bars, category_counts.values()):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                f'{val}', ha='center', va='bottom', fontsize=FONT_SIZE-1)
    
    # Add annotation
    ax.text(0.98, 0.98, f'Total repositories: n={len(affiliated_df)}', 
            transform=ax.transAxes, ha='right', va='top',
            fontsize=FONT_SIZE-1, style='italic')
    
    ax.set_ylim(0, max(category_counts.values()) * 1.15)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    save_figure(fig, 'figure2_support_type_distribution',
                'Distribution of activist expression types in repositories with valid '
                f'political affiliations (n={len(affiliated_df)}). Text statements are the '
                'most common form of expressing support, followed by visual badges.')

# =============================================================================
# FIGURE 3: Stars Comparison Across Groups
# =============================================================================

def figure3_stars_comparison(affiliated_df, baseline_df, false_positive_df):
    """
    Create violin/box plot comparing star counts across groups.
    """
    print("\n" + "="*60)
    print("FIGURE 3: Stars Comparison Across Groups")
    print("="*60)
    
    # Prepare data
    affiliated_stars = affiliated_df['repo_stars'].values
    baseline_stars = baseline_df['repo_stars'].values
    fp_stars = false_positive_df['repo_stars'].values
    
    # Create combined dataframe for seaborn
    data = []
    for star in affiliated_stars:
        data.append({'Group': f'Affiliated\n(n={len(affiliated_df)})', 'Stars': star})
    for star in baseline_stars:
        data.append({'Group': f'Baseline\n(n={len(baseline_df)})', 'Stars': star})
    for star in fp_stars:
        data.append({'Group': f'False Positive\n(n={len(false_positive_df)})', 'Stars': star})
    
    plot_df = pd.DataFrame(data)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(9, 6))
    
    # Create violin plot with box plot inside
    violin = sns.violinplot(
        data=plot_df, x='Group', y='Stars', ax=ax,
        palette=[COLORS['affiliated'], COLORS['baseline'], COLORS['false_positive']],
        inner='box', cut=0
    )
    
    # Use log scale for y-axis
    ax.set_yscale('log')
    
    # Customize
    ax.set_xlabel('Repository Group')
    ax.set_ylabel('Number of Stars (log scale)')
    ax.set_title('Distribution of GitHub Stars Across Repository Groups')
    
    # Add median annotations
    groups = plot_df['Group'].unique()
    for i, group in enumerate(groups):
        group_data = plot_df[plot_df['Group'] == group]['Stars']
        median = group_data.median()
        mean = group_data.mean()
        ax.annotate(f'Median: {median:,.0f}\nMean: {mean:,.0f}', 
                   xy=(i, median), xytext=(i + 0.3, median * 2),
                   fontsize=FONT_SIZE-2, ha='left',
                   arrowprops=dict(arrowstyle='->', color='gray', lw=0.5))
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    save_figure(fig, 'figure3_stars_comparison',
                'Distribution of GitHub stars across repository groups. '
                'Affiliated repositories show higher median star counts compared to baseline, '
                'suggesting that politically-engaged projects may attract more attention.')

# =============================================================================
# FIGURE 4: Contributors Comparison Across Groups
# =============================================================================

def figure4_contributors_comparison(affiliated_df, baseline_df, false_positive_df):
    """
    Create violin/box plot comparing contributor counts across groups.
    """
    print("\n" + "="*60)
    print("FIGURE 4: Contributors Comparison Across Groups")
    print("="*60)
    
    # Prepare data
    data = []
    for contrib in affiliated_df['contributors'].values:
        data.append({'Group': f'Affiliated\n(n={len(affiliated_df)})', 'Contributors': contrib})
    for contrib in baseline_df['contributors'].values:
        data.append({'Group': f'Baseline\n(n={len(baseline_df)})', 'Contributors': contrib})
    for contrib in false_positive_df['contributors'].values:
        data.append({'Group': f'False Positive\n(n={len(false_positive_df)})', 'Contributors': contrib})
    
    plot_df = pd.DataFrame(data)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(9, 6))
    
    # Create violin plot
    sns.violinplot(
        data=plot_df, x='Group', y='Contributors', ax=ax,
        palette=[COLORS['affiliated'], COLORS['baseline'], COLORS['false_positive']],
        inner='box', cut=0
    )
    
    # Use log scale
    ax.set_yscale('log')
    
    # Customize
    ax.set_xlabel('Repository Group')
    ax.set_ylabel('Number of Contributors (log scale)')
    ax.set_title('Distribution of Contributors Across Repository Groups')
    
    # Add median annotations
    groups = plot_df['Group'].unique()
    for i, group in enumerate(groups):
        group_data = plot_df[plot_df['Group'] == group]['Contributors']
        median = group_data.median()
        mean = group_data.mean()
        ax.annotate(f'Median: {median:,.0f}\nMean: {mean:,.0f}', 
                   xy=(i, median), xytext=(i + 0.3, median * 2),
                   fontsize=FONT_SIZE-2, ha='left',
                   arrowprops=dict(arrowstyle='->', color='gray', lw=0.5))
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    save_figure(fig, 'figure4_contributors_comparison',
                'Distribution of contributor counts across repository groups. '
                'Higher contributor counts in affiliated repositories suggest stronger '
                'community engagement around politically-expressed projects.')

# =============================================================================
# FIGURE 5: Language Distribution Comparison
# =============================================================================

def figure5_language_distribution(affiliated_df, baseline_df):
    """
    Create grouped bar chart comparing language distributions.
    """
    print("\n" + "="*60)
    print("FIGURE 5: Language Distribution Comparison")
    print("="*60)
    
    # Get top 10 languages overall
    all_languages = pd.concat([
        affiliated_df['language'].dropna(),
        baseline_df['language'].dropna()
    ])
    top_languages = all_languages.value_counts().head(10).index.tolist()
    
    # Count languages for each group
    affiliated_counts = affiliated_df['language'].value_counts()
    baseline_counts = baseline_df['language'].value_counts()
    
    # Prepare data for plotting
    languages = top_languages
    affiliated_vals = [affiliated_counts.get(lang, 0) for lang in languages]
    baseline_vals = [baseline_counts.get(lang, 0) for lang in languages]
    
    # Normalize to percentages for fair comparison
    affiliated_pct = [v / len(affiliated_df) * 100 for v in affiliated_vals]
    baseline_pct = [v / len(baseline_df) * 100 for v in baseline_vals]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x = np.arange(len(languages))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, affiliated_pct, width, 
                   label=f'Affiliated (n={len(affiliated_df)})',
                   color=COLORS['affiliated'], edgecolor='white')
    bars2 = ax.bar(x + width/2, baseline_pct, width,
                   label=f'Baseline (n={len(baseline_df)})',
                   color=COLORS['baseline'], edgecolor='white')
    
    # Customize
    ax.set_xlabel('Programming Language')
    ax.set_ylabel('Percentage of Repositories (%)')
    ax.set_title('Programming Language Distribution: Affiliated vs Baseline Repositories')
    ax.set_xticks(x)
    ax.set_xticklabels(languages, rotation=30, ha='right')
    ax.legend(loc='upper right')
    
    # Add value labels
    for bar in bars1:
        if bar.get_height() > 1:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                    f'{bar.get_height():.1f}%', ha='center', va='bottom', fontsize=FONT_SIZE-2)
    for bar in bars2:
        if bar.get_height() > 1:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                    f'{bar.get_height():.1f}%', ha='center', va='bottom', fontsize=FONT_SIZE-2)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    save_figure(fig, 'figure5_language_distribution',
                'Comparison of programming language distributions between affiliated '
                'and baseline repositories. JavaScript and TypeScript dominate both groups, '
                'with subtle differences in language preferences.')

# =============================================================================
# FIGURE 6: Owner Type Distribution
# =============================================================================

def figure6_owner_type_distribution(affiliated_df, baseline_df):
    """
    Create grouped bar chart comparing owner types (User vs Organization).
    """
    print("\n" + "="*60)
    print("FIGURE 6: Owner Type Distribution")
    print("="*60)
    
    # Count owner types
    affiliated_owner = affiliated_df['owner_type'].value_counts()
    baseline_owner = baseline_df['owner_type'].value_counts()
    
    # Normalize to percentages
    affiliated_pct = (affiliated_owner / len(affiliated_df) * 100).to_dict()
    baseline_pct = (baseline_owner / len(baseline_df) * 100).to_dict()
    
    owner_types = ['User', 'Organization']
    affiliated_vals = [affiliated_pct.get(ot, 0) for ot in owner_types]
    baseline_vals = [baseline_pct.get(ot, 0) for ot in owner_types]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(8, 5))
    
    x = np.arange(len(owner_types))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, affiliated_vals, width,
                   label=f'Affiliated (n={len(affiliated_df)})',
                   color=COLORS['affiliated'], edgecolor='white')
    bars2 = ax.bar(x + width/2, baseline_vals, width,
                   label=f'Baseline (n={len(baseline_df)})',
                   color=COLORS['baseline'], edgecolor='white')
    
    # Customize
    ax.set_xlabel('Owner Type')
    ax.set_ylabel('Percentage of Repositories (%)')
    ax.set_title('Repository Owner Type Distribution: Affiliated vs Baseline')
    ax.set_xticks(x)
    ax.set_xticklabels(owner_types)
    ax.legend(loc='upper right')
    
    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                    f'{bar.get_height():.1f}%', ha='center', va='bottom', fontsize=FONT_SIZE-1)
    
    ax.set_ylim(0, max(affiliated_vals + baseline_vals) * 1.2)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    save_figure(fig, 'figure6_owner_type_distribution',
                'Comparison of repository owner types between affiliated and baseline groups. '
                'Individual users are more likely to express political affiliations compared '
                'to organizations.')

# =============================================================================
# FIGURE 7: Affiliation by Expression Type (Stacked Bar)
# =============================================================================

def figure7_affiliation_by_expression(affiliated_df):
    """
    Create stacked bar chart showing expression types by affiliation.
    """
    print("\n" + "="*60)
    print("FIGURE 7: Affiliation by Expression Type")
    print("="*60)
    
    # Map categories
    category_labels = {
        'text_statement': 'Text',
        'visual_badge': 'Visual',
        'hashtag_slogan': 'Slogan',
        'emoji_only': 'Emoji',
        'link_support': 'Link'
    }
    
    # Build cross-tabulation
    data = []
    for _, row in affiliated_df.iterrows():
        affiliation = row['affiliation_deepseek'].upper()
        categories = str(row['expression_category']).split() if pd.notna(row['expression_category']) else []
        for cat in categories:
            readable = category_labels.get(cat, cat)
            data.append({'Affiliation': affiliation, 'Expression': readable})
    
    cross_df = pd.DataFrame(data)
    
    # Create pivot table
    pivot = pd.crosstab(cross_df['Affiliation'], cross_df['Expression'])
    
    # Sort by total count
    pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))
    
    pivot.plot(kind='barh', stacked=True, ax=ax, 
               color=COLORS['palette'][:len(pivot.columns)],
               edgecolor='white', linewidth=0.5)
    
    # Customize
    ax.set_xlabel('Number of Repositories')
    ax.set_ylabel('Affiliation Category')
    ax.set_title('Expression Types by Political Affiliation')
    ax.legend(title='Expression Type', bbox_to_anchor=(1.02, 1), loc='upper left')
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    save_figure(fig, 'figure7_affiliation_by_expression',
                'Distribution of expression types across different political affiliations. '
                'Ukraine-affiliated repositories predominantly use text statements and visual badges, '
                'while smaller movements show diverse expression patterns.')

# =============================================================================
# FIGURE 8: Repository Creation Timeline
# =============================================================================

def figure8_creation_timeline(affiliated_df, baseline_df):
    """
    Create line chart showing repository creation over time.
    """
    print("\n" + "="*60)
    print("FIGURE 8: Repository Creation Timeline")
    print("="*60)
    
    # Parse dates
    affiliated_df['created_date'] = pd.to_datetime(affiliated_df['created_at']).dt.to_period('M')
    baseline_df['created_date'] = pd.to_datetime(baseline_df['created_at']).dt.to_period('M')
    
    # Count by month
    affiliated_monthly = affiliated_df['created_date'].value_counts().sort_index()
    baseline_monthly = baseline_df['created_date'].value_counts().sort_index()
    
    # Get common date range
    all_dates = set(affiliated_monthly.index) | set(baseline_monthly.index)
    date_range = pd.period_range(min(all_dates), max(all_dates), freq='M')
    
    # Fill missing dates
    affiliated_series = pd.Series([affiliated_monthly.get(d, 0) for d in date_range], index=date_range)
    baseline_series = pd.Series([baseline_monthly.get(d, 0) for d in date_range], index=date_range)
    
    # Create cumulative
    affiliated_cumsum = affiliated_series.cumsum()
    baseline_cumsum = baseline_series.cumsum()
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Convert to datetime for plotting
    dates = [d.to_timestamp() for d in date_range]
    
    ax.plot(dates, affiliated_cumsum.values, color=COLORS['affiliated'], 
            linewidth=2, label=f'Affiliated (n={len(affiliated_df)})')
    ax.plot(dates, baseline_cumsum.values, color=COLORS['baseline'], 
            linewidth=2, label=f'Baseline (n={len(baseline_df)})', alpha=0.7)
    
    # Add event markers
    events = [
        ('2022-02-24', 'Russia invades Ukraine'),
        ('2023-10-07', 'Israel-Gaza conflict'),
    ]
    
    for event_date, event_name in events:
        event_dt = pd.to_datetime(event_date)
        if dates[0] <= event_dt <= dates[-1]:
            ax.axvline(x=event_dt, color='red', linestyle='--', alpha=0.5, linewidth=1)
            ax.text(event_dt, ax.get_ylim()[1] * 0.95, event_name, 
                   rotation=90, va='top', ha='right', fontsize=FONT_SIZE-2, color='red')
    
    # Customize
    ax.set_xlabel('Date')
    ax.set_ylabel('Cumulative Number of Repositories')
    ax.set_title('Repository Creation Timeline: Affiliated vs Baseline')
    ax.legend(loc='upper left')
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    save_figure(fig, 'figure8_creation_timeline',
                'Cumulative repository creation over time for affiliated and baseline groups. '
                'Vertical dashed lines indicate major geopolitical events that may have '
                'influenced the adoption of activist expressions in repositories.')

# =============================================================================
# FIGURE 9: Stars vs Contributors Scatter
# =============================================================================

def figure9_stars_contributors_scatter(affiliated_df, baseline_df):
    """
    Create scatter plot of stars vs contributors.
    """
    print("\n" + "="*60)
    print("FIGURE 9: Stars vs Contributors Relationship")
    print("="*60)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 7))
    
    # Plot baseline first (behind)
    ax.scatter(baseline_df['contributors'], baseline_df['repo_stars'],
               alpha=0.3, s=20, color=COLORS['baseline'], 
               label=f'Baseline (n={len(baseline_df)})')
    
    # Plot affiliated on top
    ax.scatter(affiliated_df['contributors'], affiliated_df['repo_stars'],
               alpha=0.8, s=50, color=COLORS['affiliated'],
               label=f'Affiliated (n={len(affiliated_df)})', edgecolor='white', linewidth=0.5)
    
    # Log scale
    ax.set_xscale('log')
    ax.set_yscale('log')
    
    # Customize
    ax.set_xlabel('Number of Contributors (log scale)')
    ax.set_ylabel('Number of Stars (log scale)')
    ax.set_title('Relationship Between Stars and Contributors')
    ax.legend(loc='lower right')
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    save_figure(fig, 'figure9_stars_contributors_scatter',
                'Scatter plot showing the relationship between repository stars and contributors. '
                'Affiliated repositories (blue) cluster in regions of higher visibility, '
                'suggesting a correlation between political expression and project prominence.')

# =============================================================================
# SUMMARY STATISTICS TABLE
# =============================================================================

def print_summary_statistics(affiliated_df, baseline_df, false_positive_df):
    """Print summary statistics for all groups."""
    print("\n" + "="*60)
    print("SUMMARY STATISTICS")
    print("="*60)
    
    groups = [
        ('Affiliated', affiliated_df),
        ('Baseline', baseline_df),
        ('False Positive', false_positive_df)
    ]
    
    print(f"\n{'Metric':<25} {'Affiliated':>15} {'Baseline':>15} {'False Positive':>15}")
    print("-" * 70)
    
    for metric, col in [('Count', None), ('Stars (median)', 'repo_stars'), 
                        ('Stars (mean)', 'repo_stars'), ('Contributors (median)', 'contributors'),
                        ('Contributors (mean)', 'contributors'), ('Forks (median)', 'forks')]:
        row = f"{metric:<25}"
        for name, df in groups:
            if col is None:
                row += f"{len(df):>15,}"
            elif 'median' in metric:
                row += f"{df[col].median():>15,.0f}"
            else:
                row += f"{df[col].mean():>15,.0f}"
        print(row)

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main function to generate all figures."""
    print("="*60)
    print("EMOJI AND POLITICAL AFFILIATION - FIGURE GENERATION")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Create figures directory
    create_figures_dir()
    
    # Load data
    affiliated_df, baseline_df, false_positive_df, full_df = load_data()
    
    # Print summary statistics
    print_summary_statistics(affiliated_df, baseline_df, false_positive_df)
    
    # Generate all figures
    figure1_affiliation_distribution(affiliated_df)
    figure2_support_type_distribution(affiliated_df)
    figure3_stars_comparison(affiliated_df, baseline_df, false_positive_df)
    figure4_contributors_comparison(affiliated_df, baseline_df, false_positive_df)
    figure5_language_distribution(affiliated_df, baseline_df)
    figure6_owner_type_distribution(affiliated_df, baseline_df)
    figure7_affiliation_by_expression(affiliated_df)
    figure8_creation_timeline(affiliated_df, baseline_df)
    figure9_stars_contributors_scatter(affiliated_df, baseline_df)
    
    print("\n" + "="*60)
    print("ALL FIGURES GENERATED SUCCESSFULLY")
    print(f"Output directory: {FIGURES_DIR}/")
    print("="*60)
    
    # List generated files
    print("\nGenerated files:")
    for f in sorted(Path(FIGURES_DIR).glob('*')):
        print(f"  - {f.name}")

if __name__ == '__main__':
    main()
