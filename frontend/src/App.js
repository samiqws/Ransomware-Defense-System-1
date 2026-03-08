import React, { useState, useEffect } from 'react';
import { Shield, AlertTriangle, Activity, FileText, Database, Settings, Eye, Lock } from 'lucide-react';
import Dashboard from './components/Dashboard';
import SettingsPanel from './components/SettingsPanel';
import MonitoringModesPanel from './components/MonitoringModesPanel';
import QuarantineView from './components/QuarantineView';
import ApiService from './services/api';
import './index.css';

function App() {
  const [currentView, setCurrentView] = useState('dashboard');
  const [systemStatus, setSystemStatus] = useState(null);
  const [realTimeEvents, setRealTimeEvents] = useState([]);
  const [systemRunning, setSystemRunning] = useState(true);
  const [isToggling, setIsToggling] = useState(false);

  useEffect(() => {
    // Fetch initial status
    ApiService.getStatus().then(status => {
      setSystemStatus(status);
      setSystemRunning(status.system_running !== false);
    }).catch(console.error);

    // Connect WebSocket
    const websocket = ApiService.connectWebSocket((event) => {
      setRealTimeEvents((prev) => [event, ...prev].slice(0, 100));

      // Update status on events
      if (event.type === 'threat_detected' || event.type === 'system_started' || event.type === 'system_stopped') {
        ApiService.getStatus().then(status => {
          setSystemStatus(status);
          setSystemRunning(status.system_running !== false);
        }).catch(console.error);
      }
    });

    // Cleanup
    return () => {
      if (websocket) {
        websocket.close();
      }
    };
  }, []);

  const handleSystemToggle = async () => {
    // Confirm before stopping
    if (systemRunning) {
      if (!window.confirm('Are you sure you want to stop the monitoring system? Threat detection will be disabled.')) {
        return;
      }
    }

    setIsToggling(true);
    try {
      const result = systemRunning
        ? await ApiService.stopSystem()
        : await ApiService.startSystem();

      if (result.success) {
        setSystemRunning(!systemRunning);
        // Update system status
        const status = await ApiService.getStatus();
        setSystemStatus(status);
      } else {
        alert(result.message || 'Failed to change system state');
      }
    } catch (error) {
      console.error('Failed to toggle system:', error);
      alert('An error occurred while trying to change the system state');
    } finally {
      setIsToggling(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-full mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-3">
              <div className="bg-gradient-to-br from-primary-500 to-primary-700 p-2 rounded-lg">
                <Shield className="h-8 w-8 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  Ransomware Defense System
                </h1>
                <p className="text-sm text-gray-500">
                  Advanced Detection & Containment Engine
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              {/* System Control Toggle Button */}
              <button
                onClick={handleSystemToggle}
                disabled={isToggling}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-all ${systemRunning
                  ? 'bg-success-500 hover:bg-success-600 text-white'
                  : 'bg-danger-500 hover:bg-danger-600 text-white'
                  } ${isToggling ? 'opacity-50 cursor-not-allowed' : ''}`}
                title={systemRunning ? 'Stop System' : 'Start System'}
              >
                {isToggling ? (
                  <>
                    <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                    <span>Loading...</span>
                  </>
                ) : systemRunning ? (
                  <>
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <rect x="6" y="4" width="4" height="16" />
                      <rect x="14" y="4" width="4" height="16" />
                    </svg>
                    <span>Stop</span>
                  </>
                ) : (
                  <>
                    <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M8 5v14l11-7z" />
                    </svg>
                    <span>Start</span>
                  </>
                )}
              </button>

              {systemStatus && (
                <div className="flex items-center space-x-2">
                  <div className={`h-3 w-3 rounded-full ${systemRunning ? 'bg-success-500 animate-pulse' : 'bg-danger-500'}`} />
                  <span className="text-sm font-medium text-gray-700">
                    {systemRunning ? 'Active' : 'Inactive'}
                  </span>
                </div>
              )}

              {systemStatus && systemStatus.active_incidents > 0 && (
                <div className="flex items-center space-x-2 bg-danger-50 px-3 py-2 rounded-lg">
                  <AlertTriangle className="h-5 w-5 text-danger-600" />
                  <span className="text-sm font-bold text-danger-700">
                    {systemStatus.active_incidents} Active Threat{systemStatus.active_incidents > 1 ? 's' : ''}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-full mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            <button
              onClick={() => setCurrentView('dashboard')}
              className={`flex items-center space-x-2 py-4 border-b-2 transition-colors ${currentView === 'dashboard'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
            >
              <Activity className="h-5 w-5" />
              <span className="font-medium">Dashboard</span>
            </button>

            <button
              onClick={() => setCurrentView('incidents')}
              className={`flex items-center space-x-2 py-4 border-b-2 transition-colors ${currentView === 'incidents'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
            >
              <AlertTriangle className="h-5 w-5" />
              <span className="font-medium">Incidents</span>
            </button>

            <button
              onClick={() => setCurrentView('events')}
              className={`flex items-center space-x-2 py-4 border-b-2 transition-colors ${currentView === 'events'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
            >
              <FileText className="h-5 w-5" />
              <span className="font-medium">Events</span>
            </button>

            <button
              onClick={() => setCurrentView('decoys')}
              className={`flex items-center space-x-2 py-4 border-b-2 transition-colors ${currentView === 'decoys'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
            >
              <Database className="h-5 w-5" />
              <span className="font-medium">Decoys</span>
            </button>

            <button
              onClick={() => setCurrentView('monitoring')}
              className={`flex items-center space-x-2 py-4 border-b-2 transition-colors ${currentView === 'monitoring'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
            >
              <Eye className="h-5 w-5" />
              <span className="font-medium">Monitoring</span>
            </button>

            <button
              onClick={() => setCurrentView('quarantine')}
              className={`flex items-center space-x-2 py-4 border-b-2 transition-colors ${currentView === 'quarantine'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
            >
              <Lock className="h-5 w-5" />
              <span className="font-medium">Quarantine</span>
            </button>

            <button
              onClick={() => setCurrentView('settings')}
              className={`flex items-center space-x-2 py-4 border-b-2 transition-colors ${currentView === 'settings'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
            >
              <Settings className="h-5 w-5" />
              <span className="font-medium">Settings</span>
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {currentView === 'monitoring' ? (
          <MonitoringModesPanel />
        ) : currentView === 'settings' ? (
          <SettingsPanel />
        ) : currentView === 'quarantine' ? (
          <QuarantineView />
        ) : (
          <Dashboard
            view={currentView}
            systemStatus={systemStatus}
            realTimeEvents={realTimeEvents}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-full mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <p className="text-sm text-gray-500">
              © 2024 Ransomware Defense System - Enterprise Edition
            </p>
            <div className="flex items-center space-x-4 text-sm text-gray-500">
              <span>Protected Paths: {systemStatus?.protected_paths || 0}</span>
              <span>•</span>
              <span>Decoy Files: {systemStatus?.decoy_files || 0}</span>
              <span>•</span>
              <span>Clients: {systemStatus?.connected_clients || 0}</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
