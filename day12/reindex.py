# FILE: day12/reindex.py
import os, time, requests
from azure.storage.blob import BlobClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

# === env ===
CONN = os.environ["AZURE_STORAGE_CONNECTION_STRING"]
ENDP = os.environ["AZURE_SEARCH_ENDPOINT"].strip().rstrip("/")
ADMIN= os.environ["AZURE_SEARCH_ADMIN_KEY"]
INDEX= os.environ.get("INDEX_NAME","docs-idx")
INDEXER=os.environ.get("INDEXER_NAME","blob-idxr")
CONT = os.environ.get("BLOB_CONTAINER","docs")

def upload(local_path, blob_name):
    bc = BlobClient.from_connection_string(CONN, container_name=CONT, blob_name=blob_name)
    with open(local_path, "rb") as f: bc.upload_blob(f, overwrite=True)
    print(f"[upload] {blob_name}")

def run_indexer():
    url = f"{ENDP}/indexers/{INDEXER}/run?api-version=2024-07-01"
    r = requests.post(url, headers={"api-key": ADMIN})
    r.raise_for_status(); print("[indexer] run accepted")

def wait_status(timeout=180):
    url = f"{ENDP}/indexers/{INDEXER}/status?api-version=2024-07-01"
    t0=time.time()
    while True:
        st = requests.get(url, headers={"api-key": ADMIN}).json()["lastResult"]
        print(f"[status] {st['status']} processed={st.get('itemsProcessed')} failed={st.get('itemsFailed')}")
        if st["status"] in ("success","transientFailure","error"): return st
        if time.time()-t0>timeout: raise TimeoutError("indexer timeout")
        time.sleep(5)

def verify():
    sc = SearchClient(endpoint=ENDP, index_name=INDEX, credential=AzureKeyCredential(ADMIN))
    cnt = sc.get_document_count()
    print("[verify] document_count =", cnt)
    hits = list(sc.search("エラー 対処", top=3, query_type="simple", search_fields=["content"]))
    print("[verify] query 'エラー 対処' hits:", [h.get("metadata_storage_name") for h in hits])

if __name__ == "__main__":
    base = r"C:\dev\azure-ai-40days\day12"
    upload(os.path.join(base,"errors_jp.md"), "errors_jp.md")
    upload(os.path.join(base,"faq_jp.md"), "faq_jp.md")
    run_indexer()
    last = wait_status()
    assert last["itemsFailed"] == 0, "indexer failed items > 0"
    verify()
    print("[done] Day12 reindex completed")
