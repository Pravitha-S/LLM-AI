from fastapi import APIRouter
from database.models import get_token_status

router = APIRouter()

@router.get("/status/{token_id}")
async def get_status(token_id: str):
    data = get_token_status(token_id.upper())
    if data:
        return {
            "found": True,
            "token_id": data["token_id"],
            "patient_name": data["patient_name"],
            "doctor": data["doctor"],
            "department": data["department"],
            "status": data["status"],
            "queue_position": data.get("queue_position")
        }
    return {"found": False}