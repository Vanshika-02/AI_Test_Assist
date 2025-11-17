import yaml
import json
import requests
import chromadb

# Load assistant config
with open('../../assistant_config.yaml', 'r') as f:
    config = yaml.safe_load(f)

API_KEY = config['azure_openai']['api_key']
ENDPOINT = config['azure_openai']['endpoint']  # Should be base URL
DEPLOYMENT = config['azure_openai']['models']['embedding']
API_VERSION = config['azure_openai']['api_version']

# Azure OpenAI embedding endpoint
embedding_url = f"{ENDPOINT}openai/deployments/{DEPLOYMENT}/embeddings?api-version={API_VERSION}"
HEADERS = {"api-key": API_KEY, "Content-Type": "application/json"}

# Load selectors
with open('../../selectors/selectors_merged_runtime_fixed.json', 'r', encoding='utf-8') as f:
    selectors_data = json.load(f)

# Extract the list of selectors
selector_list = selectors_data['selectors']

# Prepare selector texts for embedding (combine key fields)
def selector_to_text(s):
    # Use attr, value, elementType, and htmlSnippet for context
    return f"{s.get('attr', '')}={s.get('value', '')} [{s.get('elementType', '')}] {s.get('htmlSnippet', '')}"

selector_texts = [selector_to_text(s) for s in selector_list]

print(f"Prepared {len(selector_texts)} selectors for embedding.")

def get_embeddings(batch):
    payload = {"input": batch}
    response = requests.post(embedding_url, headers=HEADERS, json=payload)
    response.raise_for_status()
    return response.json()["data"]

# Connect to ChromaDB server (uses default ./chroma folder internally)
client = chromadb.HttpClient(host="localhost", port=8000)
try:
    collection = client.get_collection("selectors_base_collection")
except Exception:
    collection = client.create_collection("selectors_base_collection")

batch_size = 50
for i in range(0, len(selector_texts), batch_size):
    batch = selector_texts[i:i+batch_size]
    embeddings = get_embeddings(batch)
    # Store each embedding with its selector text
    for j, emb in enumerate(embeddings):
        collection.add(
            embeddings=[emb['embedding']],
            documents=[batch[j]],
            ids=[f"selector_{i+j}"]
        )
print("All embeddings stored in ChromaDB.")