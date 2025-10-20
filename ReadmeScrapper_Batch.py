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
OUTPUT_CSV = "github_readmes_batch.csv"  # Main output file (will be appended to)
MIN_STARS = 1000  # Minimum number of stars
MAX_STARS = 150000  # Maximum number of stars
MIN_CONTRIBUTORS = 0  # Minimum number of contributors (0 = no minimum, contributors = people who made commits)
README_CHAR_LIMIT = 1000000  # Maximum number of characters to keep from README
NUMBER_OF_TOKENS = 12  # Total number of GitHub tokens available in .env file
MAX_WORKERS = 4  # Number of parallel threads (can be less than NUMBER_OF_TOKENS for fewer logical processors)

# Load GitHub tokens from environment variables
github_tokens = []
for i in range(1, NUMBER_OF_TOKENS + 1):
    token = os.getenv(f'GITHUB_TOKEN_{i}')
    if token:
        github_tokens.append(token)

if not github_tokens:
    raise ValueError("No GitHub tokens found! Please set GITHUB_TOKEN_1, GITHUB_TOKEN_2, etc. in .env file")
# ============================

class BatchReadmeScrapper:
    def __init__(self, github_tokens, max_workers):
        """Initialize scrapper with multiple tokens and worker configuration"""
        self.base_url = "https://api.github.com"
        self.tokens = github_tokens if isinstance(github_tokens, list) else [github_tokens]
        self.max_workers = max_workers
        
        # Create headers for each token
        self.all_headers = []
        for token in self.tokens:
            headers = {
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "Authorization": f"Bearer {token}"
            }
            self.all_headers.append(headers)
        
        # Distribute tokens across workers (each worker gets one or more tokens)
        self.tokens_per_worker = len(self.tokens) // max_workers
        if self.tokens_per_worker == 0:
            self.tokens_per_worker = 1
        
        # Create token groups for each worker
        self.worker_token_groups = []
        for i in range(max_workers):
            start_idx = i * self.tokens_per_worker
            end_idx = start_idx + self.tokens_per_worker
            if i == max_workers - 1:  # Last worker gets remaining tokens
                end_idx = len(self.all_headers)
            self.worker_token_groups.append(self.all_headers[start_idx:end_idx])
        
        self.headers = self.all_headers[0]
        self.print_lock = threading.Lock()
        self.repos_lock = threading.Lock()
        self.scraped_urls = set()  # Track scraped repos to avoid duplicates
        
        # Track rate limit status for each token
        self.token_rate_limits = {}
        self.rate_limit_lock = threading.Lock()
        for i, token in enumerate(self.tokens):
            self.token_rate_limits[i] = {
                'remaining': 5000,
                'reset_time': None,
                'is_limited': False
            }
    
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
    
    def _update_rate_limit_from_response(self, response, token_index):
        """Update rate limit tracking from API response headers"""
        try:
            remaining = int(response.headers.get('X-RateLimit-Remaining', 5000))
            reset_timestamp = int(response.headers.get('X-RateLimit-Reset', 0))
            reset_time = datetime.fromtimestamp(reset_timestamp) if reset_timestamp else None
            
            with self.rate_limit_lock:
                self.token_rate_limits[token_index]['remaining'] = remaining
                self.token_rate_limits[token_index]['reset_time'] = reset_time
                self.token_rate_limits[token_index]['is_limited'] = (remaining < 10)
        except:
            pass
    
    def _get_available_token(self, token_group):
        """Get a non-rate-limited token from the group, or None if all are limited"""
        for headers in token_group:
            # Find the token index for this header
            token_index = self.all_headers.index(headers)
            with self.rate_limit_lock:
                if not self.token_rate_limits[token_index]['is_limited']:
                    return headers, token_index
        return None, None
    
    def _all_tokens_limited(self):
        """Check if all tokens are rate limited"""
        with self.rate_limit_lock:
            return all(info['is_limited'] for info in self.token_rate_limits.values())
    
    def _get_earliest_reset_time(self):
        """Get the earliest reset time among all rate-limited tokens"""
        with self.rate_limit_lock:
            reset_times = [info['reset_time'] for info in self.token_rate_limits.values() 
                          if info['reset_time'] is not None]
            return min(reset_times) if reset_times else None
    
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
        Step 2: Scrape a batch of repositories (parallel with configured workers)
        """
        batch_start_time = datetime.now()
        
        print(f"\n{'='*80}")
        print(f"BATCH {batch_num}/{total_batches}: SCRAPING {len(repos_batch)} REPOSITORIES")
        print(f"{'='*80}")
        print(f"⏰ Batch started at: {batch_start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        repo_data_list = []
        repos_per_worker = len(repos_batch) // self.max_workers + 1
        
        # Split repos among workers
        worker_batches = [repos_batch[i:i+repos_per_worker] 
                         for i in range(0, len(repos_batch), repos_per_worker)]
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            for worker_id, worker_repos in enumerate(worker_batches):
                if not worker_repos:
                    continue
                # Each worker gets its assigned token group
                token_group = self.worker_token_groups[worker_id % len(self.worker_token_groups)]
                future = executor.submit(
                    self._scrape_repos_worker,
                    worker_repos, worker_id + 1, token_group, batch_num
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
    
    def _scrape_repos_worker(self, repos, worker_id, token_group, batch_num):
        """Worker function to scrape repositories - rotates through assigned tokens"""
        repo_data_list = []
        current_token_idx = 0
        
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
            created_at = repo.get("created_at", "")  # Get repository creation date
            
            # Get an available token (not rate limited)
            headers, token_index = self._get_available_token(token_group)
            if headers is None:
                # All tokens in this group are rate limited
                with self.print_lock:
                    print(f"[W{worker_id}] ⚠️  All tokens exhausted, stopping early")
                break
            
            with self.print_lock:
                print(f"[W{worker_id} {idx}/{len(repos)}] {owner}/{repo_name} ({stars:,} ⭐)")
            
            # Get contributors count (publicly accessible, before README to ensure README is last)
            if MIN_CONTRIBUTORS > 0:
                contributors_count = self._get_contributors_count(owner, repo_name, headers, token_index)
                # Skip repo if below minimum contributors
                if contributors_count < MIN_CONTRIBUTORS:
                    with self.print_lock:
                        print(f"   ⏭️  Skipped: Only {contributors_count} contributors (min: {MIN_CONTRIBUTORS})")
                    continue
            else:
                # Always fetch contributors count
                contributors_count = self._get_contributors_count(owner, repo_name, headers, token_index)
            
            # Get README (always last API call)
            readme_content = self._get_readme(owner, repo_name, headers, token_index)
            
            repo_data = {
                "repo_owner": owner,
                "repo_name": repo_name,
                "repo_stars": stars,
                "repo_url": repo_url,
                "description": description,
                "contributors": contributors_count,
                "topics": topics,
                "created_at": created_at,
                "readme": readme_content or ""
            }
            repo_data_list.append(repo_data)
            
            time.sleep(0.3)  # Rate limiting
        
        return repo_data_list
    
    def _get_contributors_count(self, owner, repo, headers, token_index):
        """Get the number of contributors for a repository (publicly accessible)"""
        # Use contributors endpoint (publicly accessible)
        url = f"{self.base_url}/repos/{owner}/{repo}/contributors"
        
        try:
            # First request to get Link header for total count
            response = requests.get(url, headers=headers, params={'per_page': 1, 'anon': 'true'}, timeout=30)
            
            # Update rate limit tracking
            self._update_rate_limit_from_response(response, token_index)
            
            if response.status_code == 200:
                # Get total count from Link header if available
                link_header = response.headers.get('Link', '')
                if 'last' in link_header:
                    import re
                    last_page = re.search(r'page=(\d+)>; rel="last"', link_header)
                    if last_page:
                        count = int(last_page.group(1))
                        return count
                # If no pagination, get all contributors on first page
                response_full = requests.get(url, headers=headers, params={'per_page': 100, 'anon': 'true'}, timeout=30)
                if response_full.status_code == 200:
                    return len(response_full.json())
                return 1  # At least 1 contributor (the owner)
            elif response.status_code == 403:
                # Rate limit or forbidden - return 0
                return 0
            elif response.status_code == 404:
                # Repository not found or no contributors
                return 0
            else:
                return 0
        except Exception as e:
            return 0
    
    def _get_readme(self, owner, repo, headers, token_index):
        """Get README content"""
        url = f"{self.base_url}/repos/{owner}/{repo}/readme"
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            
            # Update rate limit tracking
            self._update_rate_limit_from_response(response, token_index)
            
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
                     "description", "contributors", "topics", "created_at", "readme"]
        
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
    
    def _wait_for_rate_limit_reset(self):
        """Wait until the earliest rate limit resets"""
        reset_time = self._get_earliest_reset_time()
        
        if reset_time is None:
            # Fallback to 60 minutes if no reset time available
            wait_seconds = 3600
            reset_time = datetime.now() + timedelta(seconds=wait_seconds)
        else:
            wait_seconds = max(0, (reset_time - datetime.now()).total_seconds())
        
        # Add 5 seconds buffer
        wait_seconds += 5
        
        print(f"\n{'='*80}")
        print(f"⏱️  WAITING FOR RATE LIMIT RESET")
        print(f"{'='*80}\n")
        print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Reset time: {reset_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Wait duration: {int(wait_seconds // 60)} minutes {int(wait_seconds % 60)} seconds")
        
        # Display rate limit status
        with self.rate_limit_lock:
            for token_idx, info in self.token_rate_limits.items():
                status = "🔴 RATE LIMITED" if info['is_limited'] else "🟢 AVAILABLE"
                print(f"  Token {token_idx + 1}: {info['remaining']:,}/5,000 remaining - {status}")
        
        print(f"\nSleeping until {reset_time.strftime('%H:%M:%S')}...\n")
        time.sleep(wait_seconds)
        
        # Reset all token limits after waiting
        with self.rate_limit_lock:
            for token_idx in self.token_rate_limits:
                self.token_rate_limits[token_idx]['is_limited'] = False
                self.token_rate_limits[token_idx]['remaining'] = 5000
        
        print(f"✅ Rate limits reset! Resuming scraping...\n")
    
    def run_continuous_scraping(self, min_stars, max_stars):
        """Main workflow: Scan → Scrape until rate limited → Wait for reset → Repeat"""
        total_start_time = datetime.now()
        
        print(f"\n{'='*80}")
        print(f"DYNAMIC RATE-LIMIT AWARE SCRAPING MODE")
        print(f"{'='*80}\n")
        print(f"Configuration:")
        print(f"  Stars: {min_stars:,} to {max_stars:,}")
        print(f"  Workers: {self.max_workers}")
        print(f"  Total Tokens: {len(self.tokens)}")
        print(f"  Tokens per Worker: {self.tokens_per_worker}")
        print(f"  Strategy: Scrape until all tokens rate-limited, then wait for reset")
        print(f"  Output: {OUTPUT_CSV}")
        print(f"\n⏰ Total scraping started at: {total_start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Step 1: Get all unique repos
        all_repos = self.get_all_unique_repos(min_stars, max_stars)
        
        if not all_repos:
            print("❌ No repositories found!")
            return
        
        total_repos = len(all_repos)
        print(f"📊 Total repos to scrape: {total_repos:,}\n")
        
        # Process repos dynamically until all are scraped
        current_idx = 0
        batch_num = 0
        is_first_save = True
        
        while current_idx < total_repos:
            batch_num += 1
            
            # Scrape repos until all tokens are rate limited
            print(f"\n{'='*80}")
            print(f"BATCH {batch_num}: SCRAPING UNTIL RATE LIMITED")
            print(f"{'='*80}")
            print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"� Starting from repo {current_idx + 1:,}/{total_repos:,}\n")
            
            batch_start_idx = current_idx
            all_batch_data = []
            
            # Scrape in chunks until all tokens exhausted
            while current_idx < total_repos and not self._all_tokens_limited():
                # Take a chunk of repos to scrape
                chunk_size = 500
                end_idx = min(current_idx + chunk_size, total_repos)
                chunk_repos = all_repos[current_idx:end_idx]
                
                # Scrape this chunk
                chunk_data = self.scrape_batch(chunk_repos, batch_num, "∞")
                all_batch_data.extend(chunk_data)
                
                current_idx = end_idx
                
                # Check if we should stop
                if self._all_tokens_limited():
                    print(f"\n⚠️  All tokens are rate limited!")
                    break
            
            # Save all data from this batch
            if all_batch_data:
                self.save_batch_to_csv(all_batch_data, is_first_batch=is_first_save)
                is_first_save = False
            
            repos_scraped = current_idx - batch_start_idx
            print(f"\n✅ Batch {batch_num} complete: {repos_scraped:,} repos scraped")
            print(f"📈 Total progress: {current_idx:,}/{total_repos:,} repos ({current_idx/total_repos*100:.1f}%)")
            
            # Wait for rate limit reset if not done
            if current_idx < total_repos:
                self._wait_for_rate_limit_reset()
        
        total_end_time = datetime.now()
        total_duration = total_end_time - total_start_time
        total_hours = total_duration.total_seconds() / 3600
        total_minutes = (total_duration.total_seconds() % 3600) / 60
        
        print(f"\n{'='*80}")
        print(f"✅ ALL SCRAPING COMPLETE!")
        print(f"{'='*80}\n")
        print(f"📊 FINAL STATISTICS:")
        print(f"  Total repos scraped: {total_repos:,}")
        print(f"  Batches completed: {batch_num}")
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
    print(f"Token Configuration:")
    print(f"  Total tokens loaded: {len(github_tokens)}")
    print(f"  Workers: {MAX_WORKERS}")
    print(f"  Tokens per worker: {len(github_tokens) // MAX_WORKERS}")
    print(f"  Max API points/hour: {len(github_tokens) * 5000:,}\n")
    
    scraper = BatchReadmeScrapper(github_tokens, MAX_WORKERS)
    
    scraper.run_continuous_scraping(
        min_stars=MIN_STARS,
        max_stars=MAX_STARS
    )


if __name__ == "__main__":
    main()
