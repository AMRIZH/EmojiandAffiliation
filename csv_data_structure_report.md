# CSV Data Structure Analysis

**Generated:** 2025-11-28 15:49:33

This report analyzes the structure and columns of the two main CSV datasets.

---

# validity_checked_affiliated_deepseek_1000_200000.csv

**Shape:** 4696 rows × 18 columns

## Column Details

| # | Column Name | Data Type | Non-Null Count | Completeness | Sample Value |
|---|-------------|-----------|----------------|--------------|-------------|
| 1 | `repo_owner` | object | 4696/4696 | 100.0% | microsoft |
| 2 | `repo_name` | object | 4696/4696 | 100.0% | AI-For-Beginners |
| 3 | `repo_stars` | int64 | 4696/4696 | 100.0% | 43318 |
| 4 | `repo_url` | object | 4696/4696 | 100.0% | https://github.com/microsoft/AI-For-Beginners |
| 5 | `description` | object | 4640/4696 | 98.8% | 12 Weeks, 24 Lessons, AI for All! |
| 6 | `contributors` | int64 | 4696/4696 | 100.0% | 64 |
| 7 | `forks` | int64 | 4696/4696 | 100.0% | 8476 |
| 8 | `language` | object | 4234/4696 | 90.2% | Jupyter Notebook |
| 9 | `owner_type` | object | 4696/4696 | 100.0% | Organization |
| 10 | `is_a_fork` | bool | 4696/4696 | 100.0% | False |
| 11 | `topics` | object | 3945/4696 | 84.0% | ai, artificial-intelligence, cnn, computer-vision,... |
| 12 | `created_at` | object | 4696/4696 | 100.0% | 2021-03-03T16:27:36Z |
| 13 | `updated_at` | object | 4696/4696 | 100.0% | 2025-10-23T13:19:28Z |
| 14 | `pushed_at` | object | 4696/4696 | 100.0% | 2025-10-23T12:49:24Z |
| 15 | `readme` | object | 4696/4696 | 100.0% | [![GitHub license](https://img.shields.io/github/l... |
| 16 | `found_emojis` | object | 4696/4696 | 100.0% | 🔥 |
| 17 | `affiliation_deepseek` | object | 4696/4696 | 100.0% | none |
| 18 | `validity` | object | 145/4696 | 3.1% | explicit |

## Data Types Summary

| Data Type | Count |
|-----------|-------|
| object | 14 |
| int64 | 3 |
| bool | 1 |

## Numeric Column Statistics

| Column | Min | Max | Mean | Median | Std Dev |
|--------|-----|-----|------|--------|---------|
| `repo_stars` | 1,000 | 193,622 | 6,061 | 2,458 | 11,798 |
| `contributors` | 1 | 7,157 | 74 | 19 | 242 |
| `forks` | 0 | 60,896 | 880 | 284 | 2,562 |

---

# 7_expression_category_labeled.csv

**Shape:** 59 rows × 19 columns

## Column Details

| # | Column Name | Data Type | Non-Null Count | Completeness | Sample Value |
|---|-------------|-----------|----------------|--------------|-------------|
| 1 | `repo_owner` | object | 59/59 | 100.0% | starship |
| 2 | `repo_name` | object | 59/59 | 100.0% | starship |
| 3 | `repo_stars` | int64 | 59/59 | 100.0% | 51811 |
| 4 | `repo_url` | object | 59/59 | 100.0% | https://github.com/starship/starship |
| 5 | `description` | object | 59/59 | 100.0% | ☄🌌️  The minimal, blazing-fast, and infinitely cus... |
| 6 | `contributors` | int64 | 59/59 | 100.0% | 637 |
| 7 | `forks` | int64 | 59/59 | 100.0% | 2266 |
| 8 | `language` | object | 56/59 | 94.9% | Rust |
| 9 | `owner_type` | object | 59/59 | 100.0% | Organization |
| 10 | `is_a_fork` | bool | 59/59 | 100.0% | False |
| 11 | `topics` | object | 55/59 | 93.2% | bash, fish, fish-prompt, fish-theme, oh-my-zsh, po... |
| 12 | `created_at` | object | 59/59 | 100.0% | 2019-04-02T03:23:12Z |
| 13 | `updated_at` | object | 59/59 | 100.0% | 2025-10-23T13:40:44Z |
| 14 | `pushed_at` | object | 59/59 | 100.0% | 2025-10-22T18:08:32Z |
| 15 | `readme` | object | 59/59 | 100.0% | <p align="center">
  <img
    width="400"
    src=... |
| 16 | `found_emojis` | object | 59/59 | 100.0% | ❤️ 🌱 |
| 17 | `affiliation_deepseek` | object | 59/59 | 100.0% | ukraine |
| 18 | `validity` | object | 59/59 | 100.0% | explicit |
| 19 | `expression_category` | object | 59/59 | 100.0% | hashtag_slogan |

## Data Types Summary

| Data Type | Count |
|-----------|-------|
| object | 15 |
| int64 | 3 |
| bool | 1 |

## Numeric Column Statistics

| Column | Min | Max | Mean | Median | Std Dev |
|--------|-----|-----|------|--------|---------|
| `repo_stars` | 1,012 | 193,622 | 9,429 | 2,864 | 26,116 |
| `contributors` | 1 | 1,013 | 113 | 30 | 194 |
| `forks` | 15 | 30,918 | 1,334 | 280 | 4,118 |

---

## File Comparison

| Metric | validity_checked_affiliated_deepseek | 7_expression_category_labeled |
|--------|-------------------------------------|-------------------------------|
| **Rows** | 4,696 | 59 |
| **Columns** | 18 | 19 |
| **Size Ratio** | 100% | 1.3% |
| **Common Columns** | 18 | 18 |
| **Additional Columns** | - | `expression_category` |

### Data Relationship

- **Source**: `validity_checked_affiliated_deepseek_1000_200000.csv` contains the full filtered dataset
- **Subset**: `7_expression_category_labeled.csv` contains only the 59 repositories that passed manual validation
- **Filter**: Repositories with `validity = 'explicit'` OR `validity = 'implicit'`
- **Enhancement**: Added `expression_category` column with manual labels

