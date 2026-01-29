from fastapi import APIRouter, HTTPException
from typing import List, Optional
from database import RecurringExpense, Trip, User, Expense
from schemas import RecurringExpense as RecurringExpenseSchema, RecurringExpenseCreate, RecurringExpenseUpdate
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from beanie.odm.operators.find.comparison import In

router = APIRouter(prefix="/recurring-expenses", tags=["recurring-expenses"])

@router.get("/", response_model=List[RecurringExpenseSchema])
async def get_recurring_expenses(trip_id: Optional[str] = None, is_active: Optional[bool] = None):
    """Get all recurring expenses"""
    query = {}
    
    if trip_id:
        query["trip.$id"] = ObjectId(trip_id)
    
    if is_active is not None:
        query["is_active"] = is_active
    
    if query:
        recurring_expenses = await RecurringExpense.find(query).to_list()
    else:
        recurring_expenses = await RecurringExpense.find_all().to_list()
    
    return recurring_expenses

@router.get("/{recurring_expense_id}", response_model=RecurringExpenseSchema)
async def get_recurring_expense(recurring_expense_id: str):
    """Get a specific recurring expense"""
    recurring_expense = await RecurringExpense.get(recurring_expense_id)
    if not recurring_expense:
        raise HTTPException(status_code=404, detail="Recurring expense not found")
    return recurring_expense

@router.post("/", response_model=RecurringExpenseSchema, status_code=201)
async def create_recurring_expense(recurring_expense: RecurringExpenseCreate):
    """Create a new recurring expense template"""
    # Verify trip if provided
    trip = None
    if recurring_expense.trip_id:
        trip = await Trip.get(recurring_expense.trip_id)
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")
    
    # Verify payer
    payer = await User.get(recurring_expense.paid_by)
    if not payer:
        raise HTTPException(status_code=404, detail="Payer not found")
    
    # Verify participants
    participants = []
    if recurring_expense.participant_ids:
        participant_object_ids = [ObjectId(pid) for pid in recurring_expense.participant_ids]
        participants = await User.find(In(User.id, participant_object_ids)).to_list()
    
    # Calculate next occurrence
    next_occurrence = calculate_next_occurrence(
        recurring_expense.start_date,
        recurring_expense.frequency,
        recurring_expense.interval
    )
    
    db_recurring_expense = RecurringExpense(
        trip=trip,
        title=recurring_expense.title,
        description=recurring_expense.description,
        amount=recurring_expense.amount,
        currency=recurring_expense.currency,
        category=recurring_expense.category,
        paid_by=payer,
        participants=participants,
        split_type=recurring_expense.split_type,
        split_data=recurring_expense.split_data,
        frequency=recurring_expense.frequency,
        interval=recurring_expense.interval,
        start_date=recurring_expense.start_date,
        end_date=recurring_expense.end_date,
        next_occurrence=next_occurrence,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    await db_recurring_expense.insert()
    return db_recurring_expense

@router.put("/{recurring_expense_id}", response_model=RecurringExpenseSchema)
async def update_recurring_expense(recurring_expense_id: str, recurring_expense_update: RecurringExpenseUpdate):
    """Update recurring expense details"""
    recurring_expense = await RecurringExpense.get(recurring_expense_id)
    if not recurring_expense:
        raise HTTPException(status_code=404, detail="Recurring expense not found")
    
    update_data = recurring_expense_update.dict(exclude_unset=True)
    if update_data:
        await recurring_expense.set(update_data)
        recurring_expense.updated_at = datetime.now(timezone.utc)
        await recurring_expense.save()
    
    return recurring_expense

@router.delete("/{recurring_expense_id}", status_code=204)
async def delete_recurring_expense(recurring_expense_id: str):
    """Delete a recurring expense"""
    recurring_expense = await RecurringExpense.get(recurring_expense_id)
    if not recurring_expense:
        raise HTTPException(status_code=404, detail="Recurring expense not found")
    
    await recurring_expense.delete()
    return None

@router.post("/process")
async def process_recurring_expenses():
    """Process all due recurring expenses and create actual expense records"""
    now = datetime.now(timezone.utc)
    
    # Find all active recurring expenses that are due
    due_expenses = await RecurringExpense.find({
        "is_active": True,
        "next_occurrence": {"$lte": now}
    }).to_list()
    
    created_count = 0
    
    for recurring in due_expenses:
        # Check if we've passed the end date
        if recurring.end_date and now > recurring.end_date:
            recurring.is_active = False
            await recurring.save()
            continue
        
        # Create the actual expense
        expense = Expense(
            trip=recurring.trip,
            title=recurring.title,
            description=recurring.description,
            amount=recurring.amount,
            currency=recurring.currency,
            category=recurring.category,
            paid_by=recurring.paid_by,
            participants=recurring.participants,
            split_type=recurring.split_type,
            split_data=recurring.split_data,
            recurring_expense_id=str(recurring.id),
            expense_date=now,
            created_at=now,
            updated_at=now
        )
        
        await expense.insert()
        
        # Update trip total if applicable
        if recurring.trip:
            trip = await Trip.get(recurring.trip.id)
            if trip:
                trip.total_spent += recurring.amount
                if trip.total_budget > 0:
                    trip.budget_used_percentage = (trip.total_spent / trip.total_budget) * 100
                await trip.save()
        
        # Update recurring expense
        recurring.last_generated = now
        recurring.next_occurrence = calculate_next_occurrence(
            recurring.next_occurrence,
            recurring.frequency,
            recurring.interval
        )
        await recurring.save()
        
        created_count += 1
    
    return {
        "processed": len(due_expenses),
        "created": created_count,
        "message": f"Created {created_count} expenses from {len(due_expenses)} recurring templates"
    }

def calculate_next_occurrence(current_date: datetime, frequency: str, interval: int) -> datetime:
    """Calculate the next occurrence date based on frequency and interval"""
    if frequency == "daily":
        return current_date + timedelta(days=interval)
    elif frequency == "weekly":
        return current_date + timedelta(weeks=interval)
    elif frequency == "monthly":
        # Add months (approximate)
        month = current_date.month + interval
        year = current_date.year + (month - 1) // 12
        month = ((month - 1) % 12) + 1
        try:
            return current_date.replace(year=year, month=month)
        except ValueError:
            # Handle day overflow (e.g., Jan 31 -> Feb 28/29)
            import calendar
            last_day = calendar.monthrange(year, month)[1]
            return current_date.replace(year=year, month=month, day=last_day)
    elif frequency == "yearly":
        try:
            return current_date.replace(year=current_date.year + interval)
        except ValueError:
            # Handle Feb 29 in non-leap years
            return current_date.replace(year=current_date.year + interval, day=28)
    else:
        return current_date + timedelta(days=30 * interval)  # Default to monthly
