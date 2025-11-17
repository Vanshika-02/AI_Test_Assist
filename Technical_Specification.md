# Technical Specification: Embedding & Vector DB Setup

## Overview
This document describes the embedding pipeline and ChromaDB vector database setup for semantic search and retrieval.

## Embedding Pipeline
- Selector data is loaded from `selectors/selectors_merged_runtime_fixed.json`.
- Each selector is converted to a text string using key fields (`attr`, `value`, `elementType`, `htmlSnippet`).
- Batches of selector texts are sent to Azure OpenAI embedding endpoint using the deployment name and API version.
- Embeddings are received and stored in ChromaDB server (`selectors_base_collection`).

## ChromaDB Setup
- ChromaDB is run in server (HTTP) mode.
- Connection is established using `chromadb.HttpClient(host="localhost", port=8000)`.
- Embeddings and selector texts are stored in the `selectors_base_collection`.
- Validation and health checks are performed using scripts:
  - `scripts/selector_embedding.py`
  - `scripts/validate_chromadb.py`
  - `scripts/report_chromadb_status.py`

## Validation Process
- Embeddings are queried using semantic search.
- Top similar selectors and scores are returned for a given query.
- Collection existence, document count, and server heartbeat are checked for health monitoring.

## Configuration
- All credentials and endpoints are managed in `assistant_config.yaml`.
- Embedding function uses Azure OpenAI deployment and API version.

## Folder Structure
- All scripts are in `scripts/`
- Data files in `selectors/` and `data/`
- Logs in `logs/`
- Reports in `reports/`