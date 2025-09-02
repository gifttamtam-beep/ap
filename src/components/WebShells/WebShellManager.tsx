import React, { useState, useEffect } from 'react';
import { 
  Globe, 
  ExternalLink, 
  Trash2, 
  RefreshCw, 
  Filter,
  Eye,
  EyeOff,
  Clock
} from 'lucide-react';
import { useChecker } from '../../context/CheckerContext';
import { CheckerService } from '../../services/checkerService';

export function WebShellManager() {
  const { state, dispatch } = useChecker();
  const [filterActive, setFilterActive] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const checkerService = CheckerService.getInstance();

  const filteredShells = filterActive 
    ? state.webShells.filter(shell => shell.status === 'active')
    : state.webShells;

  const refreshAllShells = async () => {
    setIsRefreshing(true);
    
    const promises = state.webShells.map(async (shell) => {
      dispatch({ type: 'UPDATE_WEBSHELL_STATUS', payload: { id: shell.id, status: 'checking' } });
      
      const status = await checkerService.checkShellStatus(shell.url);
      dispatch({ type: 'UPDATE_WEBSHELL_STATUS', payload: { id: shell.id, status } });
    });

    await Promise.allSettled(promises);
    setIsRefreshing(false);
  };

  const refreshSingleShell = async (shellId: string, url: string) => {
    dispatch({ type: 'UPDATE_WEBSHELL_STATUS', payload: { id: shellId, status: 'checking' } });
    
    const status = await checkerService.checkShellStatus(url);
    dispatch({ type: 'UPDATE_WEBSHELL_STATUS', payload: { id: shellId, status } });
  };

  const removeShell = (shellId: string) => {
    if (confirm('Are you sure you want to remove this shell?')) {
      dispatch({ type: 'REMOVE_WEBSHELL', payload: shellId });
    }
  };

  const openShell = (url: string) => {
    window.open(url, '_blank');
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <div className="w-2 h-2 bg-green-400 rounded-full" />;
      case 'inactive':
        return <div className="w-2 h-2 bg-red-400 rounded-full" />;
      case 'checking':
        return <div className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse" />;
      default:
        return <div className="w-2 h-2 bg-gray-400 rounded-full" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <span className="status-active">Active</span>;
      case 'inactive':
        return <span className="status-inactive">Inactive</span>;
      case 'checking':
        return <span className="status-checking">Checking</span>;
      default:
        return <span className="status-inactive">Error</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">WebShell Manager</h3>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setFilterActive(!filterActive)}
              className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-colors ${
                filterActive 
                  ? 'bg-primary-600 text-white' 
                  : 'bg-dark-700 text-gray-300 hover:bg-dark-600'
              }`}
            >
              {filterActive ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
              <span>Active Only</span>
            </button>

            <button
              onClick={refreshAllShells}
              disabled={isRefreshing || state.webShells.length === 0}
              className="btn-secondary flex items-center space-x-2 disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              <span>Refresh All</span>
            </button>
          </div>
        </div>

        <div className="text-sm text-gray-400">
          Total Shells: {state.webShells.length} | 
          Active: {state.webShells.filter(s => s.status === 'active').length} |
          Showing: {filteredShells.length}
        </div>
      </div>

      {/* Shells Table */}
      <div className="card p-6">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-dark-700">
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-300">URL</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-300">Status</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-300">Last Checked</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-300">Uploaded</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-300">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredShells.length > 0 ? (
                filteredShells.map((shell) => (
                  <tr key={shell.id} className="table-row">
                    <td className="py-3 px-4">
                      <div className="flex items-center space-x-3">
                        {getStatusIcon(shell.status)}
                        <span className="text-sm text-gray-300 font-mono">{shell.url}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      {getStatusBadge(shell.status)}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center space-x-2 text-sm text-gray-400">
                        <Clock className="w-3 h-3" />
                        <span>{new Date(shell.lastChecked).toLocaleString()}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-sm text-gray-400">
                        {new Date(shell.uploadedAt).toLocaleDateString()}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => openShell(shell.url)}
                          className="p-1 text-gray-400 hover:text-primary-400 transition-colors"
                          title="Open Shell"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </button>
                        
                        <button
                          onClick={() => refreshSingleShell(shell.id, shell.url)}
                          className="p-1 text-gray-400 hover:text-blue-400 transition-colors"
                          title="Refresh Status"
                          disabled={shell.status === 'checking'}
                        >
                          <RefreshCw className={`w-4 h-4 ${shell.status === 'checking' ? 'animate-spin' : ''}`} />
                        </button>
                        
                        <button
                          onClick={() => removeShell(shell.id)}
                          className="p-1 text-gray-400 hover:text-red-400 transition-colors"
                          title="Remove Shell"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-gray-400">
                    {filterActive 
                      ? 'No active shells found'
                      : 'No shells uploaded yet. Start checking to upload shells automatically.'
                    }
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}