import React, { useState, useEffect } from 'react';
import { Lock, RefreshCcw, Trash2, AlertCircle, FileKey } from 'lucide-react';
import ApiService from '../services/api';

const QuarantineView = () => {
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchItems = async () => {
        setLoading(true);
        try {
            const data = await ApiService.getQuarantineItems();
            setItems(data);
        } catch (err) {
            setError(err.message || 'Failed to fetch quarantine list');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchItems();
    }, []);

    const handleRestore = async (id, name) => {
        if (!window.confirm(`Are you sure you want to RESTORE ${name} to its original location? This might be dangerous.`)) return;
        try {
            const result = await ApiService.restoreQuarantinedItem(id);
            if (result.success || result.message === "Restored successfully") {
                setItems(items.map(item => item.id === id ? { ...item, status: 'restored' } : item));
                alert('File restored successfully');
            } else {
                alert(result.detail || 'Failed to restore');
            }
        } catch (err) {
            alert('Error restoring file: ' + err.message);
        }
    };

    const handleDelete = async (id, name) => {
        if (!window.confirm(`Are you sure you want to PERMANENTLY DELETE ${name}?`)) return;
        try {
            const result = await ApiService.deleteQuarantinedItem(id);
            if (result.success || result.message === "Deleted successfully") {
                setItems(items.map(item => item.id === id ? { ...item, status: 'deleted' } : item));
                alert('File permanently deleted');
            } else {
                alert(result.detail || 'Failed to delete');
            }
        } catch (err) {
            alert('Error deleting file: ' + err.message);
        }
    };

    if (loading) return <div className="p-8 text-center text-gray-500 animate-pulse">Loading Quarantine Data...</div>;

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-xl font-bold text-gray-900 flex items-center">
                        <Lock className="w-6 h-6 mr-2 text-danger-500" />
                        Quarantined Threats
                    </h2>
                    <p className="text-sm text-gray-500 mt-1">
                        Malicious executables captured and isolated by the containment engine.
                    </p>
                </div>
                <button
                    onClick={fetchItems}
                    className="flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium"
                >
                    <RefreshCcw className="w-4 h-4 mr-2" />
                    Refresh
                </button>
            </div>

            {error && (
                <div className="bg-danger-50 text-danger-700 p-4 rounded-lg flex items-center shadow-sm">
                    <AlertCircle className="w-5 h-5 mr-2" />
                    {error}
                </div>
            )}

            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">File Details</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date Captured</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Incident ID</th>
                                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {items.length === 0 ? (
                                <tr>
                                    <td colSpan="5" className="px-6 py-12 text-center text-gray-500">
                                        <FileKey className="w-12 h-12 mx-auto text-gray-300 mb-3" />
                                        <p className="font-medium text-gray-900">No quarantined items</p>
                                        <p className="text-sm">The system hasn't isolated any threats recently.</p>
                                    </td>
                                </tr>
                            ) : (
                                items.map((item) => (
                                    <tr key={item.id} className="hover:bg-gray-50 transition-colors">
                                        <td className="px-6 py-4">
                                            <div className="flex items-center mt-1">
                                                <div className="text-sm font-medium text-gray-900 truncate max-w-xs" title={item.original_path}>
                                                    {item.original_path.split('\\').pop() || item.original_path.split('/').pop()}
                                                </div>
                                            </div>
                                            <div className="text-xs text-gray-500 mt-1 truncate max-w-sm" title={item.original_path}>
                                                {item.original_path}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {new Date(item.timestamp).toLocaleString()}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className="text-xs font-mono text-gray-600 bg-gray-100 px-2 py-1 rounded">
                                                {item.incident_id.substring(0, 8)}...
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-center">
                                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                        ${item.status === 'quarantined' ? 'bg-warning-100 text-warning-800' :
                                                    item.status === 'restored' ? 'bg-success-100 text-success-800' :
                                                        'bg-gray-100 text-gray-800'}`}>
                                                {item.status.toUpperCase()}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                            {item.status === 'quarantined' && (
                                                <div className="flex justify-end space-x-2">
                                                    <button
                                                        onClick={() => handleRestore(item.id, item.original_path)}
                                                        className="text-primary-600 hover:text-primary-900 flex items-center bg-primary-50 px-2 py-1 rounded transition-colors"
                                                        title="Restore file to original location"
                                                    >
                                                        <RefreshCcw className="w-4 h-4 mr-1" /> Restore
                                                    </button>
                                                    <button
                                                        onClick={() => handleDelete(item.id, item.original_path)}
                                                        className="text-danger-600 hover:text-danger-900 flex items-center bg-danger-50 px-2 py-1 rounded transition-colors"
                                                        title="Permanently delete file"
                                                    >
                                                        <Trash2 className="w-4 h-4 mr-1" /> Delete
                                                    </button>
                                                </div>
                                            )}
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default QuarantineView;
