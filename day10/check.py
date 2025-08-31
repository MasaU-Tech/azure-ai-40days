import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
sc = SearchClient(
    endpoint=os.environ["AZURE_SEARCH_ENDPOINT"].strip(),
    index_name=os.environ.get("INDEX_NAME","docs-idx"),
    credential=AzureKeyCredential(os.environ["AZURE_SEARCH_ADMIN_KEY"].strip())
)
print("document_count =", sc.get_document_count())
for d in sc.search("*", top=10):
    print(repr(d.get("metadata_storage_name")), (d.get("content","")[:60] or "").replace("\n"," "))