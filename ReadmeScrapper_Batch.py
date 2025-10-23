import requests
import csv
import time
import base64
from datetime import datetime, timedelta
import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================
# CONFIGURATION - Edit these variables
# ============================
OUTPUT_CSV = "github_readmes_batch.csv"  # Main output file (will be appended to)
MIN_STARS = 100  # Minimum number of stars
MAX_STARS = 400000  # Maximum number of stars
MIN_CONTRIBUTORS = 0  # Minimum number of contributors (0 = no minimum, contributors = people who made commits)
README_CHAR_LIMIT = 1000000  # Maximum number of characters to keep from README
NUMBER_OF_TOKENS = 20  # Total number of GitHub tokens available in .env file
MAX_WORKERS = 12  # Number of parallel threads (match this with your logical processors)
PARALLEL_SCAN_WORKERS = 20  # Number of parallel workers for scanning phase (1-20, recommended: 4-8)

# Load GitHub tokens from environment variables
github_tokens = []
for i in range(1, NUMBER_OF_TOKENS + 1):
    token = os.getenv(f'GITHUB_TOKEN_{i}')
    if token:
        github_tokens.append(token)

if not github_tokens:
    raise ValueError("No GitHub tokens found! Please set GITHUB_TOKEN_1, GITHUB_TOKEN_2, etc. in .env file")

