import React, { useState, useEffect } from 'react';
import { Eye, Shield, HardDrive, AlertCircle, CheckCircle2, RefreshCw, FileText } from 'lucide-react';
import ApiService from '../services/api';

function MonitoringModesPanel() {
  const [modes, setModes] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    loadMonitoringModes();
    loadStats();

    // Refresh stats every 10 seconds
    const interval = setInterval(loadStats, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadStats = async () => {
    try {
      const data = await ApiService.getStatistics();
      setStats(data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const loadMonitoringModes = async () => {
    try {
      const data = await ApiService.getMonitoringModes();
      // التأكد من وجود البيانات قبل تعيينها
      if (data && data.modes) {
        setModes(data.modes);
      } else {
        // تعيين قيم افتراضية إذا لم تكن البيانات موجودة
        setModes({
          user_files: false,
          decoy_files: false,
          system_files: false,
          yara_scanning: true
        });
        setMessage({ type: 'error', text: 'Failed to load monitoring modes - using defaults' });
        setTimeout(() => setMessage(null), 5000);
      }
      setLoading(false);
    } catch (error) {
      console.error('Failed to load monitoring modes:', error);
      // تعيين قيم افتراضية في حالة الخطأ
      setModes({
        user_files: false,
        decoy_files: false,
        system_files: false,
        yara_scanning: true
      });
      setMessage({ type: 'error', text: 'Failed to connect to server' });
      setTimeout(() => setMessage(null), 5000);
      setLoading(false);
    }
  };

  const handleToggle = async (mode) => {
    try {
      setSaving(true);
      const newValue = !modes[mode];

      const result = await ApiService.setMonitoringMode(mode, newValue);

      if (result.status === 'success') {
        setModes(result.modes);
        setMessage({
          type: 'success',
          text: `${getModeNameEn(mode)} monitoring ${newValue ? 'enabled' : 'disabled'}`
        });
        setTimeout(() => setMessage(null), 3000);
      } else {
        throw new Error(result.message || 'Failed to update mode');
      }
    } catch (error) {
      console.error('Failed to update monitoring mode:', error);
      setMessage({
        type: 'error',
        text: error.message || 'Failed to update settings. Check console for details.'
      });
      setTimeout(() => setMessage(null), 5000);
    } finally {
      setSaving(false);
    }
  };

  const getModeNameEn = (mode) => {
    const names = {
      'user_files': 'User Files',
      'decoy_files': 'Decoy Files',
      'system_files': 'System Files',
      'yara_scanning': 'YARA Scanner'
    };
    return names[mode] || mode;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Eye className="h-8 w-8 text-primary-600" />
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Monitoring Modes</h2>
            <p className="text-sm text-gray-600">Configure what files to monitor</p>
          </div>
        </div>
        <button
          onClick={loadMonitoringModes}
          className="flex items-center space-x-2 px-4 py-2 text-sm font-medium text-primary-700 bg-primary-50 rounded-lg hover:bg-primary-100 transition-colors"
        >
          <RefreshCw className="h-4 w-4" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Success/Error Message */}
      {message && (
        <div className={`flex items-center space-x-2 px-4 py-3 rounded-lg ${message.type === 'success' ? 'bg-success-50 text-success-700' : 'bg-danger-50 text-danger-700'
          }`}>
          {message.type === 'success' ? (
            <CheckCircle2 className="h-5 w-5" />
          ) : (
            <AlertCircle className="h-5 w-5" />
          )}
          <span className="text-sm font-medium">{message.text}</span>
        </div>
      )}

      {/* Monitoring Modes Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* User Files Mode */}
        <div className={`card border-2 ${modes?.user_files ? 'border-primary-300 bg-primary-50' : 'border-gray-200'}`}>
          <div className="flex flex-col h-full">
            <div className="flex items-start justify-between mb-4">
              <div className={`p-3 rounded-lg ${modes?.user_files ? 'bg-primary-600' : 'bg-gray-400'}`}>
                <HardDrive className="h-6 w-6 text-white" />
              </div>
              <button
                onClick={() => handleToggle('user_files')}
                disabled={saving}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 ${modes?.user_files ? 'bg-primary-600' : 'bg-gray-300'
                  } ${saving ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${modes?.user_files ? 'translate-x-1' : 'translate-x-6'
                    }`}
                />
              </button>
            </div>

            <h3 className="text-lg font-bold text-gray-900 mb-2">User Files</h3>
            <p className="text-xs text-gray-600 mb-3">Personal Documents & Data</p>

            <p className="text-sm text-gray-700 mb-4 flex-grow">
              Monitor user's personal files: Documents, Pictures, Downloads, Desktop, and Videos
            </p>

            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${modes?.user_files ? 'bg-success-500' : 'bg-gray-400'}`}></div>
              <span className="text-sm font-medium text-gray-700">
                {modes?.user_files ? 'Enabled' : 'Disabled'}
              </span>
            </div>
          </div>
        </div>

        {/* Decoy Files Mode */}
        <div className={`card border-2 ${modes?.decoy_files ? 'border-success-300 bg-success-50' : 'border-gray-200'}`}>
          <div className="flex flex-col h-full">
            <div className="flex items-start justify-between mb-4">
              <div className={`p-3 rounded-lg ${modes?.decoy_files ? 'bg-success-600' : 'bg-gray-400'}`}>
                <Shield className="h-6 w-6 text-white" />
              </div>
              <button
                onClick={() => handleToggle('decoy_files')}
                disabled={saving}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-success-500 ${modes?.decoy_files ? 'bg-success-600' : 'bg-gray-300'
                  } ${saving ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${modes?.decoy_files ? 'translate-x-1' : 'translate-x-6'
                    }`}
                />
              </button>
            </div>

            <h3 className="text-lg font-bold text-gray-900 mb-2">Decoy Files</h3>
            <p className="text-xs text-gray-600 mb-3">Honeypot Trap Files</p>

            <p className="text-sm text-gray-700 mb-4 flex-grow">
              Deploy honeypot files for early ransomware detection before real files are compromised
            </p>

            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${modes?.decoy_files ? 'bg-success-500' : 'bg-gray-400'}`}></div>
              <span className="text-sm font-medium text-gray-700">
                {modes?.decoy_files ? 'Enabled' : 'Disabled'}
              </span>
            </div>
          </div>
        </div>

        {/* System Files Mode */}
        <div className={`card border-2 ${modes?.system_files ? 'border-warning-300 bg-warning-50' : 'border-gray-200'}`}>
          <div className="flex flex-col h-full">
            <div className="flex items-start justify-between mb-4">
              <div className={`p-3 rounded-lg ${modes?.system_files ? 'bg-warning-600' : 'bg-gray-400'}`}>
                <Eye className="h-6 w-6 text-white" />
              </div>
              <button
                onClick={() => handleToggle('system_files')}
                disabled={saving}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-warning-500 ${modes?.system_files ? 'bg-warning-600' : 'bg-gray-300'
                  } ${saving ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${modes?.system_files ? 'translate-x-1' : 'translate-x-6'
                    }`}
                />
              </button>
            </div>

            <h3 className="text-lg font-bold text-gray-900 mb-2">System Files</h3>
            <p className="text-xs text-gray-600 mb-3">Windows System Files</p>

            <p className="text-sm text-gray-700 mb-4 flex-grow">
              Monitor Windows system files (not recommended - may impact performance)
            </p>

            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${modes?.system_files ? 'bg-warning-500' : 'bg-gray-400'}`}></div>
              <span className="text-sm font-medium text-gray-700">
                {modes?.system_files ? 'Enabled' : 'Disabled'}
              </span>
            </div>
          </div>
        </div>

        {/* YARA Scanning Mode */}
        <div className={`card border-2 ${modes?.yara_scanning ? 'border-danger-300 bg-danger-50' : 'border-gray-200'}`}>
          <div className="flex flex-col h-full">
            <div className="flex items-start justify-between mb-4">
              <div className={`p-3 rounded-lg ${modes?.yara_scanning ? 'bg-danger-600' : 'bg-gray-400'}`}>
                <AlertCircle className="h-6 w-6 text-white" />
              </div>
              <button
                onClick={() => handleToggle('yara_scanning')}
                disabled={saving}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-danger-500 ${modes?.yara_scanning ? 'bg-danger-600' : 'bg-gray-300'
                  } ${saving ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${modes?.yara_scanning ? 'translate-x-1' : 'translate-x-6'
                    }`}
                />
              </button>
            </div>

            <h3 className="text-lg font-bold text-gray-900 mb-2">YARA Scanner</h3>
            <p className="text-xs text-gray-600 mb-3">Malware Signatures</p>

            <p className="text-sm text-gray-700 mb-4 flex-grow">
              Pre-scan files for known malware and ransomware signatures natively
            </p>

            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${modes?.yara_scanning ? 'bg-success-500' : 'bg-gray-400'}`}></div>
              <span className="text-sm font-medium text-gray-700">
                {modes?.yara_scanning ? 'Enabled' : 'Disabled'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Monitoring Statistics */}
      <div className="card bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
        <div className="flex items-start space-x-3">
          <FileText className="h-6 w-6 text-blue-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h4 className="text-sm font-semibold text-blue-900 mb-3">Monitoring Statistics</h4>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-blue-700 mb-1">Total Monitored Files</p>
                <p className="text-2xl font-bold text-blue-900">{stats?.monitored_files?.toLocaleString() || 0}</p>
              </div>
              <div>
                <p className="text-xs text-blue-700 mb-1">Decoy Files</p>
                <p className="text-2xl font-bold text-blue-900">{stats?.decoy_files?.toLocaleString() || 0}</p>
              </div>
              <div>
                <p className="text-xs text-blue-700 mb-1">Total Events</p>
                <p className="text-2xl font-bold text-blue-900">{stats?.total_events?.toLocaleString() || 0}</p>
              </div>
              <div>
                <p className="text-xs text-blue-700 mb-1">Suspicious Events</p>
                <p className="text-2xl font-bold text-blue-900">{stats?.suspicious_events?.toLocaleString() || 0}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recommendations */}
      <div className="card bg-primary-50 border-primary-200">
        <div className="flex items-start space-x-3">
          <AlertCircle className="h-6 w-6 text-primary-600 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="text-sm font-semibold text-primary-900 mb-2">Recommendations</h4>
            <ul className="text-sm text-primary-800 space-y-1">
              <li>✅ <strong>Daily Use:</strong> Enable User Files + Decoy Files</li>
              <li>🎯 <strong>Early Detection:</strong> Enable Decoy Files only</li>
              <li>⚠️ <strong>System Files:</strong> Maximum protection only (impacts performance)</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default MonitoringModesPanel;
