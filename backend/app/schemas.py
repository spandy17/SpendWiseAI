from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# =========================
# AUTHENTICATION SCHEMAS
# =========================

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


# =========================
# EXPENSE SCHEMAS
# =========================

class ExpenseCreate(BaseModel):
    title: str
    amount: float = Field(gt=0)
    category: str
    payment_method: str
    date: datetime
    description: Optional[str] = None


class ExpenseUpdate(BaseModel):
    title: Optional[str] = None
    amount: Optional[float] = Field(default=None, gt=0)
    category: Optional[str] = None
    payment_method: Optional[str] = None
    date: Optional[datetime] = None
    description: Optional[str] = None

class IncomeCreate(BaseModel):
    source: str
    amount: float = Field(gt=0)
    date: datetime
    description: Optional[str] = None

class BudgetCreate(BaseModel):
    category: str
    limit_amount: float = Field(gt=0)
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=2020)


class BudgetUpdate(BaseModel):
    category: Optional[str] = None
    limit_amount: Optional[float] = Field(default=None, gt=0)
    month: Optional[int] = Field(default=None, ge=1, le=12)
    year: Optional[int] = Field(default=None, ge=2020)