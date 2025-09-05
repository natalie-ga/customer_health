"""
Customer Health Scoring Service

This module implements the actual health scoring logic based on customer behavior.
M3: Implements login frequency scoring as the first real health factor.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from ..models import Customer, Event


def calc_login_score(events_30d: List[Event]) -> float:
    """
    Calculate login frequency score based on 30 days of login events.
    
    Args:
        events_30d: List of login events from past 30 days
        
    Returns:
        float: Login score between 0-100
        
    Scoring Logic:
    - Count unique login days (not total logins)
    - 0 days = 0 points
    - 1-5 days = 20 points  (Low activity)
    - 6-15 days = 50 points (Moderate activity) 
    - 16-20 days = 70 points (Good activity)
    - 21-25 days = 85 points (High activity)
    - 26+ days = 100 points (Excellent activity)
    """
    if not events_30d:
        return 0.0
    
    # Count unique login days (not total login events)
    unique_login_days = set()
    for event in events_30d:
        # Extract just the date part (ignore time)
        login_date = event.ts.date()
        unique_login_days.add(login_date)
    
    day_count = len(unique_login_days)
    
    # Score mapping based on unique active days
    if day_count == 0:
        return 0.0
    elif day_count <= 5:
        return 20.0
    elif day_count <= 15:
        return 50.0
    elif day_count <= 20:
        return 70.0
    elif day_count <= 25:
        return 85.0
    else:
        return 100.0


def get_customer_login_events_30d(db: Session, customer_id: str) -> List[Event]:
    """
    Fetch login events for a customer from the past 30 days.
    
    Args:
        db: Database session
        customer_id: Customer UUID
        
    Returns:
        List of login events from past 30 days
    """
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    events = db.query(Event).filter(
        and_(
            Event.customer_id == customer_id,
            Event.event_type == 'login',
            Event.ts >= thirty_days_ago
        )
    ).order_by(Event.ts.desc()).all()
    
    return events


def calculate_customer_health_score(db: Session, customer: Customer) -> Dict[str, Any]:
    """
    Calculate comprehensive health score for a customer.
    
    M3 Implementation: Uses real login frequency + stub factors with weights.
    
    Args:
        db: Database session
        customer: Customer model instance
        
    Returns:
        Dict containing score breakdown and final score
    """
    # Get login events for scoring
    login_events = get_customer_login_events_30d(db, customer.id)
    
    # Calculate login frequency score (real implementation)
    login_score = calc_login_score(login_events)
    
    # Stub scores for other factors (will be implemented in future milestones)
    support_ticket_score = 75.0  # Stub: assume moderate support activity
    feature_usage_score = 80.0   # Stub: assume good feature usage
    payment_health_score = 90.0  # Stub: assume good payment status
    
    # Weighted scoring system
    weights = {
        'login_frequency': 0.4,      # 40% - Primary focus for M3
        'support_tickets': 0.2,      # 20% - Stub
        'feature_usage': 0.25,       # 25% - Stub  
        'payment_health': 0.15       # 15% - Stub
    }
    
    # Calculate weighted total
    weighted_score = (
        login_score * weights['login_frequency'] +
        support_ticket_score * weights['support_tickets'] +
        feature_usage_score * weights['feature_usage'] +
        payment_health_score * weights['payment_health']
    )
    
    # Determine health label
    if weighted_score >= 80:
        label = "Healthy"
    elif weighted_score >= 60:
        label = "At Risk"
    else:
        label = "Unhealthy"
    
    return {
        'score': round(weighted_score, 1),
        'label': label,
        'breakdown': {
            'login_frequency': {
                'score': login_score,
                'weight': weights['login_frequency'],
                'login_days': len(set(event.ts.date() for event in login_events)),
                'total_logins': len(login_events)
            },
            'support_tickets': {
                'score': support_ticket_score,
                'weight': weights['support_tickets'],
                'note': 'Stub implementation'
            },
            'feature_usage': {
                'score': feature_usage_score,
                'weight': weights['feature_usage'],
                'note': 'Stub implementation'
            },
            'payment_health': {
                'score': payment_health_score,
                'weight': weights['payment_health'],
                'note': 'Stub implementation'
            }
        },
        'last_updated': datetime.now().isoformat()
    }
