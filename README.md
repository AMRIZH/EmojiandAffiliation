# GitHub Repository Scraper & Political Affiliation Analyzer

A Python research pipeline for analyzing political and social activism in GitHub repositories through emoji usage and LLM classification.

## 🎯 Overview

Scrape 100K+ GitHub repositories → Filter by political emojis → Classify affiliations with AI → Visualize patterns

**Key Features:**
- 🚀 Automated batch scraping (8K repos/hour with 8 tokens)
- 🔍 41 political emojis across 7 categories (Palestine/Israel, Ukraine, BLM, Climate, LGBTQ+, etc.)
- 🤖 Dual LLM support (DeepSeek or OpenAI)
- 📊 9 visualization charts
- ⚡ Auto re-scanning to bypass GitHub's 1,000 result limit

## 📊 Research Workflow

```mermaid
graph TD
    A[1. Scraping<br/>ReadmeScrapper_Batch.py] --> B[Raw Data<br/>github_readmes_batch.csv<br/>8 columns]
    B --> C[2. Filtering<br/>filtering.py]
    C --> D[Filtered Data<br/>Cleaned_github_readmes.csv<br/>+ found_emojis column]
    D --> E[3. Classification<br/>AffiliationExtractor_*.py]
    E --> F[Classified Data<br/>github_affiliation*.csv<br/>+ affiliation column]
    F --> G[4. Visualization<br/>visualization.py]
    F --> H[5. Reports<br/>AffiliationSamples.py]
    G --> I[9 Charts<br/>visualizations/]
    H --> J[Text Reports<br/>affiliated_repositories.txt]
    
    style A fill:#e1f5ff
    style C fill:#fff3e0
    style E fill:#f3e5f5
    style G fill:#e8f5e9
    style H fill:#e8f5e9
```

**Pipeline Steps:**
1. **Scrape** → Collect repo metadata + README (8K/hour)
2. **Filter** → Keep only repos with political emojis (1-5% retention)
3. **Classify** → LLM determines affiliation (8 categories)
4. **Visualize** → Generate 9 analytical charts
5. **Report** → Create text summaries

## �️ Core Components

| Script | Purpose | Key Feature |
|--------|---------|-------------|
| `ReadmeScrapper_Batch.py` | Scrape repos | 8 tokens, auto re-scan, 8K/hour |
| `filtering.py` | Filter by emojis | 41 emojis, 7 categories |
| `AffiliationExtractor_deepseek.py` | Classify (DeepSeek) | Cost-effective, prompt caching |
| `AffiliationExtractor_OpenAI.py` | Classify (OpenAI) | gpt-4o-mini, enhanced prompts |
| `visualization.py` | Create charts | 9 charts, 300 DPI |
| `AffiliationSamples.py` | Generate reports | Text summaries |

