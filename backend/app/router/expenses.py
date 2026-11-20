from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user_id
from app.database import expenses_collection
from app.schemas import ExpenseCreate, ExpenseUpdate


router = APIRouter(
    prefix="/expenses",
    tags=["Expenses"]
)


# -------------------------
# CREATE EXPENSE
# -------------------------
@router.post("/")
def create_expense(
    expense: ExpenseCreate,
    user_id: str = Depends(get_current_user_id)
):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID"
        )

    new_expense = {
        "user_id": ObjectId(user_id),
        "title": expense.title,
        "amount": expense.amount,
        "category": expense.category,
        "payment_method": expense.payment_method,
        "date": expense.date,
        "description": expense.description,
        "created_at": datetime.now(timezone.utc)
    }

    result = expenses_collection.insert_one(new_expense)

    return {
        "message": "Expense added successfully",
        "expense_id": str(result.inserted_id)
    }


# -------------------------
# GET ALL MY EXPENSES
# -------------------------
@router.get("/")
def get_expenses(
    user_id: str = Depends(get_current_user_id)
):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID"
        )

    expenses = expenses_collection.find(
        {"user_id": ObjectId(user_id)}
    ).sort("date", -1)

    result = []

    for expense in expenses:
        result.append({
            "id": str(expense["_id"]),
            "title": expense["title"],
            "amount": expense["amount"],
            "category": expense["category"],
            "payment_method": expense["payment_method"],
            "date": expense["date"],
            "description": expense.get("description")
        })

    return result


# -------------------------
# UPDATE EXPENSE
# -------------------------
@router.put("/{expense_id}")
def update_expense(
    expense_id: str,
    expense: ExpenseUpdate,
    user_id: str = Depends(get_current_user_id)
):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID"
        )

    if not ObjectId.is_valid(expense_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid expense ID"
        )

    update_data = expense.model_dump(
        exclude_unset=True,
        exclude_none=True
    )

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    result = expenses_collection.update_one(
        {
            "_id": ObjectId(expense_id),
            "user_id": ObjectId(user_id)
        },
        {
            "$set": update_data
        }
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )

    return {
        "message": "Expense updated successfully"
    }


# -------------------------
# DELETE EXPENSE
# -------------------------
@router.delete("/{expense_id}")
def delete_expense(
    expense_id: str,
    user_id: str = Depends(get_current_user_id)
):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID"
        )

    if not ObjectId.is_valid(expense_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid expense ID"
        )

    result = expenses_collection.delete_one(
        {
            "_id": ObjectId(expense_id),
            "user_id": ObjectId(user_id)
        }
    )

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )

    return {
        "message": "Expense deleted successfully"
    }