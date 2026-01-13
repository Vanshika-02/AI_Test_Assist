"""
FastAPI Application for Test Automation Backend - CLEANED VERSION
"""
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from pathlib import Path
from datetime import timezone
import logging
import re  # Add this import
import json
from openai import AzureOpenAI
from fastapi import Query
from config_loader import load_config, get_azure_client
from fastapi import BackgroundTasks
from fastapi import Body

from pydantic import BaseModel
from typing import List, Optional
from config import settings
from utils import setup_logging
from database import engine, get_db, Base, SessionLocal
from models import Ticket, TestExecution, ExecutionStep
from services import TestExecutionService
from jira_api import router as jira_router  # 🟢 ADD THIS LINE
from typing import Optional
import os
import requests
import subprocess
from dotenv import load_dotenv
from selector_feedback import router as selector_feedback_router
from models import Base

load_dotenv()
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")

# Setup logging
logger = setup_logging(settings.log_level)
logger.info("Starting Test Automation API...")

# Create all tables
Base.metadata.create_all(bind=engine)
logger.info("Database tables verified")
print("EXTERNAL_PROJECT_PATH =", os.getenv("EXTERNAL_PROJECT_PATH"))

# ============================================================================
# INITIALIZE FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Test Automation API",
    description="AI-Powered Vision-Based Test Automation Backend",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

azure_client = AzureOpenAI(
    api_key=settings.azure_openai_api_key,
    api_version=settings.azure_openai_api_version,
    azure_endpoint=settings.azure_openai_endpoint
)

PENDING_DIR = r"C:\Idea Projects\AI_Test_Assist\insights\pending"

class Feedback(BaseModel):
    step: str
    selector: str
    ticket_id: str
    step_number: int

# def generate_embedding(text: str):
#     # Dummy embedding, replace with actual model
#     return [0.1, 0.2, 0.3]


# def generate_embedding(text: str):
#     response = azure_client.embeddings.create(
#         input=text,
#         model=settings.azure_openai_embedding_model
#     )
#     return response.data[0].embedding  # This will be a list of 1536 floats

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    # allow_origins=["*"],  # In production, specify exact origins
    allow_origins=["http://localhost:4200"],  # Angular dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 🟢 INCLUDE JIRA ROUTER
app.include_router(jira_router)
app.include_router(selector_feedback_router)

# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

@app.get("/")
def read_root():
    """Root endpoint - API health check"""
    return {
        "message": "Test Automation API is running!",
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }




# ============================================================================
# CORE TEST EXECUTION ENDPOINTS
# ============================================================================

# @app.post("/api/execute-test")
# async def execute_test(
#     ticket_id: str,
#     background_tasks: BackgroundTasks,
#     db: Session = Depends(get_db)
# ):
#     """
#     Execute test for a ticket

#     Query Params:
#         - ticket_id: JIRA ticket ID (e.g., RBPLCD-8835)

#     Returns:
#         {
#             "execution_id": "exec_RBPLCD-8835_20251120_120000",
#             "ticket_id": "RBPLCD-8835",
#             "status": "pending",
#             "message": "Test execution started"
#         }
#     """
#     try:
#         logger.info(f"📥 Received test execution request for ticket: {ticket_id}")

#         # Validate ticket exists
#         ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
#         if not ticket:
#             raise HTTPException(
#                 status_code=404,
#                 detail=f"Ticket '{ticket_id}' not found. Please upload the ticket first."
#             )

#         # Create execution record
#         service = TestExecutionService(db)
#         execution = service.create_execution_record(
#             ticket_id=ticket_id,
#             project_id=ticket.project_id
#         )

#         logger.info(f"✅ Created execution: {execution.execution_id}")

#         # Start background task
#         background_tasks.add_task(
#             execute_test_in_background,
#             execution_id=execution.execution_id,
#             ticket_id=ticket_id,
#             project_id=ticket.project_id
#         )

#         return {
#             "execution_id": execution.execution_id,
#             "ticket_id": ticket_id,
#             "status": "pending",
#             "message": "Test execution started"
#         }

#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"❌ Error starting execution: {e}", exc_info=True)
#         raise HTTPException(status_code=500, detail=str(e))







# @app.post("/api/execute-test")
# async def execute_test(
#     ticket_id: str,
#     background_tasks: BackgroundTasks,
#     db: Session = Depends(get_db)
# ):
#     """
#     Fetch ticket from Jira and run Playwright test.
#     """
#     try:
#         logger.info(f"📥 Received test execution request for ticket: {ticket_id}")

#         # Fetch ticket from Jira
#         url = f"{JIRA_BASE_URL}/rest/api/2/issue/{ticket_id}"
#         headers = {
#             "Authorization": f"Bearer {JIRA_API_TOKEN}",
#             "Accept": "application/json"
#         }
#         response = requests.get(url, headers=headers, timeout=10)
#         if response.status_code != 200:
#             raise HTTPException(status_code=404, detail=f"Failed to fetch Jira ticket: {response.text}")

#         jira_data = response.json()
#         fields = jira_data.get("fields", {})
#         summary = fields.get("summary", "")
#         description = fields.get("description", "")
#         project_id = None

#         # Start Playwright test as a background task
#         # background_tasks.add_task(run_playwright_test, ticket_id, summary, description)

#         # return {
#         #     "ticket_id": ticket_id,
#         #     "status": "pending",
#         #     "message": "Playwright test execution started"
#         # }

# # Create execution record
#         service = TestExecutionService(db)
#         execution = service.create_execution_record(
#             ticket_id=ticket_id,
#             # project_id=ticket.project_id
#             project_id=None # Since we don't have a local ticket record
#         )

#         logger.info(f"✅ Created execution: {execution.execution_id}")

#          # Start background task
#         # background_tasks.add_task(
#         #     execute_test_in_background,
#         #     execution_id=execution.execution_id,
#         #     ticket_id=ticket_id,
#         #     project_id=ticket.project_id
#         # )
#         background_tasks.add_task(
#             execute_test_in_background,
#             execution.execution_id,
#             ticket_id,
#             project_id
#         )

#         return {
#             "execution_id": execution.execution_id,
#             "ticket_id": ticket_id,
#             "status": "pending",
#             "message": "Test execution started"
#         }


#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"❌ Error starting execution: {e}", exc_info=True)
#         raise HTTPException(status_code=500, detail=str(e))







