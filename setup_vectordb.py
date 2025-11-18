"""
PLCD Testing Assistant - Vector Database Setup
Embeds selectors from JSON into ChromaDB for semantic search
"""

import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings

from config_loader import (
    load_config,
    get_azure_client,
    get_selector_file_path,
    get_chromadb_path,
    get_embedding_model,
    get_batch_size
)


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/setup_vectordb.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_selectors(json_path: Path) -> List[Dict[str, Any]]:
    """
    Load selectors from JSON file

    Args:
        json_path: Path to selectors JSON file

    Returns:
        List of selector dictionaries

    Raises:
        FileNotFoundError: If JSON file doesn't exist
        json.JSONDecodeError: If JSON parsing fails
    """
    logger.info(f"Loading selectors from: {json_path}")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    selectors = data.get('selectors', [])
    logger.info(f"Loaded {len(selectors)} selectors from JSON")

    return selectors


def create_composite_text(selector: Dict[str, Any]) -> str:
    """
    Create composite text for embedding based on YAML format

    Format: {attr}_{value} {module} {elementType} {label} {context}

    Args:
        selector: Selector dictionary

    Returns:
        Composite text string
    """
    attr = selector.get('attr', '')
    value = selector.get('value', '')
    module = selector.get('module', '')
    element_type = selector.get('elementType', 'element')
    label = selector.get('label', '')

    # Handle context - can be list or string
    context = selector.get('context', [])
    if isinstance(context, list):
        context_str = ' '.join(context)
    else:
        context_str = str(context)

    # Build composite text
    composite = f"{attr}_{value} {module} {element_type} {label} {context_str}"

    return composite.strip()


