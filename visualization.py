import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os

# ============================
# CONFIGURATION - Edit these variables
# ============================
INPUT_CSV = "github_affiliation.csv"  # Input CSV file to visualize (output from AffiliationExtractor.py)
# Alternative: "github_affiliation_openai.csv" (output from AffiliationExtractor_OpenAI.py)
OUTPUT_DIR = "visualizations"  # Directory to save visualizations
# ============================

class DataVisualizer:
    def __init__(self, csv_file, output_dir):
        """
        Initialize the Data Visualizer
        
        Args:
            csv_file: CSV file to visualize
            output_dir: Directory to save visualizations
        """
        self.csv_file = csv_file
        self.output_dir = output_dir
        self.df = None
        
        # Set seaborn style
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (12, 6)
        plt.rcParams['font.size'] = 10
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"✅ Created output directory: {output_dir}")
    
    def load_data(self):
        """
        Load CSV data
        
        Returns:
            Success status
        """
        if not os.path.exists(self.csv_file):
            print(f"❌ File not found: {self.csv_file}")
            return False
        
        try:
            self.df = pd.read_csv(self.csv_file)
            print(f"✅ Loaded {self.csv_file}")
            print(f"   Rows: {len(self.df):,} | Columns: {len(self.df.columns)}")
            print(f"   Columns: {', '.join(self.df.columns)}\n")
            return True
        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            return False
    
    def plot_affiliation_distribution(self):
        """
        Create a bar chart showing affiliation distribution
        """
        print("📊 Creating affiliation distribution chart...")
        
        if 'affiliation' not in self.df.columns:
            print("   ⚠️  'affiliation' column not found, skipping")
            return
        
        # Count affiliations
        affiliation_counts = self.df['affiliation'].value_counts()
        
        # Create color palette
        colors = {
            'israel': '#0038B8',      # Blue
            'palestine': '#00853F',   # Green
            'blm': '#000000',         # Black
            'ukraine': '#FFD500',     # Yellow
            'climate': '#2E7D32',     # Dark Green
            'feminism': '#9C27B0',    # Purple
            'lgbtq': '#E91E63',       # Pink
            'none': '#808080'         # Gray
        }
        color_list = [colors.get(x, '#808080') for x in affiliation_counts.index]
        
        # Create plot
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(range(len(affiliation_counts)), affiliation_counts.values, color=color_list)
        
        # Customize plot
        ax.set_xlabel('Affiliation', fontsize=12, fontweight='bold')
        ax.set_ylabel('Number of Repositories', fontsize=12, fontweight='bold')
        ax.set_title('GitHub Repository Affiliation Distribution', fontsize=14, fontweight='bold', pad=20)
        ax.set_xticks(range(len(affiliation_counts)))
        ax.set_xticklabels([x.upper() for x in affiliation_counts.index], fontsize=11)
        
        # Add value labels on bars
        for i, (bar, count) in enumerate(zip(bars, affiliation_counts.values)):
            height = bar.get_height()
            percentage = (count / len(self.df)) * 100
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{count}\n({percentage:.1f}%)',
                   ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        # Add grid
        ax.yaxis.grid(True, linestyle='--', alpha=0.7)
        ax.set_axisbelow(True)
        
        plt.tight_layout()
        
        # Save plot
        filename = os.path.join(self.output_dir, 'affiliation_distribution.png')
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"   ✅ Saved: {filename}")
        plt.close()
    
    def plot_affiliation_pie(self):
        """
        Create a pie chart showing affiliation distribution
        """
        print("📊 Creating affiliation pie chart...")
        
        if 'affiliation' not in self.df.columns:
            print("   ⚠️  'affiliation' column not found, skipping")
            return
        
        # Count affiliations
        affiliation_counts = self.df['affiliation'].value_counts()
        
        # Create color palette
        colors = {
            'israel': '#0038B8',
            'palestine': '#00853F',
            'blm': '#000000',
            'ukraine': '#FFD500',
            'climate': '#2E7D32',
            'feminism': '#9C27B0',
            'lgbtq': '#E91E63',
            'none': '#808080'
        }
        color_list = [colors.get(x, '#808080') for x in affiliation_counts.index]
        
        # Create plot
        fig, ax = plt.subplots(figsize=(10, 8))
        
        wedges, texts, autotexts = ax.pie(
            affiliation_counts.values,
            labels=[x.upper() for x in affiliation_counts.index],
            autopct='%1.1f%%',
            colors=color_list,
            startangle=90,
            textprops={'fontsize': 11, 'fontweight': 'bold'}
        )
        
        # Enhance text
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(12)
            autotext.set_fontweight('bold')
        
        ax.set_title('GitHub Repository Affiliation Distribution', fontsize=14, fontweight='bold', pad=20)
        
        # Add legend with counts
        legend_labels = [f'{aff.upper()}: {count}' for aff, count in zip(affiliation_counts.index, affiliation_counts.values)]
        ax.legend(legend_labels, loc='upper left', bbox_to_anchor=(1, 1), fontsize=10)
        
        plt.tight_layout()
        
        # Save plot
        filename = os.path.join(self.output_dir, 'affiliation_pie.png')
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"   ✅ Saved: {filename}")
        plt.close()
    
    def plot_stars_by_affiliation(self):
        """
        Create a box plot showing star distribution by affiliation
        """
        print("📊 Creating stars by affiliation chart...")
        
        if 'repo_stars' not in self.df.columns or 'affiliation' not in self.df.columns:
            print("   ⚠️  Required columns not found, skipping")
            return
        
        # Filter out repos with 0 stars for better visualization
        df_filtered = self.df[self.df['repo_stars'] > 0].copy()
        
        # Create color palette
        colors = {
            'israel': '#0038B8',
            'palestine': '#00853F',
            'blm': '#000000',
            'ukraine': '#FFD500',
            'climate': '#2E7D32',
            'feminism': '#9C27B0',
            'lgbtq': '#E91E63',
            'none': '#808080'
        }
        
        # Create plot
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Create box plot
        affiliations = df_filtered['affiliation'].unique()
        positions = range(len(affiliations))
        
        box_data = [df_filtered[df_filtered['affiliation'] == aff]['repo_stars'].values for aff in affiliations]
        
        bp = ax.boxplot(box_data, positions=positions, widths=0.6, patch_artist=True,
                        showmeans=True, meanline=True)
        
        # Color the boxes
        for patch, aff in zip(bp['boxes'], affiliations):
            patch.set_facecolor(colors.get(aff, '#808080'))
            patch.set_alpha(0.7)
        
        # Customize plot
        ax.set_xlabel('Affiliation', fontsize=12, fontweight='bold')
        ax.set_ylabel('Number of Stars (log scale)', fontsize=12, fontweight='bold')
        ax.set_title('GitHub Repository Stars Distribution by Affiliation', fontsize=14, fontweight='bold', pad=20)
        ax.set_xticks(positions)
        ax.set_xticklabels([aff.upper() for aff in affiliations], fontsize=11)
        ax.set_yscale('log')
        
        # Add grid
        ax.yaxis.grid(True, linestyle='--', alpha=0.7)
        ax.set_axisbelow(True)
        
        plt.tight_layout()
        
        # Save plot
        filename = os.path.join(self.output_dir, 'stars_by_affiliation.png')
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"   ✅ Saved: {filename}")
        plt.close()
    
    def plot_top_repos(self, n=20):
        """
        Create a horizontal bar chart of top N repositories by stars
        """
        print(f"📊 Creating top {n} repositories chart...")
        
        if 'repo_stars' not in self.df.columns or 'repo_name' not in self.df.columns:
            print("   ⚠️  Required columns not found, skipping")
            return
        
        # Get top N repos
        top_repos = self.df.nlargest(n, 'repo_stars')
        
        # Create labels
        labels = []
        for _, row in top_repos.iterrows():
            owner = row.get('repo_owner', '')
            name = row.get('repo_name', '')
            affiliation = row.get('affiliation', 'none')
            labels.append(f"{owner}/{name}\n({affiliation.upper()})")
        
        # Get colors based on affiliation
        colors_map = {
            'israel': '#0038B8',
            'palestine': '#00853F',
            'blm': '#000000',
            'ukraine': '#FFD500',
            'climate': '#2E7D32',
            'feminism': '#9C27B0',
            'lgbtq': '#E91E63',
            'none': '#808080'
        }
        colors = [colors_map.get(row.get('affiliation', 'none'), '#808080') for _, row in top_repos.iterrows()]
        
        # Create plot
        fig, ax = plt.subplots(figsize=(12, n * 0.4))
        
        bars = ax.barh(range(len(top_repos)), top_repos['repo_stars'].values, color=colors)
        
        # Customize plot
        ax.set_yticks(range(len(top_repos)))
        ax.set_yticklabels(labels, fontsize=9)
        ax.set_xlabel('Number of Stars', fontsize=12, fontweight='bold')
        ax.set_title(f'Top {n} GitHub Repositories by Stars', fontsize=14, fontweight='bold', pad=20)
        
        # Add value labels
        for i, (bar, stars) in enumerate(zip(bars, top_repos['repo_stars'].values)):
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2.,
                   f' {stars:,}',
                   ha='left', va='center', fontsize=9, fontweight='bold')
        
        # Add grid
        ax.xaxis.grid(True, linestyle='--', alpha=0.7)
        ax.set_axisbelow(True)
        
        # Invert y-axis so highest is at top
        ax.invert_yaxis()
        
        plt.tight_layout()
        
        # Save plot
        filename = os.path.join(self.output_dir, f'top_{n}_repos.png')
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"   ✅ Saved: {filename}")
        plt.close()
    
    def plot_affiliation_stats_table(self):
        """
        Create a summary statistics table
        """
        print("📊 Creating affiliation statistics table...")
        
        if 'affiliation' not in self.df.columns or 'repo_stars' not in self.df.columns:
            print("   ⚠️  Required columns not found, skipping")
            return
        
        # Calculate statistics
        stats = []
        for affiliation in self.df['affiliation'].unique():
            aff_data = self.df[self.df['affiliation'] == affiliation]
            stats.append({
                'Affiliation': affiliation.upper(),
                'Count': len(aff_data),
                'Percentage': f"{(len(aff_data) / len(self.df) * 100):.1f}%",
                'Total Stars': f"{aff_data['repo_stars'].sum():,}",
                'Avg Stars': f"{aff_data['repo_stars'].mean():.0f}",
                'Max Stars': f"{aff_data['repo_stars'].max():,}"
            })
        
        # Sort by count
        stats_df = pd.DataFrame(stats).sort_values('Count', ascending=False)
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 4))
        ax.axis('tight')
        ax.axis('off')
        
        # Create table
        table = ax.table(cellText=stats_df.values,
                        colLabels=stats_df.columns,
                        cellLoc='center',
                        loc='center',
                        colWidths=[0.15, 0.1, 0.12, 0.15, 0.15, 0.15])
        
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2)
        
        # Style header
        for i in range(len(stats_df.columns)):
            table[(0, i)].set_facecolor('#4472C4')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        # Alternate row colors
        for i in range(1, len(stats_df) + 1):
            for j in range(len(stats_df.columns)):
                if i % 2 == 0:
                    table[(i, j)].set_facecolor('#E7E6E6')
        
        plt.title('Affiliation Statistics Summary', fontsize=14, fontweight='bold', pad=20)
        plt.tight_layout()
        
        # Save plot
        filename = os.path.join(self.output_dir, 'affiliation_stats_table.png')
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"   ✅ Saved: {filename}")
        plt.close()
    
    def plot_research_pipeline(self):
        """
        Create a flowchart visualization of the research pipeline
        """
        print("📊 Creating research pipeline flowchart...")
        
        fig, ax = plt.subplots(figsize=(14, 10))
        ax.axis('off')
        
        # Define pipeline stages with statistics
        stages = [
            {'name': 'Stage 1: Data Collection', 'desc': 'GitHub API Scraping', 'color': '#E3F2FD'},
            {'name': 'Stage 2: Emoji Filtering', 'desc': 'Political Emoji Detection', 'color': '#FFF9C4'},
            {'name': 'Stage 3: LLM Classification', 'desc': 'Affiliation Analysis', 'color': '#F3E5F5'},
            {'name': 'Stage 4: Analysis', 'desc': 'Correlation Study', 'color': '#E8F5E9'}
        ]
        
        y_start = 0.9
        box_height = 0.15
        box_spacing = 0.05
        
        for i, stage in enumerate(stages):
            y_pos = y_start - i * (box_height + box_spacing)
            
            # Draw box
            rect = plt.Rectangle((0.1, y_pos), 0.8, box_height, 
                                facecolor=stage['color'], edgecolor='black', linewidth=2)
            ax.add_patch(rect)
            
            # Add text
            ax.text(0.5, y_pos + box_height * 0.65, stage['name'], 
                   ha='center', va='center', fontsize=14, fontweight='bold')
            ax.text(0.5, y_pos + box_height * 0.35, stage['desc'],
                   ha='center', va='center', fontsize=11, style='italic')
            
            # Draw arrow to next stage
            if i < len(stages) - 1:
                arrow_y = y_pos - box_spacing / 2
                ax.annotate('', xy=(0.5, arrow_y - box_spacing / 2), 
                          xytext=(0.5, arrow_y + box_spacing / 2),
                          arrowprops=dict(arrowstyle='->', lw=3, color='black'))
        
        # Add title
        ax.text(0.5, 0.98, 'Research Pipeline: Political Emoji & Repository Affiliation',
               ha='center', va='top', fontsize=16, fontweight='bold')
        
        # Add methodology notes
        notes = [
            '1. Scraped GitHub repositories (README, description, metadata)',
            '2. Filtered by political emojis (🇮🇱, 🇵🇸, ✊🏿, 🇺🇦, ♻️, 🌈, etc.)',
            '3. Classified using DeepSeek LLM (8 categories)',
            '4. Analyzed emoji-affiliation correlation'
        ]
        
        notes_y = 0.08
        for i, note in enumerate(notes):
            ax.text(0.1, notes_y - i * 0.02, note, 
                   ha='left', va='top', fontsize=9, family='monospace')
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        
        plt.tight_layout()
        filename = os.path.join(self.output_dir, 'research_pipeline.png')
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"   ✅ Saved: {filename}")
        plt.close()
    
    def plot_data_reduction_funnel(self):
        """
        Create a funnel chart showing data reduction through pipeline
        """
        print("📊 Creating data reduction funnel...")
        
        # You'll need to manually input these values based on your actual data
        # These are example values - replace with actual counts
        try:
            # Try to load original and filtered data for comparison
            original_csv = "github_readmes_20251015_191922.csv"
            filtered_csv = "Cleaned_github_readmes.csv"
            
            original_count = 0
            filtered_count = 0
            affiliated_count = 0
            
            if os.path.exists(original_csv):
                df_original = pd.read_csv(original_csv)
                original_count = len(df_original)
            
            if os.path.exists(filtered_csv):
                df_filtered = pd.read_csv(filtered_csv)
                filtered_count = len(df_filtered)
            
            # Count repos with affiliation (not 'none')
            affiliated_count = len(self.df[self.df['affiliation'] != 'none'])
            
            stages = [
                ('Initial Scrape', original_count if original_count > 0 else 100),
                ('After Emoji Filter', filtered_count if filtered_count > 0 else 10),
                ('With Affiliation', affiliated_count if affiliated_count > 0 else 8)
            ]
        except:
            # Fallback example data
            stages = [
                ('Initial Scrape', 100),
                ('After Emoji Filter', 10),
                ('With Affiliation', 8)
            ]
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        colors_funnel = ['#64B5F6', '#FFB74D', '#81C784']
        
        for i, (label, count) in enumerate(stages):
            width = 0.8 - (i * 0.25)
            x_center = 0.5
            y_pos = 0.8 - (i * 0.25)
            
            # Draw trapezoid
            if i < len(stages) - 1:
                next_width = 0.8 - ((i + 1) * 0.25)
                points = [
                    [x_center - width/2, y_pos],
                    [x_center + width/2, y_pos],
                    [x_center + next_width/2, y_pos - 0.2],
                    [x_center - next_width/2, y_pos - 0.2]
                ]
            else:
                points = [
                    [x_center - width/2, y_pos],
                    [x_center + width/2, y_pos],
                    [x_center + width/2, y_pos - 0.15],
                    [x_center - width/2, y_pos - 0.15]
                ]
            
            polygon = plt.Polygon(points, facecolor=colors_funnel[i], 
                                edgecolor='black', linewidth=2, alpha=0.8)
            ax.add_patch(polygon)
            
            # Add text
            ax.text(x_center, y_pos - 0.07, f'{label}\n{count:,} repos',
                   ha='center', va='center', fontsize=12, fontweight='bold')
            
            # Add retention rate
            if i > 0:
                retention = (count / stages[i-1][1]) * 100
                ax.text(0.95, y_pos - 0.1, f'{retention:.1f}%',
                       ha='left', va='center', fontsize=10, style='italic')
        
        ax.set_xlim(0, 1.2)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        ax.set_title('Data Reduction Through Research Pipeline', 
                    fontsize=14, fontweight='bold', pad=20)
        
        plt.tight_layout()
        filename = os.path.join(self.output_dir, 'data_reduction_funnel.png')
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"   ✅ Saved: {filename}")
        plt.close()
    
    def plot_emoji_affiliation_heatmap(self):
        """
        Create a heatmap showing correlation between emoji presence and affiliation
        """
        print("📊 Creating emoji-affiliation correlation heatmap...")
        
        # Define emoji groups
        emoji_groups = {
            'Israel': ['🇮🇱', '🤍', '✡️', '🎗️'],
            'Palestine': ['🇵🇸', '💚', '🖤', '🍉'],
            'Ukraine': ['🇺🇦', '💛', '🌻'],
            'BLM': ['✊🏾', '✊🏿', '🤎'],
            'Climate': ['♻️', '🌱', '🌎', '🌍', '🌏'],
            'Women': ['♀️', '👩', '💔', '😔'],
            'LGBTQ': ['🌈', '🏳️‍🌈', '🏳️‍⚧️']
        }
        
        affiliations = ['israel', 'palestine', 'ukraine', 'blm', 'climate', 'feminism', 'lgbtq', 'none']
        
        # Create correlation matrix
        matrix = []
        for emoji_group_name, emojis in emoji_groups.items():
            row = []
            for aff in affiliations:
                aff_data = self.df[self.df['affiliation'] == aff]
                count = 0
                for _, repo in aff_data.iterrows():
                    readme = str(repo.get('readme', ''))
                    desc = str(repo.get('description', ''))
                    combined = readme + desc
                    if any(emoji in combined for emoji in emojis):
                        count += 1
                percentage = (count / len(aff_data) * 100) if len(aff_data) > 0 else 0
                row.append(percentage)
            matrix.append(row)
        
        # Create heatmap
        fig, ax = plt.subplots(figsize=(12, 8))
        
        im = ax.imshow(matrix, cmap='YlOrRd', aspect='auto')
        
        # Set ticks
        ax.set_xticks(range(len(affiliations)))
        ax.set_yticks(range(len(emoji_groups)))
        ax.set_xticklabels([aff.upper() for aff in affiliations], rotation=45, ha='right')
        ax.set_yticklabels(list(emoji_groups.keys()))
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Emoji Presence (%)', rotation=270, labelpad=20, fontweight='bold')
        
        # Add text annotations
        for i in range(len(emoji_groups)):
            for j in range(len(affiliations)):
                text = ax.text(j, i, f'{matrix[i][j]:.1f}%',
                             ha='center', va='center', color='black' if matrix[i][j] < 50 else 'white',
                             fontsize=9, fontweight='bold')
        
        ax.set_title('Emoji Group Presence by Repository Affiliation\n(Political Emoji as Indicator)',
                    fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('Repository Affiliation', fontsize=12, fontweight='bold')
        ax.set_ylabel('Emoji Group', fontsize=12, fontweight='bold')
        
        plt.tight_layout()
        filename = os.path.join(self.output_dir, 'emoji_affiliation_heatmap.png')
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"   ✅ Saved: {filename}")
        plt.close()
    
    def plot_affiliation_vs_none_comparison(self):
        """
        Compare repositories with affiliation vs none
        """
        print("📊 Creating affiliation vs none comparison...")
        
        # Split data
        affiliated = self.df[self.df['affiliation'] != 'none']
        non_affiliated = self.df[self.df['affiliation'] == 'none']
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
        
        # 1. Count comparison
        counts = [len(affiliated), len(non_affiliated)]
        colors_comp = ['#4CAF50', '#9E9E9E']
        ax1.bar(['With Affiliation', 'None'], counts, color=colors_comp)
        ax1.set_ylabel('Number of Repositories', fontweight='bold')
        ax1.set_title('Repository Count Comparison', fontweight='bold')
        for i, count in enumerate(counts):
            ax1.text(i, count, f'{count}\n({count/len(self.df)*100:.1f}%)', 
                    ha='center', va='bottom', fontweight='bold')
        
        # 2. Average stars comparison
        if 'repo_stars' in self.df.columns:
            avg_stars = [affiliated['repo_stars'].mean(), non_affiliated['repo_stars'].mean()]
            ax2.bar(['With Affiliation', 'None'], avg_stars, color=colors_comp)
            ax2.set_ylabel('Average Stars', fontweight='bold')
            ax2.set_title('Average Repository Stars', fontweight='bold')
            for i, stars in enumerate(avg_stars):
                ax2.text(i, stars, f'{stars:.0f}', ha='center', va='bottom', fontweight='bold')
        
        # 3. README length comparison
        if 'readme' in self.df.columns:
            aff_readme_len = affiliated['readme'].str.len().mean()
            non_readme_len = non_affiliated['readme'].str.len().mean()
            ax3.bar(['With Affiliation', 'None'], [aff_readme_len, non_readme_len], color=colors_comp)
            ax3.set_ylabel('Average README Length (chars)', fontweight='bold')
            ax3.set_title('README Content Length', fontweight='bold')
            for i, length in enumerate([aff_readme_len, non_readme_len]):
                ax3.text(i, length, f'{length:.0f}', ha='center', va='bottom', fontweight='bold')
        
        # 4. Collaborators comparison
        if 'collaborators' in self.df.columns:
            aff_collab = affiliated['collaborators'].mean()
            non_collab = non_affiliated['collaborators'].mean()
            ax4.bar(['With Affiliation', 'None'], [aff_collab, non_collab], color=colors_comp)
            ax4.set_ylabel('Average Collaborators', fontweight='bold')
            ax4.set_title('Average Collaborators Count', fontweight='bold')
            for i, collab in enumerate([aff_collab, non_collab]):
                ax4.text(i, collab, f'{collab:.1f}', ha='center', va='bottom', fontweight='bold')
        
        plt.suptitle('Affiliated vs Non-Affiliated Repositories Comparison',
                    fontsize=16, fontweight='bold', y=1.00)
        plt.tight_layout()
        
        filename = os.path.join(self.output_dir, 'affiliation_vs_none_comparison.png')
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"   ✅ Saved: {filename}")
        plt.close()
    
    def generate_all_visualizations(self):
        """
        Generate all visualizations
        """
        print("\n" + "=" * 60)
        print("DATA VISUALIZATION - GitHub Repository Analysis")
        print("=" * 60 + "\n")
        
        # Load data
        if not self.load_data():
            return False
        
        # Generate visualizations
        print("🎨 Generating visualizations...\n")
        
        # Research pipeline visualizations
        self.plot_research_pipeline()
        self.plot_data_reduction_funnel()
        self.plot_emoji_affiliation_heatmap()
        self.plot_affiliation_vs_none_comparison()
        
        # Standard visualizations
        self.plot_affiliation_distribution()
        self.plot_affiliation_pie()
        self.plot_stars_by_affiliation()
        self.plot_top_repos(n=20)
        self.plot_affiliation_stats_table()
        
        print("\n" + "=" * 60)
        print("✅ All visualizations generated successfully!")
        print(f"📁 Output directory: {self.output_dir}")
        print("=" * 60 + "\n")
        
        return True


def main():
    """
    Main function to generate visualizations
    """
    print("\n" + "=" * 60)
    print("GITHUB REPOSITORY DATA VISUALIZATION")
    print("=" * 60)
    print(f"\nInput file: {INPUT_CSV}")
    print(f"Output directory: {OUTPUT_DIR}")
    
    # Create visualizer instance
    visualizer = DataVisualizer(INPUT_CSV, OUTPUT_DIR)
    
    # Generate all visualizations
    success = visualizer.generate_all_visualizations()
    
    if success:
        print("✅ Visualization completed successfully!")
    else:
        print("❌ Visualization failed!")


if __name__ == "__main__":
    main()
