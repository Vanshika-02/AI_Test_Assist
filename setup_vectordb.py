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


def extract_page_context(page_url: str) -> str:
    """
    Extract page context from URL

    Args:
        page_url: Full URL

    Returns:
        Page context string (e.g., "dashboard", "login")
    """
    if not page_url:
        return ""

    # Extract path from URL
    # http://.../client/dashboard → "dashboard"
    # http://.../client/steps → "steps"
    try:
        from urllib.parse import urlparse
        path = urlparse(page_url).path
        parts = [p for p in path.split('/') if p]
        if parts:
            return parts[-1]  # Last path segment
    except:
        pass

    return ""


def convert_to_natural_language(selector: Dict[str, Any], config: Dict[str, Any], azure_client) -> str:
    """
    Use LLM to convert technical selector fields to natural language action description

    Args:
        selector: Selector dictionary
        config: Configuration dictionary
        azure_client: Azure OpenAI client

    Returns:
        Natural language description string
    """
    embedding_strategy = config.get('selectors', {}).get('embedding_strategy', {})

    # Check if LLM conversion is enabled
    if not embedding_strategy.get('use_llm_conversion', False):
        return create_composite_text(selector, config)

    # Extract fields for LLM
    include_fields = embedding_strategy.get('include_fields', [])
    field_values = {}

    for field in include_fields:
        if field == "pageUrl":
            field_values['page_context'] = extract_page_context(selector.get('pageUrl', ''))
        elif field == "context":
            context = selector.get('context', [])
            field_values['context'] = ', '.join(context) if isinstance(context, list) else str(context)
        else:
            value = selector.get(field, '')
            field_values[field] = value if value else ''

    # Build LLM prompt
    prompt_template = embedding_strategy.get('conversion_prompt', '')
    if not prompt_template:
        logger.warning("No conversion_prompt in YAML, using template-based format")
        return create_composite_text(selector, config)

    try:
        prompt = prompt_template.format(**field_values)
    except KeyError as e:
        logger.warning(f"Missing field in prompt template: {e}")
        return create_composite_text(selector, config)

    # Call LLM
    try:
        chat_model = config['azure_openai']['models']['chat']

        response = azure_client.chat.completions.create(
            model=chat_model,
            messages=[
                {"role": "system", "content": "You convert technical UI element details into natural action descriptions. Be concise and action-oriented."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=50
        )

        natural_language = response.choices[0].message.content.strip()

        # Ensure it's not empty
        if not natural_language:
            logger.warning(f"Empty LLM response, falling back to template")
            return create_composite_text(selector, config)

        return natural_language

    except Exception as e:
        logger.error(f"LLM conversion failed: {e}")
        return create_composite_text(selector, config)


def create_composite_text(selector: Dict[str, Any], config: Dict[str, Any]) -> str:
    """
    Create composite text for embedding based on YAML configuration

    Reads embedding_strategy from YAML to determine which fields to include
    and how to format them.

    Args:
        selector: Selector dictionary
        config: Configuration dictionary with embedding_strategy

    Returns:
        Composite text string for embedding
    """
    embedding_strategy = config.get('selectors', {}).get('embedding_strategy', {})
    composite_format = embedding_strategy.get('composite_format', '')
    include_fields = embedding_strategy.get('include_fields', [])

    # If no config, fall back to default
    if not composite_format:
        logger.warning("No embedding_strategy in YAML, using default format")
        composite_format = "{attr}_{value} {module} {elementType} {label} {context}"
        include_fields = ["attr", "value", "module", "elementType", "label", "context"]

    # Build field values dictionary
    field_values = {}

    for field in include_fields:
        if field == "pageUrl":
            # Special handling: convert URL to page_context
            page_url = selector.get('pageUrl', '')
            field_values['page_context'] = extract_page_context(page_url)
        elif field == "context":
            # Handle context - can be list or string
            context = selector.get('context', [])
            if isinstance(context, list):
                field_values['context'] = ' '.join(context)
            else:
                field_values['context'] = str(context) if context else ''
        else:
            # Regular field
            field_values[field] = selector.get(field, '')

    # Replace placeholders in composite format
    try:
        composite = composite_format.format(**field_values)
    except KeyError as e:
        logger.warning(f"Missing field in composite_format: {e}")
        # Fall back to simple concatenation
        composite = ' '.join(str(v) for v in field_values.values() if v)

    # Clean up extra spaces and separators
    composite = composite.replace('  ', ' ').replace(' | |', ' |').strip()

    return composite


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
        # Convert to natural language using LLM
        doc_text = convert_to_natural_language(selector, config, azure_client)

        # Log first 5 for verification
        if idx < 5:
            logger.info(f"  Selector {idx}: {doc_text}")

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

        # Build metadata - include both embedding fields and metadata-only fields
        embedding_strategy = config.get('selectors', {}).get('embedding_strategy', {})
        metadata_fields = embedding_strategy.get('metadata_fields', [])
        include_fields = embedding_strategy.get('include_fields', [])

        # Start with basic metadata
        metadata = {
            "id": selector_id,
            "full_selector": full_selector
        }

        # Add all embedding fields to metadata (for filtering/debugging)
        for field in include_fields:
            if field == "pageUrl":
                page_val = extract_page_context(selector.get('pageUrl', ''))
                metadata['page_context'] = page_val if page_val is not None else ''
            elif field == "context":
                metadata['context'] = context_str if context_str is not None else ''
            else:
                field_val = selector.get(field, '')
                metadata[field] = field_val if field_val is not None else ''

        # Add metadata-only fields
        for field in metadata_fields:
            if field not in metadata:  # Don't duplicate
                field_val = selector.get(field, '')
                metadata[field] = field_val if field_val is not None else ''

        # Ensure critical fields are present
        if 'attr' not in metadata:
            metadata['attr'] = attr
        if 'value' not in metadata:
            metadata['value'] = value
        if 'module' not in metadata:
            metadata['module'] = selector.get('module', '')
        if 'priority' not in metadata:
            metadata['priority'] = selector.get('priority', 50)
        if 'isDynamic' not in metadata:
            metadata['isDynamic'] = selector.get('isDynamic', False)

        metadatas.append(metadata)

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
