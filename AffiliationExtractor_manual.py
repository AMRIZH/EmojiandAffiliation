import pandas as pd
import webbrowser
import os
from datetime import datetime

# ============================
# CONFIGURATION
# ============================
INPUT_CSV = r"datasets/affiliated_deepseek_1000_200000.csv"  # Input CSV file
OUTPUT_CSV = r"datasets/affiliated_manual.csv"  # Output CSV with manual classifications
PROGRESS_FILE = "manual_annotation_progress.txt"  # Hidden file to track progress

# Affiliation codes (single letter shortcuts)
AFFILIATION_CODES = {
    'i': 'israel',
    'p': 'palestine',
    'b': 'blm',
    'u': 'ukraine',
    'c': 'climate',
    'f': 'feminism',
    'l': 'lgbtq',
    'd': 'democrats',
    'r': 'republican',
    'n': 'none',
}

# ============================


class ManualAnnotator:
    def __init__(self, input_file, output_file, progress_file):
        """
        Initialize the Manual Annotator
        
        Args:
            input_file: Input CSV filename
            output_file: Output CSV filename
            progress_file: Progress tracking file
        """
        self.input_file = input_file
        self.output_file = output_file
        self.progress_file = progress_file
        self.df = None
        self.current_index = 0
        self.annotations = {}
    
    def load_data(self):
        """Load CSV and restore progress if exists"""
        print(f"\n{'='*60}")
        print("MANUAL AFFILIATION ANNOTATOR")
        print(f"{'='*60}\n")
        
        # Load input CSV
        if not os.path.exists(self.input_file):
            print(f"❌ Error: File not found - {self.input_file}")
            return False
        
        try:
            print(f"📂 Loading {self.input_file}...")
            self.df = pd.read_csv(self.input_file, encoding='utf-8', low_memory=False)
            print(f"✅ Loaded {len(self.df):,} repositories\n")
        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            return False
        
        # Load progress if exists
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r') as f:
                    self.current_index = int(f.read().strip())
                print(f"📋 Resuming from index {self.current_index} ({self.current_index}/{len(self.df)})")
            except:
                self.current_index = 0
        
        # Load existing annotations if output file exists
        if os.path.exists(self.output_file):
            try:
                existing_df = pd.read_csv(self.output_file, encoding='utf-8')
                
                # Build annotations dictionary from existing data (only non-'none' values)
                count = 0
                for idx, row in existing_df.iterrows():
                    repo_url = row.get('repo_url', '')
                    affiliation = row.get('affiliation_manual', 'none')
                    # Only load actual annotations (not default 'none' values)
                    if affiliation != 'none':
                        self.annotations[repo_url] = affiliation
                        count += 1
                
                if count > 0:
                    print(f"📋 Found {count:,} existing annotations\n")
            except Exception as e:
                print(f"⚠️  Could not load existing annotations: {e}\n")
        
        return True
    
    def save_progress(self):
        """Save current progress index"""
        try:
            with open(self.progress_file, 'w') as f:
                f.write(str(self.current_index))
        except Exception as e:
            print(f"⚠️  Warning: Could not save progress: {e}")
    
    def save_annotations(self):
        """Save all annotations to output CSV"""
        try:
            # Create a copy of the dataframe with manual annotations
            output_df = self.df.copy()
            
            # Add manual affiliation column
            output_df['affiliation_manual'] = output_df['repo_url'].map(self.annotations).fillna('none')
            
            # Save to CSV
            output_df.to_csv(self.output_file, index=False, encoding='utf-8')
            
            return True
        except Exception as e:
            print(f"❌ Error saving annotations: {e}")
            return False
    
    def display_help(self):
        """Display help information"""
        print(f"\n{'='*60}")
        print("AFFILIATION CODES")
        print(f"{'='*60}")
        for code, affiliation in sorted(AFFILIATION_CODES.items()):
            print(f"  {code.upper()} = {affiliation.capitalize()}")
        print(f"\n  X or EXIT = Save and quit")
        print(f"  SKIP or S = Skip this repository")
        print(f"  HELP or H = Show this help")
        print(f"{'='*60}\n")
    
    def annotate(self):
        """Main annotation loop"""
        self.display_help()
        
        total = len(self.df)
        annotated_count = len(self.annotations)
        
        print(f"Progress: {annotated_count}/{total} annotated ({(annotated_count/total*100):.1f}%)")
        print(f"Starting from index: {self.current_index}\n")
        
        while self.current_index < total:
            row = self.df.iloc[self.current_index]
            
            repo_owner = row.get('repo_owner', 'unknown')
            repo_name = row.get('repo_name', 'unknown')
            repo_url = row.get('repo_url', '')
            repo_stars = row.get('repo_stars', 0)
            description = row.get('description', '')
            found_emojis = row.get('found_emojis', '')
            
            # Check if already annotated
            if repo_url in self.annotations:
                print(f"[{self.current_index + 1}/{total}] ⏭️  Already annotated: {repo_owner}/{repo_name} → {self.annotations[repo_url].upper()}")
                self.current_index += 1
                continue
            
            # Display repository info
            print(f"\n{'='*60}")
            print(f"Repository [{self.current_index + 1}/{total}]")
            print(f"{'='*60}")
            print(f"Owner/Name: {repo_owner}/{repo_name}")
            print(f"Stars: {repo_stars:,}")
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
                user_input = input("\nEnter affiliation code (or HELP): ").strip().lower()
                
                # Handle special commands
                if user_input in ['x', 'exit']:
                    print("\n💾 Saving and exiting...")
                    self.save_progress()
                    self.save_annotations()
                    print(f"✅ Saved {len(self.annotations):,} annotations")
                    print(f"📊 Progress: {self.current_index}/{total} ({(self.current_index/total*100):.1f}%)")
                    return True
                
                elif user_input in ['skip', 's']:
                    print("⏭️  Skipped")
                    self.current_index += 1
                    break
                
                elif user_input in ['help', 'h', '?']:
                    self.display_help()
                    continue
                
                elif user_input in AFFILIATION_CODES:
                    affiliation = AFFILIATION_CODES[user_input]
                    self.annotations[repo_url] = affiliation
                    print(f"✅ Classified as: {affiliation.upper()}")
                    
                    # Auto-save every 10 annotations
                    if len(self.annotations) % 10 == 0:
                        self.save_annotations()
                        print(f"💾 Auto-saved ({len(self.annotations)} annotations)")
                    
                    self.current_index += 1
                    self.save_progress()
                    break
                
                else:
                    print(f"❌ Invalid code: '{user_input}'. Type HELP for options.")
        
        # Finished all repositories
        print(f"\n{'='*60}")
        print("🎉 ANNOTATION COMPLETE!")
        print(f"{'='*60}")
        print(f"Total annotated: {len(self.annotations):,} repositories")
        
        self.save_annotations()
        print(f"✅ Saved to: {self.output_file}")
        
        # Clean up progress file
        if os.path.exists(self.progress_file):
            os.remove(self.progress_file)
        
        return True
    
    def show_statistics(self):
        """Show annotation statistics"""
        if not self.annotations:
            print("No annotations yet.")
            return
        
        print(f"\n{'='*60}")
        print("ANNOTATION STATISTICS")
        print(f"{'='*60}")
        
        # Count affiliations
        affiliation_counts = {}
        for affiliation in self.annotations.values():
            affiliation_counts[affiliation] = affiliation_counts.get(affiliation, 0) + 1
        
        # Display counts
        total = len(self.annotations)
        for affiliation, count in sorted(affiliation_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total) * 100
            print(f"{affiliation.upper():15s}: {count:4d} ({percentage:5.1f}%)")
        
        print(f"\nTotal: {total:,} annotations")
        print(f"{'='*60}\n")


def main():
    """Main function"""
    annotator = ManualAnnotator(INPUT_CSV, OUTPUT_CSV, PROGRESS_FILE)
    
    if not annotator.load_data():
        return
    
    # Show existing statistics if any
    if annotator.annotations:
        annotator.show_statistics()
    
    # Start annotation
    annotator.annotate()


if __name__ == "__main__":
    main()
