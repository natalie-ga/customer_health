"""
Customer Health Scoring Service

This module implements the comprehensive health scoring logic based on customer behavior.
Implements 5 health factors: Login Frequency, Feature Adoption, Support Tickets, 
Payment Timeliness, and API Usage.
"""
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Set, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, text

from ..models import Customer, Event


def get_period_dates(days: int = 30) -> tuple[datetime, datetime]:
    """Get start and end dates for the analysis period."""
    # For demo purposes, use the last 30 days of actual data (2024-09-01 to 2024-09-30)
    # In production, this would be datetime.now() - timedelta(days=days)
    end_date = datetime(2024, 9, 30, 23, 59, 0)
    start_date = end_date - timedelta(days=days)
    return start_date, end_date


# 1. LOGIN FREQUENCY SCORE
def calc_login_frequency_score(db: Session, customer_id: str, period_start: datetime, period_end: datetime) -> Dict[str, Any]:
    """Calculate login frequency score based on days logged in vs total days in period."""
    # Get unique login days in period
    login_days_query = text("""
        SELECT DISTINCT DATE(ts) as login_date
        FROM events 
        WHERE event_type = 'user_login'
          AND ts >= :period_start 
          AND ts <= :period_end
          AND customer_id = :customer_id
    """)
    
    result = db.execute(login_days_query, {
        'period_start': period_start,
        'period_end': period_end,
        'customer_id': customer_id
    }).fetchall()
    
    days_logged_in = len(result)
    total_days_in_period = (period_end.date() - period_start.date()).days + 1
    
    if total_days_in_period == 0:
        login_frequency_percentage = 0
    else:
        login_frequency_percentage = (days_logged_in / total_days_in_period) * 100
    
    login_frequency_score = min(100, login_frequency_percentage)
    
    return {
        'score': round(login_frequency_score, 1),
        'days_logged_in': days_logged_in,
        'total_days_in_period': total_days_in_period,
        'login_frequency_percentage': round(login_frequency_percentage, 1)
    }


# 2. FEATURE ADOPTION SCORE
def calc_feature_adoption_score(db: Session, customer_id: str, period_start: datetime, period_end: datetime) -> Dict[str, Any]:
    """Calculate feature adoption score combining onboarding completion and feature usage diversity."""
    # Get feature metrics
    feature_metrics_query = text("""
        SELECT 
            COUNT(DISTINCT CASE 
                WHEN event_type = 'feature_onboarded' 
                  AND (event_metadata->>'completion_percentage')::int = 100
                THEN event_metadata->>'feature_name' 
            END) as features_onboarded,
            COUNT(DISTINCT CASE 
                WHEN event_type = 'feature_used' 
                THEN event_metadata->>'feature_name' 
            END) as features_used,
            COUNT(CASE WHEN event_type = 'feature_used' THEN 1 END) as total_feature_usage
        FROM events 
        WHERE event_type IN ('feature_onboarded', 'feature_used')
          AND ts >= :period_start 
          AND ts <= :period_end
          AND customer_id = :customer_id
    """)
    
    result = db.execute(feature_metrics_query, {
        'period_start': period_start,
        'period_end': period_end,
        'customer_id': customer_id
    }).fetchone()
    
    features_onboarded = result[0] if result[0] else 0
    features_used = result[1] if result[1] else 0
    total_feature_usage = result[2] if result[2] else 0
    
    # Assume 8 total features available
    total_features = 8
    
    # Calculate component scores
    onboarding_score = (features_onboarded / total_features) * 30  # 30% weight
    diversity_score = (min(total_features, features_used) / total_features) * 50  # 50% weight
    engagement_score = min(100, total_feature_usage / 10.0) * 0.2  # 20% weight
    
    feature_adoption_score = onboarding_score + diversity_score + engagement_score
    
    return {
        'score': round(feature_adoption_score, 1),
        'features_onboarded': features_onboarded,
        'features_used': features_used,
        'total_feature_usage': total_feature_usage,
        'onboarding_score': round(onboarding_score, 1),
        'diversity_score': round(diversity_score, 1),
        'engagement_score': round(engagement_score, 1)
    }


