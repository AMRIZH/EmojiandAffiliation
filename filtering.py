import pandas as pd
import csv
from datetime import datetime

# ============================
# CONFIGURATION - Edit these variables
# ============================
INPUT_CSV = "github_readmes_100_300000.csv"  # Input CSV file to filter
OUTPUT_CSV = "filtered_github_1000_200000.csv"  # Output CSV file (default: github_filtered_TIMESTAMP.csv)
MIN_STARS = 1000  # Minimum number of stars (set to 0 for no minimum)
MAX_STARS = 200000  # Maximum number of stars (set to None for no maximum)
MIN_CONTRIBUTORS = 0  # Minimum number of contributors (set to 0 for no minimum)
MAX_CONTRIBUTORS = None  # Maximum number of contributors (set to None for no maximum)
INCLUDE_FORK = False  # Set to False to exclude forked repositories (only include original repos)
REFILTER = False  # Set to True to re-filter affiliation data (skips emoji detection, uses existing 'found_emojis' column)

# ============================
# RE-FILTERING AFFILIATION DATA (set REFILTER = True to use these)
# ============================
# INPUT_CSV = "github_affiliation_openai.csv"  # Affiliation extractor output
# OUTPUT_CSV = "Cleaned_github_affiliation.csv"  # Re-filtered affiliation output
# MIN_STARS = 1000  # Adjust as needed
# MAX_STARS = 200000  # Adjust as needed
# MIN_CONTRIBUTORS = 5  # Adjust as needed
# MAX_CONTRIBUTORS = None  # Adjust as needed
# REFILTER = True  # Enable re-filter mode

# Political emojis to search for (Unicode format)
POLITICAL_EMOJIS = [
    # Israel & Palestine Conflict
    "🇮🇱",      # Flag: Israel - pro-Israel support
    "💙",       # Blue Heart - pro-Israel symbolism (with white heart)
    "🤍",       # White Heart - pro-Israel symbolism
    "✡️",       # Star of David - Jewish/Israeli symbol
    "🎗",       # Reminder Ribbon - used for hostages awareness (explicit in article)
    "🇵🇸",      # Flag: Palestine - pro-Palestine support
    "❤️",       # Red Heart - Palestinian flag colors (with green, white, black)
    "💚",       # Green Heart - Palestinian flag / climate activism
    "🖤",       # Black Heart - Palestinian flag / BLM
    "🍉",       # Watermelon - symbolic Palestine reference

    # War in Ukraine
    "🇺🇦",      # Flag: Ukraine - support for Ukraine
    "💙",       # Blue Heart (duplicate but valid) - Ukraine flag colors (with yellow)
    "💛",       # Yellow Heart - Ukraine flag colors
    "🌻",       # Sunflower - Ukraine's national flower
    "🇷🇺",      # Flag: Russia - pro-Russia stance

    # Black Lives Matter
    "✊",       # Raised Fist - BLM solidarity/resistance
    "✊🏾",     # Raised Fist: Medium-Dark Skin Tone - BLM
    "✊🏿",     # Raised Fist: Dark Skin Tone - BLM
    "🖤",       # Black Heart - BLM
    "🤎",       # Brown Heart - BLM/Black identity

    # Climate Change Activism
    "♻️",       # Recycling Symbol - climate activism
    "🌱",       # Seedling - environmental causes
    "🌍",       # Globe Europe-Africa
    "🌎",       # Globe Americas
    "🌏",       # Globe Asia-Australia
    "🔥",       # Fire - climate disaster/warming

    # Women's Rights & Feminist Activism
    "♀️",       # Female Sign - women's rights
    "🚺",       # Women's Room - feminist activism
    "💔",       # Broken Heart - #MeToo/harassment protest
    "😔",       # Pensive Face - #MeToo/solidarity
    "🍚",       # Cooked Rice - China #MeToo (米兔 = mi tu)
    "🐰",       # Rabbit Face - China #MeToo (米兔 = mi tu)

    # LGBTQ+ Activism
    "🌈",       # Rainbow - LGBTQ+ rights/Pride
    "🏳️‍🌈",    # Rainbow Flag - LGBTQ+ Pride
    "🏳️‍⚧️",    # Transgender Flag - transgender rights

    # 2024 United States Election
    "🇺🇸", # US fag
    "🗳️", # ballot
    "🦅", # Eagle - US patriotic / presidential symbolism
    "🐘", # elephants (democrat party)
]

