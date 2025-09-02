import React, { useState } from 'react';
import { Search, Download, ExternalLink, Filter } from 'lucide-react';
import { useChecker } from '../../context/CheckerContext';
import { CheckResult } from '../../types';

export function ResultsTable() {
  const { state } = useChecker();
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<'all' | 'valid' | 'invalid' | 'error'>('all');

  const filteredResults = state.checkResults.filter(result => {
    const matchesSearch = 
      result.url.toLowerCase().includes(searchTerm.toLowerCase()) ||
      result.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
      result.cmsType.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesFilter = filterStatus === 'all' || result.status === filterStatus;
    
    return matchesSearch && matchesFilter;
  });

  const exportResults = () => {
    const csvContent = [
      'URL,Username,Password,CMS Type,Status,Timestamp',
      ...filteredResults.map(result => 
        `"${result.url}","${result.username}","${result.password}","${result.cmsType}","${result.status}","${result.timestamp}"`
      )
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `checker_results_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getStatusBadge = (status: CheckResult['status']) => {
    switch (status) {
      case 'valid':
        return <span className="status-active">Valid</span>;
      case 'invalid':
        return <span className="status-inactive">Invalid</span>;
      case 'error':
        return <span className="status-checking">Error</span>;
    }
  };

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">Check Results</h3>
        <div className="flex items-center space-x-3">
          <button
            onClick={exportResults}
            className="btn-secondary flex items-center space-x-2"
            disabled={filteredResults.length === 0}
          >
            <Download className="w-4 h-4" />
            <span>Export</span>
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center space-x-4 mb-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search results..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input-field pl-10 w-full"
          />
        </div>

        <div className="flex items-center space-x-2">
          <Filter className="w-4 h-4 text-gray-400" />
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value as any)}
            className="input-field"
          >
            <option value="all">All Status</option>
            <option value="valid">Valid Only</option>
            <option value="invalid">Invalid Only</option>
            <option value="error">Error Only</option>
          </select>
        </div>
      </div>

      {/* Results Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-dark-700">
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-300">URL</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-300">Credentials</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-300">CMS Type</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-300">Status</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-300">Time</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-300">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredResults.length > 0 ? (
              filteredResults.map((result, index) => (
                <tr key={index} className="table-row">
                  <td className="py-3 px-4">
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-300 font-mono">{result.url}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <div className="text-sm">
                      <div className="text-gray-300">{result.username}</div>
                      <div className="text-gray-500 font-mono">{'•'.repeat(result.password.length)}</div>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-sm text-gray-300">{result.cmsType}</span>
                  </td>
                  <td className="py-3 px-4">
                    {getStatusBadge(result.status)}
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-sm text-gray-400">
                      {new Date(result.timestamp).toLocaleTimeString()}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <button
                      onClick={() => window.open(result.url, '_blank')}
                      className="p-1 text-gray-400 hover:text-primary-400 transition-colors"
                      title="Open URL"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={6} className="py-8 text-center text-gray-400">
                  No results available. Start checking to see results here.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {filteredResults.length > 0 && (
        <div className="mt-4 text-sm text-gray-400 text-center">
          Showing {filteredResults.length} of {state.checkResults.length} results
        </div>
      )}
    </div>
  );
}