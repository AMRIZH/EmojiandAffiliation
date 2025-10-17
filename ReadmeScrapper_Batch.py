import requests
import csv
import time
import base64
from datetime import datetime, timedelta
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================
# CONFIGURATION - Edit these variables
# ============================
MIN_STARS = 1000  # Minimum number of stars
MAX_STARS = 160000  # Maximum number of stars
REPOS_PER_HOUR = 8000  # Repositories to scrape per hour (example: 6 tokens * 1000 repos each)
MIN_COLLABORATORS = 0  # Minimum number of collaborators (0 = no minimum)
README_CHAR_LIMIT = 10000000  # Maximum number of characters to keep from README
MAX_WORKERS = 8 # Number of parallel threads (matches number of tokens)
OUTPUT_CSV = "github_readmes_batch.csv"  # Main output file (will be appended to)

# Load GitHub tokens from environment variables
github_tokens = []
for i in range(1, 9):  # Load up to 8 tokens
    token = os.getenv(f'GITHUB_TOKEN_{i}')
    if token:
        github_tokens.append(token)

if not github_tokens:
    raise ValueError("No GitHub tokens found! Please set GITHUB_TOKEN_1, GITHUB_TOKEN_2, etc. in .env file")
# ============================

class BatchReadmeScrapper:
    def __init__(self, github_tokens):
        """Initialize scrapper with multiple tokens"""
        self.base_url = "https://api.github.com"
        self.tokens = github_tokens if isinstance(github_tokens, list) else [github_tokens]
        
        # Create headers for each token
        self.all_headers = []
        for token in self.tokens:
            headers = {
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "Authorization": f"Bearer {token}"
            }
            self.all_headers.append(headers)
        
        self.headers = self.all_headers[0]
        self.print_lock = threading.Lock()
        self.repos_lock = threading.Lock()
        self.scraped_urls = set()  # Track scraped repos to avoid duplicates
    
    def get_all_unique_repos(self, min_stars, max_stars):
        """
        Step 1: Scan for ALL unique repositories by using fine-grained star ranges
        
        Returns:
            List of all unique repository URLs with metadata
        """
        print(f"\n{'='*80}")
        print(f"STEP 1: SCANNING FOR ALL UNIQUE REPOSITORIES")
        print(f"{'='*80}\n")
        print(f"Star range: {min_stars:,} to {max_stars:,}")
        print(f"Strategy: Fine-grained star-based pagination to bypass 1,000 limit")
        
        scan_start_time = datetime.now()
        print(f"⏰ Scanning started at: {scan_start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        all_repos = []
        current_max = max_stars
        range_size = 2000  # Start with larger range (more efficient)
        
        # Work backwards from high stars to low stars
        while current_max >= min_stars:
            current_min = max(min_stars, current_max - range_size)
            
            with self.print_lock:
                print(f"🔍 Scanning stars {current_min:,} to {current_max:,}... (range: {range_size})")
            
            # Use first token for scanning
            repos = self._search_repo_metadata(current_min, current_max, self.all_headers[0])
            
            if repos:
                # Check if we hit the 1,000 limit
                if len(repos) >= 1000:
                    with self.print_lock:
                        print(f"   ⚠️  Hit 1,000 limit! Re-scanning with smaller ranges to avoid data loss...")
                    
                    # Re-scan this range with smaller chunks
                    new_range_size = max(10, range_size // 3)
                    rescan_max = current_max
                    rescan_repos = []
                    
                    while rescan_max >= current_min:
                        rescan_min = max(current_min, rescan_max - new_range_size)
                        
                        with self.print_lock:
                            print(f"   🔄 Re-scanning {rescan_min:,} to {rescan_max:,} (range: {new_range_size})")
                        
                        chunk_repos = self._search_repo_metadata(rescan_min, rescan_max, self.all_headers[0])
                        
                        if chunk_repos:
                            rescan_repos.extend(chunk_repos)
                            with self.print_lock:
                                print(f"      ✅ Found {len(chunk_repos)} repos | Re-scan total: {len(rescan_repos)}")
                            
                            # If still hitting limit in re-scan, reduce further
                            if len(chunk_repos) >= 1000:
                                new_range_size = max(10, new_range_size // 2)
                                with self.print_lock:
                                    print(f"      ⚠️  Still hit limit, reducing to {new_range_size}")
                        
                        rescan_max = rescan_min - 1
                        time.sleep(0.3)
                    
                    # Use re-scanned repos instead
                    all_repos.extend(rescan_repos)
                    with self.print_lock:
                        print(f"   ✅ Re-scan complete: {len(rescan_repos)} repos | Total: {len(all_repos):,}")
                    
                    # Adjust range size for next iteration
                    range_size = new_range_size
                else:
                    # No limit hit - add repos normally
                    all_repos.extend(repos)
                    with self.print_lock:
                        print(f"   ✅ Found {len(repos)} repos | Total: {len(all_repos):,}")
                    
                    # Dynamic range adjustment
                    if len(repos) >= 500:
                        # Getting close to limit - reduce slightly
                        range_size = max(500, int(range_size * 0.8))
                    elif len(repos) < 100:
                        # Very sparse - increase range size aggressively
                        range_size = min(10000, range_size * 3)
                        with self.print_lock:
                            print(f"   📈 Sparse region, expanding range to {range_size}")
                    elif len(repos) < 300:
                        # Somewhat sparse - increase range
                        range_size = min(5000, range_size * 2)
            else:
                # No repos found - expand range
                range_size = min(10000, range_size * 2)
            
            current_max = current_min - 1
            time.sleep(0.3)  # Reduced wait time for efficiency
        
        scan_end_time = datetime.now()
        scan_duration = scan_end_time - scan_start_time
        scan_minutes = scan_duration.total_seconds() / 60
        
        print(f"\n✅ Scan complete: Found {len(all_repos):,} total unique repositories")
        print(f"⏱️  Scanning duration: {int(scan_minutes)} minutes {int(scan_duration.total_seconds() % 60)} seconds\n")
        
        return all_repos
    
    def _search_repo_metadata(self, min_stars, max_stars, headers):
        """Search for repository metadata in a star range"""
        repos = []
        page = 1
        
        while len(repos) < 1000:
            url = f"{self.base_url}/search/repositories"
            params = {
                "q": f"stars:{min_stars}..{max_stars}",
                "sort": "stars",
                "order": "desc",
                "per_page": 100,
                "page": page
            }
            
            try:
                response = requests.get(url, headers=headers, params=params, timeout=30)
                
                if response.status_code != 200:
                    break
                
                data = response.json()
                items = data.get("items", [])
                
                if not items:
                    break
                
                repos.extend(items)
                
                if len(repos) >= data.get("total_count", 0) or page >= 10:
                    break
                
                page += 1
                time.sleep(0.5)
                
            except Exception as e:
                with self.print_lock:
                    print(f"   Error: {e}")
                break
        
        return repos[:1000]
    
    def scrape_batch(self, repos_batch, batch_num, total_batches):
        """
        Step 2: Scrape a batch of repositories (parallel with 6 workers)
        """
        batch_start_time = datetime.now()
        
        print(f"\n{'='*80}")
        print(f"BATCH {batch_num}/{total_batches}: SCRAPING {len(repos_batch)} REPOSITORIES")
        print(f"{'='*80}")
        print(f"⏰ Batch started at: {batch_start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        repo_data_list = []
        repos_per_worker = len(repos_batch) // MAX_WORKERS + 1
        
        # Split repos among workers
        worker_batches = [repos_batch[i:i+repos_per_worker] 
                         for i in range(0, len(repos_batch), repos_per_worker)]
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {}
            for worker_id, worker_repos in enumerate(worker_batches):
                if not worker_repos:
                    continue
                headers = self.all_headers[worker_id % len(self.all_headers)]
                future = executor.submit(
                    self._scrape_repos_worker,
                    worker_repos, worker_id + 1, headers, batch_num
                )
                futures[future] = worker_id + 1
            
            for future in as_completed(futures):
                worker_id = futures[future]
                try:
                    worker_data = future.result()
                    repo_data_list.extend(worker_data)
                except Exception as e:
                    print(f"❌ Worker {worker_id} failed: {e}")
        
        batch_end_time = datetime.now()
        batch_duration = batch_end_time - batch_start_time
        batch_minutes = batch_duration.total_seconds() / 60
        
        print(f"\n✅ Batch {batch_num} complete: {len(repo_data_list)} repos scraped")
        print(f"⏱️  Batch duration: {int(batch_minutes)} minutes {int(batch_duration.total_seconds() % 60)} seconds")
        print(f"📊 Average time per repo: {batch_duration.total_seconds() / len(repos_batch):.2f} seconds\n")
        
        return repo_data_list
    
    def _scrape_repos_worker(self, repos, worker_id, headers, batch_num):
        """Worker function to scrape repositories"""
        repo_data_list = []
        
        for idx, repo in enumerate(repos, 1):
            owner = repo["owner"]["login"]
            repo_name = repo["name"]
            repo_url = repo["html_url"]
            
            # Skip if already scraped
            with self.repos_lock:
                if repo_url in self.scraped_urls:
                    continue
                self.scraped_urls.add(repo_url)
            
            stars = repo["stargazers_count"]
            description = repo.get("description", "") or ""
            topics = ", ".join(repo.get("topics", []))
            
            with self.print_lock:
                print(f"[W{worker_id} {idx}/{len(repos)}] {owner}/{repo_name} ({stars:,} ⭐)")
            
            # Get collaborators count (before README to ensure README is last)
            if MIN_COLLABORATORS > 0:
                collaborators_count = self._get_collaborators_count(owner, repo_name, headers)
                # Skip repo if below minimum collaborators
                if collaborators_count < MIN_COLLABORATORS:
                    with self.print_lock:
                        print(f"   ⏭️  Skipped: Only {collaborators_count} collaborators (min: {MIN_COLLABORATORS})")
                    continue
            else:
                # Always fetch collaborators count
                collaborators_count = self._get_collaborators_count(owner, repo_name, headers)
            
            # Get README (always last API call)
            readme_content = self._get_readme(owner, repo_name, headers)
            
            repo_data = {
                "repo_owner": owner,
                "repo_name": repo_name,
                "repo_stars": stars,
                "repo_url": repo_url,
                "description": description,
                "collaborators": collaborators_count,
                "topics": topics,
                "readme": readme_content or ""
            }
            repo_data_list.append(repo_data)
            
            time.sleep(0.3)  # Rate limiting
        
        return repo_data_list
    
    def _get_collaborators_count(self, owner, repo, headers):
        """Get the number of collaborators for a repository"""
        url = f"{self.base_url}/repos/{owner}/{repo}/collaborators"
        
        try:
            response = requests.get(url, headers=headers, params={'per_page': 1}, timeout=30)
            
            if response.status_code == 200:
                # Get total count from Link header if available
                link_header = response.headers.get('Link', '')
                if 'last' in link_header:
                    import re
                    last_page = re.search(r'page=(\d+)>; rel="last"', link_header)
                    if last_page:
                        return int(last_page.group(1))
                # If no pagination, count the items in response
                return len(response.json())
            else:
                return 0
        except:
            return 0
    
    def _get_readme(self, owner, repo, headers):
        """Get README content"""
        url = f"{self.base_url}/repos/{owner}/{repo}/readme"
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                content = data.get('content', '')
                if content:
                    decoded = base64.b64decode(content).decode('utf-8', errors='ignore')
                    if README_CHAR_LIMIT:
                        decoded = decoded[:README_CHAR_LIMIT]
                    return decoded
        except:
            pass
        
        return None
    
    def save_batch_to_csv(self, repo_data, is_first_batch=False):
        """
        Step 3: Save batch to CSV (append mode)
        """
        if not repo_data:
            return
        
        fieldnames = ["repo_owner", "repo_name", "repo_stars", "repo_url", 
                     "description", "collaborators", "topics", "readme"]
        
        mode = 'w' if is_first_batch else 'a'
        write_header = is_first_batch
        
        try:
            with open(OUTPUT_CSV, mode, newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                if write_header:
                    writer.writeheader()
                writer.writerows(repo_data)
            
            print(f"💾 Saved {len(repo_data)} repos to {OUTPUT_CSV}")
        except Exception as e:
            print(f"❌ Error saving CSV: {e}")
    
    def wait_for_next_batch(self, batch_num, total_batches):
        """
        Step 4: Wait 60 minutes before next batch
        """
        if batch_num < total_batches:
            print(f"\n{'='*80}")
            print(f"⏱️  WAITING 60 MINUTES BEFORE NEXT BATCH")
            print(f"{'='*80}\n")
            
            wait_minutes = 60
            end_time = datetime.now() + timedelta(minutes=wait_minutes)
            
            print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Next batch starts: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Sleeping for {wait_minutes} minutes...\n")
            
            time.sleep(wait_minutes * 60)
    
    def run_continuous_scraping(self, min_stars, max_stars, repos_per_hour):
        """
        Main workflow: Scan → Batch scrape → Save → Wait → Repeat
        """
        total_start_time = datetime.now()
        
        print(f"\n{'='*80}")
        print(f"CONTINUOUS BATCH SCRAPING MODE")
        print(f"{'='*80}\n")
        print(f"Configuration:")
        print(f"  Stars: {min_stars:,} to {max_stars:,}")
        print(f"  Repos per hour: {repos_per_hour:,}")
        print(f"  Workers: {MAX_WORKERS}")
        print(f"  Tokens: {len(self.tokens)}")
        print(f"  Output: {OUTPUT_CSV}")
        print(f"\n⏰ Total scraping started at: {total_start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Step 1: Get all unique repos
        all_repos = self.get_all_unique_repos(min_stars, max_stars)
        
        if not all_repos:
            print("❌ No repositories found!")
            return
        
        # Calculate batches
        total_repos = len(all_repos)
        num_batches = (total_repos + repos_per_hour - 1) // repos_per_hour
        
        print(f"📊 Total repos to scrape: {total_repos:,}")
        print(f"📦 Number of batches: {num_batches}")
        print(f"🕒 Estimated time: {num_batches} hours\n")
        
        # Process each batch
        for batch_num in range(1, num_batches + 1):
            start_idx = (batch_num - 1) * repos_per_hour
            end_idx = min(start_idx + repos_per_hour, total_repos)
            batch_repos = all_repos[start_idx:end_idx]
            
            # Step 2: Scrape batch
            batch_data = self.scrape_batch(batch_repos, batch_num, num_batches)
            
            # Step 3: Save to CSV
            self.save_batch_to_csv(batch_data, is_first_batch=(batch_num == 1))
            
            print(f"\n📈 Progress: {end_idx:,}/{total_repos:,} repos ({end_idx/total_repos*100:.1f}%)")
            
            # Step 4: Wait before next batch (except for last batch)
            self.wait_for_next_batch(batch_num, num_batches)
        
        total_end_time = datetime.now()
        total_duration = total_end_time - total_start_time
        total_hours = total_duration.total_seconds() / 3600
        total_minutes = (total_duration.total_seconds() % 3600) / 60
        
        print(f"\n{'='*80}")
        print(f"✅ ALL SCRAPING COMPLETE!")
        print(f"{'='*80}\n")
        print(f"📊 FINAL STATISTICS:")
        print(f"  Total repos scraped: {total_repos:,}")
        print(f"  Batches completed: {num_batches}")
        print(f"  Output file: {OUTPUT_CSV}")
        print(f"\n⏱️  TOTAL TIME:")
        print(f"  Started: {total_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Ended: {total_end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Duration: {int(total_hours)} hours {int(total_minutes)} minutes")
        print(f"  Average: {total_duration.total_seconds() / total_repos:.2f} seconds per repo")
        print(f"\n{'='*80}")


def main():
    """Main function"""
    print(f"\n{'='*80}")
    print(f"GITHUB BATCH README SCRAPER")
    print(f"{'='*80}\n")
    
    scraper = BatchReadmeScrapper(github_tokens)
    
    scraper.run_continuous_scraping(
        min_stars=MIN_STARS,
        max_stars=MAX_STARS,
        repos_per_hour=REPOS_PER_HOUR
    )


if __name__ == "__main__":
    main()
