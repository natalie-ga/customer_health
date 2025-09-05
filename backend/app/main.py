from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from .database import get_db
from .models import Customer
from .services.health_scoring import calculate_customer_health_score

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