# 3. SUPPORT TICKET SCORE
def calc_support_ticket_score(db: Session, customer_id: str, period_start: datetime, period_end: datetime) -> Dict[str, Any]:
    """Calculate support health considering ticket volume, resolution rate, and escalations."""
    # Get support metrics
    support_metrics_query = text("""
        SELECT 
            COUNT(CASE WHEN event_type = 'support_ticket_created' THEN 1 END) as tickets_created,
            COUNT(CASE WHEN event_type = 'support_ticket_resolved' THEN 1 END) as tickets_resolved,
            COUNT(CASE 
                WHEN event_type = 'support_ticket_resolved' 
                  AND event_metadata->>'resolution_type' = 'escalated' 
                THEN 1 
            END) as tickets_escalated,
            COUNT(CASE 
                WHEN event_type = 'support_ticket_created' 
                  AND event_metadata->>'priority' IN ('high', 'critical')
                THEN 1 
            END) as high_priority_tickets,
            AVG(CASE 
                WHEN event_type = 'support_ticket_resolved' 
                  AND event_metadata->>'satisfaction_score' IS NOT NULL
                THEN (event_metadata->>'satisfaction_score')::float 
            END) as avg_satisfaction
        FROM events 
        WHERE event_type IN ('support_ticket_created', 'support_ticket_resolved')
          AND ts >= :period_start 
          AND ts <= :period_end
          AND customer_id = :customer_id
    """)
    
    result = db.execute(support_metrics_query, {
        'period_start': period_start,
        'period_end': period_end,
        'customer_id': customer_id
    }).fetchone()
    
    tickets_created = result[0] if result[0] else 0
    tickets_resolved = result[1] if result[1] else 0
    tickets_escalated = result[2] if result[2] else 0
    high_priority_tickets = result[3] if result[3] else 0
    avg_satisfaction = result[4] if result[4] else None
    
    # Calculate currently open tickets
    open_tickets_query = text("""
        SELECT COUNT(*) as currently_open_tickets
        FROM (
            SELECT 
                event_metadata->>'ticket_id' as ticket_id,
                SUM(CASE WHEN event_type = 'support_ticket_created' THEN 1 ELSE 0 END) as created,
                SUM(CASE WHEN event_type = 'support_ticket_resolved' THEN 1 ELSE 0 END) as resolved
            FROM events 
            WHERE event_type IN ('support_ticket_created', 'support_ticket_resolved')
              AND ts >= :period_start 
              AND ts <= :period_end
              AND customer_id = :customer_id
            GROUP BY event_metadata->>'ticket_id'
        ) ticket_status
        WHERE created > resolved
    """)
    
    open_result = db.execute(open_tickets_query, {
        'period_start': period_start,
        'period_end': period_end,
        'customer_id': customer_id
    }).fetchone()
    
    currently_open_tickets = open_result[0] if open_result[0] else 0
    
    # Calculate component scores (convert to float)
    volume_score = max(0, 100.0 - (float(tickets_created) * 5))  # -5 points per ticket
    resolution_rate_score = float((tickets_resolved / tickets_created * 100)) if tickets_created > 0 else 100.0
    escalation_penalty = max(0, 100.0 - (float(tickets_escalated) * 20))  # -20 points per escalation
    priority_penalty = max(0, 100.0 - (float(high_priority_tickets) * 15))  # -15 points per high priority
    open_ticket_penalty = max(0, 100.0 - (float(currently_open_tickets) * 10))  # -10 points per open ticket
    satisfaction_score = float(avg_satisfaction * 20) if avg_satisfaction else 80.0  # Convert 1-5 scale to 0-100
    
    # Weighted combination
    support_score = (
        (volume_score * 0.3) + 
        (resolution_rate_score * 0.2) + 
        (escalation_penalty * 0.2) + 
        (priority_penalty * 0.15) + 
        (open_ticket_penalty * 0.1) + 
        (satisfaction_score * 0.05)
    )
    
    return {
        'score': round(support_score, 1),
        'tickets_created': tickets_created,
        'tickets_resolved': tickets_resolved,
        'tickets_escalated': tickets_escalated,
        'high_priority_tickets': high_priority_tickets,
        'currently_open_tickets': currently_open_tickets,
        'avg_satisfaction': round(avg_satisfaction, 1) if avg_satisfaction else None,
        'resolution_rate': round((tickets_resolved / tickets_created * 100), 1) if tickets_created > 0 else 100
    }


