import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def process_gene_expression_data(file_path):
    """Processes gene expression data, calculates mean expression for each gene and condition, and plots a heatmap.

    Args:
    file_path: Path to the gene expression data file.
    """

    # Read the data into a Pandas DataFrame
    df = pd.read_csv(file_path, sep='\t', index_col=0)

    # Reshape the DataFrame to calculate mean expression for each gene and condition
    df_reshaped = df.copy()
    df_reshaped.columns = df_reshaped.columns.str.split('.', expand=True)
    print(df_reshaped.columns)
    df_reshaped = df_reshaped.stack(level=1).reset_index()
    df_reshaped.columns = ['gene', 'condition', 'expression']

    # Calculate mean expression for each gene and condition
    mean_df = df_reshaped.groupby(['gene', 'condition']).mean().unstack()

    # Create a heatmap
    sns.heatmap(mean_df, cmap='coolwarm')
    plt.title('Mean Gene Expression')
    plt.show()

# Example usage
file_path = 'home/static/files/transcriptome/transcriptome/Anethum.graveolens.gene_exp.tpm.txt'  # Replace with your file path
process_gene_expression_data(file_path)
