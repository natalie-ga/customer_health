from fastapi import FastAPI, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel

from .database import get_db
from .models import Customer, Event
from .services.health_scoring import calculate_customer_health_score

class EventCreate(BaseModel):
    event_type: str
    ts: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

app = FastAPI(title="Customer Health API", version="1.0.0")

@app.get("/")
def read_root():
    return {"message": "Customer Health API is running"}

@app.get("/api/customers")
def get_customers(db: Session = Depends(get_db)):
    """
    Return customers from database with real health scores based on login frequency.
    M3 implementation: Uses actual login events for scoring with weighted factors.
    """
    # Fetch all customers from database
    customers = db.query(Customer).all()
    
    # Transform to API response format with real health scores
    customer_list = []
    for customer in customers:
        # Calculate real health score using login frequency + weighted factors
        health_data = calculate_customer_health_score(db, customer)
        
        customer_data = {
            "id": str(customer.id),
            "name": customer.name,
            "score": health_data["score"]
        }
        customer_list.append(customer_data)
    
    return customer_list

@app.get("/api/customers/{id}/health")
def get_customer_health(id: str, db: Session = Depends(get_db)):
    """
    Return the detailed health score breakdown for a specific customer.
    """
    customer = db.query(Customer).filter(Customer.id == id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    health_data = calculate_customer_health_score(db, customer)

    return {
        "id": str(customer.id),
        "name": customer.name,
        "score": health_data["score"],
        "label": health_data["label"],
        "last_updated": health_data["last_updated"],
        "breakdown": health_data["breakdown"]
    }

class EventCreate(BaseModel):
    event_type: str
    ts: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@app.post("/api/customers/{id}/events")
def create_customer_event(id: str, event_data: EventCreate, db: Session = Depends(get_db)):
    """
    Create a new customer event.
    E1 implementation: Accept event_type, optional ts and metadata, insert and return event.
    """
    # Verify customer exists
    customer = db.query(Customer).filter(Customer.id == id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Parse timestamp if provided, otherwise use current time
    event_timestamp = datetime.now()
    if event_data.ts:
        try:
            event_timestamp = datetime.fromisoformat(event_data.ts.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid timestamp format. Use ISO format.")
    
    # Create event object
    event = Event(
        customer_id=id,
        event_type=event_data.event_type,
        ts=event_timestamp,
        event_metadata=event_data.metadata
    )
    
    db.add(event)
    db.commit()
    db.refresh(event)
    
    return {
        "id": str(event.id),
        "customer_id": event.customer_id,
        "event_type": event.event_type,
        "ts": event.ts.isoformat(),
        "event_metadata": event.event_metadata
    }

@app.get("/api/customers/{id}/events")
def get_customer_events(id: str, db: Session = Depends(get_db)):
    """
    Get all events for a specific customer.
    """
    # Verify customer exists
    customer = db.query(Customer).filter(Customer.id == id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Get all events for this customer, ordered by timestamp (newest first)
    events = db.query(Event).filter(Event.customer_id == id).order_by(Event.ts.desc()).all()
    
    # Transform to API response format
    event_list = []
    for event in events:
        event_data = {
            "id": str(event.id),
            "customer_id": event.customer_id,
            "event_type": event.event_type,
            "ts": event.ts.isoformat(),
            "event_metadata": event.event_metadata
        }
        event_list.append(event_data)
    
    return {
        "customer_id": id,
        "customer_name": customer.name,
        "total_events": len(event_list),
        "events": event_list
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
