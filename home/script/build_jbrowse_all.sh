#!/bin/bash
# Path definitions
GENOME_BASE="/mnt/d/Coding/Web/apiaceae/data/apiaceae_assembly"
GFF_BASE="/mnt/d/Coding/Web/apiaceae/data/apiaceae_gff"
OUTPUT_BASE="/mnt/d/Coding/Web/apiaceae/home/static/jbrowse"
TEMPLATE_PATH="/mnt/d/Coding/Web/apiaceae/home/static/jbrowse/template"

for fasta_path in "$GENOME_BASE"/*.genome.fa.gz
do
    filename=$(basename "$fasta_path")
    raw_species=${filename%.genome.fa.gz}
    species=$(echo "$raw_species" | tr '.' '_' | tr ' ' '_' | sed 's/[[:space:]]*$//')
    species_out="$OUTPUT_BASE/$species"
    gff_raw="$GFF_BASE/${raw_species}.gff"

    echo "--- Processing $species ---"
    
    # 1. Prepare Directory
    rm -rf "$species_out" && mkdir -p "$species_out"
    cp -r "$TEMPLATE_PATH"/. "$species_out/"
    cd "$species_out" || exit

    # 2. Use HARD LINKS instead of symlinks (Fixes Django 404)
    ln "$fasta_path" .
    ln "${fasta_path}.fai" .
    ln "${fasta_path}.gzi" .

    # 3. Process GFF
    jbrowse sort-gff "$gff_raw" | bgzip > "${species}.gff.gz"
    tabix -p gff "${species}.gff.gz"

    # 4. Add Assembly & Track with PREDICTABLE IDs
    jbrowse add-assembly "$filename" --name "$species" --load inPlace
    jbrowse add-track "${species}.gff.gz" --name "Gene Annotations" --trackId "${species}_track" --assemblyNames "$species" --load inPlace

    # 5. Create the Session (Matches the IDs above exactly)
    cat > session.json <<EOF
{
  "name": "Default Session",
  "view": {
    "id": "lv",
    "type": "LinearGenomeView",
    "tracks": [
      { "type": "ReferenceSequenceTrack", "configuration": "${species}-ReferenceSequenceTrack", "displays": [{ "type": "LinearReferenceSequenceDisplay", "configuration": "${species}-ReferenceSequenceTrack-LinearReferenceSequenceDisplay" }] },
      { "type": "FeatureTrack", "configuration": "${species}_track", "displays": [{ "type": "LinearBasicDisplay", "configuration": "${species}_track-LinearBasicDisplay" }] }
    ]
  }
}
EOF
    jbrowse set-default-session --session session.json --target config.json
    rm session.json
done