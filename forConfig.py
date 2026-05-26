import os

# helper code
# track configuration for IGV customization


track_list = []
for fname in sorted(os.listdir("bedgraphs_by_label")):
    if not fname.endswith(".bedGraph"):
        continue
    name = fname.replace(".bedGraph", "")
    entry = f'''{{
        name: "{name}",
        url: "bedgraphs_by_label/{fname}",
        format: "bedgraph",
        autoscale: true
    }}'''
    track_list.append(entry)

track_list.append('''{
    name: "Annotations",
    url: "annotations.gff",
    format: "gff",
    color: "0,128,0",
    displayMode: "EXPANDED"
}''')

print("tracks: [\n" + ",\n".join(track_list) + "\n]")