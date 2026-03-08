const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class ApiService {
  async getStatus() {
    const response = await fetch(`${API_BASE_URL}/api/status`);
    return response.json();
  }

  async getIncidents(limit = 50) {
    const response = await fetch(`${API_BASE_URL}/api/incidents?limit=${limit}`);
    return response.json();
  }

  async getEvents(limit = 100) {
    const response = await fetch(`${API_BASE_URL}/api/events?limit=${limit}`);
    return response.json();
  }

  async getAlerts(unacknowledgedOnly = false) {
    const response = await fetch(`${API_BASE_URL}/api/alerts?unacknowledged_only=${unacknowledgedOnly}`);
    return response.json();
  }

  async getDecoys() {
    const response = await fetch(`${API_BASE_URL}/api/decoys`);
    return response.json();
  }

  async getStatistics() {
    const response = await fetch(`${API_BASE_URL}/api/stats`);
    return response.json();
  }

  async triggerContainment(incidentId) {
    const response = await fetch(`${API_BASE_URL}/api/containment/${incidentId}`, {
      method: 'POST',
    });
    return response.json();
  }

  async disableSystemLockdown() {
    const response = await fetch(`${API_BASE_URL}/api/containment/disable-lockdown`, {
      method: 'POST',
    });
    return response.json();
  }

  async getContainmentSettings() {
    const response = await fetch(`${API_BASE_URL}/api/settings/containment`);
    return response.json();
  }

  async updateContainmentSettings(settings) {
    const response = await fetch(`${API_BASE_URL}/api/settings/containment`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(settings),
    });
    return response.json();
  }

  async exportReport(days = 7) {
    const response = await fetch(`${API_BASE_URL}/api/export/report?days=${days}`);
    return response.json();
  }

  async deployDecoys(count = 10) {
    const response = await fetch(`${API_BASE_URL}/api/decoys/deploy?count=${count}`, {
      method: 'POST',
    });
    return response.json();
  }

  async deleteDecoy(decoyPath) {
    const encodedPath = encodeURIComponent(decoyPath);
    const response = await fetch(`${API_BASE_URL}/api/decoys/${encodedPath}`, {
      method: 'DELETE',
    });
    return response.json();
  }

  async deleteAllDecoys() {
    const response = await fetch(`${API_BASE_URL}/api/decoys/delete-all`, {
      method: 'POST',
    });
    return response.json();
  }

  async deleteAlert(alertId) {
    const response = await fetch(`${API_BASE_URL}/api/alerts/${alertId}`, {
      method: 'DELETE',
    });
    return response.json();
  }

  async deleteAllAlerts() {
    const response = await fetch(`${API_BASE_URL}/api/alerts/delete-all`, {
      method: 'POST',
    });
    return response.json();
  }

  async acknowledgeAlert(alertId) {
    const response = await fetch(`${API_BASE_URL}/api/alerts/${alertId}/acknowledge`, {
      method: 'POST',
    });
    return response.json();
  }

  async deleteEvent(eventId) {
    const response = await fetch(`${API_BASE_URL}/api/events/${eventId}`, {
      method: 'DELETE',
    });
    return response.json();
  }

  async deleteAllEvents() {
    const response = await fetch(`${API_BASE_URL}/api/events/delete-all`, {
      method: 'POST',
    });
    return response.json();
  }

  // Monitoring Modes API
  async getMonitoringModes() {
    const response = await fetch(`${API_BASE_URL}/api/monitoring/modes`);
    return response.json();
  }

  async setMonitoringMode(mode, enabled) {
    const response = await fetch(`${API_BASE_URL}/api/monitoring/modes/set?mode=${mode}&enabled=${enabled}`, {
      method: 'POST',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update monitoring mode');
    }

    return response.json();
  }

  async updateMonitoringModes(modes) {
    const response = await fetch(`${API_BASE_URL}/api/monitoring/modes`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(modes)
    });
    return response.json();
  }

  async startSystem() {
    const response = await fetch(`${API_BASE_URL}/api/system/start`, {
      method: 'POST'
    });
    return response.json();
  }

  async stopSystem() {
    const response = await fetch(`${API_BASE_URL}/api/system/stop`, {
      method: 'POST'
    });
    return response.json();
  }

  // File Protection API
  async getProtectionStats() {
    const response = await fetch(`${API_BASE_URL}/api/protection/stats`);
    return response.json();
  }

  async getFileBackups(filePath) {
    const encodedPath = encodeURIComponent(filePath);
    const response = await fetch(`${API_BASE_URL}/api/protection/backups/${encodedPath}`);
    return response.json();
  }

  async restoreFile(filePath, versionIndex = -1) {
    const response = await fetch(`${API_BASE_URL}/api/protection/restore?file_path=${encodeURIComponent(filePath)}&version_index=${versionIndex}`, {
      method: 'POST',
    });
    return response.json();
  }

  async restoreAllFiles() {
    const response = await fetch(`${API_BASE_URL}/api/protection/restore-all`, {
      method: 'POST',
    });
    return response.json();
  }

  // Drive Monitoring API
  async getDriveStats() {
    const response = await fetch(`${API_BASE_URL}/api/drives/stats`);
    return response.json();
  }

  async getMonitoredDrives() {
    const response = await fetch(`${API_BASE_URL}/api/drives/list`);
    return response.json();
  }

  // Quarantine API
  async getQuarantineItems() {
    const response = await fetch(`${API_BASE_URL}/api/quarantine`);
    if (!response.ok) throw new Error('Failed to fetch quarantine list');
    return response.json();
  }

  async restoreQuarantinedItem(itemId) {
    const response = await fetch(`${API_BASE_URL}/api/quarantine/${itemId}/restore`, {
      method: 'POST'
    });
    if (!response.ok) throw new Error('Failed to restore quarantined file');
    return response.json();
  }

  async deleteQuarantinedItem(itemId) {
    const response = await fetch(`${API_BASE_URL}/api/quarantine/${itemId}`, {
      method: 'DELETE'
    });
    if (!response.ok) throw new Error('Failed to permanently delete quarantined file');
    return response.json();
  }

  connectWebSocket(onMessage) {
    const ws = new WebSocket(`ws://localhost:8000/ws`);

    ws.onopen = () => {
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onMessage(data);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      // Reconnect after 5 seconds
      setTimeout(() => this.connectWebSocket(onMessage), 5000);
    };

    return ws;
  }
}

const apiServiceInstance = new ApiService();
export default apiServiceInstance;
