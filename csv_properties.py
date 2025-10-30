import pandas as pd
import sys

# ============================
# CONFIGURATION
# ============================
CSV_FILE = "filtered_github_1000_200000.csv"  # CSV file to analyze

# ============================


def analyze_csv(csv_file):
    """
    Analyze CSV file and display key properties
    
    Args:
        csv_file: Path to CSV file
    """
    try:
        print(f"\n{'='*60}")
        print(f"CSV FILE ANALYSIS")
        print(f"{'='*60}")
        print(f"File: {csv_file}\n")
        
        # Load CSV
        print("📂 Loading CSV file...")
        df = pd.read_csv(csv_file, encoding='utf-8')
        
        print(f"✅ Successfully loaded!\n")
        
        # 1. Column names
        print(f"{'='*60}")
        print(f"1. COLUMN NAMES ({len(df.columns)} columns)")
        print(f"{'='*60}")
        for i, col in enumerate(df.columns, 1):
            print(f"   {i:2d}. {col}")
        
        # 2 & 3. Star statistics
        if 'repo_stars' in df.columns:
            print(f"\n{'='*60}")
            print(f"2-3. STAR STATISTICS")
            print(f"{'='*60}")
            max_stars = df['repo_stars'].max()
            min_stars = df['repo_stars'].min()
            avg_stars = df['repo_stars'].mean()
            median_stars = df['repo_stars'].median()
            
            print(f"   Maximum stars: {max_stars:,}")
            print(f"   Minimum stars: {min_stars:,}")
            print(f"   Average stars: {avg_stars:,.2f}")
            print(f"   Median stars:  {median_stars:,.0f}")
        else:
            print(f"\n⚠️  Column 'repo_stars' not found in CSV")
        
        # 4. Repositories with emojis (check multiple possible column names)
        emoji_col = None
        possible_emoji_cols = ['found_emojis', 'emoji_found', 'emojis']
        
        for col in possible_emoji_cols:
            if col in df.columns:
                emoji_col = col
                break
        
        if emoji_col:
            print(f"\n{'='*60}")
            print(f"4. EMOJI STATISTICS")
            print(f"{'='*60}")
            # Count repos with emojis (non-null and non-empty)
            repos_with_emojis = df[emoji_col].notna().sum()
            repos_with_emojis = repos_with_emojis - (df[emoji_col] == '').sum()
            
            print(f"   Emoji column: '{emoji_col}'")
            print(f"   Repositories with emojis: {repos_with_emojis:,}")
            print(f"   Repositories without emojis: {len(df) - repos_with_emojis:,}")
            print(f"   Percentage with emojis: {(repos_with_emojis / len(df) * 100):.2f}%")
        else:
            print(f"\n{'='*60}")
            print(f"4. EMOJI STATISTICS")
            print(f"{'='*60}")
            print(f"   ⚠️  No emoji column found (checked: {', '.join(possible_emoji_cols)})")
        
        # 5. Total repositories
        print(f"\n{'='*60}")
        print(f"5. TOTAL REPOSITORIES")
        print(f"{'='*60}")
        print(f"   Total repositories: {len(df):,}")
        
        # Additional useful statistics
        print(f"\n{'='*60}")
        print(f"ADDITIONAL STATISTICS")
        print(f"{'='*60}")
        
        # Check for is_a_fork column
        if 'is_a_fork' in df.columns:
            fork_count = df['is_a_fork'].sum()
            original_count = len(df) - fork_count
            print(f"   Forked repositories: {fork_count:,} ({(fork_count/len(df)*100):.1f}%)")
            print(f"   Original repositories: {original_count:,} ({(original_count/len(df)*100):.1f}%)")
        
        # Check for contributors
        contrib_col = 'contributors' if 'contributors' in df.columns else 'collaborators' if 'collaborators' in df.columns else None
        if contrib_col:
            max_contrib = df[contrib_col].max()
            min_contrib = df[contrib_col].min()
            avg_contrib = df[contrib_col].mean()
            print(f"   Max contributors: {max_contrib:,}")
            print(f"   Min contributors: {min_contrib:,}")
            print(f"   Avg contributors: {avg_contrib:.1f}")
        
        # Check for README
        if 'readme' in df.columns:
            repos_with_readme = df['readme'].notna().sum()
            print(f"   Repositories with README: {repos_with_readme:,} ({(repos_with_readme/len(df)*100):.1f}%)")
        
        # Check for affiliation columns
        affiliation_cols = [col for col in df.columns if 'affiliation' in col.lower()]
        if affiliation_cols:
            print(f"\n   Affiliation columns found: {', '.join(affiliation_cols)}")
            for aff_col in affiliation_cols:
                print(f"\n   Distribution for '{aff_col}':")
                value_counts = df[aff_col].value_counts()
                for value, count in value_counts.items():
                    print(f"      {value}: {count:,} ({(count/len(df)*100):.1f}%)")
        
        print(f"\n{'='*60}")
        print(f"✅ Analysis completed successfully!")
        print(f"{'='*60}\n")
        
        return True
        
    except FileNotFoundError:
        print(f"❌ Error: File not found - {csv_file}")
        print(f"   Please check the file path and try again.\n")
        return False
    except Exception as e:
        print(f"❌ Error analyzing CSV: {e}\n")
        return False


def main():
    """
    Main function
    """
    # Check if file is provided as command line argument
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        csv_file = CSV_FILE
    
    analyze_csv(csv_file)


if __name__ == "__main__":
    main()
