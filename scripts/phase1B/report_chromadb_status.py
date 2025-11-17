import chromadb
import yaml
import requests

# Load assistant config
with open('../../assistant_config.yaml', 'r') as f:
    config = yaml.safe_load(f)

client = chromadb.HttpClient(host="localhost", port=8000)

# List all collections
collections = client.list_collections()
print("ChromaDB Collections:")
for col in collections:
    print(f"- {col.name}")

# Check selectors_base_collection status
try:
    collection = client.get_collection("selectors_base_collection")
    count = collection.count()
    print(f"\n'selectors_base_collection' exists with {count} documents.")
    # Embedding function info is not available from server-side collection object
except Exception as e:
    print("\n'selectors_base_collection' not found or error occurred:", e)

# Check server heartbeat (use v2 API)
try:
    resp = requests.get("http://localhost:8000/api/v2/heartbeat")
    if resp.status_code == 200:
        print("\nChromaDB server heartbeat OK.")
    else:
        print("\nChromaDB server heartbeat failed:", resp.text)
except Exception as e:
    print("\nCould not reach ChromaDB server:", e)