# Load Discord webhook URL
DISCORD_WEBHOOK_URL = os.getenv('discord_webhook_url')
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
        
        # Tracking statistics for logging
        self.sleep_cycles = 0
        self.batch_durations = []
        self.scan_duration = None
        
        # Cache management
        self.cache_dir = "cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Discord webhook URL
        self.discord_webhook_url = DISCORD_WEBHOOK_URL
    
    def _send_discord_message(self, content=None, embed=None):
        """Send a message to Discord via webhook"""
        if not self.discord_webhook_url:
            return False
        
        try:
            payload = {}
            
            if content:
                # Discord has a 2000 character limit for content
                if len(content) > 2000:
                    content = content[:1997] + "..."
                payload["content"] = content
            
            if embed:
                payload["embeds"] = [embed]
            
            response = requests.post(
                self.discord_webhook_url,
                json=payload,
                timeout=10
            )
            
            return response.status_code == 204
        except Exception as e:
            with self.print_lock:
                print(f"⚠️  Failed to send Discord notification: {e}")
            return False
    
    def _get_cache_filename(self, min_stars, max_stars):
        """Generate cache filename based on star range"""
        return os.path.join(self.cache_dir, f"star_distribution_{min_stars}_{max_stars}.json")
    
    def _load_cache(self, min_stars, max_stars):
        """Load cached star distribution if available"""
        cache_file = self._get_cache_filename(min_stars, max_stars)
        
        if not os.path.exists(cache_file):
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Check if cache is recent (less than 7 days old)
            cache_age = datetime.now() - datetime.fromisoformat(cache_data['timestamp'])
            if cache_age.days > 7:
                print(f"⚠️  Cache is {cache_age.days} days old, will refresh")
                return None
            
            print(f"✅ Loaded cache from {cache_file}")
            print(f"   Cache age: {cache_age.days} days")
            print(f"   Total repos in cache: {cache_data['total_repos']:,}")
            return cache_data['repos']
        except Exception as e:
            print(f"⚠️  Failed to load cache: {e}")
            return None
    
    def _save_cache(self, min_stars, max_stars, repos):
        """Save star distribution to cache"""
        cache_file = self._get_cache_filename(min_stars, max_stars)
        
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'min_stars': min_stars,
                'max_stars': max_stars,
                'total_repos': len(repos),
                'repos': repos
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
            
            print(f"💾 Saved cache to {cache_file}")
            print(f"   Total repos cached: {len(repos):,}")
        except Exception as e:
            print(f"⚠️  Failed to save cache: {e}")
    
    def get_all_unique_repos(self, min_stars, max_stars):
        """
        Step 1: Scan for ALL unique repositories by using fine-grained star ranges
        OPTIMIZED: Parallel scanning with multiple tokens + smart initial range sizing + cache
        
        Returns:
            List of all unique repository URLs with metadata
        """
        print(f"\n{'='*80}")
        print(f"STEP 1: SCANNING FOR ALL UNIQUE REPOSITORIES (PARALLEL MODE + CACHE)")
        print(f"{'='*80}\n")
        print(f"Star range: {min_stars:,} to {max_stars:,}")
        print(f"Strategy: Parallel fine-grained star-based pagination with caching")
        print(f"Parallel workers: {PARALLEL_SCAN_WORKERS}\n")
        
        # Try to load from cache first
        print(f"🔍 Checking for cached data...")
        cached_repos = self._load_cache(min_stars, max_stars)
        
        if cached_repos is not None:
            print(f"✅ Using cached data, skipping scan phase!\n")
            return cached_repos
        
        print(f"❌ No exact cache found, checking for partial cache...")
        
        # Check if we can load a higher range cache (e.g., 500-200000) and scan only the lower range (100-500)
        partial_cached_repos = None
        scan_min = min_stars
        scan_max = max_stars
        
        # Try to find cache for 500-200000 if our range includes it
        if min_stars < 500 and max_stars >= 500:
            print(f"   Checking for cache: 500-{max_stars}...")
            partial_cached_repos = self._load_cache(500, max_stars)
            if partial_cached_repos is not None:
                print(f"✅ Found partial cache: 500-{max_stars:,} stars ({len(partial_cached_repos):,} repos)")
                print(f"   Will only scan new range: {min_stars:,}-499 stars\n")
                scan_min = min_stars
                scan_max = 499
            else:
                print(f"   No partial cache found\n")
        else:
            print(f"   No applicable partial cache\n")
        
        scan_start_time = datetime.now()
        print(f"⏰ Scanning started at: {scan_start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Split star range into chunks using exponential distribution
        # Higher stars = larger chunks (sparse), Lower stars = smaller chunks (dense)
        num_parallel_scanners = min(PARALLEL_SCAN_WORKERS, len(self.all_headers))
        
        # Generate exponential distribution of star ranges
        scan_ranges = self._generate_exponential_scan_ranges(scan_min, scan_max, num_parallel_scanners)
        
        if partial_cached_repos is not None:
            print(f"🚀 Parallel scanning NEW range only ({scan_min:,}-{scan_max:,} stars) with {num_parallel_scanners} tokens:")
        else:
            print(f"🚀 Parallel scanning with {num_parallel_scanners} tokens:")
        print(f"   Strategy: Exponential distribution (large chunks for high stars, small chunks for low stars)\n")
        for chunk_min, chunk_max, idx in scan_ranges:
            chunk_size = chunk_max - chunk_min + 1
            print(f"   Token {idx+1}: {chunk_min:,} to {chunk_max:,} stars (range: {chunk_size:,})")
        print()
        
        # Parallel scanning with ThreadPoolExecutor
        all_repos = []
        with ThreadPoolExecutor(max_workers=num_parallel_scanners) as executor:
            futures = {}
            for chunk_min, chunk_max, token_idx in scan_ranges:
                future = executor.submit(
                    self._scan_star_range,
                    chunk_min, chunk_max, token_idx, min_stars
                )
                futures[future] = (chunk_min, chunk_max, token_idx)
            
            for future in as_completed(futures):
                chunk_min, chunk_max, token_idx = futures[future]
                try:
                    repos = future.result()
                    all_repos.extend(repos)
                    with self.print_lock:
                        print(f"✅ Token {token_idx+1} completed: {len(repos):,} repos from {chunk_min:,}-{chunk_max:,}")
                except Exception as e:
                    with self.print_lock:
                        print(f"❌ Token {token_idx+1} failed for range {chunk_min:,}-{chunk_max:,}: {e}")
        
        scan_end_time = datetime.now()
        scan_duration = scan_end_time - scan_start_time
        scan_minutes = scan_duration.total_seconds() / 60
        
        # Store scan duration for final report
        self.scan_duration = scan_duration
        
        print(f"\n✅ Scan complete: Found {len(all_repos):,} repositories in range {scan_min:,}-{scan_max:,}")
        print(f"⏱️  Scanning duration: {int(scan_minutes)} minutes {int(scan_duration.total_seconds() % 60)} seconds\n")
        
        # Send scanning report to Discord
        scan_embed = {
            "title": "🔍 Repository Scanning Complete",
            "color": 0x00FF00,  # Green
            "fields": [
                {"name": "Star Range", "value": f"{scan_min:,} - {scan_max:,}", "inline": True},
                {"name": "Repositories Found", "value": f"{len(all_repos):,}", "inline": True},
                {"name": "Duration", "value": f"{int(scan_minutes)}m {int(scan_duration.total_seconds() % 60)}s", "inline": True},
                {"name": "Parallel Workers", "value": f"{num_parallel_scanners}", "inline": True},
                {"name": "Cache Used", "value": "Yes" if partial_cached_repos else "No", "inline": True}
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        self._send_discord_message(embed=scan_embed)
        
        # Merge with partial cache if available
        if partial_cached_repos is not None:
            print(f"🔗 Merging with cached data ({len(partial_cached_repos):,} repos from 500-{max_stars:,})...")
            all_repos.extend(partial_cached_repos)
            print(f"✅ Total combined: {len(all_repos):,} unique repositories\n")
        
        # Save combined results to cache for future runs
        print(f"💾 Saving combined results to cache...")
        self._save_cache(min_stars, max_stars, all_repos)
        
        return all_repos
    
    def _get_smart_initial_range(self, stars):
        """
        Smart initial range sizing based on star density
        High stars = sparse (large range), Low stars = dense (small range)
        """
        if stars >= 100000:
            return 10000  # Very sparse
        elif stars >= 50000:
            return 5000   # Sparse
        elif stars >= 20000:
            return 3000   # Moderate-sparse
        elif stars >= 10000:
            return 2000   # Moderate
        elif stars >= 5000:
            return 1000   # Moderate-dense
        elif stars >= 2000:
            return 500    # Dense
        elif stars >= 1000:
            return 200    # Very dense
        else:
            return 100    # Extremely dense
    
    def _generate_exponential_scan_ranges(self, min_stars, max_stars, num_workers):
        """
        Generate scan ranges using exponential distribution
        Assigns larger ranges to high stars (sparse) and smaller ranges to low stars (dense)
        
        Strategy:
        - Use exponential curve to distribute the star range
        - High star ranges get exponentially larger chunks
        - Low star ranges get exponentially smaller chunks
        - Ensures balanced workload despite varying repository density
        
        Args:
            min_stars: Minimum stars
            max_stars: Maximum stars
            num_workers: Number of parallel workers
            
        Returns:
            List of tuples: [(chunk_min, chunk_max, worker_idx), ...]
        """
        import math
        
        # Use logarithmic scale for exponential distribution
        # log_min and log_max represent the logarithmic boundaries
        log_min = math.log10(max(min_stars, 1))  # Avoid log(0)
        log_max = math.log10(max_stars)
        log_range = log_max - log_min
        
        # Generate exponentially distributed breakpoints
        breakpoints = []
        for i in range(num_workers + 1):
            # Calculate position on logarithmic scale (reversed, high stars first)
            log_pos = log_max - (i * log_range / num_workers)
            star_pos = int(10 ** log_pos)
            breakpoints.append(max(min_stars, min(star_pos, max_stars)))
        
        # Ensure boundaries are exact
        breakpoints[0] = max_stars
        breakpoints[-1] = min_stars
        
        # Create ranges from breakpoints (working backwards from high to low)
        scan_ranges = []
        for i in range(num_workers):
            chunk_max = breakpoints[i]
            chunk_min = breakpoints[i + 1]
            
            # Skip empty ranges
            if chunk_max < chunk_min:
                continue
                
            scan_ranges.append((chunk_min, chunk_max, i))
        
        return scan_ranges
    
    def _scan_star_range(self, min_stars, max_stars, token_idx, global_min):
        """
        Scan a specific star range with one token (used for parallel scanning)
        """
        headers = self.all_headers[token_idx]
        all_repos = []
        current_max = max_stars
        range_size = self._get_smart_initial_range(max_stars)  # Smart initial sizing
        
        # Work backwards from high stars to low stars
        while current_max >= min_stars:
            current_min = max(min_stars, current_max - range_size)
            
            with self.print_lock:
                print(f"[T{token_idx+1}] 🔍 {current_min:,}-{current_max:,} (range: {range_size})")
            
            # Use assigned token for this range
            repos = self._search_repo_metadata(current_min, current_max, headers)
            
            if repos:
                # Check if we hit the 1,000 limit
                if len(repos) >= 1000:
                    with self.print_lock:
                        print(f"   ⚠️  Hit 1,000 limit! Re-scanning with smaller ranges to avoid data loss...")
                    
                    # Re-scan this range with smaller chunks (more aggressive reduction)
                    new_range_size = max(1, range_size // 5)  # More aggressive initial reduction
                    rescan_max = current_max
                    rescan_repos = []
                    rescan_attempts = 0
                    max_rescan_attempts = 5
                    
                    while rescan_max >= current_min and rescan_attempts < max_rescan_attempts:
                        rescan_min = max(current_min, rescan_max - new_range_size)
                        
                        with self.print_lock:
                            print(f"   🔄 Re-scanning {rescan_min:,} to {rescan_max:,} (range: {new_range_size})")
                        
                        chunk_repos = self._search_repo_metadata(rescan_min, rescan_max, self.all_headers[0])
                        
                        if chunk_repos:
                            # Check if we're still hitting the limit
                            if len(chunk_repos) >= 1000:
                                with self.print_lock:
                                    print(f"      ⚠️  Still hit 1,000 limit! Reducing range dramatically...")
                                
                                # Highly aggressive reduction when still hitting limit
                                new_range_size = max(1, new_range_size // 4)
                                rescan_attempts += 1
                                
                                with self.print_lock:
                                    print(f"      🔻 New range size: {new_range_size} (attempt {rescan_attempts}/{max_rescan_attempts})")
                                
                                # Don't add these repos, re-scan with smaller range
                                continue
                            else:
                                # Successfully got less than 1,000 repos
                                rescan_repos.extend(chunk_repos)
                                with self.print_lock:
                                    print(f"      ✅ Found {len(chunk_repos)} repos | Re-scan total: {len(rescan_repos)}")
                                
                                # Move to next range
                                rescan_max = rescan_min - 1
                                rescan_attempts = 0  # Reset attempts counter
                        else:
                            # No repos found, move to next range
                            rescan_max = rescan_min - 1
                        
                        time.sleep(0.05)  # Reduced sleep time for faster scanning
                    
                    # Use re-scanned repos instead
                    all_repos.extend(rescan_repos)
                    with self.print_lock:
                        print(f"   ✅ Re-scan complete: {len(rescan_repos)} repos | Total: {len(all_repos):,}")
                    
                    # Adjust range size for next iteration (keep it small after hitting limit)
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
            time.sleep(0.05)  # Optimized sleep time (4x faster)
        
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
                time.sleep(0.1)  # Reduced from 0.3 to 0.1 for faster scanning
                
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
            updated_at = repo.get("updated_at", "")  # Get last update time
            pushed_at = repo.get("pushed_at", "")  # Get last push time
            forks = repo.get("forks_count", 0)  # Get number of forks
            language = repo.get("language", "") or ""  # Get primary programming language
            owner_type = repo["owner"].get("type", "")  # Get owner type (User or Organization)
            
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
                "forks": forks,
                "language": language,
                "owner_type": owner_type,
                "topics": topics,
                "created_at": created_at,
                "updated_at": updated_at,
                "pushed_at": pushed_at,
                "readme": readme_content or ""
            }
            repo_data_list.append(repo_data)

            time.sleep(0.2)  # Rate limiting

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
                     "description", "contributors", "forks", "language", "owner_type", 
                     "topics", "created_at", "updated_at", "pushed_at", "readme"]
        
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
        self.sleep_cycles += 1
        
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
            batch_start_time = datetime.now()
            
            # Scrape in chunks until all tokens exhausted
            chunk_count = 0
            while current_idx < total_repos and not self._all_tokens_limited():
                # Take a chunk of repos to scrape
                chunk_size = 500
                end_idx = min(current_idx + chunk_size, total_repos)
                chunk_repos = all_repos[current_idx:end_idx]
                
                chunk_count += 1
                
                # Scrape this chunk (show "Batch X - Chunk Y" format)
                print(f"\n📦 Batch {batch_num} - Chunk {chunk_count}")
                chunk_data = self.scrape_batch(chunk_repos, f"{batch_num}.{chunk_count}", "⚡")
                all_batch_data.extend(chunk_data)
                
                current_idx = end_idx
                
                # Show chunk progress
                repos_so_far = current_idx - batch_start_idx
                print(f"   Chunk complete: {len(chunk_data):,} repos scraped in this chunk")
                print(f"   Batch progress: {repos_so_far:,} repos scraped this batch")
                
                # Check if we should stop
                if self._all_tokens_limited():
                    print(f"\n⚠️  All tokens are rate limited!")
                    break
            
            # Save all data from this batch
            if all_batch_data:
                self.save_batch_to_csv(all_batch_data, is_first_batch=is_first_save)
                is_first_save = False
            
            # Track batch duration
            batch_end_time = datetime.now()
            batch_duration = batch_end_time - batch_start_time
            self.batch_durations.append(batch_duration)
            
            repos_scraped = current_idx - batch_start_idx
            print(f"\n{'='*80}")
            print(f"✅ BATCH {batch_num} COMPLETE")
            print(f"{'='*80}")
            print(f"📊 Batch Statistics:")
            print(f"   Repos scraped this batch: {repos_scraped:,}")
            print(f"   Chunks processed: {chunk_count}")
            print(f"   Average repos/chunk: {repos_scraped/chunk_count:.1f}")
            print(f"\n📈 Overall Progress:")
            print(f"   Total scraped: {current_idx:,} / {total_repos:,} repos")
            print(f"   Progress: {current_idx/total_repos*100:.2f}%")
            print(f"   Remaining: {total_repos - current_idx:,} repos")
            print(f"{'='*80}")
            
            # Wait for rate limit reset if not done
            if current_idx < total_repos:
                self._wait_for_rate_limit_reset()
        
        total_end_time = datetime.now()
        total_duration = total_end_time - total_start_time
        total_hours = total_duration.total_seconds() / 3600
        total_minutes = (total_duration.total_seconds() % 3600) / 60
        
        # Calculate statistics
        avg_batch_duration = sum([d.total_seconds() for d in self.batch_durations]) / len(self.batch_durations) if self.batch_durations else 0
        total_sleep_time = self.sleep_cycles * 3600  # Approximate (1 hour per sleep)
        actual_work_time = total_duration.total_seconds() - total_sleep_time
        
        # Check if cache was used
        cache_file = self._get_cache_filename(min_stars, max_stars)
        cache_used = os.path.exists(cache_file) and self.scan_duration and self.scan_duration.total_seconds() < 10
        
        # Prepare report content
        report_lines = []
        report_lines.append("="*80)
        report_lines.append("GITHUB README SCRAPER - FINAL REPORT")
        report_lines.append("="*80)
        report_lines.append(f"Generated: {total_end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        report_lines.append("⚙️  CONFIGURATION:")
        report_lines.append(f"  Star range: {MIN_STARS:,} to {MAX_STARS:,}")
        report_lines.append(f"  Minimum contributors: {MIN_CONTRIBUTORS}")
        report_lines.append(f"  README character limit: {README_CHAR_LIMIT:,}")
        report_lines.append(f"  Total tokens: {len(self.tokens)}")
        report_lines.append(f"  Scraping workers: {self.max_workers}")
        report_lines.append(f"  Parallel scan workers: {PARALLEL_SCAN_WORKERS}")
        report_lines.append(f"  Tokens per worker: {self.tokens_per_worker}")
        report_lines.append(f"  Output file: {OUTPUT_CSV}")
        report_lines.append("")
        
        report_lines.append("📊 SCRAPING STATISTICS:")
        report_lines.append(f"  Total repositories scanned: {total_repos:,}")
        report_lines.append(f"  Total repositories scraped: {current_idx:,}")
        report_lines.append(f"  Batches completed: {batch_num}")
        report_lines.append(f"  Output file: {OUTPUT_CSV}")
        report_lines.append("")
        
        report_lines.append("⏱️  TIME STATISTICS:")
        report_lines.append(f"  Started: {total_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"  Ended: {total_end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"  Total duration: {int(total_hours)} hours {int(total_minutes)} minutes")
        report_lines.append("")
        
        report_lines.append("🔍 SCANNING PHASE:")
        if self.scan_duration:
            scan_mins = int(self.scan_duration.total_seconds() / 60)
            scan_secs = int(self.scan_duration.total_seconds() % 60)
            report_lines.append(f"  Scanning duration: {scan_mins} minutes {scan_secs} seconds")
            report_lines.append(f"  Repositories found: {total_repos:,}")
            report_lines.append(f"  Parallel scan workers used: {PARALLEL_SCAN_WORKERS}")
            if cache_used:
                report_lines.append(f"  Cache: ✅ USED (loaded from cache)")
            else:
                report_lines.append(f"  Cache: ❌ NOT USED (fresh scan, saved to cache)")
        report_lines.append("")
        
        report_lines.append("🔄 BATCH DETAILS:")
        for i, duration in enumerate(self.batch_durations, 1):
            batch_mins = int(duration.total_seconds() / 60)
            batch_secs = int(duration.total_seconds() % 60)
            report_lines.append(f"  Batch {i}: {batch_mins} minutes {batch_secs} seconds")
        if self.batch_durations:
            avg_mins = int(avg_batch_duration / 60)
            avg_secs = int(avg_batch_duration % 60)
            report_lines.append(f"  Average batch duration: {avg_mins} minutes {avg_secs} seconds")
        report_lines.append("")
        
        report_lines.append("😴 RATE LIMIT SLEEP CYCLES:")
        report_lines.append(f"  Number of 1-hour sleeps: {self.sleep_cycles}")
        report_lines.append(f"  Total sleep time: ~{self.sleep_cycles} hours")
        report_lines.append(f"  Actual working time: ~{int(actual_work_time / 3600)} hours {int((actual_work_time % 3600) / 60)} minutes")
        report_lines.append("")
        
        report_lines.append("⚡ PERFORMANCE METRICS:")
        if total_repos > 0:
            report_lines.append(f"  Average time per repo: {total_duration.total_seconds() / total_repos:.2f} seconds")
            if actual_work_time > 0:
                report_lines.append(f"  Effective speed: {current_idx / (actual_work_time / 3600):.1f} repos/hour")
        report_lines.append(f"  Tokens used: {len(self.tokens)}")
        report_lines.append(f"  Workers: {self.max_workers}")
        report_lines.append(f"  API capacity: {len(self.tokens) * 5000:,} requests/hour")
        report_lines.append(f"  Theoretical max speed: {len(self.tokens) * 5000 * 0.8:.0f} repos/hour (80% efficiency)")
        report_lines.append("")
        
        report_lines.append("💡 INSIGHTS & ANALYSIS:")
        if self.sleep_cycles > 0:
            repos_per_cycle = total_repos / (self.sleep_cycles + 1)
            report_lines.append(f"  Repositories per rate limit cycle: {repos_per_cycle:.1f}")
            actual_repos_per_hour = current_idx / total_hours if total_hours > 0 else 0
            report_lines.append(f"  Actual throughput: {actual_repos_per_hour:.1f} repos/hour (including sleep)")
        
        efficiency = (actual_work_time / total_duration.total_seconds() * 100) if total_duration.total_seconds() > 0 else 0
        report_lines.append(f"  Time efficiency: {efficiency:.1f}% (working vs total time)")
        
        if self.batch_durations:
            report_lines.append(f"  Batches required: {batch_num} (rate limit cycles)")
        
        # Scanning optimization insights
        if cache_used:
            report_lines.append(f"  Scanning: ⚡ CACHED (near-instant, saved ~10-20 minutes)")
        elif PARALLEL_SCAN_WORKERS > 1:
            report_lines.append(f"  Scanning: 🚀 PARALLEL ({PARALLEL_SCAN_WORKERS} tokens, ~{PARALLEL_SCAN_WORKERS}x faster)")
        
        # Token utilization
        if len(self.tokens) > 0 and actual_work_time > 0:
            theoretical_capacity = len(self.tokens) * 5000 * (actual_work_time / 3600)
            actual_api_calls = current_idx * 3  # Approximate: search + contributors + readme
            token_utilization = (actual_api_calls / theoretical_capacity * 100) if theoretical_capacity > 0 else 0
            report_lines.append(f"  Token utilization: {token_utilization:.1f}% of total API capacity")
        
        # Performance recommendation
        if self.sleep_cycles > 2:
            report_lines.append(f"  💡 Recommendation: Consider adding more tokens to reduce sleep cycles")
        elif efficiency < 50 and self.sleep_cycles > 0:
            report_lines.append(f"  💡 Recommendation: Most time spent waiting, system is rate-limited")
        elif PARALLEL_SCAN_WORKERS < min(4, len(self.tokens)) and not cache_used:
            report_lines.append(f"  💡 Recommendation: Increase PARALLEL_SCAN_WORKERS to {min(4, len(self.tokens))} for faster scanning")
        
        report_lines.append("")
        
        report_lines.append("="*80)
        report_lines.append("END OF REPORT")
        report_lines.append("="*80)
        
        # Print report to console
        print(f"\n{'='*80}")
        print(f"✅ ALL SCRAPING COMPLETE!")
        print(f"{'='*80}\n")
        for line in report_lines:
            print(line)
        
        # Send final report to Discord
        total_time_str = f"{int(total_hours)}h {int(total_minutes)}m"
        scan_time_str = f"{int(self.scan_duration.total_seconds() / 60)}m {int(self.scan_duration.total_seconds() % 60)}s" if self.scan_duration else "N/A"
        cache_status = "✅ Used" if cache_used else "❌ Fresh scan"
        
        final_embed = {
            "title": "🎉 GitHub Scraping Complete!",
            "color": 0x0099FF,  # Blue
            "description": f"Successfully scraped **{current_idx:,}** repositories",
            "fields": [
                {"name": "📊 Total Repos", "value": f"{total_repos:,}", "inline": True},
                {"name": "✅ Scraped", "value": f"{current_idx:,}", "inline": True},
                {"name": "🔄 Batches", "value": f"{batch_num}", "inline": True},
                {"name": "⏱️ Total Time", "value": total_time_str, "inline": True},
                {"name": "🔍 Scan Time", "value": scan_time_str, "inline": True},
                {"name": "💾 Cache", "value": cache_status, "inline": True},
                {"name": "😴 Sleep Cycles", "value": f"{self.sleep_cycles}", "inline": True},
                {"name": "⚡ Workers", "value": f"{self.max_workers}", "inline": True},
                {"name": "🔑 Tokens", "value": f"{len(self.tokens)}", "inline": True},
                {"name": "📁 Output File", "value": f"`{OUTPUT_CSV}`", "inline": False}
            ],
            "footer": {"text": f"Star Range: {MIN_STARS:,} - {MAX_STARS:,}"},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add performance insights
        if actual_repos_per_hour := (current_idx / total_hours if total_hours > 0 else 0):
            final_embed["fields"].append({
                "name": "🚀 Throughput",
                "value": f"{actual_repos_per_hour:.1f} repos/hour",
                "inline": True
            })
        
        self._send_discord_message(embed=final_embed)
        
        # Save report to log file
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "scraping_report.txt")
        
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write("\n\n")  # Add spacing between reports
                for line in report_lines:
                    f.write(line + "\n")
            print(f"\n📝 Report appended to: {log_file}")
        except Exception as e:
            print(f"\n⚠️  Warning: Could not write to log file: {e}")
        
        print(f"\n{'='*80}\n")


def main():
    """Main function"""
    print(f"\n{'='*80}")
    print(f"GITHUB BATCH README SCRAPER")
    print(f"{'='*80}\n")
    print(f"Token Configuration:")
    print(f"  Total tokens loaded: {len(github_tokens)}")
    print(f"  Workers: {MAX_WORKERS}")
    print(f"  Parallel scan workers: {PARALLEL_SCAN_WORKERS}")
    print(f"  Tokens per worker: {len(github_tokens) // MAX_WORKERS}")
    print(f"  Max API points/hour: {len(github_tokens) * 5000:,}")
    print(f"  Cache directory: cache/")
    print(f"  Logs will be saved to: logs/scraping_report.txt\n")
    
    scraper = BatchReadmeScrapper(github_tokens, MAX_WORKERS)
    
    scraper.run_continuous_scraping(
        min_stars=MIN_STARS,
        max_stars=MAX_STARS
    )


if __name__ == "__main__":
    main()
