from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from sqlalchemy.orm import Session
from database_sql import RecurringExpense, Trip, User, Expense, get_db
from schemas_sql import RecurringExpense as RecurringExpenseSchema, RecurringExpenseCreate, RecurringExpenseUpdate
from datetime import datetime, timezone, timedelta
from utils.timezone_utils import get_ist_now

router = APIRouter(prefix="/recurring-expenses", tags=["recurring-expenses"])

@router.get("/", response_model=List[RecurringExpenseSchema])
def get_recurring_expenses(
    user_id: Optional[int] = None,
    trip_id: Optional[int] = None, 
    is_active: Optional[bool] = None, 
    db: Session = Depends(get_db)
):
    """Get all recurring expenses or filtered by user/trip"""
    query = db.query(RecurringExpense)
    
    if user_id:
        # Filter recurring expenses where user is the payer
        query = query.filter(RecurringExpense.paid_by_id == user_id)
        
    if trip_id:
        query = query.filter(RecurringExpense.trip_id == trip_id)
    
    if is_active is not None:
        query = query.filter(RecurringExpense.is_active == is_active)
    
    recurring_expenses = query.all()
    return recurring_expenses

@router.get("/{recurring_expense_id}", response_model=RecurringExpenseSchema)
def get_recurring_expense(recurring_expense_id: int, db: Session = Depends(get_db)):
    """Get a specific recurring expense"""
    recurring_expense = db.query(RecurringExpense).filter(RecurringExpense.id == recurring_expense_id).first()
    if not recurring_expense:
        raise HTTPException(status_code=404, detail="Recurring expense not found")
    return recurring_expense

@router.post("/", response_model=RecurringExpenseSchema, status_code=status.HTTP_201_CREATED)
def create_recurring_expense(recurring_expense: RecurringExpenseCreate, db: Session = Depends(get_db)):
    """Create a new recurring expense template"""
    if recurring_expense.trip_id:
        trip = db.query(Trip).filter(Trip.id == recurring_expense.trip_id).first()
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")
    
    payer = db.query(User).filter(User.id == recurring_expense.paid_by_id).first()
    if not payer:
        raise HTTPException(status_code=404, detail="Payer not found")
    
    next_occurrence = calculate_next_occurrence(
        recurring_expense.start_date,
        recurring_expense.frequency,
        recurring_expense.interval
    )
    
    db_recurring_expense = RecurringExpense(
        trip_id=recurring_expense.trip_id,
        title=recurring_expense.title,
        description=recurring_expense.description,
        amount=recurring_expense.amount,
        currency=recurring_expense.currency,
        category=recurring_expense.category,
        paid_by_id=recurring_expense.paid_by_id,
        split_type=recurring_expense.split_type,
        split_data=recurring_expense.split_data,
        frequency=recurring_expense.frequency,
        interval=recurring_expense.interval,
        start_date=recurring_expense.start_date,
        end_date=recurring_expense.end_date,
        next_occurrence=next_occurrence,
        is_active=True,
        created_at=get_ist_now(),
        updated_at=get_ist_now()
    )
    
    db.add(db_recurring_expense)
    db.commit()
    db.refresh(db_recurring_expense)
    return db_recurring_expense

@router.put("/{recurring_expense_id}", response_model=RecurringExpenseSchema)
def update_recurring_expense(recurring_expense_id: int, recurring_expense_update: RecurringExpenseUpdate, db: Session = Depends(get_db)):
    """Update recurring expense details"""
    recurring_expense = db.query(RecurringExpense).filter(RecurringExpense.id == recurring_expense_id).first()
    if not recurring_expense:
        raise HTTPException(status_code=404, detail="Recurring expense not found")
    
    update_data = recurring_expense_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(recurring_expense, key, value)
        
    recurring_expense.updated_at = get_ist_now()
    db.commit()
    db.refresh(recurring_expense)
    return recurring_expense

@router.delete("/{recurring_expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recurring_expense(recurring_expense_id: int, db: Session = Depends(get_db)):
    """Delete a recurring expense"""
    recurring_expense = db.query(RecurringExpense).filter(RecurringExpense.id == recurring_expense_id).first()
    if not recurring_expense:
        raise HTTPException(status_code=404, detail="Recurring expense not found")
    
    db.delete(recurring_expense)
    db.commit()
    return None

@router.post("/process")
def process_recurring_expenses(db: Session = Depends(get_db)):
    """Process all due recurring expenses"""
    now = get_ist_now()
    due_expenses = db.query(RecurringExpense).filter(
        RecurringExpense.is_active == True,
        RecurringExpense.next_occurrence <= now
    ).all()
    
    created_count = 0
    for recurring in due_expenses:
        if recurring.end_date and now > recurring.end_date:
            recurring.is_active = False
            continue
        
        expense = Expense(
            trip_id=recurring.trip_id,
            title=recurring.title,
            description=recurring.description,
            amount=recurring.amount,
            currency=recurring.currency,
            category=recurring.category,
            paid_by_id=recurring.paid_by_id,
            split_type=recurring.split_type,
            split_data=recurring.split_data,
            recurring_expense_id=recurring.id,
            expense_date=now,
            created_at=now,
            updated_at=now
        )
        db.add(expense)
        
        if recurring.trip_id:
            trip = db.query(Trip).filter(Trip.id == recurring.trip_id).first()
            if trip:
                trip.total_spent += recurring.amount
                if trip.total_budget > 0:
                    trip.budget_used_percentage = (trip.total_spent / trip.total_budget) * 100
        
        recurring.last_generated = now
        recurring.next_occurrence = calculate_next_occurrence(
            recurring.next_occurrence,
            recurring.frequency,
            recurring.interval
        )
        created_count += 1
    
    db.commit()
    return {"processed": len(due_expenses), "created": created_count}

def calculate_next_occurrence(current_date: datetime, frequency: str, interval: int) -> datetime:
    if frequency == "daily":
        return current_date + timedelta(days=interval)
    elif frequency == "weekly":
        return current_date + timedelta(weeks=interval)
    elif frequency == "monthly":
        month = current_date.month + interval
        year = current_date.year + (month - 1) // 12
        month = ((month - 1) % 12) + 1
        try:
            return current_date.replace(year=year, month=month)
        except ValueError:
            import calendar
            last_day = calendar.monthrange(year, month)[1]
            return current_date.replace(year=year, month=month, day=last_day)
    elif frequency == "yearly":
        try:
            return current_date.replace(year=current_date.year + interval)
        except ValueError:
            return current_date.replace(year=current_date.year + interval, day=28)
    else:
        return current_date + timedelta(days=30 * interval)