@app.post("/api/execute-test")
async def execute_test(
    ticket_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Fetch ticket from Jira (not from local DB) and run the same Playwright test.
    """

     # 🔥 ADD THIS AT THE VERY TOP
    print(f"🔥🔥🔥 ENDPOINT CALLED: /api/execute-test with ticket_id={ticket_id}")
    logger.info(f"🔥🔥🔥 ENDPOINT CALLED: /api/execute-test with ticket_id={ticket_id}")

    try:
        logger.info(f"📥 Fetching ticket from Jira: {ticket_id}")

        # Fetch ticket from Jira instead of local database
        url = f"{JIRA_BASE_URL}/rest/api/2/issue/{ticket_id}"
        headers = {
            "Authorization": f"Bearer {JIRA_API_TOKEN}",
            "Accept": "application/json"
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            raise HTTPException(
                status_code=404,
                detail=f"Failed to fetch Jira ticket '{ticket_id}': {response.text}"
            )

        jira_data = response.json()
        fields = jira_data.get("fields", {})
        summary = fields.get("summary", "")
        description = fields.get("description", "")

        logger.info(f"✅ Fetched from Jira: {summary}")

        # Create execution record (optional - can be removed if you don't want ANY database)
        service = TestExecutionService(db)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        execution_id = f"exec_{ticket_id}_{timestamp}"

        # If you removed the foreign key constraint, this will work:
        execution = TestExecution(
            execution_id=execution_id,
            ticket_id=ticket_id,
            project_id=None,  # No local project
            status="pending",
            overall_status="UNKNOWN",
            started_at=datetime.now()
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)

        logger.info(f"✅ Created execution: {execution.execution_id}")

        # Use your EXISTING background task (same Playwright execution)
        background_tasks.add_task(
            execute_test_in_background,
            execution_id=execution.execution_id,
            ticket_id=ticket_id,
            project_id=None  # Pass None since no local project
        )

        return {
            "execution_id": execution.execution_id,
            "ticket_id": ticket_id,
            "status": "pending",
            "message": f"Test execution started for: {summary}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error starting execution: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))






# Add this to your main.py after the execute_test endpoint

# ============================================================================
# RERUN TEST EXECUTION ENDPOINT
# ============================================================================

@app.post("/api/rerun-test")
async def rerun_test(
    ticket_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Rerun test for a ticket using the latest generated script

    Query Params:
        - ticket_id: JIRA ticket ID (e.g., RBPLCD-8835)

    Returns:
        {
            "execution_id": "rerun_RBPLCD-8835_20251126_120000",
            "ticket_id": "RBPLCD-8835",
            "status": "pending",
            "script_path": "path/to/script.py",
            "message": "Test rerun started"
        }
    """
    try:
        logger.info(f"📥 Received rerun request for ticket: {ticket_id}")

        # # Validate ticket exists
        # ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
        # if not ticket:
        #     raise HTTPException(
        #         status_code=404,
        #         detail=f"Ticket '{ticket_id}' not found. Please upload the ticket first."
        #     )


        # REMOVE ticket DB check
        # ticket = None
        project_id = None


        # Find the latest generated script for this ticket
        external_path = Path(settings.external_project_path)
        scripts_folder = external_path / "Generated_Scripts"

        if not scripts_folder.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Scripts folder not found: {scripts_folder}"
            )

        # Find all scripts matching the ticket_id pattern
        script_pattern = f"*{ticket_id}*.py"
        matching_scripts = list(scripts_folder.glob(script_pattern))

        if not matching_scripts:
            raise HTTPException(
                status_code=404,
                detail=f"No generated script found for ticket '{ticket_id}'. Please run the test first."
            )

        # Get the latest script by modification time
        latest_script = max(matching_scripts, key=lambda p: p.stat().st_mtime)

        logger.info(f"📜 Found latest script: {latest_script.name}")

        # Create execution record for rerun
        service = TestExecutionService(db)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        execution_id = f"rerun_{ticket_id}_{timestamp}"

        execution = TestExecution(
            execution_id=execution_id,
            ticket_id=ticket_id,
            # project_id=ticket.project_id,
            project_id=project_id,
            status="pending",
            overall_status="UNKNOWN",
            started_at=datetime.now()
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)

        logger.info(f"✅ Created rerun execution: {execution.execution_id}")

        # Start background task for rerun
        background_tasks.add_task(
            rerun_test_in_background,
            execution_id=execution.execution_id,
            ticket_id=ticket_id,
            script_path=str(latest_script),
            # project_id=ticket.project_id
            project_id=project_id
        )

        return {
            "execution_id": execution.execution_id,
            "ticket_id": ticket_id,
            "status": "pending",
            "script_path": str(latest_script),
            "message": f"Test rerun started using script: {latest_script.name}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error starting rerun: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# RERUN BACKGROUND TASK
# ============================================================================

def rerun_test_in_background(
    execution_id: str,
    ticket_id: str,
    script_path: str,
    project_id: int
):
    """
    Background task to rerun test by executing the generated script directly
    Similar to calling python plcd_taseq.py
    """
    import subprocess
    import re

    db = SessionLocal()
    service = TestExecutionService(db)

    logger.info("="*70)
    logger.info(f"🔄 RERUN TASK STARTED")
    logger.info(f"   Execution ID: {execution_id}")
    logger.info(f"   Ticket ID: {ticket_id}")
    logger.info(f"   Script: {script_path}")
    logger.info(f"   Started at: {datetime.now().isoformat()}")
    logger.info("="*70)

    try:
        # Update status to running
        execution = db.query(TestExecution).filter(
            TestExecution.execution_id == execution_id
        ).first()
        execution.status = "running"
        db.commit()
        logger.info("✅ Status updated to 'running'")

        # Path to external project
        external_project_path = Path(settings.external_project_path)

        # Find Python executable
        python_exe = None
        venv_paths = [
            external_project_path / "venv" / "Scripts" / "python.exe",  # Windows
            external_project_path / "venv" / "bin" / "python",  # Linux/Mac
        ]

        for venv_path in venv_paths:
            if venv_path.exists():
                python_exe = str(venv_path)
                logger.info(f"✅ Found Python: {python_exe}")
                break

        if not python_exe:
            # Fallback to system Python
            import shutil
            python_exe = shutil.which("python") or shutil.which("python3")
            if not python_exe:
                raise FileNotFoundError("Python executable not found")
            logger.info(f"⚠️  Using system Python: {python_exe}")

        # Execute the script
        # logger.info(f"🏃 Executing script: {script_path}")

        # result = subprocess.run(
        #     [python_exe, script_path],
        #     cwd=str(external_project_path),
        #     capture_output=True,
        #     text=True,
        #     timeout=600  # 10 minutes timeout
        # )

        # logger.info(f"📤 Script execution completed with return code: {result.returncode}")

        # # Log output
        # if result.stdout:
        #     logger.info(f"STDOUT:\n{result.stdout[:1000]}")  # First 1000 chars
        # if result.stderr:
        #     logger.warning(f"STDERR:\n{result.stderr[:1000]}")
        logger.info(f"🏃 [RERUN_BG] About to execute script: {script_path}")
        result = subprocess.run(
            [python_exe, script_path],
            cwd=str(external_project_path),
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes timeout
        )        
        logger.info(f"🏃 [RERUN_BG] Script execution completed with return code: {result.returncode}")
        if result.stdout:
            logger.info(f"🏃 [RERUN_BG] STDOUT:\n{result.stdout[:1000]}")
        if result.stderr:
            logger.warning(f"🏃 [RERUN_BG] STDERR:\n{result.stderr[:1000]}")
        # Parse results from output or find generated files
        # Look for the latest report/video files
        reports_folder = external_project_path / "Reports"
        videos_folder = external_project_path / "Videos"

        # Find latest report for this ticket
        report_path = None
        if reports_folder.exists():
            reports = sorted(
                reports_folder.glob(f"*{ticket_id}*.html"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            if reports:
                report_path = str(reports[0])
                logger.info(f"📄 Found report: {reports[0].name}")

        # Find latest video (videos may not have ticket_id in name)
        video_path = None
        if videos_folder.exists():
            videos = sorted(
                videos_folder.glob("*.webm"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            if videos:
                video_path = str(videos[0])
                logger.info(f"🎥 Found video: {videos[0].name}")

        # Parse overall status from report if available
        overall_status = "UNKNOWN"
        if report_path and Path(report_path).exists():
            try:
                with open(report_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()

                # Try multiple patterns to find status
                patterns = [
                    r'<h2[^>]*>\s*Overall\s+Status:\s*(PASSED|FAILED)\s*</h2>',
                    r'<div[^>]*class=["\']overall-status[^"\']*["\'][^>]*>\s*(PASSED|FAILED)',
                    r'Overall\s+Status:\s*<[^>]+>\s*(PASSED|FAILED)',
                ]

                for pattern in patterns:
                    match = re.search(pattern, html_content, re.IGNORECASE)
                    if match:
                        overall_status = match.group(1).upper()
                        logger.info(f"✅ Parsed overall status: {overall_status}")
                        break

                # Fallback: count PASSED/FAILED in table
                if overall_status == "UNKNOWN":
                    passed_count = len(re.findall(r'>\s*PASSED\s*<', html_content, re.IGNORECASE))
                    failed_count = len(re.findall(r'>\s*FAILED\s*<', html_content, re.IGNORECASE))
                    if failed_count > 0:
                        overall_status = "FAILED"
                    elif passed_count > 0:
                        overall_status = "PASSED"
                    logger.info(f"📊 Inferred status from counts: {overall_status} (P:{passed_count}, F:{failed_count})")

            except Exception as e:
                logger.warning(f"Could not parse report status: {e}")

        # Parse steps from report if available
        if report_path and Path(report_path).exists():
            try:
                with open(report_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()

                # Extract table rows
                table_match = re.search(r'<table[^>]*>(.*?)</table>', html_content, re.DOTALL | re.IGNORECASE)
                if table_match:
                    table_content = table_match.group(1)
                    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_content, re.DOTALL | re.IGNORECASE)

                    step_num = 1
                    for row in rows[1:]:  # Skip header row
                        cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL | re.IGNORECASE)
                        if len(cells) >= 3:
                            step_text = re.sub(r'<[^>]+>', '', cells[1]).strip()
                            status = re.sub(r'<[^>]+>', '', cells[2]).strip().upper()

                            if step_text and status in ['PASSED', 'FAILED']:
                                step = ExecutionStep(
                                    execution_id=execution_id,
                                    step_num=step_num,
                                    step_text=step_text,
                                    status=status,
                                    screenshot_path=None
                                )
                                db.add(step)
                                step_num += 1

                    db.commit()
                    logger.info(f"✅ Saved {step_num-1} steps to database")

            except Exception as e:
                logger.warning(f"Could not parse steps from report: {e}")


        # Update execution with results
        execution.status = "completed"
        execution.overall_status = overall_status
        execution.report_path = report_path
        execution.script_path = script_path
        execution.video_path = video_path
        execution.completed_at = datetime.now()
        execution.error_message = None
        db.commit()

# 🔥 ADD THIS LINE HERE
        service._generate_summary_from_db(execution_id, ticket_id)
        logger.info("="*70)
        logger.info("✅ TEST RERUN COMPLETED SUCCESSFULLY")
        logger.info(f"   Execution ID: {execution_id}")
        logger.info(f"   Overall Status: {overall_status}")
        logger.info(f"   📄 Report: {report_path or 'N/A'}")
        logger.info(f"   📜 Script: {script_path}")
        logger.info(f"   🎥 Video: {video_path or 'N/A'}")
        logger.info(f"   Completed at: {datetime.now().isoformat()}")
        logger.info("="*70)

    except subprocess.TimeoutExpired:
        error_msg = "Test execution timed out (10 minutes limit)"
        logger.error(f"❌ {error_msg}")

        execution = db.query(TestExecution).filter(
            TestExecution.execution_id == execution_id
        ).first()
        execution.status = "failed"
        execution.overall_status = "FAILED"
        execution.error_message = error_msg
        execution.completed_at = datetime.now()
        db.commit()

    except Exception as e:
        logger.error("="*70)
        logger.error(f"❌ RERUN TASK FAILED")
        logger.error(f"   Execution ID: {execution_id}")
        logger.error(f"   Error: {e}")
        logger.error(f"   Failed at: {datetime.now().isoformat()}")
        logger.error("="*70)

        error_message = str(e)[:500]

        try:
            execution = db.query(TestExecution).filter(
                TestExecution.execution_id == execution_id
            ).first()
            execution.status = "failed"
            execution.overall_status = "FAILED"
            execution.error_message = error_message
            execution.completed_at = datetime.now()
            db.commit()
            logger.info("✅ Updated execution status to 'failed' in database")
        except Exception as db_error:
            logger.error(f"❌ Could not update database with failure: {db_error}")

        import traceback
        logger.error("Full traceback:")
        logger.error(traceback.format_exc())

    finally:
        db.close()
        logger.info(f"🏁 Rerun task ended for {execution_id}")
        logger.info("")


# ============================================================================
# HELPER ENDPOINT - List Available Scripts
# ============================================================================

@app.get("/api/scripts/{ticket_id}")
def list_generated_scripts(ticket_id: str):
    """
    List all generated scripts for a ticket

    Returns:
        {
            "ticket_id": "RBPLCD-8835",
            "scripts": [
                {
                    "filename": "RBPLCD-8835_20251126_120000.py",
                    "path": "full/path/to/script.py",
                    "created": "2025-11-26T12:00:00",
                    "size": 15234
                }
            ]
        }
    """
    try:
        external_path = Path(settings.external_project_path)
        scripts_folder = external_path / "Generated_Scripts"

        if not scripts_folder.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Scripts folder not found: {scripts_folder}"
            )

        # Find all scripts for this ticket
        script_pattern = f"*{ticket_id}*.py"
        matching_scripts = list(scripts_folder.glob(script_pattern))

        scripts = []
        for script_path in sorted(matching_scripts, key=lambda p: p.stat().st_mtime, reverse=True):
            stat = script_path.stat()
            scripts.append({
                "filename": script_path.name,
                "path": str(script_path),
                "created": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "size": stat.st_size
            })

        return {
            "ticket_id": ticket_id,
            "scripts_count": len(scripts),
            "scripts": scripts
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing scripts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# @app.get("/api/execution-status/{execution_id}")
# def get_execution_status(
#     execution_id: str,
#     db: Session = Depends(get_db)
# ):
#     """
#     Get real-time execution status with progress
#     """
#     execution = db.query(TestExecution).filter(
#         TestExecution.execution_id == execution_id
#     ).first()

#     if not execution:
#         raise HTTPException(status_code=404, detail="Execution not found")

#     # Get step information
#     total_steps = db.query(ExecutionStep).filter(
#         ExecutionStep.execution_id == execution_id
#     ).count()

#     completed_steps = db.query(ExecutionStep).filter(
#         ExecutionStep.execution_id == execution_id,
#         ExecutionStep.status.in_(["PASSED", "FAILED"])
#     ).count()

#     # Calculate progress
#     progress = 0
#     message = "Initializing..."
#     current_step = None

#     if execution.status == "pending":
#         progress = 0
#         message = "Test execution queued..."
#     elif execution.status == "running":
#         if total_steps > 0:
#             progress = int((completed_steps / total_steps) * 100)

#             last_step = db.query(ExecutionStep).filter(
#                 ExecutionStep.execution_id == execution_id
#             ).order_by(ExecutionStep.step_num.desc()).first()

#             if last_step:
#                 current_step = last_step.description
#                 message = f"Executing Step {completed_steps + 1}/{total_steps}..."
#         else:
#             progress = 10
#             message = "Parsing JIRA ticket and preparing test steps..."
#     elif execution.status == "completed":
#         progress = 100
#         message = f"Test execution completed - {execution.overall_status}"
#     elif execution.status == "failed":
#         progress = 100
#         message = execution.error_message or "Test execution failed"

#     # 🆕 ADD THIS: Check if summary exists
#     summary_available = False
#     if execution.status == "completed" and execution.ticket_id:
#         external_path = Path(settings.external_project_path)
#         summary_path = external_path / "Reports" / "summaries" / f"summary_{execution.ticket_id}_latest.json"
#         summary_available = summary_path.exists()
#         logger.info(f"📊 Summary check for {execution.ticket_id}: {summary_available} (path: {summary_path})")

#     return {
#         "execution_id": execution.execution_id,
#         "ticket_id": execution.ticket_id,
#         "status": execution.status,
#         "progress": progress,
#         "overall_status": execution.overall_status,
#         "message": message,
#         "current_step": current_step,
#         "steps_completed": completed_steps,
#         "steps_total": total_steps,
#         "started_at": execution.started_at.isoformat() if execution.started_at else None,
#         "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
#         "report_path": execution.report_path,
#         "script_path": execution.script_path,
#         "video_path": execution.video_path,
#         "summary_available": summary_available  # 🆕 NEW FIELD
#     }


@app.get("/api/execution-status/{execution_id}")
def get_execution_status(
    execution_id: str,
    db: Session = Depends(get_db)
):
    """
    Get real-time execution status with progress
    """
    execution = db.query(TestExecution).filter(
        TestExecution.execution_id == execution_id
    ).first()

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    # Get step information
    total_steps = db.query(ExecutionStep).filter(
        ExecutionStep.execution_id == execution_id
    ).count()

    completed_steps = db.query(ExecutionStep).filter(
        ExecutionStep.execution_id == execution_id,
        ExecutionStep.status.in_(["PASSED", "FAILED"])
    ).count()

    # Calculate progress
    progress = 0
    message = "Initializing..."
    current_step = None

    if execution.status == "pending":
        progress = 0
        message = "Test execution queued..."
    elif execution.status == "running":
        if total_steps > 0:
            # 🔥 FIX: Better progress calculation
            progress = min(int((completed_steps / total_steps) * 90), 90)

            last_step = db.query(ExecutionStep).filter(
                ExecutionStep.execution_id == execution_id
            ).order_by(ExecutionStep.step_num.desc()).first()

            if last_step:
                current_step = last_step.description
                message = f"Executing Step {completed_steps + 1}/{total_steps}: {last_step.description[:50]}..."
            else:
                message = f"Processing steps... ({completed_steps}/{total_steps})"
        else:
            # 🔥 FIX: Show incremental progress based on time elapsed
            if execution.started_at:
                # elapsed_seconds = (datetime.utcnow() - execution.started_at).total_seconds()
                elapsed_seconds = (datetime.now() - execution.started_at).total_seconds()
                # Estimate: 60 seconds = 80% progress
                estimated_progress = min(int((elapsed_seconds / 60) * 80), 80)
                progress = max(10, estimated_progress)
                message = f"Parsing JIRA ticket and preparing test steps... ({int(elapsed_seconds)}s elapsed)"
            else:
                progress = 10
                message = "Parsing JIRA ticket and preparing test steps..."
    elif execution.status == "completed":
        progress = 100
        message = f"Test execution completed - {execution.overall_status}"
    elif execution.status == "failed":
        progress = 100
        message = execution.error_message or "Test execution failed"

    # Check if summary exists
    summary_available = False
    if execution.status == "completed" and execution.ticket_id:
        external_path = Path(settings.external_project_path)
        summary_path = external_path / "Reports" / "summaries" / f"summary_{execution.ticket_id}_latest.json"
        summary_available = summary_path.exists()
        logger.info(f"📊 Summary check for {execution.ticket_id}: {summary_available} (path: {summary_path})")

        # 🔥 ADD THIS: List what files ARE in summaries folder
        if not summary_available:
            summaries_folder = external_path / "Reports" / "summaries"
            if summaries_folder.exists():
                existing_files = list(summaries_folder.glob("*.json"))
                logger.warning(f"⚠️ Summary NOT found. Existing summaries: {[f.name for f in existing_files]}")

    return {
        "execution_id": execution.execution_id,
        "ticket_id": execution.ticket_id,  # 🔥 CRITICAL: Return ticket_id
        "status": execution.status,
        "progress": progress,
        "overall_status": execution.overall_status,
        "message": message,
        "current_step": current_step,
        "steps_completed": completed_steps,
        "steps_total": total_steps,
        "started_at": execution.started_at.isoformat() if execution.started_at else None,
        "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
        "report_path": execution.report_path,
        "script_path": execution.script_path,
        "video_path": execution.video_path,
        "summary_available": summary_available
    }


# ============================================================================
# DOWNLOAD ENDPOINTS
# ============================================================================

@app.get("/api/download-report/{execution_id}")
def download_html_report(execution_id: str, db: Session = Depends(get_db)):
    """
    Download the HTML report for a completed execution
    """
    execution = db.query(TestExecution).filter(
        TestExecution.execution_id == execution_id
    ).first()

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    if not execution.report_path:
        raise HTTPException(
            status_code=400,
            detail="Report not generated yet. Please wait for test completion."
        )

    report_path = Path(execution.report_path)

    if not report_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Report file not found at: {execution.report_path}"
        )

    logger.info(f"📥 Serving report: {report_path.name}")

    return FileResponse(
        path=str(report_path),
        media_type="text/html",
        filename=f"{execution.ticket_id}_report.html"
    )
# from pathlib import Path
# import json

# ============================================================================
# SUMMARY JSON ENDPOINTS
# ============================================================================

@app.get("/api/summary/{ticket_id}")
def get_test_summary(ticket_id: str):
    """
    Get latest JSON summary for a ticket
    Returns lightweight summary data before downloading full report

    Example: GET /api/summary/RBPLCD-8001

    Returns:
        {
            "ticket_id": "RBPLCD-8001",
            "ticket_title": "Edit teststep measurement...",
            "summary": {
                "overall_status": "PASSED",
                "total_steps": 9,
                "passed": 8,
                "execution_time": "77.7s",
                "avg_confidence": 0.90
            },
            "agent_usage": {...},
            "insights": {...},
            "artifacts": {...}
        }
    """
    try:
        # Path to external TA_AI_Project
        external_path = Path(settings.external_project_path)
        summaries_folder = external_path / "Reports" / "summaries"

        if not summaries_folder.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Summaries folder not found. Please run a test first."
            )

        # Load latest summary
        latest_summary_path = summaries_folder / f"summary_{ticket_id}_latest.json"

        if not latest_summary_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"No summary found for ticket '{ticket_id}'. Please run the test first."
            )

        with open(latest_summary_path, 'r', encoding='utf-8') as f:
            summary_data = json.load(f)

        logger.info(f"📊 Served summary for {ticket_id}")

        return summary_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/summary/{ticket_id}/{timestamp}")
def get_test_summary_by_timestamp(ticket_id: str, timestamp: str):
    """
    Get specific summary by timestamp

    Example: GET /api/summary/RBPLCD-8001/20250115_143000
    """
    try:
        external_path = Path(settings.external_project_path)
        summaries_folder = external_path / "Reports" / "summaries"

        summary_path = summaries_folder / f"summary_{ticket_id}_{timestamp}.json"

        if not summary_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Summary not found for {ticket_id} at {timestamp}"
            )

        with open(summary_path, 'r', encoding='utf-8') as f:
            summary_data = json.load(f)

        return summary_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/summaries")
def list_all_summaries(
    limit: int = 50,
    status: str = None,
    module: str = None
):
    """
    List all available test summaries with filtering

    Query params:
        - limit: Number of results (default: 50)
        - status: Filter by status (PASSED/FAILED)
        - module: Filter by module

    Example: GET /api/summaries?limit=10&status=PASSED
    """
    try:
        external_path = Path(settings.external_project_path)
        summaries_folder = external_path / "Reports" / "summaries"

        if not summaries_folder.exists():
            return {
                "count": 0,
                "summaries": []
            }

        summaries = []

        # Find all summary files (excluding _latest.json)
        for json_file in summaries_folder.glob("summary_*.json"):
            if '_latest.json' in str(json_file):
                continue

            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Apply filters
                if status and data['summary']['overall_status'] != status:
                    continue

                if module and data.get('module') != module:
                    continue

                summaries.append({
                    'ticket_id': data['ticket_id'],
                    'ticket_title': data['ticket_title'],
                    'module': data['module'],
                    'execution_date': data['execution_date'],
                    'overall_status': data['summary']['overall_status'],
                    'total_steps': data['summary']['total_steps'],
                    'passed': data['summary']['passed'],
                    'failed': data['summary']['failed'],
                    'execution_time': data['summary']['execution_time'],
                    'avg_confidence': data['summary']['avg_confidence'],
                    'status_emoji': data['insights']['status_emoji'],
                    'file_path': str(json_file)
                })

            except Exception as e:
                logger.warning(f"Could not read summary {json_file}: {e}")
                continue

        # Sort by execution date (newest first)
        summaries.sort(key=lambda x: x['execution_date'], reverse=True)

        # Apply limit
        summaries = summaries[:limit]

        return {
            "count": len(summaries),
            "summaries": summaries
        }

    except Exception as e:
        logger.error(f"Error listing summaries: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/summary-stats")
def get_summary_statistics():
    """
    Get overall statistics across all test executions

    Returns:
        {
            "total_executions": 25,
            "total_passed": 20,
            "total_failed": 5,
            "success_rate": 80.0,
            "avg_execution_time": 75.3,
            "avg_confidence": 0.87,
            "recent_executions": [...]
        }
    """
    try:
        external_path = Path(settings.external_project_path)
        summaries_folder = external_path / "Reports" / "summaries"

        if not summaries_folder.exists():
            return {
                "total_executions": 0,
                "total_passed": 0,
                "total_failed": 0,
                "success_rate": 0.0,
                "avg_execution_time": 0.0,
                "avg_confidence": 0.0,
                "recent_executions": []
            }

        summaries = []

        for json_file in summaries_folder.glob("summary_*.json"):
            if '_latest.json' in str(json_file):
                continue

            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    summaries.append(data)
            except:
                continue

        if not summaries:
            return {
                "total_executions": 0,
                "total_passed": 0,
                "total_failed": 0,
                "success_rate": 0.0,
                "avg_execution_time": 0.0,
                "avg_confidence": 0.0,
                "recent_executions": []
            }

        total_executions = len(summaries)
        total_passed = sum(1 for s in summaries if s['summary']['overall_status'] == 'PASSED')
        total_failed = sum(1 for s in summaries if s['summary']['overall_status'] == 'FAILED')

        # Calculate averages
        total_time = 0.0
        for s in summaries:
            try:
                time_str = s['summary']['execution_time'].replace('s', '')
                total_time += float(time_str)
            except:
                pass

        avg_time = total_time / total_executions if total_executions > 0 else 0.0
        avg_confidence = sum(s['summary'].get('avg_confidence', 0.0) for s in summaries) / total_executions

        # Get recent executions
        recent = sorted(summaries, key=lambda x: x['execution_date'], reverse=True)[:10]
        recent_list = [
            {
                'ticket_id': s['ticket_id'],
                'status': s['summary']['overall_status'],
                'execution_date': s['execution_date']
            }
            for s in recent
        ]

        return {
            "total_executions": total_executions,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "success_rate": round((total_passed / total_executions * 100), 1),
            "avg_execution_time": round(avg_time, 1),
            "avg_confidence": round(avg_confidence, 2),
            "recent_executions": recent_list
        }

    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# @app.post("/api/process-feedback")
# async def process_feedback(ticket_id: str):
#     import subprocess
#     external_project_path = settings.external_project_path
#     plcd_script = Path(external_project_path) / "plcd_taseq.py"
#     python_exe = str(Path(external_project_path) / "venv" / "Scripts" / "python.exe")
#     # Call plcd_taseq.py with --process-feedback argument
#     result = subprocess.run(
#         [python_exe, str(plcd_script), ticket_id, "--process-feedback"],
#         cwd=str(external_project_path),
#         capture_output=True,
#         text=True,
#         timeout=300
#     )
#     return {
#         "stdout": result.stdout,
#         "stderr": result.stderr,
#         "returncode": result.returncode
#     }

from pydantic import BaseModel
from fastapi import Query

class FeedbackProcessRequest(BaseModel):
    feedback: str

@app.post("/api/process-feedback")
async def process_feedback(
    ticket_id: str = Query(...),
    request: FeedbackProcessRequest = None
):
    import subprocess
    external_project_path = settings.external_project_path
    plcd_script = Path(external_project_path) / "plcd_taseq.py"
    python_exe = str(Path(external_project_path) / "venv" / "Scripts" / "python.exe")
    feedback_text = request.feedback if request else ""
    # Pass feedback_text as an argument to plcd_taseq.py
    result = subprocess.run(
        [python_exe, str(plcd_script), ticket_id, "--process-feedback", feedback_text],
        cwd=str(external_project_path),
        capture_output=True,
        text=True,
        timeout=300
    )
    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode
    }


class RerunFeedbackRequest(BaseModel):
    ticket_id: str
    feedback_text: str = ""
    
# @app.post("/api/rerun-with-feedback")
# async def rerun_with_feedback(
#     # ticket_id: str,
#     # feedback_text: str = "",
    
#     # ticket_id = requests.request.ticket_id,
#     # feedback_text = requests.request.feedback_text,
#     # background_tasks: BackgroundTasks = None
#     request: RerunFeedbackRequest,
#     background_tasks: BackgroundTasks = None
# ):
#     """
#     Trigger plcd_taseq.py feedback loop for rerun with updated selectors.
#     """
#     ticket_id = request.ticket_id
#     feedback_text = request.feedback_text
#     logger.info(f"🔁 [API] Rerun with feedback called for ticket: {ticket_id}, feedback: {feedback_text}")
#     import subprocess
#     external_project_path = settings.external_project_path
#     plcd_script = Path(external_project_path) / "plcd_taseq.py"
#     python_exe = str(Path(external_project_path) / "venv" / "Scripts" / "python.exe")

#     def run_feedback_loop():
#         subprocess.run(
#             [python_exe, str(plcd_script), ticket_id, "--process-feedback", feedback_text],
#             cwd=str(external_project_path),
#             capture_output=True,
#             text=True,
#             timeout=600
#         )

#     if background_tasks:
#         background_tasks.add_task(run_feedback_loop)
#         return {"status": "started"}
#     else:
#         run_feedback_loop()
#         return {"status": "completed"}
    

# @app.post("/api/rerun-with-feedback")
# async def rerun_with_feedback(
#     request: RerunFeedbackRequest,
#     background_tasks: BackgroundTasks = None,
#     db: Session = Depends(get_db)
# ):
#     """
#     Process feedback and then rerun the test for the ticket.
#     """
#     ticket_id = request.ticket_id
#     feedback_text = request.feedback_text
#     logger.info(f"🔁 [API] Rerun with feedback called for ticket: {ticket_id}, feedback: {feedback_text}")

#     external_project_path = settings.external_project_path
#     plcd_script = Path(external_project_path) / "plcd_taseq.py"
#     python_exe = str(Path(external_project_path) / "venv" / "Scripts" / "python.exe")

