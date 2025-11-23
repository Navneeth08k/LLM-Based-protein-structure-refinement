import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def main():
    csv_path = "benchmark_results.csv"
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return

    df = pd.read_csv(csv_path)
    
    # Filter for Success
    df = df[df['status'] == 'Success']
    
    if df.empty:
        print("No successful results to plot.")
        return

    # Create a label combining UniProt and Target
    df['Label'] = df['uniprot_id'] + " (" + df['target'] + ")"

    # Plot 1: Improvement
    plt.figure(figsize=(12, 6))
    sns.set_theme(style="whitegrid")
    
    # Color bars based on positive/negative improvement
    colors = ['green' if x >= 0 else 'red' for x in df['improvement']]
    
    ax = sns.barplot(x='Label', y='improvement', data=df, palette=colors)
    
    plt.axhline(0, color='black', linewidth=1)
    plt.xticks(rotation=45, ha='right')
    plt.ylabel('RMSD Improvement (Å)')
    plt.title('Automated Pipeline Performance: RMSD Improvement per Target')
    plt.tight_layout()
    
    output_path = "benchmark_summary_improvement.png"
    plt.savefig(output_path)
    print(f"Saved improvement plot to {output_path}")
    
    # Plot 2: Absolute RMSD Comparison
    plt.figure(figsize=(12, 6))
    
    # Melt for grouped bar chart
    df_melted = df.melt(id_vars=['Label'], value_vars=['rmsd_original', 'rmsd_refined'], 
                        var_name='Type', value_name='RMSD')
    
    sns.barplot(x='Label', y='RMSD', hue='Type', data=df_melted, palette="muted")
    
    plt.xticks(rotation=45, ha='right')
    plt.ylabel('RMSD (Å)')
    plt.title('RMSD Comparison: Original vs Refined')
    plt.tight_layout()
    
    output_path_2 = "benchmark_summary_rmsd.png"
    plt.savefig(output_path_2)
    print(f"Saved comparison plot to {output_path_2}")

if __name__ == "__main__":
    main()