**Political Emojis (41 total):**
- 🇮🇱 🇵🇸 🍉 (Israel/Palestine) • 🇺🇦 🇷🇺 (Ukraine/Russia) • ✊🏾 ✊🏿 (BLM)
- ♻️ 🌱 (Climate) • 🌈 🏳️‍🌈 🏳️‍⚧️ (LGBTQ+) • ♀️ 💔 (Women's Rights)

**Affiliation Categories:** israel, palestine, blm, ukraine, climate, feminism, lgbtq, none

## � Quick Start

### 1. Installation

```bash
# Clone repository
git clone <your-repo-url>
cd githubscrapper

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate      # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure `.env` File

Create `.env` in project root:

```bash
# GitHub Tokens (get from https://github.com/settings/tokens)
GITHUB_TOKEN_1=github_pat_xxxxx
GITHUB_TOKEN_2=github_pat_xxxxx
# ... up to GITHUB_TOKEN_8

# LLM API Key (choose one)
deepseek_api_key=sk-xxxxx    # or
openai_api_key=sk-xxxxx
```

**Token Setup:** GitHub Settings → Developer Settings → Personal Access Tokens → Fine-grained tokens
- Permissions: Contents (Read), Metadata (Read)
- 8 tokens = 40K requests/hour

## 📖 Usage

### Step 1: Scrape Repositories

```bash
python ReadmeScrapper_Batch.py
```

**What it does:** Scrapes repos with 1K-160K stars using 8 tokens in parallel
- Output: `github_readmes_batch.csv` (8 columns: owner, name, stars, url, description, collaborators, topics, readme)
- Time: ~12-17 hours for 100K repos
- Auto re-scans when hitting GitHub's 1,000 result limit

### Step 2: Filter by Emojis

```bash
python filtering.py
```

**What it does:** Filters repos containing 41 political emojis
- Output: `Cleaned_github_readmes.csv` (+ `found_emojis` column)
- Typical retention: 1-5% of original repos

### Step 3: Classify Affiliations

```bash
# Option A: DeepSeek (cheaper)
python AffiliationExtractor_deepseek.py

# Option B: OpenAI (more accurate)
python AffiliationExtractor_OpenAI.py
```

**What it does:** Uses LLM to classify repos into 8 categories
- Output: `github_affiliation.csv` or `github_affiliation_openai.csv` (+ `affiliation` column)
- Categories: israel, palestine, blm, ukraine, climate, feminism, lgbtq, none

### Step 4: Visualize

```bash
python visualization.py
```

**What it does:** Generates 9 charts analyzing the data
- Output: `visualizations/` folder with PNG files (300 DPI)

### Step 5: Generate Reports (Optional)

```bash
python AffiliationSamples.py
```

**What it does:** Creates text summaries of affiliated repos
- Output: `affiliated_repositories.txt` and `affiliated_repositories_simple.txt`

## 📁 Project Structure

```
githubscrapper/
├── ReadmeScrapper_Batch.py           # Step 1: Scrape repos
├── filtering.py                      # Step 2: Filter by emojis
├── AffiliationExtractor_deepseek.py  # Step 3: Classify (DeepSeek)
├── AffiliationExtractor_OpenAI.py    # Step 3: Classify (OpenAI)
├── visualization.py                  # Step 4: Generate charts
├── AffiliationSamples.py             # Step 5: Text reports
├── .env                              # API keys (not in git)
├── requirements.txt                  # Dependencies
├── results/                          # Output CSVs
└── visualizations/                   # Output charts
```

## ⚡ Performance

| Tokens | Throughput | 100K Repos |
|--------|------------|------------|
| 1 token | ~1K/hour | ~100 hours |
| 8 tokens | ~8K/hour | ~12-17 hours |

## 🔧 Configuration

Edit variables at the top of each script:

**`ReadmeScrapper_Batch.py`:**
```python
MIN_STARS = 1000              # Minimum stars
MAX_STARS = 160000            # Maximum stars
REPOS_PER_HOUR = 8000         # Batch size
MAX_WORKERS = 8               # Workers (= tokens)
README_CHAR_LIMIT = 30000     # README limit
```

**Emoji List** (in `filtering.py`):

```python
# In filtering.py - Edit POLITICAL_EMOJIS list

POLITICAL_EMOJIS = [
    # Israel (4 emojis)
    "🇮🇱",      # Flag: Israel
    "🤍",       # White Heart (with blue)
    "✡️",       # Star of David
    "🎗️",       # Reminder Ribbon
    
    # Palestine (4 emojis)
    "🇵🇸",      # Flag: Palestine
    "💚",       # Green Heart
    "🖤",       # Black Heart
    "🍉",       # Watermelon (symbolic)
    
    # Ukraine/Russia (4 emojis)
    "🇺🇦",      # Flag: Ukraine
    "💛",       # Yellow Heart
    "🌻",       # Sunflower (Ukraine national)
    "🇷🇺",      # Flag: Russia
    
    # Black Lives Matter (4 emojis)
    "✊",       # Raised Fist
    "✊🏾",      # Medium-Dark Skin Tone
    "✊🏿",      # Dark Skin Tone
    "🤎",       # Brown Heart
    
    # Climate Change (6 emojis)
    "♻️",       # Recycling Symbol
    "🌱",       # Seedling
    "🌍", "🌎", "🌏",  # Globe variants
    "🔥",       # Fire (climate disaster)
    
    # Women's Rights (6 emojis)
    "♀️",       # Female Sign
    "👩",       # Woman
    "💔",       # Broken Heart (#MeToo)
    "😔",       # Pensive Face
    "🍚",       # Rice (China #MeToo: 米兔)
    "🐰",       # Rabbit (China #MeToo: 米兔)
    
    # LGBTQ+ (3 emojis)
    "🌈",       # Rainbow
    "🏳️‍🌈",    # Rainbow Flag
    "🏳️‍⚧️",    # Transgender Flag
]
```

**To add new emojis:**
1. Add emoji to `POLITICAL_EMOJIS` list
2. Add descriptive comment
3. Run filtering again on same CSV (will re-process)

**To add new categories:**
1. Add emojis to list
2. Update `AffiliationExtractor_*.py` SYSTEM_PROMPT with new category
3. Add to `valid_affiliations` list in classifier

### LLM Classification Configuration

#### DeepSeek Settings
```python
MODEL_ID = "deepseek-chat"        # Model name
TEMPERATURE = 0.0                 # Deterministic (no randomness)
MAX_TOKENS = 10                   # One-word response only
SYSTEM_PROMPT = """..."""         # Cached at class level
MAX_RETRIES = 3                   # Retry on failure
```

#### OpenAI Settings
```python
MODEL_ID = "gpt-4o-mini"          # Latest mini model
TEMPERATURE = 0.0                 # Deterministic
MAX_TOKENS = 10                   # One-word response
MAX_RETRIES = 3                   # Retry on failure
```

**Cost Comparison** (approximate):
- **DeepSeek**: $0.14 per 1M input tokens, $0.28 per 1M output
- **OpenAI gpt-4o-mini**: $0.15 per 1M input tokens, $0.60 per 1M output
- **For 10K repos**: DeepSeek ~$0.50, OpenAI ~$1.50

### Batch Processing Configuration

```python
# In ReadmeScrapper_Batch.py

MIN_STARS = 1000              # Lower = more repos (denser)
MAX_STARS = 160000            # Upper bound (adjust if needed)
REPOS_PER_HOUR = 8000         # Must match: tokens × 1000
MAX_WORKERS = 8               # Must match: number of tokens
MIN_COLLABORATORS = 0         # Set >0 to filter small projects
README_CHAR_LIMIT = 30000     # Truncate to save bandwidth
```

**Optimization Tips:**
- `MIN_COLLABORATORS = 5`: Filters out personal/small projects
- `README_CHAR_LIMIT = 10000`: Faster, sufficient for classification
- `REPOS_PER_HOUR = 6000`: More conservative, reduces API errors

## 📊 Complete Data Schema

### Pipeline Data Flow

```
github_readmes_batch.csv (8 columns)
    ↓ filtering.py
Cleaned_github_readmes.csv (9 columns = 8 + found_emojis)
    ↓ AffiliationExtractor_*.py
github_affiliation*.csv (10 columns = 9 + affiliation)
```

### 1. Scraper Output: `github_readmes_batch.csv`

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `repo_owner` | String | GitHub username/org | `microsoft` |
| `repo_name` | String | Repository name | `vscode` |
| `repo_stars` | Integer | Star count | `162000` |
| `repo_url` | String | Full GitHub URL | `https://github.com/microsoft/vscode` |
| `description` | String | Repo description | `Visual Studio Code` |
| `collaborators` | Integer | Collaborator count | `428` |
| `topics` | String | Comma-separated | `editor, electron, typescript` |
| `readme` | String | README content (30K char limit) | `# Visual Studio Code\n\n...` |

**File Size**: ~500 MB for 100K repos (depending on README length)

### 2. Filtered Output: `Cleaned_github_readmes.csv`

Same as above **PLUS**:

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `found_emojis` | String | Space-separated emojis | `🏳️‍🌈 🌈` |

**Retention Rate**: Typically 1-5% of original repos (depends on emoji prevalence)

### 3. Classification Output: `github_affiliation.csv` or `github_affiliation_openai.csv`

Same as filtered **PLUS**:

| Column | Type | Description | Possible Values |
|--------|------|-------------|-----------------|
| `affiliation` | String | LLM classification | `israel`, `palestine`, `blm`, `ukraine`, `climate`, `feminism`, `lgbtq`, `none` |

**Typical Distribution** (example from research):
- `none`: 60-80% (neutral projects)
- `climate`: 5-10% (most common activism)
- `lgbtq`: 3-7%
- `ukraine`: 2-5%
- `palestine`: 1-3%
- `israel`: 1-2%
- `blm`: 1-2%
- `feminism`: 1-2%

### Data Types & Validation

**NULL Handling:**
- `description`: Empty string if null
- `topics`: Empty string if no topics
- `readme`: Empty string if not found
- `collaborators`: 0 if fetch failed
- `found_emojis`: Empty string if no matches
- `affiliation`: Defaults to "none" on error

**Character Limits:**
- `repo_owner`: ~100 chars (GitHub limit)
- `repo_name`: ~100 chars (GitHub limit)
- `description`: ~350 chars (GitHub limit)
- `topics`: ~500 chars (varies)
- `readme`: 30,000 chars (configurable)
- `found_emojis`: ~200 chars (depends on matches)
- `affiliation`: 15 chars max

**CSV Encoding**: UTF-8 with BOM for Windows compatibility

## 🐛 Troubleshooting

### Rate Limit Errors (403)

**Symptoms:**
```
Error in Query 1: 403 - API rate limit exceeded
⚠️ API error (status 403), attempt 1/3
```

**Diagnosis:**
```powershell
# Check rate limit status
python -c "from ReadmeScrapper import ReadmeScrapper; s = ReadmeScrapper(['your_token']); s.check_rate_limit()"
```

**Solutions:**
- ✅ **Add more tokens**: Up to 8 tokens in `.env` file
- ✅ **Reduce batch size**: `REPOS_PER_HOUR = 6000` (instead of 8000)
- ✅ **Increase sleep time**: Edit `time.sleep(0.3)` → `time.sleep(0.5)`
- ✅ **Wait for reset**: Rate limits reset every hour
- ✅ **Check token permissions**: Ensure "Contents: Read" and "Metadata: Read"

**Prevention:**
- Use 8 tokens from different accounts for stability
- Monitor console output for rate limit warnings
- The script automatically retries with exponential backoff

#### 2. Missing Repositories / Incomplete Data

**Symptoms:**
```
Expected: 10,000 repos
Got: 9,000 repos
```

**Diagnosis:**
Check logs for:
```
⚠️ Hit 1,000 limit!
🔄 Re-scanning with smaller ranges...
```

**Solutions:**
- ✅ **Already handled**: Batch scraper auto re-scans!
- ✅ **Verify completion**: Check final scan summary shows all repos
- ✅ **Manual verification**: Compare `total_count` in API vs actual scraped
- ❌ **Not an issue**: If using `ReadmeScrapper_Batch.py` (automatic)

**If still missing repos:**
- Lower `MAX_STARS` to focus on specific range
- Run multiple passes with different star ranges
- Check GitHub search API status: https://www.githubstatus.com/

#### 3. CSV Encoding Issues

**Symptoms:**
```
UnicodeDecodeError: 'utf-8' codec can't decode byte
Special characters display as: �
```

**Solutions:**
- ✅ **Already handled**: All scripts use `encoding='utf-8'`
- ✅ **Open in Excel**: Use "Data → From Text/CSV" → select UTF-8
- ✅ **Python reading**: Always specify `encoding='utf-8'`
- ✅ **Fix existing CSV**: 
  ```python
  df = pd.read_csv('file.csv', encoding='utf-8', errors='ignore')
  df.to_csv('fixed.csv', encoding='utf-8', index=False)
  ```

#### 4. API Timeout Errors

**Symptoms:**
```
Timeout fetching README for owner/repo
requests.exceptions.Timeout
```

**Solutions:**
- ✅ **Increase timeout**: Edit `timeout=30` → `timeout=60` in code
- ✅ **Check internet**: Verify stable connection
- ✅ **GitHub status**: Check https://www.githubstatus.com/
- ✅ **Retry mechanism**: Script auto-retries 3 times with backoff

**Timeout locations to increase:**
```python
# In ReadmeScrapper_Batch.py
response = requests.get(url, headers=headers, timeout=60)  # Increase from 30
```

#### 5. LLM Classification Errors

**Symptoms:**
```
❌ Exception: API error (status 429)
⚠️ All retries failed, defaulting to 'none'
```

**Solutions:**

**DeepSeek:**
- ✅ Check API key in `.env`: `deepseek_api_key=sk-...`
- ✅ Verify balance: https://platform.deepseek.com/
- ✅ Rate limit: Wait if hitting quota
- ✅ Increase `time.sleep(0.5)` → `time.sleep(1.0)` between requests

**OpenAI:**
- ✅ Check API key in `.env`: `openai_api_key=sk-...`
- ✅ Verify credits: https://platform.openai.com/usage
- ✅ Model availability: Ensure `gpt-4o-mini` is accessible
- ✅ Retry with DeepSeek if OpenAI unavailable

#### 6. Empty README Content

**Symptoms:**
```
⚠️ No README content
README column is empty in CSV
```

**Causes & Solutions:**
- ✅ **No README exists**: Normal - some repos have no README
- ✅ **Binary README**: Script handles base64 decoding automatically
- ✅ **Large README**: Truncated to 30K chars (intentional)
- ✅ **Encoding issues**: Uses `errors='ignore'` to handle invalid UTF-8

**Statistics:**
- ~90-95% of repos with 5K+ stars have READMEs
- Empty READMEs are tracked and reported in summary

#### 7. Memory Issues (Large Datasets)

**Symptoms:**
```
MemoryError: Unable to allocate array
Process killed (OOM)
```

**Solutions:**
- ✅ **Reduce batch size**: `REPOS_PER_HOUR = 4000`
- ✅ **Lower README limit**: `README_CHAR_LIMIT = 10000`
- ✅ **Process in chunks**: Run multiple smaller batches
- ✅ **Close applications**: Free up RAM during execution
- ✅ **Use 64-bit Python**: Handles larger datasets

**Memory usage estimates:**
- 1K repos: ~50 MB RAM
- 10K repos: ~500 MB RAM
- 100K repos: ~5 GB RAM (with 30K char READMEs)

#### 8. Visualization Errors

**Symptoms:**
```
KeyError: 'affiliation'
FileNotFoundError: No such file or directory
```

**Solutions:**
- ✅ **Verify input file**: Check `INPUT_CSV` matches actual filename
- ✅ **Check columns**: Ensure CSV has required columns
- ✅ **Install matplotlib**: `pip install matplotlib seaborn`
- ✅ **Create output dir**: `mkdir visualizations` (auto-created normally)

**Required columns for visualization:**
- `repo_owner`, `repo_name`, `repo_stars`, `repo_url`
- `affiliation` (for affiliation charts)
- Optional: `collaborators`, `readme`, `description`

#### 9. .env File Not Loaded

**Symptoms:**
```
ValueError: No GitHub tokens found!
❌ Error: DeepSeek API key not found
```

**Solutions:**
- ✅ **File location**: `.env` must be in project root (same folder as scripts)
- ✅ **File name**: Exactly `.env` (not `env.txt` or `.env.txt`)
- ✅ **No quotes**: Keys should not have quotes: `GITHUB_TOKEN_1=token_value`
- ✅ **Install python-dotenv**: `pip install python-dotenv`
- ✅ **Test loading**:
  ```python
  from dotenv import load_dotenv
  import os
  load_dotenv()
  print(os.getenv('GITHUB_TOKEN_1'))  # Should print token
  ```

#### 10. Windows-Specific Issues

**PowerShell Execution Policy:**
```powershell
# If you get "cannot be loaded because running scripts is disabled"
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Long Path Issues:**
```powershell
# Enable long paths in Windows 10/11
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```

**CSV Opening in Excel:**
- Use "Data → From Text/CSV" with UTF-8 encoding
- OR use LibreOffice Calc (better Unicode support)

**Most common fix:** Add more tokens to `.env` file

## 📝 Research Applications

- 🌍 Study political/social movements in open source communities
- 📈 Analyze emoji usage as political indicators
- 🔍 Measure activism correlation with repository metrics
- 📊 Track temporal trends of political engagement in tech

## 🤝 Contributing

This is an active research project. **Contributions welcome!**

Fork, create feature branch, and open PR. Priority areas: more emojis, better LLM prompts, new visualizations. Follow PEP 8.

## ⚠️ Ethical Considerations

- Uses **public data only**, respects GitHub ToS and rate limits
- For **academic research** - not for profiling or surveillance
- **Limitations**: LLM biases, emoji ambiguity, missing cultural context
- Obtain IRB approval if required, cite appropriately in publications

## 📄 License

MIT License. Uses GitHub API, DeepSeek/OpenAI LLMs, pandas, matplotlib, seaborn.



---

**Version**: 3.0 | **Python**: 3.7+ | **Status**: Production-Ready

