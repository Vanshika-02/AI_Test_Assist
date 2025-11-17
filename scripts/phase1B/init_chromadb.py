import chromadb

client = chromadb.HttpClient(host="localhost", port=8000)
selectors_base = client.create_collection("selectors_base_collection")
runtime_learned = client.create_collection("runtime_learned_collection")

print("ChromaDB initialized with collections.")