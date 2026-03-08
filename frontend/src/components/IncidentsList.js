import React, { useState } from 'react';
import { AlertTriangle, Shield, Clock, ChevronDown, ChevronUp, CheckCircle, XCircle, Zap, Network, HardDrive, Lock } from 'lucide-react';
import ApiService from '../services/api';

function IncidentsList({ incidents, compact, onRefresh }) {
  const [expandedIncident, setExpandedIncident] = useState(null);
  const [containingIncident, setContainingIncident] = useState(null);

  const handleContainment = async (incidentId) => {
    setContainingIncident(incidentId);
    try {
      await ApiService.triggerContainment(incidentId);
      alert('Containment actions executed successfully');
      if (onRefresh) onRefresh();
    } catch (error) {
      alert('Failed to execute containment: ' + error.message);
    }
    setContainingIncident(null);
  };

  const getSeverityColor = (severity) => {
    const colors = {
      critical: 'text-danger-600 bg-danger-50 border-danger-200',
      high: 'text-warning-600 bg-warning-50 border-warning-200',
      medium: 'text-yellow-600 bg-yellow-50 border-yellow-200',
      low: 'text-blue-600 bg-blue-50 border-blue-200',
    };
    return colors[severity] || colors.low;
  };

  if (!incidents || incidents.length === 0) {
    return (
      <div className="card text-center py-12">
        <Shield className="h-16 w-16 mx-auto text-success-500 mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">No Incidents Detected</h3>
        <p className="text-gray-600">Your system is secure. No ransomware threats detected.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {incidents.map((incident) => (
        <div
          key={incident.id}
          className={`card border-l-4 ${getSeverityColor(incident.severity)} hover:shadow-lg transition-shadow`}
        >
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <div className="flex items-center space-x-3">
                <AlertTriangle className={`h-5 w-5 ${incident.severity === 'critical' ? 'text-danger-600' : 'text-warning-600'}`} />
                <div>
                  <h4 className="text-lg font-semibold text-gray-900">
                    Incident #{incident.id.substring(0, 8)}
                  </h4>
                  <div className="flex items-center space-x-4 mt-1">
                    <span className="text-sm text-gray-600 flex items-center">
                      <Clock className="h-4 w-4 mr-1" />
                      {new Date(incident.start_time).toLocaleString()}
                    </span>
                    <span className={`badge badge-${incident.severity}`}>
                      {incident.severity?.toUpperCase()}
                    </span>
                    <span className="badge bg-gray-100 text-gray-700">
                      {incident.status}
                    </span>
                    {incident.is_contained ? (
                      <span className="badge bg-success-100 text-success-700 flex items-center space-x-1">
                        <Shield className="h-3 w-3" />
                        <span>Contained</span>
                      </span>
                    ) : (
                      <span className="badge bg-warning-100 text-warning-700 flex items-center space-x-1">
                        <AlertTriangle className="h-3 w-3" />
                        <span>Not Contained</span>
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {!compact && (
                <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Process:</span>
                    <span className="ml-2 font-medium text-gray-900">{incident.process_name || 'Unknown'}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Affected Files:</span>
                    <span className="ml-2 font-medium text-gray-900">{incident.affected_files || 0}</span>
                  </div>
                </div>
              )}
            </div>

            <div className="flex items-center space-x-2">
              {incident.status === 'active' && (
                <button
                  onClick={() => handleContainment(incident.id)}
                  disabled={containingIncident === incident.id}
                  className="btn-danger text-sm"
                >
                  {containingIncident === incident.id ? 'Containing...' : 'Contain'}
                </button>
              )}
              {!compact && (
                <button
                  onClick={() => setExpandedIncident(expandedIncident === incident.id ? null : incident.id)}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  {expandedIncident === incident.id ? (
                    <ChevronUp className="h-5 w-5 text-gray-600" />
                  ) : (
                    <ChevronDown className="h-5 w-5 text-gray-600" />
                  )}
                </button>
              )}
            </div>
          </div>

          {expandedIncident === incident.id && (
            <div className="mt-4 pt-4 border-t border-gray-200 space-y-4">
              <div>
                <h5 className="font-semibold text-gray-900 mb-2">Incident Details</h5>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600 block">Incident ID:</span>
                    <span className="font-mono text-xs text-gray-900">{incident.id}</span>
                  </div>
                  <div>
                    <span className="text-gray-600 block">Status:</span>
                    <span className="font-medium text-gray-900">{incident.status}</span>
                  </div>
                  <div>
                    <span className="text-gray-600 block">Severity:</span>
                    <span className={`badge badge-${incident.severity}`}>{incident.severity}</span>
                  </div>
                  <div>
                    <span className="text-gray-600 block">Process Name:</span>
                    <span className="font-medium text-gray-900">{incident.process_name || 'N/A'}</span>
                  </div>
                </div>
              </div>

              {/* Containment Actions Section */}
              {incident.containment_actions && incident.containment_actions.length > 0 && (
                <div>
                  <h5 className="font-semibold text-gray-900 mb-3 flex items-center">
                    <Shield className="h-5 w-5 mr-2 text-primary-600" />
                    Containment Actions ({incident.successful_actions_count}/{incident.containment_actions_count} Successful)
                  </h5>
                  <div className="space-y-2">
                    {incident.containment_actions.map((action, idx) => {
                      const getActionIcon = (type) => {
                        if (type === 'process_kill') return <Zap className="h-4 w-4" />;
                        if (type === 'network_isolation') return <Network className="h-4 w-4" />;
                        if (type === 'disable_network_drives') return <HardDrive className="h-4 w-4" />;
                        if (type === 'lock_workstation') return <Lock className="h-4 w-4" />;
                        return <Shield className="h-4 w-4" />;
                      };

                      const getActionName = (type) => {
                        const names = {
                          'process_kill': 'Process Termination',
                          'network_isolation': 'Network Isolation',
                          'disable_network_drives': 'Network Drives Disconnection',
                          'lock_workstation': 'Workstation Lock'
                        };
                        return names[type] || type;
                      };

                      return (
                        <div
                          key={idx}
                          className={`flex items-center justify-between p-3 rounded-lg border ${
                            action.success
                              ? 'bg-success-50 border-success-200'
                              : 'bg-danger-50 border-danger-200'
                          }`}
                        >
                          <div className="flex items-center space-x-3">
                            <div className={`${action.success ? 'text-success-600' : 'text-danger-600'}`}>
                              {getActionIcon(action.action_type)}
                            </div>
                            <div>
                              <p className={`text-sm font-medium ${action.success ? 'text-success-900' : 'text-danger-900'}`}>
                                {getActionName(action.action_type)}
                              </p>
                              {action.target && (
                                <p className="text-xs text-gray-600 mt-0.5">
                                  Target: {action.target}
                                </p>
                              )}
                              <p className="text-xs text-gray-500 mt-0.5">
                                {action.auto_triggered ? 'Auto-triggered' : 'Manual'} • {new Date(action.timestamp).toLocaleTimeString()}
                              </p>
                            </div>
                          </div>
                          <div>
                            {action.success ? (
                              <CheckCircle className="h-5 w-5 text-success-600" />
                            ) : (
                              <XCircle className="h-5 w-5 text-danger-600" />
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* No Containment Message */}
              {(!incident.containment_actions || incident.containment_actions.length === 0) && (
                <div className="bg-warning-50 border border-warning-200 rounded-lg p-4">
                  <div className="flex items-start space-x-3">
                    <AlertTriangle className="h-5 w-5 text-warning-600 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-warning-900">No Containment Actions Executed</p>
                      <p className="text-xs text-warning-700 mt-1">
                        This incident has not been contained yet. Click the "Contain" button to execute containment actions.
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

export default IncidentsList;
