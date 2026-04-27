import pandas as pd
from datetime import datetime
import os

# ============================
# CONFIGURATION - Edit these variables
# ============================
INPUT_CSV = r"datasets/validity_checked_affiliated_deepseek_1000_200000.csv"  # Input CSV file with affiliations
# Supported: github_affiliation_deepseek.csv, github_affiliation_openai.csv, github_affiliation_combined.csv
OUTPUT_TXT = r"datasets/validity_checked_affiliated_deepseek_1000_200000.txt"  # Output text file
OUTPUT_MD = r"datasets/validity_checked_affiliated_deepseek_1000_200000.md"  # Output markdown file
EXCLUDE_NONE = True  # Set to True to exclude repos with 'none' affiliation
# ============================

class AffiliationSamplePrinter:
    def __init__(self, input_csv, output_txt, exclude_none=True):
        """
        Initialize the Affiliation Sample Printer
        
        Args:
            input_csv: Input CSV file with affiliation data
            output_txt: Output text file path
            exclude_none: Whether to exclude repos with 'none' affiliation
        """
        self.input_csv = input_csv
        self.output_txt = output_txt
        self.exclude_none = exclude_none
        self.df = None
    
    def load_data(self):
        """
        Load CSV data
        
        Returns:
            Success status
        """
        if not os.path.exists(self.input_csv):
            print(f"❌ File not found: {self.input_csv}")
            return False
        
        try:
            self.df = pd.read_csv(self.input_csv)
            print(f"✅ Loaded {self.input_csv}")
            print(f"   Total rows: {len(self.df):,}")
            
            # Detect available affiliation columns
            has_deepseek = 'affiliation_deepseek' in self.df.columns
            has_openai = 'affiliation_openai' in self.df.columns
            has_legacy = 'affiliation' in self.df.columns
            
            if has_deepseek:
                print(f"   ✓ Found affiliation_deepseek column")
            if has_openai:
                print(f"   ✓ Found affiliation_openai column")
            if has_legacy:
                print(f"   ✓ Found affiliation column (legacy)")
            
            if not (has_deepseek or has_openai or has_legacy):
                print(f"   ❌ No affiliation column found!")
                print(f"   Available columns: {', '.join(self.df.columns)}")
                return False
            
            # Create 'affiliation' column for filtering (use any available)
            if has_deepseek:
                self.df['affiliation'] = self.df['affiliation_deepseek']
            elif has_openai:
                self.df['affiliation'] = self.df['affiliation_openai']
            elif has_legacy and 'affiliation' not in self.df.columns:
                pass  # already exists
            
            if self.exclude_none:
                original_count = len(self.df)
                self.df = self.df[self.df['affiliation'] != 'none']
                print(f"   After filtering 'none': {len(self.df):,} repositories")
                print(f"   Excluded: {original_count - len(self.df):,} repositories\n")
            
            return True
        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            return False
    
    def generate_report(self):
        """
        Generate text report of affiliated repositories
        
        Returns:
            Success status
        """
        if self.df is None or len(self.df) == 0:
            print("❌ No data to process")
            return False
        
        print("📝 Generating report...\n")
        
        # Sort by affiliation and then by stars (descending)
        df_sorted = self.df.sort_values(['affiliation', 'repo_stars'], 
                                       ascending=[True, False])
        
        # Calculate statistics
        total_repos = len(df_sorted)
        explicit_count = len(df_sorted[df_sorted['validity'].str.lower() == 'explicit']) if 'validity' in df_sorted.columns else 0
        implicit_count = len(df_sorted[df_sorted['validity'].str.lower() == 'implicit']) if 'validity' in df_sorted.columns else 0
        
        # Open file for writing
        try:
            with open(self.output_txt, 'w', encoding='utf-8') as f:
                # Write header
                f.write("=" * 80 + "\n")
                f.write("GITHUB REPOSITORIES WITH POLITICAL AFFILIATION\n")
                f.write("=" * 80 + "\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"\n")
                f.write(f"SUMMARY STATISTICS:\n")
                f.write(f"  Total Repositories with Affiliation: {total_repos:,}\n")
                f.write(f"  Explicit Affiliations: {explicit_count:,} ({explicit_count/total_repos*100:.1f}%)\n")
                f.write(f"  Implicit Affiliations: {implicit_count:,} ({implicit_count/total_repos*100:.1f}%)\n")
                f.write(f"  False/Other: {total_repos - explicit_count - implicit_count:,} ({(total_repos - explicit_count - implicit_count)/total_repos*100:.1f}%)\n")
                f.write("=" * 80 + "\n\n")
                
                # Group by affiliation
                affiliations = df_sorted['affiliation'].unique()
                
                for affiliation in sorted(affiliations):
                    aff_data = df_sorted[df_sorted['affiliation'] == affiliation]
                    
                    # Affiliation section header
                    f.write("\n" + "=" * 80 + "\n")
                    f.write(f"AFFILIATION: {affiliation.upper()}\n")
                    f.write(f"Count: {len(aff_data):,} repositories\n")
                    f.write("=" * 80 + "\n\n")
                    
                    # List repositories
                    for idx, (_, row) in enumerate(aff_data.iterrows(), 1):
                        owner = row.get('repo_owner', 'unknown')
                        name = row.get('repo_name', 'unknown')
                        stars = row.get('repo_stars', 0)
                        url = row.get('repo_url', '')
                        found_emojis = row.get('found_emojis', '')
                        # Try both column names for contributors
                        contributors = row.get('contributors', row.get('contributor_count', 0))
                        validity = row.get('validity', '')
                        
                        f.write(f"[{idx}] {owner}/{name}\n")
                        f.write(f"    Stars: {stars:,}\n")
                        f.write(f"    Contributors: {contributors:,}\n")
                        f.write(f"    URL: {url}\n")
                        if found_emojis:
                            f.write(f"    Emojis: {found_emojis}\n")
                        
                        # Show all available affiliation columns
                        if 'affiliation_deepseek' in row and pd.notna(row.get('affiliation_deepseek')):
                            f.write(f"    Affiliation (DeepSeek): {row['affiliation_deepseek'].upper()}\n")
                        if 'affiliation_openai' in row and pd.notna(row.get('affiliation_openai')):
                            f.write(f"    Affiliation (OpenAI): {row['affiliation_openai'].upper()}\n")
                        if 'affiliation' in row and pd.notna(row.get('affiliation')):
                            # Only show legacy if no deepseek/openai columns exist
                            if 'affiliation_deepseek' not in row and 'affiliation_openai' not in row:
                                f.write(f"    Affiliation: {row['affiliation'].upper()}\n")
                        
                        # Show validity if available
                        if validity and pd.notna(validity):
                            f.write(f"    Validity: {validity.upper()}\n")
                        
                        f.write("\n")
                
                # Write summary
                f.write("\n" + "=" * 80 + "\n")
                f.write("SUMMARY BY AFFILIATION\n")
                f.write("=" * 80 + "\n\n")
                
                for affiliation in sorted(affiliations):
                    count = len(df_sorted[df_sorted['affiliation'] == affiliation])
                    percentage = (count / len(df_sorted)) * 100
                    total_stars = df_sorted[df_sorted['affiliation'] == affiliation]['repo_stars'].sum()
                    avg_stars = df_sorted[df_sorted['affiliation'] == affiliation]['repo_stars'].mean()
                    
                    # Count validity types per affiliation
                    aff_explicit = len(df_sorted[(df_sorted['affiliation'] == affiliation) & (df_sorted['validity'].str.lower() == 'explicit')]) if 'validity' in df_sorted.columns else 0
                    aff_implicit = len(df_sorted[(df_sorted['affiliation'] == affiliation) & (df_sorted['validity'].str.lower() == 'implicit')]) if 'validity' in df_sorted.columns else 0
                    
                    f.write(f"{affiliation.upper():15s}: {count:4d} repos ({percentage:5.1f}%) | "
                           f"Stars: {total_stars:,} (avg: {avg_stars:,.0f}) | "
                           f"Explicit: {aff_explicit} | Implicit: {aff_implicit}\n")
                
                f.write("\n" + "=" * 80 + "\n")
                f.write("END OF REPORT\n")
                f.write("=" * 80 + "\n")
            
            print(f"✅ Report generated successfully!")
            print(f"📄 Output file: {self.output_txt}")
            
            # Print statistics
            print(f"\n📊 Statistics:")
            for affiliation in sorted(affiliations):
                count = len(df_sorted[df_sorted['affiliation'] == affiliation])
                print(f"   {affiliation.upper():15s}: {count:4d} repositories")
            
            return True
            
        except Exception as e:
            print(f"❌ Error generating report: {e}")
            return False
    
    def generate_simple_list(self, output_file=None):
        """
        Generate a simple list format as markdown (one line per repo)
        
        Args:
            output_file: Optional different output filename
        
        Returns:
            Success status
        """
        if self.df is None or len(self.df) == 0:
            print("❌ No data to process")
            return False
        
        if output_file is None:
            output_file = OUTPUT_MD
        
        print(f"\n📝 Generating simple markdown list...")
        
        # Sort by affiliation and then by stars (descending)
        df_sorted = self.df.sort_values(['affiliation', 'repo_stars'], 
                                       ascending=[True, False])
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                # Write markdown header
                f.write("# GitHub Repositories with Political Affiliation\n\n")
                f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n")
                f.write(f"**Total Repositories:** {len(df_sorted):,}\n\n")
                f.write("---\n\n")
                
                # Group by affiliation and create sections
                affiliations = sorted(df_sorted['affiliation'].unique())
                
                for affiliation in affiliations:
                    aff_data = df_sorted[df_sorted['affiliation'] == affiliation]
                    
                    # Section header
                    f.write(f"## {affiliation.upper()} ({len(aff_data):,} repositories)\n\n")
                    
                    # Check if validity column exists
                    has_validity = 'validity' in self.df.columns and self.df['validity'].notna().any()
                    
                    # Table header
                    if has_validity:
                        f.write("| Repository | Stars | Contributors | Emojis | Affiliation | Validity |\n")
                        f.write("|------------|-------|--------------|--------|-------------|----------|\n")
                    else:
                        f.write("| Repository | Stars | Contributors | Emojis | Affiliation |\n")
                        f.write("|------------|-------|--------------|--------|-------------|\n")
                    
                    # Write each repo as table row
                    for _, row in aff_data.iterrows():
                        owner = row.get('repo_owner', 'unknown')
                        name = row.get('repo_name', 'unknown')
                        stars = row.get('repo_stars', 0)
                        url = row.get('repo_url', '')
                        found_emojis = row.get('found_emojis', '')
                        # Try both column names for contributors
                        contributors = row.get('contributors', row.get('contributor_count', 0))
                        validity = row.get('validity', '')
                        
                        # Build affiliation string showing all available columns
                        aff_parts = []
                        if 'affiliation_deepseek' in row and pd.notna(row.get('affiliation_deepseek')):
                            aff_parts.append(f"DS:{row['affiliation_deepseek'].upper()}")
                        if 'affiliation_openai' in row and pd.notna(row.get('affiliation_openai')):
                            aff_parts.append(f"OAI:{row['affiliation_openai'].upper()}")
                        if not aff_parts and 'affiliation' in row and pd.notna(row.get('affiliation')):
                            aff_parts.append(row['affiliation'].upper())
                        
                        affiliation_str = " / ".join(aff_parts) if aff_parts else "NONE"
                        emoji_str = found_emojis if found_emojis else "-"
                        validity_str = validity.upper() if validity and pd.notna(validity) else "-"
                        
                        # Format as markdown table row
                        if has_validity:
                            f.write(f"| [{owner}/{name}]({url}) | {stars:,} | {contributors:,} | {emoji_str} | {affiliation_str} | {validity_str} |\n")
                        else:
                            f.write(f"| [{owner}/{name}]({url}) | {stars:,} | {contributors:,} | {emoji_str} | {affiliation_str} |\n")
                    
                    f.write("\n")
                
                # Write summary section
                f.write("---\n\n")
                f.write("## Summary by Affiliation\n\n")
                f.write("| Affiliation | Count | Percentage | Total Stars | Avg Stars |\n")
                f.write("|-------------|-------|------------|-------------|----------|\n")
                
                for affiliation in affiliations:
                    count = len(df_sorted[df_sorted['affiliation'] == affiliation])
                    percentage = (count / len(df_sorted)) * 100
                    total_stars = df_sorted[df_sorted['affiliation'] == affiliation]['repo_stars'].sum()
                    avg_stars = df_sorted[df_sorted['affiliation'] == affiliation]['repo_stars'].mean()
                    
                    f.write(f"| {affiliation.upper()} | {count:,} | {percentage:.1f}% | {total_stars:,} | {avg_stars:,.0f} |\n")
                
                f.write("\n---\n")
            
            print(f"✅ Markdown list generated!")
            print(f"📄 Output file: {output_file}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error generating markdown list: {e}")
            return False
    
    def run(self):
        """
        Main method to run the report generator
        
        Returns:
            Success status
        """
        print("\n" + "=" * 80)
        print("AFFILIATION SAMPLE PRINTER")
        print("=" * 80 + "\n")
        
        # Load data
        if not self.load_data():
            return False
        
        # Generate detailed report
        success1 = self.generate_report()
        
        # Generate markdown list
        success2 = self.generate_simple_list()
        
        if success1 or success2:
            print("\n✅ Reports generated successfully!")
            return True
        else:
            print("\n❌ Report generation failed!")
            return False


def main():
    """
    Main function to generate affiliation sample reports
    """
    print("\n" + "=" * 80)
    print("GITHUB REPOSITORY AFFILIATION SAMPLE GENERATOR")
    print("=" * 80)
    print(f"\nInput CSV: {INPUT_CSV}")
    print(f"Output TXT: {OUTPUT_TXT}")
    print(f"Output MD: {OUTPUT_MD}")
    print(f"Exclude 'none': {EXCLUDE_NONE}")
    
    # Create printer instance
    printer = AffiliationSamplePrinter(INPUT_CSV, OUTPUT_TXT, EXCLUDE_NONE)
    
    # Generate reports
    success = printer.run()
    
    if success:
        print("\n✅ All reports completed successfully!")
    else:
        print("\n❌ Report generation failed!")


if __name__ == "__main__":
    main()
