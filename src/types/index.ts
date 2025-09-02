export interface ComboLine {
  url: string;
  username: string;
  password: string;
}

export interface CheckResult {
  url: string;
  username: string;
  password: string;
  cmsType: string;
  status: 'valid' | 'invalid' | 'error';
  timestamp: string;
}

export interface WebShell {
  id: string;
  url: string;
  status: 'active' | 'inactive' | 'checking' | 'error';
  lastChecked: string;
  uploadedAt: string;
}

export interface Stats {
  totalExtracted: number;
  totalChecked: number;
  totalFailed: number;
  totalValid: number;
  totalInvalid: number;
  totalShellsUploaded: number;
  activeThreads: number;
}

export interface CheckerConfig {
  timeout: number;
  removeDuplicates: boolean;
  activeChecker: boolean;
  useProxy: boolean;
  maxThreads: number;
}

export type CMSType = 'WordPress' | 'Joomla' | 'cPanel' | 'WHM' | 'DirectAdmin' | 'Plesk' | 'Moodle' | 'Unknown';