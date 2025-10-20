import pandas as pd
import csv
from datetime import datetime

# ============================
# CONFIGURATION - Edit these variables
# ============================
INPUT_CSV = "github_readmes_batch.csv"  # Input CSV file to filter
OUTPUT_CSV = "Cleaned_github_readmes.csv"  # Output CSV file (default: github_filtered_TIMESTAMP.csv)

# Political emojis to search for
POLITICAL_EMOJIS = [
    # Israel & Palestine Conflict
    "🇮🇱",      # Flag: Israel - pro-Israel support
    "💙",       # Blue Heart - pro-Israel symbolism (with white heart)
    "🤍",       # White Heart - pro-Israel symbolism
    "✡️",       # Star of David - Jewish/Israeli symbol
    "�🇸",      # Flag: Palestine - pro-Palestine support
    "❤️",       # Red Heart - Palestinian flag colors (with green, white, black)
    "💚",       # Green Heart - Palestinian flag / climate activism
    "🖤",       # Black Heart - Palestinian flag / BLM
    "🍉",       # Watermelon - symbolic Palestine reference
    
    # War in Ukraine
    "🇺🇦",      # Flag: Ukraine - support for Ukraine
    "💛",       # Yellow Heart - Ukraine flag colors (with blue)
    "🌻",       # Sunflower - Ukraine's national flower
    "🇷🇺",      # Flag: Russia - pro-Russia stance
    
    # Black Lives Matter
    "✊",       # Raised Fist - BLM solidarity/resistance
    "✊🏾",      # Raised Fist: Medium-Dark Skin Tone - BLM
    "✊🏿",      # Raised Fist: Dark Skin Tone - BLM
    "🤎",       # Brown Heart - BLM/Black identity
    
    # Climate Change Activism
    "♻️",       # Recycling Symbol - climate activism
    "🌱",       # Seedling - environmental causes
    "�",       # Globe Europe-Africa - climate activism
    "�",       # Globe Americas - climate activism
    "🌏",       # Globe Asia-Australia - climate activism
    "🔥",       # Fire - climate disaster/warming
    
    # Women's Rights & Feminist Activism
    "♀️",       # Female Sign - women's rights
    "�",       # Women's Room - feminist activism
    "💔",       # Broken Heart - #MeToo/harassment protest
    "😔",       # Pensive Face - #MeToo/solidarity
    "�",       # Cooked Rice - China #MeToo (米兔 = mi tu)
    "🐰",       # Rabbit Face - China #MeToo (米兔 = mi tu)
    
    # LGBTQ+ Activism
    "�🌈",       # Rainbow - LGBTQ+ rights/Pride
    "🏳️‍🌈",    # Rainbow Flag - LGBTQ+ Pride
    "🏳️‍⚧️",    # Transgender Flag - transgender rights
]
# ============================


