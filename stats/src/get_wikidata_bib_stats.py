import rdflib
import requests
import pandas as pd
from datetime import datetime

# Load the TTL file
ttl_file_path = "./stats/data/read.ttl"  # Change this to your file path
g = rdflib.Graph()
g.parse(ttl_file_path, format="ttl")

# Extract the QIDs for articles
article_qids = set()

for s, p, o in g:
    if str(p) == "https://github.com/lubianat/wikidata_bib/tree/main/has_notes":
        article_qids.add(str(s).split("/")[-1])

# Count unique article QIDs
unique_article_qids_count = len(article_qids)
print(f"Total unique article QIDs: {unique_article_qids_count}")

# Wikidata SPARQL query to get all articles used as references for cell types
sparql_query = """
SELECT ?cell ?article WHERE {
  ?cell p:P31 ?statement .
  ?statement ps:P31 wd:Q189118 ;
             prov:wasDerivedFrom/pr:P248 ?article.
}
"""

# Wikidata SPARQL endpoint
sparql_url = "https://query.wikidata.org/sparql"
response = requests.get(sparql_url, params={"query": sparql_query, "format": "json"})
data = response.json()

# Process the SPARQL query results
cell_article_pairs = []
for result in data["results"]["bindings"]:
    cell_qid = result["cell"]["value"].split("/")[-1]
    article_qid = result["article"]["value"].split("/")[-1]
    cell_article_pairs.append((cell_qid, article_qid))

# Convert to DataFrame for easier manipulation
df = pd.DataFrame(cell_article_pairs, columns=["Cell QID", "Article QID"])

# Cross-reference with the article QIDs from the TTL file
matched_cells = df[df["Article QID"].isin(article_qids)]

# Results
unique_matched_cell_qids = matched_cells["Cell QID"].nunique()
unique_matched_article_qids = matched_cells["Article QID"].nunique()

print(f"Total unique article QIDs: {unique_article_qids_count}")
print(f"QIDs referencing cell types: {unique_matched_article_qids}")
print(f"Cell types found: {unique_matched_cell_qids}")

# Save the results to a CSV file
matched_cells.to_csv("./stats/results/matched_cells.csv", index=False)

# Update the SVG file with the statistics
svg_template_path = "./stats//data/stats.svg"
updated_svg_path = (
    f"./stats/results/wikidatabib_stats_{datetime.now().strftime('%Y%m%d')}.svg"
)

with open(svg_template_path, "r") as file:
    svg_content = file.read()

svg_content = svg_content.replace("{{total_articles}}", str(unique_article_qids_count))
svg_content = svg_content.replace(
    "{{filtered_articles}}", str(unique_matched_article_qids)
)
svg_content = svg_content.replace("{{total_classes}}", str(unique_matched_cell_qids))

with open(updated_svg_path, "w") as file:
    file.write(svg_content)

print(f"SVG file updated successfully: {updated_svg_path}")