# 4. PAYMENT TIMELINESS SCORE
def calc_payment_timeliness_score(db: Session, customer_id: str, period_start: datetime, period_end: datetime) -> Dict[str, Any]:
    """Calculate payment health considering overdue invoices, payment delays, and failed payments."""
    # Get payment metrics
    payment_metrics_query = text("""
        WITH payment_metrics AS (
            SELECT 
                inv.invoice_id,
                inv.amount_usd,
                inv.due_date,
                pay.payment_date,
                pay.days_early_late,
                CASE 
                    WHEN pay.payment_date IS NULL THEN 'unpaid'
                    WHEN pay.days_early_late <= 0 THEN 'on_time_or_early'
                    WHEN pay.days_early_late BETWEEN 1 AND 10 THEN 'late_acceptable'
                    WHEN pay.days_early_late > 10 THEN 'late_concerning'
                END as payment_status,
                COALESCE(fail.failure_count, 0) as failure_count
            FROM (
                SELECT 
                    event_metadata->>'invoice_id' as invoice_id,
                    (event_metadata->>'amount_usd')::float as amount_usd,
                    (event_metadata->>'due_date')::date as due_date,
                    ts
                FROM events 
                WHERE event_type = 'invoice_generated'
                  AND ts >= :period_start 
                  AND ts <= :period_end
                  AND customer_id = :customer_id
            ) inv
            LEFT JOIN (
                SELECT 
                    event_metadata->>'invoice_id' as invoice_id,
                    (event_metadata->>'payment_date')::date as payment_date,
                    (event_metadata->>'days_early_late')::int as days_early_late
                FROM events 
                WHERE event_type = 'payment_received'
                  AND customer_id = :customer_id
            ) pay ON inv.invoice_id = pay.invoice_id
            LEFT JOIN (
                SELECT 
                    event_metadata->>'invoice_id' as invoice_id,
                    COUNT(*) as failure_count
                FROM events 
                WHERE event_type = 'payment_failed'
                  AND customer_id = :customer_id
                GROUP BY event_metadata->>'invoice_id'
            ) fail ON inv.invoice_id = fail.invoice_id
        )
        SELECT 
            COUNT(*) as total_invoices,
            COUNT(CASE WHEN payment_status = 'unpaid' THEN 1 END) as unpaid_invoices,
            COUNT(CASE WHEN payment_status = 'on_time_or_early' THEN 1 END) as on_time_payments,
            COUNT(CASE WHEN payment_status = 'late_acceptable' THEN 1 END) as late_acceptable,
            COUNT(CASE WHEN payment_status = 'late_concerning' THEN 1 END) as late_concerning,
            SUM(failure_count) as total_payment_failures,
            AVG(CASE WHEN days_early_late IS NOT NULL THEN days_early_late END) as avg_payment_delay,
            SUM(CASE WHEN payment_status = 'unpaid' THEN amount_usd ELSE 0 END) as unpaid_amount
        FROM payment_metrics
    """)
    
    result = db.execute(payment_metrics_query, {
        'period_start': period_start,
        'period_end': period_end,
        'customer_id': customer_id
    }).fetchone()
    
    total_invoices = result[0] if result[0] else 0
    unpaid_invoices = result[1] if result[1] else 0
    on_time_payments = result[2] if result[2] else 0
    late_acceptable = result[3] if result[3] else 0
    late_concerning = result[4] if result[4] else 0
    total_payment_failures = result[5] if result[5] else 0
    avg_payment_delay = result[6] if result[6] else 0
    unpaid_amount = result[7] if result[7] else 0
    
    # Calculate component scores (convert Decimal to float)
    on_time_rate_score = float((on_time_payments / total_invoices * 100)) if total_invoices > 0 else 100.0
    unpaid_penalty = max(0, 100.0 - (float(unpaid_invoices) * 25))  # -25 points per unpaid
    late_penalty = max(0, 100.0 - (float(late_concerning) * 15))  # -15 points per concerning late
    failure_penalty = max(0, 100.0 - (float(total_payment_failures) * 10))  # -10 points per failure
    delay_penalty = max(0, 100.0 - (float(avg_payment_delay) * 2))  # -2 points per avg day late
    
    # Weighted payment score
    payment_score = (
        (on_time_rate_score * 0.4) + 
        (unpaid_penalty * 0.3) + 
        (late_penalty * 0.15) + 
        (failure_penalty * 0.1) + 
        (delay_penalty * 0.05)
    )
    
    return {
        'score': round(payment_score, 1),
        'total_invoices': total_invoices,
        'unpaid_invoices': unpaid_invoices,
        'on_time_payments': on_time_payments,
        'late_concerning': late_concerning,
        'total_payment_failures': total_payment_failures,
        'avg_payment_delay': round(avg_payment_delay, 1),
        'unpaid_amount': unpaid_amount,
        'on_time_rate': round((on_time_payments / total_invoices * 100), 1) if total_invoices > 0 else 100
    }


