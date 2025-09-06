import React, { useState, useEffect } from 'react';

const CustomerDetail = ({ customer, onBack }) => {
  const [healthData, setHealthData] = useState(null);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchCustomerDetails();
  }, [customer.id]);

  const fetchCustomerDetails = async () => {
    try {
      setLoading(true);
      
      // Fetch health details and events in parallel
      const [healthResponse, eventsResponse] = await Promise.all([
        fetch(`/api/customers/${customer.id}/health`),
        fetch(`/api/customers/${customer.id}/events`)
      ]);

      if (!healthResponse.ok || !eventsResponse.ok) {
        throw new Error('Failed to fetch customer details');
      }

      const health = await healthResponse.json();
      const eventsData = await eventsResponse.json();

      setHealthData(health);
      setEvents(eventsData.events.slice(0, 10)); // Show last 10 events
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const getHealthLabel = (score) => {
    if (score >= 80) return 'Excellent';
    if (score >= 60) return 'Good';
    if (score >= 40) return 'Fair';
    return 'Poor';
  };

  const getHealthBadgeClass = (score) => {
    if (score >= 80) return 'excellent';
    if (score >= 60) return 'good';
    if (score >= 40) return 'fair';
    return 'poor';
  };

  if (loading) {
    return (
      <div className="customer-detail">
        <div className="detail-header">
          <button className="back-button" onClick={onBack}>
            ← Back to List
          </button>
          <h2>{customer.name}</h2>
        </div>
        <div className="detail-content">
          <div className="loading">Loading customer details...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="customer-detail">
        <div className="detail-header">
          <button className="back-button" onClick={onBack}>
            ← Back to List
          </button>
          <h2>{customer.name}</h2>
        </div>
        <div className="detail-content">
          <div className="error">Error: {error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="customer-detail">
      <div className="detail-header">
        <button className="back-button" onClick={onBack}>
          ← Back to List
        </button>
        <div>
          <h2>{healthData.name}</h2>
          <p style={{ margin: 0, opacity: 0.8 }}>ID: {healthData.id}</p>
        </div>
      </div>

      <div className="detail-content">
        {/* Health Overview */}
        <div className="detail-section">
          <h3>Health Overview</h3>
          <div className="health-overview">
            <div className="health-metric">
              <h4>Overall Score</h4>
              <div className="value">{healthData.score}</div>
            </div>
            <div className="health-metric">
              <h4>Status</h4>
              <div className="value">
                <span className={`health-badge ${getHealthBadgeClass(healthData.score)}`}>
                  {getHealthLabel(healthData.score)}
                </span>
              </div>
            </div>
            <div className="health-metric">
              <h4>Last Updated</h4>
              <div className="value" style={{ fontSize: '0.875rem' }}>
                {formatDate(healthData.last_updated)}
              </div>
            </div>
          </div>
        </div>

        {/* Health Breakdown */}
        <div className="detail-section">
          <h3>Health Factor Breakdown</h3>
          <div className="breakdown-grid">
            {Object.entries(healthData.breakdown).map(([factor, data]) => (
              <div key={factor} className="factor-card">
                <h4>{factor.replace('_', ' ').toUpperCase()}</h4>
                <div className="factor-score">{data.score}</div>
                <div className="factor-details">
                  <div>Weight: {(data.weight * 100).toFixed(0)}%</div>
                  {data.total_logins && (
                    <div>Total Logins: {data.total_logins}</div>
                  )}
                  {data.unique_features && (
                    <div>Features Used: {data.unique_features}</div>
                  )}
                  {data.total_opened && (
                    <div>Support Tickets: {data.total_opened} opened, {data.total_closed} closed</div>
                  )}
                  {data.note && (
                    <div style={{ fontStyle: 'italic' }}>{data.note}</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Events */}
        <div className="detail-section">
          <h3>Recent Events</h3>
          <div className="events-list">
            {events.length > 0 ? (
              events.map((event) => (
                <div key={event.id} className="event-item">
                  <div>
                    <div className="event-type">{event.event_type}</div>
                    {event.event_metadata && (
                      <div style={{ fontSize: '0.875rem', color: '#6c757d' }}>
                        {JSON.stringify(event.event_metadata, null, 2)}
                      </div>
                    )}
                  </div>
                  <div className="event-time">
                    {formatDate(event.ts)}
                  </div>
                </div>
              ))
            ) : (
              <div style={{ padding: '1rem', textAlign: 'center', color: '#6c757d' }}>
                No recent events found
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CustomerDetail;
