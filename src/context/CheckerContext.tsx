import React, { createContext, useContext, useReducer, ReactNode } from 'react';
import { ComboLine, CheckResult, WebShell, Stats, CheckerConfig } from '../types';

interface CheckerState {
  comboFiles: File[];
  extractedLines: ComboLine[];
  checkResults: CheckResult[];
  webShells: WebShell[];
  stats: Stats;
  config: CheckerConfig;
  isChecking: boolean;
  isExtracting: boolean;
}

type CheckerAction =
  | { type: 'SET_COMBO_FILES'; payload: File[] }
  | { type: 'SET_EXTRACTED_LINES'; payload: ComboLine[] }
  | { type: 'ADD_CHECK_RESULT'; payload: CheckResult }
  | { type: 'ADD_WEBSHELL'; payload: WebShell }
  | { type: 'UPDATE_WEBSHELL_STATUS'; payload: { id: string; status: WebShell['status'] } }
  | { type: 'REMOVE_WEBSHELL'; payload: string }
  | { type: 'UPDATE_STATS'; payload: Partial<Stats> }
  | { type: 'UPDATE_CONFIG'; payload: Partial<CheckerConfig> }
  | { type: 'SET_CHECKING'; payload: boolean }
  | { type: 'SET_EXTRACTING'; payload: boolean }
  | { type: 'RESET_RESULTS' };

const initialState: CheckerState = {
  comboFiles: [],
  extractedLines: [],
  checkResults: [],
  webShells: [],
  stats: {
    totalExtracted: 0,
    totalChecked: 0,
    totalFailed: 0,
    totalValid: 0,
    totalInvalid: 0,
    totalShellsUploaded: 0,
    activeThreads: 0,
  },
  config: {
    timeout: 10,
    removeDuplicates: true,
    activeChecker: true,
    useProxy: false,
    maxThreads: 150,
  },
  isChecking: false,
  isExtracting: false,
};

function checkerReducer(state: CheckerState, action: CheckerAction): CheckerState {
  switch (action.type) {
    case 'SET_COMBO_FILES':
      return { ...state, comboFiles: action.payload };
    
    case 'SET_EXTRACTED_LINES':
      return { 
        ...state, 
        extractedLines: action.payload,
        stats: { ...state.stats, totalExtracted: action.payload.length }
      };
    
    case 'ADD_CHECK_RESULT':
      const newResult = action.payload;
      const updatedStats = { ...state.stats };
      updatedStats.totalChecked += 1;
      
      if (newResult.status === 'valid') {
        updatedStats.totalValid += 1;
      } else if (newResult.status === 'invalid') {
        updatedStats.totalInvalid += 1;
      } else {
        updatedStats.totalFailed += 1;
      }
      
      return {
        ...state,
        checkResults: [...state.checkResults, newResult],
        stats: updatedStats,
      };
    
    case 'ADD_WEBSHELL':
      return {
        ...state,
        webShells: [...state.webShells, action.payload],
        stats: { ...state.stats, totalShellsUploaded: state.stats.totalShellsUploaded + 1 }
      };
    
    case 'UPDATE_WEBSHELL_STATUS':
      return {
        ...state,
        webShells: state.webShells.map(shell =>
          shell.id === action.payload.id
            ? { ...shell, status: action.payload.status, lastChecked: new Date().toISOString() }
            : shell
        ),
      };
    
    case 'REMOVE_WEBSHELL':
      return {
        ...state,
        webShells: state.webShells.filter(shell => shell.id !== action.payload),
      };
    
    case 'UPDATE_STATS':
      return {
        ...state,
        stats: { ...state.stats, ...action.payload },
      };
    
    case 'UPDATE_CONFIG':
      return {
        ...state,
        config: { ...state.config, ...action.payload },
      };
    
    case 'SET_CHECKING':
      return { ...state, isChecking: action.payload };
    
    case 'SET_EXTRACTING':
      return { ...state, isExtracting: action.payload };
    
    case 'RESET_RESULTS':
      return {
        ...state,
        checkResults: [],
        webShells: [],
        stats: { ...initialState.stats, totalExtracted: state.stats.totalExtracted },
      };
    
    default:
      return state;
  }
}

const CheckerContext = createContext<{
  state: CheckerState;
  dispatch: React.Dispatch<CheckerAction>;
} | null>(null);

export function CheckerProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(checkerReducer, initialState);

  return (
    <CheckerContext.Provider value={{ state, dispatch }}>
      {children}
    </CheckerContext.Provider>
  );
}

export function useChecker() {
  const context = useContext(CheckerContext);
  if (!context) {
    throw new Error('useChecker must be used within a CheckerProvider');
  }
  return context;
}