# Reporting Guide: ChromaDB Embedding & Semantic Search

## Overview
This guide explains how to generate and interpret reports from your ChromaDB vector database using Azure OpenAI embeddings.

## Generating a Report
- Run the script:
  ```
  python scripts/generate_chromadb_report.py
  ```
- The script will:
  - Print the total number of selectors in the collection.
  - Query the database for similar selectors based on a sample query.
  - Print the top 5 results with similarity scores.
  - Save the same report to `reports/chromadb_report.txt`.

## Understanding the Output
- **Document count:** Shows how many selectors are stored.
- **Top similar selectors:** Lists the most relevant selectors for your query, with similarity scores.
- **Score:** Lower scores mean higher similarity.

## Troubleshooting
- If you see errors, check:
  - ChromaDB server is running.
  - Azure OpenAI credentials and endpoint are correct.
  - The embedding function is specified for queries.

## Customization
- Change the `query_text` in the script to test other selectors.
- Adjust `n_results` to show more or fewer results.

## Next Steps
- Use these reports to validate embedding quality.
- Share results with your team for feedback.
- Integrate reporting into your agent or automation workflows.
