#!/usr/bin/env python3
"""
8_Results.py - Generate Complete Research Results for RQ1, RQ2, RQ3

This script produces publication-ready results paragraphs with actual statistics
from the dataset, following the template structure from ChatGPT suggestions.

Output:
- FINAL/Research_Results.md (Markdown format)
- FINAL/Research_Results.pdf (PDF format via markdown conversion)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from scipy import stats
import shutil
import sys

# Import enhanced report generator
from enhanced_report_generator import generate_comprehensive_report

# =============================================================================
# CONFIGURATION
# =============================================================================

AFFILIATED_CSV = "FinalDataset/7_expression_category_labeled.csv"
FULL_DATASET_CSV = "FinalDataset/validity_checked_affiliated_deepseek_1000_200000.csv"
FIGURES_DIR = "figures"
OUTPUT_DIR = "FINAL"

# Expression category mapping
EXPRESSION_LABELS = {
    'text_statement': 'Text Statement',
    'visual_badge': 'Visual/Badge',
    'hashtag_slogan': 'Hashtag/Slogan',
    'emoji_only': 'Emoji Only',
    'link_support': 'Link Support'
}

# =============================================================================
# DATA LOADING
# =============================================================================

def load_data():
    """Load all datasets for analysis."""
    print("Loading datasets...")
    
    # Affiliated (validated activist repos)
    affiliated_df = pd.read_csv(AFFILIATED_CSV, encoding='utf-8')
    
    # Full dataset
    full_df = pd.read_csv(FULL_DATASET_CSV, encoding='utf-8')
    
    # Baseline: repos with emoji but no valid affiliation
    baseline_df = full_df[
        (full_df['affiliation_deepseek'] == 'none') | 
        (full_df['validity'].isna()) |
        (full_df['validity'] == 'false') |
        (full_df['validity'] == '')
    ].copy()
    
    # False positives: had affiliation predicted but marked as false/invalid
    false_positive_df = full_df[
        (full_df['affiliation_deepseek'] != 'none') & 
        ((full_df['validity'] == 'false') | (full_df['validity'].isna()) | (full_df['validity'] == ''))
    ].copy()
    
    print(f"  Affiliated repos: {len(affiliated_df)}")
    print(f"  Full dataset: {len(full_df)}")
    print(f"  Baseline repos: {len(baseline_df)}")
    print(f"  False positive repos: {len(false_positive_df)}")
    
    return affiliated_df, baseline_df, false_positive_df, full_df

# =============================================================================
# STATISTICAL ANALYSIS
# =============================================================================

def compute_rq1_statistics(affiliated_df, full_df):
    """Compute statistics for RQ1: Types of repositories with political emojis."""
    stats_dict = {}
    
    # Total counts
    stats_dict['n_affiliated'] = len(affiliated_df)
    stats_dict['n_total_emoji'] = len(full_df)
    stats_dict['pct_affiliated'] = (len(affiliated_df) / len(full_df)) * 100
    
    # Affiliation distribution
    aff_counts = affiliated_df['affiliation_deepseek'].value_counts()
    stats_dict['affiliations'] = []
    for aff, count in aff_counts.items():
        pct = (count / len(affiliated_df)) * 100
        stats_dict['affiliations'].append({
            'name': aff.upper(),
            'count': count,
            'percentage': pct
        })
    
    # Top languages (all)
    lang_counts = affiliated_df['language'].value_counts()
    stats_dict['top_languages'] = []
    for lang, count in lang_counts.items():
        pct = (count / len(affiliated_df)) * 100
        stats_dict['top_languages'].append({
            'name': lang if pd.notna(lang) else 'N/A',
            'count': count,
            'percentage': pct
        })
    
    # Owner type distribution
    owner_counts = affiliated_df['owner_type'].value_counts()
    stats_dict['owner_types'] = {}
    for owner, count in owner_counts.items():
        stats_dict['owner_types'][owner] = {
            'count': count,
            'percentage': (count / len(affiliated_df)) * 100
        }
    
    # Total stars in affiliated repos
    stats_dict['total_stars'] = affiliated_df['repo_stars'].sum()
    stats_dict['avg_stars'] = affiliated_df['repo_stars'].mean()
    stats_dict['median_stars'] = affiliated_df['repo_stars'].median()
    stats_dict['max_stars'] = affiliated_df['repo_stars'].max()
    
    # Top repositories by stars
    top_repos = affiliated_df.nlargest(10, 'repo_stars')[['repo_owner', 'repo_name', 'repo_stars', 'affiliation_deepseek', 'language']].to_dict('records')
    stats_dict['top_repos'] = top_repos
    
    # Emoji usage analysis
    emoji_counts = {}
    for emojis_str in affiliated_df['found_emojis']:
        if pd.notna(emojis_str):
            for emoji in str(emojis_str).split():
                emoji_counts[emoji] = emoji_counts.get(emoji, 0) + 1
    stats_dict['emoji_usage'] = sorted(emoji_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Creation timeline
    try:
        affiliated_df['created_year'] = pd.to_datetime(affiliated_df['created_at']).dt.year
        year_counts = affiliated_df['created_year'].value_counts().sort_index().to_dict()
        stats_dict['creation_by_year'] = year_counts
    except:
        stats_dict['creation_by_year'] = {}
    
    return stats_dict

def compute_rq2_statistics(affiliated_df, full_df):
    """Compute statistics for RQ2: Expression types and false positives."""
    stats_dict = {}
    
    # Count expression categories
    category_counts = {}
    for categories_str in affiliated_df['expression_category']:
        if pd.notna(categories_str) and categories_str:
            for category in str(categories_str).split():
                readable = EXPRESSION_LABELS.get(category, category)
                category_counts[readable] = category_counts.get(readable, 0) + 1
    
    # Sort by count
    sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
    stats_dict['expression_types'] = []
    for cat, count in sorted_categories:
        pct = (count / len(affiliated_df)) * 100
        stats_dict['expression_types'].append({
            'name': cat,
            'count': count,
            'percentage': pct
        })
    
    # Emoji-only stats
    emoji_only_count = category_counts.get('Emoji Only', 0)
    stats_dict['emoji_only_count'] = emoji_only_count
    stats_dict['emoji_only_pct'] = (emoji_only_count / len(affiliated_df)) * 100
    
    # False positive analysis
    # Repos with predicted affiliation but not validated as true
    all_predicted = full_df[full_df['affiliation_deepseek'] != 'none']
    validated = affiliated_df  # These are the truly affiliated
    
    stats_dict['n_predicted'] = len(all_predicted)
    stats_dict['n_validated'] = len(validated)
    stats_dict['n_false_positive'] = len(all_predicted) - len(validated)
    stats_dict['false_positive_rate'] = ((len(all_predicted) - len(validated)) / len(all_predicted)) * 100 if len(all_predicted) > 0 else 0
    
    # Overall signal strength
    stats_dict['n_total_emoji_repos'] = len(full_df)
    stats_dict['true_activist_rate'] = (len(validated) / len(full_df)) * 100
    
    # Multi-expression analysis
    multi_count = 0
    single_count = 0
    category_combos = {}
    for categories_str in affiliated_df['expression_category']:
        if pd.notna(categories_str) and categories_str:
            cats = str(categories_str).split()
            if len(cats) > 1:
                multi_count += 1
                combo_key = ' + '.join(sorted([EXPRESSION_LABELS.get(c, c) for c in cats]))
                category_combos[combo_key] = category_combos.get(combo_key, 0) + 1
            else:
                single_count += 1
    
    stats_dict['multi_expression_count'] = multi_count
    stats_dict['multi_expression_pct'] = (multi_count / len(affiliated_df)) * 100
    stats_dict['single_expression_count'] = single_count
    stats_dict['category_combinations'] = sorted(category_combos.items(), key=lambda x: x[1], reverse=True)
    
    # Expression by affiliation
    expr_by_aff = {}
    for _, row in affiliated_df.iterrows():
        aff = row['affiliation_deepseek'].upper()
        if aff not in expr_by_aff:
            expr_by_aff[aff] = {}
        if pd.notna(row['expression_category']) and row['expression_category']:
            for cat in str(row['expression_category']).split():
                readable = EXPRESSION_LABELS.get(cat, cat)
                expr_by_aff[aff][readable] = expr_by_aff[aff].get(readable, 0) + 1
    stats_dict['expression_by_affiliation'] = expr_by_aff
    
    # Validity breakdown (explicit vs implicit)
    validity_counts = affiliated_df['validity'].value_counts().to_dict()
    stats_dict['explicit_count'] = validity_counts.get('EXPLICIT', 0) + validity_counts.get('explicit', 0)
    stats_dict['implicit_count'] = validity_counts.get('IMPLICIT', 0) + validity_counts.get('implicit', 0)
    stats_dict['explicit_pct'] = (stats_dict['explicit_count'] / len(affiliated_df)) * 100
    stats_dict['implicit_pct'] = (stats_dict['implicit_count'] / len(affiliated_df)) * 100
    
    return stats_dict

def compute_rq3_statistics(affiliated_df, baseline_df, false_positive_df):
    """Compute statistics for RQ3: Repository characteristics comparison."""
    stats_dict = {}
    
    # Stars comparison
    stats_dict['stars'] = {
        'affiliated': {
            'median': affiliated_df['repo_stars'].median(),
            'mean': affiliated_df['repo_stars'].mean(),
            'std': affiliated_df['repo_stars'].std(),
            'min': affiliated_df['repo_stars'].min(),
            'max': affiliated_df['repo_stars'].max()
        },
        'baseline': {
            'median': baseline_df['repo_stars'].median(),
            'mean': baseline_df['repo_stars'].mean(),
            'std': baseline_df['repo_stars'].std(),
            'min': baseline_df['repo_stars'].min(),
            'max': baseline_df['repo_stars'].max()
        },
        'false_positive': {
            'median': false_positive_df['repo_stars'].median(),
            'mean': false_positive_df['repo_stars'].mean(),
            'std': false_positive_df['repo_stars'].std(),
            'min': false_positive_df['repo_stars'].min(),
            'max': false_positive_df['repo_stars'].max()
        }
    }
    
    # Mann-Whitney U test for stars
    stat, p_value = stats.mannwhitneyu(
        affiliated_df['repo_stars'], 
        baseline_df['repo_stars'],
        alternative='two-sided'
    )
    stats_dict['stars_test'] = {
        'statistic': stat,
        'p_value': p_value,
        'significant': p_value < 0.05
    }
    
    # Contributors comparison
    stats_dict['contributors'] = {
        'affiliated': {
            'median': affiliated_df['contributors'].median(),
            'mean': affiliated_df['contributors'].mean(),
            'std': affiliated_df['contributors'].std()
        },
        'baseline': {
            'median': baseline_df['contributors'].median(),
            'mean': baseline_df['contributors'].mean(),
            'std': baseline_df['contributors'].std()
        },
        'false_positive': {
            'median': false_positive_df['contributors'].median(),
            'mean': false_positive_df['contributors'].mean(),
            'std': false_positive_df['contributors'].std()
        }
    }
    
    # Mann-Whitney U test for contributors
    stat, p_value = stats.mannwhitneyu(
        affiliated_df['contributors'], 
        baseline_df['contributors'],
        alternative='two-sided'
    )
    stats_dict['contributors_test'] = {
        'statistic': stat,
        'p_value': p_value,
        'significant': p_value < 0.05
    }
    
    # Owner type comparison
    aff_org_pct = (affiliated_df['owner_type'] == 'Organization').sum() / len(affiliated_df) * 100
    base_org_pct = (baseline_df['owner_type'] == 'Organization').sum() / len(baseline_df) * 100
    fp_org_pct = (false_positive_df['owner_type'] == 'Organization').sum() / len(false_positive_df) * 100
    
    stats_dict['org_percentage'] = {
        'affiliated': aff_org_pct,
        'baseline': base_org_pct,
        'false_positive': fp_org_pct
    }
    
    # Language comparison
    stats_dict['languages'] = {
        'affiliated': affiliated_df['language'].value_counts().head(5).to_dict(),
        'baseline': baseline_df['language'].value_counts().head(5).to_dict()
    }
    
    # Sample sizes
    stats_dict['n_affiliated'] = len(affiliated_df)
    stats_dict['n_baseline'] = len(baseline_df)
    stats_dict['n_false_positive'] = len(false_positive_df)
    
    return stats_dict

# =============================================================================
# MARKDOWN GENERATION
# =============================================================================

def generate_markdown_report(rq1_stats, rq2_stats, rq3_stats, affiliated_df):
    """Generate the complete markdown research results report."""
    
    md = []
    
    # Header
    md.append("# Research Results: Emoji and Political Affiliation in GitHub Repositories")
    md.append("")
    md.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md.append("")
    md.append("---")
    md.append("")
    
    # Executive Summary
    md.append("## Executive Summary")
    md.append("")
    md.append(f"This study analyzed **{rq1_stats['n_total_emoji']:,}** GitHub repositories containing political or activist emojis. ")
    md.append(f"Through manual validation, we identified **{rq1_stats['n_affiliated']}** repositories ({rq1_stats['pct_affiliated']:.2f}%) ")
    md.append("with genuine political or activist affiliations. The following sections present detailed findings for each research question.")
    md.append("")
    md.append("---")
    md.append("")
    
    # ==========================================================================
    # RQ1 RESULTS
    # ==========================================================================
    md.append("## RQ1: What kinds of GitHub repositories use politically meaningful emojis?")
    md.append("")
    
    # Main paragraph
    top3 = rq1_stats['affiliations'][:3]
    top_langs = rq1_stats['top_languages'][:3]
    
    md.append(f"Among the {rq1_stats['n_total_emoji']:,} popular repositories that contain at least one political or activist emoji, ")
    md.append(f"we identified **{rq1_stats['n_affiliated']} repositories** with a clearly validated activist affiliation ")
    md.append(f"(approximately **{rq1_stats['pct_affiliated']:.2f}%** of all emoji-bearing repositories). ")
    md.append(f"The most common affiliations were **{top3[0]['name']}** (n={top3[0]['count']}, {top3[0]['percentage']:.1f}%), ")
    md.append(f"followed by **{top3[1]['name']}** (n={top3[1]['count']}, {top3[1]['percentage']:.1f}%) ")
    md.append(f"and **{top3[2]['name']}** (n={top3[2]['count']}, {top3[2]['percentage']:.1f}%). ")
    md.append(f"In terms of programming languages, these repositories are primarily written in ")
    md.append(f"**{top_langs[0]['name']}** ({top_langs[0]['percentage']:.1f}%), ")
    md.append(f"**{top_langs[1]['name']}** ({top_langs[1]['percentage']:.1f}%), and ")
    md.append(f"**{top_langs[2]['name']}** ({top_langs[2]['percentage']:.1f}%). ")
    md.append("Overall, this shows that political emoji signaling appears primarily in established, ")
    md.append("high-visibility technical projects rather than in small or niche repositories.")
    md.append("")
    
    # Affiliation table
    md.append("### Distribution of Political Affiliations")
    md.append("")
    md.append("| Affiliation | Count | Percentage |")
    md.append("|-------------|-------|------------|")
    for aff in rq1_stats['affiliations']:
        md.append(f"| {aff['name']} | {aff['count']} | {aff['percentage']:.1f}% |")
    md.append("")
    
    # Owner type
    md.append("### Repository Ownership")
    md.append("")
    user_stats = rq1_stats['owner_types'].get('User', {'count': 0, 'percentage': 0})
    org_stats = rq1_stats['owner_types'].get('Organization', {'count': 0, 'percentage': 0})
    md.append(f"- **Individual Users:** {user_stats['count']} repositories ({user_stats['percentage']:.1f}%)")
    md.append(f"- **Organizations:** {org_stats['count']} repositories ({org_stats['percentage']:.1f}%)")
    md.append("")
    
    # Figure reference
    md.append("### Associated Figures")
    md.append("")
    md.append("**Figure 1: Distribution of Political/Activist Affiliations**")
    md.append("")
    md.append("![Figure 1](../figures/figure1_affiliation_distribution.png)")
    md.append("")
    md.append(f"*Figure 1. Distribution of activist affiliations among the {rq1_stats['n_affiliated']} validated repositories. ")
    md.append("The plot shows how many repositories explicitly support each movement (Ukraine, Palestine, LGBTQ+, BLM, Climate, etc.) ")
    md.append("among popular GitHub projects that use political emojis.*")
    md.append("")
    
    md.append("---")
    md.append("")
    
    # ==========================================================================
    # RQ2 RESULTS
    # ==========================================================================
    md.append("## RQ2: How do these repositories express political or activist support, and how many cases are false positives?")
    md.append("")
    
    # Main paragraph
    top2_expr = rq2_stats['expression_types'][:2]
    
    md.append("We classified the way each repository expresses support into five categories: ")
    md.append("**text statements**, **link-based support**, **slogans or hashtags**, **visual banners/badges**, and **emoji-only**. ")
    md.append(f"Among the {rq2_stats['n_validated']} validated activist repositories, the most common support type was ")
    md.append(f"**{top2_expr[0]['name']}** (n={top2_expr[0]['count']}, {top2_expr[0]['percentage']:.1f}%), ")
    md.append(f"followed by **{top2_expr[1]['name']}** (n={top2_expr[1]['count']}, {top2_expr[1]['percentage']:.1f}%). ")
    md.append(f"Emoji-only signals were relatively rare, with only **{rq2_stats['emoji_only_count']} repositories** ")
    md.append(f"({rq2_stats['emoji_only_pct']:.1f}%) relying solely on activist emojis without any supporting text, link, or image.")
    md.append("")
    
    # False positive analysis
    md.append("### False Positive Analysis")
    md.append("")
    md.append(f"When considering all {rq2_stats['n_total_emoji_repos']:,} repositories that contain political emojis, ")
    md.append(f"only **{rq2_stats['n_validated']}** (approximately **{rq2_stats['true_activist_rate']:.2f}%**) were confirmed as truly activist. ")
    md.append(f"Among the {rq2_stats['n_predicted']} repositories where our AI classifier predicted a political affiliation, ")
    md.append(f"**{rq2_stats['n_false_positive']}** ({rq2_stats['false_positive_rate']:.1f}%) turned out to be false positives ")
    md.append("where emojis were used decoratively or with unrelated meanings. ")
    md.append("This indicates that political emojis in popular GitHub repositories are a **weak but non-random signal** ")
    md.append("of activist content, and their meaning must be interpreted in context rather than from emoji presence alone.")
    md.append("")
    
    # Expression types table
    md.append("### Expression Type Distribution")
    md.append("")
    md.append("| Expression Type | Count | Percentage |")
    md.append("|-----------------|-------|------------|")
    for expr in rq2_stats['expression_types']:
        md.append(f"| {expr['name']} | {expr['count']} | {expr['percentage']:.1f}% |")
    md.append("")
    
    # Figure reference
    md.append("### Associated Figures")
    md.append("")
    md.append("**Figure 2: Support Type Distribution**")
    md.append("")
    md.append("![Figure 2](../figures/figure2_support_type_distribution.png)")
    md.append("")
    md.append(f"*Figure 2. Support types used by activist-affiliated repositories. Bars show the number of repositories ")
    md.append("that express support through text statements, visual badges, slogans/hashtags, emoji-only signals, and links. ")
    md.append("This illustrates how often emojis are accompanied by explicit activist content.*")
    md.append("")
    
    md.append("**Figure 7: Affiliation by Expression Type**")
    md.append("")
    md.append("![Figure 7](../figures/figure7_affiliation_by_expression.png)")
    md.append("")
    md.append("*Figure 7. Distribution of expression types across different political affiliations. ")
    md.append("Ukraine-affiliated repositories predominantly use text statements and visual badges, ")
    md.append("while smaller movements show diverse expression patterns.*")
    md.append("")
    
    md.append("---")
    md.append("")
    
    # ==========================================================================
    # RQ3 RESULTS
    # ==========================================================================
    md.append("## RQ3: What are the characteristics of these repositories and their contributors?")
    md.append("")
    
    # Main paragraph
    aff_stars = rq3_stats['stars']['affiliated']
    base_stars = rq3_stats['stars']['baseline']
    aff_contrib = rq3_stats['contributors']['affiliated']
    base_contrib = rq3_stats['contributors']['baseline']
    
    stars_diff = "higher" if aff_stars['median'] > base_stars['median'] else "lower"
    contrib_diff = "higher" if aff_contrib['median'] > base_contrib['median'] else "lower"
    stars_sig = "statistically significant" if rq3_stats['stars_test']['significant'] else "not statistically significant"
    contrib_sig = "statistically significant" if rq3_stats['contributors_test']['significant'] else "not statistically significant"
    
    md.append(f"We compared the {rq3_stats['n_affiliated']} activist-affiliated repositories with two baselines: ")
    md.append(f"repositories with political emojis but no validated affiliation ({rq3_stats['n_baseline']:,} repos) ")
    md.append(f"and repositories flagged as false positives ({rq3_stats['n_false_positive']} repos).")
    md.append("")
    
    md.append("### Stars Comparison")
    md.append("")
    md.append(f"Activist repositories show **{stars_diff} star counts** compared to baseline repositories ")
    md.append(f"(median **{aff_stars['median']:,.0f}** vs **{base_stars['median']:,.0f}** in baseline). ")
    md.append(f"This difference is **{stars_sig}** according to a Mann-Whitney U test ")
    md.append(f"(U = {rq3_stats['stars_test']['statistic']:,.0f}, p = {rq3_stats['stars_test']['p_value']:.4f}).")
    md.append("")
    
    md.append("### Contributors Comparison")
    md.append("")
    md.append(f"In terms of contributors, activist repositories show **{contrib_diff} contributor counts** ")
    md.append(f"(median **{aff_contrib['median']:,.0f}** vs **{base_contrib['median']:,.0f}** in baseline). ")
    md.append(f"This difference is **{contrib_sig}** (U = {rq3_stats['contributors_test']['statistic']:,.0f}, ")
    md.append(f"p = {rq3_stats['contributors_test']['p_value']:.4f}), suggesting that activist signaling is ")
    if rq3_stats['contributors_test']['significant']:
        md.append("associated with more collaborative or community-driven projects.")
    else:
        md.append("not clearly associated with different levels of community involvement.")
    md.append("")
    
    md.append("### Owner Type Comparison")
    md.append("")
    md.append(f"Regarding project ownership, activist repositories show **{rq3_stats['org_percentage']['affiliated']:.1f}%** ")
    md.append(f"organization ownership compared to **{rq3_stats['org_percentage']['baseline']:.1f}%** in baseline repositories. ")
    if rq3_stats['org_percentage']['affiliated'] > rq3_stats['org_percentage']['baseline']:
        md.append("This suggests that organizations are more likely to publicly adopt activist messaging in their projects.")
    else:
        md.append("This suggests that individual developers are more likely to express political stances in their projects.")
    md.append("")
    
    # Statistics tables
    md.append("### Detailed Statistics")
    md.append("")
    md.append("#### Stars Distribution")
    md.append("")
    md.append("| Group | N | Median | Mean | Std Dev | Min | Max |")
    md.append("|-------|---|--------|------|---------|-----|-----|")
    md.append(f"| Affiliated | {rq3_stats['n_affiliated']} | {aff_stars['median']:,.0f} | {aff_stars['mean']:,.0f} | {aff_stars['std']:,.0f} | {aff_stars['min']:,} | {aff_stars['max']:,} |")
    md.append(f"| Baseline | {rq3_stats['n_baseline']:,} | {base_stars['median']:,.0f} | {base_stars['mean']:,.0f} | {base_stars['std']:,.0f} | {base_stars['min']:,} | {base_stars['max']:,} |")
    fp_stars = rq3_stats['stars']['false_positive']
    md.append(f"| False Positive | {rq3_stats['n_false_positive']} | {fp_stars['median']:,.0f} | {fp_stars['mean']:,.0f} | {fp_stars['std']:,.0f} | {fp_stars['min']:,} | {fp_stars['max']:,} |")
    md.append("")
    
    md.append("#### Contributors Distribution")
    md.append("")
    md.append("| Group | N | Median | Mean | Std Dev |")
    md.append("|-------|---|--------|------|---------|")
    md.append(f"| Affiliated | {rq3_stats['n_affiliated']} | {aff_contrib['median']:,.0f} | {aff_contrib['mean']:,.0f} | {aff_contrib['std']:,.0f} |")
    md.append(f"| Baseline | {rq3_stats['n_baseline']:,} | {base_contrib['median']:,.0f} | {base_contrib['mean']:,.0f} | {base_contrib['std']:,.0f} |")
    fp_contrib = rq3_stats['contributors']['false_positive']
    md.append(f"| False Positive | {rq3_stats['n_false_positive']} | {fp_contrib['median']:,.0f} | {fp_contrib['mean']:,.0f} | {fp_contrib['std']:,.0f} |")
    md.append("")
    
    # Figure references
    md.append("### Associated Figures")
    md.append("")
    md.append("**Figure 3: Stars Comparison Across Groups**")
    md.append("")
    md.append("![Figure 3](../figures/figure3_stars_comparison.png)")
    md.append("")
    md.append("*Figure 3. Distribution of star counts for activist-affiliated repositories compared to baseline groups. ")
    md.append("Violin plots highlight differences in the central tendency and spread of popularity across the three groups.*")
    md.append("")
    
    md.append("**Figure 4: Contributors Comparison Across Groups**")
    md.append("")
    md.append("![Figure 4](../figures/figure4_contributors_comparison.png)")
    md.append("")
    md.append("*Figure 4. Distribution of contributor counts for activist-affiliated repositories and baseline groups. ")
    md.append("The figure shows community involvement levels across different repository types.*")
    md.append("")
    
    md.append("**Figure 5: Language Distribution**")
    md.append("")
    md.append("![Figure 5](../figures/figure5_language_distribution.png)")
    md.append("")
    md.append("*Figure 5. Primary programming languages used in activist-affiliated repositories compared to baseline. ")
    md.append("The figure shows which technology ecosystems are more likely to host activist repositories.*")
    md.append("")
    
    md.append("**Figure 6: Owner Type Distribution**")
    md.append("")
    md.append("![Figure 6](../figures/figure6_owner_type_distribution.png)")
    md.append("")
    md.append("*Figure 6. Owner types for activist-affiliated repositories and baselines, showing the proportion of ")
    md.append("repositories owned by individual users versus organizations.*")
    md.append("")
    
    md.append("**Figure 9: Stars vs Contributors Relationship**")
    md.append("")
    md.append("![Figure 9](../figures/figure9_stars_contributors_scatter.png)")
    md.append("")
    md.append("*Figure 9. Scatter plot showing the relationship between repository stars and contributors. ")
    md.append("Affiliated repositories cluster in regions of higher visibility.*")
    md.append("")
    
    md.append("---")
    md.append("")
    
    # ==========================================================================
    # CONCLUSIONS
    # ==========================================================================
    md.append("## Summary of Key Findings")
    md.append("")
    md.append("### RQ1 Summary")
    md.append(f"- **{rq1_stats['n_affiliated']} repositories** ({rq1_stats['pct_affiliated']:.2f}%) contain genuine activist affiliations")
    md.append(f"- **{top3[0]['name']}** dominates with {top3[0]['percentage']:.1f}% of affiliated repositories")
    md.append(f"- Primary languages: {', '.join([l['name'] for l in top_langs[:3]])}")
    md.append("")
    
    md.append("### RQ2 Summary")
    md.append(f"- **{top2_expr[0]['name']}** is the most common expression type ({top2_expr[0]['percentage']:.1f}%)")
    md.append(f"- Only **{rq2_stats['emoji_only_pct']:.1f}%** rely on emoji-only signals")
    md.append(f"- **{rq2_stats['false_positive_rate']:.1f}%** false positive rate among predicted affiliations")
    md.append(f"- Political emojis are a weak signal: only {rq2_stats['true_activist_rate']:.2f}% of emoji repos are truly activist")
    md.append("")
    
    md.append("### RQ3 Summary")
    md.append(f"- Affiliated repos have **{stars_diff}** median stars ({aff_stars['median']:,.0f} vs {base_stars['median']:,.0f})")
    md.append(f"- Affiliated repos have **{contrib_diff}** median contributors ({aff_contrib['median']:,.0f} vs {base_contrib['median']:,.0f})")
    md.append(f"- Stars difference is **{stars_sig}** (p = {rq3_stats['stars_test']['p_value']:.4f})")
    md.append(f"- Contributors difference is **{contrib_sig}** (p = {rq3_stats['contributors_test']['p_value']:.4f})")
    md.append("")
    
    md.append("---")
    md.append("")
    
    # ==========================================================================
    # FIGURE LIST
    # ==========================================================================
    md.append("## List of Figures")
    md.append("")
    md.append("| Figure | Filename | Research Question |")
    md.append("|--------|----------|-------------------|")
    md.append("| Figure 1 | figure1_affiliation_distribution | RQ1 |")
    md.append("| Figure 2 | figure2_support_type_distribution | RQ2 |")
    md.append("| Figure 3 | figure3_stars_comparison | RQ3 |")
    md.append("| Figure 4 | figure4_contributors_comparison | RQ3 |")
    md.append("| Figure 5 | figure5_language_distribution | RQ3 |")
    md.append("| Figure 6 | figure6_owner_type_distribution | RQ3 |")
    md.append("| Figure 7 | figure7_affiliation_by_expression | RQ2 |")
    md.append("| Figure 8 | figure8_creation_timeline | Supplementary |")
    md.append("| Figure 9 | figure9_stars_contributors_scatter | RQ3 |")
    md.append("")
    
    md.append("---")
    md.append("")
    md.append(f"*Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    md.append("")
    
    return "\n".join(md)

# =============================================================================
# PDF GENERATION
# =============================================================================

def generate_pdf(md_path, pdf_path):
    """Generate PDF from markdown using fpdf2."""
    
    try:
        from fpdf import FPDF
        import re
        
        def clean_markdown(text):
            """Remove all markdown formatting from text."""
            # Remove bold
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
            # Remove italic
            text = re.sub(r'\*([^*]+)\*', r'\1', text)
            # Remove inline code
            text = re.sub(r'`([^`]+)`', r'\1', text)
            # Encode for PDF
            text = text.encode('latin-1', 'replace').decode('latin-1')
            return text
        
        with open(md_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # Create PDF
        pdf = FPDF(orientation='P', format='A4')
        pdf.set_margins(left=15, top=15, right=15)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # Process markdown line by line
        lines = md_content.split('\n')
        
        for line in lines:
            # Skip image references but add placeholder
            if line.startswith('!['):
                pdf.set_font('Helvetica', 'I', 8)
                pdf.set_text_color(100, 100, 100)
                pdf.write(4, '[See figures in FINAL/figures/ folder]')
                pdf.ln(6)
                continue
            
            if line.startswith('*Figure'):
                pdf.set_font('Helvetica', 'I', 8)
                pdf.set_text_color(100, 100, 100)
                text = clean_markdown(line)
                pdf.write(4, text)
                pdf.ln(6)
                continue
            
            # Handle tables - convert to simple text format
            if line.startswith('|'):
                cells = [c.strip() for c in line.split('|')[1:-1]]
                # Skip separator rows
                if cells and all(c.replace('-', '').replace(':', '') == '' for c in cells):
                    continue
                if cells:
                    pdf.set_font('Helvetica', size=8)
                    pdf.set_text_color(0, 0, 0)
                    row_text = ' | '.join(cells)
                    row_text = clean_markdown(row_text)
                    pdf.write(4, row_text)
                    pdf.ln()
                continue
            
            # Headers
            if line.startswith('# '):
                pdf.ln(4)
                pdf.set_font('Helvetica', 'B', 16)
                pdf.set_text_color(46, 134, 171)
                text = clean_markdown(line[2:])
                pdf.write(10, text)
                pdf.ln(12)
            elif line.startswith('## '):
                pdf.ln(4)
                pdf.set_font('Helvetica', 'B', 13)
                pdf.set_text_color(233, 79, 55)
                text = clean_markdown(line[3:])
                pdf.write(8, text)
                pdf.ln(10)
            elif line.startswith('### '):
                pdf.ln(3)
                pdf.set_font('Helvetica', 'B', 11)
                pdf.set_text_color(27, 153, 139)
                text = clean_markdown(line[4:])
                pdf.write(6, text)
                pdf.ln(8)
            elif line.startswith('#### '):
                pdf.ln(2)
                pdf.set_font('Helvetica', 'B', 10)
                pdf.set_text_color(0, 0, 0)
                text = clean_markdown(line[5:])
                pdf.write(6, text)
                pdf.ln(8)
            elif line.startswith('---'):
                pdf.ln(3)
                pdf.set_draw_color(200, 200, 200)
                pdf.line(15, pdf.get_y(), 195, pdf.get_y())
                pdf.ln(5)
            elif line.startswith('- '):
                pdf.set_font('Helvetica', size=10)
                pdf.set_text_color(0, 0, 0)
                text = '  * ' + clean_markdown(line[2:])
                pdf.write(5, text)
                pdf.ln()
            elif line.strip():
                pdf.set_font('Helvetica', size=10)
                pdf.set_text_color(0, 0, 0)
                text = clean_markdown(line)
                pdf.write(5, text)
                pdf.ln()
            else:
                pdf.ln(3)
        
        pdf.output(pdf_path)
        print(f"  ✅ Saved: {pdf_path}")
        return True
        
    except ImportError:
        print("  Installing fpdf2 for PDF generation...")
        import subprocess
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'fpdf2', '-q'])
        try:
            from fpdf import FPDF
            return generate_pdf(md_path, pdf_path)
        except:
            pass
    except Exception as e:
        print(f"  ⚠️  PDF generation error: {e}")
    
    print("  ⚠️  PDF generation failed. Markdown file is still available.")
    return False

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main function to generate research results."""
    print("="*70)
    print("RESEARCH RESULTS GENERATION")
    print("Emoji and Political Affiliation in GitHub Repositories")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # Create output directory
    Path(OUTPUT_DIR).mkdir(exist_ok=True)
    print(f"\nOutput directory: {OUTPUT_DIR}/")
    
    # Load data
    affiliated_df, baseline_df, false_positive_df, full_df = load_data()
    
    # Compute statistics for each RQ
    print("\nComputing statistics...")
    
    print("  - RQ1: Affiliation distribution")
    rq1_stats = compute_rq1_statistics(affiliated_df, full_df)
    
    print("  - RQ2: Expression types and false positives")
    rq2_stats = compute_rq2_statistics(affiliated_df, full_df)
    
    print("  - RQ3: Repository characteristics")
    rq3_stats = compute_rq3_statistics(affiliated_df, baseline_df, false_positive_df)
    
    # Generate markdown report
    print("\nGenerating COMPREHENSIVE markdown report...")
    md_content = generate_comprehensive_report(rq1_stats, rq2_stats, rq3_stats, affiliated_df)
    
    md_path = f"{OUTPUT_DIR}/Research_Results.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    print(f"  ✅ Saved: {md_path}")
    
    # Generate PDF
    print("\nGenerating PDF report...")
    pdf_path = f"{OUTPUT_DIR}/Research_Results.pdf"
    generate_pdf(md_path, pdf_path)
    
    # Copy relevant figures to FINAL folder
    print("\nCopying figures to FINAL folder...")
    figures_to_copy = [
        'figure1_affiliation_distribution.png',
        'figure2_support_type_distribution.png',
        'figure3_stars_comparison.png',
        'figure4_contributors_comparison.png',
        'figure5_language_distribution.png',
        'figure6_owner_type_distribution.png',
        'figure7_affiliation_by_expression.png',
        'figure8_creation_timeline.png',
        'figure9_stars_contributors_scatter.png'
    ]
    
    figures_subdir = Path(OUTPUT_DIR) / 'figures'
    figures_subdir.mkdir(exist_ok=True)
    
    for fig in figures_to_copy:
        src = Path(FIGURES_DIR) / fig
        dst = figures_subdir / fig
        if src.exists():
            shutil.copy(src, dst)
            print(f"  ✅ Copied: {fig}")
        else:
            print(f"  ⚠️  Not found: {fig}")
    
    print("\n" + "="*70)
    print("RESEARCH RESULTS GENERATION COMPLETE")
    print("="*70)
    print(f"\nOutput files:")
    print(f"  - {OUTPUT_DIR}/Research_Results.md")
    print(f"  - {OUTPUT_DIR}/Research_Results.pdf (if pandoc available)")
    print(f"  - {OUTPUT_DIR}/figures/ (all relevant figures)")
    
    # Print quick summary
    print("\n" + "-"*70)
    print("QUICK RESULTS SUMMARY")
    print("-"*70)
    print(f"\n📊 RQ1: {rq1_stats['n_affiliated']} repos ({rq1_stats['pct_affiliated']:.2f}%) have valid activist affiliations")
    print(f"   Top affiliation: {rq1_stats['affiliations'][0]['name']} ({rq1_stats['affiliations'][0]['percentage']:.1f}%)")
    print(f"\n📊 RQ2: {rq2_stats['expression_types'][0]['name']} is most common expression ({rq2_stats['expression_types'][0]['percentage']:.1f}%)")
    print(f"   False positive rate: {rq2_stats['false_positive_rate']:.1f}%")
    print(f"\n📊 RQ3: Affiliated repos have {'higher' if rq3_stats['stars']['affiliated']['median'] > rq3_stats['stars']['baseline']['median'] else 'lower'} median stars")
    print(f"   Stars test p-value: {rq3_stats['stars_test']['p_value']:.4f} ({'significant' if rq3_stats['stars_test']['significant'] else 'not significant'})")
    print(f"   Contributors test p-value: {rq3_stats['contributors_test']['p_value']:.4f} ({'significant' if rq3_stats['contributors_test']['significant'] else 'not significant'})")

if __name__ == '__main__':
    main()
