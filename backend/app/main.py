from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import random

from .database import get_db
from .models import Customer

app = FastAPI(title="Customer Health API", version="1.0.0")

def calculate_mock_score(customer: Customer) -> dict:
    """
    Calculate a mock health score for a customer.
    In M2, this is still mocked but will be real in later milestones.
    """
    # Generate a consistent but varied score based on customer data
    random.seed(hash(str(customer.id)))
    score = random.randint(60, 95)
    
    if score >= 85:
        label = "Healthy"
    elif score >= 70:
        label = "At Risk"
    else:
        label = "Unhealthy"
    
    return {
        "score": score,
        "label": label,
        "last_updated": datetime.now().isoformat()
    }

@app.get("/")
def read_root():
    return {"message": "Customer Health API is running"}

@app.get("/api/customers")
def get_customers(db: Session = Depends(get_db)):
    """
    Return customers from database with mock health scores.
    M2 implementation: reads customers from DB, scores still mocked.
    """
    # Fetch all customers from database
    customers = db.query(Customer).all()
    
    # Transform to API response format with mock scores
    customer_list = []
    for customer in customers:
        health_data = calculate_mock_score(customer)
        customer_data = {
            "id": str(customer.id),
            "name": customer.name,
            "segment": customer.segment,
            "score": health_data["score"],
            "label": health_data["label"],
            "last_updated": health_data["last_updated"]
        }
        customer_list.append(customer_data)
    
    return customer_list

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
