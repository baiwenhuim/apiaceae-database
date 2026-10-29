#!/usr/bin/env python3
"""
最终完整版：自动建库 + 自动合并 + 自动生成 all_species 数据库
文件名已统一 → 仅转小写即可匹配 Django
"""
import os
import subprocess
import glob

# ===================== 路径 =====================
BASE = "/mnt/d/Coding/Web/apiaceae/data"
CDS_DIR = f"{BASE}/apiaceae_cds"
PEP_DIR = f"{BASE}/apiaceae_pep"

OUT_NUC = f"{BASE}/blast_dbs/nucleotide"
OUT_PROT = f"{BASE}/blast_dbs/protein"

os.makedirs(OUT_NUC, exist_ok=True)
os.makedirs(OUT_PROT, exist_ok=True)

# ===================== 需要修复的物种 =====================
NEED_FIX = {
    "Changium_smyrnioides",
    "Dickinsia_hydrocotyloides",
    "Heracleum_sosnowskyi",
    "Ligusticum_chuanxiong_hapA",
    "Ligusticum_chuanxiong_hapB",
    "Petroselinum_crispum_var._neapolitanum"
}

# ===================== 工具函数 =====================
def db_exists(path):
    return os.path.exists(f"{path}.psq") or os.path.exists(f"{path}.nsq")

def fix_fasta(infile, outfile, is_protein=False):
    valid_aa = set("ACDEFGHIKLMNPQRSTVWY*X-")
    with open(infile) as f, open(outfile, "w") as w:
        for line in f:
            if line.startswith(">"):
                parts = line.strip().split(maxsplit=1)
                seq_id = parts[0][1:][:50]
                desc = parts[1] if len(parts) > 1 else ""
                w.write(f">{seq_id} {desc}\n")
            else:
                if is_protein:
                    line = "".join([c for c in line.strip() if c in valid_aa]) + "\n"
                w.write(line)

def run_makeblastdb(infa, outdb, dbtype, title):
    cmd = [
        "makeblastdb", "-in", infa, "-dbtype", dbtype,
        "-out", outdb, "-title", title, "-parse_seqids"
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✓ 成功: {outdb}")
        return True
    except Exception as e:
        print(f"✗ 失败: {e}")
        return False

# ===================== 1. 构建单个物种库 =====================
def build_individual():
    print("=" * 70)
    print(" 构建单个物种数据库（已存在跳过）")
    print("=" * 70)

    # CDS
    for fa in glob.glob(f"{CDS_DIR}/*.cds"):
        sp = os.path.basename(fa).replace(".cds", "")
        dbname = sp.lower()
        out = f"{OUT_NUC}/{dbname}"

        if db_exists(out):
            print(f"✅ 跳过: {sp}")
            continue

        print(f"\n处理: {sp}")
        if sp in NEED_FIX:
            tmp = fa + ".tmp"
            fix_fasta(fa, tmp, is_protein=False)
            run_makeblastdb(tmp, out, "nucl", dbname)
            os.remove(tmp)
        else:
            run_makeblastdb(fa, out, "nucl", dbname)

    # PEP
    for fa in glob.glob(f"{PEP_DIR}/*.pep"):
        sp = os.path.basename(fa).replace(".pep", "")
        dbname = sp.lower()
        out = f"{OUT_PROT}/{dbname}"

        if db_exists(out):
            print(f"✅ 跳过: {sp}")
            continue

        print(f"\n处理: {sp}")
        if sp in NEED_FIX:
            tmp = fa + ".tmp"
            fix_fasta(fa, tmp, is_protein=True)
            run_makeblastdb(tmp, out, "prot", dbname)
            os.remove(tmp)
        else:
            run_makeblastdb(fa, out, "prot", dbname)

# ===================== 2. 自动合并所有物种 =====================
def merge_all():
    print("\n" + "=" * 70)
    print(" 自动合并所有物种 → all_species")
    print("=" * 70)

    # 合并 CDS
    cds_files = sorted(glob.glob(f"{CDS_DIR}/*.cds"))
    merge_cds = f"{CDS_DIR}/all_species.cds"
    if not os.path.exists(merge_cds):
        with open(merge_cds, "w") as w:
            for fa in cds_files:
                with open(fa) as f:
                    w.write(f.read())
        print(f"✓ 合并完成: {merge_cds}")

    # 合并 PEP
    pep_files = sorted(glob.glob(f"{PEP_DIR}/*.pep"))
    merge_pep = f"{PEP_DIR}/all_species.pep"
    if not os.path.exists(merge_pep):
        with open(merge_pep, "w") as w:
            for fa in pep_files:
                with open(fa) as f:
                    w.write(f.read())
        print(f"✓ 合并完成: {merge_pep}")

    return merge_cds, merge_pep

# ===================== 3. 构建合并数据库 =====================
def build_merged(merge_cds, merge_pep):
    print("\n" + "=" * 70)
    print(" 构建 all_species 合并数据库")
    print("=" * 70)

    # CDS all_species
    out = f"{OUT_NUC}/all_species"
    if not db_exists(out):
        tmp = merge_cds + ".tmp"
        fix_fasta(merge_cds, tmp, is_protein=False)
        run_makeblastdb(tmp, out, "nucl", "All Species")
        os.remove(tmp)

    # PEP all_species
    out = f"{OUT_PROT}/all_species"
    if not db_exists(out):
        tmp = merge_pep + ".tmp"
        fix_fasta(merge_pep, tmp, is_protein=True)
        run_makeblastdb(tmp, out, "prot", "All Species")
        os.remove(tmp)

# ===================== 主函数 =====================
if __name__ == "__main__":
    build_individual()
    cds, pep = merge_all()
    build_merged(cds, pep)
    print("\n🎉 全部完成！")
    print(f"CDS 合并库: {OUT_NUC}/all_species")
    print(f"Protein 合并库: {OUT_PROT}/all_species")