@app.post("/api/rerun-with-feedback")
async def rerun_with_feedback(
    request: RerunFeedbackRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    ticket_id = request.ticket_id
    feedback_text = request.feedback_text

    logger.info(f"Rerun with feedback for {ticket_id}")

    # =====================================================
    # 1️⃣ CREATE EXECUTION FIRST (VERY IMPORTANT)
    # =====================================================
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    execution_id = f"rerun_{ticket_id}_{timestamp}"

    execution = TestExecution(
        execution_id=execution_id,
        ticket_id=ticket_id,
        project_id=None,
        status="pending",
        overall_status="UNKNOWN",
        started_at=datetime.now()
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)

    # =====================================================
    # 2️⃣ ADD BACKGROUND TASK
    # =====================================================
    background_tasks.add_task(
        process_feedback_and_rerun,
        execution_id,
        ticket_id,
        feedback_text
    )

    # =====================================================
    # 3️⃣ RETURN execution_id TO FRONTEND 🔥
    # =====================================================
    return {
        "execution_id": execution_id,
        "status": "started"
    }


    # def process_feedback_and_rerun():
    # def process_feedback_and_rerun(execution_id: str, ticket_id: str, feedback_text: str):

    #     # 1. Process feedback
    #     subprocess.run(
    #         [python_exe, str(plcd_script), ticket_id, "--process-feedback", feedback_text],
    #         cwd=str(external_project_path),
    #         capture_output=True,
    #         text=True,
    #         timeout=600
    #     )
    #     # 2. Find latest script for rerun
    #     scripts_folder = Path(external_project_path) / "Generated_Scripts"
    #     matching_scripts = list(scripts_folder.glob(f"*{ticket_id}*.py"))
    #     if not matching_scripts:
    #         logger.error(f"No generated script found for ticket '{ticket_id}'.")
    #         return
    #     latest_script = max(matching_scripts, key=lambda p: p.stat().st_mtime)
    #     # 3. Create new execution record for rerun
    #     service = TestExecutionService(db)
    #     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    #     execution_id = f"rerun_{ticket_id}_{timestamp}"
    #     execution = TestExecution(
    #         execution_id=execution_id,
    #         ticket_id=ticket_id,
    #         project_id=None,
    #         status="pending",
    #         overall_status="UNKNOWN",
    #         started_at=datetime.now()
    #     )
    #     db.add(execution)
    #     db.commit()
    #     db.refresh(execution)
    #     # 4. Start rerun in background
    #     rerun_test_in_background(
    #         execution_id=execution_id,
    #         ticket_id=ticket_id,
    #         script_path=str(latest_script),
    #         project_id=None
    #     )

    # if background_tasks:
    #     background_tasks.add_task(process_feedback_and_rerun)
    #     return {"status": "started"}
    # else:
    #     process_feedback_and_rerun()
    #     return {"status": "completed"}
    
    
# def process_feedback_and_rerun(
#     execution_id: str,
#     ticket_id: str,
#     feedback_text: str
# ):
#     logger.info(f"Processing feedback and rerun for {ticket_id}")

#     # =====================================================
#     # 1️⃣ APPLY FEEDBACK (UPDATE SELECTOR KB)
#     # =====================================================
#     external_project_path = settings.external_project_path
#     plcd_script = Path(external_project_path) / "plcd_taseq.py"
#     python_exe = str(Path(external_project_path) / "venv" / "Scripts" / "python.exe")
#     if not Path(python_exe).exists():
#         import shutil
#         python_exe = shutil.which("python") or shutil.which("python3")
#         if not python_exe:
#             logger.error("Python executable not found for feedback rerun.")
#             return

#     # subprocess.run(
#     #     [python_exe, str(plcd_script), ticket_id, "--process-feedback", feedback_text],
#     #     cwd=str(external_project_path),
#     #     capture_output=True,
#     #     text=True,
#     #     timeout=600
#     # )
#     # 1️⃣ APPLY FEEDBACK
#     logger.info(f"🔁 [RERUN] Running process-feedback subprocess for {ticket_id} with feedback: {feedback_text}")
#     feedback_result = subprocess.run(
#         [python_exe, str(plcd_script), ticket_id, "--process-feedback", feedback_text],
#         cwd=str(external_project_path),
#         capture_output=True,
#         text=True,
#         timeout=600
#     )
#     logger.info(f"🔁 [RERUN] process-feedback return code: {feedback_result.returncode}")
#     logger.info(f"🔁 [RERUN] STDOUT: {feedback_result.stdout[:500]}")
#     logger.info(f"🔁 [RERUN] STDERR: {feedback_result.stderr[:500]}")

#     # =====================================================
#     # 2️⃣ FIND LATEST GENERATED SCRIPT
#     # =====================================================
#     scripts_folder = Path(external_project_path) / "Generated_Scripts"
#     matching_scripts = list(scripts_folder.glob(f"*{ticket_id}*.py"))

#     if not matching_scripts:
#         logger.error(f"No generated script found for ticket '{ticket_id}'")
#         return

#     latest_script = max(matching_scripts, key=lambda p: p.stat().st_mtime)
    
#     # # 3️⃣ RUN PLAYWRIGHT (🔥 THIS WAS MISSING 🔥)
#     # result = subprocess.run(
#     #     [python_exe, str(latest_script), ticket_id, "--no-feedback"],
#     #     cwd=str(external_project_path),
#     #     capture_output=True,
#     #     text=True,
#     #     timeout=600
#     # )
#     # 3️⃣ RUN PLAYWRIGHT (RERUN)
#     # logger.info(f"🔁 [RERUN] Running Playwright rerun subprocess with script: {latest_script}")
#     # rerun_result = subprocess.run(
#     #     [python_exe, str(latest_script), ticket_id, "--no-feedback"],
#     #     cwd=str(external_project_path),
#     #     capture_output=True,
#     #     text=True,
#     #     timeout=600
#     # )

#     # logger.info("🎭 Playwright execution completed")
#     # logger.info(f"🔁 [RERUN] rerun return code: {rerun_result.returncode}")
#     # logger.info(f"🔁 [RERUN] STDOUT: {rerun_result.stdout[:500]}")
#     # logger.info(f"🔁 [RERUN] STDERR: {rerun_result.stderr[:500]}")
    
    

#     # =====================================================
#     # 3️⃣ RUN TEST AGAIN USING SAME execution_id
#     # =====================================================
#     rerun_test_in_background(
#         execution_id=execution_id,
#         ticket_id=ticket_id,
#         script_path=str(latest_script),
#         project_id=None
#     )

# def process_feedback_and_rerun(
#     execution_id: str,
#     ticket_id: str,
#     feedback_text: str
# ):
#     """
#     Process feedback and rerun test WITH PLAYWRIGHT EXECUTION
#     """
#     db = SessionLocal()
    
#     try:
#         logger.info(f"🔁 [RERUN] Starting for {execution_id}")
        
#         # 1️⃣ APPLY FEEDBACK
#         external_project_path = Path(settings.external_project_path)
#         plcd_script = external_project_path / "plcd_taseq.py"
#         python_exe = str(external_project_path / "venv" / "Scripts" / "python.exe")
        
#         if not Path(python_exe).exists():
#             import shutil
#             python_exe = shutil.which("python") or shutil.which("python3")
        
#         logger.info(f"🔁 [RERUN] Processing feedback: {feedback_text[:50]}...")
        
#         # Run feedback processing
#         feedback_result = subprocess.run(
#             [python_exe, str(plcd_script), ticket_id, "--process-feedback", feedback_text],
#             cwd=str(external_project_path),
#             capture_output=True,
#             text=True,
#             timeout=600
#         )
        
#         logger.info(f"🔁 [RERUN] Feedback processed, return code: {feedback_result.returncode}")
        
#         # 2️⃣ FIND LATEST SCRIPT
#         # scripts_folder = external_project_path / "Generated_Scripts"
#         # matching_scripts = list(scripts_folder.glob(f"*{ticket_id}*.py"))
        
#         # if not matching_scripts:
#         #     raise FileNotFoundError(f"No script found for {ticket_id}")
#         scripts_folder = external_project_path / "Generated_Scripts"
#         matching_scripts = list(scripts_folder.glob(f"*{ticket_id}*.py"))

#         if not matching_scripts:
#             logger.info(f"No script found for {ticket_id}, generating new script with feedback...")
#     # Run test generation with feedback (this should create the script)
#             result = subprocess.run(
#                 [python_exe, str(plcd_script), ticket_id, "--process-feedback", feedback_text, "--no-feedback"],
#                 cwd=str(external_project_path),
#                 capture_output=True,
#                 text=True,
#                 timeout=600
#             )
#             logger.info(f"Test generation with feedback completed, return code: {result.returncode}")
#             logger.info(f"STDOUT: {result.stdout[:500]}")
#             logger.info(f"STDERR: {result.stderr[:500]}")

#     # Now continue as usual: find the new script, run it, generate summary
#             matching_scripts = list(scripts_folder.glob(f"*{ticket_id}*.py"))
#             if not matching_scripts:
#                 logger.error(f"Still no script found after generation for ticket '{ticket_id}'")
#         # Mark as failed, return
#                 return
        
#         latest_script = max(matching_scripts, key=lambda p: p.stat().st_mtime)
#         logger.info(f"🔁 [RERUN] Using script: {latest_script.name}")
        
#         # 3️⃣ UPDATE EXECUTION TO RUNNING
#         execution = db.query(TestExecution).filter(
#             TestExecution.execution_id == execution_id
#         ).first()
        
#         if execution:
#             execution.status = "running"
#             execution.started_at = datetime.now()
#             db.commit()
#             logger.info(f"🔁 [RERUN] Status set to 'running'")
        
#         # 4️⃣ RUN PLAYWRIGHT TEST (BLOCKING)
#         logger.info(f"🔁 [RERUN] Running Playwright with updated selector...")
        
#         playwright_result = subprocess.run(
#             [python_exe, str(plcd_script), ticket_id, "--no-feedback"],
#             cwd=str(external_project_path),
#             capture_output=True,
#             text=True,
#             timeout=600
#         )
        
#         logger.info(f"🔁 [RERUN] Playwright completed, return code: {playwright_result.returncode}")
        
#         # 5️⃣ FIND NEW ARTIFACTS
#         report_path = None
#         script_path = str(latest_script)
#         video_path = None
#         overall_status = "UNKNOWN"
        
#         reports_folder = external_project_path / "Reports"
#         if reports_folder.exists():
#             reports = sorted(
#                 reports_folder.glob(f"*{ticket_id}*.html"),
#                 key=lambda p: p.stat().st_mtime,
#                 reverse=True
#             )
#             if reports:
#                 report_path = str(reports[0])
#                 logger.info(f"🔁 [RERUN] Found new report: {reports[0].name}")
        
#         videos_folder = external_project_path / "Videos"
#         if videos_folder.exists():
#             videos = sorted(
#                 videos_folder.glob("*.webm"),
#                 key=lambda p: p.stat().st_mtime,
#                 reverse=True
#             )
#             if videos:
#                 video_path = str(videos[0])
        
#         # 6️⃣ PARSE STATUS FROM REPORT
#         if report_path and Path(report_path).exists():
#             try:
#                 with open(report_path, 'r', encoding='utf-8') as f:
#                     html = f.read()
                
#                 match = re.search(r'<div[^>]*class=["\'][^"\']*status-(PASSED|FAILED)[^"\']*["\'][^>]*>\s*(PASSED|FAILED)\s*</div>', html, re.IGNORECASE)
#                 if match:
#                     overall_status = match.group(2).upper()
#                 else:
#                     passed = len(re.findall(r'>\s*PASSED\s*<', html, re.IGNORECASE))
#                     failed = len(re.findall(r'>\s*FAILED\s*<', html, re.IGNORECASE))
#                     overall_status = "FAILED" if failed > 0 else ("PASSED" if passed > 0 else "UNKNOWN")
                
#                 logger.info(f"🔁 [RERUN] Status: {overall_status}")
#             except Exception as e:
#                 logger.warning(f"Could not parse status: {e}")
        
#         # 7️⃣ LOAD STEPS FROM JSON
#         steps_file = external_project_path / "Reports" / "steps" / f"steps_{ticket_id}.json"
#         steps_saved = False
        
#         if steps_file.exists():
#             with open(steps_file, "r", encoding="utf-8") as f:
#                 raw_steps = json.load(f)
            
#             logger.info(f"🔁 [RERUN] Loaded {len(raw_steps)} steps from JSON")
            
#             # Delete old steps
#             db.query(ExecutionStep).filter(
#                 ExecutionStep.execution_id == execution_id
#             ).delete()
#             db.commit()
            
#             # Save new steps
#             for step in raw_steps:
#                 db.add(ExecutionStep(
#                     execution_id=execution_id,
#                     step_num=step.get("step_number"),
#                     step_text=step.get("step_text"),
#                     status=step.get("status"),
#                     selector_used=step.get("selector", ""),
#                     agent_used=step.get("agent_used", ""),
#                     confidence=step.get("confidence", 0.0),
#                     action_type=step.get("action_type", ""),
#                     screenshot_path=None
#                 ))
            
#             db.commit()
#             steps_saved = True
#             logger.info(f"🔁 [RERUN] Saved {len(raw_steps)} steps to DB")
        
#         # 8️⃣ UPDATE EXECUTION RECORD
#         final_status = "completed" if report_path else "failed"
        
#         db.refresh(execution)
#         execution.status = final_status
#         execution.overall_status = overall_status
#         execution.completed_at = datetime.now()
#         execution.report_path = report_path
#         execution.script_path = script_path
#         execution.video_path = video_path
#         execution.error_message = None if report_path else "No report generated"
#         db.commit()
        
#         logger.info(f"🔁 [RERUN] Execution marked as '{final_status}'")
        
#         # 9️⃣ GENERATE SUMMARY
#         if steps_saved:
#             service = TestExecutionService(db)
#             service._generate_summary_from_db(execution_id, ticket_id)
#             logger.info(f"🔁 [RERUN] Summary generated")
        
#         logger.info(f"🔁 [RERUN] COMPLETED for {execution_id}")
        
#     except Exception as e:
#         logger.error(f"❌ [RERUN] Failed: {e}")
#         import traceback
#         logger.error(traceback.format_exc())
        
#         # Mark as failed
#         try:
#             execution = db.query(TestExecution).filter(
#                 TestExecution.execution_id == execution_id
#             ).first()
#             if execution:
#                 execution.status = "failed"
#                 execution.overall_status = "FAILED"
#                 execution.completed_at = datetime.now()
#                 execution.error_message = str(e)[:500]
#                 db.commit()
#         except:
#             pass
    
#     finally:
#         db.close()

def process_feedback_and_rerun(
    execution_id: str,
    ticket_id: str,
    feedback_text: str
):
    """
    Always generate a new script with feedback, then run Playwright, then update summary.
    """
    db = SessionLocal()
    try:
        logger.info(f"🔁 [RERUN] Starting for {execution_id}")

        external_project_path = Path(settings.external_project_path)
        plcd_script = external_project_path / "plcd_taseq.py"
        python_exe = str(external_project_path / "venv" / "Scripts" / "python.exe")
        if not Path(python_exe).exists():
            import shutil
            python_exe = shutil.which("python") or shutil.which("python3")

        # 1️⃣ Always generate a new script with feedback
        logger.info(f"🔁 [RERUN] Generating new script with feedback: {feedback_text[:50]}...")
        feedback_result = subprocess.run(
            [python_exe, str(plcd_script), ticket_id, "--process-feedback", feedback_text, "--no-feedback"],
            cwd=str(external_project_path),
            capture_output=True,
            text=True,
            timeout=600
        )
        logger.info(f"🔁 [RERUN] Script generation return code: {feedback_result.returncode}")
        logger.info(f"STDOUT: {feedback_result.stdout[:500]}")
        logger.info(f"STDERR: {feedback_result.stderr[:500]}")

        # 2️⃣ Find the newly generated script
        scripts_folder = external_project_path / "Generated_Scripts"
        matching_scripts = list(scripts_folder.glob(f"*{ticket_id}*.py"))
        if not matching_scripts:
            logger.error(f"❌ [RERUN] Script generation failed for ticket '{ticket_id}'")
            return

        latest_script = max(matching_scripts, key=lambda p: p.stat().st_mtime)
        logger.info(f"🔁 [RERUN] Using script: {latest_script.name}")

        # 3️⃣ Mark execution as running
        execution = db.query(TestExecution).filter(
            TestExecution.execution_id == execution_id
        ).first()
        if execution:
            execution.status = "running"
            execution.started_at = datetime.now()
            db.commit()
            logger.info(f"🔁 [RERUN] Status set to 'running'")

        # 4️⃣ Run Playwright using the new script
        logger.info(f"🔁 [RERUN] Running Playwright with updated selector...")
        playwright_result = subprocess.run(
            [python_exe, str(latest_script), ticket_id, "--no-feedback"],
            cwd=str(external_project_path),
            capture_output=True,
            text=True,
            timeout=600
        )
        logger.info(f"🔁 [RERUN] Playwright completed, return code: {playwright_result.returncode}")
        logger.info(f"STDOUT: {playwright_result.stdout[:500]}")
        logger.info(f"STDERR: {playwright_result.stderr[:500]}")

        # 5️⃣ Find new artifacts and update DB
        report_path = None
        script_path = str(latest_script)
        video_path = None
        overall_status = "UNKNOWN"

        reports_folder = external_project_path / "Reports"
        if reports_folder.exists():
            reports = sorted(
                reports_folder.glob(f"*{ticket_id}*.html"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            if reports:
                report_path = str(reports[0])
                logger.info(f"🔁 [RERUN] Found new report: {reports[0].name}")

        videos_folder = external_project_path / "Videos"
        if videos_folder.exists():
            videos = sorted(
                videos_folder.glob("*.webm"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            if videos:
                video_path = str(videos[0])

        # 6️⃣ Parse status from report
        if report_path and Path(report_path).exists():
            try:
                with open(report_path, 'r', encoding='utf-8') as f:
                    html = f.read()
                match = re.search(r'<div[^>]*class=["\'][^"\']*status-(PASSED|FAILED)[^"\']*["\'][^>]*>\s*(PASSED|FAILED)\s*</div>', html, re.IGNORECASE)
                if match:
                    overall_status = match.group(2).upper()
                else:
                    passed = len(re.findall(r'>\s*PASSED\s*<', html, re.IGNORECASE))
                    failed = len(re.findall(r'>\s*FAILED\s*<', html, re.IGNORECASE))
                    overall_status = "FAILED" if failed > 0 else ("PASSED" if passed > 0 else "UNKNOWN")
                logger.info(f"🔁 [RERUN] Status: {overall_status}")
            except Exception as e:
                logger.warning(f"Could not parse status: {e}")

        # 7️⃣ Load steps from JSON
        steps_file = external_project_path / "Reports" / "steps" / f"steps_{ticket_id}.json"
        steps_saved = False

        if steps_file.exists():
            with open(steps_file, "r", encoding="utf-8") as f:
                raw_steps = json.load(f)
            logger.info(f"🔁 [RERUN] Loaded {len(raw_steps)} steps from JSON")
            db.query(ExecutionStep).filter(
                ExecutionStep.execution_id == execution_id
            ).delete()
            db.commit()
            for step in raw_steps:
                db.add(ExecutionStep(
                    execution_id=execution_id,
                    step_num=step.get("step_number"),
                    step_text=step.get("step_text"),
                    status=step.get("status"),
                    selector_used=step.get("selector", ""),
                    agent_used=step.get("agent_used", ""),
                    confidence=step.get("confidence", 0.0),
                    action_type=step.get("action_type", ""),
                    screenshot_path=None
                ))
            db.commit()
            steps_saved = True
            logger.info(f"🔁 [RERUN] Saved {len(raw_steps)} steps to DB")

        # 8️⃣ Update execution record
        final_status = "completed" if report_path else "failed"
        db.refresh(execution)
        execution.status = final_status
        execution.overall_status = overall_status
        execution.completed_at = datetime.now()
        execution.report_path = report_path
        execution.script_path = script_path
        execution.video_path = video_path
        execution.error_message = None if report_path else "No report generated"
        db.commit()
        logger.info(f"🔁 [RERUN] Execution marked as '{final_status}'")

        # 9️⃣ Generate summary
        if steps_saved:
            service = TestExecutionService(db)
            service._generate_summary_from_db(execution_id, ticket_id)
            logger.info(f"🔁 [RERUN] Summary generated")

        logger.info(f"🔁 [RERUN] COMPLETED for {execution_id}")

    except Exception as e:
        logger.error(f"❌ [RERUN] Failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        try:
            execution = db.query(TestExecution).filter(
                TestExecution.execution_id == execution_id
            ).first()
            if execution:
                execution.status = "failed"
                execution.overall_status = "FAILED"
                execution.completed_at = datetime.now()
                execution.error_message = str(e)[:500]
                db.commit()
        except:
            pass
    finally:
        db.close()

    
@app.post("/api/feedback")
async def receive_feedback(feedback: Feedback):
    embedding = generate_embedding(feedback.selector)
    data = {
        "step": feedback.step,
        "selector": feedback.selector,
        "confidence": 0.95,
        "category": "failed",
        "module": "Teststep",
        "context": {
            "module": "Teststep",
            "action_type": "click",
            "sequential_context": {
                "previous_steps": [],
                "last_successful_action": None,
                "last_selector_used": None,
                "page_state_before_failure": "",
                "current_module": "Teststep"
            }
        },
        "metadata": {
            "ticket_id": feedback.ticket_id,
            "step_number": feedback.step_number,
            "timestamp": datetime.now().isoformat(),
            "issue_description": "selector not found",
            "reasoning": "",
            "browser": "edge",
            "tester_id": "manual_feedback",
            "source": "tester_feedback",
            "feedback_type": "failed"
        },
        "embedding": embedding,
        "storage_metadata": {
            "saved_at": datetime.now().isoformat(),
            "file_path": "",  # Fill in if needed
            "storage_type": "failed",
            "embedded": True
        }
    }
    os.makedirs(PENDING_DIR, exist_ok=True)
    filename = f"{feedback.ticket_id}_step{feedback.step_number}_{int(datetime.now().timestamp())}.json"
    filepath = os.path.join(PENDING_DIR, filename)
    data["storage_metadata"]["file_path"] = filepath
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    return {"status": "success", "file": filename}

# ============================================================================
# HELPER: Check if summary exists
# ============================================================================

@app.get("/api/summary-exists/{ticket_id}")
def check_summary_exists(ticket_id: str):
    """
    Quick check if summary exists for a ticket
    Useful for frontend to decide whether to show summary preview

    Returns:
        {
            "exists": true,
            "ticket_id": "RBPLCD-8001",
            "latest_execution": "2025-11-24 13:53:02"
        }
    """
    try:
        external_path = Path(settings.external_project_path)
        summaries_folder = external_path / "Reports" / "summaries"
        latest_summary_path = summaries_folder / f"summary_{ticket_id}_latest.json"

        if not latest_summary_path.exists():
            return {
                "exists": False,
                "ticket_id": ticket_id,
                "latest_execution": None
            }

        with open(latest_summary_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return {
            "exists": True,
            "ticket_id": ticket_id,
            "latest_execution": data.get('execution_date'),
            "overall_status": data['summary']['overall_status'],
            "has_report": data['artifacts']['has_report'],
            "has_video": data['artifacts']['has_video']
        }

    except Exception as e:
        logger.error(f"Error checking summary: {e}")
        return {
            "exists": False,
            "ticket_id": ticket_id,
            "latest_execution": None
        }

@app.get("/api/download-script/{execution_id}")
def download_playwright_script(execution_id: str, db: Session = Depends(get_db)):
    """
    Download the Playwright script for a completed execution
    """
    execution = db.query(TestExecution).filter(
        TestExecution.execution_id == execution_id
    ).first()

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    if not execution.script_path:
        raise HTTPException(
            status_code=400,
            detail="Script not generated yet. Please wait for test completion."
        )

    script_path = Path(execution.script_path)

    if not script_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Script file not found at: {execution.script_path}"
        )

    logger.info(f"📥 Serving script: {script_path.name}")

    return FileResponse(
        path=str(script_path),
        media_type="text/x-python",
        filename=f"{execution.ticket_id}_script.py"
    )


@app.get("/api/download-video/{execution_id}")
def download_test_video(execution_id: str, db: Session = Depends(get_db)):
    """
    Download the test execution video for a completed execution
    """
    execution = db.query(TestExecution).filter(
        TestExecution.execution_id == execution_id
    ).first()

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    if not execution.video_path:
        raise HTTPException(
            status_code=400,
            detail="Video not generated yet. Please wait for test completion."
        )

    video_path = Path(execution.video_path)

    if not video_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Video file not found at: {execution.video_path}"
        )

    logger.info(f"📥 Serving video: {video_path.name}")

    return FileResponse(
        path=str(video_path),
        media_type="video/webm",
        filename=f"{execution.ticket_id}_video.webm"
    )

# Add these debug endpoints to your main.py after the other endpoints

@app.get("/api/debug/execution-logs/{execution_id}")
def get_execution_logs(execution_id: str):
    """
    Get recent log entries for an execution (for debugging)
    """
    try:
        log_file = Path("logs") / "app.log"
        if not log_file.exists():
            return {"logs": "Log file not found", "log_path": str(log_file)}

        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Find lines related to this execution
        relevant_lines = []
        for line in lines:
            if execution_id in line:
                relevant_lines.append(line.rstrip())

        # Get last 100 lines
        return {
            "execution_id": execution_id,
            "total_lines": len(relevant_lines),
            "logs": '\n'.join(relevant_lines[-100:])
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/debug/artifacts/{ticket_id}")
def debug_artifacts(ticket_id: str):
    """
    Debug endpoint to check what artifact files exist for a ticket
    """
    try:
        from config import settings

        external_path = Path(settings.external_project_path)

        if not external_path.exists():
            return {"error": f"External project path not found: {external_path}"}

        # Search all artifact folders
        reports_folder = external_path / "Reports"
        scripts_folder = external_path / "Generated_Scripts"
        videos_folder = external_path / "Videos"

        def get_file_info(path: Path):
            """Get file info with timestamp"""
            stat = path.stat()
            return {
                "name": path.name,
                "path": str(path),
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_mtime).isoformat()
            }

        # Find all files for this ticket
        reports = []
        if reports_folder.exists():
            reports = [
                get_file_info(p)
                for p in sorted(
                    reports_folder.glob(f"*{ticket_id}*.html"),
                    key=lambda x: x.stat().st_mtime,
                    reverse=True
                )
            ]

        scripts = []
        if scripts_folder.exists():
            scripts = [
                get_file_info(p)
                for p in sorted(
                    scripts_folder.glob(f"*{ticket_id}*.py"),
                    key=lambda x: x.stat().st_mtime,
                    reverse=True
                )
            ]

        videos = []
        if videos_folder.exists():
            # Get last 5 videos
            videos = [
                get_file_info(p)
                for p in sorted(
                    videos_folder.glob("*.webm"),
                    key=lambda x: x.stat().st_mtime,
                    reverse=True
                )[:5]
            ]

        return {
            "ticket_id": ticket_id,
            "external_path": str(external_path),
            "reports": reports,
            "scripts": scripts,
            "recent_videos": videos,
            "current_time": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Debug artifacts error: {e}", exc_info=True)
        return {"error": str(e)}


# @app.get("/api/debug/parse-report/{execution_id}")
# def debug_parse_report(execution_id: str, db: Session = Depends(get_db)):
#     """
#     Debug endpoint to show what we're parsing from the report
#     """
#     try:
#         execution = db.query(TestExecution).filter(
#             TestExecution.execution_id == execution_id
#         ).first()

#         if not execution or not execution.report_path:
#             return {"error": "No report path found"}

#         report_path = Path(execution.report_path)

#         if not report_path.exists():
#             return {"error": f"Report not found: {report_path}"}

#         with open(report_path, 'r', encoding='utf-8') as f:
#             html_content = f.read()

#         import re

#         # Extract key parts
#         result = {
#             "execution_id": execution_id,
#             "report_path": str(report_path),
#             "report_size": len(html_content),
#             "patterns_found": {}
#         }

#         # Check for overall status patterns
#         overall_patterns = {
#             "h2_overall_status": r'<h2[^>]*>\s*Overall\s+Status:\s*(PASSED|FAILED)\s*</h2>',
#             "div_overall_status": r'<div[^>]*class=["\']overall-status[^"\']*["\'][^>]*>\s*(PASSED|FAILED)',
#             "generic_status": r'Overall\s+Status:\s*<[^>]+>\s*(PASSED|FAILED)',
#         }

#         for name, pattern in overall_patterns.items():
#             match = re.search(pattern, html_content, re.IGNORECASE)
#             if match:
#                 result["patterns_found"][name] = match.group(1).upper()

#         # Count step statuses
#         step_table = re.search(r'<table[^>]*>(.*?)</table>', html_content, re.DOTALL | re.IGNORECASE)
#         if step_table:
#             table_content = step_table.group(1)

#             passed_in_table = len(re.findall(r'>\s*PASSED\s*<', table_content, re.IGNORECASE))
#             failed_in_table = len(re.findall(r'>\s*FAILED\s*<', table_content, re.IGNORECASE))

#             result["step_table"] = {
#                 "found": True,
#                 "passed_count": passed_in_table,
#                 "failed_count": failed_in_table
#             }

#         # Count all occurrences
#         all_passed = len(re.findall(r'\bPASSED\b', html_content))
#         all_failed = len(re.findall(r'\bFAILED\b', html_content))

#         result["word_counts"] = {
#             "passed": all_passed,
#             "failed": all_failed
#         }

#         # Extract a snippet around "Overall Status" if found
#         status_match = re.search(r'.{0,200}Overall\s+Status.{0,200}', html_content, re.IGNORECASE | re.DOTALL)
#         if status_match:
#             result["status_snippet"] = status_match.group(0)

#         # Get first 1000 chars of HTML for inspection
#         result["html_preview"] = html_content[:1000]

#         return result

#     except Exception as e:
#         logger.error(f"Debug parse report error: {e}", exc_info=True)
#         return {"error": str(e)}


# ...existing code...

@app.get("/api/debug/parse-report/{execution_id}")
async def debug_parse_report(execution_id: str, db: Session = Depends(get_db)):
    """
    🔍 DEBUG ENDPOINT: Parse HTML report and show step extraction
    
    Example: GET http://localhost:8000/api/debug/parse-report/exec_RBPLCD-8960_20260111_003255
    
    Returns:
        {
            "execution_id": "exec_RBPLCD-8960_20260111_003255",
            "report_path": "C:\\path\\to\\report.html",
            "total_rows": 10,
            "rows_parsed": [
                {
                    "row_index": 0,
                    "is_header": true,
                    "num_cells": 6,
                    "cells": ["Step #", "Description", "Status", "Selector", "Agent", "Confidence"],
                    "raw_html": "<tr><th>Step #</th>..."
                },
                {
                    "row_index": 1,
                    "is_header": false,
                    "num_cells": 6,
                    "cells": ["1", "Click login button", "PASSED", "#login", "L1", "0.95"],
                    "raw_html": "<tr><td>1</td>..."
                }
            ],
            "table_preview": "<thead><tr>..."
        }
    """
    try:
        # Find execution
        execution = db.query(TestExecution).filter(
            TestExecution.execution_id == execution_id
        ).first()
        
        if not execution:
            return {
                "error": f"Execution {execution_id} not found",
                "available_executions": [
                    e.execution_id for e in db.query(TestExecution).order_by(
                        TestExecution.started_at.desc()
                    ).limit(10).all()
                ]
            }
        
        if not execution.report_path or not Path(execution.report_path).exists():
            return {
                "error": f"Report not found",
                "report_path": execution.report_path,
                "execution_status": execution.status,
                "overall_status": execution.overall_status
            }
        
        logger.info(f"🔍 DEBUG: Parsing report for {execution_id}")
        logger.info(f"   Report path: {execution.report_path}")
        
        # Read HTML
        with open(execution.report_path, 'r', encoding='utf-8') as f:
            html = f.read()
        
        logger.info(f"   HTML size: {len(html)} bytes")
        
        # Extract table
        table_match = re.search(r'<table[^>]*>(.*?)</table>', html, re.DOTALL | re.IGNORECASE)
        
        if not table_match:
            return {
                "error": "No <table> found in HTML",
                "html_preview": html[:1000],
                "report_path": execution.report_path,
                "html_size": len(html),
                "has_table_tag": "<table" in html.lower()
            }
        
        table_html = table_match.group(1)
        
        # Extract rows
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL | re.IGNORECASE)
        
        logger.info(f"   Found {len(rows)} rows in table")
        
        debug_info = {
            "execution_id": execution_id,
            "report_path": execution.report_path,
            "total_rows": len(rows),
            "html_size": len(html),
            "table_size": len(table_html),
            "rows_parsed": []
        }
        
        # Parse each row
        for idx, row in enumerate(rows):
            cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL | re.IGNORECASE)
            
            # Also check for <th> tags (header row)
            if idx == 0 and len(cells) == 0:
                cells = re.findall(r'<th[^>]*>(.*?)</th>', row, re.DOTALL | re.IGNORECASE)
            
            # Clean HTML tags from cells
            clean_cells = [re.sub(r'<[^>]+>', '', cell).strip() for cell in cells]
            
            debug_info["rows_parsed"].append({
                "row_index": idx,
                "is_header": idx == 0,
                "num_cells": len(cells),
                "cells": clean_cells[:10],  # Limit to first 10 cells
                "raw_html": row[:200]  # First 200 chars of raw HTML
            })
        
        # Show first few rows of actual HTML table for inspection
        debug_info["table_preview"] = table_html[:1000]
        
        # Add recommendations based on what we found
        if len(rows) > 0:
            first_data_row = debug_info["rows_parsed"][1] if len(debug_info["rows_parsed"]) > 1 else None
            if first_data_row:
                num_cells = first_data_row["num_cells"]
                debug_info["recommendations"] = {
                    "cells_per_row": num_cells,
                    "suggested_mapping": _suggest_cell_mapping(num_cells, first_data_row["cells"])
                }
        
        return debug_info
    
    except Exception as e:
        import traceback
        logger.error(f"❌ DEBUG endpoint error: {e}")
        logger.error(traceback.format_exc())
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }


def _suggest_cell_mapping(num_cells: int, sample_cells: list) -> dict:
    """
    Helper function to suggest cell mapping based on content
    """
    mapping = {}
    
    if num_cells >= 3:
        mapping["step_num_index"] = 0
        mapping["step_text_index"] = 1
        mapping["status_index"] = 2
    
    if num_cells >= 4:
        mapping["selector_index"] = 3
    
    if num_cells >= 5:
        mapping["agent_index"] = 4
    
    if num_cells >= 6:
        mapping["confidence_index"] = 5
    
    mapping["example"] = f"""
    # Example parsing code for {num_cells} columns:
    step_num = int(re.sub(r'<[^>]+>', '', cells[0]).strip())
    step_text = re.sub(r'<[^>]+>', '', cells[1]).strip()[:200]
    status = re.sub(r'<[^>]+>', '', cells[2]).strip().upper()
    """
    
    if num_cells >= 4:
        mapping["example"] += """
    selector = re.sub(r'<[^>]+>', '', cells[3]).strip()
    agent = re.sub(r'<[^>]+>', '', cells[4]).strip() if len(cells) > 4 else ""
    confidence = float(re.sub(r'<[^>]+>', '', cells[5]).strip()) if len(cells) > 5 else 0.0
    """
    
    return mapping

# ...existing code...





@app.get("/api/debug/steps/{execution_id}")
def debug_steps_count(execution_id: str, db: Session = Depends(get_db)):
    count = db.query(ExecutionStep).filter(ExecutionStep.execution_id == execution_id).count()
    return {"execution_id": execution_id, "steps_count": count}


# Add this to your main.py after the other debug endpoints
def test_python_executable():
    """
    Test if Python executable can be found and works
    """
    try:
        from config import settings
        import shutil

        external_path = Path(settings.external_project_path)

        results = {
            "external_path": str(external_path),
            "external_path_exists": external_path.exists(),
            "python_checks": []
        }

        # Check venv paths
        venv_paths = [
            external_path / "venv" / "Scripts" / "python.exe",
            external_path / "venv" / "bin" / "python",
        ]

        for venv_path in venv_paths:
            check = {
                "path": str(venv_path),
                "exists": venv_path.exists(),
                "version": None,
                "works": False
            }

            if venv_path.exists():
                try:
                    result = subprocess.run(
                        [str(venv_path), "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    check["version"] = result.stdout.strip()
                    check["works"] = result.returncode == 0
                except Exception as e:
                    check["error"] = str(e)

            results["python_checks"].append(check)

        # Check system Python
        for cmd in ["python", "python3", "py"]:
            python_path = shutil.which(cmd)
            if python_path:
                check = {
                    "path": python_path,
                    "exists": True,
                    "command": cmd,
                    "version": None,
                    "works": False
                }

                try:
                    result = subprocess.run(
                        [python_path, "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    check["version"] = result.stdout.strip()
                    check["works"] = result.returncode == 0
                except Exception as e:
                    check["error"] = str(e)

                results["python_checks"].append(check)

        return results

    except Exception as e:
        logger.error(f"Test Python error: {e}", exc_info=True)
        return {"error": str(e)}
# ============================================================================
# TICKET MANAGEMENT (MINIMAL)
# ============================================================================

@app.get("/api/tickets/{ticket_id}")
def get_ticket_details(ticket_id: str, db: Session = Depends(get_db)):
    """
    Get ticket details by ticket_id
    """
    ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=404,
            detail=f"Ticket '{ticket_id}' not found. Please upload the ticket file to Jira_Tickets/ folder."
        )

    # Parse steps from file if available
    steps = []
    if ticket.file_path and Path(ticket.file_path).exists():
        try:
            with open(ticket.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Simple step extraction (you can improve this)
                lines = content.split('\n')
                step_num = 1
                for line in lines:
                    if re.match(r'^\s*(Step\s*\d+\.?|\d+\.)', line.strip()):
                        steps.append({
                            'num': step_num,
                            'text': line.strip()
                        })
                        step_num += 1
        except Exception as e:
            logger.warning(f"Could not parse steps from ticket file: {e}")

    return {
        "id": ticket.id,
        "ticket_id": ticket.ticket_id,
        "title": ticket.title,
        "module": ticket.module,
        "project_id": ticket.project_id,
        "file_path": ticket.file_path,
        "steps": steps,
        "created_at": ticket.created_at.isoformat() if ticket.created_at else None
    }

class UpdateTitleRequest(BaseModel):
    session_id: str
    new_title: str

class ChatSessionResponse(BaseModel):
    id: str
    title: str
    date: str
    messages: List[dict]

@app.put("/api/chat-session/title")
def update_chat_title(
    request: UpdateTitleRequest,
    db: Session = Depends(get_db)
):
    """
    Update chat session title

    Body:
        {
            "session_id": "1702888800000",
            "new_title": "Updated title here"
        }

    Returns:
        {
            "session_id": "1702888800000",
            "title": "Updated title here",
            "updated_at": "2025-12-15T10:30:00",
            "message": "Title updated successfully"
        }
    """
    try:
        logger.info(f"📝 Updating title for session: {request.session_id}")

        # Here you would update your database
        # For now, we'll just validate and return success
        # You'll need to add a ChatSession table to your database

        # TODO: Add actual database update
        # session = db.query(ChatSession).filter(
        #     ChatSession.id == request.session_id
        # ).first()
        #
        # if not session:
        #     raise HTTPException(status_code=404, detail="Session not found")
        #
        # session.title = request.new_title
        # session.updated_at = datetime.now()
        # db.commit()

        return {
            "session_id": request.session_id,
            "title": request.new_title,
            "updated_at": datetime.now().isoformat(),
            "message": "Title updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating title: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chat-sessions")
def get_chat_sessions(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get all chat sessions for current user

    Query params:
        - limit: Number of sessions to return (default: 50)

    Returns:
        {
            "count": 10,
            "sessions": [
                {
                    "id": "1702888800000",
                    "title": "Chat title",
                    "date": "2025-12-15T10:00:00",
                    "messages": [...]
                }
            ]
        }
    """
    try:
        logger.info(f"📋 Fetching chat sessions (limit: {limit})")

        # TODO: Add actual database query
        # sessions = db.query(ChatSession).order_by(
        #     ChatSession.created_at.desc()
        # ).limit(limit).all()

        # For now, return empty array
        # Frontend will continue using localStorage

        return {
            "count": 0,
            "sessions": []
        }

    except Exception as e:
        logger.error(f"❌ Error fetching sessions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/chat-session/{session_id}")
def delete_chat_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a chat session

    Path params:
        - session_id: ID of session to delete

    Returns:
        {
            "message": "Session deleted successfully",
            "session_id": "1702888800000"
        }
    """
    try:
        logger.info(f"🗑️ Deleting session: {session_id}")

        # TODO: Add actual database delete
        # session = db.query(ChatSession).filter(
        #     ChatSession.id == session_id
        # ).first()
        #
        # if not session:
        #     raise HTTPException(status_code=404, detail="Session not found")
        #
        # db.delete(session)
        # db.commit()

        return {
            "message": "Session deleted successfully",
            "session_id": session_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# BACKGROUND TASK
# ============================================================================

"""
REPLACE the execute_test_in_background function in your main.py with this version
This ensures proper completion and error handling
"""

# def execute_test_in_background(
#     execution_id: str,
#     ticket_id: str,
#     # project_id: int
#     project_id: Optional[int]  # 🟢 CHANGE THIS - Allow None

# ):
#     """
#     Background task to execute test workflow using external run_test.py
#     FIXED: Better error handling and ensures completion
#     """
#     db = SessionLocal()
#     service = TestExecutionService(db)
    
#     # Track if we've successfully updated to a final state
#     final_status_set = False

#     logger.info("="*70)
#     logger.info(f"🚀 BACKGROUND TASK STARTED")
#     logger.info(f"   Execution ID: {execution_id}")
#     logger.info(f"   Ticket ID: {ticket_id}")
#     logger.info(f"   Project ID: {project_id}")  # 🟢 ADD THIS LINE
#     logger.info(f"   External Path: {settings.external_project_path}")
#     logger.info(f"   Started at: {datetime.now().isoformat()}")
#     logger.info("="*70)

#     try:
#         # Update status to running
#         service.update_execution_status(
#             execution_id=execution_id,
#             status="running"
#         )
#         logger.info("✅ Status updated to 'running'")

#         # Path to your external TA_AI_Project
#         external_project_path = settings.external_project_path

#         logger.info(f"📁 External project path: {external_project_path}")

#         # Verify path exists
#         if not Path(external_project_path).exists():
#             raise FileNotFoundError(f"External project not found: {external_project_path}")
#             logger.info("✅ External project path exists")

#        # Check if plcd_taseq.py exists
#         plcd_script = Path(external_project_path) / "plcd_taseq.py"
#         if not plcd_script.exists():
#             raise FileNotFoundError(f"plcd_taseq.py not found at: {plcd_script}")
#         logger.info(f"✅ Found plcd_taseq.py at: {plcd_script}")


#         logger.info("🏃 Starting test workflow execution...")
#         # CRITICAL: Add logging around this call
#         logger.info("📞 Calling service.run_test_workflow()...")

#         # Run test workflow (this will now wait for completion)
#         state = service.run_test_workflow(
#             ticket_id=ticket_id,
#             project_id=project_id,
#             execution_id=execution_id,
#             external_project_path=external_project_path
#         )
#         if not state:
#           logger.error("❌ Test runner returned None or empty state! Marking as failed.")
#           service.update_execution_status(
#                 execution_id=execution_id,
#                 status="failed",
#                 overall_status="FAILED",
#                 error_message="Test runner crashed or did not return results."
#           )
#           service._generate_summary_from_db(execution_id, ticket_id)  # <-- ADD THIS LINE
#           db.close()
#           return
#         logger.info(f"📋 Workflow returned state: {state}")


# # Log what we got back
#         if state:
#             logger.info(f"📄 Report path: {state.get('report_path')}")
#             logger.info(f"📜 Script path: {state.get('script_path')}")
#             logger.info(f"🎥 Video path: {state.get('video_path')}")
#             logger.info(f"📊 Overall status: {state.get('overall_status')}")
#         else:
#             logger.warning("⚠️  Workflow returned None or empty state!")

#         logger.info("✅ Test workflow completed, saving results to database...")

#         # Save results to database (steps are already saved in run_test_workflow)
#         service.save_execution_results(execution_id, state)
#         service._generate_summary_from_db(execution_id, ticket_id)
#         # Determine if we should mark as 'completed' or 'failed'
#         # If we have a report, mark as 'completed' even if tests failed
#         has_report = bool(state.get('report_path'))
#         overall_status = state.get('overall_status', 'UNKNOWN')


#         # if has_report:
#         #     # Mark as completed - user can download report
#         #     final_status = "completed"
#         #     logger.info(f"✅ Marking as completed (report available, status: {overall_status})")
#         # else:
#         #     # No report - mark as failed
#         #     final_status = "failed"
#         #     logger.warning(f"⚠️  Marking as failed (no report generated)")
#         if has_report and overall_status != "FAILED":
#            final_status = "completed"
#            logger.info(f"✅ Marking as completed (report available, status: {overall_status})")
#         else:
#            final_status = "failed"
#            logger.warning(f"⚠️  Marking as failed (no report or test failed, status: {overall_status})")


#         # Update status to completed
#         service.update_execution_status(
#             execution_id=execution_id,
#             status=final_status,
#             overall_status=overall_status,
#             report_path=state.get('report_path', ''),
#             script_path=state.get('script_path', ''),
#             video_path=state.get('video_path', ''),
#             error_message=None if has_report else "Test execution failed or no report generated."
            
#         )
#         service._generate_summary_from_db(execution_id, ticket_id)  # <-- Add this line here
#         logger.info("="*70)
#         logger.info("✅ TEST EXECUTION COMPLETED SUCCESSFULLY")
#         logger.info(f"   Execution ID: {execution_id}")
#         logger.info(f"   Overall Status: {state.get('overall_status', 'UNKNOWN')}")
#         logger.info(f"   📄 Report: {state.get('report_path', 'N/A')}")
#         logger.info(f"   📜 Script: {state.get('script_path', 'N/A')}")
#         logger.info(f"   🎥 Video: {state.get('video_path', 'N/A')}")
#         logger.info(f"   Completed at: {datetime.now().isoformat()}")
#         logger.info("="*70)

#     except Exception as e:
#         logger.error("="*70)
#         logger.error(f"❌ BACKGROUND TASK FAILED")
#         logger.error(f"   Execution ID: {execution_id}")
#         logger.error(f"   Error: {e}")
#         logger.error(f"   Failed at: {datetime.now().isoformat()}")
#         logger.error("="*70)

#  # Log full traceback
#         import traceback
#         logger.error("Full traceback:")
#         logger.error(traceback.format_exc())

#         # Get detailed error message
#         error_str = str(e)
#         error_lines = []
#         for line in error_str.split('\n'):
#             if not line.strip().startswith('[INFO]') and not line.strip().startswith('[DEBUG]'):
#                 if line.strip():
#                     error_lines.append(line.strip())

#         clean_error = '\n'.join(error_lines[:10]) if error_lines else str(e)

#         # Truncate if too long
#         if len(clean_error) > 500:
#             clean_error = clean_error[:500] + "...\n(Check server logs for full details)"


#         # Mark as failed in database
#         try:
#             service.update_execution_status(
#                 execution_id=execution_id,
#                 status="failed",
#                 overall_status="FAILED",
#                 # error_message=error_message
#                 error_message=clean_error  # <-- Use the cleaned error message here
#             )
#             service._generate_summary_from_db(execution_id, ticket_id)  # <-- ADD THIS LINE
#             logger.info("✅ Updated execution status to 'failed' in database")
#         except Exception as db_error:
#             logger.error(f"❌ Could not update database with failure: {db_error}")

#         # Log full traceback
#         import traceback
#         logger.error("Full traceback:")
#         logger.error(traceback.format_exc())

#     finally:
#         db.close()
#         logger.info(f"🏁 Background task ended for {execution_id}")
#         logger.info("")  # Empty line for readability




# def execute_test_in_background(
#     execution_id: str,
#     ticket_id: str,
#     project_id: Optional[int]
# ):
#     db = SessionLocal()
#     service = TestExecutionService(db)

#     logger.info("=" * 70)
#     logger.info(f"🚀 BACKGROUND TASK STARTED")
#     logger.info(f"   Execution ID: {execution_id}")
#     logger.info(f"   Ticket ID: {ticket_id}")
#     logger.info(f"   Project ID: {project_id}")
#     logger.info("=" * 70)

#     try:
#         # 1️⃣ Mark running
#         service.update_execution_status(
#             execution_id=execution_id,
#             status="running"
#         )

#         external_project_path = Path(settings.external_project_path)

#         # 2️⃣ Run Playwright workflow (BLOCKING)
#         state = service.run_test_workflow(
#             ticket_id=ticket_id,
#             project_id=project_id,
#             execution_id=execution_id,
#             external_project_path=str(external_project_path)
#         )

#         if not state:
#             raise RuntimeError("Test workflow returned empty state")

#         # 3️⃣ Generate summary (this already works)
#         service._generate_summary_from_db(execution_id, ticket_id)

#         # ============================================================
#         # 🔥 FORCE SYNC DB WITH REAL FILES (CRITICAL FIX)
#         # ============================================================

#         report_path = None
#         video_path = None
#         script_path = None

#         # 📄 Report
#         reports_folder = external_project_path / "Reports"
#         if reports_folder.exists():
#             reports = sorted(
#                 reports_folder.glob(f"*{ticket_id}*.html"),
#                 key=lambda p: p.stat().st_mtime,
#                 reverse=True
#             )
#             if reports:
#                 report_path = str(reports[0])

#         # 🎥 Video
#         videos_folder = external_project_path / "Videos"
#         if videos_folder.exists():
#             videos = sorted(
#                 videos_folder.glob("*.webm"),
#                 key=lambda p: p.stat().st_mtime,
#                 reverse=True
#             )
#             if videos:
#                 video_path = str(videos[0])

#         # 📜 Script
#         scripts_folder = external_project_path / "Generated_Scripts"
#         if scripts_folder.exists():
#             scripts = sorted(
#                 scripts_folder.glob(f"*{ticket_id}*.py"),
#                 key=lambda p: p.stat().st_mtime,
#                 reverse=True
#             )
#             if scripts:
#                 script_path = str(scripts[0])

#         # 4️⃣ Determine final status
#         overall_status = state.get("overall_status", "UNKNOWN")
#         final_status = "completed" if report_path else "failed"

#         # 5️⃣ FINAL DB UPDATE (THIS FIXES UI)
#         execution = db.query(TestExecution).filter(
#             TestExecution.execution_id == execution_id
#         ).first()

#         execution.status = final_status
#         execution.overall_status = overall_status
#         execution.report_path = report_path
#         execution.script_path = script_path
#         execution.video_path = video_path
#         execution.completed_at = datetime.now()
#         execution.error_message = None

#         db.commit()

#         logger.info("✅ EXECUTION COMPLETED AND DB SYNCED")
#         logger.info(f"📄 Report: {report_path}")
#         logger.info(f"📜 Script: {script_path}")
#         logger.info(f"🎥 Video: {video_path}")

#     except Exception as e:
#         logger.error(f"❌ EXECUTION FAILED: {e}", exc_info=True)

#         service.update_execution_status(
#             execution_id=execution_id,
#             status="failed",
#             overall_status="FAILED",
#             error_message=str(e)[:500]
#         )

#     finally:
#         db.close()
#         logger.info(f"🏁 Background task ended: {execution_id}")





# def execute_test_in_background(
#     execution_id: str,
#     ticket_id: str,
#     project_id: Optional[int]
# ):
#     """
#     Background task to execute test workflow using external plcd_taseq.py
#     FIXED: Ensures clean termination and immediate summary generation
#     """
#     db = SessionLocal()
#     service = TestExecutionService(db)
#     final_status_set = False

#     logger.info("="*70)
#     logger.info(f"🚀 BACKGROUND TASK STARTED")
#     logger.info(f"   Execution ID: {execution_id}")
#     logger.info(f"   Ticket ID: {ticket_id}")
#     logger.info(f"   Project ID: {project_id}")
#     logger.info("="*70)

#     try:
#         # ============================================================================
#         # STEP 1: Mark as running
#         # ============================================================================
#         execution = db.query(TestExecution).filter(
#             TestExecution.execution_id == execution_id
#         ).first()

#         if not execution:
#             logger.error(f"❌ Execution {execution_id} not found!")
#             return

#         execution.status = "running"
#         execution.started_at = datetime.utcnow()
#         db.commit()
#         logger.info("✅ Status updated to 'running'")

#         # ============================================================================
#         # STEP 2: Validate external project
#         # ============================================================================
#         external_project_path = Path(settings.external_project_path)
#         if not external_project_path.exists():
#             raise FileNotFoundError(f"External project not found: {external_project_path}")

#         plcd_script = external_project_path / "plcd_taseq.py"
#         if not plcd_script.exists():
#             raise FileNotFoundError(f"plcd_taseq.py not found at: {plcd_script}")
        
#         logger.info(f"✅ Found plcd_taseq.py at: {plcd_script}")

#         # ============================================================================
#         # STEP 3: Find Python executable
#         # ============================================================================
#         python_exe = None
#         venv_paths = [
#             external_project_path / "venv" / "Scripts" / "python.exe",  # Windows
#             external_project_path / "venv" / "bin" / "python",  # Linux/Mac
#         ]

#         for venv_path in venv_paths:
#             if venv_path.exists():
#                 python_exe = str(venv_path)
#                 logger.info(f"✅ Found Python: {python_exe}")
#                 break

#         if not python_exe:
#             import shutil
#             python_exe = shutil.which("python") or shutil.which("python3")
#             if not python_exe:
#                 raise FileNotFoundError("Python executable not found")
#             logger.info(f"⚠️ Using system Python: {python_exe}")

#         # ============================================================================
#         # STEP 4: Execute Playwright test (SINGLE RUN, NO FEEDBACK)
#         # ============================================================================
#         logger.info(f"🏃 Executing test: {ticket_id} --no-feedback")
        
#         # ✅ CRITICAL: Use --no-feedback flag to prevent interactive loop
#         result = subprocess.run(
#             [python_exe, str(plcd_script), ticket_id, "--no-feedback"],
#             cwd=str(external_project_path),
#             capture_output=True,
#             text=True,
#             timeout=600  # 10 minutes
#         )

#         logger.info(f"📤 Playwright execution completed with return code: {result.returncode}")

#         if result.stdout:
#             logger.debug(f"STDOUT:\n{result.stdout[:1000]}")
#         if result.stderr:
#             logger.warning(f"STDERR:\n{result.stderr[:1000]}")

#         # ============================================================================
#         # STEP 5: Locate generated artifacts (SYNC WITH ACTUAL FILES)
#         # ============================================================================
#         report_path = None
#         script_path = None
#         video_path = None
#         overall_status = "UNKNOWN"

#         # Find report
#         reports_folder = external_project_path / "Reports"
#         if reports_folder.exists():
#             reports = sorted(
#                 reports_folder.glob(f"*{ticket_id}*.html"),
#                 key=lambda p: p.stat().st_mtime,
#                 reverse=True
#             )
#             if reports:
#                 report_path = str(reports[0])
#                 logger.info(f"📄 Found report: {reports[0].name}")

#         # Find script
#         scripts_folder = external_project_path / "Generated_Scripts"
#         if scripts_folder.exists():
#             scripts = sorted(
#                 scripts_folder.glob(f"*{ticket_id}*.py"),
#                 key=lambda p: p.stat().st_mtime,
#                 reverse=True
#             )
#             if scripts:
#                 script_path = str(scripts[0])
#                 logger.info(f"📜 Found script: {scripts[0].name}")

#         # Find video
#         videos_folder = external_project_path / "Videos"
#         if videos_folder.exists():
#             videos = sorted(
#                 videos_folder.glob("*.webm"),
#                 key=lambda p: p.stat().st_mtime,
#                 reverse=True
#             )
#             if videos:
#                 video_path = str(videos[0])
#                 logger.info(f"🎥 Found video: {videos[0].name}")

#         # Parse overall status from report
#         if report_path and Path(report_path).exists():
#             try:
#                 with open(report_path, 'r', encoding='utf-8') as f:
#                     html_content = f.read()

#                 patterns = [
#                     r'<h2[^>]*>\s*Overall\s+Status:\s*(PASSED|FAILED)\s*</h2>',
#                     r'<div[^>]*class=["\']overall-status[^"\']*["\'][^>]*>\s*(PASSED|FAILED)',
#                 ]

#                 for pattern in patterns:
#                     match = re.search(pattern, html_content, re.IGNORECASE)
#                     if match:
#                         overall_status = match.group(1).upper()
#                         logger.info(f"✅ Parsed overall status: {overall_status}")
#                         break

#                 if overall_status == "UNKNOWN":
#                     passed_count = len(re.findall(r'>\s*PASSED\s*<', html_content, re.IGNORECASE))
#                     failed_count = len(re.findall(r'>\s*FAILED\s*<', html_content, re.IGNORECASE))
#                     overall_status = "FAILED" if failed_count > 0 else ("PASSED" if passed_count > 0 else "UNKNOWN")
#                     logger.info(f"📊 Inferred status: {overall_status} (P:{passed_count}, F:{failed_count})")

#             except Exception as e:
#                 logger.warning(f"Could not parse report status: {e}")

#         # ============================================================================
#         # STEP 6: Save execution steps from report (for summary generation)
#         # ============================================================================
#         # if report_path and Path(report_path).exists():
#         #     try:
#         #         with open(report_path, 'r', encoding='utf-8') as f:
#         #             html_content = f.read()

#         #         table_match = re.search(r'<table[^>]*>(.*?)</table>', html_content, re.DOTALL | re.IGNORECASE)
#         #         if table_match:
#         #             table_content = table_match.group(1)
#         #             rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_content, re.DOTALL | re.IGNORECASE)
                    
#         #             # 🔒 DELETE old steps for this execution (prevents duplicates)
#         #             try:
#         #                 deleted = db.query(ExecutionStep).filter(
#         #                     ExecutionStep.execution_id == execution_id
#         #                 ).delete()
#         #                 db.commit()
#         #                 logger.info(f"🧹 Deleted {deleted} old steps for execution {execution_id}")
#         #             except Exception as e:
#         #                    logger.error(f"❌ Failed to delete old steps: {e}")
#         #                    db.rollback()
                           
#         #             step_num = 1
#         #             for row in rows[1:]:  # Skip header
#         #                 cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL | re.IGNORECASE)
#         #                 if len(cells) >= 3:
#         #                     # 🔥 FIX: Clean step text - remove HTML tags AND console output
#         #                     raw_step_text = re.sub(r'<[^>]+>', '', cells[1]).strip()
#         #                     # step_text = re.sub(r'<[^>]+>', '', cells[1]).strip()
#         #                     # status = re.sub(r'<[^>]+>', '', cells[2]).strip().upper()
#         #                     # Remove console output patterns that might have bled into step text
#         #             # Pattern 1: Remove everything after "Failed to search" or similar error messages
#         #                     step_text = re.split(r'(?:Failed to search|Error:|âœ" |â|Trying L2|\[OK\]|\[FAILED\]|\[SKIPPED\])', raw_step_text)[0].strip()
                    
#         #             # Pattern 2: Remove log prefixes like "UI element step detected..."
#         #                     step_text = re.split(r'(?:UI element step detected|Checking pending insights|No pending insight)', step_text)[0].strip()
                    
#         #             # Pattern 3: Remove confidence indicators like "[L1 Low Confidence: 0.50]"
#         #                     step_text = re.sub(r'\[L\d+[^\]]*\]', '', step_text).strip()
                    
#         #                     status = re.sub(r'<[^>]+>', '', cells[2]).strip().upper()

#         #                     # if step_text and status in ['PASSED', 'FAILED']:
#         #                     #     step = ExecutionStep(
#         #                     #         execution_id=execution_id,
#         #                     #         step_num=step_num,
#         #                     #         step_text=step_text,
#         #                     #         status=status,
#         #                     #         screenshot_path=None
#         #                     #     )
#         #                     #     db.add(step)
#         #                     #     step_num += 1
#         #                     # Only save steps with valid status
#         #                     if step_text and status in ['PASSED', 'FAILED', 'SKIPPED']:
#         #                 # 🔥 FIX: Check for duplicates before adding
#         #                         # existing_step = db.query(ExecutionStep).filter(
#         #                         #     ExecutionStep.execution_id == execution_id,
#         #                         #     ExecutionStep.step_num == step_num
#         #                         # ).first()
#         #                         step = ExecutionStep(
#         #                             execution_id=execution_id,
#         #                             step_num=step_num,
#         #                             step_text=step_text,
#         #                             status=status,
#         #                             screenshot_path=None
#         #                         )
#         #                         db.add(step)
#         #                         step_num += 1
                        
#         #                 # if not existing_step:
#         #                 #     step = ExecutionStep(
#         #                 #         execution_id=execution_id,
#         #                 #         step_num=step_num,
#         #                 #         step_text=step_text,
#         #                 #         status=status,
#         #                 #         screenshot_path=None
#         #                 #     )
#         #                 #     db.add(step)
#         #                 #     step_num += 1


#         #             db.commit()
#         #             logger.info(f"✅ Saved {step_num-1} steps to database")
#         #         else:
#         #             logger.warning("No step table found in HTML report!")
#         #     except Exception as e:
#         #         logger.warning(f"Could not parse steps: {e}")

#         #     # except Exception as e:
#         #     #     logger.warning(f"Could not parse steps: {e}")
#         #     #     import traceback
#         #     #     logger.warning(traceback.format_exc())

#         # if report_path and Path(report_path).exists():
#         #     try:
#         #         logger.info(f"📥 Parsing execution steps from report: {report_path}")
                
#         #         with open(report_path, 'r', encoding='utf-8') as f:
#         #             html_content = f.read()
                
#         #         logger.debug(f"Report size: {len(html_content)} bytes")
                
#         #         # Find table
#         #         table_match = re.search(r'<table[^>]*>(.*?)</table>', html_content, re.DOTALL | re.IGNORECASE)
                
#         #         if not table_match:
#         #             logger.error("❌ No <table> found in HTML report!")
#         #             logger.debug(f"Report preview: {html_content[:500]}")
#         #         else:
#         #             table_content = table_match.group(1)
#         #             rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_content, re.DOTALL | re.IGNORECASE)
                    
#         #             logger.info(f"Found {len(rows)} table rows")
                    
#         #             # 🔥 DELETE old steps for this execution (prevents duplicates)
#         #             # deleted = db.query(ExecutionStep).filter(
#         #             #     ExecutionStep.execution_id == execution_id
#         #             # ).delete()
#         #             # db.commit()
#         #             # logger.info(f"🧹 Deleted {deleted} old steps")
                    
#         #             step_num = 1
#         #             saved_count = 0  # <-- ADD THIS LINE
#         #             for idx, row in enumerate(rows[1:], start=1):  # Skip header
#         #                 try:
#         #                     cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL | re.IGNORECASE)
#         #                     logger.debug(f"🔍 Row {idx}: Found {len(cells)} cells")
                            
#         #                     if len(cells) < 6:
#         #                         logger.debug(f"Row {idx} has only {len(cells)} cells, skipping")
#         #                         continue
                            
#         #                     step_num = int(re.sub(r'<[^>]+>', '', cells[0]).strip())
#         #                     step_text = re.sub(r'<[^>]+>', '', cells[1]).strip()
#         #                     selector = re.sub(r'<[^>]+>', '', cells[2]).strip()
#         #                     agent = re.sub(r'<[^>]+>', '', cells[3]).strip()
#         #                     confidence = float(re.sub(r'<[^>]+>', '', cells[4]).strip())
#         #                     # status = re.sub(r'<[^>]+>', '', cells[5]).strip().upper()
#         #                     status = re.sub(r'<[^>]+>', '', cells[5]).strip().upper()  # <-- FIXED
                            
#         #                     # Clean step text
#         #                     # raw_step_text = re.sub(r'<[^>]+>', '', cells[1]).strip()
#         #                     # step_text = re.split(r'(?:Failed to search|Error:|✓ |[OK]|[FAILED])', raw_step_text)[0].strip()
#         #                     # status = re.sub(r'<[^>]+>', '', cells[2]).strip().upper()
                            
#         #                     # # Extract status
#         #                     # raw_status = re.sub(r'<[^>]+>', '', cells[2]).strip().upper()
#         #                     # status = raw_status if raw_status in ['PASSED', 'FAILED', 'SKIPPED'] else 'UNKNOWN'
                            
#         #                     # logger.debug(f"   Raw text: {raw_step_text[:80]}...")
#         #                     # logger.debug(f"   Clean text: {step_text[:80]}...")
#         #                     # logger.debug(f"   Status: {status}")
                            
#         #                     logger.debug(f"Row {idx}: text='{step_text[:50]}...', status='{status}'")
                            
#         #                     if step_text and status in ['PASSED', 'FAILED', 'SKIPPED']:
#         #                         step = ExecutionStep(
#         #                             execution_id=execution_id,
#         #                             step_num=step_num,
#         #                             # step_text=step_text,
#         #                             step_text=step_text[:200],  # Limit to 200 chars
#         #                             status=status,
#         #                             screenshot_path=None,
#         #                             selector_used=selector,
#         #                             agent_used=agent,
#         #                             confidence=confidence,
#         #                             action_type=None  # Fill if available
#         #                         )
#         #                         db.add(step)
#         #                         step_num += 1
#         #                         saved_count += 1
#         #                         logger.debug(f"✅ Added step {step_num-1}")
#         #                     else:
#         #                         logger.debug(f"⚠️  Skipped row {idx}: invalid text or status")
                        
#         #                 except Exception as row_error:
#         #                     logger.warning(f"⚠️  Failed to parse row {idx}: {row_error}")
#         #                     continue
                    
#         #             db.commit()
#         #             logger.info(f"✅ Saved {step_num-1} steps to database")
#         #             logger.info(f"✅ Saved {saved_count} steps to database")
                    
#         #             # DEBUG: Add a test step to verify DB/model
#         #             step = ExecutionStep(
#         #                 execution_id=execution_id,
#         #                 step_num=999,
#         #                 step_text="DEBUG STEP",
#         #                 status="PASSED",
#         #                 selector_used="dummy",
#         #                 agent_used="dummy",
#         #                 confidence=1.0,
#         #                 action_type=None,
#         #                 screenshot_path=None
#         #             )
#         #             db.add(step)
#         #             db.commit()
#         #             logger.info("✅ DEBUG STEP added to execution_steps table")
                    
#         #             # # 🔥 VERIFY SAVE
#         #             # saved_count = db.query(ExecutionStep).filter(
#         #             #     ExecutionStep.execution_id == execution_id
#         #             # ).count()
#         #             # logger.info(f"🔍 Verification: {saved_count} steps in DB for {execution_id}")
                    
#         #             # 🔥 VERIFY what was actually saved
#         #             verification_count = db.query(ExecutionStep).filter(
#         #                 ExecutionStep.execution_id == execution_id
#         #             ).count()
#         #             logger.info(f"🔍 Verification: {verification_count} steps now in DB for {execution_id}")
                    
#         #             if verification_count == 0:
#         #                 logger.error(f"❌ CRITICAL: No steps in DB after save! Check parsing logic!")
            
#         #     except Exception as e:
#         #         logger.error(f"❌ Failed to parse steps from report: {e}")
#         #         import traceback
#         #         logger.error(traceback.format_exc())
#         # else:
#         #     logger.warning(f"⚠️  No report found at: {report_path}")
        
#         if report_path and Path(report_path).exists():
#             try:
#                 logger.info(f"📥 Parsing execution steps from report: {report_path}")
#                 with open(report_path, 'r', encoding='utf-8') as f:
#                      html_content = f.read()
        
#         # Clean HTML - remove script tags and comments
#                 html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
#                 html_content = re.sub(r'<!--.*?-->', '', html_content, flags=re.DOTALL)
#                 step_patterns = [
#             # Pattern 1: Table rows with step number
#                      r'<tr[^>]*>\s*<td[^>]*>\s*(\d+)\s*</td>.*?<td[^>]*>(.*?)</td>.*?<td[^>]*>(PASSED|FAILED|SKIPPED)</td>',
#             # Pattern 2: Any step-like structure
#                      r'Step\s+(\d+)[^<]*<[^>]*>(.*?)</[^>]*>.*?(PASSED|FAILED|SKIPPED)',
#             ]
#                 saved_steps = []
#                 for pattern in step_patterns:
#                     matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
#                     for match in matches:
#                         if len(match) >= 3:
#                             step_num = int(match[0].strip())
#                             step_text = re.sub(r'<[^>]+>', '', match[1]).strip()[:200]  # Clean and limit
#                             status = match[2].strip().upper()
                    
#                     # Skip if we already have this step
#                             if any(s[0] == step_num for s in saved_steps):
#                                 continue
                    
#                             saved_steps.append((step_num, step_text, status))
        
#         # If no patterns found, try manual extraction
#                 if not saved_steps:
#                     logger.warning("⚠️ No step patterns found, trying manual extraction")
            
#             # Extract all text and look for step-like content
#                     text_only = re.sub(r'<[^>]+>', ' ', html_content)
#                     lines = text_only.split('\n')
            
#                     step_num = 1
#                     for line in lines:
#                         line = line.strip()
#                         if (('Step' in line or 'step' in line) and 
#                             any(status in line for status in ['PASSED', 'FAILED', 'SKIPPED'])):
                    
#                     # Clean the line
#                             step_text = line[:200]
#                             status = 'PASSED' if 'PASSED' in line.upper() else \
#                                     'FAILED' if 'FAILED' in line.upper() else 'SKIPPED'
                    
#                             saved_steps.append((step_num, step_text, status))
#                             step_num += 1
        
#         # Save steps to database
#                 if saved_steps:
#                     logger.info(f"Found {len(saved_steps)} steps to save")
            
#             # Delete existing steps first
#                     deleted = db.query(ExecutionStep).filter(
#                            ExecutionStep.execution_id == execution_id
#                     ).delete()
#                     logger.info(f"🧹 Deleted {deleted} old steps")
            
#             # Add new steps
#                     for step_num, step_text, status in saved_steps:
#                         step = ExecutionStep(
#                             execution_id=execution_id,
#                             step_num=step_num,
#                             step_text=step_text,
#                             status=status,
#                             screenshot_path=None,
#                             selector_used="",
#                             agent_used="",
#                             confidence=0.0,
#                             action_type=""
#                         )
#                         db.add(step)
            
#                     db.commit()
#                     logger.info(f"✅ Successfully saved {len(saved_steps)} steps to database")
#                 else:
#                     logger.warning("⚠️ No steps could be extracted from report")
            
#             # Add a single debug step so summary can generate
#                     debug_step = ExecutionStep(
#                         execution_id=execution_id,
#                         step_num=1,
#                         step_text="No steps could be parsed from report",
#                         status="FAILED",
#                         screenshot_path=None,
#                         selector_used="",
#                         agent_used="",
#                         confidence=0.0,
#                         action_type=""
#                     )
#                     db.add(debug_step)
#                     db.commit()
#                     logger.info("✅ Added debug step for summary generation")
            
#             except Exception as e:
#                 logger.error(f"❌ Failed to parse steps: {e}")
#                 import traceback
#                 logger.error(traceback.format_exc())
        
#         # Even if parsing fails, add a debug step
#                 try:
#                     debug_step = ExecutionStep(
#                         execution_id=execution_id,
#                         step_num=1,
#                         step_text=f"Step parsing failed: {str(e)[:100]}",
#                         status="FAILED",
#                         screenshot_path=None,
#                         selector_used="",
#                         agent_used="",
#                         confidence=0.0,
#                         action_type=""
#                     )
#                     db.add(debug_step)
#                     db.commit()
#                     logger.info("✅ Added fallback debug step")
#                 except:
#                     logger.error("❌ Could not add fallback debug step")

#         # ============================================================================
#         # STEP 7: Update execution to "completed" (CRITICAL)
#         # ============================================================================
#         final_status = "completed" if report_path else "failed"
        
#         db.refresh(execution)  # Get fresh state
#         execution.status = final_status
#         execution.overall_status = overall_status
#         # execution.completed_at = datetime.utcnow()
#         execution.completed_at = datetime.now()
#         execution.report_path = report_path
#         execution.script_path = script_path
#         execution.video_path = video_path
#         execution.error_message = None if report_path else "No report generated"
#         db.commit()
#         # final_status_set = True
#         #  🔥 THIS WAS MISSING
#         # service._generate_summary_from_db(execution_id, ticket_id)
        
#         logger.info(f"✅ Execution marked as '{final_status}'")

#         # ============================================================================
#         # STEP 8: Generate summary (AFTER DB update, BEFORE feedback)
#         # ============================================================================
#         logger.info("📊 Generating test summary...")
#         try:
#             service._generate_summary_from_db(execution_id, ticket_id)
#             logger.info("✅ Summary generated successfully")
#         except Exception as summary_error:
#             logger.error(f"⚠️ Summary generation failed: {summary_error}")

#         # ============================================================================
#         # SUCCESS
#         # ============================================================================
#         logger.info("="*70)
#         logger.info("✅ TEST EXECUTION COMPLETED SUCCESSFULLY")
#         logger.info(f"   Execution ID: {execution_id}")
#         logger.info(f"   Final Status: {final_status}")
#         logger.info(f"   Overall Status: {overall_status}")
#         logger.info(f"   📄 Report: {report_path or 'N/A'}")
#         logger.info(f"   📜 Script: {script_path or 'N/A'}")
#         logger.info(f"   🎥 Video: {video_path or 'N/A'}")
#         logger.info("="*70)

#     except subprocess.TimeoutExpired:
#         error_msg = "Test execution timed out (10 minutes)"
#         logger.error(f"⏰ {error_msg}")
#         _mark_execution_as_failed(db, execution_id, error_msg, service, ticket_id)
#         final_status_set = True

#     except FileNotFoundError as e:
#         error_msg = f"Configuration error: {str(e)}"
#         logger.error(f"❌ {error_msg}")
#         _mark_execution_as_failed(db, execution_id, error_msg, service, ticket_id)
#         final_status_set = True

#     except Exception as e:
#         logger.error("="*70)
#         logger.error(f"❌ EXECUTION FAILED")
#         logger.error(f"   Execution ID: {execution_id}")
#         logger.error(f"   Error: {e}")
#         logger.error("="*70)

#         import traceback
#         logger.error("Full traceback:")
#         logger.error(traceback.format_exc())

#         error_message = str(e)[:500]
#         _mark_execution_as_failed(db, execution_id, error_message, service, ticket_id)
#         final_status_set = True

#     finally:
#         # ============================================================================
#         # CRITICAL: Ensure execution is NEVER left in 'running' state
#         # ============================================================================
#         try:
#             if not final_status_set:
#                 logger.warning("⚠️ Final status was NOT set - forcing to 'failed'")
#                 execution = db.query(TestExecution).filter(
#                     TestExecution.execution_id == execution_id
#                 ).first()

#                 if execution and execution.status == "running":
#                     logger.error(f"❌ Execution {execution_id} still 'running'! Forcing to 'failed'")
#                     execution.status = "failed"
#                     execution.completed_at = datetime.utcnow()
#                     execution.overall_status = "FAILED"
#                     execution.error_message = "Execution did not complete normally"
#                     db.commit()
                    
#                     # Try to generate summary even for forced failure
#                     try:
#                         service._generate_summary_from_db(execution_id, ticket_id)
#                     except:
#                         pass

#         except Exception as finally_error:
#             logger.error(f"❌ Error in finally block: {finally_error}")
        
#         finally:
#             db.close()
#             logger.info(f"🔒 Database session closed for {execution_id}\n")


# def _mark_execution_as_failed(
#     db: Session, 
#     execution_id: str, 
#     error_message: str,
#     service: TestExecutionService,
#     ticket_id: str
# ):
#     """Mark execution as failed and generate summary"""
#     try:
#         execution = db.query(TestExecution).filter(
#             TestExecution.execution_id == execution_id
#         ).first()

#         if execution:
#             execution.status = "failed"
#             execution.overall_status = "FAILED"
#             execution.completed_at = datetime.utcnow()
#             execution.error_message = error_message[:500]
#             db.commit()
#             logger.info(f"✅ Execution {execution_id} marked as 'failed'")
            
#             # Generate summary for failed execution
#             try:
#                 service._generate_summary_from_db(execution_id, ticket_id)
#                 logger.info("✅ Generated summary for failed execution")
#             except Exception as e:
#                 logger.warning(f"⚠️ Could not generate summary for failed execution: {e}")

#     except Exception as e:
#         logger.error(f"❌ Failed to mark execution as failed: {e}")
# this one is correct


# ...existing code...

# Add this BEFORE execute_test_in_background function
def _mark_execution_as_failed(
    db: Session, 
    execution_id: str, 
    error_message: str,
    service: TestExecutionService,
    ticket_id: str
):
    """
    Helper function to mark execution as failed and generate summary
    """
    try:
        execution = db.query(TestExecution).filter(
            TestExecution.execution_id == execution_id
        ).first()

        if execution:
            execution.status = "failed"
            execution.overall_status = "FAILED"
            execution.completed_at = datetime.now()
            execution.error_message = error_message[:500]
            db.commit()
            logger.info(f"✅ Execution {execution_id} marked as 'failed'")
            
            # Try to generate summary for failed execution
            try:
                service._generate_summary_from_db(execution_id, ticket_id)
                logger.info("✅ Generated summary for failed execution")
            except Exception as e:
                logger.warning(f"⚠️ Could not generate summary for failed execution: {e}")

    except Exception as e:
        logger.error(f"❌ Failed to mark execution as failed: {e}")
        db.rollback()


# def execute_test_in_background(
#     execution_id: str,
#     ticket_id: str,
#     project_id: Optional[int]
# ):
#     """
#     Background task - FIXED VERSION
#     """
#     # ...existing code...
class StepData(BaseModel):
    execution_id: str
    steps: list

@app.post("/api/save-steps")
def save_steps(
    data: StepData,
    db: Session = Depends(get_db)
):
    """
    Save execution steps from external runner.
    """
    execution_id = data.execution_id
    steps = data.steps

    # Delete old steps
    db.query(ExecutionStep).filter(ExecutionStep.execution_id == execution_id).delete()
    db.commit()

    saved_count = 0
    for step in steps:
        db.add(ExecutionStep(
            execution_id=execution_id,
            step_num=step.get("step_num"),
            step_text=step.get("step_text"),
            status=step.get("status"),
            selector_used=step.get("selector_used", ""),
            agent_used=step.get("agent_used", ""),
            confidence=step.get("confidence", 0.0),
            action_type=step.get("action_type", ""),
            screenshot_path=step.get("screenshot_path")
        ))
        saved_count += 1
    db.commit()
    return {"saved": saved_count}




# def execute_test_in_background(
#     execution_id: str,
#     ticket_id: str,
#     project_id: Optional[int]
# ):
#     """
#     Background task - FIXED VERSION
#     """
#     db = SessionLocal()
#     service = TestExecutionService(db)
#     final_status_set = False

#     logger.info("="*70)
#     logger.info(f"🚀 BACKGROUND TASK STARTED")
#     logger.info(f"   Execution ID: {execution_id}")
#     logger.info(f"   Ticket ID: {ticket_id}")
#     logger.info("="*70)

#     try:
#         # Step 1: Mark as running
#         execution = db.query(TestExecution).filter(
#             TestExecution.execution_id == execution_id
#         ).first()
#         execution.status = "running"
#         execution.started_at = datetime.now()
#         db.commit()

#         # Step 2: Validate paths
#         external_project_path = Path(settings.external_project_path)
#         plcd_script = external_project_path / "plcd_taseq.py"
        
#         if not plcd_script.exists():
#             raise FileNotFoundError(f"plcd_taseq.py not found: {plcd_script}")

#         # Step 3: Find Python executable
#         python_exe = str(external_project_path / "venv" / "Scripts" / "python.exe")
#         if not Path(python_exe).exists():
#             import shutil
#             python_exe = shutil.which("python") or shutil.which("python3")

#         # Step 4: Execute test with --no-feedback
#         logger.info(f"🏃 Executing: {ticket_id} --no-feedback")
        
#         result = subprocess.run(
#             [python_exe, str(plcd_script), ticket_id, "--no-feedback"],
#             cwd=str(external_project_path),
#             capture_output=True,
#             text=True,
#             timeout=600
#         )

#         logger.info(f"📤 Return code: {result.returncode}")

#         # Step 5: Find artifacts
#         report_path = None
#         script_path = None
#         video_path = None
#         overall_status = "UNKNOWN"

#         reports_folder = external_project_path / "Reports"
#         if reports_folder.exists():
#             reports = sorted(
#                 reports_folder.glob(f"*{ticket_id}*.html"),
#                 key=lambda p: p.stat().st_mtime,
#                 reverse=True
#             )
#             if reports:
#                 report_path = str(reports[0])
#                 logger.info(f"📄 Found report: {reports[0].name}")

#         scripts_folder = external_project_path / "Generated_Scripts"
#         if scripts_folder.exists():
#             scripts = sorted(
#                 scripts_folder.glob(f"*{ticket_id}*.py"),
#                 key=lambda p: p.stat().st_mtime,
#                 reverse=True
#             )
#             if scripts:
#                 script_path = str(scripts[0])

#         videos_folder = external_project_path / "Videos"
#         if videos_folder.exists():
#             videos = sorted(
#                 videos_folder.glob("*.webm"),
#                 key=lambda p: p.stat().st_mtime,
#                 reverse=True
#             )
#             if videos:
#                 video_path = str(videos[0])

#         # Step 6: Parse overall status from report
#         if report_path:
#             try:
#                 with open(report_path, 'r', encoding='utf-8') as f:
#                     html = f.read()
                
#                 # match = re.search(r'Overall\s+Status[:\s]+(PASSED|FAILED)', html, re.IGNORECASE)
#                 # match = re.search(r'Overall\s+Status[:\s]+(PASSED|FAILED)', html, re.IGNORECASE)
#                 # 🔥 FIX: Look for <div class="value status-PASSED">PASSED</div>
#                 match = re.search(r'<div[^>]*class=["\'][^"\']*status-(PASSED|FAILED)[^"\']*["\'][^>]*>\s*(PASSED|FAILED)\s*</div>', html, re.IGNORECASE)
#                 if match:
#                     overall_status = match.group(2).upper()  # Use the text inside the div, not the class name
#                     logger.info(f"✅ Parsed status from div: {overall_status}")
#                 else:
#             # Fallback 1: Try simpler patterns
#                     match = re.search(r'Overall\s+Status[:\s]+(PASSED|FAILED)', html, re.IGNORECASE)
#                 if match:
#                     overall_status = match.group(1).upper()
#                     logger.info(f"✅ Parsed status from text: {overall_status}")
#                 else:
#                     # Fallback: count passed/failed
#                     passed = len(re.findall(r'>\s*PASSED\s*<', html, re.IGNORECASE))
#                     failed = len(re.findall(r'>\s*FAILED\s*<', html, re.IGNORECASE))
#                     overall_status = "FAILED" if failed > 0 else ("PASSED" if passed > 0 else "UNKNOWN")
                
#                 logger.info(f"✅ Parsed status: {overall_status}")
#             except Exception as e:
#                 logger.warning(f"Could not parse status: {e}")

#         # 🔥 Step 7: Parse and save steps FIRST (CRITICAL FIX)
#         # steps_saved = False
#         # if report_path and Path(report_path).exists():
#         #     try:
#         #         logger.info("📥 Parsing steps from report...")
#         #         with open(report_path, 'r', encoding='utf-8') as f:
#         #             html = f.read()

#         #         # 🔥 FIX: Use correct regex for YOUR HTML structure
#         #         table_match = re.search(r'<table[^>]*>(.*?)</table>', html, re.DOTALL | re.IGNORECASE)
                
#         #         if table_match:
#         #             # DELETE old steps FIRST
#         #             deleted = db.query(ExecutionStep).filter(
#         #                 ExecutionStep.execution_id == execution_id
#         #             ).delete()
#         #             db.commit()
#         #             logger.info(f"🧹 Deleted {deleted} old steps")
                    
#         #             # Parse rows
#         #             table_html = table_match.group(1)
#         #             rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL | re.IGNORECASE)
#         #             logger.info(f"📋 Found {len(rows)} rows in table")
                    
#         #             saved_count = 0
#         #             for idx, row in enumerate(rows[1:], start=1):  # Skip header
#         #                 try:
#         #                     # Extract all cells
#         #                     cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL | re.IGNORECASE)
#         #                     logger.info(f"   Row {idx}: Found {len(cells)} cells")
                            
#         #                     if len(cells) < 6:
#         #                         logger.warning(f"   Row {idx}: Skipping (only {len(cells)} cells)")
#         #                         continue
                            
#         #                     # Map to your table structure
#         #                     # step_num = int(re.sub(r'<[^>]+>', '', cells[0]).strip())
#         #                     # step_text = re.sub(r'<[^>]+>', '', cells[1]).strip()[:200]
#         #                     # selector = re.sub(r'<[^>]+>', '', cells[2]).strip()
#         #                     # agent = re.sub(r'<[^>]+>', '', cells[3]).strip()
#         #                     # confidence = 0.0
#         #                     # try:
#         #                     #     confidence_text = re.sub(r'<[^>]+>', '', cells[4]).strip()
#         #                     #     confidence = float(confidence_text)
                            
#         #                     # 🔥 CRITICAL: Extract data from YOUR specific HTML structure
#         #             # Cell 0: Step number
#         #                     step_num = int(re.sub(r'<[^>]+>', '', cells[0]).strip())
                    
#         #             # Cell 1: Step description
#         #                     step_text = re.sub(r'<[^>]+>', '', cells[1]).strip()[:200]
                    
#         #             # Cell 2: Selector (inside <span class="selector">)
#         #                     selector_match = re.search(r'<span[^>]*class=["\']selector["\'][^>]*>(.*?)</span>', cells[2], re.DOTALL | re.IGNORECASE)
#         #                     selector = selector_match.group(1) if selector_match else re.sub(r'<[^>]+>', '', cells[2]).strip()
#         #                     selector = re.sub(r'<[^>]+>', '', selector).strip()  # Clean any remaining tags
                    
#         #             # Cell 3: Agent (inside <span class="badge badge-XXX">)
#         #                     agent_match = re.search(r'<span[^>]*class=["\']badge[^"\']*["\'][^>]*>(.*?)</span>', cells[3], re.DOTALL | re.IGNORECASE)
#         #                     agent = agent_match.group(1) if agent_match else re.sub(r'<[^>]+>', '', cells[3]).strip()
#         #                     agent = re.sub(r'<[^>]+>', '', agent).strip()
                    
#         #             # Cell 4: Confidence
#         #                     confidence = 0.0
#         #                     try:
#         #                         confidence_text = re.sub(r'<[^>]+>', '', cells[4]).strip()
#         #                         confidence = float(confidence_text)
#         #                     except:
#         #                         pass
#         #                     status_text = re.sub(r'<[^>]+>', '', cells[5]).strip()
#         #                     status_match = re.search(r'badge-(PASSED|FAILED|SKIPPED)', cells[5], re.IGNORECASE)
#         #                     if status_match:
#         #                         status = status_match.group(1).upper()
#         #                     else:
#         #                         status = status_text.upper() if status_text.upper() in ['PASSED', 'FAILED', 'SKIPPED'] else 'UNKNOWN'
#         #                     logger.info(f"   Row {idx}: step={step_num}, text='{step_text[:30]}...', status={status}")
#         #                     if step_text and status in ['PASSED', 'FAILED', 'SKIPPED']:
#         #                         step = ExecutionStep(
#         #                             execution_id=execution_id,
#         #                             step_num=step_num,
#         #                             step_text=step_text,
#         #                             status=status,
#         #                             selector_used=selector,
#         #                             agent_used=agent,
#         #                             confidence=confidence,
#         #                             action_type="",
#         #                             screenshot_path=None
#         #                         )
#         #                         db.add(step)
#         #                         saved_count += 1
#         #                 except Exception as row_error:
#         #                     logger.warning(f"⚠️ Failed to parse row {idx}: {row_error}")
#         #                     continue
#         #             db.commit()
#         #             logger.info(f"✅ Saved {saved_count} steps to database")
#         #             # VERIFY steps were saved
#         #             verification = db.query(ExecutionStep).filter(
#         #                 ExecutionStep.execution_id == execution_id
#         #             ).count()
#         #             logger.info(f"🔍 Verification: {verification} steps in DB")
#         #             steps_saved = (verification > 0)
#         #         else:
#         #             logger.warning("⚠️ No <table> found in HTML")
#         #     except Exception as e:
#         #         logger.error(f"❌ Step parsing failed: {e}")
#         #         import traceback
#         #         logger.error(traceback.format_exc())

#         # # Step 8: Update execution record
#         # final_status = "completed" if report_path else "failed"
#         # db.refresh(execution)
#         # execution.status = final_status
#         # execution.overall_status = overall_status
#         # execution.completed_at = datetime.now()
#         # execution.report_path = report_path
#         # execution.script_path = script_path
#         # execution.video_path = video_path
#         # execution.error_message = None if report_path else "No report generated"
#         # db.commit()
#         # final_status_set = True
        
        
        
#         # 🔥 Step 7: Parse and save steps FIRST (CRITICAL FIX)
#         steps_saved = False
#         if report_path and Path(report_path).exists():
#             try:        
#                 logger.info(f"🔥 Parsing steps from report for execution: {execution_id}")
#                 with open(report_path, 'r', encoding='utf-8') as f:
#                     html = f.read()

#         # 🔥 FIX: Use correct regex for YOUR HTML structure
#                 table_match = re.search(r'<table[^>]*>(.*?)</table>', html, re.DOTALL | re.IGNORECASE)
        
#                 if table_match:
#             # DELETE old steps FIRST
#                      deleted = db.query(ExecutionStep).filter(
#                          ExecutionStep.execution_id == execution_id
#                      ).delete()
#                      db.commit()
#                      logger.info(f"🧹 Deleted {deleted} old steps for {execution_id}")
            
#             # Parse rows
#                      table_html = table_match.group(1)
#                      rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL | re.IGNORECASE)
            
#                      logger.info(f"📋 Found {len(rows)} rows in table for {execution_id}")
            
#                      saved_count = 0
#                      for idx, row in enumerate(rows[1:], start=1):  # Skip header
#                          try:
#                     # Extract all cells
#                              cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL | re.IGNORECASE)
                    
#                              if len(cells) < 6:
#                                  continue
                    
#                     # Parse all fields (keeping your existing logic)
#                              step_num = int(re.sub(r'<[^>]+>', '', cells[0]).strip())
#                              step_text = re.sub(r'<[^>]+>', '', cells[1]).strip()[:200]
                    
#                              selector_match = re.search(r'<span[^>]*class=["\']selector["\'][^>]*>(.*?)</span>', cells[2], re.DOTALL | re.IGNORECASE)
#                              selector = selector_match.group(1) if selector_match else re.sub(r'<[^>]+>', '', cells[2]).strip()
#                              selector = re.sub(r'<[^>]+>', '', selector).strip()
                    
#                              agent_match = re.search(r'<span[^>]*class=["\']badge[^"\']*["\'][^>]*>(.*?)</span>', cells[3], re.DOTALL | re.IGNORECASE)
#                              agent = agent_match.group(1) if agent_match else re.sub(r'<[^>]+>', '', cells[3]).strip()
#                              agent = re.sub(r'<[^>]+>', '', agent).strip()
                    
#                              confidence = 0.0
#                              try:
#                                  confidence_text = re.sub(r'<[^>]+>', '', cells[4]).strip()
#                                  confidence = float(confidence_text)
#                              except:
#                                  pass
                    
#                              status_match = re.search(r'<span[^>]*class=["\']badge\s+badge-(PASSED|FAILED|SKIPPED)["\'][^>]*>', cells[5], re.IGNORECASE)
#                              if status_match:
#                                  status = status_match.group(1).upper()
#                              else:
#                                  status_text = re.sub(r'<[^>]+>', '', cells[5]).strip().upper()
#                                  status = status_text if status_text in ['PASSED', 'FAILED', 'SKIPPED'] else 'UNKNOWN'
                    
#                              logger.info(f"   Row {idx}: step={step_num}, text='{step_text[:30]}...', status={status}")
                    
#                              if step_text and status in ['PASSED', 'FAILED', 'SKIPPED']:
#                                  step = ExecutionStep(
#                                      execution_id=execution_id,  # 🔥 CRITICAL: Use correct execution_id
#                                      step_num=step_num,
#                                      step_text=step_text,
#                                      status=status,
#                                      selector_used=selector,
#                                      agent_used=agent,
#                                      confidence=confidence,
#                                      action_type="",
#                                      screenshot_path=None
#                                  )
#                                  db.add(step)
#                                  saved_count += 1
#                                  logger.info(f"   ✅ Added step {step_num} to {execution_id}")
                        
#                          except Exception as row_error:
#                              logger.error(f"   ❌ Failed to parse row {idx}: {row_error}")
#                              continue
            
#                      db.commit()
#                      logger.info(f"✅ Committed {saved_count} steps to database for {execution_id}")
            
#             # VERIFY steps were saved
#                      verification = db.query(ExecutionStep).filter(
#                          ExecutionStep.execution_id == execution_id
#                      ).count()
#                      logger.info(f"🔍 Verification: {verification} steps in DB for {execution_id}")
            
#                      if verification > 0:
#                          steps_saved = True
#                          logger.info(f"✅ Steps successfully saved for {execution_id}")
#                      else:
#                          logger.error(f"❌ CRITICAL: No steps in DB for {execution_id} after commit!")
#                 else:
#                     logger.error(f"❌ No <table> found in HTML report for {execution_id}")
            
#             except Exception as e:
#                    logger.error(f"❌ Step parsing failed for {execution_id}: {e}")
#                    import traceback
#                    logger.error(traceback.format_exc())

# # Step 8: Update execution record
#         final_status = "completed" if report_path else "failed"
#         db.refresh(execution)
#         execution.status = final_status
#         execution.overall_status = overall_status
#         execution.completed_at = datetime.now()
#         execution.report_path = report_path
#         execution.script_path = script_path
#         execution.video_path = video_path
#         execution.error_message = None if report_path else "No report generated"
#         db.commit()
#         final_status_set = True

#         logger.info(f"✅ Execution {execution_id} marked as '{final_status}'")

#         # Step 9: Generate summary AFTER steps are saved
#         if steps_saved:
#                 logger.info("📊 Generating summary...")
#         try:
#             service._generate_summary_from_db(execution_id, ticket_id)
#             summary_path = external_project_path / "Reports" / "summaries" / f"summary_{ticket_id}_latest.json"
#             if summary_path.exists():
#                         logger.info(f"✅ Summary generated: {summary_path}")
#             else:
#                         logger.error(f"❌ Summary file NOT created")
#         except Exception as summary_error:
#                 logger.error(f"⚠️ Summary generation failed: {summary_error}")
#                 import traceback
#                 logger.error(traceback.format_exc())
#         else:
#             logger.warning("⚠️ Skipping summary generation - no steps in database")

#         logger.info("="*70)
#         logger.info("✅ EXECUTION COMPLETED")
#         logger.info(f"   Status: {final_status} / {overall_status}")
#         logger.info(f"   Report: {report_path}")
#         logger.info("="*70)

#     except Exception as e:
#         logger.error(f"❌ EXECUTION FAILED: {e}")
#         import traceback
#         logger.error(traceback.format_exc())
#         _mark_execution_as_failed(db, execution_id, str(e)[:500], service, ticket_id)
#         final_status_set = True

#     finally:
#         if not final_status_set:
#             logger.warning("⚠️ Forcing execution to failed state")
#             execution = db.query(TestExecution).filter(
#                 TestExecution.execution_id == execution_id
#             ).first()
#             if execution and execution.status == "running":
#                 execution.status = "failed"
#                 execution.completed_at = datetime.now()
#                 db.commit()
#         db.close()
#         logger.info(f"🔒 Session closed: {execution_id}\n")


logger.error("🔥 execute_test_in_background CALLED")

def execute_test_in_background(
    execution_id: str,
    ticket_id: str,
    project_id: Optional[int]
):
    """
    Background task - FIXED VERSION WITH PROPER EXECUTION ID HANDLING
    """
    db = SessionLocal()
    service = TestExecutionService(db)
    final_status_set = False

    # 🔥 LOG THE EXECUTION ID AT THE VERY START
    logger.info("="*70)
    logger.info(f"🚀 BACKGROUND TASK STARTED")
    logger.info(f"   🆔 Execution ID: {execution_id}")  # <-- CRITICAL
    logger.info(f"   🎫 Ticket ID: {ticket_id}")
    logger.info("="*70)

    try:
        # Step 1: Mark as running
        execution = db.query(TestExecution).filter(
            TestExecution.execution_id == execution_id
        ).first()
        
        if not execution:
            logger.error(f"❌ Execution {execution_id} not found in database!")
            return
            
        execution.status = "running"
        execution.started_at = datetime.now()
        db.commit()
        logger.info(f"✅ Status updated to 'running' for {execution_id}")

        # Step 2: Validate paths
        external_project_path = Path(settings.external_project_path)
        plcd_script = external_project_path / "plcd_taseq.py"
        
        if not plcd_script.exists():
            raise FileNotFoundError(f"plcd_taseq.py not found: {plcd_script}")

        # Step 3: Find Python executable
        python_exe = str(external_project_path / "venv" / "Scripts" / "python.exe")
        if not Path(python_exe).exists():
            import shutil
            python_exe = shutil.which("python") or shutil.which("python3")

        # Step 4: Execute test with --no-feedback
        logger.info(f"🏃 Executing: {ticket_id} --no-feedback for {execution_id}")
        
        result = subprocess.run(
            [python_exe, str(plcd_script), ticket_id, "--no-feedback"],
            cwd=str(external_project_path),
            capture_output=True,
            text=True,
            timeout=600
        )
        
        # ===============================
# LOAD REAL STEPS FROM plcd_taseq
# ===============================

        # steps_file = external_project_path / "Reports" / "steps" / f"steps_{ticket_id}.json"
        # steps_saved = False
        
        # if steps_file.exists():
        #     with open(steps_file, "r", encoding="utf-8") as f:
        #         real_steps = json.load(f)

        #     # logger.info(f"📥 Loaded {len(real_steps)} real steps from plcd_taseq")
        #     logger.info(f"Loaded {len(real_steps)} steps from JSON")

        #     service._save_steps_to_db(execution_id, real_steps)
        # else:
        #     logger.warning("⚠️ No step file found from plcd_taseq")


        # logger.info(f"📤 Return code: {result.returncode} for {execution_id}")
        # ===============================
# LOAD REAL STEPS FROM plcd_taseq
# ===============================

        steps_file = external_project_path / "Reports" / "steps" / f"steps_{ticket_id}.json"

        steps_saved = False

        if steps_file.exists():
            with open(steps_file, "r", encoding="utf-8") as f:
                raw_steps = json.load(f)

            logger.info(f"Loaded {len(raw_steps)} steps from JSON")

    # 🔥 NORMALIZE STEP FORMAT FOR DB
            normalized_steps = []
            for step in raw_steps:
                normalized_steps.append({
                    "step_number": step.get("step_number"),
                    "step_text": step.get("step_text"),
                    "selector": step.get("selector"),   # maps to selector_used
                    "status": step.get("status"),
                    "confidence": step.get("confidence", 0.0),
                    "agent_used": step.get("agent_used"),
                    "action_type": step.get("action_type"),
                })

            service._save_steps_to_db(execution_id, normalized_steps)
            steps_saved = True

            logger.info(f"Saved {len(normalized_steps)} steps to DB")
        else:
            logger.error("Steps JSON file not found, skipping DB save")
        
        # ===============================
# GENERATE SUMMARY (ONLY IF STEPS EXIST)
# ===============================
        if steps_saved:
            service._generate_summary_from_db(execution_id, ticket_id)
        else:
            logger.error("Summary skipped because no steps were saved")



        # Step 5: Find artifacts
        report_path = None
        script_path = None
        video_path = None
        overall_status = "UNKNOWN"

        reports_folder = external_project_path / "Reports"
        if reports_folder.exists():
            reports = sorted(
                reports_folder.glob(f"*{ticket_id}*.html"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            if reports:
                report_path = str(reports[0])
                logger.info(f"📄 Found report: {reports[0].name} for {execution_id}")

        scripts_folder = external_project_path / "Generated_Scripts"
        if scripts_folder.exists():
            scripts = sorted(
                scripts_folder.glob(f"*{ticket_id}*.py"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            if scripts:
                script_path = str(scripts[0])

        videos_folder = external_project_path / "Videos"
        if videos_folder.exists():
            videos = sorted(
                videos_folder.glob("*.webm"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            if videos:
                video_path = str(videos[0])

        # Step 6: Parse overall status from report
        if report_path:
            try:
                with open(report_path, 'r', encoding='utf-8') as f:
                    html = f.read()
                
                # 🔥 FIX: Look for <div class="value status-PASSED">PASSED</div>
                match = re.search(r'<div[^>]*class=["\'][^"\']*status-(PASSED|FAILED)[^"\']*["\'][^>]*>\s*(PASSED|FAILED)\s*</div>', html, re.IGNORECASE)
                if match:
                    overall_status = match.group(2).upper()
                    logger.info(f"✅ Parsed status: {overall_status} for {execution_id}")
                else:
                    # Fallback
                    passed = len(re.findall(r'>\s*PASSED\s*<', html, re.IGNORECASE))
                    failed = len(re.findall(r'>\s*FAILED\s*<', html, re.IGNORECASE))
                    overall_status = "FAILED" if failed > 0 else ("PASSED" if passed > 0 else "UNKNOWN")
                    logger.info(f"📊 Inferred status: {overall_status} for {execution_id}")
                    
            except Exception as e:
                logger.warning(f"Could not parse status for {execution_id}: {e}")

        # 🔥 Step 7: Parse and save steps - CRITICAL FIX
        steps_saved = False
        if report_path and Path(report_path).exists():
            try:
                logger.info(f"🔥 Parsing steps from report for {execution_id}")
                with open(report_path, 'r', encoding='utf-8') as f:
                    html = f.read()

                table_match = re.search(r'<table[^>]*>(.*?)</table>', html, re.DOTALL | re.IGNORECASE)
                
                if table_match:
                    # 🔥 DELETE old steps for THIS execution_id ONLY
                    logger.info(f"🧹 Deleting old steps for {execution_id}")
                    deleted = db.query(ExecutionStep).filter(
                        ExecutionStep.execution_id == execution_id
                    ).delete()
                    db.commit()
                    logger.info(f"🧹 Deleted {deleted} old steps for {execution_id}")
                    
                    # Parse rows
                    table_html = table_match.group(1)
                    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL | re.IGNORECASE)
                    
                    logger.info(f"📋 Found {len(rows)} rows in table for {execution_id}")
                    
                    saved_count = 0
                    for idx, row in enumerate(rows[1:], start=1):  # Skip header
                        try:
                            cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL | re.IGNORECASE)
                            
                            if len(cells) < 6:
                                continue
                            
                            # Parse fields
                            step_num = int(re.sub(r'<[^>]+>', '', cells[0]).strip())
                            step_text = re.sub(r'<[^>]+>', '', cells[1]).strip()[:200]
                            
                            selector_match = re.search(r'<span[^>]*class=["\']selector["\'][^>]*>(.*?)</span>', cells[2], re.DOTALL | re.IGNORECASE)
                            selector = selector_match.group(1) if selector_match else re.sub(r'<[^>]+>', '', cells[2]).strip()
                            selector = re.sub(r'<[^>]+>', '', selector).strip()
                            
                            agent_match = re.search(r'<span[^>]*class=["\']badge[^"\']*["\'][^>]*>(.*?)</span>', cells[3], re.DOTALL | re.IGNORECASE)
                            agent = agent_match.group(1) if agent_match else re.sub(r'<[^>]+>', '', cells[3]).strip()
                            agent = re.sub(r'<[^>]+>', '', agent).strip()
                            
                            confidence = 0.0
                            try:
                                confidence_text = re.sub(r'<[^>]+>', '', cells[4]).strip()
                                confidence = float(confidence_text)
                            except:
                                pass
                            
                            status_match = re.search(r'<span[^>]*class=["\']badge\s+badge-(PASSED|FAILED|SKIPPED)["\'][^>]*>', cells[5], re.IGNORECASE)
                            if status_match:
                                status = status_match.group(1).upper()
                            else:
                                status_text = re.sub(r'<[^>]+>', '', cells[5]).strip().upper()
                                status = status_text if status_text in ['PASSED', 'FAILED', 'SKIPPED'] else 'UNKNOWN'
                            
                            if step_text and status in ['PASSED', 'FAILED', 'SKIPPED']:
                                # 🔥 CRITICAL: Use the correct execution_id
                                step = ExecutionStep(
                                    execution_id=execution_id,  # <-- THIS MUST BE CORRECT
                                    step_num=step_num,
                                    step_text=step_text,
                                    status=status,
                                    selector_used=selector,
                                    agent_used=agent,
                                    confidence=confidence,
                                    action_type="",
                                    screenshot_path=None
                                )
                                db.add(step)
                                saved_count += 1
                                
                        except Exception as row_error:
                            logger.error(f"❌ Failed to parse row {idx} for {execution_id}: {row_error}")
                            continue
                    
                    # 🔥 COMMIT ALL STEPS AT ONCE
                    db.commit()
                    logger.info(f"✅ Committed {saved_count} steps for {execution_id}")
                    
                    # 🔥 VERIFY - Use execution_id from this function scope
                    verification = db.query(ExecutionStep).filter(
                        ExecutionStep.execution_id == execution_id
                    ).count()
                    logger.info(f"🔍 Verification: {verification} steps in DB for {execution_id}")
                    
                    steps_saved = (verification > 0)
                else:
                    logger.error(f"❌ No <table> found in HTML for {execution_id}")
                    
            except Exception as e:
                logger.error(f"❌ Step parsing failed for {execution_id}: {e}")
                import traceback
                logger.error(traceback.format_exc())

        # Step 8: Update execution record
        final_status = "completed" if report_path else "failed"
        db.refresh(execution)
        execution.status = final_status
        execution.overall_status = overall_status
        execution.completed_at = datetime.now()
        execution.report_path = report_path
        execution.script_path = script_path
        execution.video_path = video_path
        execution.error_message = None if report_path else "No report generated"
        db.commit()
        final_status_set = True

        logger.info(f"✅ Execution {execution_id} marked as '{final_status}'")

        # Step 9: Generate summary - ALWAYS RUN
        logger.info(f"📊 Generating summary for {execution_id} (steps_saved={steps_saved})...")
        try:
            
            # 🔥 TEMP DEBUG: force one step into DB
            # logger.error("🔥 FORCING DUMMY STEP SAVE")

            # dummy_steps = [{
            #     "step_number": 1,
            #     "step_text": "Dummy step for validation",
            #     "status": "PASSED",
            #     "selector": "",
            #     "agent_used": "SYSTEM",
            #     "confidence": 1.0,
            #     "action_type": "VALIDATION"
            # }]

            # service._save_steps_to_db(execution_id, dummy_steps)

            # 🔥 PASS THE CORRECT execution_id
            # service._generate_summary_from_db(execution_id, ticket_id)
            
            summary_path = external_project_path / "Reports" / "summaries" / f"summary_{ticket_id}_latest.json"
            if summary_path.exists():
                logger.info(f"✅ Summary generated: {summary_path}")
            else:
                logger.error(f"❌ Summary NOT created at: {summary_path}")
                
        except Exception as summary_error:
            logger.error(f"❌ Summary generation failed for {execution_id}: {summary_error}")
            import traceback
            logger.error(traceback.format_exc())

        logger.info("="*70)
        logger.info(f"✅ EXECUTION COMPLETED for {execution_id}")
        logger.info(f"   Status: {final_status} / {overall_status}")
        logger.info(f"   Report: {report_path}")
        logger.info("="*70)

    except Exception as e:
        logger.error(f"❌ EXECUTION FAILED for {execution_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        _mark_execution_as_failed(db, execution_id, str(e)[:500], service, ticket_id)
        final_status_set = True

    finally:
        if not final_status_set:
            logger.warning(f"⚠️ Forcing {execution_id} to failed state")
            execution = db.query(TestExecution).filter(
                TestExecution.execution_id == execution_id
            ).first()
            if execution and execution.status == "running":
                execution.status = "failed"
                execution.completed_at = datetime.now()
                db.commit()
        db.close()
        logger.info(f"🔒 Session closed: {execution_id}\n")


## Key Changes

# 1. **Added `execution_id` to EVERY log message** so you can track which execution is being processed
# 2. **Ensured `execution_id` is used consistently** throughout the function
# 3. **Added verification** that steps are being saved to the correct execution_id
# 4. **Made summary generation always run** regardless of steps_saved status

## After Applying

# 1. **Save `main.py`**
# 2. **Restart FastAPI**
# 3. **Run a new test**
# 4. **Check logs** - you should now see:
# ```
#    🆔 Execution ID: exec_RBPLCD-8960_20260111_XXXXXX
#    ...
#    ✅ Committed 7 steps for exec_RBPLCD-8960_20260111_XXXXXX
#    🔍 Verification: 7 steps in DB for exec_RBPLCD-8960_20260111_XXXXXX
#    📊 Generating summary for exec_RBPLCD-8960_20260111_XXXXXX (steps_saved=True)...
#    ✅ Summary generated: C:\...\summary_RBPLCD-8960_latest.json







# def execute_test_in_background(
#     execution_id: str,
#     ticket_id: str,
#     # project_id: int
#     project_id: Optional[int]  # 🟢 CHANGE THIS - Allow None

# ):
#     """
#     Background task to execute test workflow using external run_test.py
#     FIXED: Better error handling and ensures completion
#     """
#     db = SessionLocal()
#     service = TestExecutionService(db)

#     logger.info("="*70)
#     logger.info(f"🚀 BACKGROUND TASK STARTED")
#     logger.info(f"   Execution ID: {execution_id}")
#     logger.info(f"   Ticket ID: {ticket_id}")
#     logger.info(f"   Project ID: {project_id}")  # 🟢 ADD THIS LINE
#     logger.info(f"   External Path: {settings.external_project_path}")
#     logger.info(f"   Started at: {datetime.now().isoformat()}")
#     logger.info("="*70)

#     try:
#         # Update status to running
#         service.update_execution_status(
#             execution_id=execution_id,
#             status="running"
#         )
#         logger.info("✅ Status updated to 'running'")

#         # Path to your external TA_AI_Project
#         external_project_path = settings.external_project_path

#         logger.info(f"📁 External project path: {external_project_path}")

#         # Verify path exists
#         if not Path(external_project_path).exists():
#             raise FileNotFoundError(f"External project not found: {external_project_path}")
#             logger.info("✅ External project path exists")

#        # Check if plcd_taseq.py exists
#         plcd_script = Path(external_project_path) / "plcd_taseq.py"
#         if not plcd_script.exists():
#             raise FileNotFoundError(f"plcd_taseq.py not found at: {plcd_script}")
#         logger.info(f"✅ Found plcd_taseq.py at: {plcd_script}")


#         logger.info("🏃 Starting test workflow execution...")
#         # CRITICAL: Add logging around this call
#         logger.info("📞 Calling service.run_test_workflow()...")

#         # Run test workflow (this will now wait for completion)
#         state = service.run_test_workflow(
#             ticket_id=ticket_id,
#             project_id=project_id,
#             execution_id=execution_id,
#             external_project_path=external_project_path
#         )
#         logger.info(f"📋 Workflow returned state: {state}")


# # Log what we got back
#         if state:
#             logger.info(f"📄 Report path: {state.get('report_path')}")
#             logger.info(f"📜 Script path: {state.get('script_path')}")
#             logger.info(f"🎥 Video path: {state.get('video_path')}")
#             logger.info(f"📊 Overall status: {state.get('overall_status')}")
#         else:
#             logger.warning("⚠️  Workflow returned None or empty state!")

#         logger.info("✅ Test workflow completed, saving results to database...")

#         # Save results to database (steps are already saved in run_test_workflow)
#         service.save_execution_results(execution_id, state)
#         service._generate_summary_from_db(execution_id, ticket_id)
#         # Determine if we should mark as 'completed' or 'failed'
#         # If we have a report, mark as 'completed' even if tests failed
#         has_report = bool(state.get('report_path'))
#         overall_status = state.get('overall_status', 'UNKNOWN')


#         if has_report:
#             # Mark as completed - user can download report
#             final_status = "completed"
#             logger.info(f"✅ Marking as completed (report available, status: {overall_status})")
#         else:
#             # No report - mark as failed
#             final_status = "failed"
#             logger.warning(f"⚠️  Marking as failed (no report generated)")


#         # Update status to completed
#         service.update_execution_status(
#             execution_id=execution_id,
#             status=final_status,
#             overall_status=overall_status,
#             report_path=state.get('report_path', ''),
#             script_path=state.get('script_path', ''),
#             video_path=state.get('video_path', ''),
#             error_message=None  # Clear any error message if we have results
#         )

#         logger.info("="*70)
#         logger.info("✅ TEST EXECUTION COMPLETED SUCCESSFULLY")
#         logger.info(f"   Execution ID: {execution_id}")
#         logger.info(f"   Overall Status: {state.get('overall_status', 'UNKNOWN')}")
#         logger.info(f"   📄 Report: {state.get('report_path', 'N/A')}")
#         logger.info(f"   📜 Script: {state.get('script_path', 'N/A')}")
#         logger.info(f"   🎥 Video: {state.get('video_path', 'N/A')}")
#         logger.info(f"   Completed at: {datetime.now().isoformat()}")
#         logger.info("="*70)

#     except Exception as e:
#         logger.error("="*70)
#         logger.error(f"❌ BACKGROUND TASK FAILED")
#         logger.error(f"   Execution ID: {execution_id}")
#         logger.error(f"   Error: {e}")
#         logger.error(f"   Failed at: {datetime.now().isoformat()}")
#         logger.error("="*70)

#  # Log full traceback
#         import traceback
#         logger.error("Full traceback:")
#         logger.error(traceback.format_exc())

#         # Get detailed error message
#         error_str = str(e)
#         error_lines = []
#         for line in error_str.split('\n'):
#             if not line.strip().startswith('[INFO]') and not line.strip().startswith('[DEBUG]'):
#                 if line.strip():
#                     error_lines.append(line.strip())

#         clean_error = '\n'.join(error_lines[:10]) if error_lines else str(e)

#         # Truncate if too long
#         if len(clean_error) > 500:
#             clean_error = clean_error[:500] + "...\n(Check server logs for full details)"


#         # Mark as failed in database
#         try:
#             service.update_execution_status(
#                 execution_id=execution_id,
#                 status="failed",
#                 overall_status="FAILED",
#                 error_message=clean_error
#             )
#             logger.info("✅ Updated execution status to 'failed' in database")
#         except Exception as db_error:
#             logger.error(f"❌ Could not update database with failure: {db_error}")

#         # Log full traceback
#         import traceback
#         logger.error("Full traceback:")
#         logger.error(traceback.format_exc())

#     finally:
#         db.close()
#         logger.info(f"🏁 Background task ended for {execution_id}")
#         logger.info("")  # Empty line for readability

# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower()
    )
