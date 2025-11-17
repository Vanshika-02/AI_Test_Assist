import chromadb
import yaml
from azure_embedding_function import AzureOpenAIEmbeddingFunction

# Load assistant config
with open('../../assistant_config.yaml', 'r') as f:
    config = yaml.safe_load(f)

API_KEY = config['azure_openai']['api_key']
ENDPOINT = config['azure_openai']['endpoint']
DEPLOYMENT = config['azure_openai']['models']['embedding']
API_VERSION = config['azure_openai']['api_version']

azure_ef = AzureOpenAIEmbeddingFunction(
    api_key=API_KEY,
    endpoint=ENDPOINT,
    deployment=DEPLOYMENT,
    api_version=API_VERSION
)

client = chromadb.HttpClient(host="localhost", port=8000)

collection = client.get_collection(
    "selectors_base_collection",
    embedding_function=azure_ef
)

# Example query after embedding:
query_text = "data-SaveBtn=AddBtn [button]"
results = collection.query(query_texts=[query_text], n_results=5)

print("Top 5 similar selectors:")
for doc, score in zip(results['documents'][0], results['distances'][0]):
    print(f"Score: {score:.4f} | Selector: {doc}")