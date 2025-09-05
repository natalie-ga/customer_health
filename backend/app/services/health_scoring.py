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


def calc_support_ticket_score(open_tickets: int, closed_tickets: int, severity_weights: Dict[str, float] = None) -> float:
    """
    Calculate support ticket score based on ticket volume (inverse scoring).
    
    Args:
        open_tickets: Number of currently open tickets
        closed_tickets: Number of closed tickets in the period
        severity_weights: Optional weights for different severities
        
    Returns:
        float: Support ticket score between 0-100 (lower tickets = higher score)
        
    Scoring Logic (Inverse):
    - More open tickets = lower score (indicates ongoing issues)
    - High volume of tickets overall = lower score (indicates problematic customer)
    - Weight open tickets more heavily than closed ones
    - 0 tickets = 100 points (perfect)
    - 1-2 tickets = 85 points (very good)
    - 3-5 tickets = 70 points (acceptable)
    - 6-10 tickets = 50 points (concerning)
    - 11-15 tickets = 30 points (high risk)
    - 16+ tickets = 10 points (critical risk)
    """
    # Weight open tickets more heavily (2x impact)
    weighted_ticket_count = (open_tickets * 2) + closed_tickets
    
    if weighted_ticket_count == 0:
        return 100.0
    elif weighted_ticket_count <= 2:
        return 85.0
    elif weighted_ticket_count <= 5:
        return 70.0
    elif weighted_ticket_count <= 10:
        return 50.0
    elif weighted_ticket_count <= 15:
        return 30.0
    else:
        return 10.0


def get_customer_support_tickets_30d(db: Session, customer_id: str) -> Dict[str, List[Event]]:
    """
    Fetch support ticket events for a customer from the past 30 days.
    
    Args:
        db: Database session
        customer_id: Customer UUID
        
    Returns:
        Dict with 'open' and 'close' ticket events from past 30 days
    """
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    # Get all ticket events
    ticket_events = db.query(Event).filter(
        and_(
            Event.customer_id == customer_id,
            Event.event_type.in_(['ticket_open', 'ticket_close']),
            Event.ts >= thirty_days_ago
        )
    ).order_by(Event.ts.asc()).all()
    
    open_events = [e for e in ticket_events if e.event_type == 'ticket_open']
    close_events = [e for e in ticket_events if e.event_type == 'ticket_close']
    
    return {
        'open': open_events,
        'close': close_events
    }


def calculate_open_ticket_count(ticket_events: Dict[str, List[Event]]) -> Dict[str, int]:
    """
    Calculate the number of currently open tickets based on open/close events.
    
    Args:
        ticket_events: Dict with 'open' and 'close' event lists
        
    Returns:
        Dict with counts: {'open': int, 'closed': int, 'net_open': int}
    """
    open_events = ticket_events['open']
    close_events = ticket_events['close']
    
    # Get ticket IDs that were opened
    opened_ticket_ids = set()
    for event in open_events:
        if event.event_metadata and 'ticket_id' in event.event_metadata:
            opened_ticket_ids.add(event.event_metadata['ticket_id'])
    
    # Get ticket IDs that were closed
    closed_ticket_ids = set()
    for event in close_events:
        if event.event_metadata and 'ticket_id' in event.event_metadata:
            closed_ticket_ids.add(event.event_metadata['ticket_id'])
    
    # Calculate net open tickets (opened but not yet closed)
    net_open_tickets = opened_ticket_ids - closed_ticket_ids
    
    return {
        'open': len(open_events),
        'closed': len(close_events), 
        'net_open': len(net_open_tickets)
    }


def calculate_customer_health_score(db: Session, customer: Customer) -> Dict[str, Any]:
    """
    Calculate comprehensive health score for a customer.
    
    M3 Implementation: Uses real login frequency + stub factors with weights.
    M4 Implementation: Adds real feature adoption scoring with configurable weights.
    M5 Implementation: Adds real support ticket volume scoring (inverse).
    
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
    
    # Get support ticket events for scoring (M5)
    ticket_events = get_customer_support_tickets_30d(db, customer.id)
    ticket_counts = calculate_open_ticket_count(ticket_events)
    support_ticket_score = calc_support_ticket_score(
        ticket_counts['net_open'], 
        ticket_counts['closed']
    )
    
    # Stub scores for remaining factors
    payment_health_score = 90.0  # Stub: assume good payment status
    
    # Configurable weights via environment variables (M5 update)
    weights = {
        'login_frequency': float(os.getenv('WEIGHT_LOGIN_FREQUENCY', '0.30')),      # 30% - Real factor
        'feature_adoption': float(os.getenv('WEIGHT_FEATURE_ADOPTION', '0.30')),    # 30% - Real factor (M4)
        'support_tickets': float(os.getenv('WEIGHT_SUPPORT_TICKETS', '0.25')),      # 25% - Real factor (M5)
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
                'total_opened': ticket_counts['open'],
                'total_closed': ticket_counts['closed'],
                'currently_open': ticket_counts['net_open'],
                'weighted_count': (ticket_counts['net_open'] * 2) + ticket_counts['closed']
            },
            'payment_health': {
                'score': payment_health_score,
                'weight': weights['payment_health'],
                'note': 'Stub implementation'
            }
        },
        'last_updated': datetime.now().isoformat()
    }
