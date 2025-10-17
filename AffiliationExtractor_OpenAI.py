import pandas as pd
import requests
import time
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================
# CONFIGURATION - Edit these variables
# ============================
INPUT_CSV = "Cleaned_github_readmes.csv"  # Input CSV file to process (output from filtering.py)
OUTPUT_CSV = "github_affiliation_openai.csv"  # Output CSV file with affiliation
OPENAI_API_KEY = os.getenv('openai_api_key')  # OpenAI API key from .env
MODEL_ID = "gpt-4o-mini"  # OpenAI model (gpt-4o-mini is the latest mini model)
MAX_RETRIES = 3  # Maximum number of retries for failed requests
# ============================

class AffiliationExtractorOpenAI:
    # Cached system prompt - defined once at class level to enable prompt caching
    SYSTEM_PROMPT = """You are a classification AI. Your ONLY task is to respond with EXACTLY ONE WORD.

Analyze the README and description content to classify the repository's affiliation/activism:

- israel (if mentions: Israel, Israeli support, Israeli tech, pro-Israel, Stand with Israel, 🇮🇱, ✡️, 🎗️)
- palestine (if mentions: Palestine, Gaza, Palestinian support, Free Palestine, pro-Palestine, 🇵🇸, 🍉)
- blm (if mentions: Black Lives Matter, BLM, racial justice, anti-racism, ✊🏾, ✊🏿)
- ukraine (if mentions: Ukraine, Ukrainian support, Stand with Ukraine, pro-Ukraine, 🇺🇦, 🌻)
- climate (if mentions: Climate change, environmental activism, sustainability, climate action, ♻️, 🌱, 🌍)
- feminism (if mentions: Women's rights, feminism, gender equality, women empowerment, ♀️, 👩)
- lgbtq (if mentions: LGBTQ, LGBT, gay rights, pride, queer, transgender, 🏳️‍🌈, 🏳️‍⚧️)
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
    
    def classify_affiliation(self, readme_text, max_retries=3):
        """
        Classify the affiliation of a repository based on its README using OpenAI
        
        Args:
            readme_text: README content
            max_retries: Maximum number of retries
            
        Returns:
            Affiliation string: 'israel', 'palestine', 'blm', 'ukraine', 'climate', 'feminism', 'lgbtq', or 'none'
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
        
        # Add affiliation column
        print("🔍 Analyzing affiliations using OpenAI LLM...")
        print(f"   Model: {self.model_id}")
        print(f"   Total repositories to process: {len(df):,}\n")
        
        affiliations = []
        
        for idx, row in df.iterrows():
            repo_owner = row.get('repo_owner', 'unknown')
            repo_name = row.get('repo_name', 'unknown')
            readme = row.get('readme', '')
            description = row.get('description', '')
            found_emojis = row.get('found_emojis', '')  # New column from filtering.py
            
            # Combine description, found emojis, and readme for better classification
            combined_text = f"Description: {description}\n"
            if found_emojis:
                combined_text += f"Found Emojis: {found_emojis}\n"
            combined_text += f"\nREADME:\n{readme}" if readme else ""
            
            print(f"[{idx + 1}/{len(df)}] Processing {repo_owner}/{repo_name}...")
            if found_emojis:
                print(f"   Found emojis: {found_emojis}")
            
            affiliation = self.classify_affiliation(combined_text, max_retries=MAX_RETRIES)
            affiliations.append(affiliation)
            
            print(f"   ✅ Affiliation: {affiliation.upper()}")
            
            # Rate limiting to avoid overwhelming the API
            time.sleep(0.5)
        
        # Add affiliation column to dataframe
        df['affiliation'] = affiliations
        
        # Save to CSV
        print(f"\n💾 Saving results to {output_file}...")
        try:
            df.to_csv(output_file, index=False, encoding='utf-8')
            print(f"✅ Successfully saved!")
            
            # Statistics
            print("\n" + "=" * 60)
            print("📊 AFFILIATION STATISTICS")
            print("=" * 60)
            
            affiliation_counts = df['affiliation'].value_counts()
            for affiliation, count in affiliation_counts.items():
                percentage = (count / len(df)) * 100
                print(f"{affiliation.upper():15s}: {count:4d} ({percentage:5.1f}%)")
            
            print(f"\nTotal: {len(df):,} repositories")
            print(f"Output file: {output_file}")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            print(f"❌ Error saving file: {e}")
            return False


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
