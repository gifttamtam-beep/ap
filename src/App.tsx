import React, { useState } from 'react';
import { CheckerProvider } from './context/CheckerContext';
import { Sidebar } from './components/Layout/Sidebar';
import { Header } from './components/Layout/Header';
import { Dashboard } from './components/Dashboard/Dashboard';
import { FileUploader } from './components/Checker/FileUploader';
import { CheckerControls } from './components/Checker/CheckerControls';
import { ResultsTable } from './components/Checker/ResultsTable';
import { WebShellManager } from './components/WebShells/WebShellManager';
import { DatabaseViewer } from './components/Database/DatabaseViewer';
import { SettingsPanel } from './components/Settings/SettingsPanel';

function AppContent() {
  const [activeTab, setActiveTab] = useState('dashboard');

  const getTabTitle = () => {
    switch (activeTab) {
      case 'dashboard': return 'Dashboard';
      case 'checker': return 'Checker';
      case 'webshells': return 'WebShell Manager';
      case 'results': return 'Results';
      case 'database': return 'Database';
      case 'settings': return 'Settings';
      default: return 'Aspire Checker';
    }
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard />;
      
      case 'checker':
        return (
          <div className="space-y-6">
            <FileUploader />
            <CheckerControls />
            <ResultsTable />
          </div>
        );
      
      case 'webshells':
        return <WebShellManager />;
      
      case 'results':
        return <ResultsTable />;
      
      case 'database':
        return <DatabaseViewer />;
      
      case 'settings':
        return <SettingsPanel />;
      
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="flex h-screen bg-dark-900">
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
      
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header title={getTabTitle()} />
        
        <main className="flex-1 overflow-y-auto p-6">
          <div className="max-w-7xl mx-auto">
            {renderContent()}
          </div>
        </main>
      </div>
    </div>
  );
}

function App() {
  return (
    <CheckerProvider>
      <AppContent />
    </CheckerProvider>
  );
}

export default App;