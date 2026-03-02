from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.chat import router as chat_router
from routes.status import router as status_router

app = FastAPI(title="DGH Kasaragod Hospital Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(status_router)

@app.get("/")
def root():
    return {"message": "DGH Kasaragod Hospital API is running"}