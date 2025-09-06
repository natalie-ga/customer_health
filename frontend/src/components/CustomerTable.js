import React from 'react';

const CustomerTable = ({ customers, onCustomerSelect }) => {
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

  return (
    <div className="customer-table">
      <div className="table-header">
        <h2>Customer Health Overview</h2>
        <p>Click on a customer to view detailed health breakdown</p>
      </div>
      
      <table className="table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Health Score</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {customers.map((customer) => (
            <tr 
              key={customer.id} 
              onClick={() => onCustomerSelect(customer)}
            >
              <td>
                <strong>{customer.name}</strong>
                <br />
                <small style={{ color: '#6c757d' }}>ID: {customer.id}</small>
              </td>
              <td>
                <span style={{ fontSize: '1.25rem', fontWeight: '600' }}>
                  {customer.score}
                </span>
              </td>
              <td>
                <span className={`health-badge ${getHealthBadgeClass(customer.score)}`}>
                  {getHealthLabel(customer.score)}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default CustomerTable;
