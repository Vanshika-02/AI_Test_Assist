import subprocess
import os

scripts = [
    "selector_embedding.py",
    "validate_chromadb.py",
    "report_chromadb_status.py",
    "test_embedding_pipeline.py",
    "embedding_logging.py",
    "generate_chromadb_report.py",
    # "check_folder_structure.py", # Uncomment if you want to include this
]

print("Running all Phase 1B scripts...\n")

for script in scripts:
    print(f"--- Running {script} ---")
    result = subprocess.run(
        ["python", script],
        cwd=os.path.dirname(__file__),
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.stderr:
        print("ERROR:", result.stderr)
    print("\n")

print("All scripts executed.")