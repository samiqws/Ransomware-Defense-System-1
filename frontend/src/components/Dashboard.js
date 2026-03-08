import React, { useState, useEffect } from 'react';
import { Shield, AlertTriangle, TrendingUp, Clock, Download, Filter, X, Database } from 'lucide-react';
import ApiService from '../services/api';
import IncidentsList from './IncidentsList';
import EventsList from './EventsList';
import DecoysList from './DecoysList';
import StatsCards from './StatsCards';
import ActivityChart from './ActivityChart';
import AlertsPanel from './AlertsPanel';

function Dashboard({ view, systemStatus, realTimeEvents }) {
  const [stats, setStats] = useState(null);
  const [incidents, setIncidents] = useState([]);
  const [events, setEvents] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [decoys, setDecoys] = useState(null);
  const [isExporting, setIsExporting] = useState(false);
  const [showEventFilters, setShowEventFilters] = useState(false);
  const [eventFilters, setEventFilters] = useState({
    type: 'all',
    suspicious: 'all',
    threatLevel: 'all'
  });
  const [isDeploying, setIsDeploying] = useState(false);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [statsData, incidentsData, eventsData, alertsData, decoysData] = await Promise.all([
        ApiService.getStatistics(),
        ApiService.getIncidents(50),
        ApiService.getEvents(100),
        ApiService.getAlerts(false),
        ApiService.getDecoys(),
      ]);

      setStats(statsData);
      setIncidents(incidentsData);
      setEvents(eventsData);
      setAlerts(alertsData);
      setDecoys(decoysData);
    } catch (error) {
      console.error('Failed to load data:', error);
    }
  };

  const handleExportReport = async () => {
    setIsExporting(true);
    try {
      const report = await ApiService.exportReport(7);

      // التحقق من صحة البيانات
      if (!report || typeof report !== 'object') {
        throw new Error('Invalid report data received');
      }

      // Create a blob from the JSON data
      const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });

      // Create a download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;

      // Generate filename with timestamp
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
      link.download = `ransomware-defense-report-${timestamp}.json`;

      // Trigger download
      document.body.appendChild(link);
      link.click();

      // Cleanup
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      // Show success message
      alert('Report exported successfully!');
    } catch (error) {
      console.error('Failed to export report:', error);
      // رسالة خطأ أكثر وضوحاً
      if (error.message.includes('NetworkError') || error.message.includes('fetch')) {
        alert('Failed to export report: Cannot connect to server. Please make sure the backend is running.');
      } else {
        alert('Failed to export report: ' + error.message);
      }
    } finally {
      setIsExporting(false);
    }
  };

  const getFilteredEvents = () => {
    if (!events || events.length === 0) return [];

    return events.filter(event => {
      // Filter by type
      if (eventFilters.type !== 'all' && event.type !== eventFilters.type) {
        return false;
      }

      // Filter by suspicious status
      if (eventFilters.suspicious === 'yes' && !event.suspicious) {
        return false;
      }
      if (eventFilters.suspicious === 'no' && event.suspicious) {
        return false;
      }

      // Filter by threat level
      if (eventFilters.threatLevel !== 'all' && event.threat_level !== eventFilters.threatLevel) {
        return false;
      }

      return true;
    });
  };

  const clearFilters = () => {
    setEventFilters({
      type: 'all',
      suspicious: 'all',
      threatLevel: 'all'
    });
  };

  const hasActiveFilters = () => {
    return eventFilters.type !== 'all' ||
      eventFilters.suspicious !== 'all' ||
      eventFilters.threatLevel !== 'all';
  };

  const handleDeployDecoys = async () => {
    const count = parseInt(prompt('How many decoy files to deploy? (1-100)', '10'));

    if (isNaN(count) || count < 1 || count > 100) {
      alert('Please enter a valid number between 1 and 100');
      return;
    }

    setIsDeploying(true);
    try {
      const result = await ApiService.deployDecoys(count);
      alert(`Success! Deployed ${result.deployed_count} decoy files.\nTotal decoys: ${result.total_decoys}`);
      await loadData(); // Refresh data
    } catch (error) {
      console.error('Failed to deploy decoys:', error);
      alert('Failed to deploy decoys: ' + error.message);
    } finally {
      setIsDeploying(false);
    }
  };

  if (view === 'incidents') {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-bold text-gray-900">Incident Management</h2>
          <button
            onClick={handleExportReport}
            disabled={isExporting}
            className="btn-secondary flex items-center space-x-2"
          >
            <Download className="h-4 w-4" />
            <span>{isExporting ? 'Exporting...' : 'Export Report'}</span>
          </button>
        </div>
        <IncidentsList incidents={incidents} onRefresh={loadData} />
      </div>
    );
  }

  if (view === 'events') {
    const filteredEvents = getFilteredEvents();

    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-bold text-gray-900">File System Events</h2>
          <div className="flex items-center space-x-2">
            {hasActiveFilters() && (
              <button
                onClick={clearFilters}
                className="btn-secondary flex items-center space-x-2"
              >
                <X className="h-4 w-4" />
                <span>Clear Filters</span>
              </button>
            )}
            <button
              onClick={() => setShowEventFilters(!showEventFilters)}
              className={`btn-secondary flex items-center space-x-2 ${hasActiveFilters() ? 'bg-primary-100 border-primary-300' : ''}`}
            >
              <Filter className="h-4 w-4" />
              <span>Filter Events</span>
              {hasActiveFilters() && (
                <span className="ml-1 px-2 py-0.5 bg-primary-600 text-white text-xs rounded-full">
                  {Object.values(eventFilters).filter(v => v !== 'all').length}
                </span>
              )}
            </button>
          </div>
        </div>

        {/* Filter Panel */}
        {showEventFilters && (
          <div className="card bg-gray-50 border-2 border-primary-200">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                <Filter className="h-5 w-5 mr-2 text-primary-600" />
                Filter Options
              </h3>
              <button
                onClick={() => setShowEventFilters(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Event Type Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Event Type
                </label>
                <select
                  value={eventFilters.type}
                  onChange={(e) => setEventFilters({ ...eventFilters, type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                >
                  <option value="all">All Types</option>
                  <option value="modified">Modified</option>
                  <option value="created">Created</option>
                  <option value="deleted">Deleted</option>
                  <option value="moved">Moved</option>
                </select>
              </div>

              {/* Suspicious Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Suspicious Activity
                </label>
                <select
                  value={eventFilters.suspicious}
                  onChange={(e) => setEventFilters({ ...eventFilters, suspicious: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                >
                  <option value="all">All Events</option>
                  <option value="yes">Suspicious Only</option>
                  <option value="no">Normal Only</option>
                </select>
              </div>

              {/* Threat Level Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Threat Level
                </label>
                <select
                  value={eventFilters.threatLevel}
                  onChange={(e) => setEventFilters({ ...eventFilters, threatLevel: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                >
                  <option value="all">All Levels</option>
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>
            </div>

            {/* Filter Summary */}
            <div className="mt-4 pt-4 border-t border-gray-200">
              <p className="text-sm text-gray-600">
                Showing <span className="font-semibold text-primary-600">{filteredEvents.length}</span> of <span className="font-semibold">{events.length}</span> events
                {hasActiveFilters() && (
                  <button
                    onClick={clearFilters}
                    className="ml-2 text-primary-600 hover:text-primary-700 underline"
                  >
                    Clear all filters
                  </button>
                )}
              </p>
            </div>
          </div>
        )}

        <EventsList events={filteredEvents} onRefresh={loadData} />
      </div>
    );
  }

  if (view === 'decoys') {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-bold text-gray-900">Decoy Files (Honeypots)</h2>
          <button
            onClick={handleDeployDecoys}
            disabled={isDeploying}
            className="btn-primary flex items-center space-x-2"
          >
            <Database className="h-4 w-4" />
            <span>{isDeploying ? 'Deploying...' : 'Deploy More Decoys'}</span>
          </button>
        </div>
        <DecoysList decoys={decoys} onRefresh={loadData} />
      </div>
    );
  }

  // Default: Dashboard view
  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <StatsCards stats={stats} systemStatus={systemStatus} />

      {/* Real-time Alerts */}
      {alerts && alerts.length > 0 && (
        <AlertsPanel alerts={alerts.slice(0, 5)} onRefresh={loadData} />
      )}

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Activity Chart */}
        <div className="lg:col-span-2">
          <ActivityChart events={events} />
        </div>

        {/* Recent Events */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Live Events</h3>
            <Clock className="h-5 w-5 text-gray-400" />
          </div>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {realTimeEvents.slice(0, 10).map((event, index) => (
              <div
                key={index}
                className="p-3 bg-gray-50 rounded-lg border border-gray-200 hover:bg-gray-100 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      {event.type === 'threat_detected' && (
                        <AlertTriangle className="h-4 w-4 text-danger-500" />
                      )}
                      <span className="text-sm font-medium text-gray-900">
                        {event.type === 'threat_detected' ? 'Threat Detected' : 'File Event'}
                      </span>
                    </div>
                    {event.data && (
                      <p className="text-xs text-gray-600 mt-1 truncate">
                        {event.data.path || event.data.message}
                      </p>
                    )}
                  </div>
                  {event.data?.threat_level && (
                    <span className={`badge badge-${event.data.threat_level}`}>
                      {event.data.threat_level}
                    </span>
                  )}
                </div>
              </div>
            ))}
            {realTimeEvents.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <Shield className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                <p className="text-sm">No events yet</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recent Incidents */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Recent Incidents</h3>
          <button
            onClick={() => window.location.hash = '#incidents'}
            className="text-sm text-primary-600 hover:text-primary-700 font-medium"
          >
            View All →
          </button>
        </div>
        <IncidentsList incidents={incidents.slice(0, 5)} compact onRefresh={loadData} />
      </div>

      {/* System Info */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <div className="flex items-center space-x-3 mb-4">
            <Shield className="h-6 w-6 text-primary-600" />
            <h3 className="text-lg font-semibold text-gray-900">Protection Status</h3>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Monitoring</span>
              <span className={`badge ${systemStatus?.monitoring ? 'badge-success' : 'bg-gray-200 text-gray-700'}`}>
                {systemStatus?.monitoring ? 'Active' : 'Inactive'}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Protected Paths</span>
              <span className="text-sm font-semibold text-gray-900">{systemStatus?.protected_paths || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Decoy Files</span>
              <span className="text-sm font-semibold text-gray-900">{systemStatus?.decoy_files || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Active Incidents</span>
              <span className={`text-sm font-semibold ${systemStatus?.active_incidents > 0 ? 'text-danger-600' : 'text-success-600'}`}>
                {systemStatus?.active_incidents || 0}
              </span>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center space-x-3 mb-4">
            <TrendingUp className="h-6 w-6 text-primary-600" />
            <h3 className="text-lg font-semibold text-gray-900">Detection Metrics</h3>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Total Events</span>
              <span className="text-sm font-semibold text-gray-900">{stats?.total_events || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Suspicious Events</span>
              <span className="text-sm font-semibold text-warning-600">{stats?.suspicious_events || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Detection Rate</span>
              <span className="text-sm font-semibold text-gray-900">
                {stats?.total_events > 0
                  ? ((stats.suspicious_events / stats.total_events) * 100).toFixed(1)
                  : 0}%
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Response Time</span>
              <span className="text-sm font-semibold text-success-600">&lt; 1s</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
