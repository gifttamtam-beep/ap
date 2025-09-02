import React from 'react';
import { Play, Square, Settings, RefreshCw } from 'lucide-react';
import { useChecker } from '../../context/CheckerContext';
import { CheckerService } from '../../services/checkerService';

export function CheckerControls() {
  const { state, dispatch } = useChecker();
  const checkerService = CheckerService.getInstance();

  const handleStart = async () => {
    if (state.comboFiles.length === 0) {
      alert('Please load combo files first');
      return;
    }

    dispatch({ type: 'SET_EXTRACTING', payload: true });
    dispatch({ type: 'RESET_RESULTS' });

    try {
      // Extract lines from files
      const extractedLines = await checkerService.extractFromFiles(
        state.comboFiles,
        (progress) => {
          // Update extraction progress if needed
        }
      );

      let finalLines = extractedLines;
      if (state.config.removeDuplicates) {
        finalLines = checkerService.removeDuplicates(extractedLines);
      }

      dispatch({ type: 'SET_EXTRACTED_LINES', payload: finalLines });
      dispatch({ type: 'SET_EXTRACTING', payload: false });

      if (!state.config.activeChecker) {
        return;
      }

      // Start checking
      dispatch({ type: 'SET_CHECKING', payload: true });
      checkerService.startChecking();

      // Process lines in batches
      const batchSize = 10;
      for (let i = 0; i < finalLines.length; i += batchSize) {
        const batch = finalLines.slice(i, i + batchSize);
        
        const promises = batch.map(async (combo) => {
          const result = await checkerService.checkLogin(combo, state.config.timeout);
          dispatch({ type: 'ADD_CHECK_RESULT', payload: result });
          
          // Simulate shell upload for valid results
          if (result.status === 'valid' && Math.random() > 0.7) {
            const shellId = `shell_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
            const shell = {
              id: shellId,
              url: `${result.url}/shell_${Math.random().toString(36).substr(2, 6)}.php`,
              status: 'active' as const,
              lastChecked: new Date().toISOString(),
              uploadedAt: new Date().toISOString(),
            };
            dispatch({ type: 'ADD_WEBSHELL', payload: shell });
          }
        });

        await Promise.allSettled(promises);
        
        // Small delay between batches
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      dispatch({ type: 'SET_CHECKING', payload: false });
    } catch (error) {
      console.error('Error during checking:', error);
      dispatch({ type: 'SET_EXTRACTING', payload: false });
      dispatch({ type: 'SET_CHECKING', payload: false });
    }
  };

  const handleStop = () => {
    checkerService.stopChecking();
    dispatch({ type: 'SET_CHECKING', payload: false });
    dispatch({ type: 'SET_EXTRACTING', payload: false });
  };

  const handleConfigChange = (key: keyof typeof state.config, value: any) => {
    dispatch({ type: 'UPDATE_CONFIG', payload: { [key]: value } });
  };

  return (
    <div className="card p-6">
      <h3 className="text-lg font-semibold text-white mb-4">Checker Controls</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Configuration */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Timeout (seconds)
            </label>
            <input
              type="number"
              value={state.config.timeout}
              onChange={(e) => handleConfigChange('timeout', parseInt(e.target.value) || 10)}
              className="input-field w-full"
              min="1"
              max="60"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Max Threads
            </label>
            <input
              type="number"
              value={state.config.maxThreads}
              onChange={(e) => handleConfigChange('maxThreads', parseInt(e.target.value) || 150)}
              className="input-field w-full"
              min="1"
              max="500"
            />
          </div>
        </div>

        {/* Options */}
        <div className="space-y-4">
          <div className="flex items-center space-x-3">
            <input
              type="checkbox"
              id="removeDuplicates"
              checked={state.config.removeDuplicates}
              onChange={(e) => handleConfigChange('removeDuplicates', e.target.checked)}
              className="w-4 h-4 text-primary-600 bg-dark-700 border-dark-600 rounded focus:ring-primary-500"
            />
            <label htmlFor="removeDuplicates" className="text-sm text-gray-300">
              Remove Duplicates
            </label>
          </div>

          <div className="flex items-center space-x-3">
            <input
              type="checkbox"
              id="activeChecker"
              checked={state.config.activeChecker}
              onChange={(e) => handleConfigChange('activeChecker', e.target.checked)}
              className="w-4 h-4 text-primary-600 bg-dark-700 border-dark-600 rounded focus:ring-primary-500"
            />
            <label htmlFor="activeChecker" className="text-sm text-gray-300">
              Active Checker
            </label>
          </div>

          <div className="flex items-center space-x-3">
            <input
              type="checkbox"
              id="useProxy"
              checked={state.config.useProxy}
              onChange={(e) => handleConfigChange('useProxy', e.target.checked)}
              className="w-4 h-4 text-primary-600 bg-dark-700 border-dark-600 rounded focus:ring-primary-500"
            />
            <label htmlFor="useProxy" className="text-sm text-gray-300">
              Use Proxy
            </label>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center space-x-4 mt-6 pt-4 border-t border-dark-700">
        <button
          onClick={handleStart}
          disabled={state.isChecking || state.isExtracting || state.comboFiles.length === 0}
          className="btn-primary flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {state.isExtracting ? (
            <RefreshCw className="w-4 h-4 animate-spin" />
          ) : (
            <Play className="w-4 h-4" />
          )}
          <span>
            {state.isExtracting ? 'Extracting...' : state.isChecking ? 'Checking...' : 'Start'}
          </span>
        </button>

        <button
          onClick={handleStop}
          disabled={!state.isChecking && !state.isExtracting}
          className="btn-secondary flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Square className="w-4 h-4" />
          <span>Stop</span>
        </button>

        <div className="flex-1" />

        <div className="text-sm text-gray-400">
          Files: {state.comboFiles.length} | 
          Extracted: {state.stats.totalExtracted}
        </div>
      </div>
    </div>
  );
}