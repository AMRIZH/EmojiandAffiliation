import pandas as pd
import webbrowser
import os
from datetime import datetime

# ============================
# CONFIGURATION
# ============================
INPUT_CSV = r"datasets/affiliated_deepseek_1000_200000.csv"  # Input CSV file with affiliation
OUTPUT_CSV = r"cache/validity_checked_affiliated_deepseek_1000_200000.csv"  # Output CSV with validity checks
PROGRESS_FILE = "validity_check_progress.txt"  # File to track progress

# Validity codes (single letter shortcuts)
VALIDITY_CODES = {
    'f': 'false',
    'i': 'implicit',
    'e': 'explicit',
}

# ============================


class ValidityChecker:
    def __init__(self, input_file, output_file, progress_file):
        """
        Initialize the Validity Checker
        
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
        self.validations = {}
    
    def load_data(self):
        """Load CSV and restore progress if exists"""
        print(f"\n{'='*60}")
        print("AFFILIATION VALIDITY CHECKER")
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
        
        # Filter to only repositories with non-'none' affiliations
        original_count = len(self.df_full)
        self.df = self.df_full[self.df_full[affiliation_col].str.lower() != 'none'].reset_index(drop=True)
        filtered_count = len(self.df)
        
        print(f"🔍 Filtered repositories:")
        print(f"   Original: {original_count:,}")
        print(f"   With affiliation (not 'none'): {filtered_count:,}")
        print(f"   Filtered out: {original_count - filtered_count:,}\n")
        
        if filtered_count == 0:
            print(f"❌ No repositories with affiliations found!")
            return False
        
        # Load progress if exists
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r') as f:
                    self.current_index = int(f.read().strip())
                print(f"📋 Resuming from index {self.current_index} ({self.current_index}/{len(self.df)})")
            except:
                self.current_index = 0
        
        # Load existing validations if output file exists
        if os.path.exists(self.output_file):
            try:
                existing_df = pd.read_csv(self.output_file, encoding='utf-8')
                
                # Build validations dictionary from existing data
                count = 0
                for idx, row in existing_df.iterrows():
                    repo_url = row.get('repo_url', '')
                    validity = row.get('validity', '')
                    # Only load actual validations (not empty values)
                    if validity and validity in ['false', 'implicit', 'explicit']:
                        self.validations[repo_url] = validity
                        count += 1
                
                if count > 0:
                    print(f"📋 Found {count:,} existing validations\n")
            except Exception as e:
                print(f"⚠️  Could not load existing validations: {e}\n")
        
        return True
    
    def save_progress(self):
        """Save current progress index"""
        try:
            with open(self.progress_file, 'w') as f:
                f.write(str(self.current_index))
        except Exception as e:
            print(f"⚠️  Warning: Could not save progress: {e}")
    
    def save_validations(self):
        """Save all validations to output CSV (full dataset with validity column)"""
        try:
            # Create a copy of the FULL dataframe (not filtered)
            output_df = self.df_full.copy()
            
            # Add validity column to full dataset
            output_df['validity'] = output_df['repo_url'].map(self.validations).fillna('')
            
            # Save to CSV
            output_df.to_csv(self.output_file, index=False, encoding='utf-8')
            
            return True
        except Exception as e:
            print(f"❌ Error saving validations: {e}")
            return False
    
    def display_help(self):
        """Display help information"""
        print(f"\n{'='*60}")
        print("VALIDITY CODES")
        print(f"{'='*60}")
        for code, validity in sorted(VALIDITY_CODES.items()):
            print(f"  {code.upper()} = {validity.capitalize()}")
        print(f"\n  X or EXIT = Save and quit")
        print(f"  SKIP or S = Skip this repository")
        print(f"  HELP or H = Show this help")
        print(f"\n  Validity Meanings:")
        print(f"  - FALSE: Affiliation is incorrect/misclassified")
        print(f"  - IMPLICIT: Affiliation is implied but not clearly stated")
        print(f"  - EXPLICIT: Affiliation is clearly and explicitly stated")
        print(f"{'='*60}\n")
    
    def check_validity(self):
        """Main validity checking loop"""
        self.display_help()
        
        total = len(self.df)
        validated_count = len(self.validations)
        
        print(f"Progress: {validated_count}/{total} validated ({(validated_count/total*100):.1f}%)")
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
            
            # Check if already validated
            if repo_url in self.validations:
                print(f"[{self.current_index + 1}/{total}] ⏭️  Already validated: {repo_owner}/{repo_name} → {self.validations[repo_url].upper()}")
                self.current_index += 1
                continue
            
            # Display repository info
            print(f"\n{'='*60}")
            print(f"Repository [{self.current_index + 1}/{total}]")
            print(f"{'='*60}")
            print(f"Owner/Name: {repo_owner}/{repo_name}")
            print(f"Stars: {repo_stars:,}")
            print(f"Affiliation: {affiliation.upper()}")
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
                user_input = input(f"\nIs '{affiliation.upper()}' affiliation valid? (F/I/E or HELP): ").strip().lower()
                
                # Handle special commands
                if user_input in ['x', 'exit']:
                    print("\n💾 Saving and exiting...")
                    self.save_progress()
                    self.save_validations()
                    print(f"✅ Saved {len(self.validations):,} validations")
                    print(f"📊 Progress: {self.current_index}/{total} ({(self.current_index/total*100):.1f}%)")
                    return True
                
                elif user_input in ['skip', 's']:
                    print("⏭️  Skipped")
                    self.current_index += 1
                    break
                
                elif user_input in ['help', 'h', '?']:
                    self.display_help()
                    continue
                
                elif user_input in VALIDITY_CODES:
                    validity = VALIDITY_CODES[user_input]
                    self.validations[repo_url] = validity
                    print(f"✅ Marked as: {validity.upper()}")
                    
                    # Auto-save every 10 validations
                    if len(self.validations) % 10 == 0:
                        self.save_validations()
                        print(f"💾 Auto-saved ({len(self.validations)} validations)")
                    
                    self.current_index += 1
                    self.save_progress()
                    break
                
                else:
                    print(f"❌ Invalid code: '{user_input}'. Type HELP for options.")
        
        # Finished all repositories
        print(f"\n{'='*60}")
        print("🎉 VALIDATION COMPLETE!")
        print(f"{'='*60}")
        print(f"Total validated: {len(self.validations):,} repositories")
        
        self.save_validations()
        print(f"✅ Saved to: {self.output_file}")
        
        # Clean up progress file
        if os.path.exists(self.progress_file):
            os.remove(self.progress_file)
        
        return True
    
    def show_statistics(self):
        """Show validation statistics"""
        if not self.validations:
            print("No validations yet.")
            return
        
        print(f"\n{'='*60}")
        print("VALIDATION STATISTICS")
        print(f"{'='*60}")
        
        # Count validations
        validity_counts = {}
        for validity in self.validations.values():
            validity_counts[validity] = validity_counts.get(validity, 0) + 1
        
        # Display counts
        total = len(self.validations)
        for validity, count in sorted(validity_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total) * 100
            print(f"{validity.upper():15s}: {count:4d} ({percentage:5.1f}%)")
        
        print(f"\nTotal: {total:,} validations")
        
        # Calculate accuracy metrics
        if 'explicit' in validity_counts or 'implicit' in validity_counts:
            correct = validity_counts.get('explicit', 0) + validity_counts.get('implicit', 0)
            accuracy = (correct / total) * 100
            print(f"\nAccuracy (Explicit + Implicit): {correct}/{total} ({accuracy:.1f}%)")
        
        print(f"{'='*60}\n")


def main():
    """Main function"""
    checker = ValidityChecker(INPUT_CSV, OUTPUT_CSV, PROGRESS_FILE)
    
    if not checker.load_data():
        return
    
    # Show existing statistics if any
    if checker.validations:
        checker.show_statistics()
    
    # Start validation
    checker.check_validity()


if __name__ == "__main__":
    main()