# 5. API USAGE SCORE
def calc_api_usage_score(db: Session, customer_id: str, period_start: datetime, period_end: datetime) -> Dict[str, Any]:
    """Calculate API usage health considering call volume, growth trends, and rate limit issues."""
    # Get API metrics
    api_metrics_query = text("""
        SELECT 
            COUNT(CASE WHEN event_type = 'api_call' THEN 1 END) as total_api_calls,
            COUNT(CASE WHEN event_type = 'api_rate_limit_exceeded' THEN 1 END) as rate_limit_hits,
            COUNT(DISTINCT DATE(ts)) as active_api_days,
            COUNT(CASE 
                WHEN event_type = 'api_call' 
                  AND (event_metadata->>'response_code')::int BETWEEN 200 AND 299 
                THEN 1 
            END)::float / NULLIF(COUNT(CASE WHEN event_type = 'api_call' THEN 1 END), 0) * 100 as success_rate,
            AVG(CASE 
                WHEN event_type = 'api_call' 
                THEN (event_metadata->>'response_time_ms')::int 
            END) as avg_response_time,
            COUNT(DISTINCT CASE 
                WHEN event_type = 'api_call' 
                THEN event_metadata->>'endpoint' 
            END) as unique_endpoints_used
        FROM events 
        WHERE event_type IN ('api_call', 'api_rate_limit_exceeded')
          AND ts >= :period_start 
          AND ts <= :period_end
          AND customer_id = :customer_id
    """)
    
    result = db.execute(api_metrics_query, {
        'period_start': period_start,
        'period_end': period_end,
        'customer_id': customer_id
    }).fetchone()
    
    total_api_calls = result[0] if result[0] else 0
    rate_limit_hits = result[1] if result[1] else 0
    active_api_days = result[2] if result[2] else 0
    success_rate = result[3] if result[3] else 90
    avg_response_time = result[4] if result[4] else 0
    unique_endpoints_used = result[5] if result[5] else 0
    
    # Calculate growth vs previous period
    previous_period_start = period_start - (period_end - period_start)
    growth_query = text("""
        SELECT COUNT(*) as previous_period_calls
        FROM events 
        WHERE event_type = 'api_call'
          AND ts >= :previous_period_start 
          AND ts < :period_start
          AND customer_id = :customer_id
    """)
    
    growth_result = db.execute(growth_query, {
        'previous_period_start': previous_period_start,
        'period_start': period_start,
        'customer_id': customer_id
    }).fetchone()
    
    previous_period_calls = growth_result[0] if growth_result[0] else 0
    
    # Calculate component scores
    period_days = (period_end.date() - period_start.date()).days + 1
    
    volume_score = min(100, (total_api_calls ** 0.5) * 10) if total_api_calls > 0 else 0  # Logarithmic scaling
    consistency_score = min(100, (active_api_days / period_days) * 100) if period_days > 0 else 0
    growth_score = 50 if previous_period_calls == 0 else min(100, ((total_api_calls / previous_period_calls - 1) * 100) + 50)
    reliability_score = success_rate
    diversity_score = min(100, unique_endpoints_used * 20)  # +20 points per unique endpoint
    engagement_bonus = min(20, rate_limit_hits * 2)  # +2 points per rate limit hit, max 20
    
    # Weighted API usage score
    api_usage_score = (
        (volume_score * 0.25) + 
        (consistency_score * 0.20) + 
        (growth_score * 0.20) + 
        (reliability_score * 0.15) + 
        (diversity_score * 0.10) + 
        (engagement_bonus * 0.10)
    )
    
    return {
        'score': round(api_usage_score, 1),
        'total_api_calls': total_api_calls,
        'rate_limit_hits': rate_limit_hits,
        'active_api_days': active_api_days,
        'success_rate': round(success_rate, 1),
        'avg_response_time': round(avg_response_time, 1),
        'unique_endpoints_used': unique_endpoints_used,
        'growth_rate': round(((total_api_calls / previous_period_calls - 1) * 100), 1) if previous_period_calls > 0 else 100
    }


