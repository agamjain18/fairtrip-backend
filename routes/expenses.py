from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from database import Expense, Trip, User, Dispute
from schemas import Expense as ExpenseSchema, ExpenseCreate, ExpenseUpdate
from datetime import datetime, timezone
import json
import math
from collections import defaultdict

router = APIRouter(prefix="/expenses", tags=["expenses"])

@router.get("/", response_model=List[ExpenseSchema])
async def get_expenses(trip_id: Optional[str] = None, skip: int = 0, limit: int = 100):
    """Get all expenses or expenses for a specific trip"""
    if trip_id:
        expenses = await Expense.find(Expense.trip.id == trip_id).skip(skip).limit(limit).to_list()
    else:
        expenses = await Expense.find_all().skip(skip).limit(limit).to_list()
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
        user_share_total = 0.0
        
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

             # Calculate share for this expense
             shares = calculate_shares(e)
             if user_id in shares:
                 user_share_total += shares[user_id]
        
        summary["user_paid"] = user_paid
        summary["user_share"] = user_share_total
        summary["user_balance"] = user_paid - user_share_total

    return summary

@router.get("/trip/{trip_id}/history")
async def get_trip_expense_history(trip_id: str, skip: int = 0, limit: int = 100):
    """Get detailed expense history for a trip with pagination"""
    expenses = await Expense.find(Expense.trip.id == trip_id).sort("-expense_date").skip(skip).limit(limit).to_list()
    
    # Enrich with user details
    history = []
    for expense in expenses:
        payer_name = "Unknown"
        if expense.paid_by:
            payer = await User.get(expense.paid_by.id)
            if payer:
                payer_name = payer.full_name or payer.username
        
        participant_names = []
        for p in expense.participants:
            user = await User.get(p.id)
            if user:
                participant_names.append(user.full_name or user.username)
        
        history.append({
            "id": str(expense.id),
            "title": expense.title,
            "amount": expense.amount,
            "currency": expense.currency,
            "category": expense.category.value if expense.category else "other",
            "paid_by": payer_name,
            "participants": participant_names,
            "split_type": expense.split_type,
            "expense_date": expense.expense_date,
            "created_at": expense.created_at,
            "status": expense.status.value if expense.status else "pending"
        })
    
    return history

@router.get("/trip/{trip_id}/analytics")
async def get_trip_analytics(trip_id: str):
    """Get detailed analytics for a trip"""
    expenses = await Expense.find(Expense.trip.id == trip_id).to_list()
    
    if not expenses:
        return {
            "total_expenses": 0,
            "total_amount": 0,
            "by_category": {},
            "by_user": {},
            "by_month": {},
            "average_expense": 0,
            "largest_expense": None,
            "most_active_payer": None
        }
    
    total_amount = sum(e.amount for e in expenses)
    
    # Category breakdown
    by_category = {}
    for expense in expenses:
        category = expense.category.value if expense.category else "other"
        if category not in by_category:
            by_category[category] = {"count": 0, "total": 0}
        by_category[category]["count"] += 1
        by_category[category]["total"] += expense.amount
    
    # User spending breakdown
    by_user = {}
    for expense in expenses:
        if expense.paid_by:
            payer_id = str(expense.paid_by.id)
            if payer_id not in by_user:
                payer = await User.get(expense.paid_by.id)
                by_user[payer_id] = {
                    "name": payer.full_name or payer.username if payer else "Unknown",
                    "paid": 0,
                    "count": 0
                }
            by_user[payer_id]["paid"] += expense.amount
            by_user[payer_id]["count"] += 1
    
    # Monthly breakdown
    from collections import defaultdict
    by_month = defaultdict(lambda: {"count": 0, "total": 0})
    for expense in expenses:
        month_key = expense.expense_date.strftime("%Y-%m")
        by_month[month_key]["count"] += 1
        by_month[month_key]["total"] += expense.amount
    
    # Find largest expense
    largest = max(expenses, key=lambda e: e.amount)
    largest_payer = await User.get(largest.paid_by.id) if largest.paid_by else None
    
    # Most active payer
    most_active_id = max(by_user.items(), key=lambda x: x[1]["count"])[0] if by_user else None
    
    return {
        "total_expenses": len(expenses),
        "total_amount": total_amount,
        "by_category": by_category,
        "by_user": by_user,
        "by_month": dict(by_month),
        "average_expense": total_amount / len(expenses) if expenses else 0,
        "largest_expense": {
            "id": str(largest.id),
            "title": largest.title,
            "amount": largest.amount,
            "paid_by": largest_payer.full_name or largest_payer.username if largest_payer else "Unknown"
        },
        "most_active_payer": by_user.get(most_active_id, {}).get("name") if most_active_id else None
    }

