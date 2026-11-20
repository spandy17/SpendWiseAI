
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.auth import router as auth_router
from app.routers.expenses import router as expenses_router
from app.routers.income import router as income_router
from app.routers.budget import router as budget_router
from app.routers.dashboard import router as dashboard_router
from app.routers.reports import router as reports_router

app = FastAPI(
    title="Expense AI",
    description="AI-Powered Smart Expense Tracker",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(expenses_router)
app.include_router(income_router)
app.include_router(budget_router)
app.include_router(dashboard_router)
app.include_router(reports_router)


@app.get("/")
def root():
    return {"message": "Expense AI Backend is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}
