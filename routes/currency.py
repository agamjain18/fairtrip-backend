from fastapi import APIRouter, HTTPException
from typing import List, Optional
from database import CurrencyRate
from schemas import CurrencyRate as CurrencyRateSchema, CurrencyRateCreate
from datetime import datetime, timezone

router = APIRouter(prefix="/currency", tags=["currency"])

@router.get("/rates", response_model=List[CurrencyRateSchema])
async def get_currency_rates(from_currency: Optional[str] = None, to_currency: Optional[str] = None):
    """Get currency exchange rates"""
    query = {}
    
    if from_currency:
        query["from_currency"] = from_currency.upper()
    
    if to_currency:
        query["to_currency"] = to_currency.upper()
    
    if query:
        rates = await CurrencyRate.find(query).to_list()
    else:
        rates = await CurrencyRate.find_all().to_list()
    
    return rates

@router.get("/convert")
async def convert_currency(amount: float, from_currency: str, to_currency: str):
    """Convert amount from one currency to another"""
    from_curr = from_currency.upper()
    to_curr = to_currency.upper()
    
    # If same currency, return as is
    if from_curr == to_curr:
        return {
            "amount": amount,
            "from_currency": from_curr,
            "to_currency": to_curr,
            "converted_amount": amount,
            "rate": 1.0
        }
    
    # Find exchange rate
    rate_record = await CurrencyRate.find_one({
        "from_currency": from_curr,
        "to_currency": to_curr
    })
    
    if not rate_record:
        # Try reverse rate
        reverse_rate = await CurrencyRate.find_one({
            "from_currency": to_curr,
            "to_currency": from_curr
        })
        
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

@router.post("/rates", response_model=CurrencyRateSchema, status_code=201)
async def create_or_update_rate(rate: CurrencyRateCreate):
    """Create or update a currency exchange rate"""
    from_curr = rate.from_currency.upper()
    to_curr = rate.to_currency.upper()
    
    # Check if rate already exists
    existing_rate = await CurrencyRate.find_one({
        "from_currency": from_curr,
        "to_currency": to_curr
    })
    
    if existing_rate:
        # Update existing rate
        existing_rate.rate = rate.rate
        existing_rate.source = rate.source
        existing_rate.updated_at = datetime.now(timezone.utc)
        await existing_rate.save()
        return existing_rate
    else:
        # Create new rate
        db_rate = CurrencyRate(
            from_currency=from_curr,
            to_currency=to_curr,
            rate=rate.rate,
            source=rate.source,
            updated_at=datetime.now(timezone.utc)
        )
        await db_rate.insert()
        return db_rate

@router.delete("/rates/{rate_id}", status_code=204)
async def delete_rate(rate_id: str):
    """Delete a currency rate"""
    rate = await CurrencyRate.get(rate_id)
    if not rate:
        raise HTTPException(status_code=404, detail="Currency rate not found")
    
    await rate.delete()
    return None

@router.post("/rates/seed")
async def seed_common_rates():
    """Seed database with common currency exchange rates (approximate)"""
    common_rates = [
        # USD base rates
        {"from": "USD", "to": "EUR", "rate": 0.92},
        {"from": "USD", "to": "GBP", "rate": 0.79},
        {"from": "USD", "to": "JPY", "rate": 149.50},
        {"from": "USD", "to": "INR", "rate": 83.12},
        {"from": "USD", "to": "AUD", "rate": 1.52},
        {"from": "USD", "to": "CAD", "rate": 1.36},
        
        # EUR base rates
        {"from": "EUR", "to": "USD", "rate": 1.09},
        {"from": "EUR", "to": "GBP", "rate": 0.86},
        {"from": "EUR", "to": "INR", "rate": 90.45},
        
        # GBP base rates
        {"from": "GBP", "to": "USD", "rate": 1.27},
        {"from": "GBP", "to": "EUR", "rate": 1.16},
        {"from": "GBP", "to": "INR", "rate": 105.32},
    ]
    
    created_count = 0
    updated_count = 0
    
    for rate_data in common_rates:
        existing = await CurrencyRate.find_one({
            "from_currency": rate_data["from"],
            "to_currency": rate_data["to"]
        })
        
        if existing:
            existing.rate = rate_data["rate"]
            existing.source = "seed"
            existing.updated_at = datetime.now(timezone.utc)
            await existing.save()
            updated_count += 1
        else:
            new_rate = CurrencyRate(
                from_currency=rate_data["from"],
                to_currency=rate_data["to"],
                rate=rate_data["rate"],
                source="seed",
                updated_at=datetime.now(timezone.utc)
            )
            await new_rate.insert()
            created_count += 1
    
    return {
        "message": f"Seeded {created_count} new rates, updated {updated_count} existing rates",
        "created": created_count,
        "updated": updated_count
    }
