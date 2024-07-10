import pandas as pd
import wikidata2df
from tqdm import tqdm
from pathlib import Path
import json
from collections import Counter
from time import gmtime, strftime


HERE = Path(__file__).parent.resolve()
BASE_FOLDER = HERE / "../results/"
QUERY_FILE = HERE / "queries/cells_and_taxa.rq"
RESULTS_FILE = BASE_FOLDER / "cells_by_taxon.csv"
EDITORS_FILE = BASE_FOLDER / "cells_wikidata_editors.csv"
AUTHORS_JSON_FILE = BASE_FOLDER / "cells_wikidata_authors.json"
AUTHORS_CSV_FILE = BASE_FOLDER / "cells_wikidata_authors.csv"
AUTHOR_STATS_FILE = "author_stats.txt"
UNEDITED_FILE = BASE_FOLDER / "unedited_by_tiago_lubiana.txt"


def get_editor_df_from_qid(qid):
    results = requests.get(
        f"https://xtools.wmflabs.org/api/page/top_editors/wikidata.org/{qid}?limit=1000"
    )
    result = results.json()
    df_nested_list = pd.json_normalize(result, record_path=["top_editors"])
    df_for_qid = df_nested_list[["username", "count"]].copy()
    df_for_qid["qid"] = qid
    return df_for_qid


def get_page_author_from_qid(qid):
    results = requests.get(
        f"https://xtools.wmflabs.org/api/page/articleinfo/wikidata.org/{qid}"
    )
    result = results.json()
    return result["author"]


def get_unedited_qids(df, editors_df, username):
    edited_qids = set(editors_df.loc[editors_df["username"] == username, "qid"])
    all_qids = set(df["qid"])
    unedited_qids = all_qids - edited_qids
    return list(unedited_qids)


# Read the SPARQL query and get the data
query = QUERY_FILE.read_text()
df = wikidata2df.wikidata2df(query)

# Calculate and print the total number of cell types
total_number = len(set(df["qid"]))
print(f"Total number of cell types on Wikidata: {total_number}")

# Fill NaNs and save cells by taxon
df.fillna("no taxon specified", inplace=True)
df.groupby("taxon_name").count().sort_values(by="qid").to_csv(RESULTS_FILE)

# Calculate specific cell types for humans and mice
human_cells = df[df["taxon_name"] == "Homo sapiens"].shape[0]
mouse_cells = df[df["taxon_name"] == "Mus musculus"].shape[0]

# Process editors data
try:
    editors_df = pd.read_csv(EDITORS_FILE)
    editors_df = editors_df[["username", "count", "qid"]].copy()
except FileNotFoundError:
    editors_df = pd.DataFrame(columns=["username", "count", "qid"])

existing_qids = set(editors_df["qid"])

new_editor_data = []

for _, row in tqdm(df.iterrows(), total=df.shape[0]):
    qid = row["qid"]
    if qid not in existing_qids:
        new_editor_data.append(get_editor_df_from_qid(qid))

if new_editor_data:
    new_editors_df = pd.concat(new_editor_data, ignore_index=True)
    editors_df = pd.concat([editors_df, new_editors_df]).drop_duplicates()

editors_df.to_csv(EDITORS_FILE, index=False)

# Reshape and analyze editor data
editors_df_reshaped = editors_df.pivot(
    index="qid", columns="username", values="count"
).fillna(0)
top_editors_by_sum = editors_df_reshaped.sum().sort_values().tail(10)
top_editors_by_count = editors_df_reshaped.count().sort_values().tail(10)

# Process authors data
if AUTHORS_JSON_FILE.exists():
    with open(AUTHORS_JSON_FILE) as f:
        author_dict = json.loads(f.read())
else:
    author_dict = {}

for _, row in tqdm(df.iterrows(), total=df.shape[0]):
    qid = row["qid"]
    if qid not in author_dict:
        author_dict[qid] = get_page_author_from_qid(qid)

with open(AUTHORS_JSON_FILE, "w") as fp:
    json.dump(author_dict, fp)

# Count authors and save to CSV
author_counts = Counter(author_dict.values())
authors_df = pd.DataFrame.from_dict(author_counts, orient="index", columns=["count"])
authors_df["author"] = authors_df.index
authors_df.to_csv(AUTHORS_CSV_FILE, index=False)

# Generate report text
edited = editors_df.loc[editors_df["username"] == "TiagoLubiana", "qid"].nunique()
created = author_counts.get("TiagoLubiana", 0)
percentage_edited = f"{(100 * edited / total_number):.1f}"
percentage_created = f"{(100 * created / total_number):.1f}"
date = strftime("%d of %B of %Y", gmtime())

report_text = f"""
Wikidata contains {total_number} subclasses of "cell ([Q7868](https://www.wikidata.org/wiki/Q7868))" as of {date}. 
From those, {human_cells} cell classes are specific for humans, and {mouse_cells} are specific for mice.  
From the {total_number} cell classes on Wikidata, {edited} ({percentage_edited}%) have been edited somehow by User:TiagoLubiana, and {created} ({percentage_created}%) have been created by User:TiagoLubiana. 
Edits included adding multilanguage labels, connecting a dangling Wikipedia page to the cell subclass hierarchy, adding identifiers, images, markers, and other pieces of information. 
Approximately 430 hundred terms were added via manual curation based on PanglaoDB entries, while the remaining {created - 430} entries were created either via Wikidata's web interface or via the curation workflow described in this chapter. 
These statistics demonstrate how the curation system efficiently contributes to the status of cell type information on Wikidata.
"""
print(report_text)

with open(AUTHOR_STATS_FILE, "w") as fp:
    json.dump(report_text, fp)

# Log unedited cell types
unedited_qids = get_unedited_qids(df, editors_df, "TiagoLubiana")
with open(UNEDITED_FILE, "w") as f:
    for qid in unedited_qids:
        f.write(f"{qid}\n")
