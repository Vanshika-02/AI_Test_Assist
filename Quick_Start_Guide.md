# Quick Start Guide: Embedding & ChromaDB Setup

## Prerequisites
- Python 3.10+
- ChromaDB server running (`chroma run --host 0.0.0.0 --port 8000`)
- Azure OpenAI API key, endpoint, deployment name, and API version

## Steps

1. **Install dependencies**
   ```
   pip install -r requirements.txt
   ```

2. **Configure Azure OpenAI**
   - Update `assistant_config.yaml` with your API key, endpoint, deployment name, and API version.

3. **Run Embedding Script**
   ```
   python scripts/selector_embedding.py
   ```
   - This will embed all selectors and store them in ChromaDB.

4. **Validate Embeddings**
   ```
   python scripts/validate_chromadb.py
   ```
   - Query the collection and check top similar selectors.

5. **Check ChromaDB Status**
   ```
   python scripts/report_chromadb_status.py
   ```
   - View collection info and server health.

## Troubleshooting
- Ensure ChromaDB server is running and accessible.
- Check API credentials and endpoint in `assistant_config.yaml`.
- Review logs for errors in `logs/`.

## Folder Structure
- Scripts: `scripts/`
- Data: `selectors/`, `data/`
- Logs: `logs/`
- Reports: `reports/`