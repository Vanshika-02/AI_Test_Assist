import openai
import numpy as np

class AzureOpenAIEmbeddingFunction:
    def __init__(self, api_key, endpoint, deployment, api_version):
        self.api_key = api_key
        self.endpoint = endpoint
        self.deployment = deployment
        self.api_version = api_version

    def __call__(self, input):
        return self.embed_query(input)

    def embed_query(self, input):
        client = openai.AzureOpenAI(
            api_key=self.api_key,
            azure_endpoint=self.endpoint,
            api_version=self.api_version
        )
        response = client.embeddings.create(
            input=input,
            model=self.deployment
        )
        # Convert to numpy array
        embeddings = [item.embedding for item in response.data]
        return np.array(embeddings)

    def name(self):
        return "azure_openai"