@router.get("/trip/{trip_id}/report")
async def generate_trip_report(trip_id: str, format: str = "json"):
    """Generate a comprehensive expense report for a trip"""
    trip = await Trip.get(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    expenses = await Expense.find(Expense.trip.id == trip_id).to_list()
    
    # Get all members
    members = []
    for member_link in trip.members:
        member = await User.get(member_link.id)
        if member:
            members.append({
                "id": str(member.id),
                "name": member.full_name or member.username
            })
    
    # Calculate balances
    balances = defaultdict(float)
    for expense in expenses:
        # Payer
        payer_id = None
        if expense.paid_by:
            if hasattr(expense.paid_by, 'id'):
                payer_id = str(expense.paid_by.id)
        
        if payer_id:
            balances[payer_id] += expense.amount
            
        # Participants
        shares = calculate_shares(expense)
        for uid, share_amount in shares.items():
            balances[uid] -= share_amount
    
    # Create member summaries
    member_summaries = []
    for member in members:
        balance = balances.get(member["id"], 0)
        member_summaries.append({
            "name": member["name"],
            "balance": round(balance, 2),
            "status": "owes" if balance < 0 else "owed" if balance > 0 else "settled"
        })
    
    report = {
        "trip": {
            "id": str(trip.id),
            "title": trip.title,
            "destination": trip.destination,
            "start_date": trip.start_date,
            "end_date": trip.end_date,
            "currency": trip.currency
        },
        "summary": {
            "total_expenses": len(expenses),
            "total_spent": trip.total_spent,
            "total_budget": trip.total_budget,
            "budget_remaining": trip.total_budget - trip.total_spent if trip.total_budget > 0 else None
        },
        "members": member_summaries,
        "expenses": [
            {
                "title": e.title,
                "amount": e.amount,
                "category": e.category.value if e.category else "other",
                "date": e.expense_date
            } for e in expenses
        ],
        "generated_at": datetime.now(timezone.utc)
    }
    
    return report

@router.get("/trip/{trip_id}/balances")
async def get_trip_balances(trip_id: str):
    """Calculate balances (who owes whom) for a trip"""
    expenses = await Expense.find(Expense.trip.id == trip_id).to_list()
    
    # 1. Calculate Net Balances
    # balances[user_id] = amount_paid - amount_consumed
    balances = defaultdict(float)
    
    for expense in expenses:
        # Payer
        payer_id = None
        if expense.paid_by:
            if hasattr(expense.paid_by, 'id'):
                payer_id = str(expense.paid_by.id)
            elif hasattr(expense.paid_by, 'ref'):
                payer_id = str(expense.paid_by.ref.id)
        
        if payer_id:
            balances[payer_id] += expense.amount
            
        # Participants (Consumers)
        shares = calculate_shares(expense)
        for uid, share_amount in shares.items():
            balances[uid] -= share_amount

    # 2. Simplify Debts
    # Split into debtors and creditors
    debtors = []
    creditors = []
    
    for uid, amount in balances.items():
        # Round to 2 decimal places to avoid floating point errors
        amount = round(amount, 2)
        if amount < -0.01:
            debtors.append({'id': uid, 'amount': amount})
        elif amount > 0.01:
            creditors.append({'id': uid, 'amount': amount})
            
    # Match them
    transactions = []
    
    # Sort by magnitude to optimize (greedy approach)
    debtors.sort(key=lambda x: x['amount']) # Ascending (most negative first)
    creditors.sort(key=lambda x: x['amount'], reverse=True) # Descending (most positive first)
    
    i = 0
    j = 0
    
    while i < len(debtors) and j < len(creditors):
        debtor = debtors[i]
        creditor = creditors[j]
        
        # The amount to settle is the minimum of what debtor owes and creditor is owed
        amount = min(abs(debtor['amount']), creditor['amount'])
        
        # Determine sender and receiver details (fetch User objects later if needed, returning IDs for now)
        transactions.append({
            "from_user": debtor['id'],
            "to_user": creditor['id'],
            "amount": round(amount, 2)
        })
        
        # Update remaining amounts
        debtor['amount'] += amount
        creditor['amount'] -= amount
        
        # If settled, move to next
        if abs(debtor['amount']) < 0.01:
            i += 1
        if creditor['amount'] < 0.01:
            j += 1
            
    # Resolve User Objects for better UI
    detailed_transactions = []
    user_cache = {}
    
    async def get_user_name(uid):
        if uid in user_cache:
            return user_cache[uid]
        try:
             from bson import ObjectId
             u = await User.get(ObjectId(uid))
             if u:
                 name = u.full_name or u.username
                 user_cache[uid] = name
                 return name
        except:
            pass
        return "Unknown"

    for t in transactions:
        from_name = await get_user_name(t['from_user'])
        to_name = await get_user_name(t['to_user'])
        
        detailed_transactions.append({
            "from": t['from_user'],
            "from_name": from_name,
            "to": t['to_user'],
            "to_name": to_name,
            "amount": t['amount']
        })

    return detailed_transactions


def calculate_shares(expense: Expense) -> dict:
    """
    Calculate how much each participant owes for a given expense.
    Returns: dict {user_id: amount}
    """
    shares = {}
    
    # Get participant IDs
    participant_ids = []
    if expense.participants:
        for p in expense.participants:
            if hasattr(p, 'id'):
                participant_ids.append(str(p.id))
            elif hasattr(p, 'ref'):
                participant_ids.append(str(p.ref.id))
                
    if not participant_ids:
        return shares
        
    num_people = len(participant_ids)
    if num_people == 0:
        return shares

    split_type = expense.split_type or "equal"
    total_amount = expense.amount
    
    if split_type == "equal":
        share_per_person = total_amount / num_people
        for pid in participant_ids:
            shares[pid] = share_per_person
            
    elif split_type == "custom":
        # Expect split_data to be JSON: {"user_id": amount, ...}
        try:
            if expense.split_data:
                custom_splits = json.loads(expense.split_data)
                # Normalize keys (ensure strings)
                for pid, amount in custom_splits.items():
                    shares[str(pid)] = float(amount)
        except:
             # Fallback to equal
             share_per_person = total_amount / num_people
             for pid in participant_ids:
                shares[pid] = share_per_person

    elif split_type == "percentage":
        # Expect split_data to be JSON: {"user_id": percentage, ...}
        try:
            if expense.split_data:
                percent_splits = json.loads(expense.split_data)
                for pid, percent in percent_splits.items():
                    shares[str(pid)] = total_amount * (float(percent) / 100.0)
        except:
             # Fallback
             pass
             
    elif split_type == "shares":
        # Expect split_data to be JSON: {"user_id": number_of_shares, ...}
         try:
            if expense.split_data:
                share_splits = json.loads(expense.split_data)
                total_shares = sum(float(v) for v in share_splits.values())
                if total_shares > 0:
                    for pid, user_shares in share_splits.items():
                        shares[str(pid)] = total_amount * (float(user_shares) / total_shares)
         except:
             pass
             
    # Sanity Calculation: ensure sum of shares equals total_amount (or close enough)
    # If not, add/subtract remainder from first person or payer (for simplicity, first person)
    # This is important for "equal" splits involving repeating decimals
    
    calculated_total = sum(shares.values())
    diff = total_amount - calculated_total
    
    if abs(diff) > 0.001 and participant_ids:
        # adjust first participant
        first_pid = participant_ids[0]
        if first_pid in shares:
            shares[first_pid] += diff
        else:
            shares[first_pid] = diff # Should not happen usually

    return shares

    
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
