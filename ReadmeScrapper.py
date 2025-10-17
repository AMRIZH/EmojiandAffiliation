import requests
import csv
import time
import base64
from datetime import datetime
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
MAX_STARS = 120000  # Maximum number of stars (set very high to include all)
MAX_REPOS = 100000   # Maximum number of repositories to scrape
MIN_COLLABORATORS = 0  # Minimum number of collaborators (0 = no minimum)
README_CHAR_LIMIT = 10000  # Maximum number of characters to keep from README (None = no limit)
MAX_WORKERS = 6  # Number of parallel threads for searching (10 recommended with multiple tokens)

# Load GitHub tokens from environment variables
github_tokens = []
for i in range(1, 9):  # Load up to 8 tokens
    token = os.getenv(f'GITHUB_TOKEN_{i}')
    if token:
        github_tokens.append(token)

if not github_tokens:
    raise ValueError("No GitHub tokens found! Please set GITHUB_TOKEN_1, GITHUB_TOKEN_2, etc. in .env file")

github_token = github_tokens[0]  # Primary token for compatibility
# ============================

class ReadmeScrapper:
    def __init__(self, github_tokens):
        """
        Initialize the README scrapper with multiple tokens
        
        Args:
            github_tokens: List of GitHub personal access tokens for distributed rate limiting
        """
        self.base_url = "https://api.github.com"
        
        # Support both single token and list of tokens
        if isinstance(github_tokens, str):
            github_tokens = [github_tokens]
        
        self.tokens = github_tokens
        
        # Create headers for each token
        self.all_headers = []
        for token in self.tokens:
            headers = {
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28"
            }
            if token:
                headers["Authorization"] = f"Bearer {token}"
            self.all_headers.append(headers)
        
        # Default headers (primary token)
        self.headers = self.all_headers[0] if self.all_headers else {}
        
        # Thread locks for parallel execution
        self.print_lock = threading.Lock()
        self.repos_lock = threading.Lock()
    
    def get_headers_for_worker(self, worker_id):
        """
        Get headers with token assigned to specific worker
        
        Args:
            worker_id: Worker ID (0-based)
            
        Returns:
            Headers dictionary with assigned token
        """
        token_idx = worker_id % len(self.all_headers)
        return self.all_headers[token_idx]
    
    def check_rate_limit(self):
        """
        Check current rate limit status
        
        Returns:
            Dictionary with rate limit information
        """
        url = f"{self.base_url}/rate_limit"
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                core = data['resources']['core']
                search = data['resources']['search']
                print("\n=== Rate Limit Status ===")
                print(f"Core API: {core['remaining']}/{core['limit']} remaining")
                print(f"Search API: {search['remaining']}/{search['limit']} remaining")
                print(f"Resets at: {datetime.fromtimestamp(core['reset']).strftime('%Y-%m-%d %H:%M:%S')}")
                
                if core['limit'] == 60:
                    print("⚠️  WARNING: Using unauthenticated rate limit (60/hour)")
                    print("   Your token may not be working properly!")
                elif core['limit'] >= 5000:
                    print("✅ Authenticated: Using enhanced rate limit (5000/hour)")
                
                return data
            else:
                print(f"Error checking rate limit: {response.status_code}")
                return None
        except Exception as e:
            print(f"Exception checking rate limit: {e}")
            return None
    
    def search_repositories(self, min_stars=5000, max_stars=1000000, max_repos=500):
        """
        Search for repositories with stars between min_stars and max_stars (PARALLEL VERSION)
        
        Args:
            min_stars: Minimum number of stars (default: 5000)
            max_stars: Maximum number of stars (default: 1000000)
            max_repos: Maximum number of repositories to fetch (default: 500)
            
        Returns:
            List of repository dictionaries
        """
        all_repos = []
        
        print(f"\nSearching for repositories with {min_stars:,} to {max_stars:,} stars...")
        print(f"Target: {max_repos} repositories")
        print(f"Using {MAX_WORKERS} parallel workers for faster scraping!\n")
        
        # GitHub API limits to 1000 results per query
        if max_repos <= 1000:
            # Single query is enough
            repos = self._search_single_range(min_stars, max_stars, max_repos, 1, 1)
            all_repos.extend(repos)
        else:
            # Need multiple queries - split the star range and run in parallel
            # Number of chunks = number of tokens to ensure equal distribution
            num_chunks = max(len(self.tokens), min(MAX_WORKERS, (max_repos + 999) // 1000))
            star_ranges = self._create_star_ranges(min_stars, max_stars, num_chunks)
            
            # Use ThreadPoolExecutor for parallel execution
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                # Submit all search tasks
                future_to_range = {}
                for idx, (range_min, range_max) in enumerate(star_ranges, 1):
                    remaining = max_repos - len(all_repos)
                    if remaining <= 0:
                        break
                    
                    fetch_count = min(remaining, 1000)
                    # Assign token to worker based on worker ID
                    worker_headers = self.get_headers_for_worker(idx - 1)
                    future = executor.submit(
                        self._search_single_range,
                        range_min, range_max, fetch_count, idx, len(star_ranges), worker_headers
                    )
                    future_to_range[future] = (range_min, range_max, idx)
                
                # Collect results as they complete
                for future in as_completed(future_to_range):
                    range_min, range_max, query_num = future_to_range[future]
                    try:
                        repos = future.result()
                        
                        # Thread-safe update of all_repos
                        with self.repos_lock:
                            # Remove duplicates
                            existing_urls = {r['html_url'] for r in all_repos}
                            new_repos = [r for r in repos if r['html_url'] not in existing_urls]
                            all_repos.extend(new_repos)
                            
                            with self.print_lock:
                                print(f"✅ Query {query_num} complete: Stars {range_min:,}-{range_max:,} ({len(repos)} repos)")
                                print(f"   Total unique repos: {len(all_repos)}/{max_repos}\n")
                    
                    except Exception as e:
                        with self.print_lock:
                            print(f"❌ Query {query_num} failed (Stars {range_min:,}-{range_max:,}): {e}\n")
        
        return all_repos[:max_repos]
    
    def _create_star_ranges(self, min_stars, max_stars, num_chunks):
        """
        Create star ranges for splitting queries
        
        Args:
            min_stars: Minimum stars
            max_stars: Maximum stars
            num_chunks: Number of chunks to create
            
        Returns:
            List of (min, max) tuples
        """
        ranges = []
        total_range = max_stars - min_stars
        chunk_size = total_range // num_chunks
        
        for i in range(num_chunks):
            range_min = min_stars + (i * chunk_size)
            range_max = min_stars + ((i + 1) * chunk_size) if i < num_chunks - 1 else max_stars
            ranges.append((range_min, range_max))
        
        # Return in descending order (highest stars first)
        return list(reversed(ranges))
    
    def _search_single_range(self, min_stars, max_stars, max_repos, query_num=1, total_queries=1, worker_headers=None):
        """
        Search for repositories in a single star range (limited to 1000 results)
        Thread-safe version for parallel execution with dedicated token per worker
        
        Args:
            min_stars: Minimum number of stars
            max_stars: Maximum number of stars
            max_repos: Maximum number of repositories to fetch (max 1000)
            query_num: Current query number (for logging)
            total_queries: Total number of queries (for logging)
            worker_headers: Headers with token assigned to this worker
            
        Returns:
            List of repository dictionaries
        """
        repos = []
        per_page = 100  # GitHub API max per page
        page = 1
        max_repos = min(max_repos, 1000)  # GitHub API hard limit
        
        # Use worker-specific headers or default
        headers = worker_headers if worker_headers else self.headers
        token_num = ((query_num - 1) % len(self.tokens)) + 1
        
        with self.print_lock:
            print(f"🔍 Query {query_num}/{total_queries} [Token {token_num}] started: Stars {min_stars:,} to {max_stars:,}")
        
        while len(repos) < max_repos:
            url = f"{self.base_url}/search/repositories"
            params = {
                "q": f"stars:{min_stars}..{max_stars}",
                "sort": "stars",
                "order": "desc",
                "per_page": per_page,
                "page": page
            }
            
            try:
                response = requests.get(url, headers=headers, params=params, timeout=30)
                
                if response.status_code != 200:
                    error_msg = response.json().get('message', 'Unknown error') if response.text else 'Unknown error'
                    with self.print_lock:
                        print(f"Error in Query {query_num}: {response.status_code} - {error_msg}")
                        if response.status_code == 403:
                            print("Rate limit may be exceeded. Check your rate limit status.")
                    break
                
                data = response.json()
                items = data.get("items", [])
                total_count = data.get("total_count", 0)
                
                if not items:
                    with self.print_lock:
                        print(f"Query {query_num}: No more repositories found. (Total available: {total_count})")
                    break
                
                repos.extend(items[:max_repos - len(repos)])
                with self.print_lock:
                    print(f"Query {query_num}: Fetched {len(repos)}/{min(max_repos, total_count)} repos...")
                
                if len(repos) >= max_repos or len(repos) >= total_count:
                    break
                
                page += 1
                
                # GitHub allows max 10 pages (1000 results)
                if page > 10:
                    with self.print_lock:
                        print(f"Query {query_num}: Reached GitHub's 1,000 result limit.")
                    break
                
                time.sleep(0.8)  # Rate limiting for search API (optimized for multiple tokens)
                
            except requests.exceptions.Timeout:
                with self.print_lock:
                    print(f"Query {query_num}: Timeout on page {page}. Retrying...")
                time.sleep(5)
                continue
            except Exception as e:
                with self.print_lock:
                    print(f"Query {query_num}: Exception while searching: {e}")
                break
        
        return repos[:max_repos]
    
    def get_readme(self, owner, repo, char_limit=None):
        """
        Get README content for a specific repository
        
        Args:
            owner: Repository owner
            repo: Repository name
            char_limit: Maximum characters to fetch (None = no limit)
            
        Returns:
            README content as string, or None if not found
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/readme"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                # README content is base64 encoded
                content = data.get('content', '')
                if content:
                    # Decode base64 content
                    try:
                        decoded_content = base64.b64decode(content).decode('utf-8')
                        # Truncate early to save memory and processing
                        if char_limit is not None and len(decoded_content) > char_limit:
                            decoded_content = decoded_content[:char_limit]
                        return decoded_content
                    except Exception as e:
                        print(f"  Error decoding README: {e}")
                        return None
                return None
            elif response.status_code == 404:
                print(f"  No README found for {owner}/{repo}")
                return None
            elif response.status_code == 403:
                print(f"  Rate limit exceeded for {owner}/{repo}")
                return None
            else:
                print(f"  Error fetching README for {owner}/{repo}: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            print(f"  Timeout fetching README for {owner}/{repo}")
            return None
        except Exception as e:
            print(f"  Exception fetching README for {owner}/{repo}: {e}")
            return None
    
    def get_collaborators_count(self, owner, repo):
        """
        Get the number of collaborators for a repository
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Number of collaborators, or 0 if unable to fetch
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/collaborators"
        
        try:
            response = requests.get(url, headers=self.headers, params={'per_page': 1}, timeout=30)
            
            if response.status_code == 200:
                # Get total count from Link header if available
                link_header = response.headers.get('Link', '')
                if 'last' in link_header:
                    # Extract the last page number which gives us the total count
                    import re
                    match = re.search(r'page=(\d+)>; rel="last"', link_header)
                    if match:
                        return int(match.group(1))
                # If no pagination, count the items in response
                return len(response.json())
            elif response.status_code == 404:
                print(f"  Collaborators info not found for {owner}/{repo}")
                return 0
            elif response.status_code == 403:
                print(f"  Rate limit exceeded for collaborators {owner}/{repo}")
                return 0
            else:
                print(f"  Error fetching collaborators for {owner}/{repo}: {response.status_code}")
                return 0
                
        except requests.exceptions.Timeout:
            print(f"  Timeout fetching collaborators for {owner}/{repo}")
            return 0
        except Exception as e:
            print(f"  Exception fetching collaborators for {owner}/{repo}: {e}")
            return 0
    
    def scrape_repositories_readmes(self, min_stars=5000, max_stars=1000000, max_repos=500, min_collaborators=0):
        """
        Main function to scrape repositories and their READMEs
        
        Args:
            min_stars: Minimum number of stars
            max_stars: Maximum number of stars
            max_repos: Maximum number of repositories to scrape
            min_collaborators: Minimum number of collaborators (default: 0)
            
        Returns:
            List of repository data dictionaries with README content
        """
        all_repo_data = []
        
        # Step 1: Get repositories
        repositories = self.search_repositories(min_stars, max_stars, max_repos)
        print(f"\nFound {len(repositories)} repositories")
        print("=" * 60)
        
        # Step 2: Get README for each repository
        for idx, repo in enumerate(repositories, 1):
            owner = repo["owner"]["login"]
            repo_name = repo["name"]
            stars = repo["stargazers_count"]
            repo_url = repo["html_url"]
            description = repo.get("description", "") or ""  # Repository description
            topics = ", ".join(repo.get("topics", []))  # Join topics as comma-separated string
            
            print(f"\n[{idx}/{len(repositories)}] Processing {owner}/{repo_name} ({stars:,} stars)...")
            if topics:
                print(f"  Topics: {topics}")
            if description:
                print(f"  Description: {description[:100]}..." if len(description) > 100 else f"  Description: {description}")
            
            # Get collaborators count only if minimum is set
            if min_collaborators > 0:
                collaborators_count = self.get_collaborators_count(owner, repo_name)
                print(f"  Collaborators: {collaborators_count}")
                
                # Filter by minimum collaborators
                if collaborators_count < min_collaborators:
                    print(f"  ⚠️  Skipping: {collaborators_count} collaborators < {min_collaborators} minimum")
                    continue
            else:
                # Skip collaborator check to save API calls
                collaborators_count = 0
            
            # Get README content with character limit to reduce API usage
            readme_content = self.get_readme(owner, repo_name, char_limit=README_CHAR_LIMIT)
            
            if readme_content:
                print(f"  ✅ README fetched ({len(readme_content):,} characters)")
            else:
                print(f"  ⚠️  No README content")
                readme_content = ""  # Empty string if no README
            
            repo_data = {
                "repo_owner": owner,
                "repo_name": repo_name,
                "repo_stars": stars,
                "repo_url": repo_url,
                "description": description,
                "collaborators": collaborators_count,
                "topics": topics,
                "readme": readme_content
            }
            all_repo_data.append(repo_data)
            
            # Rate limiting - optimized for multiple tokens
            time.sleep(0.5)
        
        return all_repo_data
    
    def save_to_csv(self, repo_data, filename=None):
        """
        Save repository data with README to CSV file
        
        Args:
            repo_data: List of repository data dictionaries
            filename: Output filename (default: github_readmes_TIMESTAMP.csv)
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"github_readmes_{timestamp}.csv"
        
        if not repo_data:
            print("No data to save")
            return
        
        fieldnames = ["repo_owner", "repo_name", "repo_stars", "repo_url", "description", "collaborators", "topics", "readme"]
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(repo_data)
            
            print("\n" + "=" * 60)
            print(f"✅ Data saved to {filename}")
            print(f"📊 Total repositories scraped: {len(repo_data)}")
            
            # Statistics
            repos_with_readme = sum(1 for r in repo_data if r['readme'])
            print(f"📝 Repositories with README: {repos_with_readme}/{len(repo_data)}")
            
        except Exception as e:
            print(f"Error saving to CSV: {e}")


def main():
    """
    Main function to run the README scraper
    """
    # Use multiple github_tokens for distributed rate limiting
    print(f"Using {len(github_tokens)} GitHub tokens for distributed scraping...\n")
    print(f"Total rate limit: {len(github_tokens) * 5000} requests/hour\n")
    
    # Initialize scraper with all tokens
    scraper = ReadmeScrapper(github_tokens)
    
    # Check rate limit to verify authentication
    scraper.check_rate_limit()
    
    # Scrape repositories and READMEs
    # Use the configuration variables from the top of the file
    print("\n" + "=" * 60)
    print(f"CONFIGURATION:")
    print(f"  Minimum Stars: {MIN_STARS:,}")
    print(f"  Maximum Stars: {MAX_STARS:,}")
    print(f"  Maximum Repositories: {MAX_REPOS}")
    print(f"  Minimum Collaborators: {MIN_COLLABORATORS}")
    print("=" * 60)
    
    repo_data = scraper.scrape_repositories_readmes(
        min_stars=MIN_STARS,
        max_stars=MAX_STARS,
        max_repos=MAX_REPOS,
        min_collaborators=MIN_COLLABORATORS
    )
    
    # Save to CSV
    scraper.save_to_csv(repo_data)
    
    print("\n✅ Scraping completed!")


if __name__ == "__main__":
    main()
