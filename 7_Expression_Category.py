import pandas as pd
import webbrowser
import os
from datetime import datetime

# ============================
# CONFIGURATION
# ============================
INPUT_CSV = r"datasets/validity_checked_affiliated_deepseek_1000_200000.csv"  # Input CSV file with validity
OUTPUT_CSV = r"datasets/7_expression_category_labeled.csv"  # Output CSV with expression categories
OUTPUT_TXT = r"datasets/7_expression_category_report.txt"  # Output TXT report
OUTPUT_MD = r"datasets/7_expression_category_report.md"  # Output MD report
PROGRESS_FILE = "7_expression_category_progress.txt"  # File to track progress

# Expression category codes (single letter shortcuts)
EXPRESSION_CODES = {
    't': 'text_statement',
    'l': 'link_support',
    'h': 'hashtag_slogan',
    'v': 'visual_badge',
    'e': 'emoji_only',
}

# ============================


class ExpressionCategoryLabeler:
    def __init__(self, input_file, output_file, progress_file):
        """
        Initialize the Expression Category Labeler
        
        Args:
            input_file: Input CSV filename
            output_file: Output CSV filename
            progress_file: Progress tracking file
        """
        self.input_file = input_file 
        self.output_file = output_file
        self.progress_file = progress_file
        self.df = None
        self.df_full = None  # Store full original CSV
        self.current_index = 0
        self.labels = {}
    
    def load_data(self):
        """Load CSV and restore progress if exists"""
        print(f"\n{'='*60}")
        print("EXPRESSION CATEGORY LABELER")
        print(f"{'='*60}\n")
        
        # Load input CSV
        if not os.path.exists(self.input_file):
            print(f"❌ Error: File not found - {self.input_file}")
            return False
        
        try:
            print(f"📂 Loading {self.input_file}...")
            self.df_full = pd.read_csv(self.input_file, encoding='utf-8', low_memory=False)
            print(f"✅ Loaded {len(self.df_full):,} repositories\n")
        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            return False
        
        # Detect affiliation column (try multiple possible column names)
        affiliation_col = None
        for col_name in ['affiliation_manual', 'affiliation_deepseek', 'affiliation_openai', 'affiliation']:
            if col_name in self.df_full.columns:
                affiliation_col = col_name
                break
        
        if affiliation_col is None:
            print(f"❌ Error: No affiliation column found in CSV")
            print(f"   Available columns: {', '.join(self.df_full.columns)}")
            return False
        
        self.affiliation_col = affiliation_col
        print(f"📋 Using affiliation column: {affiliation_col}\n")
        
        # Check if validity column exists
        if 'validity' not in self.df_full.columns:
            print(f"❌ Error: No 'validity' column found in CSV")
            return False
        
        # Filter to only repositories with valid affiliations (explicit + implicit)
        original_count = len(self.df_full)
        self.df = self.df_full[
            self.df_full['validity'].str.lower().isin(['explicit', 'implicit'])
        ].reset_index(drop=True)
        filtered_count = len(self.df)
        
        print(f"🔍 Filtered repositories:")
        print(f"   Original: {original_count:,}")
        print(f"   With valid affiliation (explicit + implicit): {filtered_count:,}")
        print(f"   Filtered out: {original_count - filtered_count:,}\n")
        
        if filtered_count == 0:
            print(f"❌ No repositories with valid affiliations found!")
            return False
        
        # Load progress if exists
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r') as f:
                    self.current_index = int(f.read().strip())
                print(f"📋 Resuming from index {self.current_index} ({self.current_index}/{len(self.df)})")
            except:
                self.current_index = 0
        
        # Load existing labels if output file exists
        if os.path.exists(self.output_file):
            try:
                existing_df = pd.read_csv(self.output_file, encoding='utf-8')
                
                # Build labels dictionary from existing data
                count = 0
                for idx, row in existing_df.iterrows():
                    repo_url = row.get('repo_url', '')
                    expression_category = row.get('expression_category', '')
                    # Only load actual labels (not empty values)
                    if expression_category:
                        # Handle both single and multiple categories
                        categories = [cat.strip() for cat in str(expression_category).split()]
                        valid_categories = [cat for cat in categories if cat in EXPRESSION_CODES.values()]
                        if valid_categories:
                            self.labels[repo_url] = ' '.join(valid_categories)
                            count += 1
                
                if count > 0:
                    print(f"📋 Found {count:,} existing labels\n")
            except Exception as e:
                print(f"⚠️  Could not load existing labels: {e}\n")
        
        return True
    
    def save_progress(self):
        """Save current progress index"""
        try:
            with open(self.progress_file, 'w') as f:
                f.write(str(self.current_index))
        except Exception as e:
            print(f"⚠️  Warning: Could not save progress: {e}")
    
    def save_labels(self):
        """Save all labels to output CSV (only valid affiliation repos)"""
        try:
            # Create a copy of the filtered dataframe (only valid affiliations)
            output_df = self.df.copy()
            
            # Add expression_category column
            output_df['expression_category'] = output_df['repo_url'].map(self.labels).fillna('')
            
            # Save to CSV
            output_df.to_csv(self.output_file, index=False, encoding='utf-8')
            
            return True
        except Exception as e:
            print(f"❌ Error saving labels: {e}")
            return False
    
    def display_help(self):
        """Display help information"""
        print(f"\n{'='*60}")
        print("EXPRESSION CATEGORY CODES")
        print(f"{'='*60}")
        print(f"  T = Text statement")
        print(f"      Clear sentence showing support or stance.")
        print(f"      Example: 'We stand with Ukraine 🇺🇦.'")
        print(f"")
        print(f"  L = Link support")
        print(f"      Main signal is an external link related to activism.")
        print(f"      Example: 'Donate here: https://...', 'Support BLM via this fund.'")
        print(f"")
        print(f"  H = Hashtag or slogan")
        print(f"      Uses campaign hashtags or short slogans.")
        print(f"      Example: #BlackLivesMatter, 'Stand With Palestine.'")
        print(f"")
        print(f"  V = Visual or badge")
        print(f"      Uses image, banner, or badge as the main signal.")
        print(f"      Example: Shields.io badge, banner image with flag or protest message.")
        print(f"")
        print(f"  E = Emoji only")
        print(f"      Only activist emoji, no activist text, link, or image.")
        print(f"      Example: project description has only '🇺🇦' or '🏳️‍🌈' as the signal.")
        print(f"")
        print(f"  MULTIPLE CATEGORIES: Separate with spaces (e.g., 't v' for text + visual)")
        print(f"")
        print(f"  X or EXIT = Save and quit")
        print(f"  SKIP or S = Skip this repository")
        print(f"  HELP = Show this help")
        print(f"{'='*60}\n")
    
    def label_expressions(self):
        """Main labeling loop"""
        self.display_help()
        
        total = len(self.df)
        labeled_count = len(self.labels)
        
        print(f"Progress: {labeled_count}/{total} labeled ({(labeled_count/total*100):.1f}%)")
        print(f"Starting from index: {self.current_index}\n")
        
        while self.current_index < total:
            row = self.df.iloc[self.current_index]
            
            repo_owner = row.get('repo_owner', 'unknown')
            repo_name = row.get('repo_name', 'unknown')
            repo_url = row.get('repo_url', '')
            repo_stars = row.get('repo_stars', 0)
            description = row.get('description', '')
            # Handle NaN/float values
            if pd.isna(description) or not isinstance(description, str):
                description = ''
            found_emojis = row.get('found_emojis', '')
            if pd.isna(found_emojis) or not isinstance(found_emojis, str):
                found_emojis = ''
            affiliation = row.get(self.affiliation_col, 'unknown')
            validity = row.get('validity', 'unknown')
            
            # Check if already labeled
            if repo_url in self.labels:
                print(f"[{self.current_index + 1}/{total}] ⏭️  Already labeled: {repo_owner}/{repo_name} → {self.labels[repo_url].upper()}")
                self.current_index += 1
                continue
            
            # Display repository info
            print(f"\n{'='*60}")
            print(f"Repository [{self.current_index + 1}/{total}]")
            print(f"{'='*60}")
            print(f"Owner/Name: {repo_owner}/{repo_name}")
            print(f"Stars: {repo_stars:,}")
            print(f"Affiliation: {affiliation.upper()} (Validity: {validity.upper()})")
            if description:
                print(f"Description: {description[:200]}{'...' if len(description) > 200 else ''}")
            if found_emojis:
                print(f"Emojis: {found_emojis}")
            print(f"URL: {repo_url}")
            print(f"{'='*60}")
            
            # Open in browser
            try:
                webbrowser.open(repo_url)
                print("🌐 Opening in browser...")
            except Exception as e:
                print(f"⚠️  Could not open browser: {e}")
            
            # Get user input
            while True:
                user_input = input(f"\nExpression category? (T/L/H/V/E/F or HELP): ").strip().lower()
                
                # Handle special commands
                if user_input in ['x', 'exit']:
                    print("\n💾 Saving and exiting...")
                    self.save_progress()
                    self.save_labels()
                    print(f"✅ Saved {len(self.labels):,} labels")
                    print(f"📊 Progress: {self.current_index}/{total} ({(self.current_index/total*100):.1f}%)")
                    return True
                
                elif user_input in ['skip', 's']:
                    print("⏭️  Skipped")
                    self.current_index += 1
                    break
                
                elif user_input in ['help', '?']:
                    self.display_help()
                    continue
                
                else:
                    # Parse input - can be single or multiple codes separated by spaces
                    codes = user_input.split()
                    categories = []
                    invalid_codes = []
                    
                    for code in codes:
                        if code in EXPRESSION_CODES:
                            categories.append(EXPRESSION_CODES[code])
                        else:
                            invalid_codes.append(code)
                    
                    if invalid_codes:
                        print(f"❌ Invalid code(s): {', '.join(invalid_codes)}. Type HELP for options.")
                    elif categories:
                        # Save as space-separated categories
                        self.labels[repo_url] = ' '.join(categories)
                        category_names = [cat.upper().replace('_', ' ') for cat in categories]
                        print(f"✅ Labeled as: {' + '.join(category_names)}")
                        
                        # Auto-save every 10 labels
                        if len(self.labels) % 10 == 0:
                            self.save_labels()
                            print(f"💾 Auto-saved ({len(self.labels)} labels)")
                        
                        self.current_index += 1
                        self.save_progress()
                        break
                    else:
                        print(f"❌ Invalid code: '{user_input}'. Type HELP for options.")
        
        # Finished all repositories
        print(f"\n{'='*60}")
        print("🎉 LABELING COMPLETE!")
        print(f"{'='*60}")
        print(f"Total labeled: {len(self.labels):,} repositories")
        
        self.save_labels()
        print(f"✅ Saved to: {self.output_file}")
        
        # Generate reports
        self.generate_reports()
        
        # Clean up progress file
        if os.path.exists(self.progress_file):
            os.remove(self.progress_file)
        
        return True
    
    def show_statistics(self):
        """Show labeling statistics"""
        if not self.labels:
            print("No labels yet.")
            return
        
        print(f"\n{'='*60}")
        print("LABELING STATISTICS")
        print(f"{'='*60}")
        
        # Count individual categories (handle multiple categories)
        category_counts = {}
        for categories_str in self.labels.values():
            for category in categories_str.split():
                category_counts[category] = category_counts.get(category, 0) + 1
        
        # Display counts
        total = len(self.labels)
        print(f"\nTotal repositories labeled: {total:,}")
        print(f"\nCategory distribution (repos can have multiple):")
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total) * 100
            print(f"  {category.upper().replace('_', ' '):20s}: {count:4d} ({percentage:5.1f}%)")
        
        # Count combination patterns
        combo_counts = {}
        for categories_str in self.labels.values():
            combo_counts[categories_str] = combo_counts.get(categories_str, 0) + 1
        
        print(f"\nCategory combinations:")
        for combo, count in sorted(combo_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total) * 100
            combo_display = ' + '.join([c.upper().replace('_', ' ') for c in combo.split()])
            print(f"  {combo_display:40s}: {count:4d} ({percentage:5.1f}%)")
        
        print(f"{'='*60}\n")
    
    def generate_reports(self):
        """Generate TXT and MD reports with statistics"""
        if not self.df.empty:
            try:
                # Load the output CSV with labels
                df_labeled = pd.read_csv(self.output_file, encoding='utf-8')
                
                print(f"\n📊 Generating reports...")
                
                # Generate TXT report
                self.generate_txt_report(df_labeled)
                print(f"✅ TXT report saved to: {OUTPUT_TXT}")
                
                # Generate MD report
                self.generate_md_report(df_labeled)
                print(f"✅ MD report saved to: {OUTPUT_MD}")
                
            except Exception as e:
                print(f"⚠️  Error generating reports: {e}")
    
    def generate_txt_report(self, df):
        """Generate text report"""
        with open(OUTPUT_TXT, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("EXPRESSION CATEGORY ANALYSIS REPORT\n")
            f.write("="*80 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Repositories: {len(df):,}\n\n")
            
            # Summary statistics
            f.write("-"*80 + "\n")
            f.write("SUMMARY STATISTICS\n")
            f.write("-"*80 + "\n\n")
            
            # Count individual categories
            category_counts = {}
            for categories_str in df['expression_category']:
                if pd.notna(categories_str) and categories_str:
                    for category in str(categories_str).split():
                        category_counts[category] = category_counts.get(category, 0) + 1
            
            f.write(f"Category Usage (repositories can have multiple):\n")
            for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / len(df)) * 100
                f.write(f"  {category.upper().replace('_', ' '):20s}: {count:4d} ({percentage:5.1f}%)\n")
            
            # Affiliation breakdown
            f.write(f"\n\nAffiliation Distribution:\n")
            aff_counts = df['affiliation_deepseek'].value_counts()
            for aff, count in aff_counts.items():
                percentage = (count / len(df)) * 100
                f.write(f"  {str(aff).upper():15s}: {count:4d} ({percentage:5.1f}%)\n")
            
            # Validity breakdown
            f.write(f"\n\nValidity Distribution:\n")
            val_counts = df['validity'].value_counts()
            for val, count in val_counts.items():
                percentage = (count / len(df)) * 100
                f.write(f"  {str(val).upper():15s}: {count:4d} ({percentage:5.1f}%)\n")
            
            # Repository statistics
            f.write(f"\n\nRepository Statistics:\n")
            f.write(f"  Total Stars: {df['repo_stars'].sum():,}\n")
            f.write(f"  Average Stars: {df['repo_stars'].mean():.0f}\n")
            f.write(f"  Median Stars: {df['repo_stars'].median():.0f}\n")
            f.write(f"  Min Stars: {df['repo_stars'].min():,}\n")
            f.write(f"  Max Stars: {df['repo_stars'].max():,}\n")
            
            # Owner type
            f.write(f"\n\nOwner Type:\n")
            owner_counts = df['owner_type'].value_counts()
            for owner, count in owner_counts.items():
                percentage = (count / len(df)) * 100
                f.write(f"  {str(owner):15s}: {count:4d} ({percentage:5.1f}%)\n")
            
            # Top languages
            f.write(f"\n\nTop 10 Languages:\n")
            lang_counts = df['language'].value_counts().head(10)
            for lang, count in lang_counts.items():
                percentage = (count / len(df)) * 100
                f.write(f"  {str(lang):20s}: {count:4d} ({percentage:5.1f}%)\n")
    
    def generate_md_report(self, df):
        """Generate markdown report"""
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
                    contributors = str(row.get('contributors', 'N/A'))
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
    """Main function"""
    labeler = ExpressionCategoryLabeler(INPUT_CSV, OUTPUT_CSV, PROGRESS_FILE)
    
    if not labeler.load_data():
        return
    
    # Show existing statistics if any
    if labeler.labels:
        labeler.show_statistics()
    
    # Start labeling
    labeler.label_expressions()


if __name__ == "__main__":
    main()
