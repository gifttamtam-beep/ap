import React from 'react';
import { Save, RotateCcw, Shield, Globe, Clock, Zap } from 'lucide-react';
import { useChecker } from '../../context/CheckerContext';

export function SettingsPanel() {
  const { state, dispatch } = useChecker();

  const handleConfigChange = (key: keyof typeof state.config, value: any) => {
    dispatch({ type: 'UPDATE_CONFIG', payload: { [key]: value } });
  };

  const resetToDefaults = () => {
    if (confirm('Reset all settings to default values?')) {
      dispatch({ 
        type: 'UPDATE_CONFIG', 
        payload: {
          timeout: 10,
          removeDuplicates: true,
          activeChecker: true,
          useProxy: false,
          maxThreads: 150,
        }
      });
    }
  };

  const saveSettings = () => {
    // In a real app, this would save to localStorage or backend
    localStorage.setItem('checkerConfig', JSON.stringify(state.config));
    alert('Settings saved successfully!');
  };

  return (
    <div className="space-y-6">
      <div className="card p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-white">Application Settings</h3>
          <div className="flex items-center space-x-3">
            <button
              onClick={resetToDefaults}
              className="btn-secondary flex items-center space-x-2"
            >
              <RotateCcw className="w-4 h-4" />
              <span>Reset</span>
            </button>
            <button
              onClick={saveSettings}
              className="btn-primary flex items-center space-x-2"
            >
              <Save className="w-4 h-4" />
              <span>Save</span>
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Performance Settings */}
          <div className="space-y-6">
            <div className="flex items-center space-x-2 mb-4">
              <Zap className="w-5 h-5 text-primary-400" />
              <h4 className="text-md font-semibold text-white">Performance</h4>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Request Timeout (seconds)
              </label>
              <input
                type="number"
                value={state.config.timeout}
                onChange={(e) => handleConfigChange('timeout', parseInt(e.target.value) || 10)}
                className="input-field w-full"
                min="1"
                max="60"
              />
              <p className="text-xs text-gray-500 mt-1">
                Maximum time to wait for each login attempt
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Maximum Threads
              </label>
              <input
                type="number"
                value={state.config.maxThreads}
                onChange={(e) => handleConfigChange('maxThreads', parseInt(e.target.value) || 150)}
                className="input-field w-full"
                min="1"
                max="1000"
              />
              <p className="text-xs text-gray-500 mt-1">
                Number of concurrent checking threads
              </p>
            </div>
          </div>

          {/* Security & Options */}
          <div className="space-y-6">
            <div className="flex items-center space-x-2 mb-4">
              <Shield className="w-5 h-5 text-primary-400" />
              <h4 className="text-md font-semibold text-white">Security & Options</h4>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-dark-700 rounded-lg">
                <div>
                  <label className="text-sm font-medium text-gray-300">Remove Duplicates</label>
                  <p className="text-xs text-gray-500">Filter out duplicate combo entries</p>
                </div>
                <input
                  type="checkbox"
                  checked={state.config.removeDuplicates}
                  onChange={(e) => handleConfigChange('removeDuplicates', e.target.checked)}
                  className="w-4 h-4 text-primary-600 bg-dark-600 border-dark-500 rounded focus:ring-primary-500"
                />
              </div>

              <div className="flex items-center justify-between p-4 bg-dark-700 rounded-lg">
                <div>
                  <label className="text-sm font-medium text-gray-300">Active Checker</label>
                  <p className="text-xs text-gray-500">Enable automatic login checking</p>
                </div>
                <input
                  type="checkbox"
                  checked={state.config.activeChecker}
                  onChange={(e) => handleConfigChange('activeChecker', e.target.checked)}
                  className="w-4 h-4 text-primary-600 bg-dark-600 border-dark-500 rounded focus:ring-primary-500"
                />
              </div>

              <div className="flex items-center justify-between p-4 bg-dark-700 rounded-lg">
                <div>
                  <label className="text-sm font-medium text-gray-300">Use Proxy</label>
                  <p className="text-xs text-gray-500">Route requests through proxy servers</p>
                </div>
                <input
                  type="checkbox"
                  checked={state.config.useProxy}
                  onChange={(e) => handleConfigChange('useProxy', e.target.checked)}
                  className="w-4 h-4 text-primary-600 bg-dark-600 border-dark-500 rounded focus:ring-primary-500"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* WebShells Table */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Active WebShells</h3>
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
                      : 'No shells uploaded yet'
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