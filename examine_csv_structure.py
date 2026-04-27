import pandas as pd

def examine_csv_structure(filename, title, output_file):
    try:
        df = pd.read_csv(filename)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# {title}\n\n")
            f.write(f"**Shape:** {df.shape[0]} rows × {df.shape[1]} columns\n\n")
            
            # Column details table
            f.write("## Column Details\n\n")
            f.write("| # | Column Name | Data Type | Non-Null Count | Completeness | Sample Value |\n")
            f.write("|---|-------------|-----------|----------------|--------------|-------------|\n")
            
            for i, col in enumerate(df.columns, 1):
                dtype = str(df[col].dtype)
                non_null = df[col].count()
                completeness = f"{non_null/len(df)*100:.1f}%"
                
                # Sample values (first non-null value)
                sample = "N/A"
                for val in df[col].dropna():
                    if pd.notna(val):
                        sample = str(val)[:50]  # Truncate long values
                        if len(str(val)) > 50:
                            sample += "..."
                        # Escape pipe characters for markdown
                        sample = sample.replace('|', '\\|')
                        break
                
                f.write(f"| {i} | `{col}` | {dtype} | {non_null}/{len(df)} | {completeness} | {sample} |\n")
            
            # Data types summary
            f.write(f"\n## Data Types Summary\n\n")
            f.write("| Data Type | Count |\n")
            f.write("|-----------|-------|\n")
            dtype_counts = df.dtypes.value_counts()
            for dtype, count in dtype_counts.items():
                f.write(f"| {dtype} | {count} |\n")
                
            # Basic statistics for numeric columns
            numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
            if len(numeric_cols) > 0:
                f.write(f"\n## Numeric Column Statistics\n\n")
                f.write("| Column | Min | Max | Mean | Median | Std Dev |\n")
                f.write("|--------|-----|-----|------|--------|---------|\n")
                for col in numeric_cols:
                    stats = df[col].describe()
                    f.write(f"| `{col}` | {stats['min']:,.0f} | {stats['max']:,.0f} | {stats['mean']:,.0f} | {stats['50%']:,.0f} | {stats['std']:,.0f} |\n")
            
            f.write(f"\n---\n\n")
        
        print(f"✅ Generated markdown report: {output_file}")
        
    except Exception as e:
        print(f"❌ Error reading {filename}: {e}")

def generate_combined_report():
    """Generate a combined markdown report for both CSV files"""
    output_file = 'csv_data_structure_report.md'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# CSV Data Structure Analysis\n\n")
        f.write(f"**Generated:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("This report analyzes the structure and columns of the two main CSV datasets.\n\n")
        f.write("---\n\n")
    
    # Examine first CSV
    examine_csv_structure('FinalDataset/validity_checked_affiliated_deepseek_1000_200000.csv', 
                         'validity_checked_affiliated_deepseek_1000_200000.csv',
                         'temp1.md')
    
    # Examine second CSV  
    examine_csv_structure('FinalDataset/7_expression_category_labeled.csv',
                         '7_expression_category_labeled.csv', 
                         'temp2.md')
    
    # Combine reports
    with open(output_file, 'a', encoding='utf-8') as f:
        # Add first file content
        with open('temp1.md', 'r', encoding='utf-8') as temp:
            f.write(temp.read())
        
        # Add second file content
        with open('temp2.md', 'r', encoding='utf-8') as temp:
            f.write(temp.read())
        
        # Add comparison section
        f.write("## File Comparison\n\n")
        
        df1 = pd.read_csv('FinalDataset/validity_checked_affiliated_deepseek_1000_200000.csv')
        df2 = pd.read_csv('FinalDataset/7_expression_category_labeled.csv')
        
        f.write("| Metric | validity_checked_affiliated_deepseek | 7_expression_category_labeled |\n")
        f.write("|--------|-------------------------------------|-------------------------------|\n")
        f.write(f"| **Rows** | {len(df1):,} | {len(df2):,} |\n")
        f.write(f"| **Columns** | {len(df1.columns)} | {len(df2.columns)} |\n")
        f.write(f"| **Size Ratio** | 100% | {len(df2)/len(df1)*100:.1f}% |\n")
        
        # Show which columns are different
        cols1 = set(df1.columns)
        cols2 = set(df2.columns)
        common_cols = cols1.intersection(cols2)
        unique_to_1 = cols1 - cols2
        unique_to_2 = cols2 - cols1
        
        f.write(f"| **Common Columns** | {len(common_cols)} | {len(common_cols)} |\n")
        if unique_to_2:
            f.write(f"| **Additional Columns** | - | `{', '.join(unique_to_2)}` |\n")
        
        f.write(f"\n### Data Relationship\n\n")
        f.write(f"- **Source**: `validity_checked_affiliated_deepseek_1000_200000.csv` contains the full filtered dataset\n")
        f.write(f"- **Subset**: `7_expression_category_labeled.csv` contains only the {len(df2)} repositories that passed manual validation\n")
        f.write(f"- **Filter**: Repositories with `validity = 'explicit'` OR `validity = 'implicit'`\n")
        f.write(f"- **Enhancement**: Added `expression_category` column with manual labels\n\n")
    
    # Clean up temp files
    import os
    try:
        os.remove('temp1.md')
        os.remove('temp2.md')
    except:
        pass
    
    print(f"✅ Combined report generated: {output_file}")

# Generate the combined markdown report
generate_combined_report()