# Emoji to shortcode mapping (for markdown format detection)
EMOJI_SHORTCODES = {
    # Israel & Palestine Conflict
    "🇮🇱": [":flag_il:", ":israel:"],
    "💙": [":blue_heart:"],
    "🤍": [":white_heart:"],
    "✡️": [":star_of_david:"],
    "🎗": [":reminder_ribbon:"],
    "🇵🇸": [":flag_ps:", ":palestinian_territories:", ":palestine:"],
    "❤️": [":heart:", ":red_heart:"],
    "💚": [":green_heart:"],
    "🖤": [":black_heart:"],
    "🍉": [":watermelon:"],

    # War in Ukraine
    "🇺🇦": [":flag_ua:", ":ukraine:"],
    "💛": [":yellow_heart:"],
    "🌻": [":sunflower:"],
    "🇷🇺": [":flag_ru:", ":ru:", ":russia:"],

    # Black Lives Matter
    "✊": [":fist:", ":raised_fist:"],
    "✊🏾": [":fist_tone4:", ":raised_fist_tone4:"],
    "✊🏿": [":fist_tone5:", ":raised_fist_tone5:"],
    "🤎": [":brown_heart:"],

    # Climate Change Activism
    "♻️": [":recycle:"],
    "🌱": [":seedling:"],
    "🌍": [":earth_africa:"],
    "🌎": [":earth_americas:"],
    "🌏": [":earth_asia:"],
    "🔥": [":fire:"],

    # Women's Rights & Feminist Activism
    "♀️": [":female_sign:"],
    "🚺": [":womens:"],
    "💔": [":broken_heart:"],
    "😔": [":pensive:"],
    "🍚": [":rice:"],
    "🐰": [":rabbit:"],

    # LGBTQ+ Activism
    "🌈": [":rainbow:"],
    "🏳️‍🌈": [":rainbow_flag:", ":pride_flag:"],
    "🏳️‍⚧️": [":transgender_flag:"],

    # 2024 United States Election
    "🇺🇸": [":flag_us:", ":us:", ":usa:"],
    "🗳️": [":ballot_box_with_ballot:", ":ballot_box:"],
    "🦅": [":eagle:"],
    "🐘": [":elephant:"],
}

# ============================


