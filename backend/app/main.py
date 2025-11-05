from fastapi import FastAPI
from dotenv import load_dotenv
import os

# Load .env variables BEFORE importing other app modules
load_dotenv()

from .database import create_db_and_tables
from .routes import auth, rides, payments, admin

# Create the "uploaded_docs" directory if it doesn't exist
os.makedirs("uploaded_docs", exist_ok=True)


app = FastAPI(title="Cab Aggregator System")

app.include_router(auth.router)
app.include_router(rides.router)
app.include_router(payments.router)
app.include_router(admin.router)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/")
def root():
    return {"message": "Cab Aggregator API is running"}