class CSVFilter:
    def __init__(self, input_csv, output_csv=None, emojis=None):
        """
        Initialize the CSV Filter
        
        Args:
            input_csv: Input CSV file to filter
            output_csv: Output CSV file (optional, will generate timestamp-based name if None)
            emojis: List of emojis to search for (optional, uses POLITICAL_EMOJIS if None)
        """
        self.input_csv = input_csv
        
        if output_csv is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_csv = f"github_filtered_{timestamp}.csv"
        else:
            self.output_csv = output_csv
        
        self.emojis = emojis if emojis is not None else POLITICAL_EMOJIS
        self.df = None
        self.filtered_df = None
    
    def load_csv(self):
        """
        Load CSV file using pandas
        
        Returns:
            Success status
        """
        try:
            print(f"\n{'='*60}")
            print("CSV FILTERING - Political Emoji Detection")
            print(f"{'='*60}\n")
            
            print(f"📂 Loading CSV file: {self.input_csv}")
            self.df = pd.read_csv(self.input_csv, encoding='utf-8')
            
            print(f"✅ Loaded {len(self.df):,} repositories")
            print(f"   Columns: {', '.join(self.df.columns)}\n")
            
            return True
        except FileNotFoundError:
            print(f"❌ Error: File not found - {self.input_csv}")
            return False
        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            return False
    
    def contains_emoji(self, text):
        """
        Check if text contains any of the political emojis
        
        Args:
            text: String to check for emojis
            
        Returns:
            Tuple of (bool: contains_emoji, list: found_emojis)
        """
        if pd.isna(text) or not isinstance(text, str):
            return False, []
        
        found_emojis = []
        for emoji in self.emojis:
            if emoji in text:
                found_emojis.append(emoji)
        
        return len(found_emojis) > 0, found_emojis
    
    def filter_repositories(self):
        """
        Filter repositories that contain political emojis in README or description
        
        Returns:
            Filtered DataFrame
        """
        print(f"🔍 Searching for political emojis in README and description...")
        print(f"   Emoji list: {' '.join(self.emojis)}\n")
        
        filtered_rows = []
        emoji_stats = {}
        
        for idx, row in self.df.iterrows():
            repo_owner = row.get('repo_owner', '')
            repo_name = row.get('repo_name', '')
            readme = row.get('readme', '')
            description = row.get('description', '')
            
            # Check README and description
            readme_has_emoji, readme_emojis = self.contains_emoji(readme)
            desc_has_emoji, desc_emojis = self.contains_emoji(description)
            
            # Combine found emojis
            all_found_emojis = list(set(readme_emojis + desc_emojis))
            
            if readme_has_emoji or desc_has_emoji:
                print(f"✅ [{len(filtered_rows)+1}] {repo_owner}/{repo_name}")
                print(f"   Found emojis: {' '.join(all_found_emojis)}")
                
                if readme_has_emoji:
                    print(f"   📝 README: {' '.join(readme_emojis)}")
                if desc_has_emoji:
                    print(f"   📄 Description: {' '.join(desc_emojis)}")
                print()
                
                # Track emoji statistics
                for emoji in all_found_emojis:
                    emoji_stats[emoji] = emoji_stats.get(emoji, 0) + 1
                
                # Add found emojis as a new column (space-separated string)
                row_with_emojis = row.copy()
                row_with_emojis['found_emojis'] = ' '.join(all_found_emojis)
                filtered_rows.append(row_with_emojis)
        
        self.filtered_df = pd.DataFrame(filtered_rows)
        
        print(f"\n{'='*60}")
        print(f"FILTERING RESULTS")
        print(f"{'='*60}")
        print(f"📊 Total repositories scanned: {len(self.df):,}")
        print(f"✅ Repositories with political emojis: {len(self.filtered_df):,}")
        print(f"❌ Repositories filtered out: {len(self.df) - len(self.filtered_df):,}")
        print(f"📈 Retention rate: {(len(self.filtered_df) / len(self.df) * 100):.2f}%")
        
        # Show emoji statistics
        if emoji_stats:
            print(f"\n{'='*60}")
            print(f"EMOJI STATISTICS")
            print(f"{'='*60}")
            sorted_stats = sorted(emoji_stats.items(), key=lambda x: x[1], reverse=True)
            for emoji, count in sorted_stats:
                print(f"{emoji}  : {count:3d} repositories")
        
        return self.filtered_df
    
    def save_filtered_csv(self):
        """
        Save filtered data to CSV file
        
        Returns:
            Success status
        """
        if self.filtered_df is None or len(self.filtered_df) == 0:
            print("\n⚠️  No data to save (no repositories match the filter criteria)")
            return False
        
        try:
            print(f"\n{'='*60}")
            print(f"💾 Saving filtered data to: {self.output_csv}")
            
            # Reorder columns to put found_emojis at the end
            cols = [col for col in self.filtered_df.columns if col != 'found_emojis']
            if 'found_emojis' in self.filtered_df.columns:
                cols.append('found_emojis')
            self.filtered_df = self.filtered_df[cols]
            
            self.filtered_df.to_csv(self.output_csv, index=False, encoding='utf-8')
            
            print(f"✅ Successfully saved {len(self.filtered_df):,} repositories")
            print(f"{'='*60}\n")
            
            return True
        except Exception as e:
            print(f"❌ Error saving CSV: {e}")
            return False
    
    def show_summary(self):
        """
        Display summary statistics about the filtered data
        """
        if self.filtered_df is None or len(self.filtered_df) == 0:
            return
        
        print(f"{'='*60}")
        print(f"SUMMARY STATISTICS")
        print(f"{'='*60}")
        
        # Star statistics
        if 'repo_stars' in self.filtered_df.columns:
            total_stars = self.filtered_df['repo_stars'].sum()
            avg_stars = self.filtered_df['repo_stars'].mean()
            max_stars = self.filtered_df['repo_stars'].max()
            min_stars = self.filtered_df['repo_stars'].min()
            
            print(f"\n⭐ Stars:")
            print(f"   Total: {total_stars:,}")
            print(f"   Average: {avg_stars:,.0f}")
            print(f"   Max: {max_stars:,}")
            print(f"   Min: {min_stars:,}")
        
        # Contributors statistics (with legacy support for 'collaborators')
        contrib_col = 'contributors' if 'contributors' in self.filtered_df.columns else 'collaborators'
        if contrib_col in self.filtered_df.columns:
            total_contrib = self.filtered_df[contrib_col].sum()
            avg_contrib = self.filtered_df[contrib_col].mean()
            
            print(f"\n👥 Contributors:")
            print(f"   Total: {total_contrib:,}")
            print(f"   Average: {avg_contrib:.1f}")
        
        # README statistics
        if 'readme' in self.filtered_df.columns:
            repos_with_readme = self.filtered_df['readme'].notna().sum()
            readme_lengths = self.filtered_df[self.filtered_df['readme'].notna()]['readme'].str.len()
            if len(readme_lengths) > 0:
                avg_readme_length = readme_lengths.mean()
                
                print(f"\n📝 README:")
                print(f"   Repositories with README: {repos_with_readme}/{len(self.filtered_df)}")
                print(f"   Average README length: {avg_readme_length:,.0f} characters")
        
        # Description statistics
        if 'description' in self.filtered_df.columns:
            repos_with_desc = self.filtered_df['description'].notna().sum()
            repos_with_desc = repos_with_desc - (self.filtered_df['description'] == '').sum()
            
            print(f"\n📄 Description:")
            print(f"   Repositories with description: {repos_with_desc}/{len(self.filtered_df)}")
        
        # Topics statistics
        if 'topics' in self.filtered_df.columns:
            repos_with_topics = self.filtered_df['topics'].notna().sum()
            repos_with_topics = repos_with_topics - (self.filtered_df['topics'] == '').sum()
            
            print(f"\n🏷️  Topics:")
            print(f"   Repositories with topics: {repos_with_topics}/{len(self.filtered_df)}")
        
        # Found emojis statistics
        if 'found_emojis' in self.filtered_df.columns:
            avg_emojis = self.filtered_df['found_emojis'].str.split().str.len().mean()
            max_emojis = self.filtered_df['found_emojis'].str.split().str.len().max()
            
            print(f"\n😀 Found Emojis:")
            print(f"   Average emojis per repo: {avg_emojis:.1f}")
            print(f"   Max emojis in a repo: {int(max_emojis)}")
        
        print(f"\n{'='*60}\n")
    
    def run(self):
        """
        Main method to run the filtering process
        
        Returns:
            Success status
        """
        # Load CSV
        if not self.load_csv():
            return False
        
        # Filter repositories
        self.filter_repositories()
        
        # Show summary
        self.show_summary()
        
        # Save filtered CSV
        if not self.save_filtered_csv():
            return False
        
        print("✅ Filtering completed successfully!\n")
        return True


def main():
    """
    Main function to run the CSV filter
    """
    print(f"\n{'='*60}")
    print("GITHUB REPOSITORY EMOJI FILTER")
    print(f"{'='*60}")
    print(f"\nConfiguration:")
    print(f"  Input CSV: {INPUT_CSV}")
    print(f"  Output CSV: {OUTPUT_CSV if OUTPUT_CSV else 'Auto-generated with timestamp'}")
    print(f"  Number of emojis to search: {len(POLITICAL_EMOJIS)}")
    
    # Create filter instance
    csv_filter = CSVFilter(INPUT_CSV, OUTPUT_CSV, POLITICAL_EMOJIS)
    
    # Run filtering
    success = csv_filter.run()
    
    if success:
        print(f"✅ Filtered data saved to: {csv_filter.output_csv}")
    else:
        print("❌ Filtering failed!")


if __name__ == "__main__":
    main()
