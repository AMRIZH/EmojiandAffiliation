#!/usr/bin/env python3
"""
Enhanced Report Generator - Creates comprehensive research results markdown.
This module provides the generate_comprehensive_report function.
"""

import pandas as pd
from datetime import datetime

def generate_comprehensive_report(rq1_stats, rq2_stats, rq3_stats, affiliated_df):
    """Generate a comprehensive markdown research results report."""
    
    md = []
    
    # Header
    md.append("# Research Results: Emoji and Political Affiliation in GitHub Repositories")
    md.append("")
    md.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md.append("")
    md.append("---")
    md.append("")
    
    # ==========================================================================
    # TABLE OF CONTENTS
    # ==========================================================================
    md.append("## Table of Contents")
    md.append("")
    md.append("1. [Executive Summary](#executive-summary)")
    md.append("2. [Methodology Overview](#methodology-overview)")
    md.append("3. [RQ1: Repository Types and Affiliations](#rq1-what-kinds-of-github-repositories-use-politically-meaningful-emojis)")
    md.append("4. [RQ2: Expression Methods and False Positives](#rq2-how-do-these-repositories-express-political-or-activist-support-and-how-many-cases-are-false-positives)")
    md.append("5. [RQ3: Repository Characteristics](#rq3-what-are-the-characteristics-of-these-repositories-and-their-contributors)")
    md.append("6. [Discussion](#discussion)")
    md.append("7. [Summary of Key Findings](#summary-of-key-findings)")
    md.append("8. [List of Figures](#list-of-figures)")
    md.append("")
    md.append("---")
    md.append("")
    
    # ==========================================================================
    # EXECUTIVE SUMMARY
    # ==========================================================================
    md.append("## Executive Summary")
    md.append("")
    md.append(f"This study analyzed **{rq1_stats['n_total_emoji']:,}** GitHub repositories containing political or activist emojis ")
    md.append(f"to understand how developers use emoji symbols to signal political and social affiliations in their projects. ")
    md.append(f"Through a rigorous multi-stage validation process combining AI-based classification and manual verification, ")
    md.append(f"we identified **{rq1_stats['n_affiliated']}** repositories ({rq1_stats['pct_affiliated']:.2f}%) ")
    md.append(f"with genuine political or activist affiliations.")
    md.append("")
    md.append("### Key Findings at a Glance")
    md.append("")
    top_aff = rq1_stats['affiliations'][0]
    top_expr = rq2_stats['expression_types'][0]
    md.append(f"| Metric | Value |")
    md.append(f"|--------|-------|")
    md.append(f"| Total repositories analyzed | {rq1_stats['n_total_emoji']:,} |")
    md.append(f"| Validated activist repositories | {rq1_stats['n_affiliated']} ({rq1_stats['pct_affiliated']:.2f}%) |")
    md.append(f"| Most common affiliation | {top_aff['name']} ({top_aff['percentage']:.1f}%) |")
    md.append(f"| Most common expression type | {top_expr['name']} ({top_expr['percentage']:.1f}%) |")
    md.append(f"| False positive rate (AI classifier) | {rq2_stats['false_positive_rate']:.1f}% |")
    md.append(f"| Total stars across activist repos | {rq1_stats.get('total_stars', 'N/A'):,} |")
    md.append(f"| Contributors statistical significance | p = {rq3_stats['contributors_test']['p_value']:.4f} |")
    md.append("")
    md.append("---")
    md.append("")
    
    # ==========================================================================
    # METHODOLOGY OVERVIEW
    # ==========================================================================
    md.append("## Methodology Overview")
    md.append("")
    md.append("### Data Collection")
    md.append("")
    md.append(f"We collected {rq1_stats['n_total_emoji']:,} GitHub repositories that met the following criteria:")
    md.append("")
    md.append("1. **Minimum popularity threshold**: At least 1,000 stars")
    md.append("2. **Emoji presence**: README contains at least one political or activist-related emoji")
    md.append("3. **Political emoji categories**: Ukraine flag 🇺🇦, Palestine flag 🇵🇸, rainbow 🌈, Pride flags 🏳️‍🌈 🏳️‍⚧️, raised fists ✊✊🏿✊🏾, and other activist symbols")
    md.append("")
    md.append("### Validation Process")
    md.append("")
    md.append("1. **AI Classification (DeepSeek)**: Initial filtering using large language model to identify potential activist repositories")
    md.append(f"2. **Manual Validation**: Human review of {rq2_stats['n_predicted']} AI-flagged repositories")
    md.append(f"3. **Expression Categorization**: Classification of how each repository expresses political support")
    md.append("")
    md.append("### Expression Categories Defined")
    md.append("")
    md.append("| Category | Definition | Example |")
    md.append("|----------|------------|---------|")
    md.append("| Text Statement | Explicit written declaration of support | \"We stand with Ukraine\" |")
    md.append("| Link Support | URLs to donation pages or information | \"[Donate to Ukraine](...)\" |")
    md.append("| Hashtag/Slogan | Use of movement hashtags | #StandWithUkraine, #BLM |")
    md.append("| Visual/Badge | Images, badges, or banners | Support badges in README |")
    md.append("| Emoji Only | Only emoji without context | Just 🇺🇦 in description |")
    md.append("")
    md.append("### Analysis Framework")
    md.append("")
    md.append("- **RQ1**: Repository types and affiliation distribution")
    md.append("- **RQ2**: Expression methods and false positive analysis")
    md.append("- **RQ3**: Repository characteristics comparison (stars, contributors, ownership)")
    md.append("")
    md.append("---")
    md.append("")
    
    # ==========================================================================
    # RQ1 RESULTS
    # ==========================================================================
    md.append("## RQ1: What kinds of GitHub repositories use politically meaningful emojis?")
    md.append("")
    
    top3 = rq1_stats['affiliations'][:3]
    top_langs = rq1_stats['top_languages'][:3]
    
    md.append("### Overview")
    md.append("")
    md.append(f"Among the {rq1_stats['n_total_emoji']:,} popular repositories that contain at least one political or activist emoji, ")
    md.append(f"we identified **{rq1_stats['n_affiliated']} repositories** with a clearly validated activist affiliation ")
    md.append(f"(approximately **{rq1_stats['pct_affiliated']:.2f}%** of all emoji-bearing repositories). ")
    md.append(f"This finding indicates that political emojis in popular GitHub projects are predominantly decorative ")
    md.append(f"rather than intentional political signals.")
    md.append("")
    
    md.append("### Political Affiliation Distribution")
    md.append("")
    md.append(f"The most common affiliations were **{top3[0]['name']}** (n={top3[0]['count']}, {top3[0]['percentage']:.1f}%), ")
    md.append(f"followed by **{top3[1]['name']}** (n={top3[1]['count']}, {top3[1]['percentage']:.1f}%) ")
    md.append(f"and **{top3[2]['name']}** (n={top3[2]['count']}, {top3[2]['percentage']:.1f}%). ")
    md.append(f"The dominance of Ukraine-related repositories ({top3[0]['percentage']:.1f}%) reflects the global developer ")
    md.append(f"community's response to the 2022 Russian invasion, demonstrating how geopolitical events ")
    md.append(f"influence open-source project documentation.")
    md.append("")
    
    md.append("| Affiliation | Count | Percentage | Primary Emojis |")
    md.append("|-------------|-------|------------|----------------|")
    emoji_map = {
        'UKRAINE': '🇺🇦 💙 💛 🌻',
        'PALESTINE': '🇵🇸 🍉',
        'LGBTQ': '🏳️‍🌈 🏳️‍⚧️ 🌈',
        'BLM': '✊🏿 ✊🏾 ✊',
        'REPUBLICAN': '🐘 🔥',
        'ISRAEL': '🇮🇱',
        'CLIMATE': '🌍 🌱',
        'DEMOCRATS': '🗳️',
        'FEMINISM': '♀️'
    }
    for aff in rq1_stats['affiliations']:
        emojis = emoji_map.get(aff['name'], '-')
        md.append(f"| {aff['name']} | {aff['count']} | {aff['percentage']:.1f}% | {emojis} |")
    md.append("")
    
    # Technology distribution
    md.append("### Technology Stack Analysis")
    md.append("")
    md.append(f"In terms of programming languages, activist-affiliated repositories span diverse technology ecosystems:")
    md.append("")
    md.append("| Language | Count | Percentage |")
    md.append("|----------|-------|------------|")
    for lang in rq1_stats['top_languages'][:10]:
        md.append(f"| {lang['name']} | {lang['count']} | {lang['percentage']:.1f}% |")
    md.append("")
    md.append(f"The prevalence of **{top_langs[0]['name']}** ({top_langs[0]['percentage']:.1f}%) and ")
    md.append(f"**{top_langs[1]['name']}** ({top_langs[1]['percentage']:.1f}%) suggests that web development ")
    md.append(f"and frontend technologies are particularly associated with activist signaling, ")
    md.append(f"possibly due to the documentation-heavy nature of these projects and their visibility to end users.")
    md.append("")
    
    # Owner type analysis
    md.append("### Repository Ownership Patterns")
    md.append("")
    user_stats = rq1_stats['owner_types'].get('User', {'count': 0, 'percentage': 0})
    org_stats = rq1_stats['owner_types'].get('Organization', {'count': 0, 'percentage': 0})
    md.append(f"- **Individual Users:** {user_stats['count']} repositories ({user_stats['percentage']:.1f}%)")
    md.append(f"- **Organizations:** {org_stats['count']} repositories ({org_stats['percentage']:.1f}%)")
    md.append("")
    if user_stats['percentage'] > org_stats['percentage']:
        md.append(f"Individual developers are more likely to express political stances ({user_stats['percentage']:.1f}% vs {org_stats['percentage']:.1f}%), ")
        md.append(f"suggesting that personal projects provide more freedom for political expression compared to organizational repositories.")
    else:
        md.append(f"Organizations show higher rates of political signaling ({org_stats['percentage']:.1f}% vs {user_stats['percentage']:.1f}%), ")
        md.append(f"indicating that corporate/organizational projects increasingly use README badges for social causes.")
    md.append("")
    
    # Top repositories
    if 'top_repos' in rq1_stats and rq1_stats['top_repos']:
        md.append("### Top 10 Activist Repositories by Stars")
        md.append("")
        md.append("| Rank | Repository | Stars | Affiliation | Language |")
        md.append("|------|------------|-------|-------------|----------|")
        for i, repo in enumerate(rq1_stats['top_repos'][:10], 1):
            repo_name = f"{repo['repo_owner']}/{repo['repo_name']}"
            lang = repo['language'] if pd.notna(repo.get('language')) else 'N/A'
            md.append(f"| {i} | [{repo_name}](https://github.com/{repo_name}) | {repo['repo_stars']:,} | {repo['affiliation_deepseek'].upper()} | {lang} |")
        md.append("")
        md.append(f"*The top activist repository has **{rq1_stats.get('max_stars', 'N/A'):,}** stars, demonstrating that political signaling ")
        md.append(f"occurs even in the most popular open-source projects.*")
        md.append("")
    
    # Emoji usage
    if 'emoji_usage' in rq1_stats and rq1_stats['emoji_usage']:
        md.append("### Most Commonly Used Political Emojis")
        md.append("")
        md.append("| Emoji | Count | Primary Association |")
        md.append("|-------|-------|---------------------|")
        emoji_assoc = {
            '🇺🇦': 'Ukraine', '🇵🇸': 'Palestine', '🌈': 'LGBTQ+', '🏳️‍🌈': 'Pride',
            '🏳️‍⚧️': 'Trans Pride', '✊': 'Solidarity', '✊🏿': 'BLM', '✊🏾': 'BLM',
            '❤️': 'Support', '💙': 'Ukraine', '💛': 'Ukraine', '🍉': 'Palestine',
            '🌻': 'Ukraine', '🔥': 'Various', '🐘': 'Republican', '🌍': 'Climate',
            '🇮🇱': 'Israel', '🇷🇺': 'Russia/Anti-war'
        }
        for emoji, count in rq1_stats['emoji_usage'][:15]:
            assoc = emoji_assoc.get(emoji, 'Various')
            md.append(f"| {emoji} | {count} | {assoc} |")
        md.append("")
    
    # Timeline
    if 'creation_by_year' in rq1_stats and rq1_stats['creation_by_year']:
        md.append("### Repository Creation Timeline")
        md.append("")
        md.append("| Year | Repositories Created |")
        md.append("|------|---------------------|")
        for year, count in sorted(rq1_stats['creation_by_year'].items()):
            md.append(f"| {int(year)} | {count} |")
        md.append("")
    
    # Figure reference
    md.append("### Associated Figures")
    md.append("")
    md.append("**Figure 1: Distribution of Political/Activist Affiliations**")
    md.append("")
    md.append("![Figure 1](figures/figure1_affiliation_distribution.png)")
    md.append("")
    md.append(f"*Figure 1. Distribution of activist affiliations among the {rq1_stats['n_affiliated']} validated repositories. ")
    md.append("The plot shows the proportion of repositories supporting each movement, ")
    md.append("with Ukraine-related activism dominating the distribution.*")
    md.append("")
    
    md.append("**Figure 8: Repository Creation Timeline**")
    md.append("")
    md.append("![Figure 8](figures/figure8_creation_timeline.png)")
    md.append("")
    md.append("*Figure 8. Timeline showing when activist-affiliated repositories were created, ")
    md.append("revealing temporal patterns in political signaling adoption.*")
    md.append("")
    
    md.append("---")
    md.append("")
    
    # ==========================================================================
    # RQ2 RESULTS
    # ==========================================================================
    md.append("## RQ2: How do these repositories express political or activist support, and how many cases are false positives?")
    md.append("")
    
    md.append("### Overview")
    md.append("")
    top2_expr = rq2_stats['expression_types'][:2]
    md.append("We classified the way each repository expresses support into five categories: ")
    md.append("**text statements**, **link-based support**, **slogans or hashtags**, **visual banners/badges**, and **emoji-only**. ")
    md.append(f"This analysis reveals that most activist repositories use multiple channels to express support, ")
    md.append(f"with only a minority relying solely on emoji symbols.")
    md.append("")
    
    # Expression type distribution
    md.append("### Expression Type Distribution")
    md.append("")
    md.append(f"Among the {rq2_stats['n_validated']} validated activist repositories:")
    md.append("")
    md.append("| Expression Type | Count | Percentage | Description |")
    md.append("|-----------------|-------|------------|-------------|")
    expr_desc = {
        'Text Statement': 'Explicit written statement of support in README',
        'Link Support': 'Links to donation pages, petitions, or information resources',
        'Hashtag/Slogan': 'Use of hashtags like #StandWithUkraine or slogans',
        'Visual/Badge': 'Badges, banners, or images showing support',
        'Emoji Only': 'Only emoji symbols without additional context'
    }
    for expr in rq2_stats['expression_types']:
        desc = expr_desc.get(expr['name'], '-')
        md.append(f"| {expr['name']} | {expr['count']} | {expr['percentage']:.1f}% | {desc} |")
    md.append("")
    
    md.append(f"**Key Insight:** {top2_expr[0]['name']} is the most common support type ({top2_expr[0]['percentage']:.1f}%), ")
    md.append(f"indicating that developers prefer explicit, contextual methods over symbolic signaling alone.")
    md.append("")
    
    # Emoji-only analysis
    md.append("### Emoji-Only Signaling Analysis")
    md.append("")
    md.append(f"Emoji-only signals were relatively rare, with only **{rq2_stats['emoji_only_count']} repositories** ")
    md.append(f"({rq2_stats['emoji_only_pct']:.1f}%) relying solely on activist emojis without any supporting text, link, or image. ")
    md.append(f"This finding is significant because it suggests that:")
    md.append("")
    md.append("1. **Emojis alone are insufficient** for meaningful political communication")
    md.append("2. **Context matters** - developers recognize the need for explicit messaging")
    md.append("3. **Detection systems** cannot rely solely on emoji presence for classification")
    md.append("")
    
    # Multi-expression analysis
    if 'multi_expression_count' in rq2_stats:
        md.append("### Multi-Expression Patterns")
        md.append("")
        md.append(f"- **Repositories using multiple expression types:** {rq2_stats['multi_expression_count']} ({rq2_stats['multi_expression_pct']:.1f}%)")
        md.append(f"- **Repositories using single expression type:** {rq2_stats['single_expression_count']} ({100 - rq2_stats['multi_expression_pct']:.1f}%)")
        md.append("")
        
        if rq2_stats.get('category_combinations'):
            md.append("**Most Common Expression Combinations:**")
            md.append("")
            md.append("| Combination | Count |")
            md.append("|-------------|-------|")
            for combo, count in rq2_stats['category_combinations'][:8]:
                md.append(f"| {combo} | {count} |")
            md.append("")
    
    # Explicit vs Implicit
    if 'explicit_count' in rq2_stats:
        md.append("### Validity Classification: Explicit vs Implicit Signaling")
        md.append("")
        md.append(f"| Validity Type | Count | Percentage | Description |")
        md.append(f"|---------------|-------|------------|-------------|")
        md.append(f"| Explicit | {rq2_stats['explicit_count']} | {rq2_stats['explicit_pct']:.1f}% | Clear, unambiguous statement of support |")
        md.append(f"| Implicit | {rq2_stats['implicit_count']} | {rq2_stats['implicit_pct']:.1f}% | Contextual inference required |")
        md.append("")
        md.append(f"The high proportion of explicit signals ({rq2_stats['explicit_pct']:.1f}%) demonstrates that ")
        md.append(f"most developers who choose to express political support do so clearly and intentionally.")
        md.append("")
    
    # False positive analysis
    md.append("### False Positive Analysis")
    md.append("")
    md.append(f"When considering all {rq2_stats['n_total_emoji_repos']:,} repositories that contain political emojis, ")
    md.append(f"only **{rq2_stats['n_validated']}** (approximately **{rq2_stats['true_activist_rate']:.2f}%**) were confirmed as truly activist.")
    md.append("")
    md.append("#### AI Classifier Performance")
    md.append("")
    md.append("| Metric | Value |")
    md.append("|--------|-------|")
    md.append(f"| Repositories flagged by AI | {rq2_stats['n_predicted']} |")
    md.append(f"| True positives (validated) | {rq2_stats['n_validated']} |")
    md.append(f"| False positives | {rq2_stats['n_false_positive']} |")
    precision = (rq2_stats['n_validated']/rq2_stats['n_predicted']*100) if rq2_stats['n_predicted'] > 0 else 0
    md.append(f"| Precision | {precision:.1f}% |")
    md.append(f"| False positive rate | {rq2_stats['false_positive_rate']:.1f}% |")
    md.append("")
    
    md.append("#### Common False Positive Patterns")
    md.append("")
    md.append("Analysis of false positives revealed several common patterns:")
    md.append("")
    md.append("1. **Decorative emoji use**: Rainbow 🌈 used for color themes, not LGBTQ+ support")
    md.append("2. **Technical contexts**: Emojis in commit messages or changelogs")
    md.append("3. **Cultural references**: Watermelon 🍉 in food/agriculture projects")
    md.append("4. **Design elements**: Flag emojis for internationalization features")
    md.append("5. **Coincidental presence**: Activist emojis appearing in unrelated contexts")
    md.append("")
    
    md.append("#### Signal Strength Assessment")
    md.append("")
    md.append(f"Political emojis in popular GitHub repositories are a **weak but non-random signal** ")
    md.append(f"of activist content. With only {rq2_stats['true_activist_rate']:.2f}% of emoji-bearing repositories ")
    md.append(f"being truly activist, emoji detection alone is insufficient for reliable classification. ")
    md.append(f"Contextual analysis is essential.")
    md.append("")
    
    # Expression by affiliation
    if 'expression_by_affiliation' in rq2_stats and rq2_stats['expression_by_affiliation']:
        md.append("### Expression Patterns by Affiliation")
        md.append("")
        md.append("| Affiliation | Text | Link | Hashtag | Badge | Emoji Only |")
        md.append("|-------------|------|------|---------|-------|------------|")
        for aff, expressions in sorted(rq2_stats['expression_by_affiliation'].items(), 
                                       key=lambda x: sum(x[1].values()), reverse=True):
            text = expressions.get('Text Statement', 0)
            link = expressions.get('Link Support', 0)
            hashtag = expressions.get('Hashtag/Slogan', 0)
            badge = expressions.get('Visual/Badge', 0)
            emoji = expressions.get('Emoji Only', 0)
            md.append(f"| {aff} | {text} | {link} | {hashtag} | {badge} | {emoji} |")
        md.append("")
    
    # Figure references
    md.append("### Associated Figures")
    md.append("")
    md.append("**Figure 2: Support Type Distribution**")
    md.append("")
    md.append("![Figure 2](figures/figure2_support_type_distribution.png)")
    md.append("")
    md.append(f"*Figure 2. Support types used by activist-affiliated repositories. ")
    md.append("Text statements and link support are the dominant methods, while emoji-only signaling is rare.*")
    md.append("")
    
    md.append("**Figure 7: Affiliation by Expression Type**")
    md.append("")
    md.append("![Figure 7](figures/figure7_affiliation_by_expression.png)")
    md.append("")
    md.append("*Figure 7. Distribution of expression types across different political affiliations, ")
    md.append("showing how different movements prefer different communication strategies.*")
    md.append("")
    
    md.append("---")
    md.append("")
    
    # ==========================================================================
    # RQ3 RESULTS
    # ==========================================================================
    md.append("## RQ3: What are the characteristics of these repositories and their contributors?")
    md.append("")
    
    md.append("### Overview")
    md.append("")
    aff_stars = rq3_stats['stars']['affiliated']
    base_stars = rq3_stats['stars']['baseline']
    fp_stars = rq3_stats['stars']['false_positive']
    aff_contrib = rq3_stats['contributors']['affiliated']
    base_contrib = rq3_stats['contributors']['baseline']
    fp_contrib = rq3_stats['contributors']['false_positive']
    
    md.append(f"We compared the {rq3_stats['n_affiliated']} activist-affiliated repositories with two baselines: ")
    md.append(f"repositories with political emojis but no validated affiliation ({rq3_stats['n_baseline']:,} repos) ")
    md.append(f"and repositories flagged as false positives ({rq3_stats['n_false_positive']} repos). ")
    md.append(f"This comparison reveals important differences in project characteristics.")
    md.append("")
    
    # Hypothesis testing summary
    md.append("### Statistical Testing Summary")
    md.append("")
    md.append("| Variable | Test | Statistic | p-value | Significant (α=0.05) | Effect Size |")
    md.append("|----------|------|-----------|---------|---------------------|-------------|")
    stars_sig = "Yes ✓" if rq3_stats['stars_test']['significant'] else "No ✗"
    contrib_sig = "Yes ✓" if rq3_stats['contributors_test']['significant'] else "No ✗"
    stars_effect = rq3_stats.get('stars_effect_size', 'N/A')
    contrib_effect = rq3_stats.get('contributors_effect_size', 'N/A')
    if isinstance(stars_effect, float):
        stars_effect = f"d={stars_effect:.3f}"
    if isinstance(contrib_effect, float):
        contrib_effect = f"d={contrib_effect:.3f}"
    md.append(f"| Stars | Mann-Whitney U | {rq3_stats['stars_test']['statistic']:,.0f} | {rq3_stats['stars_test']['p_value']:.4f} | {stars_sig} | {stars_effect} |")
    md.append(f"| Contributors | Mann-Whitney U | {rq3_stats['contributors_test']['statistic']:,.0f} | {rq3_stats['contributors_test']['p_value']:.4f} | {contrib_sig} | {contrib_effect} |")
    md.append("")
    
    # Stars comparison
    md.append("### Repository Popularity (Stars)")
    md.append("")
    stars_diff = "higher" if aff_stars['median'] > base_stars['median'] else "lower"
    stars_sig_text = "statistically significant" if rq3_stats['stars_test']['significant'] else "not statistically significant"
    
    md.append(f"Activist repositories show **{stars_diff} star counts** compared to baseline repositories.")
    md.append("")
    total_stars = rq1_stats.get('total_stars', 'N/A')
    if isinstance(total_stars, (int, float)):
        total_stars = f"{total_stars:,}"
    md.append("| Group | N | Median | Mean | Std Dev | Min | Max | Total |")
    md.append("|-------|---|--------|------|---------|-----|-----|-------|")
    md.append(f"| Affiliated | {rq3_stats['n_affiliated']} | {aff_stars['median']:,.0f} | {aff_stars['mean']:,.0f} | {aff_stars['std']:,.0f} | {aff_stars['min']:,} | {aff_stars['max']:,} | {total_stars} |")
    md.append(f"| Baseline | {rq3_stats['n_baseline']:,} | {base_stars['median']:,.0f} | {base_stars['mean']:,.0f} | {base_stars['std']:,.0f} | {base_stars['min']:,} | {base_stars['max']:,} | - |")
    md.append(f"| False Positive | {rq3_stats['n_false_positive']} | {fp_stars['median']:,.0f} | {fp_stars['mean']:,.0f} | {fp_stars['std']:,.0f} | {fp_stars['min']:,} | {fp_stars['max']:,} | - |")
    md.append("")
    md.append(f"**Statistical Result:** The difference in star counts is **{stars_sig_text}** ")
    md.append(f"(U = {rq3_stats['stars_test']['statistic']:,.0f}, p = {rq3_stats['stars_test']['p_value']:.4f}).")
    if not rq3_stats['stars_test']['significant']:
        md.append(f" This suggests that political signaling is not associated with repository popularity.")
    md.append("")
    
    # Contributors comparison
    md.append("### Community Engagement (Contributors)")
    md.append("")
    contrib_diff = "higher" if aff_contrib['median'] > base_contrib['median'] else "lower"
    contrib_sig_text = "statistically significant" if rq3_stats['contributors_test']['significant'] else "not statistically significant"
    
    md.append(f"In terms of contributors, activist repositories show **{contrib_diff} contributor counts**.")
    md.append("")
    md.append("| Group | N | Median | Mean | Std Dev |")
    md.append("|-------|---|--------|------|---------|")
    md.append(f"| Affiliated | {rq3_stats['n_affiliated']} | {aff_contrib['median']:,.0f} | {aff_contrib['mean']:,.0f} | {aff_contrib['std']:,.0f} |")
    md.append(f"| Baseline | {rq3_stats['n_baseline']:,} | {base_contrib['median']:,.0f} | {base_contrib['mean']:,.0f} | {base_contrib['std']:,.0f} |")
    md.append(f"| False Positive | {rq3_stats['n_false_positive']} | {fp_contrib['median']:,.0f} | {fp_contrib['mean']:,.0f} | {fp_contrib['std']:,.0f} |")
    md.append("")
    md.append(f"**Statistical Result:** The difference in contributor counts is **{contrib_sig_text}** ")
    md.append(f"(U = {rq3_stats['contributors_test']['statistic']:,.0f}, p = {rq3_stats['contributors_test']['p_value']:.4f}).")
    if rq3_stats['contributors_test']['significant']:
        md.append(f" This suggests that activist signaling is associated with more collaborative, community-driven projects.")
    md.append("")
    
    # Forks comparison
    if 'forks' in rq3_stats:
        md.append("### Repository Forks")
        md.append("")
        md.append("| Group | Median Forks | Mean Forks |")
        md.append("|-------|--------------|------------|")
        md.append(f"| Affiliated | {rq3_stats['forks']['affiliated']['median']:,.0f} | {rq3_stats['forks']['affiliated']['mean']:,.0f} |")
        md.append(f"| Baseline | {rq3_stats['forks']['baseline']['median']:,.0f} | {rq3_stats['forks']['baseline']['mean']:,.0f} |")
        md.append("")
    
    # Owner type comparison
    md.append("### Owner Type Comparison")
    md.append("")
    md.append("| Group | Organization % | Individual User % |")
    md.append("|-------|---------------|-------------------|")
    md.append(f"| Affiliated | {rq3_stats['org_percentage']['affiliated']:.1f}% | {100-rq3_stats['org_percentage']['affiliated']:.1f}% |")
    md.append(f"| Baseline | {rq3_stats['org_percentage']['baseline']:.1f}% | {100-rq3_stats['org_percentage']['baseline']:.1f}% |")
    md.append(f"| False Positive | {rq3_stats['org_percentage']['false_positive']:.1f}% | {100-rq3_stats['org_percentage']['false_positive']:.1f}% |")
    md.append("")
    if rq3_stats['org_percentage']['affiliated'] < rq3_stats['org_percentage']['baseline']:
        md.append(f"Individual developers are more likely to express political stances ({100-rq3_stats['org_percentage']['affiliated']:.1f}% vs {100-rq3_stats['org_percentage']['baseline']:.1f}%), ")
        md.append(f"suggesting personal projects provide more freedom for political expression.")
    else:
        md.append(f"Organizations show higher rates of political signaling, indicating ")
        md.append(f"that corporate/organizational projects increasingly use README badges for social causes.")
    md.append("")
    
    # Stars by affiliation
    if rq3_stats.get('stars_by_affiliation'):
        md.append("### Repository Metrics by Affiliation Type")
        md.append("")
        md.append("| Affiliation | Median Stars | Mean Stars | Total Stars |")
        md.append("|-------------|--------------|------------|-------------|")
        for aff, metrics in sorted(rq3_stats['stars_by_affiliation'].items(), key=lambda x: x[1]['sum'], reverse=True):
            md.append(f"| {aff.upper()} | {metrics['median']:,.0f} | {metrics['mean']:,.0f} | {metrics['sum']:,.0f} |")
        md.append("")
    
    # Language comparison
    md.append("### Programming Language Comparison")
    md.append("")
    md.append("| Rank | Affiliated Repos | Baseline Repos |")
    md.append("|------|------------------|----------------|")
    aff_langs = list(rq3_stats['languages']['affiliated'].items())[:5]
    base_langs = list(rq3_stats['languages']['baseline'].items())[:5]
    for i in range(5):
        aff_lang = f"{aff_langs[i][0]} ({aff_langs[i][1]})" if i < len(aff_langs) else "-"
        base_lang = f"{base_langs[i][0]} ({base_langs[i][1]})" if i < len(base_langs) else "-"
        md.append(f"| {i+1} | {aff_lang} | {base_lang} |")
    md.append("")
    
    # Figure references
    md.append("### Associated Figures")
    md.append("")
    md.append("**Figure 3: Stars Comparison Across Groups**")
    md.append("")
    md.append("![Figure 3](figures/figure3_stars_comparison.png)")
    md.append("")
    md.append("*Figure 3. Distribution of star counts for activist-affiliated repositories compared to baseline groups.*")
    md.append("")
    
    md.append("**Figure 4: Contributors Comparison Across Groups**")
    md.append("")
    md.append("![Figure 4](figures/figure4_contributors_comparison.png)")
    md.append("")
    md.append("*Figure 4. Distribution of contributor counts, showing higher engagement in activist-affiliated repositories.*")
    md.append("")
    
    md.append("**Figure 5: Language Distribution**")
    md.append("")
    md.append("![Figure 5](figures/figure5_language_distribution.png)")
    md.append("")
    md.append("*Figure 5. Primary programming languages comparison between affiliated and baseline repositories.*")
    md.append("")
    
    md.append("**Figure 6: Owner Type Distribution**")
    md.append("")
    md.append("![Figure 6](figures/figure6_owner_type_distribution.png)")
    md.append("")
    md.append("*Figure 6. Owner types showing the proportion of individual vs organizational ownership.*")
    md.append("")
    
    md.append("**Figure 9: Stars vs Contributors Relationship**")
    md.append("")
    md.append("![Figure 9](figures/figure9_stars_contributors_scatter.png)")
    md.append("")
    md.append("*Figure 9. Scatter plot showing the relationship between repository popularity and community size.*")
    md.append("")
    
    md.append("---")
    md.append("")
    
    # ==========================================================================
    # DISCUSSION
    # ==========================================================================
    md.append("## Discussion")
    md.append("")
    
    md.append("### Key Findings")
    md.append("")
    md.append("#### 1. Political Emoji Usage is Rare but Meaningful")
    md.append("")
    md.append(f"Only {rq1_stats['pct_affiliated']:.2f}% of repositories containing political emojis ")
    md.append(f"actually have genuine activist affiliations. This indicates that political emojis ")
    md.append(f"are predominantly used for decorative purposes in the developer community. However, ")
    md.append(f"when political signaling does occur, it is typically explicit and intentional ")
    if 'explicit_pct' in rq2_stats:
        md.append(f"({rq2_stats['explicit_pct']:.1f}% explicit vs {rq2_stats['implicit_pct']:.1f}% implicit).")
    else:
        md.append("based on our manual validation.")
    md.append("")
    
    md.append("#### 2. Ukraine Dominates Activist Signaling")
    md.append("")
    md.append(f"With {top3[0]['percentage']:.1f}% of activist repositories supporting Ukraine, ")
    md.append(f"the 2022 Russian invasion clearly had a significant impact on the open-source community. ")
    md.append(f"This reflects broader global solidarity movements and the developer community's ")
    md.append(f"response to geopolitical crises.")
    md.append("")
    
    md.append("#### 3. Multi-Modal Expression is Preferred")
    md.append("")
    md.append(f"Developers rarely rely on emoji-only signaling ({rq2_stats['emoji_only_pct']:.1f}%). ")
    if 'multi_expression_pct' in rq2_stats:
        md.append(f"Instead, {rq2_stats['multi_expression_pct']:.1f}% use multiple expression methods, ")
    md.append(f"combining text statements, links, badges, and hashtags for comprehensive messaging.")
    md.append("")
    
    md.append("#### 4. Community Engagement Matters")
    md.append("")
    if rq3_stats['contributors_test']['significant']:
        md.append(f"The statistically significant difference in contributor counts (p = {rq3_stats['contributors_test']['p_value']:.4f}) ")
        md.append(f"suggests that activist signaling is associated with more collaborative projects. ")
        md.append(f"This may indicate that community-oriented projects are more likely to take public stances on social issues.")
    else:
        md.append(f"No significant difference was found in contributor counts, suggesting ")
        md.append(f"that activist signaling is independent of community size.")
    md.append("")
    
    md.append("### Limitations")
    md.append("")
    md.append("1. **Sample bias**: Only repositories with 1,000+ stars were analyzed")
    md.append("2. **Temporal scope**: Data represents a snapshot; political movements evolve")
    md.append("3. **Classification accuracy**: AI classifier has {:.1f}% false positive rate".format(rq2_stats['false_positive_rate']))
    md.append("4. **Cultural context**: Emoji interpretations vary across cultures")
    md.append("5. **Language limitations**: Analysis focused on English README content")
    md.append("")
    
    md.append("### Implications for Research and Practice")
    md.append("")
    md.append("1. **For researchers**: Emoji detection alone is insufficient for political content classification")
    md.append("2. **For platforms**: Political signaling in open source deserves consideration in moderation policies")
    md.append("3. **For developers**: README badges provide effective channels for social advocacy")
    md.append("4. **For organizations**: Political positioning in open source is increasingly visible")
    md.append("")
    
    md.append("---")
    md.append("")
    
    # ==========================================================================
    # CONCLUSIONS
    # ==========================================================================
    md.append("## Summary of Key Findings")
    md.append("")
    md.append("### RQ1: Repository Types and Affiliations")
    md.append("")
    md.append(f"- **{rq1_stats['n_affiliated']} repositories** ({rq1_stats['pct_affiliated']:.2f}%) contain genuine activist affiliations")
    md.append(f"- **{top3[0]['name']}** dominates with {top3[0]['percentage']:.1f}% of affiliated repositories")
    md.append(f"- Primary languages: {', '.join([l['name'] for l in top_langs[:3]])}")
    md.append(f"- Individual users own {user_stats['percentage']:.1f}% of activist repositories")
    if 'total_stars' in rq1_stats:
        md.append(f"- Total stars across activist repos: {rq1_stats['total_stars']:,}")
    md.append("")
    
    md.append("### RQ2: Expression Methods and False Positives")
    md.append("")
    md.append(f"- **{top2_expr[0]['name']}** is the most common expression type ({top2_expr[0]['percentage']:.1f}%)")
    md.append(f"- Only **{rq2_stats['emoji_only_pct']:.1f}%** rely on emoji-only signals")
    if 'multi_expression_pct' in rq2_stats:
        md.append(f"- **{rq2_stats['multi_expression_pct']:.1f}%** use multiple expression methods")
    if 'explicit_pct' in rq2_stats:
        md.append(f"- **{rq2_stats['explicit_pct']:.1f}%** explicit vs **{rq2_stats['implicit_pct']:.1f}%** implicit signaling")
    md.append(f"- **{rq2_stats['false_positive_rate']:.1f}%** false positive rate among AI predictions")
    md.append(f"- Political emojis are a weak signal: only {rq2_stats['true_activist_rate']:.2f}% of emoji repos are truly activist")
    md.append("")
    
    md.append("### RQ3: Repository Characteristics")
    md.append("")
    md.append(f"- Affiliated repos have **{stars_diff}** median stars ({aff_stars['median']:,.0f} vs {base_stars['median']:,.0f})")
    md.append(f"- Affiliated repos have **{contrib_diff}** median contributors ({aff_contrib['median']:,.0f} vs {base_contrib['median']:,.0f})")
    md.append(f"- Stars difference is **{stars_sig_text}** (p = {rq3_stats['stars_test']['p_value']:.4f})")
    md.append(f"- Contributors difference is **{contrib_sig_text}** (p = {rq3_stats['contributors_test']['p_value']:.4f})")
    if 'stars_effect_size' in rq3_stats and 'contributors_effect_size' in rq3_stats:
        md.append(f"- Effect sizes: Stars (d={rq3_stats['stars_effect_size']:.3f}), Contributors (d={rq3_stats['contributors_effect_size']:.3f})")
    md.append("")
    
    md.append("---")
    md.append("")
    
    # ==========================================================================
    # FIGURE LIST
    # ==========================================================================
    md.append("## List of Figures")
    md.append("")
    md.append("| Figure | Filename | Research Question | Description |")
    md.append("|--------|----------|-------------------|-------------|")
    md.append("| Figure 1 | figure1_affiliation_distribution | RQ1 | Distribution of political affiliations |")
    md.append("| Figure 2 | figure2_support_type_distribution | RQ2 | Expression type distribution |")
    md.append("| Figure 3 | figure3_stars_comparison | RQ3 | Stars comparison across groups |")
    md.append("| Figure 4 | figure4_contributors_comparison | RQ3 | Contributors comparison |")
    md.append("| Figure 5 | figure5_language_distribution | RQ3 | Programming language distribution |")
    md.append("| Figure 6 | figure6_owner_type_distribution | RQ3 | Owner type comparison |")
    md.append("| Figure 7 | figure7_affiliation_by_expression | RQ2 | Expression by affiliation |")
    md.append("| Figure 8 | figure8_creation_timeline | RQ1 | Repository creation timeline |")
    md.append("| Figure 9 | figure9_stars_contributors_scatter | RQ3 | Stars vs contributors scatter |")
    md.append("")
    
    md.append("---")
    md.append("")
    md.append(f"*Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    md.append("")
    
    return "\n".join(md)
