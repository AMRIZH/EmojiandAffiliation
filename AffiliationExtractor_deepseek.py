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
INPUT_CSV = "Cleaned_github_readmes_500stars.csv"  # Input CSV file to process (output from filtering.py)
OUTPUT_CSV = "github_affiliation_deepseek.csv"  # Output CSV file with affiliation
DEEPSEEK_API_KEY = os.getenv('deepseek_api_key')  # DeepSeek API key from .env
MODEL_ID = "deepseek-chat"  # DeepSeek model ID
MAX_RETRIES = 3  # Maximum number of retries for failed requests
MAX_WORKERS = 12  # Number of parallel workers for multithreading
# ============================

class AffiliationExtractor:
    # Cached system prompt - defined once at class level to enable prompt caching
    SYSTEM_PROMPT = """You are a classification AI. Your ONLY task is to respond with EXACTLY ONE WORD.

Analyze the README and description content to classify the repository's affiliation/activism:

- israel (if mentions: Israel, Israeli support, Israeli tech, pro-Israel, Stand with Israel)
- palestine (if mentions: Palestine, Gaza, Palestinian support, Free Palestine, pro-Palestine)
- blm (if mentions: Black Lives Matter, BLM, racial justice, anti-racism)
- ukraine (if mentions: Ukraine, Ukrainian support, Stand with Ukraine, pro-Ukraine)
- climate (if mentions: Climate change, environmental activism, sustainability, climate action)
- feminism (if mentions: Women's rights, feminism, gender equality, women empowerment)
- lgbtq (if mentions: LGBTQ, LGBT, gay rights, pride, queer, transgender)
- none (if no clear political/social activism affiliation found or neutral content)

RULES:
1. Respond with EXACTLY ONE WORD: israel, palestine, blm, ukraine, climate, feminism, lgbtq, or none
2. Use lowercase only
3. No punctuation, no explanation, no additional text
4. Only classify if there is CLEAR evidence in the README or description
5. If unclear or neutral, respond: none
6. Choose the MOST DOMINANT affiliation if multiple are present"""
    
    def __init__(self, api_key, model_id):
        """
        Initialize the Affiliation Extractor
        
        Args:
            api_key: DeepSeek API key
            model_id: DeepSeek model ID
        """
        self.api_key = api_key
        self.model_id = model_id
        self.base_url = "https://api.deepseek.com/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.print_lock = Lock()  # Thread-safe printing
    
    def classify_affiliation(self, readme_text, max_retries=3):
        """
        Classify the affiliation of a repository based on its README
        
        Args:
            readme_text: README content
            max_retries: Maximum number of retries
            
        Returns:
            Affiliation string: 'palestine', 'israel', 'russia', 'ukraine', or 'none'
        """
        if not readme_text or pd.isna(readme_text) or readme_text.strip() == "":
            return "none"
        
        # Truncate README if too long (to avoid token limits)
        max_chars = 3000
        if len(readme_text) > max_chars:
            readme_text = readme_text[:max_chars]
        
        user_prompt = f"README content:\n\n{readme_text}\n\nClassification:"
        
        # Use DeepSeek API format with cached system prompt
        payload = {
            "model": self.model_id,
            "messages": [
                {
                    "role": "system",
                    "content": self.SYSTEM_PROMPT  # Use cached prompt
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
                    
                    # Extract the response text from DeepSeek format
                    if isinstance(result, dict) and 'choices' in result:
                        affiliation = result['choices'][0]['message']['content']
                    else:
                        affiliation = str(result)
                    
                    # Clean and normalize the response
                    affiliation = affiliation.lower().strip().replace('.', '').replace('!', '')
                    
                    # Extract valid affiliation
                    valid_affiliations = ['israel', 'palestine', 'blm', 'ukraine', 'climate', 'feminism', 'lgbtq', 'none']
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
        readme = row.get('readme', '')
        description = row.get('description', '')
        found_emojis = row.get('found_emojis', '')
        
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
        print("AFFILIATION EXTRACTOR - Analyzing GitHub Repositories")
        print("=" * 60 + "\n")
        
        # Load CSV file
        if not os.path.exists(input_file):
            print(f"❌ File not found: {input_file}")
            return False
        
        try:
            df = pd.read_csv(input_file)
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
        
        # Add affiliation column with multithreading
        print("🔍 Analyzing affiliations using DeepSeek LLM...")
        print(f"   Model: {self.model_id}")
        print(f"   Prompt Caching: ENABLED (reduces costs)")
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
        df['affiliation_deepseek'] = affiliations
        
        # Save to CSV
        print(f"\n💾 Saving results to {output_file}...")
        try:
            df.to_csv(output_file, index=False, encoding='utf-8')
            print(f"✅ Successfully saved!")
            
            # Statistics
            print("\n" + "=" * 60)
            print("📊 AFFILIATION STATISTICS (DeepSeek)")
            print("=" * 60)
            
            affiliation_counts = df['affiliation_deepseek'].value_counts()
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
        Save detailed extraction report to logs/extraction_report_deepseek.txt
        
        Args:
            df: DataFrame with affiliation_deepseek column
            output_file: Output CSV filename
        """
        import os
        
        try:
            # Create logs directory if it doesn't exist
            os.makedirs('logs', exist_ok=True)
            
            log_file = 'logs/extraction_report_deepseek.txt'
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*70}\n")
                f.write(f"AFFILIATION EXTRACTION REPORT (DeepSeek) - {timestamp}\n")
                f.write(f"{'='*70}\n")
                f.write(f"Model: {self.model_id}\n")
                f.write(f"Output: {output_file}\n")
                f.write(f"Total repositories processed: {len(df):,}\n")
                
                # Overall affiliation statistics
                f.write(f"\n{'='*70}\n")
                f.write(f"AFFILIATION STATISTICS\n")
                f.write(f"{'='*70}\n")
                
                affiliation_counts = df['affiliation_deepseek'].value_counts()
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
                        affiliation = row.get('affiliation_deepseek', 'none')
                        
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
    Main function to extract affiliations
    """
    print("\n" + "=" * 60)
    print("GITHUB REPOSITORY AFFILIATION EXTRACTOR")
    print("=" * 60)
    print(f"\nInput file: {INPUT_CSV}")
    print(f"Output file: {OUTPUT_CSV}")
    print(f"Model: {MODEL_ID}")
    
    # Check if API key is available
    if not DEEPSEEK_API_KEY:
        print("\n❌ Error: DeepSeek API key not found in .env file")
        print("   Please ensure 'deepseek_api_key' is set in .env")
        return
    
    print(f"API Key: {DEEPSEEK_API_KEY[:10]}...{DEEPSEEK_API_KEY[-4:]}")
    
    # Create extractor instance
    extractor = AffiliationExtractor(DEEPSEEK_API_KEY, MODEL_ID)
    
    # Process the CSV
    success = extractor.process_csv(INPUT_CSV, OUTPUT_CSV)
    
    if success:
        print("\n✅ Affiliation extraction completed successfully!")
    else:
        print("\n❌ Affiliation extraction failed!")


if __name__ == "__main__":
    main()
