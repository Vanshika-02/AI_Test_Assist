import chromadb
import yaml
from azure_embedding_function import AzureOpenAIEmbeddingFunction

with open('../../assistant_config.yaml', 'r') as f:
    config = yaml.safe_load(f)

client = chromadb.HttpClient(host="localhost", port=8000)

azure_ef = AzureOpenAIEmbeddingFunction(
    api_key=config['azure_openai']['api_key'],
    endpoint=config['azure_openai']['endpoint'],
    deployment=config['azure_openai']['models']['embedding'],
    api_version=config['azure_openai']['api_version']
)

collection = client.get_collection(
    "selectors_base_collection",
    embedding_function=azure_ef
)

count = collection.count()
print(f"Collection 'selectors_base_collection' contains {count} documents.\n")

query_text = "data-SaveBtn=AddBtn [button]"
results = collection.query(query_texts=[query_text], n_results=5)

print("Top 5 similar selectors for query:")
for doc, score in zip(results['documents'][0], results['distances'][0]):
    print(f"Score: {score:.4f} | Selector: {doc}")

# Optionally, save report to a file
with open("../../reports/chromadb_report.txt", "w", encoding="utf-8") as report_file:
    report_file.write(f"Collection 'selectors_base_collection' contains {count} documents.\n\n")
    report_file.write("Top 5 similar selectors for query:\n")
    for doc, score in zip(results['documents'][0], results['distances'][0]):
        report_file.write(f"Score: {score:.4f} | Selector: {doc}\n")