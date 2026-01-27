from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database_sql import get_db, Expense, Trip, User, Dispute, expense_participants, increment_trip_members_version, Settlement
from schemas_sql import Expense as ExpenseSchema, ExpenseCreate, ExpenseUpdate, User as UserSchema

from datetime import datetime, timezone
import json
from collections import defaultdict

router = APIRouter(prefix="/expenses", tags=["expenses"])

@router.get("/", response_model=List[ExpenseSchema])
def get_expenses(trip_id: Optional[int] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all expenses or expenses for a specific trip"""
    query = db.query(Expense)
    if trip_id:
        query = query.filter(Expense.trip_id == trip_id)
    expenses = query.offset(skip).limit(limit).all()
    return expenses

@router.get("/{expense_id}", response_model=ExpenseSchema)
def get_expense(expense_id: int, db: Session = Depends(get_db)):
    """Get a specific expense"""
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense

@router.post("/", response_model=ExpenseSchema, status_code=status.HTTP_201_CREATED)
def create_expense(expense: ExpenseCreate, db: Session = Depends(get_db)):
    """Create a new expense"""
    trip = db.query(Trip).filter(Trip.id == expense.trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    payer = db.query(User).filter(User.id == expense.paid_by_id).first()
    if not payer:
        raise HTTPException(status_code=404, detail="Payer not found")

    participants = []
    if expense.participant_ids:
        participants = db.query(User).filter(User.id.in_(expense.participant_ids)).all()
        
    db_expense = Expense(
        trip_id=expense.trip_id,
        title=expense.title,
        description=expense.description,
        amount=expense.amount,
        currency=expense.currency,
        category=expense.category,
        location=expense.location,
        split_type=expense.split_type,
        split_data=expense.split_data,
        expense_date=expense.expense_date or datetime.now(timezone.utc),
        paid_by_id=expense.paid_by_id,
        participants=participants,
        receipt_url=expense.receipt_url,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    db.add(db_expense)
    
    # Update trip total spent
    trip.total_spent += expense.amount
    if trip.total_budget > 0:
        trip.budget_used_percentage = (trip.total_spent / trip.total_budget) * 100
        
    db.commit()
    db.refresh(db_expense)

    # Real-time sync: increment version for all participants
    increment_trip_members_version(db, db_expense.trip_id)

    return db_expense

@router.put("/{expense_id}", response_model=ExpenseSchema)
def update_expense(expense_id: int, expense_update: ExpenseUpdate, db: Session = Depends(get_db)):
    """Update expense details"""
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    old_amount = expense.amount
    update_data = expense_update.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(expense, key, value)
        
    expense.updated_at = datetime.now(timezone.utc)
    
    if 'amount' in update_data:
        new_amount = update_data['amount']
        trip = db.query(Trip).filter(Trip.id == expense.trip_id).first()
        if trip:
            trip.total_spent = trip.total_spent - old_amount + new_amount
            if trip.total_budget > 0:
                trip.budget_used_percentage = (trip.total_spent / trip.total_budget) * 100
    
    db.commit()
    db.refresh(expense)
    return expense

@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    """Delete an expense"""
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    trip = db.query(Trip).filter(Trip.id == expense.trip_id).first()
    if trip:
        trip.total_spent -= expense.amount
        if trip.total_budget > 0:
            trip.budget_used_percentage = (trip.total_spent / trip.total_budget) * 100
    
    db.delete(expense)
    db.commit()
    return None

@router.get("/{expense_id}/participants", response_model=List[UserSchema])
def get_expense_participants(expense_id: int, db: Session = Depends(get_db)):
    """Get all participants of an expense"""
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense.participants

@router.post("/{expense_id}/participants/{user_id}")
def add_expense_participant(expense_id: int, user_id: int, db: Session = Depends(get_db)):
    """Add a participant to an expense"""
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user in expense.participants:
        raise HTTPException(status_code=400, detail="User is already a participant")
    
    expense.participants.append(user)
    db.commit()
    return {"message": "Participant added successfully"}

@router.post("/{expense_id}/disputes")
def create_dispute(expense_id: int, user_id: int, reason: str, db: Session = Depends(get_db)):
    """Create a dispute for an expense"""
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
         raise HTTPException(status_code=404, detail="User not found")

    dispute = Dispute(
        expense_id=expense_id,
        raised_by_id=user_id,
        reason=reason,
        status="open",
        created_at=datetime.now(timezone.utc)
    )
    
    expense.status = "disputed"
    db.add(dispute)
    db.commit()
    db.refresh(dispute)
    return dispute

@router.get("/user/{user_id}/summary")
def get_user_expense_summary(user_id: int, db: Session = Depends(get_db)):
    """Get global expense summary for a user across all trips"""
    # Find all expenses where user is payer or participant
    expenses = db.query(Expense).join(Expense.participants).filter(
        (Expense.paid_by_id == user_id) | (User.id == user_id)
    ).distinct().all()
    
    total_spent = 0.0
    to_receive = 0.0
    to_give = 0.0
    
    # Track balances with other users
    balances = defaultdict(float) # userId -> amount
    
    for e in expenses:
        shares = calculate_shares_sql(e)
        user_share = shares.get(str(user_id), 0.0)
        
        if e.paid_by_id == user_id:
            # User paid for this
            total_spent += e.amount
            # Others owe the user their shares
            for pid, share in shares.items():
                if pid != str(user_id):
                    balances[pid] += share
                    to_receive += share
        else:
            # Someone else paid, user is a participant
            to_give += user_share
            balances[str(e.paid_by_id)] -= user_share
            
    # Include Settlements
    settlements = db.query(Settlement).filter(
        (Settlement.from_user_id == user_id) | (Settlement.to_user_id == user_id)
    ).all()
    
    for s in settlements:
        if s.from_user_id == user_id:
            # User paid someone (settled a debt)
            # This increases the balance (less negative) with that person
            balances[str(s.to_user_id)] += s.amount
        elif s.to_user_id == user_id:
            # Someone paid the user
            # This decreases the balance (less positive) with that person
            balances[str(s.from_user_id)] -= s.amount

    # Recalculate totals from net balances
    to_receive = 0.0
    to_give = 0.0
    
    for uid, amount in balances.items():
        if amount > 0:
            to_receive += amount
        elif amount < 0:
            to_give += abs(amount)
    
    return {
        "total_spent": total_spent,
        "to_receive": to_receive,
        "to_give": to_give,
        "total_balance": to_receive - to_give,
        "friend_balances": balances
    }

@router.get("/trip/{trip_id}/summary")
def get_trip_expense_summary(trip_id: int, user_id: Optional[int] = None, db: Session = Depends(get_db)):

    """Get expense summary for a trip"""
    expenses = db.query(Expense).filter(Expense.trip_id == trip_id).all()
    
    total_spent = sum(e.amount for e in expenses)
    
    summary = {
        "total_spent": total_spent,
        "expense_count": len(expenses),
        "by_category": {},
        "by_status": {}
    }
    
    for expense in expenses:
        category = expense.category.value if expense.category else "other"
        summary["by_category"][category] = summary["by_category"].get(category, 0) + expense.amount
        
        status = expense.status.value if expense.status else "pending"
        summary["by_status"][status] = summary["by_status"].get(status, 0) + 1
    
    # Calculate balances for all members in the trip
    member_balances = defaultdict(float)
    trip_members = db.query(User).join(User.trips).filter(Trip.id == trip_id).all()
    member_ids = [str(m.id) for m in trip_members]
    
    for e in expenses:
        shares = calculate_shares_sql(e)
        paid_by_str = str(e.paid_by_id)
        for pid, share in shares.items():
            if pid in member_ids:
                member_balances[pid] -= share
                member_balances[paid_by_str] += share
    
    # Add trip settlements to member balances
    all_settlements = db.query(Settlement).filter(Settlement.trip_id == trip_id).all()
    for s in all_settlements:
        member_balances[str(s.from_user_id)] += s.amount
        member_balances[str(s.to_user_id)] -= s.amount
    
    summary["member_balances"] = member_balances

    if user_id:
        user_balance = member_balances.get(str(user_id), 0.0)
        user_paid = sum(e.amount for e in expenses if e.paid_by_id == user_id)
        user_share_total = sum(calculate_shares_sql(e).get(str(user_id), 0.0) for e in expenses)
        
        summary["user_paid"] = user_paid
        summary["user_share"] = user_share_total
        summary["user_balance"] = user_balance

    return summary

def calculate_shares_sql(expense: Expense) -> dict:
    shares = {}
    participant_ids = [str(p.id) for p in expense.participants]
    
    if not participant_ids:
        return shares
        
    num_people = len(participant_ids)
    split_type = expense.split_type or "equal"
    total_amount = expense.amount
    
    if split_type == "equal":
        share_per_person = total_amount / num_people
        for pid in participant_ids:
            shares[pid] = share_per_person
    elif split_type == "custom" and expense.split_data:
        if isinstance(expense.split_data, dict):
            shares = expense.split_data
        else:
            try:
                shares = json.loads(expense.split_data)
            except:
                pass
    # ... handle other split types similarly ...
    
    return shares
