import unittest
import chromadb
import yaml
from azure_embedding_function import AzureOpenAIEmbeddingFunction

class TestChromaDBPipeline(unittest.TestCase):
    def setUp(self):
        with open('../../assistant_config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        self.client = chromadb.HttpClient(host="localhost", port=8000)
        self.collection_name = "selectors_base_collection"
        self.azure_ef = AzureOpenAIEmbeddingFunction(
            api_key=config['azure_openai']['api_key'],
            endpoint=config['azure_openai']['endpoint'],
            deployment=config['azure_openai']['models']['embedding'],
            api_version=config['azure_openai']['api_version']
        )

    def test_collection_exists(self):
        collections = [col.name for col in self.client.list_collections()]
        self.assertIn(self.collection_name, collections, "Collection does not exist.")

    def test_collection_count(self):
        collection = self.client.get_collection(self.collection_name)
        count = collection.count()
        self.assertGreater(count, 0, "Collection is empty.")

    def test_query(self):
        # Always specify the embedding function for queries
        collection = self.client.get_collection(
            self.collection_name,
            embedding_function=self.azure_ef
        )
        query_text = "data-SaveBtn=AddBtn [button]"
        results = collection.query(query_texts=[query_text], n_results=3)
        self.assertTrue(len(results['documents'][0]) > 0, "No results returned from query.")

if __name__ == "__main__":
    unittest.main()