class CSVFilter:
    def __init__(self, input_csv, output_csv=None, emojis=None, min_stars=None, max_stars=None, min_contributors=None, max_contributors=None, include_fork=True, refilter=False):
        """
        Initialize the CSV Filter
        
        Args:
            input_csv: Input CSV file to filter
            output_csv: Output CSV file (optional, will generate timestamp-based name if None)
            emojis: List of emojis to search for (optional, uses POLITICAL_EMOJIS if None)
            min_stars: Minimum star count (optional, filters repos below this)
            max_stars: Maximum star count (optional, filters repos above this)
            min_contributors: Minimum contributor count (optional, filters repos below this)
            max_contributors: Maximum contributor count (optional, filters repos above this)
            include_fork: If False, exclude forked repositories (optional, default True)
            refilter: If True, skip emoji detection and use existing 'found_emojis' column (for re-filtering affiliation data)
        """
        self.input_csv = input_csv
        
        if output_csv is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_csv = f"github_filtered_{timestamp}.csv"
        else:
            self.output_csv = output_csv
        
        self.emojis = emojis if emojis is not None else POLITICAL_EMOJIS
        self.min_stars = min_stars if min_stars is not None else 0
        self.max_stars = max_stars
        self.min_contributors = min_contributors if min_contributors is not None else 0
        self.max_contributors = max_contributors
        self.include_fork = include_fork
        self.refilter = refilter
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
            if self.refilter:
                print("CSV RE-FILTERING - Affiliation Data")
            else:
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
        Check if text contains any of the political emojis (Unicode or markdown shortcode)
        
        Args:
            text: String to check for emojis
            
        Returns:
            Tuple of (bool: contains_emoji, list: found_emojis)
        """
        if pd.isna(text) or not isinstance(text, str):
            return False, []
        
        found_emojis = []
        text_lower = text.lower()  # Convert to lowercase for case-insensitive shortcode matching
        
        for emoji in self.emojis:
            # Check for Unicode emoji
            if emoji in text:
                found_emojis.append(emoji)
            # Check for markdown shortcodes
            elif emoji in EMOJI_SHORTCODES:
                for shortcode in EMOJI_SHORTCODES[emoji]:
                    if shortcode in text_lower:
                        # Store the Unicode emoji (normalized format)
                        if emoji not in found_emojis:
                            found_emojis.append(emoji)
                        break
        
        return len(found_emojis) > 0, found_emojis
    
    def filter_repositories(self):
        """
        Display filtering configuration (deprecated - logic moved to run())
        
        This method now only displays the filter configuration.
        The actual filtering is done in run() to properly capture emoji_stats.
        """
        if self.refilter:
            print(f"🔍 Re-filtering repositories (using existing 'found_emojis' column)...")
        else:
            print(f"🔍 Searching for political emojis in README and description...")
            print(f"   Emoji list: {' '.join(self.emojis)}")
        if self.min_stars > 0 or self.max_stars is not None:
            star_range = f"{self.min_stars:,}"
            if self.max_stars is not None:
                star_range += f" to {self.max_stars:,}"
            else:
                star_range += "+"
            print(f"   Star range filter: {star_range} stars")
        if self.min_contributors > 0 or self.max_contributors is not None:
            contrib_range = f"{self.min_contributors:,}"
            if self.max_contributors is not None:
                contrib_range += f" to {self.max_contributors:,}"
            else:
                contrib_range += "+"
            print(f"   Contributor range filter: {contrib_range} contributors")
        print()
    
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
            
            # Reorder columns to put found_emojis at the end (only in normal mode)
            if not self.refilter:
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
    
    def save_report_to_log(self, emoji_stats):
        """
        Save filtering report to logs/filterresult.txt
        
        Args:
            emoji_stats: Dictionary of emoji statistics from filtering
        """
        import os
        
        try:
            # Create logs directory if it doesn't exist
            os.makedirs('logs', exist_ok=True)
            
            log_file = 'logs/filterresult.txt'
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"FILTERING REPORT - {timestamp}\n")
                f.write(f"{'='*60}\n")
                f.write(f"Mode: {'RE-FILTER' if self.refilter else 'FILTER'}\n")
                f.write(f"Input: {self.input_csv}\n")
                f.write(f"Output: {self.output_csv}\n")
                f.write(f"\n{'='*60}\n")
                f.write(f"FILTERING RESULTS\n")
                f.write(f"{'='*60}\n")
                f.write(f"📊 Total repositories scanned: {len(self.df):,}\n")
                f.write(f"✅ Repositories with political emojis: {len(self.filtered_df):,}\n")
                f.write(f"❌ Repositories filtered out: {len(self.df) - len(self.filtered_df):,}\n")
                f.write(f"📈 Retention rate: {(len(self.filtered_df) / len(self.df) * 100):.2f}%\n")
                
                # Emoji statistics
                if emoji_stats:
                    f.write(f"\n{'='*60}\n")
                    f.write(f"EMOJI STATISTICS\n")
                    f.write(f"{'='*60}\n")
                    sorted_stats = sorted(emoji_stats.items(), key=lambda x: x[1], reverse=True)
                    for emoji, count in sorted_stats:
                        f.write(f"{emoji}  : {count:3d} repositories\n")
                
                # Summary statistics
                if self.filtered_df is not None and len(self.filtered_df) > 0:
                    f.write(f"{'='*60}\n")
                    f.write(f"SUMMARY STATISTICS\n")
                    f.write(f"{'='*60}\n")
                    
                    # Star statistics
                    if 'repo_stars' in self.filtered_df.columns:
                        total_stars = self.filtered_df['repo_stars'].sum()
                        avg_stars = self.filtered_df['repo_stars'].mean()
                        max_stars = self.filtered_df['repo_stars'].max()
                        min_stars = self.filtered_df['repo_stars'].min()
                        
                        f.write(f"\n⭐ Stars:\n")
                        f.write(f"   Total: {total_stars:,}\n")
                        f.write(f"   Average: {avg_stars:,.0f}\n")
                        f.write(f"   Max: {max_stars:,}\n")
                        f.write(f"   Min: {min_stars:,}\n")
                    
                    # Contributors statistics
                    contrib_col = 'contributors' if 'contributors' in self.filtered_df.columns else 'collaborators'
                    if contrib_col in self.filtered_df.columns:
                        total_contrib = self.filtered_df[contrib_col].sum()
                        avg_contrib = self.filtered_df[contrib_col].mean()
                        
                        f.write(f"\n👥 Contributors:\n")
                        f.write(f"   Total: {total_contrib:,}\n")
                        f.write(f"   Average: {avg_contrib:.1f}\n")
                    
                    # README statistics
                    if 'readme' in self.filtered_df.columns:
                        repos_with_readme = self.filtered_df['readme'].notna().sum()
                        readme_lengths = self.filtered_df[self.filtered_df['readme'].notna()]['readme'].str.len()
                        if len(readme_lengths) > 0:
                            avg_readme_length = readme_lengths.mean()
                            
                            f.write(f"\n📝 README:\n")
                            f.write(f"   Repositories with README: {repos_with_readme}/{len(self.filtered_df)}\n")
                            f.write(f"   Average README length: {avg_readme_length:,.0f} characters\n")
                    
                    # Description statistics
                    if 'description' in self.filtered_df.columns:
                        repos_with_desc = self.filtered_df['description'].notna().sum()
                        repos_with_desc = repos_with_desc - (self.filtered_df['description'] == '').sum()
                        
                        f.write(f"\n📄 Description:\n")
                        f.write(f"   Repositories with description: {repos_with_desc}/{len(self.filtered_df)}\n")
                    
                    # Topics statistics
                    if 'topics' in self.filtered_df.columns:
                        repos_with_topics = self.filtered_df['topics'].notna().sum()
                        repos_with_topics = repos_with_topics - (self.filtered_df['topics'] == '').sum()
                        
                        f.write(f"\n🏷️  Topics:\n")
                        f.write(f"   Repositories with topics: {repos_with_topics}/{len(self.filtered_df)}\n")
                    
                    # Found emojis statistics
                    if 'found_emojis' in self.filtered_df.columns:
                        avg_emojis = self.filtered_df['found_emojis'].str.split().str.len().mean()
                        max_emojis = self.filtered_df['found_emojis'].str.split().str.len().max()
                        
                        f.write(f"\n😀 Found Emojis:\n")
                        f.write(f"   Average emojis per repo: {avg_emojis:.1f}\n")
                        f.write(f"   Max emojis in a repo: {int(max_emojis)}\n")
                    
                    # Affiliation statistics (for refilter mode)
                    if self.refilter and ('affiliation' in self.filtered_df.columns or 
                                          'affiliation_openai' in self.filtered_df.columns or 
                                          'affiliation_deepseek' in self.filtered_df.columns):
                        # Check which affiliation column exists
                        affiliation_col = None
                        if 'affiliation_openai' in self.filtered_df.columns:
                            affiliation_col = 'affiliation_openai'
                        elif 'affiliation_deepseek' in self.filtered_df.columns:
                            affiliation_col = 'affiliation_deepseek'
                        elif 'affiliation' in self.filtered_df.columns:
                            affiliation_col = 'affiliation'
                        
                        if affiliation_col:
                            affiliation_counts = self.filtered_df[affiliation_col].value_counts()
                            
                            f.write(f"\n🏢 Affiliation Distribution ({affiliation_col}):\n")
                            for affiliation, count in affiliation_counts.items():
                                percentage = (count / len(self.filtered_df)) * 100
                                f.write(f"   {affiliation}: {count} ({percentage:.1f}%)\n")
                
                f.write(f"\n{'='*60}\n")
                f.write(f"💾 Output saved to: {self.output_csv}\n")
                f.write(f"✅ Successfully saved {len(self.filtered_df):,} repositories\n")
                f.write(f"{'='*60}\n\n")
            
            print(f"📋 Report appended to: {log_file}")
            
        except Exception as e:
            print(f"⚠️  Warning: Could not save report to log file: {e}")
    
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
        
        # Affiliation statistics (for refilter mode)
        if self.refilter and ('affiliation' in self.filtered_df.columns or 
                              'affiliation_openai' in self.filtered_df.columns or 
                              'affiliation_deepseek' in self.filtered_df.columns):
            # Check which affiliation column exists
            affiliation_col = None
            if 'affiliation_openai' in self.filtered_df.columns:
                affiliation_col = 'affiliation_openai'
            elif 'affiliation_deepseek' in self.filtered_df.columns:
                affiliation_col = 'affiliation_deepseek'
            elif 'affiliation' in self.filtered_df.columns:
                affiliation_col = 'affiliation'
            
            if affiliation_col:
                affiliation_counts = self.filtered_df[affiliation_col].value_counts()
                
                print(f"\n🏢 Affiliation Distribution ({affiliation_col}):")
                for affiliation, count in affiliation_counts.items():
                    percentage = (count / len(self.filtered_df)) * 100
                    print(f"   {affiliation}: {count} ({percentage:.1f}%)")
        
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
        
        # Filter repositories and capture emoji stats
        emoji_stats = {}
        filtered_rows = []
        
        # Inline filtering to capture emoji_stats
        for idx, row in self.df.iterrows():
            repo_owner = row.get('repo_owner', '')
            repo_name = row.get('repo_name', '')
            repo_stars = row.get('repo_stars', 0)
            readme = row.get('readme', '')
            description = row.get('description', '')
            
            repo_contributors = row.get('contributors', row.get('collaborators', 0))
            
            # Star filtering
            if repo_stars < self.min_stars:
                continue
            if self.max_stars is not None and repo_stars > self.max_stars:
                continue
            
            # Contributor filtering
            if repo_contributors < self.min_contributors:
                continue
            if self.max_contributors is not None and repo_contributors > self.max_contributors:
                continue
            
            # Fork filtering
            if not self.include_fork:
                is_fork = row.get('is_a_fork', False)
                # Skip if it's a fork and we're excluding forks
                if is_fork:
                    continue
            
            if self.refilter:
                existing_emojis = row.get('found_emojis', '')
                if pd.notna(existing_emojis) and existing_emojis:
                    all_found_emojis = existing_emojis.split()
                    for emoji in all_found_emojis:
                        emoji_stats[emoji] = emoji_stats.get(emoji, 0) + 1
                    filtered_rows.append(row.copy())
            else:
                readme_has_emoji, readme_emojis = self.contains_emoji(readme)
                desc_has_emoji, desc_emojis = self.contains_emoji(description)
                all_found_emojis = list(set(readme_emojis + desc_emojis))
                
                if readme_has_emoji or desc_has_emoji:
                    for emoji in all_found_emojis:
                        emoji_stats[emoji] = emoji_stats.get(emoji, 0) + 1
                    row_with_emojis = row.copy()
                    row_with_emojis['found_emojis'] = ' '.join(all_found_emojis)
                    filtered_rows.append(row_with_emojis)
        
        self.filtered_df = pd.DataFrame(filtered_rows)
        
        # Display results
        self._display_filter_results(emoji_stats)
        
        # Show summary
        self.show_summary()
        
        # Save filtered CSV
        if not self.save_filtered_csv():
            return False
        
        # Save report to log file
        self.save_report_to_log(emoji_stats)
        
        print("✅ Filtering completed successfully!\n")
        return True
    
    def _display_filter_results(self, emoji_stats):
        """
        Display filtering results and emoji statistics
        
        Args:
            emoji_stats: Dictionary of emoji counts
        """
        print(f"\n{'='*60}")
        print(f"FILTERING RESULTS")
        print(f"{'='*60}")
        print(f"📊 Total repositories scanned: {len(self.df):,}")
        print(f"✅ Repositories with political emojis: {len(self.filtered_df):,}")
        print(f"❌ Repositories filtered out: {len(self.df) - len(self.filtered_df):,}")
        print(f"📈 Retention rate: {(len(self.filtered_df) / len(self.df) * 100):.2f}%")
        
        if emoji_stats:
            print(f"\n{'='*60}")
            print(f"EMOJI STATISTICS")
            print(f"{'='*60}")
            sorted_stats = sorted(emoji_stats.items(), key=lambda x: x[1], reverse=True)
            for emoji, count in sorted_stats:
                print(f"{emoji}  : {count:3d} repositories")


def main():
    """
    Main function to run the CSV filter
    """
    print(f"\n{'='*60}")
    if REFILTER:
        print("GITHUB REPOSITORY RE-FILTER (Affiliation Data)")
    else:
        print("GITHUB REPOSITORY EMOJI FILTER")
    print(f"{'='*60}")
    print(f"\nConfiguration:")
    print(f"  Mode: {'RE-FILTER (using existing emojis)' if REFILTER else 'FILTER (detect emojis)'}")
    print(f"  Input CSV: {INPUT_CSV}")
    print(f"  Output CSV: {OUTPUT_CSV if OUTPUT_CSV else 'Auto-generated with timestamp'}")
    print(f"  Star range: {MIN_STARS:,} to {MAX_STARS:,}" if MAX_STARS else f"  Minimum stars: {MIN_STARS:,}")
    if MIN_CONTRIBUTORS > 0 or MAX_CONTRIBUTORS is not None:
        print(f"  Contributor range: {MIN_CONTRIBUTORS:,} to {MAX_CONTRIBUTORS:,}" if MAX_CONTRIBUTORS else f"  Minimum contributors: {MIN_CONTRIBUTORS:,}")
    print(f"  Include forks: {'Yes' if INCLUDE_FORK else 'No (original repos only)'}")
    if not REFILTER:
        print(f"  Number of emojis to search: {len(POLITICAL_EMOJIS)}")
    
    # Create filter instance
    csv_filter = CSVFilter(INPUT_CSV, OUTPUT_CSV, POLITICAL_EMOJIS, MIN_STARS, MAX_STARS, MIN_CONTRIBUTORS, MAX_CONTRIBUTORS, INCLUDE_FORK, REFILTER)
    
    # Run filtering
    success = csv_filter.run()
    
    if success:
        print(f"✅ Filtered data saved to: {csv_filter.output_csv}")
    else:
        print("❌ Filtering failed!")


if __name__ == "__main__":
    main()
