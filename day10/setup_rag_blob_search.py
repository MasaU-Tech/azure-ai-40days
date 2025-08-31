# FILE: C:\dev\azure-ai-40days\day10\setup_rag_blob_search.py
import os, time
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient, SearchIndexerClient
from azure.search.documents.indexes.models import (
    SearchIndex, SimpleField, SearchableField, SearchFieldDataType,
    SearchIndexerDataSourceConnection, SearchIndexerDataContainer,
    SearchIndexer, IndexingParameters, IndexingParametersConfiguration
)
from azure.search.documents import SearchClient

endpoint   = os.environ["AZURE_SEARCH_ENDPOINT"].strip().rstrip("/")
key        = os.environ["AZURE_SEARCH_ADMIN_KEY"].strip()
index_name = os.getenv("INDEX_NAME", "docs-idx")
container  = os.getenv("BLOB_CONTAINER", "docs")
conn_str   = os.environ["AZURE_STORAGE_CONNECTION_STRING"].strip()

# 1) インデックス作成（最小フィールド）
idx_client = SearchIndexClient(endpoint, AzureKeyCredential(key))
fields = [
    SimpleField(name="id", type=SearchFieldDataType.String, key=True),
    SearchableField(name="content", type=SearchFieldDataType.String),
    SimpleField(name="metadata_storage_name", type=SearchFieldDataType.String, filterable=True),
    SimpleField(name="metadata_storage_path", type=SearchFieldDataType.String, filterable=True),
]
idx = SearchIndex(name=index_name, fields=fields)
idx_client.create_or_update_index(idx)

# 2) データソース & インデクサ（まず default で確実に通す）
ixr_client = SearchIndexerClient(endpoint, AzureKeyCredential(key))
ds = SearchIndexerDataSourceConnection(
    name="blob-ds", type="azureblob", connection_string=conn_str,
    container=SearchIndexerDataContainer(name=container)
)
ixr_client.create_or_update_data_source_connection(ds)

# ❌ ここで IndexingParameters / IndexingParametersConfiguration を渡さない
# 既定（parsingMode=default 他）でまず通す
ixr = SearchIndexer(
    name="blob-idxr",
    data_source_name="blob-ds",
    target_index_name=index_name
)
ixr_client.create_or_update_indexer(ixr)
ixr_client.run_indexer("blob-idxr")

# 3) 反映待ち（最大60秒、5秒間隔）
for _ in range(12):
    st = ixr_client.get_indexer_status("blob-idxr")
    last = getattr(st, "last_result", None)
    if last and getattr(last, "status", "").lower() == "success":
        break
    time.sleep(5)

# 4) 検索
sc = SearchClient(endpoint=endpoint, index_name=index_name, credential=AzureKeyCredential(key))
for d in sc.search("Azure", top=3):
    print(d.get("metadata_storage_name"), (d.get("content","")[:60] or "").replace("\n"," "))
