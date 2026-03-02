from fastapi import APIRouter
from pydantic import BaseModel
import uuid
import re
from services.llm_service import get_llm_response
from database.models import save_query, get_token_status, save_chat_history

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    session_id: str = None

@router.post("/chat")
async def chat(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())
    msg = req.message
    save_chat_history(session_id, "user", msg)
    

    # Check if asking about token inline
    if "token" in msg.lower():
        token_match = re.search(r'KSD\d{4}|\b\d{4}\b', msg.upper())
        if token_match:
            token_id = token_match.group()
            if not token_id.startswith('KSD'):
                token_id = 'KSD' + token_id
            data = get_token_status(token_id)
            if data:
                response = (
                    f"Token <strong>{data['token_id']}</strong><br/>"
                    f"Patient: {data['patient_name']}<br/>"
                    f"Doctor: {data['doctor']}<br/>"
                    f"Status: <strong>{data['status']}</strong>"
                )
                if data.get('queue_position'):
                    response += f"<br/>Queue Position: #{data['queue_position']}"
                
                save_chat_history(session_id, "assistant", response)
                save_query(session_id, msg, response)
                return {"response": response, "session_id": session_id}
    
    # RAG + LLM response
    response = get_llm_response(msg)
    save_chat_history(session_id, "assistant", response)
    save_query(session_id, msg, response)
    print(f"\n{'='*40}")
    print(f"USER: {req.message}")
    print(f"BOT:  {response[:100]}...")
    print(f"{'='*40}\n")
    return {"response": response, "session_id": session_id}
