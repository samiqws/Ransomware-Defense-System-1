import React, { useState } from 'react';
import { FileText, Clock, AlertTriangle, Trash2, AlertOctagon } from 'lucide-react';
import ApiService from '../services/api';

function EventsList({ events, onRefresh }) {
  const [deletingEvent, setDeletingEvent] = useState(null);

  const handleDeleteEvent = async (eventId, event) => {
    event.stopPropagation();
    
    if (!window.confirm('Are you sure you want to delete this event?')) {
      return;
    }

    setDeletingEvent(eventId);
    try {
      await ApiService.deleteEvent(eventId);
      if (onRefresh) onRefresh();
    } catch (error) {
      console.error('Failed to delete event:', error);
      alert('Failed to delete event: ' + error.message);
    } finally {
      setDeletingEvent(null);
    }
  };

  const handleDeleteAll = async () => {
    if (!window.confirm('⚠️ WARNING: This will delete ALL events!\n\nAre you sure?')) {
      return;
    }

    try {
      const result = await ApiService.deleteAllEvents();
      alert(result.message);
      if (onRefresh) onRefresh();
    } catch (error) {
      console.error('Failed to delete all events:', error);
      alert('Failed to delete all events: ' + error.message);
    }
  };
  const getThreatBadge = (threatLevel) => {
    if (!threatLevel || threatLevel === 'none') return null;
    return (
      <span className={`badge badge-${threatLevel}`}>
        {threatLevel}
      </span>
    );
  };

  const getEventIcon = (eventType, suspicious) => {
    if (suspicious) {
      return <AlertTriangle className="h-4 w-4 text-danger-500" />;
    }
    return <FileText className="h-4 w-4 text-gray-400" />;
  };

  if (!events || events.length === 0) {
    return (
      <div className="card text-center py-12">
        <FileText className="h-16 w-16 mx-auto text-gray-300 mb-4" />
        <p className="text-gray-600">No events recorded yet</p>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
          <FileText className="h-5 w-5 text-primary-600" />
          <span>File System Events ({events.length})</span>
        </h3>
        {events.length > 0 && (
          <button
            onClick={handleDeleteAll}
            className="btn-danger text-sm flex items-center space-x-2"
          >
            <AlertOctagon className="h-4 w-4" />
            <span>Delete All Events</span>
          </button>
        )}
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Time
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Event Type
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                File Path
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Threat Level
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {events.map((event) => (
              <tr
                key={event.id}
                className={`hover:bg-gray-50 ${event.suspicious ? 'bg-danger-50' : ''}`}
              >
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  <div className="flex items-center">
                    <Clock className="h-4 w-4 mr-2 text-gray-400" />
                    {new Date(event.timestamp).toLocaleString()}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center space-x-2">
                    {getEventIcon(event.type, event.suspicious)}
                    <span className="text-sm font-medium text-gray-900">{event.type}</span>
                  </div>
                </td>
                <td className="px-6 py-4 text-sm text-gray-900 max-w-md truncate" title={event.path}>
                  {event.path}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {getThreatBadge(event.threat_level)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {event.suspicious ? (
                    <span className="badge badge-critical">Suspicious</span>
                  ) : (
                    <span className="badge badge-success">Normal</span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <button
                    onClick={(e) => handleDeleteEvent(event.id, e)}
                    disabled={deletingEvent === event.id}
                    className="text-danger-600 hover:text-danger-900 flex items-center space-x-1"
                    title="Delete this event"
                  >
                    <Trash2 className="h-4 w-4" />
                    <span>{deletingEvent === event.id ? 'Deleting...' : 'Delete'}</span>
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default EventsList;
