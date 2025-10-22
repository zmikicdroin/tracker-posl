import React, { useState, useEffect } from 'react';
import { Calendar, momentLocalizer } from 'react-big-calendar';
import moment from 'moment';
import 'react-big-calendar/lib/css/react-big-calendar.css';
import { getApplications } from '../services/api';

const localizer = momentLocalizer(moment);

function CalendarView({ onBack }) {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [date, setDate] = useState(new Date());
  const [view, setView] = useState('month');

  useEffect(() => {
    fetchApplications();
  }, []);

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

  // Transform applications into calendar events
  const events = applications.flatMap((app) => {
    const eventsList = [];
    
    // Application date event
    const appDate = new Date(app.application_date);
    eventsList.push({
      id: `app-${app.id}`,
      title: `${app.company} (Applied)`,
      start: appDate,
      end: appDate,
      allDay: true,
      resource: { ...app, eventType: 'application' },
    });

    // Interview date event
    if (app.interview_date && app.status === 'interview') {
      const intDate = new Date(app.interview_date);
      eventsList.push({
        id: `int-${app.id}`,
        title: `${app.company} (Interview)`,
        start: intDate,
        end: intDate,
        allDay: true,
        resource: { ...app, eventType: 'interview' },
      });
    }

    // Accepted date event
    if (app.accepted_date && app.status === 'accepted') {
      const accDate = new Date(app.accepted_date);
      eventsList.push({
        id: `acc-${app.id}`,
        title: `${app.company} (Accepted)`,
        start: accDate,
        end: accDate,
        allDay: true,
        resource: { ...app, eventType: 'accepted' },
      });
    }

    // Rejected date event
    if (app.rejected_date && app.status === 'rejected') {
      const rejDate = new Date(app.rejected_date);
      eventsList.push({
        id: `rej-${app.id}`,
        title: `${app.company} (Rejected)`,
        start: rejDate,
        end: rejDate,
        allDay: true,
        resource: { ...app, eventType: 'rejected' },
      });
    }

    return eventsList;
  });

  // Custom event styling based on status
  const eventStyleGetter = (event) => {
    let backgroundColor = '#667eea'; // default
    
    const eventType = event.resource.eventType;
    
    switch (eventType) {
      case 'application':
        backgroundColor = '#667eea'; // purple for application
        break;
      case 'pending':
      case 'interview':
        backgroundColor = '#ffc107'; // yellow/gold for interview
        break;
      case 'accepted':
        backgroundColor = '#28a745'; // green
        break;
      case 'rejected':
        backgroundColor = '#dc3545'; // red
        break;
      default:
        backgroundColor = '#667eea';
    }

    return {
      style: {
        backgroundColor,
        borderRadius: '5px',
        opacity: 0.9,
        color: 'white',
        border: '0px',
        display: 'block',
        fontWeight: 'bold',
      },
    };
  };

  // Custom event component
  const EventComponent = ({ event }) => (
    <div className="calendar-event">
      <strong>{event.title}</strong>
    </div>
  );

  // Handle navigation
  const handleNavigate = (newDate) => {
    setDate(newDate);
  };

  // Handle view change
  const handleViewChange = (newView) => {
    setView(newView);
  };

  return (
    <div className="calendar-container">
      <div className="calendar-header">
        <button className="back-btn" onClick={onBack}>
          ← Back to Dashboard
        </button>
        <h2>📅 Application Calendar</h2>
        <div className="calendar-legend">
          <span className="legend-item application">⬤ Applied</span>
          <span className="legend-item interview">⬤ Interview</span>
          <span className="legend-item accepted">⬤ Accepted</span>
          <span className="legend-item rejected">⬤ Rejected</span>
        </div>
      </div>

      {loading && <p className="loading">Loading calendar...</p>}
      {error && <div className="error-message">{error}</div>}

      {!loading && (
        <div className="calendar-wrapper">
          <Calendar
            localizer={localizer}
            events={events}
            startAccessor="start"
            endAccessor="end"
            style={{ height: 600 }}
            eventPropGetter={eventStyleGetter}
            components={{
              event: EventComponent,
            }}
            views={['month', 'week', 'day', 'agenda']}
            view={view}
            date={date}
            onNavigate={handleNavigate}
            onView={handleViewChange}
            defaultView="month"
            popup
            selectable
            onSelectEvent={(event) => {
              const app = event.resource;
              const eventType = app.eventType;
              let dateInfo = '';
              
              if (eventType === 'application') {
                dateInfo = `Applied: ${moment(app.application_date).format('MMMM D, YYYY')}`;
              } else if (eventType === 'interview') {
                dateInfo = `Interview: ${moment(app.interview_date).format('MMMM D, YYYY')}`;
              } else if (eventType === 'accepted') {
                dateInfo = `Accepted: ${moment(app.accepted_date).format('MMMM D, YYYY')}`;
              } else if (eventType === 'rejected') {
                dateInfo = `Rejected: ${moment(app.rejected_date).format('MMMM D, YYYY')}`;
              }

              alert(
                `Company: ${app.company}\n` +
                `${dateInfo}\n` +
                `Status: ${app.status}\n` +
                `${app.cover_letter ? '\n' + app.cover_letter.substring(0, 100) + '...' : ''}`
              );
            }}
            messages={{
              today: 'Today',
              previous: 'Back',
              next: 'Next',
              month: 'Month',
              week: 'Week',
              day: 'Day',
              agenda: 'Agenda',
              date: 'Date',
              time: 'Time',
              event: 'Event',
              showMore: (total) => `+${total} more`,
            }}
          />
        </div>
      )}

      <div className="calendar-stats">
        <div className="stat-card">
          <h3>{applications.length}</h3>
          <p>Total Applications</p>
        </div>
        <div className="stat-card">
          <h3>{applications.filter(a => a.status === 'pending').length}</h3>
          <p>Pending</p>
        </div>
        <div className="stat-card">
          <h3>{applications.filter(a => a.status === 'interview').length}</h3>
          <p>Interviews</p>
        </div>
        <div className="stat-card">
          <h3>{applications.filter(a => a.status === 'accepted').length}</h3>
          <p>Accepted</p>
        </div>
        <div className="stat-card">
          <h3>{applications.filter(a => a.status === 'rejected').length}</h3>
          <p>Rejected</p>
        </div>
      </div>
    </div>
  );
}

export default CalendarView;