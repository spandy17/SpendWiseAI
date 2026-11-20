
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Budget
from app.auth import get_current_user_id
from app.schemas import BudgetCreate, BudgetUpdate

router = APIRouter(prefix="/budgets", tags=["Budgets"])


@router.post("/")
def create_budget(
    budget: BudgetCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    existing = db.query(Budget).filter(
        Budget.user_id == int(user_id),
        Budget.category == budget.category,
        Budget.month == budget.month,
        Budget.year == budget.year
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Budget already exists for this category and month"
        )

    new_budget = Budget(
        user_id=int(user_id),
        category=budget.category,
        limit_amount=budget.limit_amount,
        month=budget.month,
        year=budget.year
    )

    db.add(new_budget)
    db.commit()
    db.refresh(new_budget)

    return {
        "message": "Budget created successfully",
        "budget_id": new_budget.id
    }


@router.get("/")
def get_budgets(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    budgets = db.query(Budget).filter(
        Budget.user_id == int(user_id)
    ).order_by(
        Budget.year.desc(),
        Budget.month.desc()
    ).all()

    return [
        {
            "id": item.id,
            "category": item.category,
            "limit_amount": item.limit_amount,
            "month": item.month,
            "year": item.year
        }
        for item in budgets
    ]


@router.put("/{budget_id}")
def update_budget(
    budget_id: int,
    budget: BudgetUpdate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    existing = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == int(user_id)
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Budget not found")

    update_data = budget.model_dump(
        exclude_unset=True,
        exclude_none=True
    )

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    for key, value in update_data.items():
        setattr(existing, key, value)

    db.commit()

    return {"message": "Budget updated successfully"}


@router.delete("/{budget_id}")
def delete_budget(
    budget_id: int,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    existing = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == int(user_id)
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Budget not found")

    db.delete(existing)
    db.commit()

    return {"message": "Budget deleted successfully"}
