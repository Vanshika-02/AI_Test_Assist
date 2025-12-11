"""
FastAPI Application for Test Automation Backend - CLEANED VERSION
"""
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from pathlib import Path
import logging
import re  # Add this import

from config import settings
from utils import setup_logging
from database import engine, get_db, Base, SessionLocal
from models import Ticket, TestExecution, ExecutionStep
from services import TestExecutionService
from jira_api import router as jira_router  # 🟢 ADD THIS LINE
from typing import Optional
import os
import requests
from dotenv import load_dotenv

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
        logger.info(f"🏃 Executing script: {script_path}")

        result = subprocess.run(
            [python_exe, script_path],
            cwd=str(external_project_path),
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes timeout
        )

        logger.info(f"📤 Script execution completed with return code: {result.returncode}")

        # Log output
        if result.stdout:
            logger.info(f"STDOUT:\n{result.stdout[:1000]}")  # First 1000 chars
        if result.stderr:
            logger.warning(f"STDERR:\n{result.stderr[:1000]}")

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
            progress = int((completed_steps / total_steps) * 100)

            last_step = db.query(ExecutionStep).filter(
                ExecutionStep.execution_id == execution_id
            ).order_by(ExecutionStep.step_num.desc()).first()

            if last_step:
                current_step = last_step.step_text
                message = f"Executing Step {completed_steps + 1}/{total_steps}..."
        else:
            progress = 10
            message = "Parsing JIRA ticket and preparing test steps..."
    elif execution.status == "completed":
        progress = 100
        message = f"Test execution completed - {execution.overall_status}"
    elif execution.status == "failed":
        progress = 100
        message = execution.error_message or "Test execution failed"

    # 🆕 ADD THIS: Check if summary exists
    summary_available = False
    if execution.status == "completed" and execution.ticket_id:
        external_path = Path(settings.external_project_path)
        summary_path = external_path / "Reports" / "summaries" / f"summary_{execution.ticket_id}_latest.json"
        summary_available = summary_path.exists()
        logger.info(f"📊 Summary check for {execution.ticket_id}: {summary_available} (path: {summary_path})")

    return {
        "execution_id": execution.execution_id,
        "ticket_id": execution.ticket_id,
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
        "summary_available": summary_available  # 🆕 NEW FIELD
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
from pathlib import Path
import json

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


@app.get("/api/debug/parse-report/{execution_id}")
def debug_parse_report(execution_id: str, db: Session = Depends(get_db)):
    """
    Debug endpoint to show what we're parsing from the report
    """
    try:
        execution = db.query(TestExecution).filter(
            TestExecution.execution_id == execution_id
        ).first()

        if not execution or not execution.report_path:
            return {"error": "No report path found"}

        report_path = Path(execution.report_path)

        if not report_path.exists():
            return {"error": f"Report not found: {report_path}"}

        with open(report_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        import re

        # Extract key parts
        result = {
            "execution_id": execution_id,
            "report_path": str(report_path),
            "report_size": len(html_content),
            "patterns_found": {}
        }

        # Check for overall status patterns
        overall_patterns = {
            "h2_overall_status": r'<h2[^>]*>\s*Overall\s+Status:\s*(PASSED|FAILED)\s*</h2>',
            "div_overall_status": r'<div[^>]*class=["\']overall-status[^"\']*["\'][^>]*>\s*(PASSED|FAILED)',
            "generic_status": r'Overall\s+Status:\s*<[^>]+>\s*(PASSED|FAILED)',
        }

        for name, pattern in overall_patterns.items():
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                result["patterns_found"][name] = match.group(1).upper()

        # Count step statuses
        step_table = re.search(r'<table[^>]*>(.*?)</table>', html_content, re.DOTALL | re.IGNORECASE)
        if step_table:
            table_content = step_table.group(1)

            passed_in_table = len(re.findall(r'>\s*PASSED\s*<', table_content, re.IGNORECASE))
            failed_in_table = len(re.findall(r'>\s*FAILED\s*<', table_content, re.IGNORECASE))

            result["step_table"] = {
                "found": True,
                "passed_count": passed_in_table,
                "failed_count": failed_in_table
            }

        # Count all occurrences
        all_passed = len(re.findall(r'\bPASSED\b', html_content))
        all_failed = len(re.findall(r'\bFAILED\b', html_content))

        result["word_counts"] = {
            "passed": all_passed,
            "failed": all_failed
        }

        # Extract a snippet around "Overall Status" if found
        status_match = re.search(r'.{0,200}Overall\s+Status.{0,200}', html_content, re.IGNORECASE | re.DOTALL)
        if status_match:
            result["status_snippet"] = status_match.group(0)

        # Get first 1000 chars of HTML for inspection
        result["html_preview"] = html_content[:1000]

        return result

    except Exception as e:
        logger.error(f"Debug parse report error: {e}", exc_info=True)
        return {"error": str(e)}


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


# ============================================================================
# BACKGROUND TASK
# ============================================================================

"""
REPLACE the execute_test_in_background function in your main.py with this version
This ensures proper completion and error handling
"""

def execute_test_in_background(
    execution_id: str,
    ticket_id: str,
    # project_id: int
    project_id: Optional[int]  # 🟢 CHANGE THIS - Allow None

):
    """
    Background task to execute test workflow using external run_test.py
    FIXED: Better error handling and ensures completion
    """
    db = SessionLocal()
    service = TestExecutionService(db)

    logger.info("="*70)
    logger.info(f"🚀 BACKGROUND TASK STARTED")
    logger.info(f"   Execution ID: {execution_id}")
    logger.info(f"   Ticket ID: {ticket_id}")
    logger.info(f"   Project ID: {project_id}")  # 🟢 ADD THIS LINE
    logger.info(f"   External Path: {settings.external_project_path}")
    logger.info(f"   Started at: {datetime.now().isoformat()}")
    logger.info("="*70)

    try:
        # Update status to running
        service.update_execution_status(
            execution_id=execution_id,
            status="running"
        )
        logger.info("✅ Status updated to 'running'")

        # Path to your external TA_AI_Project
        external_project_path = settings.external_project_path

        logger.info(f"📁 External project path: {external_project_path}")

        # Verify path exists
        if not Path(external_project_path).exists():
            raise FileNotFoundError(f"External project not found: {external_project_path}")
            logger.info("✅ External project path exists")

       # Check if plcd_taseq.py exists
        plcd_script = Path(external_project_path) / "plcd_taseq.py"
        if not plcd_script.exists():
            raise FileNotFoundError(f"plcd_taseq.py not found at: {plcd_script}")
        logger.info(f"✅ Found plcd_taseq.py at: {plcd_script}")


        logger.info("🏃 Starting test workflow execution...")
        # CRITICAL: Add logging around this call
        logger.info("📞 Calling service.run_test_workflow()...")

        # Run test workflow (this will now wait for completion)
        state = service.run_test_workflow(
            ticket_id=ticket_id,
            project_id=project_id,
            execution_id=execution_id,
            external_project_path=external_project_path
        )
        logger.info(f"📋 Workflow returned state: {state}")


# Log what we got back
        if state:
            logger.info(f"📄 Report path: {state.get('report_path')}")
            logger.info(f"📜 Script path: {state.get('script_path')}")
            logger.info(f"🎥 Video path: {state.get('video_path')}")
            logger.info(f"📊 Overall status: {state.get('overall_status')}")
        else:
            logger.warning("⚠️  Workflow returned None or empty state!")

        logger.info("✅ Test workflow completed, saving results to database...")

        # Save results to database (steps are already saved in run_test_workflow)
        service.save_execution_results(execution_id, state)
        # Determine if we should mark as 'completed' or 'failed'
        # If we have a report, mark as 'completed' even if tests failed
        has_report = bool(state.get('report_path'))
        overall_status = state.get('overall_status', 'UNKNOWN')


        if has_report:
            # Mark as completed - user can download report
            final_status = "completed"
            logger.info(f"✅ Marking as completed (report available, status: {overall_status})")
        else:
            # No report - mark as failed
            final_status = "failed"
            logger.warning(f"⚠️  Marking as failed (no report generated)")


        # Update status to completed
        service.update_execution_status(
            execution_id=execution_id,
            status=final_status,
            overall_status=overall_status,
            report_path=state.get('report_path', ''),
            script_path=state.get('script_path', ''),
            video_path=state.get('video_path', ''),
            error_message=None  # Clear any error message if we have results
        )

        logger.info("="*70)
        logger.info("✅ TEST EXECUTION COMPLETED SUCCESSFULLY")
        logger.info(f"   Execution ID: {execution_id}")
        logger.info(f"   Overall Status: {state.get('overall_status', 'UNKNOWN')}")
        logger.info(f"   📄 Report: {state.get('report_path', 'N/A')}")
        logger.info(f"   📜 Script: {state.get('script_path', 'N/A')}")
        logger.info(f"   🎥 Video: {state.get('video_path', 'N/A')}")
        logger.info(f"   Completed at: {datetime.now().isoformat()}")
        logger.info("="*70)

    except Exception as e:
        logger.error("="*70)
        logger.error(f"❌ BACKGROUND TASK FAILED")
        logger.error(f"   Execution ID: {execution_id}")
        logger.error(f"   Error: {e}")
        logger.error(f"   Failed at: {datetime.now().isoformat()}")
        logger.error("="*70)

 # Log full traceback
        import traceback
        logger.error("Full traceback:")
        logger.error(traceback.format_exc())

        # Get detailed error message
        error_str = str(e)
        error_lines = []
        for line in error_str.split('\n'):
            if not line.strip().startswith('[INFO]') and not line.strip().startswith('[DEBUG]'):
                if line.strip():
                    error_lines.append(line.strip())

        clean_error = '\n'.join(error_lines[:10]) if error_lines else str(e)

        # Truncate if too long
        if len(clean_error) > 500:
            clean_error = clean_error[:500] + "...\n(Check server logs for full details)"


        # Mark as failed in database
        try:
            service.update_execution_status(
                execution_id=execution_id,
                status="failed",
                overall_status="FAILED",
                error_message=error_message
            )
            logger.info("✅ Updated execution status to 'failed' in database")
        except Exception as db_error:
            logger.error(f"❌ Could not update database with failure: {db_error}")

        # Log full traceback
        import traceback
        logger.error("Full traceback:")
        logger.error(traceback.format_exc())

    finally:
        db.close()
        logger.info(f"🏁 Background task ended for {execution_id}")
        logger.info("")  # Empty line for readability


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
