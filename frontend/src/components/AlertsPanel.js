import React, { useState } from 'react';
import { AlertTriangle, Bell, X, Trash2, AlertOctagon, Check } from 'lucide-react';
import ApiService from '../services/api';

function AlertsPanel({ alerts, onRefresh }) {
  const [deletingAlert, setDeletingAlert] = useState(null);
  const [acknowledgingAlert, setAcknowledgingAlert] = useState(null);

  const handleDeleteAlert = async (alertId, event) => {
    event.stopPropagation();
    
    if (!window.confirm('Are you sure you want to delete this alert?')) {
      return;
    }

    setDeletingAlert(alertId);
    try {
      await ApiService.deleteAlert(alertId);
      if (onRefresh) onRefresh();
    } catch (error) {
      console.error('Failed to delete alert:', error);
      alert('Failed to delete alert: ' + error.message);
    } finally {
      setDeletingAlert(null);
    }
  };

  const handleAcknowledgeAlert = async (alertId, event) => {
    event.stopPropagation();
    
    setAcknowledgingAlert(alertId);
    try {
      await ApiService.acknowledgeAlert(alertId);
      if (onRefresh) onRefresh();
    } catch (error) {
      console.error('Failed to acknowledge alert:', error);
      alert('Failed to acknowledge alert: ' + error.message);
    } finally {
      setAcknowledgingAlert(null);
    }
  };

  const handleDeleteAll = async () => {
    if (!window.confirm('⚠️ WARNING: This will delete ALL alerts!\n\nAre you sure?')) {
      return;
    }

    try {
      const result = await ApiService.deleteAllAlerts();
      alert(result.message);
      if (onRefresh) onRefresh();
    } catch (error) {
      console.error('Failed to delete all alerts:', error);
      alert('Failed to delete all alerts: ' + error.message);
    }
  };
  const getSeverityColor = (severity) => {
    const colors = {
      critical: 'bg-danger-50 border-danger-200 text-danger-900',
      high: 'bg-warning-50 border-warning-200 text-warning-900',
      medium: 'bg-yellow-50 border-yellow-200 text-yellow-900',
      low: 'bg-blue-50 border-blue-200 text-blue-900',
    };
    return colors[severity] || colors.low;
  };

  const getSeverityIcon = (severity) => {
    if (severity === 'critical' || severity === 'high') {
      return <AlertTriangle className="h-5 w-5" />;
    }
    return <Bell className="h-5 w-5" />;
  };

  if (!alerts || alerts.length === 0) {
    return (
      <div className="card text-center py-8">
        <Bell className="h-12 w-12 mx-auto text-gray-300 mb-3" />
        <p className="text-gray-600">No alerts</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
          <Bell className="h-5 w-5 text-primary-600" />
          <span>Recent Alerts ({alerts.length})</span>
        </h3>
        {alerts.length > 0 && (
          <button
            onClick={handleDeleteAll}
            className="btn-danger text-sm flex items-center space-x-2"
          >
            <AlertOctagon className="h-4 w-4" />
            <span>Delete All</span>
          </button>
        )}
      </div>

      <div className="space-y-3">
        {alerts.map((alert) => (
          <div
            key={alert.id}
            className={`p-4 rounded-lg border-l-4 ${getSeverityColor(alert.severity)} shadow-sm`}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-3 flex-1">
                <div className="mt-0.5">
                  {getSeverityIcon(alert.severity)}
                </div>
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <h4 className="font-semibold">{alert.type.replace(/_/g, ' ').toUpperCase()}</h4>
                    <span className={`badge badge-${alert.severity}`}>
                      {alert.severity}
                    </span>
                    {alert.acknowledged && (
                      <span className="badge bg-gray-100 text-gray-600 flex items-center space-x-1">
                        <Check className="h-3 w-3" />
                        <span>Acknowledged</span>
                      </span>
                    )}
                  </div>
                  <p className="text-sm mt-1">{alert.message}</p>
                  <p className="text-xs mt-2 opacity-75">
                    {new Date(alert.timestamp).toLocaleString()}
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-2 ml-3">
                {!alert.acknowledged && (
                  <button
                    onClick={(e) => handleAcknowledgeAlert(alert.id, e)}
                    disabled={acknowledgingAlert === alert.id}
                    className="p-1 hover:bg-success-100 text-success-600 rounded transition-colors"
                    title="Acknowledge alert"
                  >
                    <Check className="h-4 w-4" />
                  </button>
                )}
                <button
                  onClick={(e) => handleDeleteAlert(alert.id, e)}
                  disabled={deletingAlert === alert.id}
                  className="p-1 hover:bg-danger-100 text-danger-600 rounded transition-colors"
                  title="Delete alert"
                >
                  {deletingAlert === alert.id ? (
                    <X className="h-4 w-4 animate-spin" />
                  ) : (
                    <Trash2 className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default AlertsPanel;
