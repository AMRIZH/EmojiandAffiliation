import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.stats import chi2_contingency, spearmanr, pearsonr, normaltest, shapiro
from datetime import datetime
import os
import warnings
import sys

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

warnings.filterwarnings('ignore')

# ============================
# CONFIGURATION
# ============================
INPUT_CSV = "github_affiliation_deepseek.csv"
OUTPUT_DIR = "statistical_analysis"
REPORT_FILE = "statistical_report.txt"
# ============================

class StatisticalAnalyzer:
    def __init__(self, csv_file, output_dir):
        """
        Initialize Statistical Analyzer for GitHub data
        
        Args:
            csv_file: Path to CSV file with affiliation data
            output_dir: Directory to save analysis results
        """
        self.csv_file = csv_file
        self.output_dir = output_dir
        self.df = None
        self.report_lines = []
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Set visualization style
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (14, 8)
        plt.rcParams['font.size'] = 10
        
    def load_data(self):
        """Load and prepare data"""
        print(f"Loading data from {self.csv_file}...")
        self.df = pd.read_csv(self.csv_file)
        
        # Rename columns for consistency (handle different CSV formats)
        column_mapping = {
            'repo_stars': 'stars',
            'repo_forks': 'forks',
            'repo_size': 'size',
            'repo_created_at': 'created_at',
            'repo_contributors': 'contributors',
            'repo_collaborators': 'contributors'  # Legacy support
        }
        self.df.rename(columns=column_mapping, inplace=True)
        
        # Handle created_at from ReadmeScrapper_Batch.py (no repo_ prefix)
        # No need to rename if already 'created_at'
        
        # Detect affiliation column (support multiple naming conventions)
        affiliation_col = None
        if 'affiliation_deepseek' in self.df.columns:
            affiliation_col = 'affiliation_deepseek'
            print(f"✓ Using affiliation column: affiliation_deepseek (DeepSeek)")
        elif 'affiliation_openai' in self.df.columns:
            affiliation_col = 'affiliation_openai'
            print(f"✓ Using affiliation column: affiliation_openai (OpenAI)")
        elif 'affiliation' in self.df.columns:
            affiliation_col = 'affiliation'
            print(f"✓ Using affiliation column: affiliation (legacy)")
        else:
            print("⚠️  No affiliation column found (affiliation_deepseek, affiliation_openai, or affiliation)")
            print("   Analysis will proceed without affiliation-based filtering")
        
        # Standardize column name to 'affiliation' for compatibility
        if affiliation_col and affiliation_col != 'affiliation':
            self.df['affiliation'] = self.df[affiliation_col]
            print(f"   Standardized to 'affiliation' column for analysis")
        
        # Create a filtered dataset excluding 'none' affiliation for focused analysis
        if affiliation_col:
            self.df_affiliated = self.df[self.df['affiliation'] != 'none'].copy()
            print(f"✓ Found {len(self.df_affiliated)} repositories with political affiliations")
        else:
            self.df_affiliated = self.df.copy()
        
        # If still no stars column, try to work with what we have
        if 'stars' not in self.df.columns and 'repo_stars' in self.df.columns:
            self.df['stars'] = self.df['repo_stars']
        
        # Convert created_at to datetime if it exists
        if 'created_at' in self.df.columns:
            self.df['created_at'] = pd.to_datetime(self.df['created_at'], errors='coerce', utc=True)
            self.df['year_created'] = self.df['created_at'].dt.year
            self.df['month_created'] = self.df['created_at'].dt.month
            
            # Create repo age in years (use timezone-aware datetime)
            from datetime import timezone
            now_utc = datetime.now(timezone.utc)
            self.df['repo_age_years'] = (now_utc - self.df['created_at']).dt.days / 365.25
        
        # Create popularity score (log scale to handle skewness)
        if 'stars' in self.df.columns:
            self.df['log_stars'] = np.log1p(self.df['stars'])
        
        if 'forks' in self.df.columns:
            self.df['log_forks'] = np.log1p(self.df['forks'])
            
            # Create engagement ratio
            if 'stars' in self.df.columns:
                self.df['engagement_ratio'] = self.df['forks'] / (self.df['stars'] + 1)
        
        print(f"✓ Loaded {len(self.df)} repositories")
        print(f"✓ Columns: {', '.join(self.df.columns.tolist())}")
        self.add_report(f"\n{'='*80}")
        self.add_report(f"STATISTICAL ANALYSIS REPORT")
        self.add_report(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.add_report(f"Dataset: {self.csv_file}")
        self.add_report(f"Total Repositories: {len(self.df):,}")
        if hasattr(self, 'df_affiliated'):
            self.add_report(f"Repositories with Political Affiliation: {len(self.df_affiliated):,}")
            self.add_report(f"Repositories with 'None' Affiliation: {len(self.df[self.df['affiliation'] == 'none']):,}")
        self.add_report(f"{'='*80}\n")
        
    def add_report(self, text):
        """Add line to report"""
        self.report_lines.append(text)
        print(text)
        
    def save_report(self):
        """Save report to file"""
        report_path = os.path.join(self.output_dir, REPORT_FILE)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.report_lines))
        print(f"\n✓ Report saved to {report_path}")
        
    def descriptive_statistics(self):
        """Calculate and visualize descriptive statistics"""
        self.add_report("\n" + "="*80)
        self.add_report("1. DESCRIPTIVE STATISTICS")
        self.add_report("="*80)
        
        # Numerical columns - only use those that exist
        numeric_cols = ['stars', 'forks', 'size', 'contributors', 'repo_age_years']
        available_cols = [col for col in numeric_cols if col in self.df.columns and self.df[col].notna().any()]
        
        for col in available_cols:
            self.add_report(f"\n{col.upper()}:")
            self.add_report(f"  Mean: {self.df[col].mean():.2f}")
            self.add_report(f"  Median: {self.df[col].median():.2f}")
            self.add_report(f"  Std Dev: {self.df[col].std():.2f}")
            self.add_report(f"  Min: {self.df[col].min():.2f}")
            self.add_report(f"  Max: {self.df[col].max():.2f}")
            self.add_report(f"  Q1 (25%): {self.df[col].quantile(0.25):.2f}")
            self.add_report(f"  Q3 (75%): {self.df[col].quantile(0.75):.2f}")
            self.add_report(f"  Skewness: {self.df[col].skew():.2f}")
            self.add_report(f"  Kurtosis: {self.df[col].kurtosis():.2f}")
        
        # Affiliation distribution
        if 'affiliation' in self.df.columns:
            self.add_report("\n\nAFFILIATION DISTRIBUTION:")
            affil_counts = self.df['affiliation'].value_counts()
            for affil, count in affil_counts.items():
                pct = (count / len(self.df)) * 100
                self.add_report(f"  {affil}: {count:,} ({pct:.2f}%)")
        
        # Create visualization
        self.plot_descriptive_stats(available_cols)
        
    def plot_descriptive_stats(self, columns):
        """Plot descriptive statistics"""
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('Descriptive Statistics - Data Distributions', fontsize=16, fontweight='bold')
        
        for idx, col in enumerate(columns[:6]):
            row = idx // 3
            col_idx = idx % 3
            ax = axes[row, col_idx]
            
            # Histogram with KDE
            self.df[col].hist(bins=50, ax=ax, alpha=0.7, edgecolor='black')
            ax.set_xlabel(col.replace('_', ' ').title())
            ax.set_ylabel('Frequency')
            ax.set_title(f'Distribution of {col.replace("_", " ").title()}')
            ax.grid(True, alpha=0.3)
            
            # Add mean and median lines
            mean_val = self.df[col].mean()
            median_val = self.df[col].median()
            ax.axvline(mean_val, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_val:.1f}')
            ax.axvline(median_val, color='green', linestyle='--', linewidth=2, label=f'Median: {median_val:.1f}')
            ax.legend()
        
        # Remove empty subplots
        for idx in range(len(columns), 6):
            row = idx // 3
            col_idx = idx % 3
            fig.delaxes(axes[row, col_idx])
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, '1_descriptive_distributions.png'), dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Saved: 1_descriptive_distributions.png")
        
    def correlation_analysis(self):
        """Perform correlation analysis"""
        self.add_report("\n" + "="*80)
        self.add_report("2. CORRELATION ANALYSIS")
        self.add_report("="*80)
        
        # Select numeric columns
        numeric_cols = ['stars', 'forks', 'size', 'contributors', 'repo_age_years', 
                       'log_stars', 'log_forks', 'engagement_ratio']
        available_cols = [col for col in numeric_cols if col in self.df.columns]
        
        # Calculate correlation matrix
        corr_matrix = self.df[available_cols].corr(method='pearson')
        
        self.add_report("\nPEARSON CORRELATION MATRIX:")
        self.add_report(corr_matrix.to_string())
        
        # Find strong correlations
        self.add_report("\n\nSTRONG CORRELATIONS (|r| > 0.5):")
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_val = corr_matrix.iloc[i, j]
                if abs(corr_val) > 0.5:
                    col1 = corr_matrix.columns[i]
                    col2 = corr_matrix.columns[j]
                    self.add_report(f"  {col1} <-> {col2}: r = {corr_val:.3f}")
        
        # Calculate Spearman correlation (for non-linear relationships)
        spearman_matrix = self.df[available_cols].corr(method='spearman')
        
        self.add_report("\n\nSPEARMAN CORRELATION (Non-linear relationships):")
        self.add_report("\nTop correlations:")
        for i in range(len(spearman_matrix.columns)):
            for j in range(i+1, len(spearman_matrix.columns)):
                corr_val = spearman_matrix.iloc[i, j]
                if abs(corr_val) > 0.5:
                    col1 = spearman_matrix.columns[i]
                    col2 = spearman_matrix.columns[j]
                    self.add_report(f"  {col1} <-> {col2}: ρ = {corr_val:.3f}")
        
        # Visualize correlations
        self.plot_correlation_matrix(corr_matrix, spearman_matrix)
        self.plot_scatter_correlations(available_cols)
        
    def plot_correlation_matrix(self, pearson_corr, spearman_corr):
        """Plot correlation matrices"""
        fig, axes = plt.subplots(1, 2, figsize=(18, 8))
        
        # Pearson correlation
        sns.heatmap(pearson_corr, annot=True, fmt='.2f', cmap='coolwarm', 
                   center=0, vmin=-1, vmax=1, ax=axes[0], 
                   square=True, linewidths=1, cbar_kws={"shrink": 0.8})
        axes[0].set_title('Pearson Correlation Matrix\n(Linear Relationships)', 
                         fontsize=14, fontweight='bold')
        
        # Spearman correlation
        sns.heatmap(spearman_corr, annot=True, fmt='.2f', cmap='coolwarm', 
                   center=0, vmin=-1, vmax=1, ax=axes[1], 
                   square=True, linewidths=1, cbar_kws={"shrink": 0.8})
        axes[1].set_title('Spearman Correlation Matrix\n(Non-linear Relationships)', 
                         fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, '2_correlation_matrices.png'), dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Saved: 2_correlation_matrices.png")
        
    def plot_scatter_correlations(self, columns):
        """Plot scatter plots for key correlations"""
        key_pairs = [
            ('stars', 'forks'),
            ('stars', 'collaborators'),
            ('repo_age_years', 'stars'),
            ('log_stars', 'log_forks')
        ]
        
        available_pairs = [(c1, c2) for c1, c2 in key_pairs 
                          if c1 in columns and c2 in columns]
        
        if not available_pairs:
            return
        
        n_pairs = len(available_pairs)
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Key Correlation Scatter Plots', fontsize=16, fontweight='bold')
        
        for idx, (col1, col2) in enumerate(available_pairs[:4]):
            row = idx // 2
            col_idx = idx % 2
            ax = axes[row, col_idx]
            
            # Scatter plot with regression line
            x = self.df[col1].dropna()
            y = self.df[col2].dropna()
            
            # Handle same-length data
            common_idx = x.index.intersection(y.index)
            x = x[common_idx]
            y = y[common_idx]
            
            ax.scatter(x, y, alpha=0.5, s=20)
            
            # Add regression line
            z = np.polyfit(x, y, 1)
            p = np.poly1d(z)
            ax.plot(x, p(x), "r--", linewidth=2, label=f'y={z[0]:.2f}x+{z[1]:.2f}')
            
            # Calculate correlation
            corr, p_value = pearsonr(x, y)
            
            ax.set_xlabel(col1.replace('_', ' ').title())
            ax.set_ylabel(col2.replace('_', ' ').title())
            ax.set_title(f'{col1.title()} vs {col2.title()}\nr={corr:.3f}, p={p_value:.4f}')
            ax.legend()
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, '3_scatter_correlations.png'), dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Saved: 3_scatter_correlations.png")
        
    def distribution_analysis(self):
        """Analyze data distributions and test for normality"""
        self.add_report("\n" + "="*80)
        self.add_report("3. DISTRIBUTION ANALYSIS")
        self.add_report("="*80)
        
        numeric_cols = ['stars', 'forks', 'size', 'contributors', 'log_stars', 'log_forks']
        available_cols = [col for col in numeric_cols if col in self.df.columns]
        
        for col in available_cols:
            self.add_report(f"\n{col.upper()}:")
            
            # Shapiro-Wilk test (for n < 5000)
            if len(self.df[col].dropna()) < 5000:
                stat, p_value = shapiro(self.df[col].dropna())
                self.add_report(f"  Shapiro-Wilk Test: statistic={stat:.4f}, p-value={p_value:.4f}")
                if p_value > 0.05:
                    self.add_report(f"  → Distribution appears NORMAL (p > 0.05)")
                else:
                    self.add_report(f"  → Distribution is NOT NORMAL (p ≤ 0.05)")
            
            # D'Agostino and Pearson's test
            stat, p_value = normaltest(self.df[col].dropna())
            self.add_report(f"  D'Agostino-Pearson Test: statistic={stat:.4f}, p-value={p_value:.4f}")
            
            # Quartiles and IQR for outlier detection
            Q1 = self.df[col].quantile(0.25)
            Q3 = self.df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outliers = self.df[(self.df[col] < lower_bound) | (self.df[col] > upper_bound)]
            
            self.add_report(f"  IQR: {IQR:.2f}")
            self.add_report(f"  Outliers (beyond 1.5*IQR): {len(outliers)} ({len(outliers)/len(self.df)*100:.2f}%)")
            self.add_report(f"  Range for 'normal' values: [{lower_bound:.2f}, {upper_bound:.2f}]")
        
        # Visualize distributions
        self.plot_distribution_analysis(available_cols)
        
    def plot_distribution_analysis(self, columns):
        """Plot distribution analysis with Q-Q plots"""
        # Filter out constant columns (no variance)
        columns = [col for col in columns if self.df[col].std() > 0]
        
        if not columns:
            print("⚠ No columns with variance to plot")
            return
        
        n_cols = len(columns)
        n_rows = (n_cols + 1) // 2
        
        fig, axes = plt.subplots(n_rows, 4, figsize=(20, n_rows*4))
        fig.suptitle('Distribution Analysis - Histograms, KDE, Q-Q Plots, and Box Plots', 
                    fontsize=16, fontweight='bold')
        
        for idx, col in enumerate(columns):
            row = idx // 2
            
            # Histogram with KDE (col 0)
            ax1 = axes[row, idx%2*2] if n_rows > 1 else axes[idx%2*2]
            self.df[col].hist(bins=50, ax=ax1, alpha=0.7, edgecolor='black', density=True)
            
            # Only add KDE if there's variance
            try:
                self.df[col].plot(kind='kde', ax=ax1, color='red', linewidth=2)
            except:
                pass  # Skip KDE if it fails
            
            ax1.set_xlabel(col.replace('_', ' ').title())
            ax1.set_ylabel('Density')
            ax1.set_title(f'{col.title()} - Distribution')
            ax1.grid(True, alpha=0.3)
            
            # Q-Q Plot (col 1)
            ax2 = axes[row, idx%2*2+1] if n_rows > 1 else axes[idx%2*2+1]
            stats.probplot(self.df[col].dropna(), dist="norm", plot=ax2)
            ax2.set_title(f'{col.title()} - Q-Q Plot')
            ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, '4_distribution_analysis.png'), dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Saved: 4_distribution_analysis.png")
        
        # Box plots for outlier visualization
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('Box Plots - Outlier Detection', fontsize=16, fontweight='bold')
        
        for idx, col in enumerate(columns[:6]):
            row = idx // 3
            col_idx = idx % 3
            ax = axes[row, col_idx]
            
            self.df.boxplot(column=col, ax=ax, patch_artist=True)
            ax.set_ylabel(col.replace('_', ' ').title())
            ax.set_title(f'{col.title()} - Box Plot')
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, '5_boxplots_outliers.png'), dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Saved: 5_boxplots_outliers.png")
        
    def affiliation_comparison(self):
        """Compare metrics across affiliations"""
        if 'affiliation' not in self.df.columns:
            return
        
        self.add_report("\n" + "="*80)
        self.add_report("4. AFFILIATION COMPARISON ANALYSIS")
        self.add_report("="*80)
        
        # Group by affiliation
        numeric_cols = ['stars', 'forks', 'size', 'contributors', 'repo_age_years']
        available_cols = [col for col in numeric_cols if col in self.df.columns]
        
        grouped = self.df.groupby('affiliation')[available_cols].agg(['mean', 'median', 'std', 'count'])
        
        self.add_report("\nGROUPED STATISTICS BY AFFILIATION:")
        self.add_report(grouped.to_string())
        
        # Perform ANOVA or Kruskal-Wallis tests
        self.add_report("\n\nSTATISTICAL TESTS (Comparing Affiliations):")
        
        for col in available_cols:
            # Skip if column has no variance
            if self.df[col].std() == 0:
                self.add_report(f"\n{col.upper()}: Skipped (no variance)")
                continue
            
            groups = [group[col].dropna() for name, group in self.df.groupby('affiliation')]
            
            # Remove empty groups
            groups = [g for g in groups if len(g) > 0]
            
            if len(groups) < 2:
                continue
            
            # Kruskal-Wallis H-test (non-parametric alternative to ANOVA)
            try:
                h_stat, p_value = stats.kruskal(*groups)
                
                self.add_report(f"\n{col.upper()}:")
                self.add_report(f"  Kruskal-Wallis H-test: H={h_stat:.4f}, p-value={p_value:.4f}")
                
                if p_value < 0.05:
                    self.add_report(f"  → SIGNIFICANT difference between affiliations (p < 0.05)")
                else:
                    self.add_report(f"  → NO significant difference between affiliations (p ≥ 0.05)")
            except ValueError as e:
                self.add_report(f"\n{col.upper()}: Skipped ({str(e)})")
        
        # Visualize affiliation comparisons
        self.plot_affiliation_comparison(available_cols)
        
    def plot_affiliation_comparison(self, columns):
        """Plot comparison visualizations by affiliation"""
        # Bar plots with error bars
        n_cols = len(columns)
        fig, axes = plt.subplots((n_cols+1)//2, 2, figsize=(16, n_cols*3))
        fig.suptitle('Mean Values by Affiliation (with Std Dev)', fontsize=16, fontweight='bold')
        
        for idx, col in enumerate(columns):
            row = idx // 2
            col_idx = idx % 2
            ax = axes[row, col_idx] if n_cols > 2 else axes[col_idx]
            
            grouped_data = self.df.groupby('affiliation')[col].agg(['mean', 'std'])
            grouped_data = grouped_data.sort_values('mean', ascending=False)
            
            x = range(len(grouped_data))
            ax.bar(x, grouped_data['mean'], yerr=grouped_data['std'], 
                  capsize=5, alpha=0.7, edgecolor='black')
            ax.set_xticks(x)
            ax.set_xticklabels(grouped_data.index, rotation=45, ha='right')
            ax.set_ylabel(col.replace('_', ' ').title())
            ax.set_title(f'Mean {col.title()} by Affiliation')
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, '6_affiliation_comparison_bars.png'), dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Saved: 6_affiliation_comparison_bars.png")
        
        # Violin plots
        fig, axes = plt.subplots((n_cols+1)//2, 2, figsize=(16, n_cols*3))
        fig.suptitle('Distribution Comparison by Affiliation (Violin Plots)', fontsize=16, fontweight='bold')
        
        for idx, col in enumerate(columns):
            row = idx // 2
            col_idx = idx % 2
            ax = axes[row, col_idx] if n_cols > 2 else axes[col_idx]
            
            sns.violinplot(data=self.df, x='affiliation', y=col, ax=ax)
            ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
            ax.set_ylabel(col.replace('_', ' ').title())
            ax.set_title(f'{col.title()} Distribution by Affiliation')
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, '7_affiliation_violins.png'), dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Saved: 7_affiliation_violins.png")
        
    def temporal_analysis(self):
        """Analyze temporal patterns"""
        if 'created_at' not in self.df.columns:
            self.add_report("\n" + "="*80)
            self.add_report("5. TEMPORAL ANALYSIS")
            self.add_report("="*80)
            self.add_report("\nSkipped: No created_at data available")
            return
        
        self.add_report("\n" + "="*80)
        self.add_report("5. TEMPORAL ANALYSIS")
        self.add_report("="*80)
        
        # Yearly trends
        yearly_stats = self.df.groupby('year_created').size()
        self.add_report("\nREPOSITORIES CREATED PER YEAR:")
        for year, count in yearly_stats.items():
            self.add_report(f"  {int(year)}: {count:,} repos")
        
        # Yearly trends by affiliation
        if 'affiliation' in self.df.columns:
            yearly_affil = pd.crosstab(self.df['year_created'], self.df['affiliation'])
            self.add_report("\n\nREPOSITORIES PER YEAR BY AFFILIATION:")
            self.add_report(yearly_affil.to_string())
        
        # Visualize temporal patterns
        self.plot_temporal_analysis()
        
    def plot_temporal_analysis(self):
        """Plot temporal patterns"""
        fig, axes = plt.subplots(2, 2, figsize=(18, 12))
        fig.suptitle('Temporal Analysis', fontsize=16, fontweight='bold')
        
        # Repos created per year
        yearly_counts = self.df.groupby('year_created').size()
        axes[0, 0].plot(yearly_counts.index, yearly_counts.values, marker='o', linewidth=2)
        axes[0, 0].set_xlabel('Year')
        axes[0, 0].set_ylabel('Number of Repositories')
        axes[0, 0].set_title('Repositories Created Per Year')
        axes[0, 0].grid(True, alpha=0.3)
        
        # Cumulative repositories
        cumulative = yearly_counts.cumsum()
        axes[0, 1].plot(cumulative.index, cumulative.values, marker='o', linewidth=2, color='green')
        axes[0, 1].set_xlabel('Year')
        axes[0, 1].set_ylabel('Cumulative Repositories')
        axes[0, 1].set_title('Cumulative Repository Growth')
        axes[0, 1].grid(True, alpha=0.3)
        
        # Repos by affiliation over time
        if 'affiliation' in self.df.columns:
            yearly_affil = pd.crosstab(self.df['year_created'], self.df['affiliation'])
            yearly_affil.plot(ax=axes[1, 0], marker='o', linewidth=2)
            axes[1, 0].set_xlabel('Year')
            axes[1, 0].set_ylabel('Number of Repositories')
            axes[1, 0].set_title('Repositories by Affiliation Over Time')
            axes[1, 0].legend(title='Affiliation', bbox_to_anchor=(1.05, 1), loc='upper left')
            axes[1, 0].grid(True, alpha=0.3)
        
        # Average stars over time
        yearly_stars = self.df.groupby('year_created')['stars'].mean()
        axes[1, 1].plot(yearly_stars.index, yearly_stars.values, marker='o', linewidth=2, color='orange')
        axes[1, 1].set_xlabel('Year')
        axes[1, 1].set_ylabel('Average Stars')
        axes[1, 1].set_title('Average Repository Stars by Creation Year')
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, '8_temporal_analysis.png'), dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Saved: 8_temporal_analysis.png")
        
    def chi_square_analysis(self):
        """Perform chi-square tests for categorical associations"""
        if 'affiliation' not in self.df.columns:
            return
        
        self.add_report("\n" + "="*80)
        self.add_report("6. CHI-SQUARE TESTS (Categorical Associations)")
        self.add_report("="*80)
        
        # Create categorical variables
        self.df['stars_category'] = pd.cut(self.df['stars'], 
                                           bins=[0, 10, 100, 1000, float('inf')],
                                           labels=['Low (0-10)', 'Medium (10-100)', 
                                                  'High (100-1K)', 'Very High (>1K)'])
        
        # Create age category only if repo_age_years exists
        if 'repo_age_years' in self.df.columns:
            self.df['age_category'] = pd.cut(self.df['repo_age_years'],
                                             bins=[0, 1, 3, 5, float('inf')],
                                             labels=['New (<1yr)', 'Recent (1-3yr)', 
                                                    'Mature (3-5yr)', 'Old (>5yr)'])
        
        # Chi-square test: Affiliation vs Stars Category
        contingency_table = pd.crosstab(self.df['affiliation'], self.df['stars_category'])
        chi2, p_value, dof, expected = chi2_contingency(contingency_table)
        
        self.add_report("\nAFFILIATION vs STARS CATEGORY:")
        self.add_report(f"  Contingency Table:")
        self.add_report(contingency_table.to_string())
        self.add_report(f"\n  Chi-square statistic: {chi2:.4f}")
        self.add_report(f"  p-value: {p_value:.4f}")
        self.add_report(f"  Degrees of freedom: {dof}")
        
        if p_value < 0.05:
            self.add_report(f"  → SIGNIFICANT association (p < 0.05)")
        else:
            self.add_report(f"  → NO significant association (p ≥ 0.05)")
        
        # Chi-square test: Affiliation vs Age Category
        contingency_table2 = None
        if 'age_category' in self.df.columns:
            contingency_table2 = pd.crosstab(self.df['affiliation'], self.df['age_category'])
            chi2, p_value, dof, expected = chi2_contingency(contingency_table2)
            
            self.add_report("\n\nAFFILIATION vs REPOSITORY AGE CATEGORY:")
            self.add_report(f"  Contingency Table:")
            self.add_report(contingency_table2.to_string())
            self.add_report(f"\n  Chi-square statistic: {chi2:.4f}")
            self.add_report(f"  p-value: {p_value:.4f}")
            self.add_report(f"  Degrees of freedom: {dof}")
            
            if p_value < 0.05:
                self.add_report(f"  → SIGNIFICANT association (p < 0.05)")
            else:
                self.add_report(f"  → NO significant association (p ≥ 0.05)")
            self.plot_chi_square_heatmaps(contingency_table, contingency_table2)
        else:
            self.add_report("\n\nAFFILIATION vs REPOSITORY AGE: Skipped (no created_at data)")
            # Only plot stars category
            fig, ax = plt.subplots(1, 1, figsize=(10, 8))
            fig.suptitle('Chi-Square Analysis - Contingency Table', fontsize=16, fontweight='bold')
            sns.heatmap(contingency_table, annot=True, fmt='d', cmap='YlOrRd', ax=ax, 
                       linewidths=1, cbar_kws={"shrink": 0.8})
            ax.set_title('Affiliation vs Stars Category')
            ax.set_ylabel('Affiliation')
            ax.set_xlabel('Stars Category')
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, '9_chi_square_heatmaps.png'), dpi=300, bbox_inches='tight')
            plt.close()
            print("✓ Saved: 9_chi_square_heatmaps.png")
        
    def plot_chi_square_heatmaps(self, table1, table2):
        """Plot heatmaps for chi-square contingency tables"""
        fig, axes = plt.subplots(1, 2, figsize=(18, 8))
        fig.suptitle('Chi-Square Analysis - Contingency Tables', fontsize=16, fontweight='bold')
        
        # Affiliation vs Stars
        sns.heatmap(table1, annot=True, fmt='d', cmap='YlOrRd', ax=axes[0], 
                   linewidths=1, cbar_kws={"shrink": 0.8})
        axes[0].set_title('Affiliation vs Stars Category')
        axes[0].set_ylabel('Affiliation')
        axes[0].set_xlabel('Stars Category')
        
        # Affiliation vs Age
        sns.heatmap(table2, annot=True, fmt='d', cmap='YlGnBu', ax=axes[1], 
                   linewidths=1, cbar_kws={"shrink": 0.8})
        axes[1].set_title('Affiliation vs Repository Age')
        axes[1].set_ylabel('Affiliation')
        axes[1].set_xlabel('Age Category')
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, '9_chi_square_heatmaps.png'), dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Saved: 9_chi_square_heatmaps.png")
        
    def advanced_insights(self):
        """Generate advanced insights and summary statistics"""
        self.add_report("\n" + "="*80)
        self.add_report("7. ADVANCED INSIGHTS & KEY FINDINGS")
        self.add_report("="*80)
        
        # Top repositories
        self.add_report("\nTOP 10 MOST STARRED REPOSITORIES:")
        cols_to_show = ['repo_name', 'stars', 'affiliation']
        if 'forks' in self.df.columns:
            cols_to_show.insert(2, 'forks')
        top_repos = self.df.nlargest(10, 'stars')[cols_to_show]
        for idx, row in top_repos.iterrows():
            if 'forks' in self.df.columns:
                self.add_report(f"  {row['repo_name']}: {row['stars']:,} stars, {row['forks']:,} forks, {row['affiliation']}")
            else:
                self.add_report(f"  {row['repo_name']}: {row['stars']:,} stars, {row['affiliation']}")
        
        # Engagement analysis
        self.add_report("\n\nENGAGEMENT METRICS:")
        total_stars = self.df['stars'].sum()
        self.add_report(f"  Total Stars: {total_stars:,}")
        
        if 'forks' in self.df.columns:
            total_forks = self.df['forks'].sum()
            self.add_report(f"  Total Forks: {total_forks:,}")
        
        if 'engagement_ratio' in self.df.columns:
            avg_engagement = self.df['engagement_ratio'].mean()
            self.add_report(f"  Average Engagement Ratio (forks/stars): {avg_engagement:.4f}")
        
        # Affiliation insights
        if 'affiliation' in self.df.columns:
            self.add_report("\n\nAFFILIATION INSIGHTS:")
            agg_dict = {
                'stars': ['sum', 'mean'],
                'repo_name': 'count'
            }
            if 'forks' in self.df.columns:
                agg_dict['forks'] = ['sum', 'mean']
            
            affil_stats = self.df.groupby('affiliation').agg(agg_dict)
            self.add_report(affil_stats.to_string())
            
            # Most popular affiliation
            most_popular = self.df.groupby('affiliation')['stars'].sum().idxmax()
            most_popular_stars = self.df.groupby('affiliation')['stars'].sum().max()
            self.add_report(f"\n  Most Popular Affiliation (by total stars): {most_popular} ({most_popular_stars:,} stars)")
        
    def affiliated_only_analysis(self):
        """Deep analysis focusing only on repositories with political affiliations (excluding 'none')"""
        if not hasattr(self, 'df_affiliated') or len(self.df_affiliated) == 0:
            self.add_report("\n⚠ No affiliated repositories found. Skipping affiliated-only analysis.")
            return
        
        self.add_report("\n" + "="*80)
        self.add_report("8. AFFILIATED REPOSITORIES ANALYSIS (Excluding 'None')")
        self.add_report("="*80)
        self.add_report(f"\nAnalyzing {len(self.df_affiliated)} repositories with political affiliations...")
        
        # Affiliation distribution (excluding none)
        self.add_report("\n--- AFFILIATION DISTRIBUTION (Political Repos Only) ---")
        aff_counts = self.df_affiliated['affiliation'].value_counts()
        for aff, count in aff_counts.items():
            percentage = (count / len(self.df_affiliated)) * 100
            self.add_report(f"  {aff.upper():15s}: {count:4d} repos ({percentage:5.2f}%)")
        
        # Descriptive statistics for affiliated repos
        self.add_report("\n--- DESCRIPTIVE STATISTICS (Political Repos Only) ---")
        numeric_cols = ['stars', 'forks', 'size', 'contributors', 'repo_age_years']
        available_cols = [col for col in numeric_cols if col in self.df_affiliated.columns and self.df_affiliated[col].notna().any()]
        
        for col in available_cols:
            self.add_report(f"\n{col.upper()}:")
            self.add_report(f"  Mean:      {self.df_affiliated[col].mean():.2f}")
            self.add_report(f"  Median:    {self.df_affiliated[col].median():.2f}")
            self.add_report(f"  Std Dev:   {self.df_affiliated[col].std():.2f}")
            self.add_report(f"  Min:       {self.df_affiliated[col].min():.2f}")
            self.add_report(f"  Max:       {self.df_affiliated[col].max():.2f}")
        
        # Correlation analysis (affiliated only)
        self.add_report("\n--- CORRELATION ANALYSIS (Political Repos Only) ---")
        corr_cols = ['stars', 'forks', 'size']
        available_corr = [col for col in corr_cols if col in self.df_affiliated.columns]
        
        if len(available_corr) >= 2:
            corr_matrix = self.df_affiliated[available_corr].corr(method='pearson')
            self.add_report("\nPearson Correlation Matrix:")
            self.add_report(corr_matrix.to_string())
        
        # Top repositories (affiliated only)
        self.add_report("\n--- TOP 10 AFFILIATED REPOSITORIES BY STARS ---")
        top_cols = ['repo_name', 'stars', 'affiliation']
        if 'forks' in self.df_affiliated.columns:
            top_cols.append('forks')
        top_affiliated = self.df_affiliated.nlargest(10, 'stars')[top_cols]
        for idx, (i, row) in enumerate(top_affiliated.iterrows(), 1):
            if 'forks' in row:
                self.add_report(f"  {idx:2d}. {row['repo_name']:50s} | {row['stars']:8,.0f} ⭐ | {row['affiliation'].upper():10s} | {row['forks']:6,.0f} forks")
            else:
                self.add_report(f"  {idx:2d}. {row['repo_name']:50s} | {row['stars']:8,.0f} ⭐ | {row['affiliation'].upper():10s}")
        
        # Comparison: affiliated vs none
        self.add_report("\n--- COMPARISON: AFFILIATED vs NONE ---")
        df_none = self.df[self.df['affiliation'] == 'none']
        
        for col in available_cols:
            affiliated_mean = self.df_affiliated[col].mean()
            none_mean = df_none[col].mean()
            difference = affiliated_mean - none_mean
            pct_diff = (difference / none_mean * 100) if none_mean != 0 else 0
            
            self.add_report(f"\n{col.upper()}:")
            self.add_report(f"  Affiliated Mean: {affiliated_mean:,.2f}")
            self.add_report(f"  None Mean:       {none_mean:,.2f}")
            self.add_report(f"  Difference:      {difference:+,.2f} ({pct_diff:+.2f}%)")
            
            # Statistical test
            if self.df_affiliated[col].std() > 0 and df_none[col].std() > 0:
                from scipy.stats import mannwhitneyu
                try:
                    statistic, p_value = mannwhitneyu(self.df_affiliated[col].dropna(), 
                                                     df_none[col].dropna(),
                                                     alternative='two-sided')
                    self.add_report(f"  Mann-Whitney U p-value: {p_value:.4f}")
                    if p_value < 0.05:
                        self.add_report(f"  ✓ Significant difference (p < 0.05)")
                    else:
                        self.add_report(f"  ✗ No significant difference (p >= 0.05)")
                except:
                    pass
        
        # Visualizations for affiliated repos
        self.plot_affiliated_only_visualizations()
    
    def plot_affiliated_only_visualizations(self):
        """Create visualizations focusing on affiliated repositories only"""
        if not hasattr(self, 'df_affiliated') or len(self.df_affiliated) == 0:
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Affiliated Repositories Analysis (Excluding "None")', 
                    fontsize=16, fontweight='bold')
        
        # 1. Affiliation distribution (pie chart)
        aff_counts = self.df_affiliated['affiliation'].value_counts()
        colors_map = {
            'israel': '#0038B8',
            'palestine': '#00853F',
            'blm': '#000000',
            'ukraine': '#FFD500',
            'climate': '#2E7D32',
            'feminism': '#9C27B0',
            'lgbtq': '#E91E63'
        }
        colors = [colors_map.get(x, '#808080') for x in aff_counts.index]
        
        axes[0, 0].pie(aff_counts.values, labels=[x.upper() for x in aff_counts.index],
                      autopct='%1.1f%%', colors=colors, startangle=90)
        axes[0, 0].set_title('Political Affiliation Distribution\n(Affiliated Repos Only)', 
                           fontweight='bold')
        
        # 2. Stars distribution by affiliation (box plot)
        aff_list = self.df_affiliated['affiliation'].unique()
        star_data = [self.df_affiliated[self.df_affiliated['affiliation'] == aff]['stars'].values 
                    for aff in aff_list]
        bp = axes[0, 1].boxplot(star_data, labels=[a.upper() for a in aff_list], patch_artist=True)
        for patch, aff in zip(bp['boxes'], aff_list):
            patch.set_facecolor(colors_map.get(aff, '#808080'))
        axes[0, 1].set_ylabel('Stars (log scale)', fontweight='bold')
        axes[0, 1].set_title('Stars Distribution by Affiliation', fontweight='bold')
        axes[0, 1].set_yscale('log')
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # 3. Top 10 affiliated repos
        top_10 = self.df_affiliated.nlargest(10, 'stars')
        repo_labels = [name[:30] + '...' if len(name) > 30 else name 
                      for name in top_10['repo_name']]
        repo_colors = [colors_map.get(aff, '#808080') for aff in top_10['affiliation']]
        
        axes[1, 0].barh(range(len(top_10)), top_10['stars'].values, color=repo_colors)
        axes[1, 0].set_yticks(range(len(top_10)))
        axes[1, 0].set_yticklabels(repo_labels, fontsize=8)
        axes[1, 0].set_xlabel('Stars', fontweight='bold')
        axes[1, 0].set_title('Top 10 Affiliated Repositories', fontweight='bold')
        axes[1, 0].invert_yaxis()
        
        # 4. Comparison: Affiliated vs None
        df_none = self.df[self.df['affiliation'] == 'none']
        metrics = ['stars', 'forks', 'size']
        available_metrics = [m for m in metrics if m in self.df_affiliated.columns]
        
        if available_metrics:
            x_pos = np.arange(len(available_metrics))
            width = 0.35
            
            affiliated_means = [self.df_affiliated[m].mean() for m in available_metrics]
            none_means = [df_none[m].mean() for m in available_metrics]
            
            axes[1, 1].bar(x_pos - width/2, affiliated_means, width, 
                          label='Affiliated', color='#4CAF50')
            axes[1, 1].bar(x_pos + width/2, none_means, width, 
                          label='None', color='#9E9E9E')
            
            axes[1, 1].set_ylabel('Mean Value', fontweight='bold')
            axes[1, 1].set_title('Affiliated vs None Comparison', fontweight='bold')
            axes[1, 1].set_xticks(x_pos)
            axes[1, 1].set_xticklabels([m.upper() for m in available_metrics])
            axes[1, 1].legend()
            axes[1, 1].set_yscale('log')
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, '10_affiliated_only_analysis.png'), 
                   dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Saved: 10_affiliated_only_analysis.png")
        
    def run_full_analysis(self):
        """Run complete statistical analysis pipeline"""
        print("\n" + "="*80)
        print("STATISTICAL ANALYSIS PIPELINE")
        print("="*80 + "\n")
        
        self.load_data()
        self.descriptive_statistics()
        self.correlation_analysis()
        self.distribution_analysis()
        self.affiliation_comparison()
        
        # Conditional analyses
        if 'created_at' in self.df.columns and self.df['created_at'].notna().any():
            self.temporal_analysis()
        else:
            print("⚠ Skipping temporal analysis (no valid created_at data)")
        
        if 'affiliation' in self.df.columns:
            self.chi_square_analysis()
        else:
            print("⚠ Skipping chi-square analysis (no affiliation data)")
        
        self.advanced_insights()
        
        # NEW: Focused analysis on affiliated repositories only
        self.affiliated_only_analysis()
        
        self.save_report()
        
        print("\n" + "="*80)
        print("✓ ANALYSIS COMPLETE")
        print(f"✓ Results saved to: {self.output_dir}/")
        print(f"✓ Report saved to: {os.path.join(self.output_dir, REPORT_FILE)}")
        print("="*80 + "\n")

def main():
    """Main execution function"""
    analyzer = StatisticalAnalyzer(INPUT_CSV, OUTPUT_DIR)
    analyzer.run_full_analysis()

if __name__ == "__main__":
    main()
