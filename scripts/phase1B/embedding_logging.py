import logging
import chromadb
import yaml

logging.basicConfig(
    filename="../../logs/embedding_pipeline.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

# Add console handler to also show logs in the terminal
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
console.setFormatter(formatter)
logging.getLogger().addHandler(console)

try:
    with open('../../assistant_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    client = chromadb.HttpClient(host="localhost", port=8000)
    collection = client.get_collection("selectors_base_collection")
    count = collection.count()
    logging.info(f"Collection exists with {count} documents.")
except Exception as e:
    logging.error(f"Error accessing ChromaDB: {e}")

try:
    query_text = "data-SaveBtn=AddBtn [button]"
    results = collection.query(query_texts=[query_text], n_results=3)
    logging.info(f"Query returned {len(results['documents'][0])} results.")
except Exception as e:
    logging.error(f"Error querying collection: {e}")