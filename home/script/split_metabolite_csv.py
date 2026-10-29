import pandas as pd
import os

# --------------------------
# Config
# --------------------------
INPUT_CSV = "/mnt/d/Coding/Web/apiaceae/home/script/metabolites.csv"
SMILE_SOURCE = "/mnt/d/Coding/Web/apiaceae/home/script/metabolite_data_wangxujie.xlsx"
OUTPUT_INFO = "/mnt/d/Coding/Web/apiaceae/home/script/metabolite_info.csv"
OUTPUT_EXPRESSION = "/mnt/d/Coding/Web/apiaceae/home/script/metabolite_expression.csv"

# --------------------------
# Run split
# --------------------------
def main():
    # Read source data
    df = pd.read_csv(INPUT_CSV, encoding="utf-8-sig")
    
    # Read SMILE data from Excel
    df_smile = pd.read_excel(SMILE_SOURCE)
    
    # Identify the PubChem CID column in Excel file (adjust if column name differs)
    # Common possibilities: "PubChem CID", "PubChem_CID", "CID", "pubChem_cid"
    pubchem_col_excel = None
    for col in df_smile.columns:
        if "pubchem" in col.lower() or "cid" in col.lower():
            pubchem_col_excel = col
            break
    
    if pubchem_col_excel is None:
        raise ValueError("Could not find PubChem CID column in metabolite_data_wangxujie.xlsx")
    
    # Identify SMILE column in Excel file
    smile_col_excel = None
    for col in df_smile.columns:
        if "smile" in col.lower() or "smiles" in col.lower():
            smile_col_excel = col
            break
    
    if smile_col_excel is None:
        raise ValueError("Could not find SMILE/SMILES column in metabolite_data_wangxujie.xlsx")
    
    # Create mapping dictionary from PubChem CID to SMILE
    # Convert CIDs to string for consistent matching
    df_smile[pubchem_col_excel] = df_smile[pubchem_col_excel].astype(str)
    smile_dict = dict(zip(df_smile[pubchem_col_excel], df_smile[smile_col_excel]))
    
    # Merge SMILE into main dataframe based on pubChem_cid
    df["pubChem_cid"] = df["pubChem_cid"].astype(str)
    df["smile"] = df["pubChem_cid"].map(smile_dict).fillna(df["smile"])
    
    # Columns up to SMILE (basic info)
    info_cols = [
        "compounds", "cn_name", "class_1", "class_2", "formula",
        "molecular_weight", "rt", "score", "cas", "pubChem_cid", "smile"
    ]
    df_info = df[info_cols].copy()
    
    # Filter: remove rows where pubChem_cid is '-' (before split)
    df_info = df_info[df_info["pubChem_cid"] != "-"]
    df_info.to_csv(OUTPUT_INFO, index=False, encoding="utf-8-sig")
    
    # Get filtered compound names for expression data
    valid_compounds = df_info["compounds"].unique()
    
    # Filter original df to keep only valid compounds
    df_filtered = df[df["compounds"].isin(valid_compounds)]
    
    # Melt expression columns to LONG format
    id_vars = ["compounds"]
    value_vars = [col for col in df_filtered.columns if col not in info_cols]
    df_expr = df_filtered.melt(id_vars=id_vars, value_vars=value_vars, var_name="sample", value_name="relative_amount")
    
    # Split sample column: KYQH-Root → species=KYQH, tissue=Root
    df_expr[["species_code", "tissue_code"]] = df_expr["sample"].str.split("-", n=1, expand=True)
    df_expr = df_expr[["compounds", "species_code", "tissue_code", "relative_amount"]]
    df_expr.to_csv(OUTPUT_EXPRESSION, index=False, encoding="utf-8-sig")
    
    # Statistics
    filled_count = df_info["smile"].notna().sum()
    total_count = len(df_info)
    
    print(f"✅ Split done! Filtered out rows with pubChem_cid = '-'")
    print(f"  - Remaining compounds: {total_count}")
    print(f"  - SMILE filled from external source: {filled_count}/{total_count} ({filled_count/total_count*100:.1f}%)")
    print(f"Info: {OUTPUT_INFO}")
    print(f"Expression: {OUTPUT_EXPRESSION}")

if __name__ == "__main__":
    main()
