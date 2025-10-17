import pandas as pd
from datetime import datetime
import os

# ============================
# CONFIGURATION - Edit these variables
# ============================
INPUT_CSV = "github_affiliation.csv"  # Input CSV file with affiliations (output from AffiliationExtractor.py)
# Alternative: "github_affiliation_openai.csv" (output from AffiliationExtractor_OpenAI.py)
OUTPUT_TXT = "affiliated_repositories.txt"  # Output text file
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
        
        # Open file for writing
        try:
            with open(self.output_txt, 'w', encoding='utf-8') as f:
                # Write header
                f.write("=" * 80 + "\n")
                f.write("GITHUB REPOSITORIES WITH POLITICAL AFFILIATION\n")
                f.write("=" * 80 + "\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Repositories: {len(df_sorted):,}\n")
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
                        
                        f.write(f"[{idx}] {owner}/{name}\n")
                        f.write(f"    Stars: {stars:,}\n")
                        f.write(f"    URL: {url}\n")
                        f.write(f"    Affiliation: {affiliation.upper()}\n")
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
                    
                    f.write(f"{affiliation.upper():15s}: {count:4d} repos ({percentage:5.1f}%) | "
                           f"Total Stars: {total_stars:,} | Avg Stars: {avg_stars:,.0f}\n")
                
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
        Generate a simple list format (one line per repo)
        
        Args:
            output_file: Optional different output filename
        
        Returns:
            Success status
        """
        if self.df is None or len(self.df) == 0:
            print("❌ No data to process")
            return False
        
        if output_file is None:
            output_file = self.output_txt.replace('.txt', '_simple.txt')
        
        print(f"\n📝 Generating simple list format...")
        
        # Sort by affiliation and then by stars (descending)
        df_sorted = self.df.sort_values(['affiliation', 'repo_stars'], 
                                       ascending=[True, False])
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                # Write header
                f.write("# GitHub Repositories with Political Affiliation\n")
                f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Total: {len(df_sorted):,} repositories\n")
                f.write("#\n")
                f.write("# Format: [AFFILIATION] Owner/Repo | Stars: N | URL\n")
                f.write("#\n\n")
                
                # Write each repo on one line
                for _, row in df_sorted.iterrows():
                    owner = row.get('repo_owner', 'unknown')
                    name = row.get('repo_name', 'unknown')
                    stars = row.get('repo_stars', 0)
                    url = row.get('repo_url', '')
                    affiliation = row.get('affiliation', 'none')
                    
                    f.write(f"[{affiliation.upper():10s}] {owner}/{name:50s} | Stars: {stars:>7,} | {url}\n")
            
            print(f"✅ Simple list generated!")
            print(f"📄 Output file: {output_file}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error generating simple list: {e}")
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
        
        # Generate simple list
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
