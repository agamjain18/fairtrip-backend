from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from database import Expense, Trip, User, Dispute
from schemas import Expense as ExpenseSchema, ExpenseCreate, ExpenseUpdate
from datetime import datetime, timezone

router = APIRouter(prefix="/expenses", tags=["expenses"])

@router.get("/", response_model=List[ExpenseSchema])
async def get_expenses(trip_id: Optional[str] = None, skip: int = 0, limit: int = 100):
    """Get all expenses or expenses for a specific trip"""
    if trip_id:
        expenses = await Expense.find(Expense.trip.id == trip_id).skip(skip).limit(limit).to_list()
    else:
        expenses = await Expense.find_all().skip(skip).limit(limit).to_list()
    return expenses

@router.get("/trip/{trip_id}", response_model=List[ExpenseSchema])
async def get_trip_expenses(trip_id: str, skip: int = 0, limit: int = 100):
    """Get all expenses for a specific trip"""
    expenses = await Expense.find(Expense.trip.id == trip_id).skip(skip).limit(limit).to_list()
    return expenses

@router.get("/{expense_id}", response_model=ExpenseSchema)
async def get_expense(expense_id: str):
    """Get a specific expense"""
    expense = await Expense.get(expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense

@router.post("/", response_model=ExpenseSchema, status_code=status.HTTP_201_CREATED)
async def create_expense(expense: ExpenseCreate):
    """Create a new expense"""
    # Verify trip exists
    trip = await Trip.get(expense.trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Verify payer exists
    payer = await User.get(expense.paid_by)
    if not payer:
        raise HTTPException(status_code=404, detail="Payer not found")

    participants = []
    if expense.participant_ids:
        # Fetch all participants
        # Beanie syntax for 'in': User.id in [list] is not directly supported as 'in' operator in python returns bool
        # Use Beanie's In(User.id, list) or find(In(User.id, list))
        from beanie.odm.operators.find.comparison import In
        
        # Ensure we have ObjectIds
        from bson import ObjectId
        participant_object_ids = []
        for pid in expense.participant_ids:
            try:
                participant_object_ids.append(ObjectId(pid))
            except:
                pass
                
        if participant_object_ids:
             participants = await User.find(In(User.id, participant_object_ids)).to_list()
        
    db_expense = Expense(
        trip=trip,
        title=expense.title,
        description=expense.description,
        amount=expense.amount,
        currency=expense.currency,
        category=expense.category,
        location=expense.location,
        split_type=expense.split_type,
        split_data=expense.split_data,
        expense_date=expense.expense_date or datetime.now(timezone.utc),
        paid_by=payer,
        participants=participants,
        receipt_url=expense.receipt_url,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    await db_expense.insert()
    
    # Update trip total spent
    # Be careful with concurrency here, but acceptable for MVP
    trip.total_spent += expense.amount
    if trip.total_budget > 0:
        trip.budget_used_percentage = (trip.total_spent / trip.total_budget) * 100
    await trip.save()
    
    return db_expense

@router.put("/{expense_id}", response_model=ExpenseSchema)
async def update_expense(expense_id: str, expense_update: ExpenseUpdate):
    """Update expense details"""
    expense = await Expense.get(expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    old_amount = expense.amount
    
    update_data = expense_update.dict(exclude_unset=True)
    if update_data:
        await expense.set(update_data)
        expense.updated_at = datetime.now(timezone.utc)
        await expense.save()
    
    # Update trip total if amount changed
    if 'amount' in update_data:
        new_amount = update_data['amount']
        # Need to fetch trip
        trip = await Trip.get(expense.trip.id)
        if trip:
             trip.total_spent = trip.total_spent - old_amount + new_amount
             if trip.total_budget > 0:
                trip.budget_used_percentage = (trip.total_spent / trip.total_budget) * 100
             await trip.save()
             
             # Also update in-memory expense object to return correct amount if needed, 
             # though 'expense' variable might already be updated by .set() but be careful
             expense.amount = new_amount

    return expense

@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(expense_id: str):
    """Delete an expense"""
    expense = await Expense.get(expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    # Update trip total
    trip = await Trip.get(expense.trip.id)
    if trip:
        trip.total_spent -= expense.amount
        if trip.total_budget > 0:
            trip.budget_used_percentage = (trip.total_spent / trip.total_budget) * 100
        await trip.save()
    
    await expense.delete()
    return None

@router.get("/{expense_id}/participants")
async def get_expense_participants(expense_id: str):
    """Get all participants of an expense"""
    expense = await Expense.get(expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    # Fetch participants if they are links
    # Expense.participants is List[Link[User]]
    participants = []
    for link in expense.participants:
         user = await User.get(link.id)
         if user:
             participants.append(user)

    return participants

@router.post("/{expense_id}/participants/{user_id}")
async def add_expense_participant(expense_id: str, user_id: str):
    """Add a participant to an expense"""
    expense = await Expense.get(expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.id in [p.id for p in expense.participants]:
        raise HTTPException(status_code=400, detail="User is already a participant")
    
    expense.participants.append(user)
    await expense.save()
    return {"message": "Participant added successfully"}

@router.post("/{expense_id}/disputes")
async def create_dispute(expense_id: str, user_id: str, reason: str):
    """Create a dispute for an expense"""
    expense = await Expense.get(expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    user = await User.get(user_id)
    if not user:
         raise HTTPException(status_code=404, detail="User not found")

    dispute = Dispute(
        expense=expense,
        raised_by=user,
        reason=reason,
        status="open",
        created_at=datetime.now(timezone.utc)
    )
    
    expense.status = "disputed"
    await expense.save()
    
    await dispute.insert()
    
    return dispute

@router.get("/trip/{trip_id}/summary")
async def get_trip_expense_summary(trip_id: str, user_id: Optional[str] = None):
    """Get expense summary for a trip"""
    expenses = await Expense.find(Expense.trip.id == trip_id).to_list()
    
    total_spent = sum(e.amount for e in expenses)
    
    summary = {
        "total_spent": total_spent,
        "expense_count": len(expenses),
        "by_category": {},
        "by_status": {}
    }
    
    # Group by category
    for expense in expenses:
        category = expense.category.value if expense.category else "other"
        summary["by_category"][category] = summary["by_category"].get(category, 0) + expense.amount
    
    # Group by status
    for expense in expenses:
        status = expense.status.value if expense.status else "pending"
        summary["by_status"][status] = summary["by_status"].get(status, 0) + 1
    
    # Calculate user share if user_id provided
    if user_id:
        user_expenses = []
        user_paid = 0.0
        
        for e in expenses:
             # Handle Link for paid_by
             payer_id = None
             if e.paid_by:
                 if hasattr(e.paid_by, 'id'):
                     payer_id = str(e.paid_by.id)
                 elif hasattr(e.paid_by, 'ref'):
                     payer_id = str(e.paid_by.ref.id)
                     
             if payer_id == user_id:
                 user_paid += e.amount

             # Handle Link for participants
             is_participant = False
             if e.participants:
                 for p in e.participants:
                     pid = None
                     if hasattr(p, 'id'):
                         pid = str(p.id)
                     elif hasattr(p, 'ref'):
                         pid = str(p.ref.id)
                         
                     if pid == user_id:
                         is_participant = True
                         break
             
             if is_participant:
                 user_expenses.append(e)
        
        user_share = 0
        for e in user_expenses:
             if e.participants:
                 user_share += e.amount / len(e.participants)
        
        summary["user_paid"] = user_paid
        summary["user_share"] = user_share
        summary["user_balance"] = user_paid - user_share
    
    return summary
@router.get("/user/{user_id}/summary")
async def get_user_expense_summary(user_id: str):
    """Get financial summary for a user across all trips"""
    # Find all expenses where user is either payer or participant
    # This might be expensive, so optimal query is needed.
    # Logic:
    # 1. Get all expenses.
    # 2. Filter in memory for now (easier with Beanie given complex schema).
    
    all_expenses = await Expense.find_all().to_list()
    
    total_paid = 0.0
    total_share = 0.0
    
    for expense in all_expenses:
        # Calculate Amount Paid
        payer_id = None
        if expense.paid_by:
             if hasattr(expense.paid_by, 'id'):
                 payer_id = str(expense.paid_by.id)
             elif hasattr(expense.paid_by, 'ref'):
                 payer_id = str(expense.paid_by.ref.id)

        if payer_id == user_id:
            total_paid += expense.amount
            
        # Calculate Share
        # Check if user is in participants
        is_participant = False
        if expense.participants:
            for p in expense.participants:
                pid = None
                if hasattr(p, 'id'):
                    pid = str(p.id)
                elif hasattr(p, 'ref'):
                    pid = str(p.ref.id)
                
                if pid == user_id:
                    is_participant = True
                    break
        
        if is_participant and expense.participants:
            # Assuming equal split for now as referenced in other endpoints
            total_share += expense.amount / len(expense.participants)
            
    return {
        "total_spent": total_share,   # What I consumed (My Share)
        "total_paid": total_paid,     # What I paid out
        "net_balance": total_paid - total_share, # +ve means I am owed, -ve means I owe
        "to_give": abs(total_paid - total_share) if total_paid < total_share else 0.0,
        "to_receive": total_paid - total_share if total_paid > total_share else 0.0
    }
