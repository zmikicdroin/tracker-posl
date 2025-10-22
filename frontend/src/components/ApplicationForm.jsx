import React, { useState, useEffect } from 'react';
import { createApplication, updateApplication } from '../services/api';

function ApplicationForm({ onApplicationCreated, editingApplication, onCancelEdit }) {
  const [company, setCompany] = useState('');
  const [applicationDate, setApplicationDate] = useState('');
  const [coverLetter, setCoverLetter] = useState('');
  const [cvFile, setCvFile] = useState(null);
  const [status, setStatus] = useState('pending');
  const [acceptedDate, setAcceptedDate] = useState('');
  const [rejectedDate, setRejectedDate] = useState('');
  const [interviewDate, setInterviewDate] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Populate form when editing
  useEffect(() => {
    if (editingApplication) {
      setCompany(editingApplication.company || '');
      setApplicationDate(editingApplication.application_date || '');
      setCoverLetter(editingApplication.cover_letter || '');
      setStatus(editingApplication.status || 'pending');
      setAcceptedDate(editingApplication.accepted_date || '');
      setRejectedDate(editingApplication.rejected_date || '');
      setInterviewDate(editingApplication.interview_date || '');
    } else {
      resetForm();
    }
  }, [editingApplication]);

  const resetForm = () => {
    setCompany('');
    setApplicationDate('');
    setCoverLetter('');
    setCvFile(null);
    setStatus('pending');
    setAcceptedDate('');
    setRejectedDate('');
    setInterviewDate('');
    setError('');
    if (document.getElementById('cv-input')) {
      document.getElementById('cv-input').value = '';
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file && file.type === 'application/pdf') {
      setCvFile(file);
      setError('');
    } else {
      setError('Please select a PDF file');
      e.target.value = '';
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const formData = new FormData();
    formData.append('company', company);
    formData.append('application_date', applicationDate);
    formData.append('cover_letter', coverLetter);
    formData.append('status', status);
    
    if (acceptedDate) formData.append('accepted_date', acceptedDate);
    if (rejectedDate) formData.append('rejected_date', rejectedDate);
    if (interviewDate) formData.append('interview_date', interviewDate);
    
    if (cvFile) {
      formData.append('cv', cvFile);
    }

    try {
      if (editingApplication) {
        await updateApplication(editingApplication.id, formData);
      } else {
        await createApplication(formData);
      }
      resetForm();
      onApplicationCreated();
      if (onCancelEdit) onCancelEdit();
    } catch (err) {
      setError(err.response?.data?.message || `Failed to ${editingApplication ? 'update' : 'create'} application`);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    resetForm();
    if (onCancelEdit) onCancelEdit();
  };

  return (
    <div className="application-form">
      <h2>{editingApplication ? '✏️ Edit Application' : '➕ Add New Application'}</h2>
      {error && <div className="error-message">{error}</div>}
      <form onSubmit={handleSubmit}>
        <div className="form-row">
          <div className="form-group">
            <label>Company Name *</label>
            <input
              type="text"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              required
              placeholder="e.g., Google, Microsoft, Amazon"
            />
          </div>
          <div className="form-group">
            <label>Application Date *</label>
            <input
              type="date"
              value={applicationDate}
              onChange={(e) => setApplicationDate(e.target.value)}
              required
              max="2099-12-31"
            />
          </div>
        </div>

        <div className="form-group">
          <label>Status</label>
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="pending">⏳ Pending</option>
            <option value="interview">📞 Interview</option>
            <option value="accepted">✅ Accepted</option>
            <option value="rejected">❌ Rejected</option>
          </select>
        </div>

        <div className="form-row">
          {status === 'interview' && (
            <div className="form-group">
              <label>Interview Date</label>
              <input
                type="date"
                value={interviewDate}
                onChange={(e) => setInterviewDate(e.target.value)}
              />
            </div>
          )}
          {status === 'accepted' && (
            <div className="form-group">
              <label>Accepted Date</label>
              <input
                type="date"
                value={acceptedDate}
                onChange={(e) => setAcceptedDate(e.target.value)}
              />
            </div>
          )}
          {status === 'rejected' && (
            <div className="form-group">
              <label>Rejected Date</label>
              <input
                type="date"
                value={rejectedDate}
                onChange={(e) => setRejectedDate(e.target.value)}
              />
            </div>
          )}
        </div>

        <div className="form-group">
          <label>Cover Letter</label>
          <textarea
            value={coverLetter}
            onChange={(e) => setCoverLetter(e.target.value)}
            placeholder="Write your cover letter here..."
            rows="6"
          />
        </div>

        <div className="form-group">
          <label>Upload CV (PDF only)</label>
          <input
            id="cv-input"
            type="file"
            accept="application/pdf"
            onChange={handleFileChange}
          />
          {cvFile && <small>Selected: {cvFile.name}</small>}
          {editingApplication && editingApplication.cv_filename && !cvFile && (
            <small>Current CV: {editingApplication.cv_filename}</small>
          )}
        </div>

        <div className="form-buttons">
          <button type="submit" disabled={loading}>
            {loading ? 'Submitting...' : (editingApplication ? 'Update Application' : 'Add Application')}
          </button>
          {editingApplication && (
            <button type="button" className="cancel-btn" onClick={handleCancel}>
              Cancel
            </button>
          )}
        </div>
      </form>
    </div>
  );
}

export default ApplicationForm;