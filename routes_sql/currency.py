from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from sqlalchemy.orm import Session
from database_sql import CurrencyRate, get_db
from schemas_sql import CurrencyRate as CurrencyRateSchema, CurrencyRateCreate
from datetime import datetime, timezone
from utils.timezone_utils import get_ist_now

router = APIRouter(prefix="/currency", tags=["currency"])

@router.get("/rates", response_model=List[CurrencyRateSchema])
def get_currency_rates(from_currency: Optional[str] = None, to_currency: Optional[str] = None, db: Session = Depends(get_db)):
    """Get currency exchange rates"""
    query = db.query(CurrencyRate)
    
    if from_currency:
        query = query.filter(CurrencyRate.from_currency == from_currency.upper())
    
    if to_currency:
        query = query.filter(CurrencyRate.to_currency == to_currency.upper())
    
    rates = query.all()
    return rates

@router.get("/convert")
def convert_currency(amount: float, from_currency: str, to_currency: str, db: Session = Depends(get_db)):
    """Convert amount from one currency to another"""
    from_curr = from_currency.upper()
    to_curr = to_currency.upper()
    
    if from_curr == to_curr:
        return {
            "amount": amount,
            "from_currency": from_curr,
            "to_currency": to_curr,
            "converted_amount": amount,
            "rate": 1.0
        }
    
    rate_record = db.query(CurrencyRate).filter(
        CurrencyRate.from_currency == from_curr,
        CurrencyRate.to_currency == to_curr
    ).first()
    
    if not rate_record:
        reverse_rate = db.query(CurrencyRate).filter(
            CurrencyRate.from_currency == to_curr,
            CurrencyRate.to_currency == from_curr
        ).first()
        
        if reverse_rate:
            rate = 1.0 / reverse_rate.rate
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Exchange rate not found for {from_curr} to {to_curr}"
            )
    else:
        rate = rate_record.rate
    
    converted_amount = amount * rate
    
    return {
        "amount": amount,
        "from_currency": from_curr,
        "to_currency": to_curr,
        "converted_amount": round(converted_amount, 2),
        "rate": rate
    }

@router.post("/rates", response_model=CurrencyRateSchema, status_code=status.HTTP_201_CREATED)
def create_or_update_rate(rate: CurrencyRateCreate, db: Session = Depends(get_db)):
    """Create or update a currency exchange rate"""
    from_curr = rate.from_currency.upper()
    to_curr = rate.to_currency.upper()
    
    existing_rate = db.query(CurrencyRate).filter(
        CurrencyRate.from_currency == from_curr,
        CurrencyRate.to_currency == to_curr
    ).first()
    
    if existing_rate:
        existing_rate.rate = rate.rate
        existing_rate.source = rate.source
        existing_rate.updated_at = get_ist_now()
        db.commit()
        db.refresh(existing_rate)
        return existing_rate
    else:
        db_rate = CurrencyRate(
            from_currency=from_curr,
            to_currency=to_curr,
            rate=rate.rate,
            source=rate.source,
            updated_at=get_ist_now()
        )
        db.add(db_rate)
        db.commit()
        db.refresh(db_rate)
        return db_rate

@router.delete("/rates/{rate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rate(rate_id: int, db: Session = Depends(get_db)):
    """Delete a currency rate"""
    rate = db.query(CurrencyRate).filter(CurrencyRate.id == rate_id).first()
    if not rate:
        raise HTTPException(status_code=404, detail="Currency rate not found")
    
    db.delete(rate)
    db.commit()
    return None

@router.post("/rates/seed")
def seed_common_rates(db: Session = Depends(get_db)):
    """Seed database with common currency exchange rates"""
    common_rates = [
        {"from": "USD", "to": "EUR", "rate": 0.92},
        {"from": "USD", "to": "GBP", "rate": 0.79},
        {"from": "USD", "to": "JPY", "rate": 149.50},
        {"from": "USD", "to": "INR", "rate": 83.12},
        {"from": "USD", "to": "AUD", "rate": 1.52},
        {"from": "USD", "to": "CAD", "rate": 1.36},
    ]
    
    created_count = 0
    updated_count = 0
    
    for rate_data in common_rates:
        existing = db.query(CurrencyRate).filter(
            CurrencyRate.from_currency == rate_data["from"],
            CurrencyRate.to_currency == rate_data["to"]
        ).first()
        
        if existing:
            existing.rate = rate_data["rate"]
            existing.source = "seed"
            existing.updated_at = get_ist_now()
            updated_count += 1
        else:
            new_rate = CurrencyRate(
                from_currency=rate_data["from"],
                to_currency=rate_data["to"],
                rate=rate_data["rate"],
                source="seed",
                updated_at=get_ist_now()
            )
            db.add(new_rate)
            created_count += 1
    
    db.commit()
    return {"created": created_count, "updated": updated_count}
