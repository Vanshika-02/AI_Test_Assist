from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
from pathlib import Path
# from main import generate_embedding
from embedding_utils import generate_embedding
import json

router = APIRouter()

class SelectorFeedback(BaseModel):
    ticket_id: str
    step_number: int
    step_text: str
    corrected_selector: str
    module: str
    action_type: str
    status: str

# def generate_embedding(selector: str):
#     # Replace with your actual embedding logic
#     # return [0.1, 0.2, 0.3]
#     insight['embedding'] = generate_embedding(f"{step_text} {module}".strip())
    

@router.post("/api/selector-feedback")
def submit_selector_feedback(feedback: SelectorFeedback):
    # embedding = generate_embedding(feedback.corrected_selector)
    embedding_text = f"{feedback.step_text} {feedback.module}".strip()
    embedding = generate_embedding(embedding_text)
    feedback_dir = Path("C:/Idea Projects/AI_Test_Assist/insights/pending")
    feedback_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"{feedback.ticket_id}_step{feedback.step_number}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
    file_path = feedback_dir / file_name
    # with open(file_path, "w", encoding="utf-8") as f:
    #     json.dump({
    #         "step": feedback.step_text,
    #         "selector": feedback.corrected_selector,
    #         "confidence": 0.95,
    #         "category": "failed" if feedback.status == "FAILED" else "suspicious",
    #         "module": feedback.module,
    #         "context": {
    #             "action_type": feedback.action_type,
    #             "current_module": feedback.module
    #         },
    #         "metadata": {
    #             "ticket_id": feedback.ticket_id,
    #             "step_number": feedback.step_number,
    #             "timestamp": datetime.now().isoformat(),
    #             "issue_description": "selector not found" if feedback.status == "FAILED" else "manual correction",
    #             "source": "tester_feedback"
    #         },
    #         "embedding": embedding
    #     }, f, indent=2)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump({
            "step": feedback.step_text,
            "selector": feedback.corrected_selector,
            "confidence": 0.95,
            "category": "failed",
            "module": feedback.module,
            "context": {
            "module": feedback.module,
            "action_type": "click",  # or use feedback.action_type if appropriate
            "sequential_context": {
                "previous_steps": [],
                "last_successful_action": None,
                "last_selector_used": None,
                "page_state_before_failure": "After step 1",
                "current_module": feedback.module
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
        "embedding": embedding
    }, f, indent=2)
    return {"message": "Feedback saved"}