# MAIN HEALTH SCORE CALCULATION
def calculate_customer_health_score(db: Session, customer: Customer) -> Dict[str, Any]:
    """
    Calculate comprehensive health score for a customer using all 5 factors.
    
    Args:
        db: Database session
        customer: Customer model instance
        
    Returns:
        Dict containing score breakdown and final score
    """
    # Get 30-day period
    period_start, period_end = get_period_dates(30)
    
    # Calculate all health factors
    login_data = calc_login_frequency_score(db, customer.id, period_start, period_end)
    feature_data = calc_feature_adoption_score(db, customer.id, period_start, period_end)
    support_data = calc_support_ticket_score(db, customer.id, period_start, period_end)
    payment_data = calc_payment_timeliness_score(db, customer.id, period_start, period_end)
    api_data = calc_api_usage_score(db, customer.id, period_start, period_end)
    
    # Configurable weights via environment variables
    weights = {
        'login_frequency': float(os.getenv('WEIGHT_LOGIN_FREQUENCY', '0.20')),
        'feature_adoption': float(os.getenv('WEIGHT_FEATURE_ADOPTION', '0.25')),
        'support_tickets': float(os.getenv('WEIGHT_SUPPORT_TICKETS', '0.20')),
        'payment_health': float(os.getenv('WEIGHT_PAYMENT_HEALTH', '0.20')),
        'api_usage': float(os.getenv('WEIGHT_API_USAGE', '0.15'))
    }
    
    # Calculate weighted total
    weighted_score = (
        login_data['score'] * weights['login_frequency'] +
        feature_data['score'] * weights['feature_adoption'] +
        support_data['score'] * weights['support_tickets'] +
        payment_data['score'] * weights['payment_health'] +
        api_data['score'] * weights['api_usage']
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
                'score': login_data['score'],
                'weight': weights['login_frequency'],
                'days_logged_in': login_data['days_logged_in'],
                'total_days_in_period': login_data['total_days_in_period'],
                'login_frequency_percentage': login_data['login_frequency_percentage']
            },
            'feature_adoption': {
                'score': feature_data['score'],
                'weight': weights['feature_adoption'],
                'features_onboarded': feature_data['features_onboarded'],
                'features_used': feature_data['features_used'],
                'total_feature_usage': feature_data['total_feature_usage']
            },
            'support_tickets': {
                'score': support_data['score'],
                'weight': weights['support_tickets'],
                'tickets_created': support_data['tickets_created'],
                'tickets_resolved': support_data['tickets_resolved'],
                'currently_open_tickets': support_data['currently_open_tickets'],
                'resolution_rate': support_data['resolution_rate']
            },
            'payment_health': {
                'score': payment_data['score'],
                'weight': weights['payment_health'],
                'total_invoices': payment_data['total_invoices'],
                'unpaid_invoices': payment_data['unpaid_invoices'],
                'on_time_rate': payment_data['on_time_rate'],
                'unpaid_amount': payment_data['unpaid_amount']
            },
            'api_usage': {
                'score': api_data['score'],
                'weight': weights['api_usage'],
                'total_api_calls': api_data['total_api_calls'],
                'active_api_days': api_data['active_api_days'],
                'success_rate': api_data['success_rate'],
                'unique_endpoints_used': api_data['unique_endpoints_used']
            }
        },
        'last_updated': datetime.now().isoformat()
    }
