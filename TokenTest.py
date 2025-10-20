import os
import requests
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Configuration
NUMBER_OF_TOKENS = 13  # Must match the value in ReadmeScrapper_Batch.py

def test_github_token(token, token_number):
    """
    Test a single GitHub token by making a simple API request
    Returns: (is_valid, rate_limit_remaining, rate_limit_reset, error_message)
    """
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Authorization": f"Bearer {token}"
    }
    
    try:
        # Test with a simple API call to get rate limit info
        response = requests.get(
            "https://api.github.com/rate_limit",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            core_info = data.get("rate", {})
            remaining = core_info.get("remaining", 0)
            limit = core_info.get("limit", 0)
            reset_timestamp = core_info.get("reset", 0)
            reset_time = datetime.fromtimestamp(reset_timestamp).strftime('%Y-%m-%d %H:%M:%S')
            
            return True, remaining, limit, reset_time, None
        
        elif response.status_code == 401:
            return False, 0, 0, None, "Unauthorized - Invalid token"
        
        elif response.status_code == 403:
            return False, 0, 0, None, "Forbidden - Token may be expired or revoked"
        
        else:
            return False, 0, 0, None, f"HTTP {response.status_code}"
    
    except requests.exceptions.Timeout:
        return False, 0, 0, None, "Request timeout"
    
    except requests.exceptions.ConnectionError:
        return False, 0, 0, None, "Connection error"
    
    except Exception as e:
        return False, 0, 0, None, f"Error: {str(e)}"


def main():
    """Test all GitHub tokens and generate report"""
    print(f"\n{'='*80}")
    print(f"GITHUB TOKEN VALIDATOR")
    print(f"{'='*80}\n")
    print(f"Testing {NUMBER_OF_TOKENS} tokens from .env file...")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    tokens_to_test = []
    
    # Load all tokens
    for i in range(1, NUMBER_OF_TOKENS + 1):
        token = os.getenv(f'GITHUB_TOKEN_{i}')
        if token:
            tokens_to_test.append((i, token))
        else:
            print(f"⚠️  GITHUB_TOKEN_{i}: Not found in .env file")
    
    print(f"\nFound {len(tokens_to_test)} tokens to test\n")
    print(f"{'='*80}\n")
    
    working_tokens = []
    broken_tokens = []
    
    # Test each token
    for token_num, token in tokens_to_test:
        print(f"Testing GITHUB_TOKEN_{token_num}...", end=" ")
        
        is_valid, remaining, limit, reset_time, error = test_github_token(token, token_num)
        
        if is_valid:
            working_tokens.append(token_num)
            print(f"✅ WORKING")
            print(f"   Rate Limit: {remaining:,}/{limit:,} remaining")
            print(f"   Resets at: {reset_time}")
        else:
            broken_tokens.append((token_num, error))
            print(f"❌ FAILED")
            print(f"   Error: {error}")
        
        print()
    
    # Summary Report
    print(f"{'='*80}")
    print(f"SUMMARY REPORT")
    print(f"{'='*80}\n")
    
    total_tested = len(tokens_to_test)
    total_working = len(working_tokens)
    total_broken = len(broken_tokens)
    missing = NUMBER_OF_TOKENS - total_tested
    
    print(f"📊 Statistics:")
    print(f"   Total tokens expected: {NUMBER_OF_TOKENS}")
    print(f"   Tokens found: {total_tested}")
    print(f"   Missing tokens: {missing}")
    print(f"   Working tokens: {total_working} ✅")
    print(f"   Broken tokens: {total_broken} ❌")
    print(f"   Success rate: {(total_working/total_tested*100) if total_tested > 0 else 0:.1f}%")
    
    if working_tokens:
        print(f"\n✅ Working tokens: {', '.join([f'TOKEN_{n}' for n in working_tokens])}")
    
    if broken_tokens:
        print(f"\n❌ Broken tokens:")
        for token_num, error in broken_tokens:
            print(f"   • GITHUB_TOKEN_{token_num}: {error}")
    
    if missing > 0:
        print(f"\n⚠️  Missing tokens:")
        for i in range(1, NUMBER_OF_TOKENS + 1):
            if not any(t[0] == i for t in tokens_to_test):
                print(f"   • GITHUB_TOKEN_{i}")
    
    print(f"\n{'='*80}")
    
    if total_broken > 0 or missing > 0:
        print(f"⚠️  ACTION REQUIRED: Please fix broken/missing tokens in .env file")
    else:
        print(f"✅ ALL TOKENS ARE WORKING! Ready to scrape.")
    
    print(f"{'='*80}\n")
    
    # Calculate total scraping capacity
    if total_working > 0:
        print(f"💡 Scraping Capacity:")
        print(f"   Total API requests/hour: {total_working * 5000:,}")
        print(f"   Recommended REPOS_PER_HOUR: {total_working * 1000:,}")
        print()


if __name__ == "__main__":
    main()
