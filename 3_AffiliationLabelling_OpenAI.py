import pandas as pd
import requests
import time
from datetime import datetime
import os
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# Load environment variables from .env file
load_dotenv()

# ============================
# CONFIGURATION - Edit these variables
# ============================
INPUT_CSV = r"datasets/affiliated_deepseek_1000_200000.csv"  # Input CSV file to process (output from filtering.py)
OUTPUT_CSV = r"datasets/affiliated_combined_1000_200000.csv"  # Output CSV file with affiliation
OPENAI_API_KEY = os.getenv('openai_api_key')  # OpenAI API key from .env
MODEL_ID = "gpt-4.1-nano"  # OpenAI model (gpt-4o-mini is cost-effective, or use gpt-4o for best quality)
MAX_RETRIES = 3  # Maximum number of retries for failed requests
MAX_WORKERS = 12  # Number of parallel workers for multithreading
USE_CACHE = True  # Use cached annotations from previous runs (set to False to force re-annotation)
CACHE_DIR = "cache"  # Directory to store annotation cache files
# ============================

class AffiliationExtractorOpenAI:
    # Cached system prompt - defined once at class level to enable prompt caching
    SYSTEM_PROMPT = """You are a classification AI. Respond with EXACTLY ONE WORD based on the repository's README or description.

Categories
israel – Israel, Israeli support, Stand with Israel, 🇮🇱, ✡️, 🎗️

palestine – Palestine, Gaza, Free Palestine, pro-Palestine, 🇵🇸, 🍉

blm – Black Lives Matter, racial justice, anti-racism, ✊🏾, ✊🏿

ukraine – Ukraine, Stand with Ukraine, pro-Ukraine, 🇺🇦, 🌻

climate – Climate change, sustainability, climate action, ♻️, 🌱, 🌍

feminism – Women's rights, gender equality, feminism, ♀️, 👩

lgbtq – LGBTQ, pride, queer, transgender rights, 🏳️‍🌈, 🏳️‍⚧️

democrat – US Democrats, Biden, blue wave, Democratic Party, 🐴

republican – US Republicans, GOP, Trump, conservative, red wave, 🐘

none – No clear affiliation

Rules

Reply with only one word:
israel, palestine, blm, ukraine, climate, feminism, lgbtq, democrat, republican, none

Use lowercase only.

No punctuation, no emoji, no explanation.

Only classify when there is clear evidence.

If unclear, neutral, or unrelated → none.

If multiple appear, choose the most dominant affiliation."""
    
    def __init__(self, api_key, model_id):
        """
        Initialize the Affiliation Extractor with OpenAI
        
        Args:
            api_key: OpenAI API key
            model_id: OpenAI model ID
        """
        self.api_key = api_key
        self.model_id = model_id
        self.base_url = "https://api.openai.com/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.print_lock = Lock()  # Thread-safe printing
        self.cache = {}  # Cache for storing annotations {repo_url: affiliation}
        self.cache_file = None  # Current cache file path
        self.cache_hits = 0  # Track cache hits
        self.cache_misses = 0  # Track cache misses
    
    def load_cache(self, use_cache=True):
        """
        Load the latest cache file or create a new one
        
        Args:
            use_cache: Whether to use existing cache (True) or create new cache (False)
        """
        import json
        import glob
        
        # Create cache directory if it doesn't exist
        os.makedirs(CACHE_DIR, exist_ok=True)
        
        if use_cache:
            # Find all cache files for OpenAI
            cache_pattern = os.path.join(CACHE_DIR, "affiliation_cache_openai_*.json")
            cache_files = glob.glob(cache_pattern)
            
            if cache_files:
                # Get the latest cache file by timestamp
                latest_cache = max(cache_files, key=os.path.getmtime)
                self.cache_file = latest_cache
                
                try:
                    with open(latest_cache, 'r', encoding='utf-8') as f:
                        self.cache = json.load(f)
                    print(f"✅ Loaded cache from: {os.path.basename(latest_cache)}")
                    print(f"   Cache entries: {len(self.cache):,}")
                    return
                except Exception as e:
                    print(f"⚠️  Could not load cache: {e}")
                    print(f"   Creating new cache...")
        
        # Create new cache file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.cache_file = os.path.join(CACHE_DIR, f"affiliation_cache_openai_{timestamp}.json")
        self.cache = {}
        print(f"📝 Created new cache: {os.path.basename(self.cache_file)}")
    
    def save_cache(self):
        """
        Save the current cache to file
        """
        import json
        
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  Warning: Could not save cache: {e}")
    
    def get_cached_affiliation(self, repo_url):
        """
        Get cached affiliation for a repository
        
        Args:
            repo_url: Repository URL
            
        Returns:
            Cached affiliation or None if not found
        """
        if repo_url in self.cache:
            self.cache_hits += 1
            return self.cache[repo_url]
        self.cache_misses += 1
        return None
    
    def set_cached_affiliation(self, repo_url, affiliation):
        """
        Store affiliation in cache
        
        Args:
            repo_url: Repository URL
            affiliation: Affiliation classification
        """
        self.cache[repo_url] = affiliation
        
        # Auto-save cache every 10 new entries
        if self.cache_misses % 10 == 0:
            self.save_cache()
    
    def classify_affiliation(self, readme_text, max_retries=3):
        """
        Classify the affiliation of a repository based on its README using OpenAI
        
        Args:
            readme_text: README content
            max_retries: Maximum number of retries
            
        Returns:
            Affiliation string: 'israel', 'palestine', 'blm', 'ukraine', 'climate', 'feminism', 'lgbtq', 'democrat', 'republican', or 'none'
        """
        if not readme_text or pd.isna(readme_text) or readme_text.strip() == "":
            return "none"
        
        # Truncate README if too long (to avoid token limits)
        max_chars = 3000
        if len(readme_text) > max_chars:
            readme_text = readme_text[:max_chars]
        
        user_prompt = f"README content:\n\n{readme_text}\n\nClassification:"
        
        # Use OpenAI API format
        payload = {
            "model": self.model_id,
            "messages": [
                {
                    "role": "system",
                    "content": self.SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            "temperature": 0.0,
            "max_tokens": 10,
            "stream": False
        }
        
        # Retry logic
        for attempt in range(max_retries):
            try:
                response = requests.post(self.base_url, json=payload, headers=self.headers, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Extract the response text from OpenAI format
                    if isinstance(result, dict) and 'choices' in result:
                        affiliation = result['choices'][0]['message']['content']
                    else:
                        affiliation = str(result)
                    
                    # Clean and normalize the response
                    affiliation = affiliation.lower().strip().replace('.', '').replace('!', '')
                    
                    # Extract valid affiliation
                    valid_affiliations = ['israel', 'palestine', 'blm', 'ukraine', 'climate', 'feminism', 'lgbtq', 'democrat', 'republican', 'none']
                    for valid in valid_affiliations:
                        if valid in affiliation:
                            return valid
                    
                    # If no valid affiliation found, return 'none'
                    return 'none'
                
                else:
                    print(f"      ⚠️  API error (status {response.status_code}), attempt {attempt + 1}/{max_retries}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                    
            except requests.exceptions.Timeout:
                print(f"      ⏱️  Timeout, attempt {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    
            except Exception as e:
                print(f"      ❌ Exception: {e}, attempt {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
        
        # If all retries failed, return 'none'
        print(f"      ❌ All retries failed, defaulting to 'none'")
        return 'none'
    
    def process_single_repository(self, idx, row, total):
        """
        Process a single repository (thread-safe)
        
        Args:
            idx: Repository index
            row: DataFrame row
            total: Total number of repositories
            
        Returns:
            Tuple of (idx, affiliation)
        """
        repo_owner = row.get('repo_owner', 'unknown')
        repo_name = row.get('repo_name', 'unknown')
        repo_url = row.get('repo_url', '')
        readme = row.get('readme', '')
        description = row.get('description', '')
        found_emojis = row.get('found_emojis', '')
        
        # Check cache first
        cached_affiliation = self.get_cached_affiliation(repo_url)
        if cached_affiliation is not None:
            with self.print_lock:
                print(f"[{idx + 1}/{total}] 💾 {repo_owner}/{repo_name} (cached)")
                print(f"   ✅ Affiliation: {cached_affiliation.upper()}")
            return idx, cached_affiliation
        
        # Combine description, found emojis, and readme for better classification
        combined_text = f"Description: {description}\n"
        if found_emojis:
            combined_text += f"Found Emojis: {found_emojis}\n"
        combined_text += f"\nREADME:\n{readme}" if readme else ""
        
        with self.print_lock:
            print(f"[{idx + 1}/{total}] Processing {repo_owner}/{repo_name}...")
            if found_emojis:
                print(f"   Found emojis: {found_emojis}")
        
        affiliation = self.classify_affiliation(combined_text, max_retries=MAX_RETRIES)
        
        # Store in cache
        self.set_cached_affiliation(repo_url, affiliation)
        
        with self.print_lock:
            print(f"   ✅ Affiliation: {affiliation.upper()}")
        
        # Rate limiting to avoid overwhelming the API
        time.sleep(0.1)
        
        return idx, affiliation
    
    def process_csv(self, input_file, output_file):
        """
        Process the CSV file and add affiliation column
        
        Args:
            input_file: Input CSV filename
            output_file: Output CSV filename
            
        Returns:
            Success status
        """
        print("\n" + "=" * 60)
        print("AFFILIATION EXTRACTOR (OpenAI) - Analyzing GitHub Repositories")
        print("=" * 60 + "\n")
        
        # Load CSV file
        if not os.path.exists(input_file):
            print(f"❌ File not found: {input_file}")
            return False
        
        try:
            print(f"📂 Loading CSV file (this may take a moment for large files)...")
            # Try fast C engine first, fall back to Python engine if needed
            try:
                df = pd.read_csv(input_file, encoding='utf-8', low_memory=False)
            except Exception:
                print("   ⚠️  Standard loading failed, trying robust mode...")
                df = pd.read_csv(input_file, encoding='utf-8', engine='python', on_bad_lines='skip')
            
            print(f"✅ Loaded {input_file}")
            print(f"   Rows: {len(df):,} | Columns: {len(df.columns)}")
            print(f"   Columns: {', '.join(df.columns)}\n")
        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            return False
        
        # Check if 'readme' column exists
        if 'readme' not in df.columns:
            print("❌ 'readme' column not found in CSV")
            return False
        
        # Load cache
        self.load_cache(use_cache=USE_CACHE)
        
        # Add affiliation column with multithreading
        print("\n🔍 Analyzing affiliations using OpenAI LLM...")
        print(f"   Model: {self.model_id}")
        print(f"   Annotation Cache: {'ENABLED' if USE_CACHE else 'DISABLED'}")
        print(f"   Workers: {MAX_WORKERS} parallel threads")
        print(f"   Total repositories to process: {len(df):,}\n")
        
        # Initialize affiliations list with None
        affiliations = [None] * len(df)
        
        # Process repositories in parallel
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Submit all tasks
            future_to_idx = {
                executor.submit(self.process_single_repository, idx, row, len(df)): idx
                for idx, row in df.iterrows()
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_idx):
                try:
                    idx, affiliation = future.result()
                    affiliations[idx] = affiliation
                except Exception as e:
                    idx = future_to_idx[future]
                    print(f"\n❌ Error processing repository at index {idx}: {e}")
                    affiliations[idx] = 'none'
        
        # Add affiliation column to dataframe
        df['affiliation_openai'] = affiliations
        
        # Save final cache
        self.save_cache()
        
        # Display cache statistics
        print(f"\n📊 Cache Statistics:")
        print(f"   Cache hits: {self.cache_hits:,} ({(self.cache_hits/(self.cache_hits+self.cache_misses)*100) if (self.cache_hits+self.cache_misses) > 0 else 0:.1f}%)")
        print(f"   Cache misses (new annotations): {self.cache_misses:,}")
        print(f"   Total cache entries: {len(self.cache):,}")
        print(f"   Cache file: {os.path.basename(self.cache_file)}")
        
        # Save to CSV
        print(f"\n💾 Saving results to {output_file}...")
        try:
            df.to_csv(output_file, index=False, encoding='utf-8')
            print(f"✅ Successfully saved!")
            
            # Statistics
            print("\n" + "=" * 60)
            print("📊 AFFILIATION STATISTICS (OpenAI)")
            print("=" * 60)
            
            affiliation_counts = df['affiliation_openai'].value_counts()
            for affiliation, count in affiliation_counts.items():
                percentage = (count / len(df)) * 100
                print(f"{affiliation.upper():15s}: {count:4d} ({percentage:5.1f}%)")
            
            print(f"\nTotal: {len(df):,} repositories")
            print(f"Output file: {output_file}")
            print("=" * 60)
            
            # Save detailed report to log file
            self.save_extraction_report(df, output_file)
            
            return True
            
        except Exception as e:
            print(f"❌ Error saving file: {e}")
            return False
    
    def save_extraction_report(self, df, output_file):
        """
        Save detailed extraction report to logs/extraction_report_openai.txt
        
        Args:
            df: DataFrame with affiliation_openai column
            output_file: Output CSV filename
        """
        import os
        
        try:
            # Create logs directory if it doesn't exist
            os.makedirs('logs', exist_ok=True)
            
            log_file = 'logs/extraction_report_openai.txt'
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*70}\n")
                f.write(f"AFFILIATION EXTRACTION REPORT (OpenAI) - {timestamp}\n")
                f.write(f"{'='*70}\n")
                f.write(f"Model: {self.model_id}\n")
                f.write(f"Output: {output_file}\n")
                f.write(f"Total repositories processed: {len(df):,}\n")
                
                # Overall affiliation statistics
                f.write(f"\n{'='*70}\n")
                f.write(f"AFFILIATION STATISTICS\n")
                f.write(f"{'='*70}\n")
                
                affiliation_counts = df['affiliation_openai'].value_counts()
                for affiliation, count in affiliation_counts.items():
                    percentage = (count / len(df)) * 100
                    f.write(f"{affiliation.upper():15s}: {count:4d} ({percentage:5.1f}%)\n")
                
                # Emoji-Affiliation correlation analysis
                if 'found_emojis' in df.columns:
                    f.write(f"\n{'='*70}\n")
                    f.write(f"EMOJI-AFFILIATION CORRELATION ANALYSIS\n")
                    f.write(f"{'='*70}\n")
                    
                    # Parse emojis and build correlation map
                    emoji_affiliation_map = {}
                    
                    for idx, row in df.iterrows():
                        emojis_str = row.get('found_emojis', '')
                        affiliation = row.get('affiliation_openai', 'none')
                        
                        if pd.notna(emojis_str) and emojis_str:
                            emojis = emojis_str.split()
                            for emoji in emojis:
                                if emoji not in emoji_affiliation_map:
                                    emoji_affiliation_map[emoji] = {}
                                
                                if affiliation not in emoji_affiliation_map[emoji]:
                                    emoji_affiliation_map[emoji][affiliation] = 0
                                
                                emoji_affiliation_map[emoji][affiliation] += 1
                    
                    # Sort emojis by total count (descending)
                    emoji_totals = {emoji: sum(affiliations.values()) 
                                   for emoji, affiliations in emoji_affiliation_map.items()}
                    sorted_emojis = sorted(emoji_totals.items(), key=lambda x: x[1], reverse=True)
                    
                    # Write emoji-affiliation correlation
                    for emoji, total_count in sorted_emojis:
                        f.write(f"\nEmoji: {emoji}\n")
                        f.write(f"Affiliations:\n")
                        
                        affiliations = emoji_affiliation_map[emoji]
                        # Sort affiliations by count (descending)
                        sorted_affiliations = sorted(affiliations.items(), key=lambda x: x[1], reverse=True)
                        
                        for affiliation, count in sorted_affiliations:
                            percentage = (count / total_count) * 100
                            f.write(f"  - {affiliation.capitalize():15s}: {count:4d} ({percentage:5.1f}%)\n")
                        
                        f.write(f"Total: {total_count}\n")
                    
                    f.write(f"\n{'='*70}\n")
                    f.write(f"Total unique emojis analyzed: {len(emoji_affiliation_map)}\n")
                
                f.write(f"{'='*70}\n\n")
            
            print(f"📋 Detailed report saved to: {log_file}")
            
        except Exception as e:
            print(f"⚠️  Warning: Could not save extraction report: {e}")


def main():
    """
    Main function to extract affiliations using OpenAI
    """
    print("\n" + "=" * 60)
    print("GITHUB REPOSITORY AFFILIATION EXTRACTOR (OpenAI)")
    print("=" * 60)
    print(f"\nInput file: {INPUT_CSV}")
    print(f"Output file: {OUTPUT_CSV}")
    print(f"Model: {MODEL_ID}")
    
    # Check if API key is available
    if not OPENAI_API_KEY:
        print("\n❌ Error: OpenAI API key not found in .env file")
        print("   Please ensure 'openai_api_key' is set in .env")
        return
    
    print(f"API Key: {OPENAI_API_KEY[:10]}...{OPENAI_API_KEY[-4:]}")
    
    # Create extractor instance
    extractor = AffiliationExtractorOpenAI(OPENAI_API_KEY, MODEL_ID)
    
    # Process the CSV
    success = extractor.process_csv(INPUT_CSV, OUTPUT_CSV)
    
    if success:
        print("\n✅ Affiliation extraction completed successfully!")
    else:
        print("\n❌ Affiliation extraction failed!")


if __name__ == "__main__":
    main()
