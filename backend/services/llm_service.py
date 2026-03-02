"""
LLM Service — Gemini Primary + Ollama Fallback
===============================================
Primary: Google Gemini 1.5 Flash (free tier)
Fallback: Ollama + Mistral 7b (free, local, no API needed)

To install Ollama fallback:
1. Download Ollama: https://ollama.ai
2. Run: ollama pull mistral
3. Ollama runs automatically at http://localhost:11434
"""

import os
import requests
from dotenv import load_dotenv
from rag.ingest import retrieve

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")

# ─── System Prompt ───────────────────────────────────────────────
SYSTEM_PROMPT = """You are the official AI assistant for District General Hospital Kasaragod, Kerala Government.

STRICT RULES:
1. Answer ONLY using the provided hospital context below.
2. Keep response to 2-3 sentences maximum. Be direct.
3. No bullet points, no headers, no markdown, no bold text.
4. If question is unrelated to hospital, say only:
   "I can only answer questions about DGH Kasaragod. Please call 04994-220330."
5. Never add disclaimers, suggestions or extra advice.
6. Never say "based on your context" or "as per the information".
7. Just answer the question directly and stop.
8. Occasionally start with Namaskaram for local feel.

HOSPITAL CONTEXT:
{context}

Give a short direct answer in plain conversational English. Maximum 3 sentences."""

# ─── Gemini ──────────────────────────────────────────────────────
def get_gemini_response(user_message: str, context: str) -> str:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash")
        prompt = SYSTEM_PROMPT.format(context=context)
        full_prompt = f"/no_think\n{prompt}\n\nUser Question: {user_message}\n\nAnswer in one sentence:"
        response = model.generate_content(full_prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini error: {e}")
        raise e

# ─── Ollama ──────────────────────────────────────────────────────
def get_ollama_response(user_message: str, context: str) -> str:
    try:
        prompt = SYSTEM_PROMPT.format(context=context)
        full_prompt = f"{prompt}\n\nUser Question: {user_message}\n\nAssistant:"
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "top_p": 0.5,
                    "num_predict": 200,
                    "stop": ["User:", "Human:", "\n\n\n"]
                }
            },
            timeout=180
        )
        if response.status_code == 200:
            result = response.json().get("response", "").strip()
            # Remove thinking tags if present
            if "<think>" in result:
                result = result.split("</think>")[-1].strip()
            # Take first sentence only
            for sep in [".", "!", "?"]:
                if sep in result:
                    result = result.split(sep)[0] + sep
                    break
            return result[:300]
        else:
            raise Exception(f"Ollama returned status {response.status_code}")
    except requests.exceptions.ConnectionError:
        raise Exception("Ollama not running")
    except Exception as e:
        print(f"Ollama error: {e}")
        raise e

# ─── Check if Ollama is running ──────────────────────────────────
def is_ollama_available() -> bool:
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        return response.status_code == 200
    except:
        return False

# ─── Main function with fallback logic ───────────────────────────
def get_llm_response(user_message: str) -> str:
    context = retrieve(user_message)
    
    # Guard 
    if not context or not context.strip():
        return "I can only answer questions about DGH Kasaragod. Please call 04994-220330."
    if LLM_PROVIDER == "ollama":
        try:
            print("Using Ollama (configured primary)...")
            return get_ollama_response(user_message, context)
        except Exception as e:
            print(f"Ollama failed: {e} -> falling back to Gemini")
            try:
                return get_gemini_response(user_message, context)
            except:
                return _fallback_response(user_message, context)
    else:
        try:
            print("Using Gemini (primary)...")
            return get_gemini_response(user_message, context)
        except Exception as gemini_error:
            print(f"Gemini failed: {gemini_error}")
            if is_ollama_available():
                try:
                    print("Falling back to Ollama...")
                    return get_ollama_response(user_message, context)
                except Exception as ollama_error:
                    print(f"Ollama also failed: {ollama_error}")
            else:
                print("Ollama not available either")
            return _fallback_response(user_message, context)

# ─── Rule-based fallback (works with zero APIs) ──────────────────
def _fallback_response(user_message: str, context: str) -> str:
    msg = user_message.lower()
    if "token" in msg:
        return "To check your token status, please enter your token number (format: KSD followed by 4 digits) in the token checker on our homepage, or visit the OPD reception."
    if any(w in msg for w in ["opd", "timing", "time", "hours", "open"]):
        return "OPD timings are Monday to Saturday, 8:00 AM to 1:00 PM. Tokens are issued from 8AM to 11AM at the OPD counter."
    if any(w in msg for w in ["emergency", "urgent", "ambulance"]):
        return "Emergency services are available 24/7. Call 108 (free ambulance) or our emergency line: 04994-220332."
    if any(w in msg for w in ["doctor", "dr", "specialist"]):
        return "We have 80+ specialist doctors. Visit our Doctors page for full schedule, or call reception: 04994-220330."
    if any(w in msg for w in ["scheme", "free", "karuna", "ayushman", "bpl"]):
        return "We support Karuna Health Scheme, Arogyakeralam, Ayushman Bharat PMJAY, RSBY and JSSK. Bring Aadhaar and ration card to avail benefits."
    if any(w in msg for w in ["medicine", "pharmacy", "drug"]):
        return "Pharmacy is open 8AM to 8PM. Emergency pharmacy 24/7. Medicines free for scheme beneficiaries."
    if any(w in msg for w in ["contact", "phone", "call", "address"]):
        return "Main Reception: 04994-220330 | Emergency: 108 | Blood Bank: 04994-220331 | Address: Medical College Road, Kasaragod, Kerala 671122"
    if any(w in msg for w in ["hi", "hello", "hey", "namaskaram"]):
        return "Namaskaram! I am the DGH Kasaragod hospital assistant. How can I help you today?"
    if any(w in msg for w in ["room", "where", "location", "block", "floor", "ward"]):
        return "For room locations and directions, please visit our reception at the main entrance or call 04994-220330. Our staff will guide you."
    if any(w in msg for w in ["book", "appointment", "schedule"]):
        return "Namaskaram! To book an appointment, please visit the OPD counter Monday to Saturday between 8AM and 11AM to collect your token. You can also call reception at 04994-220330."
    if any(w in msg for w in ["bed", "capacity", "icu", "admitted"]):
        return "We have 120 general beds and 10 ICU beds. For admission enquiries call 04994-220330."
  
    hospital_keywords = ["hospital", "doctor", "opd", "token", "medicine", 
                        "emergency", "blood", "scheme", "appointment", 
                        "ward", "bed", "room", "kasaragod", "dgh"]
    if not any(w in msg for w in hospital_keywords):
        return "I can only answer questions about District General Hospital Kasaragod. For other queries please call 04994-220330."

    return "Namaskaram! For assistance please call our helpline at 04994-220330 or visit reception. OPD open Monday-Saturday 8AM-1PM."