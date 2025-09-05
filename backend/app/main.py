from fastapi import FastAPI
from datetime import datetime
import json

app = FastAPI(title="Customer Health API", version="1.0.0")

@app.get("/")
def read_root():
    return {"message": "Customer Health API is running"}

@app.get("/api/customers")
def get_customers():
    """
    Return a mock list of customers with health scores.
    This is the M0 walking skeleton implementation.
    """
    mock_customer = {
        "id": "c_1",
        "name": "Acme",
        "segment": "smb", 
        "score": 82,
        "label": "Healthy",
        "last_updated": datetime.now().isoformat()
    }
    
    return [mock_customer]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
