import React, { useRef } from 'react';
import { Upload, File, X } from 'lucide-react';
import { useChecker } from '../../context/CheckerContext';

export function FileUploader() {
  const { state, dispatch } = useChecker();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    if (files.length > 0) {
      dispatch({ type: 'SET_COMBO_FILES', payload: files });
    }
  };

  const handleDrop = (event: React.DragEvent) => {
    event.preventDefault();
    const files = Array.from(event.dataTransfer.files);
    if (files.length > 0) {
      dispatch({ type: 'SET_COMBO_FILES', payload: files });
    }
  };

  const handleDragOver = (event: React.DragEvent) => {
    event.preventDefault();
  };

  const removeFile = (index: number) => {
    const newFiles = state.comboFiles.filter((_, i) => i !== index);
    dispatch({ type: 'SET_COMBO_FILES', payload: newFiles });
  };

  return (
    <div className="card p-6">
      <h3 className="text-lg font-semibold text-white mb-4">Load Combo Files</h3>
      
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        className="border-2 border-dashed border-dark-600 rounded-lg p-8 text-center hover:border-primary-500 transition-colors cursor-pointer"
        onClick={() => fileInputRef.current?.click()}
      >
        <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-300 mb-2">Drop combo files here or click to browse</p>
        <p className="text-sm text-gray-500">Supports .txt files with URL:username:password format</p>
        
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".txt"
          onChange={handleFileSelect}
          className="hidden"
        />
      </div>

      {state.comboFiles.length > 0 && (
        <div className="mt-4">
          <h4 className="text-sm font-medium text-gray-300 mb-2">
            Selected Files ({state.comboFiles.length})
          </h4>
          <div className="space-y-2 max-h-32 overflow-y-auto">
            {state.comboFiles.map((file, index) => (
              <div key={index} className="flex items-center justify-between p-2 bg-dark-700 rounded-lg">
                <div className="flex items-center space-x-2">
                  <File className="w-4 h-4 text-gray-400" />
                  <span className="text-sm text-gray-300">{file.name}</span>
                  <span className="text-xs text-gray-500">
                    ({(file.size / 1024).toFixed(1)} KB)
                  </span>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    removeFile(index);
                  }}
                  className="p-1 text-gray-400 hover:text-red-400 transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}