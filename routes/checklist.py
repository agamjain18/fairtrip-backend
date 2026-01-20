from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from database import ChecklistItem, User, Trip
from schemas import ChecklistItem as ChecklistItemSchema, ChecklistItemCreate, ChecklistItemUpdate
from datetime import datetime, timezone
from beanie import PydanticObjectId, Link

router = APIRouter(prefix="/checklist", tags=["checklist"])

@router.get("/trip/{trip_id}", response_model=List[ChecklistItemSchema])
async def get_checklist_items(trip_id: str):
    """Get all checklist items for a trip"""
    items = await ChecklistItem.find(ChecklistItem.trip.id == PydanticObjectId(trip_id)).to_list()
    return items

@router.get("/{item_id}", response_model=ChecklistItemSchema)
async def get_checklist_item(item_id: str):
    """Get a specific checklist item"""
    item = await ChecklistItem.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    return item

@router.post("/", response_model=ChecklistItemSchema, status_code=status.HTTP_201_CREATED)
async def create_checklist_item(item: ChecklistItemCreate):
    """Create a new checklist item"""
    trip = await Trip.get(item.trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    assignees = []
    if item.assignee_ids:
        for uid in item.assignee_ids:
            user = await User.get(uid)
            if user:
                assignees.append(user)

    db_item = ChecklistItem(
        trip=trip,
        title=item.title,
        description=item.description,
        category=item.category,
        priority=item.priority,
        due_date=item.due_date,
        assignees=assignees,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    await db_item.insert()
    return db_item

@router.put("/{item_id}", response_model=ChecklistItemSchema)
async def update_checklist_item(item_id: str, item_update: ChecklistItemUpdate):
    """Update checklist item"""
    item = await ChecklistItem.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    
    update_data = item_update.dict(exclude_unset=True)
    
    # Handle completion
    if 'is_completed' in update_data:
        if update_data['is_completed'] and not item.is_completed:
            item.completed_at = datetime.now(timezone.utc)
        elif not update_data['is_completed']:
            item.completed_at = None
    
    if update_data:
        await item.set(update_data)
        item.updated_at = datetime.now(timezone.utc)
        await item.save()

    return item

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_checklist_item(item_id: str):
    """Delete a checklist item"""
    item = await ChecklistItem.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    
    await item.delete()
    return None

@router.post("/{item_id}/toggle")
async def toggle_checklist_item(item_id: str):
    """Toggle checklist item completion status"""
    item = await ChecklistItem.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    
    item.is_completed = not item.is_completed
    item.completed_at = datetime.now(timezone.utc) if item.is_completed else None
    item.updated_at = datetime.now(timezone.utc)
    
    await item.save()
    return item

@router.get("/trip/{trip_id}/summary")
async def get_checklist_summary(trip_id: str):
    """Get checklist summary for a trip"""
    items = await ChecklistItem.find(ChecklistItem.trip.id == PydanticObjectId(trip_id)).to_list()
    
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
    
    # Group by category
    for item in items:
        category = item.category or "uncategorized"
        if category not in summary["by_category"]:
            summary["by_category"][category] = {"total": 0, "completed": 0}
        summary["by_category"][category]["total"] += 1
        if item.is_completed:
            summary["by_category"][category]["completed"] += 1
    
    # Group by priority
    for item in items:
        priority = item.priority or "medium"
        if priority not in summary["by_priority"]:
            summary["by_priority"][priority] = {"total": 0, "completed": 0}
        summary["by_priority"][priority]["total"] += 1
        if item.is_completed:
            summary["by_priority"][priority]["completed"] += 1
    
    return summary
