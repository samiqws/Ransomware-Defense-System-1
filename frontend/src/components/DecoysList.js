import React, { useState } from 'react';
import { Database, CheckCircle, AlertTriangle, Trash2, AlertOctagon } from 'lucide-react';
import ApiService from '../services/api';

function DecoysList({ decoys, onRefresh }) {
  const [deletingDecoy, setDeletingDecoy] = useState(null);
  const [deletingAll, setDeletingAll] = useState(false);

  const handleDeleteDecoy = async (decoyPath) => {
    if (!window.confirm(`Are you sure you want to delete this decoy?\n\n${decoyPath}`)) {
      return;
    }

    setDeletingDecoy(decoyPath);
    try {
      const result = await ApiService.deleteDecoy(decoyPath);
      alert(result.message);
      if (onRefresh) onRefresh();
    } catch (error) {
      console.error('Failed to delete decoy:', error);
      alert('Failed to delete decoy: ' + error.message);
    } finally {
      setDeletingDecoy(null);
    }
  };

  const handleDeleteAll = async () => {
    if (!window.confirm('⚠️ WARNING: This will delete ALL decoy files!\n\nAre you sure you want to continue?')) {
      return;
    }

    setDeletingAll(true);
    try {
      const result = await ApiService.deleteAllDecoys();
      alert(`${result.message}\nDeleted: ${result.deleted_count} files${result.failed_count > 0 ? `\nFailed: ${result.failed_count} files` : ''}`);
      if (onRefresh) onRefresh();
    } catch (error) {
      console.error('Failed to delete all decoys:', error);
      alert('Failed to delete all decoys: ' + error.message);
    } finally {
      setDeletingAll(false);
    }
  };
  if (!decoys || decoys.total === 0) {
    return (
      <div className="card text-center py-12">
        <Database className="h-16 w-16 mx-auto text-gray-300 mb-4" />
        <p className="text-gray-600">No decoy files deployed</p>
        <button className="btn-primary mt-4">Deploy Decoys</button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card bg-gradient-to-br from-primary-50 to-primary-100">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-primary-900">Total Decoys</p>
              <p className="text-3xl font-bold text-primary-900 mt-2">{decoys.total}</p>
            </div>
            <Database className="h-12 w-12 text-primary-500" />
          </div>
        </div>

        <div className="card bg-gradient-to-br from-success-50 to-success-100">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-success-900">Intact</p>
              <p className="text-3xl font-bold text-success-900 mt-2">
                {decoys.decoys?.filter(d => !d.compromised).length || decoys.total}
              </p>
            </div>
            <CheckCircle className="h-12 w-12 text-success-500" />
          </div>
        </div>

        <div className="card bg-gradient-to-br from-danger-50 to-danger-100">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-danger-900">Compromised</p>
              <p className="text-3xl font-bold text-danger-900 mt-2">
                {decoys.decoys?.filter(d => d.compromised).length || 0}
              </p>
            </div>
            <AlertTriangle className="h-12 w-12 text-danger-500" />
          </div>
        </div>
      </div>

      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Decoy Files</h3>
          {decoys.total > 0 && (
            <button
              onClick={handleDeleteAll}
              disabled={deletingAll}
              className="btn-danger text-sm flex items-center space-x-2"
            >
              <AlertOctagon className="h-4 w-4" />
              <span>{deletingAll ? 'Deleting All...' : 'Delete All Decoys'}</span>
            </button>
          )}
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  File Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Path
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Size
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
              {decoys.decoys?.slice(0, 20).map((decoy, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    <span className="badge bg-gray-100 text-gray-700">{decoy.type}</span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600 max-w-md truncate" title={decoy.path}>
                    {decoy.path}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {(decoy.size / 1024).toFixed(2)} KB
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`badge ${decoy.compromised ? 'badge-critical' : 'badge-success'}`}>
                      {decoy.compromised ? 'Compromised' : 'Intact'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <button
                      onClick={() => handleDeleteDecoy(decoy.path)}
                      disabled={deletingDecoy === decoy.path}
                      className="text-danger-600 hover:text-danger-900 flex items-center space-x-1"
                      title="Delete this decoy"
                    >
                      <Trash2 className="h-4 w-4" />
                      <span>{deletingDecoy === decoy.path ? 'Deleting...' : 'Delete'}</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {decoys.decoys && decoys.decoys.length > 20 && (
          <div className="mt-4 text-center text-sm text-gray-500">
            Showing 20 of {decoys.total} decoys
          </div>
        )}
      </div>
    </div>
  );
}

export default DecoysList;