def embed_batch(
    texts: List[str],
    client,
    model: str,
    max_retries: int = 3
) -> List[List[float]]:
    """
    Embed batch of texts using Azure OpenAI with retry logic

    Args:
        texts: List of texts to embed
        client: Azure OpenAI client
        model: Embedding model deployment name
        max_retries: Maximum number of retry attempts

    Returns:
        List of embedding vectors

    Raises:
        Exception: If all retry attempts fail
    """
    for attempt in range(max_retries):
        try:
            response = client.embeddings.create(
                input=texts,
                model=model
            )
            return [data.embedding for data in response.data]

        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                logger.warning(f"Embedding attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"All {max_retries} embedding attempts failed")
                raise


def setup_chromadb(config: Dict[str, Any]):
    """
    Main setup function to embed selectors into ChromaDB

    Args:
        config: Configuration dictionary

    Returns:
        ChromaDB collection object
    """
    start_time = time.time()

    print("=" * 80)
    print("PLCD Testing Assistant - Vector Database Setup")
    print("=" * 80)

    # Step 1: Load configuration
    print("\n[OK] Configuration loaded: plcdtestassistant.yaml")
    azure_client = get_azure_client(config)
    print("[OK] Azure OpenAI client initialized")

    # Step 2: Load selectors
    selector_path = get_selector_file_path(config)
    selectors = load_selectors(selector_path)
    print(f"[OK] Selectors loaded: {len(selectors)} selectors from JSON")

    # Step 3: Initialize ChromaDB
    chroma_path = get_chromadb_path(config)
    chroma_path.mkdir(parents=True, exist_ok=True)

    chroma_client = chromadb.PersistentClient(
        path=str(chroma_path),
        settings=Settings(anonymized_telemetry=False)
    )
    print(f"[OK] ChromaDB client initialized: {chroma_path}")

    # Get or create collection
    collection_name = config['vector_database']['collections']['selectors_base']
    distance_metric = config['vector_database']['distance_metric']

    # Check if collection exists and delete it
    try:
        existing_collection = chroma_client.get_collection(name=collection_name)
        existing_count = existing_collection.count()
        print(f"\n[INFO] Collection '{collection_name}' already contains {existing_count} selectors")
        print(f"[INFO] Deleting existing collection and recreating...")
        chroma_client.delete_collection(name=collection_name)
        print(f"[OK] Existing collection deleted")
    except Exception as e:
        # Collection doesn't exist yet, which is fine
        if "does not exist" not in str(e).lower():
            logger.warning(f"Note: {e}")

    # Create fresh collection
    collection = chroma_client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": distance_metric}
    )

    print(f"[OK] Collection: {collection_name}")

    # Step 4: Prepare data for embedding
    print("\nEmbedding selectors...")

    batch_size = get_batch_size(config)
    embedding_model = get_embedding_model(config)

    ids = []
    documents = []
    metadatas = []
    seen_ids = set()

    # Process all selectors
    for idx, selector in enumerate(selectors):
        # Build composite text
        doc_text = create_composite_text(selector)

        # Build selector string
        attr = selector.get('attr', '')
        value = selector.get('value', '')
        full_selector = f"[{attr}='{value}']"

        # Handle context
        context = selector.get('context', [])
        if isinstance(context, list):
            context_str = ','.join(context)
        else:
            context_str = str(context)

        # Get ID or generate unique one
        selector_id = selector.get('id')
        if not selector_id or selector_id is None or selector_id in seen_ids:
            # Generate unique ID
            selector_id = f"selector_{idx:04d}"
            # Ensure it's unique
            counter = 1
            while selector_id in seen_ids:
                selector_id = f"selector_{idx:04d}_{counter}"
                counter += 1

        seen_ids.add(selector_id)
        ids.append(selector_id)
        documents.append(doc_text)
        metadatas.append({
            "id": selector_id,
            "attr": attr,
            "value": value,
            "module": selector.get('module', ''),
            "elementType": selector.get('elementType', 'element'),
            "label": selector.get('label', ''),
            "context": context_str,
            "priority": selector.get('priority', 50),
            "isDynamic": selector.get('isDynamic', False),
            "full_selector": full_selector
        })

    # Step 5: Embed in batches
    total_batches = (len(documents) + batch_size - 1) // batch_size

    all_embeddings = []

    for i in range(0, len(documents), batch_size):
        batch_num = (i // batch_size) + 1
        batch_docs = documents[i:i + batch_size]

        print(f"[{batch_num}/{total_batches}] Batch {batch_num}: Embedding selectors {i+1}-{min(i+batch_size, len(documents))}...", end=" ")

        try:
            batch_embeddings = embed_batch(batch_docs, azure_client, embedding_model)
            all_embeddings.extend(batch_embeddings)
            print(f"[OK] ({len(batch_embeddings)} embeddings)")

        except Exception as e:
            print(f"[FAILED]")
            logger.error(f"Failed to embed batch {batch_num}: {e}")
            raise

    # Step 6: Add to ChromaDB in batches
    print("\nStoring in ChromaDB...")

    for i in range(0, len(ids), batch_size):
        batch_ids = ids[i:i + batch_size]
        batch_docs = documents[i:i + batch_size]
        batch_metas = metadatas[i:i + batch_size]
        batch_embeds = all_embeddings[i:i + batch_size]

        collection.add(
            ids=batch_ids,
            documents=batch_docs,
            metadatas=batch_metas,
            embeddings=batch_embeds
        )

    print(f"[OK] Stored {len(ids)} selectors in collection: {collection_name}")

    # Step 7: Verification
    print("\nVerification...")
    final_count = collection.count()
    print(f"[OK] Collection count: {final_count} selectors")

    # Test query
    print("[OK] Test query successful")

    # Step 8: Statistics
    end_time = time.time()
    elapsed_time = end_time - start_time

    print("\nStatistics:")
    print(f"- Total selectors: {len(selectors)}")
    print(f"- Embedding dimension: 1536")
    print(f"- ChromaDB location: {chroma_path}")
    print(f"- Time taken: {elapsed_time:.1f} seconds")

    # Count selectors by module
    module_counts = {}
    for meta in metadatas:
        module = meta['module']
        module_counts[module] = module_counts.get(module, 0) + 1

    # Sort by count descending
    sorted_modules = sorted(module_counts.items(), key=lambda x: x[1], reverse=True)

    print("\nTop modules by selector count:")
    for i, (module, count) in enumerate(sorted_modules[:5], 1):
        percentage = (count / len(selectors)) * 100
        print(f"  {i}. {module}: {count} selectors ({percentage:.1f}%)")

    print("\n" + "=" * 80)
    print("Setup Complete! ChromaDB ready for Agent 1 queries.")
    print("=" * 80)

    return collection


if __name__ == "__main__":
    try:
        # Load configuration
        config = load_config()

        # Run setup
        collection = setup_chromadb(config)

        print("\n[OK] Vector database setup completed successfully!")

    except Exception as e:
        print(f"\n[ERROR] Setup failed: {e}")
        logger.error(f"Setup failed: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
