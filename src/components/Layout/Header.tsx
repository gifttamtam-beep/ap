import React from 'react';
import { Bell, User, Minimize2, Maximize2, X } from 'lucide-react';

interface HeaderProps {
  title: string;
}

export function Header({ title }: HeaderProps) {
  const handleMinimize = () => {
    // In a real desktop app, this would minimize the window
    console.log('Minimize window');
  };

  const handleMaximize = () => {
    // In a real desktop app, this would toggle maximize/restore
    console.log('Toggle maximize/restore');
  };

  const handleClose = () => {
    // In a real desktop app, this would close the window
    if (confirm('Are you sure you want to close the application?')) {
      window.close();
    }
  };

  return (
    <header className="bg-dark-800 border-b border-dark-700 px-6 py-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">{title}</h2>
          <p className="text-sm text-gray-400">Manage your checking operations</p>
        </div>

        <div className="flex items-center space-x-4">
          <button className="p-2 text-gray-400 hover:text-white hover:bg-dark-700 rounded-lg transition-colors">
            <Bell className="w-5 h-5" />
          </button>
          
          <button className="p-2 text-gray-400 hover:text-white hover:bg-dark-700 rounded-lg transition-colors">
            <User className="w-5 h-5" />
          </button>

          <div className="flex items-center space-x-1 ml-4">
            <button
              onClick={handleMinimize}
              className="p-2 text-gray-400 hover:text-white hover:bg-dark-700 rounded-lg transition-colors"
            >
              <Minimize2 className="w-4 h-4" />
            </button>
            
            <button
              onClick={handleMaximize}
              className="p-2 text-gray-400 hover:text-white hover:bg-dark-700 rounded-lg transition-colors"
            >
              <Maximize2 className="w-4 h-4" />
            </button>
            
            <button
              onClick={handleClose}
              className="p-2 text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}