from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .notifications import send_notification_sql
from database_sql import get_db, ChecklistItem, User, Trip, increment_trip_members_version
from schemas_sql import ChecklistItem as ChecklistItemSchema, ChecklistItemCreate, ChecklistItemUpdate
from datetime import datetime, timezone

router = APIRouter(prefix="/checklist", tags=["checklist"])

@router.get("/trip/{trip_id}", response_model=List[ChecklistItemSchema])
def get_checklist_items(trip_id: int, db: Session = Depends(get_db)):
    """Get all checklist items for a trip"""
    items = db.query(ChecklistItem).filter(ChecklistItem.trip_id == trip_id).all()
    return items

@router.get("/{item_id}", response_model=ChecklistItemSchema)
def get_checklist_item(item_id: int, db: Session = Depends(get_db)):
    """Get a specific checklist item"""
    item = db.query(ChecklistItem).filter(ChecklistItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    return item

@router.post("/", response_model=ChecklistItemSchema, status_code=status.HTTP_201_CREATED)
def create_checklist_item(item: ChecklistItemCreate, db: Session = Depends(get_db)):
    """Create a new checklist item"""
    trip = db.query(Trip).filter(Trip.id == item.trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    assignees = []
    if item.assignee_ids:
        assignees = db.query(User).filter(User.id.in_(item.assignee_ids)).all()

    db_item = ChecklistItem(
        trip_id=item.trip_id,
        title=item.title,
        description=item.description,
        category=item.category,
        priority=item.priority,
        due_date=item.due_date,
        assignees=assignees,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    
    # Real-time sync
    increment_trip_members_version(db, db_item.trip_id)

    # Notify assignees
    for assignee in assignees:
        send_notification_sql(
            db,
            user_id=assignee.id,
            title="Task Assigned",
            message=f"You've been assigned to: {db_item.title} in '{trip.title}'",
            notification_type="system",
            action_url=f"/trip/{trip.id}/checklist"
        )

    return db_item

@router.put("/{item_id}", response_model=ChecklistItemSchema)
def update_checklist_item(item_id: int, item_update: ChecklistItemUpdate, db: Session = Depends(get_db)):
    """Update checklist item"""
    item = db.query(ChecklistItem).filter(ChecklistItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    
    update_data = item_update.dict(exclude_unset=True)
    
    if 'is_completed' in update_data:
        if update_data['is_completed'] and not item.is_completed:
            item.completed_at = datetime.now(timezone.utc)
        elif not update_data['is_completed']:
            item.completed_at = None
    
    for key, value in update_data.items():
        setattr(item, key, value)
        
    item.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(item)
    
    # Real-time sync
    increment_trip_members_version(db, item.trip_id)
    return item

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_checklist_item(item_id: int, db: Session = Depends(get_db)):
    """Delete a checklist item"""
    item = db.query(ChecklistItem).filter(ChecklistItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    
    trip_id = item.trip_id
    db.delete(item)
    db.commit()
    
    # Real-time sync
    increment_trip_members_version(db, trip_id)
    return None

@router.post("/{item_id}/toggle")
def toggle_checklist_item(item_id: int, db: Session = Depends(get_db)):
    """Toggle checklist item completion status"""
    item = db.query(ChecklistItem).filter(ChecklistItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    
    item.is_completed = not item.is_completed
    item.completed_at = datetime.now(timezone.utc) if item.is_completed else None
    item.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(item)
    
    # Real-time sync
    increment_trip_members_version(db, item.trip_id)
    return item

@router.get("/trip/{trip_id}/summary")
def get_checklist_summary(trip_id: int, db: Session = Depends(get_db)):
    """Get checklist summary for a trip"""
    items = db.query(ChecklistItem).filter(ChecklistItem.trip_id == trip_id).all()
    
    total = len(items)
    completed = sum(1 for item in items if item.is_completed)
    
    summary = {
        "total_items": total,
        "completed_items": completed,
        "pending_items": total - completed,
        "completion_percentage": (completed / total * 100) if total > 0 else 0,
        "by_category": {},
        "by_priority": {}
    }
    
    for item in items:
        category = item.category or "uncategorized"
        if category not in summary["by_category"]:
            summary["by_category"][category] = {"total": 0, "completed": 0}
        summary["by_category"][category]["total"] += 1
        if item.is_completed:
            summary["by_category"][category]["completed"] += 1
    
    for item in items:
        priority = item.priority or "medium"
        if priority not in summary["by_priority"]:
            summary["by_priority"][priority] = {"total": 0, "completed": 0}
        summary["by_priority"][priority]["total"] += 1
        if item.is_completed:
            summary["by_priority"][priority]["completed"] += 1
    
    return summary
