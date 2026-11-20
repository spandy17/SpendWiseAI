
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Income
from app.auth import get_current_user_id
from app.schemas import IncomeCreate

router = APIRouter(prefix="/income", tags=["Income"])


@router.post("/")
def create_income(
    income: IncomeCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    new_income = Income(
        user_id=int(user_id),
        source=income.source,
        amount=income.amount,
        date=income.date,
        description=income.description
    )

    db.add(new_income)
    db.commit()
    db.refresh(new_income)

    return {
        "message": "Income added successfully",
        "income_id": new_income.id
    }


@router.get("/")
def get_income(
    search: str = "",
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    query = db.query(Income).filter(
        Income.user_id == int(user_id)
    )

    if search:
        query = query.filter(Income.source.ilike(f"%{search}%"))

    incomes = query.order_by(Income.date.desc()).all()

    return [
        {
            "id": item.id,
            "source": item.source,
            "amount": item.amount,
            "date": item.date,
            "description": item.description
        }
        for item in incomes
    ]


@router.put("/{income_id}")
def update_income(
    income_id: int,
    income: IncomeCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    existing = db.query(Income).filter(
        Income.id == income_id,
        Income.user_id == int(user_id)
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Income not found")

    existing.source = income.source
    existing.amount = income.amount
    existing.date = income.date
    existing.description = income.description

    db.commit()

    return {"message": "Income updated successfully"}


@router.delete("/{income_id}")
def delete_income(
    income_id: int,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    existing = db.query(Income).filter(
        Income.id == income_id,
        Income.user_id == int(user_id)
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Income not found")

    db.delete(existing)
    db.commit()

    return {"message": "Income deleted successfully"}
