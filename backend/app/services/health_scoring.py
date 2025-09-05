"""
Customer Health Scoring Service

This module implements the actual health scoring logic based on customer behavior.
M3: Implements login frequency scoring as the first real health factor.
M4: Adds feature adoption scoring as the second real health factor.
"""
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Set
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


def calc_feature_adoption_score(distinct_features_used: int, features_available: int = 15) -> float:
    """
    Calculate feature adoption score based on distinct features used.
    
    Args:
        distinct_features_used: Number of unique features the customer has used
        features_available: Total number of features available (default: 15)
        
    Returns:
        float: Feature adoption score between 0-100
        
    Scoring Logic:
    - Calculate adoption rate: distinct_features_used / features_available
    - 0% adoption = 0 points
    - 1-20% adoption = 30 points  (Basic usage)
    - 21-40% adoption = 50 points (Moderate usage)
    - 41-60% adoption = 70 points (Good usage)
    - 61-80% adoption = 85 points (Advanced usage)
    - 81%+ adoption = 100 points (Power user)
    """
    if features_available <= 0 or distinct_features_used < 0:
        return 0.0
    
    adoption_rate = min(distinct_features_used / features_available, 1.0)
    
    if adoption_rate == 0:
        return 0.0
    elif adoption_rate <= 0.20:
        return 30.0
    elif adoption_rate <= 0.40:
        return 50.0
    elif adoption_rate <= 0.60:
        return 70.0
    elif adoption_rate <= 0.80:
        return 85.0
    else:
        return 100.0


def get_customer_feature_usage_30d(db: Session, customer_id: str) -> List[Event]:
    """
    Fetch feature_use events for a customer from the past 30 days.
    
    Args:
        db: Database session
        customer_id: Customer UUID
        
    Returns:
        List of feature_use events from past 30 days
    """
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    events = db.query(Event).filter(
        and_(
            Event.customer_id == customer_id,
            Event.event_type == 'feature_use',
            Event.ts >= thirty_days_ago
        )
    ).all()
    
    return events


def get_distinct_features_used(feature_events: List[Event]) -> Set[str]:
    """
    Extract distinct features used from feature_use events.
    
    Args:
        feature_events: List of feature_use events
        
    Returns:
        Set of unique feature names used
    """
    features = set()
    for event in feature_events:
        if event.event_metadata and 'feature' in event.event_metadata:
            features.add(event.event_metadata['feature'])
    return features


def calculate_customer_health_score(db: Session, customer: Customer) -> Dict[str, Any]:
    """
    Calculate comprehensive health score for a customer.
    
    M3 Implementation: Uses real login frequency + stub factors with weights.
    M4 Implementation: Adds real feature adoption scoring with configurable weights.
    
    Args:
        db: Database session
        customer: Customer model instance
        
    Returns:
        Dict containing score breakdown and final score
    """
    # Get login events for scoring (M3)
    login_events = get_customer_login_events_30d(db, customer.id)
    login_score = calc_login_score(login_events)
    
    # Get feature usage events for scoring (M4)
    feature_events = get_customer_feature_usage_30d(db, customer.id)
    distinct_features = get_distinct_features_used(feature_events)
    feature_adoption_score = calc_feature_adoption_score(len(distinct_features))
    
    # Stub scores for other factors (will be implemented in future milestones)
    support_ticket_score = 75.0  # Stub: assume moderate support activity
    payment_health_score = 90.0  # Stub: assume good payment status
    
    # Configurable weights via environment variables (M4 requirement)
    weights = {
        'login_frequency': float(os.getenv('WEIGHT_LOGIN_FREQUENCY', '0.35')),      # 35% - Real factor
        'feature_adoption': float(os.getenv('WEIGHT_FEATURE_ADOPTION', '0.35')),    # 35% - Real factor (M4)
        'support_tickets': float(os.getenv('WEIGHT_SUPPORT_TICKETS', '0.15')),      # 15% - Stub
        'payment_health': float(os.getenv('WEIGHT_PAYMENT_HEALTH', '0.15'))         # 15% - Stub
    }
    
    # Calculate weighted total
    weighted_score = (
        login_score * weights['login_frequency'] +
        feature_adoption_score * weights['feature_adoption'] +
        support_ticket_score * weights['support_tickets'] +
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
            'feature_adoption': {
                'score': feature_adoption_score,
                'weight': weights['feature_adoption'],
                'distinct_features_used': len(distinct_features),
                'features_used': sorted(list(distinct_features)),
                'adoption_rate': round(len(distinct_features) / 15 * 100, 1)
            },
            'support_tickets': {
                'score': support_ticket_score,
                'weight': weights['support_tickets'],
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
