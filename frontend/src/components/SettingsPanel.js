import React, { useState, useEffect } from 'react';
import { Shield, Lock, Network, HardDrive, AlertCircle, CheckCircle2, Settings as SettingsIcon, Database } from 'lucide-react';
import ApiService from '../services/api';

function SettingsPanel() {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const data = await ApiService.getContainmentSettings();
      setSettings(data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to load settings:', error);
      setLoading(false);
    }
  };

  const handleToggle = async (key) => {
    try {
      setSaving(true);
      const newSettings = { ...settings, [key]: !settings[key] };

      const result = await ApiService.updateContainmentSettings({ [key]: !settings[key] });

      if (result.success) {
        setSettings(newSettings);
        setMessage({ type: 'success', text: 'Settings updated successfully' });
        setTimeout(() => setMessage(null), 3000);
      }
    } catch (error) {
      console.error('Failed to update settings:', error);
      setMessage({ type: 'error', text: 'Failed to update settings' });
      setTimeout(() => setMessage(null), 3000);
    } finally {
      setSaving(false);
    }
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
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <SettingsIcon className="h-8 w-8 text-primary-600" />
          <h2 className="text-2xl font-bold text-gray-900">Containment Settings</h2>
        </div>
        {message && (
          <div className={`flex items-center space-x-2 px-4 py-2 rounded-lg ${message.type === 'success' ? 'bg-success-50 text-success-700' : 'bg-danger-50 text-danger-700'
            }`}>
            {message.type === 'success' ? (
              <CheckCircle2 className="h-5 w-5" />
            ) : (
              <AlertCircle className="h-5 w-5" />
            )}
            <span className="text-sm font-medium">{message.text}</span>
          </div>
        )}
      </div>

      {/* Auto Containment - Primary Setting */}
      <div className="card bg-gradient-to-br from-primary-50 to-primary-100 border-2 border-primary-200">
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-4 flex-1">
            <div className="p-3 bg-primary-600 rounded-lg">
              <Shield className="h-6 w-6 text-white" />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-bold text-gray-900 mb-1">Auto Containment</h3>
              <p className="text-sm text-gray-600 mb-3">
                When enabled, the system will automatically execute containment actions when a high-severity threat is detected
              </p>
              <div className={`inline-flex items-center space-x-2 px-3 py-1 rounded-full text-sm font-medium ${settings?.auto_contain
                ? 'bg-success-100 text-success-700'
                : 'bg-gray-200 text-gray-700'
                }`}>
                <div className={`w-2 h-2 rounded-full ${settings?.auto_contain ? 'bg-success-500' : 'bg-gray-400'}`}></div>
                <span>{settings?.auto_contain ? 'Enabled' : 'Disabled'}</span>
              </div>
            </div>
          </div>
          <button
            onClick={() => handleToggle('auto_contain')}
            disabled={saving}
            className={`relative inline-flex h-8 w-14 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 ${settings?.auto_contain ? 'bg-primary-600' : 'bg-gray-300'
              } ${saving ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            <span
              className={`inline-block h-6 w-6 transform rounded-full bg-white shadow-md transition-transform ${settings?.auto_contain ? 'translate-x-7' : 'translate-x-1'
                }`}
            />
          </button>
        </div>
      </div>

      {/* Individual Containment Actions */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Containment Actions</h3>
        <div className="space-y-4">
          {/* Kill Process */}
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
            <div className="flex items-center space-x-3">
              <AlertCircle className="h-5 w-5 text-danger-600" />
              <div>
                <p className="text-sm font-medium text-gray-900">Kill Suspicious Process</p>
                <p className="text-xs text-gray-500">Terminate the process that is encrypting files</p>
              </div>
            </div>
            <button
              onClick={() => handleToggle('kill_process')}
              disabled={saving}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 ${settings?.kill_process ? 'bg-success-600' : 'bg-gray-300'
                } ${saving ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white shadow-sm transition-transform ${settings?.kill_process ? 'translate-x-6' : 'translate-x-1'
                  }`}
              />
            </button>
          </div>

          {/* Network Isolation */}
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
            <div className="flex items-center space-x-3">
              <Network className="h-5 w-5 text-warning-600" />
              <div>
                <p className="text-sm font-medium text-gray-900">Network Isolation</p>
                <p className="text-xs text-gray-500">Disconnect all network connections for critical threats</p>
              </div>
            </div>
            <button
              onClick={() => handleToggle('isolate_network')}
              disabled={saving}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 ${settings?.isolate_network ? 'bg-success-600' : 'bg-gray-300'
                } ${saving ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white shadow-sm transition-transform ${settings?.isolate_network ? 'translate-x-6' : 'translate-x-1'
                  }`}
              />
            </button>
          </div>

          {/* Network Drives */}
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
            <div className="flex items-center space-x-3">
              <HardDrive className="h-5 w-5 text-primary-600" />
              <div>
                <p className="text-sm font-medium text-gray-900">Disconnect Network Drives</p>
                <p className="text-xs text-gray-500">Disconnect all shared network drives</p>
              </div>
            </div>
            <button
              onClick={() => handleToggle('disable_network_drives')}
              disabled={saving}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 ${settings?.disable_network_drives ? 'bg-success-600' : 'bg-gray-300'
                } ${saving ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white shadow-sm transition-transform ${settings?.disable_network_drives ? 'translate-x-6' : 'translate-x-1'
                  }`}
              />
            </button>
          </div>

          {/* Lock System */}
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
            <div className="flex items-center space-x-3">
              <Lock className="h-5 w-5 text-gray-600" />
              <div>
                <p className="text-sm font-medium text-gray-900">Lock System</p>
                <p className="text-xs text-gray-500">Lock the computer immediately (critical threats only)</p>
              </div>
            </div>
            <button
              onClick={() => handleToggle('lock_system')}
              disabled={saving}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 ${settings?.lock_system ? 'bg-success-600' : 'bg-gray-300'
                } ${saving ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${settings?.lock_system ? 'translate-x-1' : 'translate-x-6'
                  }`}
              />
            </button>
          </div>

          {/* File Backup System */}
          <div className="flex items-center justify-between p-4 bg-primary-50 rounded-lg hover:bg-primary-100 transition-colors border border-primary-200">
            <div className="flex items-center space-x-3">
              <Database className="h-5 w-5 text-primary-600" />
              <div>
                <p className="text-sm font-medium text-primary-900">File Backup System</p>
                <p className="text-xs text-primary-700">Silently backup files when they are modified (Anti-Ransomware core feature)</p>
              </div>
            </div>
            <button
              onClick={() => handleToggle('enable_backup')}
              disabled={saving}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 ${settings?.enable_backup !== false ? 'bg-success-600' : 'bg-gray-300'
                } ${saving ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${settings?.enable_backup !== false ? 'translate-x-6' : 'translate-x-1'
                  }`}
              />
            </button>
          </div>
        </div>
      </div>

      {/* Warning Notice */}
      <div className="card bg-warning-50 border-warning-200">
        <div className="flex items-start space-x-3">
          <AlertCircle className="h-6 w-6 text-warning-600 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="text-sm font-semibold text-warning-900 mb-1">Important Warning</h4>
            <p className="text-sm text-warning-800">
              Auto containment will automatically terminate processes and isolate the system when a threat is detected. Make sure to test the system in a safe environment before enabling auto containment in production.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SettingsPanel;
