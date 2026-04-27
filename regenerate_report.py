#!/usr/bin/env python3
"""
Regenerate Expression Category Report
"""

import pandas as pd
from datetime import datetime

OUTPUT_CSV = r"datasets/7_expression_category_labeled.csv"
OUTPUT_MD = r"datasets/7_expression_category_report.md"

def generate_md_report(df):
    """Generate markdown report with detailed per-repository tables"""
    with open(OUTPUT_MD, 'w', encoding='utf-8') as f:
        f.write("# Expression Category Analysis Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n")
        f.write(f"**Total Repositories:** {len(df):,}\n\n")
        f.write("---\n\n")
        
        # Summary statistics
        f.write("## Summary Statistics\n\n")
        
        # Count individual categories
        category_counts = {}
        for categories_str in df['expression_category']:
            if pd.notna(categories_str) and categories_str:
                for category in str(categories_str).split():
                    category_counts[category] = category_counts.get(category, 0) + 1
        
        f.write("### Category Distribution\n\n")
        f.write("| Category | Count | Percentage |\n")
        f.write("|----------|-------|------------|\n")
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(df)) * 100
            f.write(f"| {category.replace('_', ' ').title()} | {count} | {percentage:.1f}% |\n")
        
        # Affiliation breakdown
        f.write("\n### Affiliation Distribution\n\n")
        f.write("| Affiliation | Count | Percentage |\n")
        f.write("|-------------|-------|------------|\n")
        aff_counts = df['affiliation_deepseek'].value_counts()
        for aff, count in aff_counts.items():
            percentage = (count / len(df)) * 100
            f.write(f"| {str(aff).upper()} | {count} | {percentage:.1f}% |\n")
        
        # Validity breakdown
        f.write("\n### Validity Distribution\n\n")
        f.write("| Validity | Count | Percentage |\n")
        f.write("|----------|-------|------------|\n")
        val_counts = df['validity'].value_counts()
        for val, count in val_counts.items():
            percentage = (count / len(df)) * 100
            f.write(f"| {str(val).title()} | {count} | {percentage:.1f}% |\n")
        
        # Repository statistics
        f.write("\n## Repository Statistics\n\n")
        f.write("| Metric | Value |\n")
        f.write("|--------|-------|\n")
        f.write(f"| Total Stars | {df['repo_stars'].sum():,} |\n")
        f.write(f"| Average Stars | {df['repo_stars'].mean():.0f} |\n")
        f.write(f"| Median Stars | {df['repo_stars'].median():.0f} |\n")
        f.write(f"| Min Stars | {df['repo_stars'].min():,} |\n")
        f.write(f"| Max Stars | {df['repo_stars'].max():,} |\n")
        
        # Owner type
        f.write("\n### Owner Type Distribution\n\n")
        f.write("| Owner Type | Count | Percentage |\n")
        f.write("|------------|-------|------------|\n")
        owner_counts = df['owner_type'].value_counts()
        for owner, count in owner_counts.items():
            percentage = (count / len(df)) * 100
            f.write(f"| {str(owner)} | {count} | {percentage:.1f}% |\n")
        
        # Top languages
        f.write("\n### Top 10 Languages\n\n")
        f.write("| Language | Count | Percentage |\n")
        f.write("|----------|-------|------------|\n")
        lang_counts = df['language'].value_counts().head(10)
        for lang, count in lang_counts.items():
            percentage = (count / len(df)) * 100
            f.write(f"| {str(lang)} | {count} | {percentage:.1f}% |\n")
        
        # Top repositories
        f.write("\n## Top 10 Repositories by Stars\n\n")
        f.write("| Repository | Stars | Affiliation | Expression Category |\n")
        f.write("|------------|-------|-------------|---------------------|\n")
        top_repos = df.nlargest(10, 'repo_stars')
        for _, row in top_repos.iterrows():
            repo_name = f"{row['repo_owner']}/{row['repo_name']}"
            categories = ' + '.join([c.replace('_', ' ').title() for c in str(row['expression_category']).split()])
            f.write(f"| [{repo_name}]({row['repo_url']}) | {row['repo_stars']:,} | {str(row['affiliation_deepseek']).upper()} | {categories} |\n")
        
        # Detailed repository tables by affiliation
        f.write("\n---\n\n")
        f.write("## Detailed Repository Information\n\n")
        
        # Group by affiliation
        affiliations = df['affiliation_deepseek'].value_counts().index.tolist()
        
        for affiliation in sorted(affiliations):
            aff_df = df[df['affiliation_deepseek'] == affiliation].sort_values('repo_stars', ascending=False)
            f.write(f"\n### {str(affiliation).upper()} ({len(aff_df)} repositories)\n\n")
            
            # Create detailed table
            f.write("| Repository | Stars | Contributors | Language | Owner Type | Emojis | Expression Category | Validity |\n")
            f.write("|------------|-------|--------------|----------|------------|--------|---------------------|----------|\n")
            
            for _, row in aff_df.iterrows():
                repo_name = f"{row['repo_owner']}/{row['repo_name']}"
                repo_link = f"[{repo_name}]({row['repo_url']})"
                stars = f"{row['repo_stars']:,}"
                contributors = str(int(row.get('contributors', 0))) if pd.notna(row.get('contributors')) else 'N/A'
                language = str(row.get('language', 'N/A')) if pd.notna(row.get('language')) else 'N/A'
                owner_type = str(row.get('owner_type', 'N/A'))
                emojis = str(row.get('found_emojis', '')) if pd.notna(row.get('found_emojis')) else ''
                
                # Format expression category
                expr_cat = str(row.get('expression_category', ''))
                if expr_cat and pd.notna(expr_cat):
                    categories = ' + '.join([c.replace('_', ' ').title() for c in expr_cat.split()])
                else:
                    categories = 'Not labeled'
                
                validity = str(row.get('validity', 'N/A')).upper()
                
                f.write(f"| {repo_link} | {stars} | {contributors} | {language} | {owner_type} | {emojis} | {categories} | {validity} |\n")
        
        # Summary by affiliation
        f.write("\n---\n\n")
        f.write("## Summary by Affiliation\n\n")
        f.write("| Affiliation | Count | Percentage | Total Stars | Avg Stars |\n")
        f.write("|-------------|-------|------------|-------------|----------|\n")
        
        for affiliation in sorted(affiliations):
            aff_df = df[df['affiliation_deepseek'] == affiliation]
            count = len(aff_df)
            percentage = (count / len(df)) * 100
            total_stars = aff_df['repo_stars'].sum()
            avg_stars = aff_df['repo_stars'].mean()
            f.write(f"| {str(affiliation).upper()} | {count} | {percentage:.1f}% | {total_stars:,} | {avg_stars:,.0f} |\n")

def main():
    print(f"Loading data from {OUTPUT_CSV}...")
    df = pd.read_csv(OUTPUT_CSV, encoding='utf-8')
    print(f"Loaded {len(df)} repositories")
    
    print(f"\nGenerating detailed markdown report...")
    generate_md_report(df)
    print(f"✅ Report saved to: {OUTPUT_MD}")
    print(f"\nReport includes:")
    print(f"  - Summary statistics")
    print(f"  - Category distribution")
    print(f"  - Detailed per-repository tables grouped by affiliation")
    print(f"  - Affiliation summary")

if __name__ == '__main__':
    main()
