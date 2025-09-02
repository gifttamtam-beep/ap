import React from 'react';
import { 
  FileText, 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  Globe, 
  Activity,
  TrendingUp,
  Clock
} from 'lucide-react';
import { StatsCard } from './StatsCard';
import { useChecker } from '../../context/CheckerContext';

export function Dashboard() {
  const { state } = useChecker();
  const { stats, checkResults, webShells, isChecking } = state;

  const recentResults = checkResults.slice(-5).reverse();
  const activeShells = webShells.filter(shell => shell.status === 'active');

  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
          title="Total Extracted"
          value={stats.totalExtracted}
          icon={FileText}
          color="blue"
        />
        <StatsCard
          title="Valid Logins"
          value={stats.totalValid}
          icon={CheckCircle}
          color="green"
        />
        <StatsCard
          title="Failed Attempts"
          value={stats.totalFailed}
          icon={XCircle}
          color="red"
        />
        <StatsCard
          title="Active Shells"
          value={activeShells.length}
          icon={Globe}
          color="purple"
        />
      </div>

      {/* Progress Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Checking Progress</h3>
            <div className={`flex items-center space-x-2 ${isChecking ? 'text-green-400' : 'text-gray-400'}`}>
              <Activity className="w-4 h-4" />
              <span className="text-sm">{isChecking ? 'Running' : 'Idle'}</span>
            </div>
          </div>
          
          <div className="space-y-4">
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Progress</span>
              <span className="text-white">
                {stats.totalChecked} / {stats.totalExtracted}
              </span>
            </div>
            
            <div className="w-full bg-dark-700 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-primary-500 to-primary-600 h-2 rounded-full transition-all duration-300"
                style={{ 
                  width: stats.totalExtracted > 0 
                    ? `${(stats.totalChecked / stats.totalExtracted) * 100}%` 
                    : '0%' 
                }}
              />
            </div>
            
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-2xl font-bold text-green-400">{stats.totalValid}</p>
                <p className="text-xs text-gray-400">Valid</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-red-400">{stats.totalInvalid}</p>
                <p className="text-xs text-gray-400">Invalid</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-yellow-400">{stats.totalFailed}</p>
                <p className="text-xs text-gray-400">Errors</p>
              </div>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">System Status</h3>
            <TrendingUp className="w-5 h-5 text-primary-400" />
          </div>
          
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Active Threads</span>
              <span className="text-white font-medium">{stats.activeThreads}</span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Success Rate</span>
              <span className="text-green-400 font-medium">
                {stats.totalChecked > 0 
                  ? `${((stats.totalValid / stats.totalChecked) * 100).toFixed(1)}%`
                  : '0%'
                }
              </span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Shells Uploaded</span>
              <span className="text-purple-400 font-medium">{stats.totalShellsUploaded}</span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Remaining</span>
              <span className="text-blue-400 font-medium">
                {stats.totalExtracted - stats.totalChecked}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Results */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Recent Results</h3>
          <Clock className="w-5 h-5 text-gray-400" />
        </div>
        
        {recentResults.length > 0 ? (
          <div className="space-y-3">
            {recentResults.map((result, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-dark-700 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className={clsx(
                    'w-2 h-2 rounded-full',
                    result.status === 'valid' ? 'bg-green-400' :
                    result.status === 'invalid' ? 'bg-red-400' : 'bg-yellow-400'
                  )} />
                  <div>
                    <p className="text-white font-medium">{result.url}</p>
                    <p className="text-sm text-gray-400">{result.username}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-300">{result.cmsType}</p>
                  <p className="text-xs text-gray-500">
                    {new Date(result.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-400">
            <AlertTriangle className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>No recent results available</p>
          </div>
        )}
      </div>
    </div>
  );
}