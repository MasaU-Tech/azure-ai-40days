import os
import sys
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

def need(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        raise RuntimeError(f"環境変数 {name} が未設定です。")
    return v

# --- debug: 起動確認 ---
print("quick_search.py start")

# === env ===
ENDP  = need("AZURE_SEARCH_ENDPOINT").rstrip("/")
ADMIN = need("AZURE_SEARCH_ADMIN_KEY")
INDEX = os.environ.get("INDEX_NAME", "docs-idx")

# クエリは引数から。未指定なら Day12Marker を探す
query = " ".join(sys.argv[1:]) or "Day12Marker"
print(f"query: {query}")

# === search ===
client = SearchClient(endpoint=ENDP, index_name=INDEX, credential=AzureKeyCredential(ADMIN))
results = client.search(
    query,
    top=5,
    query_type="simple",
    search_fields=["content"],
    highlight_fields="content",
    highlight_pre_tag="[",
    highlight_post_tag="]"
)

found = False
for r in results:
    found = True
    name = r.get("metadata_storage_name")
    score = r.get("@search.score")
    score_str = f"{score:.4f}" if isinstance(score, (int, float)) else str(score)
    snippet = ""
    hl = r.get("@search.highlights")
    if isinstance(hl, dict) and hl.get("content"):
        snippet = hl["content"][0]
    print(f"- {name}  score={score_str}")
    if snippet:
        print(f"  snippet: {snippet}")

if not found:
    print("(no hits)")
