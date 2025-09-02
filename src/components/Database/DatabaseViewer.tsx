import React, { useState } from 'react';
import { Database, Download, Search, Filter, FileText } from 'lucide-react';
import { useChecker } from '../../context/CheckerContext';

export function DatabaseViewer() {
  const { state } = useChecker();
  const [activeFilter, setActiveFilter] = useState<'all' | 'wordpress' | 'cpanel' | 'joomla' | 'shells'>('all');
  const [searchTerm, setSearchTerm] = useState('');

  const getFilteredData = () => {
    let data: any[] = [];
    
    switch (activeFilter) {
      case 'wordpress':
        data = state.checkResults.filter(r => r.cmsType === 'WordPress' && r.status === 'valid');
        break;
      case 'cpanel':
        data = state.checkResults.filter(r => r.cmsType === 'cPanel' && r.status === 'valid');
        break;
      case 'joomla':
        data = state.checkResults.filter(r => r.cmsType === 'Joomla' && r.status === 'valid');
        break;
      case 'shells':
        data = state.webShells;
        break;
      default:
        data = state.checkResults.filter(r => r.status === 'valid');
    }

    if (searchTerm) {
      data = data.filter(item => 
        JSON.stringify(item).toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    return data;
  };

  const exportData = (format: 'txt' | 'csv' | 'json') => {
    const data = getFilteredData();
    let content = '';
    let filename = '';

    switch (format) {
      case 'txt':
        if (activeFilter === 'shells') {
          content = data.map(shell => shell.url).join('\n');
          filename = 'shells.txt';
        } else {
          content = data.map(result => `${result.url}:${result.username}:${result.password}`).join('\n');
          filename = `${activeFilter}_results.txt`;
        }
        break;
      
      case 'csv':
        if (activeFilter === 'shells') {
          content = 'URL,Status,Last Checked,Uploaded At\n' + 
                   data.map(shell => `"${shell.url}","${shell.status}","${shell.lastChecked}","${shell.uploadedAt}"`).join('\n');
          filename = 'shells.csv';
        } else {
          content = 'URL,Username,Password,CMS Type,Status,Timestamp\n' + 
                   data.map(result => `"${result.url}","${result.username}","${result.password}","${result.cmsType}","${result.status}","${result.timestamp}"`).join('\n');
          filename = `${activeFilter}_results.csv`;
        }
        break;
      
      case 'json':
        content = JSON.stringify(data, null, 2);
        filename = `${activeFilter}_results.json`;
        break;
    }

    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const filteredData = getFilteredData();

  return (
    <div className="space-y-6">
      <div className="card p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <Database className="w-6 h-6 text-primary-400" />
            <h3 className="text-lg font-semibold text-white">Database Viewer</h3>
          </div>
          
          <div className="flex items-center space-x-3">
            <button
              onClick={() => exportData('txt')}
              className="btn-secondary flex items-center space-x-2"
              disabled={filteredData.length === 0}
            >
              <FileText className="w-4 h-4" />
              <span>TXT</span>
            </button>
            <button
              onClick={() => exportData('csv')}
              className="btn-secondary flex items-center space-x-2"
              disabled={filteredData.length === 0}
            >
              <Download className="w-4 h-4" />
              <span>CSV</span>
            </button>
            <button
              onClick={() => exportData('json')}
              className="btn-secondary flex items-center space-x-2"
              disabled={filteredData.length === 0}
            >
              <Download className="w-4 h-4" />
              <span>JSON</span>
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center space-x-4 mb-6">
          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-gray-400" />
            <select
              value={activeFilter}
              onChange={(e) => setActiveFilter(e.target.value as any)}
              className="input-field"
            >
              <option value="all">All Valid Results</option>
              <option value="wordpress">WordPress</option>
              <option value="cpanel">cPanel</option>
              <option value="joomla">Joomla</option>
              <option value="shells">WebShells</option>
            </select>
          </div>

          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search database..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input-field pl-10 w-full"
            />
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-dark-700 p-4 rounded-lg text-center">
            <p className="text-2xl font-bold text-green-400">
              {state.checkResults.filter(r => r.cmsType === 'WordPress' && r.status === 'valid').length}
            </p>
            <p className="text-sm text-gray-400">WordPress</p>
          </div>
          <div className="bg-dark-700 p-4 rounded-lg text-center">
            <p className="text-2xl font-bold text-blue-400">
              {state.checkResults.filter(r => r.cmsType === 'cPanel' && r.status === 'valid').length}
            </p>
            <p className="text-sm text-gray-400">cPanel</p>
          </div>
          <div className="bg-dark-700 p-4 rounded-lg text-center">
            <p className="text-2xl font-bold text-purple-400">
              {state.checkResults.filter(r => r.cmsType === 'Joomla' && r.status === 'valid').length}
            </p>
            <p className="text-sm text-gray-400">Joomla</p>
          </div>
          <div className="bg-dark-700 p-4 rounded-lg text-center">
            <p className="text-2xl font-bold text-yellow-400">{state.webShells.length}</p>
            <p className="text-sm text-gray-400">Shells</p>
          </div>
        </div>
      </div>

      {/* Data Table */}
      <div className="card p-6">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-dark-700">
                {activeFilter === 'shells' ? (
                  <>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-300">Shell URL</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-300">Status</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-300">Last Checked</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-300">Uploaded</th>
                  </>
                ) : (
                  <>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-300">URL</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-300">Username</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-300">Password</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-300">CMS Type</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-300">Checked</th>
                  </>
                )}
              </tr>
            </thead>
            <tbody>
              {filteredData.length > 0 ? (
                filteredData.map((item, index) => (
                  <tr key={index} className="table-row">
                    {activeFilter === 'shells' ? (
                      <>
                        <td className="py-3 px-4">
                          <span className="text-sm text-gray-300 font-mono">{item.url}</span>
                        </td>
                        <td className="py-3 px-4">
                          <span className={`status-${item.status === 'active' ? 'active' : 'inactive'}`}>
                            {item.status}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <span className="text-sm text-gray-400">
                            {new Date(item.lastChecked).toLocaleString()}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <span className="text-sm text-gray-400">
                            {new Date(item.uploadedAt).toLocaleDateString()}
                          </span>
                        </td>
                      </>
                    ) : (
                      <>
                        <td className="py-3 px-4">
                          <span className="text-sm text-gray-300 font-mono">{item.url}</span>
                        </td>
                        <td className="py-3 px-4">
                          <span className="text-sm text-gray-300">{item.username}</span>
                        </td>
                        <td className="py-3 px-4">
                          <span className="text-sm text-gray-400 font-mono">
                            {'•'.repeat(item.password.length)}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <span className="text-sm text-gray-300">{item.cmsType}</span>
                        </td>
                        <td className="py-3 px-4">
                          <span className="text-sm text-gray-400">
                            {new Date(item.timestamp).toLocaleString()}
                          </span>
                        </td>
                      </>
                    )}
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={activeFilter === 'shells' ? 4 : 5} className="py-8 text-center text-gray-400">
                    No data available for the selected filter
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {filteredData.length > 0 && (
          <div className="mt-4 text-sm text-gray-400 text-center">
            Showing {filteredData.length} entries
          </div>
        )}
      </div>
    </div>
  );
}