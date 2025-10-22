import React, { useState, useEffect } from 'react';
import { getApplications, deleteApplication } from '../services/api';
import ApplicationForm from './ApplicationForm';
import CalendarView from './Calendar';

function Dashboard({ onLogout }) {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCalendar, setShowCalendar] = useState(false);
  const [editingApplication, setEditingApplication] = useState(null);

  const fetchApplications = async () => {
    try {
      const response = await getApplications();
      setApplications(response.data);
      setError('');
    } catch (err) {
      setError('Failed to load applications');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApplications();
  }, []);

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this application?')) {
      try {
        await deleteApplication(id);
        fetchApplications();
      } catch (err) {
        setError('Failed to delete application');
      }
    }
  };

  const handleEdit = (app) => {
    setEditingApplication(app);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleCancelEdit = () => {
    setEditingApplication(null);
  };

  const handleApplicationCreated = () => {
    fetchApplications();
    setEditingApplication(null);
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  // If calendar view is active, show calendar
  if (showCalendar) {
    return <CalendarView onBack={() => setShowCalendar(false)} />;
  }

  // Otherwise show dashboard
  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>📋 Job Application Tracker</h1>
        <div className="header-buttons">
          <button 
            className="calendar-btn" 
            onClick={() => setShowCalendar(true)}
          >
            📅 Calendar View
          </button>
          <button className="logout-btn" onClick={onLogout}>
            Logout
          </button>
        </div>
      </div>

      <ApplicationForm 
        onApplicationCreated={handleApplicationCreated} 
        editingApplication={editingApplication}
        onCancelEdit={handleCancelEdit}
      />

      <div className="applications-section">
        <h2>My Applications ({applications.length})</h2>
        {loading && <p>Loading applications...</p>}
        {error && <div className="error-message">{error}</div>}
        
        {!loading && applications.length === 0 && (
          <p className="no-applications">
            No applications yet. Add your first one above!
          </p>
        )}

        <div className="applications-grid">
          {applications.map((app) => (
            <div key={app.id} className="application-card">
              <div className="card-header">
                <h3>{app.company}</h3>
                <div className="card-actions">
                  <button
                    className="edit-btn"
                    onClick={() => handleEdit(app)}
                    title="Edit application"
                  >
                    ✏️
                  </button>
                  <button
                    className="delete-btn"
                    onClick={() => handleDelete(app.id)}
                    title="Delete application"
                  >
                    🗑️
                  </button>
                </div>
              </div>
              <p className="app-date">
                <strong>Applied:</strong> {formatDate(app.application_date)}
              </p>
              <p className="app-status">
                <strong>Status:</strong> 
                <span className={`status-badge status-${app.status}`}>
                  {app.status === 'pending' && '⏳'}
                  {app.status === 'interview' && '📞'}
                  {app.status === 'accepted' && '✅'}
                  {app.status === 'rejected' && '❌'}
                  {' '}{app.status}
                </span>
              </p>
              {app.interview_date && (
                <p className="app-date">
                  <strong>Interview:</strong> {formatDate(app.interview_date)}
                </p>
              )}
              {app.accepted_date && (
                <p className="app-date">
                  <strong>Accepted:</strong> {formatDate(app.accepted_date)}
                </p>
              )}
              {app.rejected_date && (
                <p className="app-date">
                  <strong>Rejected:</strong> {formatDate(app.rejected_date)}
                </p>
              )}
              {app.cover_letter && (
                <div className="cover-letter">
                  <strong>Cover Letter:</strong>
                  <p>{app.cover_letter}</p>
                </div>
              )}
              {app.cv_filename && (
                <p className="cv-file">
                  <strong>CV:</strong> 📄 {app.cv_filename}
                </p>
              )}
              <p className="created-at">
                <small>Created: {formatDate(app.created_at)}</small>
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;