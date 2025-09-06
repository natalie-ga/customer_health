import React, { useState, useEffect } from 'react';
import './App.css';
import CustomerTable from './components/CustomerTable';
import CustomerDetail from './components/CustomerDetail';

function App() {
  const [customers, setCustomers] = useState([]);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchCustomers();
  }, []);

  const fetchCustomers = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/customers');
      if (!response.ok) {
        throw new Error('Failed to fetch customers');
      }
      const data = await response.json();
      setCustomers(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCustomerSelect = (customer) => {
    setSelectedCustomer(customer);
  };

  const handleBackToList = () => {
    setSelectedCustomer(null);
  };

  if (loading) {
    return (
      <div className="app">
        <div className="loading">Loading customers...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="app">
        <div className="error">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Customer Health Dashboard</h1>
      </header>
      
      <main className="app-main">
        {!selectedCustomer ? (
          <CustomerTable 
            customers={customers} 
            onCustomerSelect={handleCustomerSelect}
          />
        ) : (
          <CustomerDetail 
            customer={selectedCustomer} 
            onBack={handleBackToList}
          />
        )}
      </main>
    </div>
  );
}

export default App;
