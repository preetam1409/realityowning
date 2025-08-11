import subprocess
import sys
import os
import platform


# Arrays with servers
ntp_servers = [
    "ntp0.ntp-servers.net", "ntp1.ntp-servers.net", "ntp2.ntp-servers.net",
    "ntp3.ntp-servers.net", "ntp4.ntp-servers.net", "ntp5.ntp-servers.net",
    "ntp6.ntp-servers.net"
]

MI_SERVERS = ['161.117.96.161', '20.157.18.26']

# Install dependencies
def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

required_packages = ["requests", "ntplib", "pytz", "urllib3", "icmplib", "colorama", "linecache"]
for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        print(f"Installing package {package}...")
        install_package(package)

os.system('cls' if os.name == 'nt' else 'clear')

import hashlib
import linecache
import random
import time
from datetime import datetime, timezone, timedelta
import ntplib
import pytz
import urllib3
import json
import statistics
from icmplib import ping
from colorama import init, Fore, Style

# Setting color
init(autoreset=True)
col_g = Fore.GREEN  # Green
col_gb = Style.BRIGHT + Fore.GREEN  # Bright green
col_b = Fore.BLUE  # Blue
col_bb = Style.BRIGHT + Fore.BLUE  # Bright blue
col_y = Fore.YELLOW  # Yellow
col_yb = Style.BRIGHT + Fore.YELLOW  # Bright yellow
col_r = Fore.RED  # Red
col_rb = Style.BRIGHT + Fore.RED  # Bright red

#=====================================================

# Version and token number (original code)
#token_number = int(input(col_g + f"[Token line number]: " + Fore.RESET))
#os.system('cls' if os.name == 'nt' else 'clear')

token_number = int(sys.argv)
os.system('cls' if os.name == 'nt' else 'clear')

#=====================================================

scriptversion = "ARU_FHL_v070425"

# Global variables
print(col_yb + f"{scriptversion}_token_#{token_number}:")
print(col_y + f"Checking account status" + Fore.RESET)
token = linecache.getline("token.txt", token_number).strip()
cookie_value = token
feedtime = float(linecache.getline("timeshift.txt", token_number).strip())
feed_time_shift = feedtime
feed_time_shift_1 = feed_time_shift / 1000

# Generates unique device ID
def generate_device_id():
    random_data = f"{random.random()}-{time.time()}"
    device_id = hashlib.sha1(random_data.encode('utf-8')).hexdigest().upper()
    return device_id

# Gets initial Beijing time via NTP
def get_initial_beijing_time():
    client = ntplib.NTPClient()
    beijing_tz = pytz.timezone("Asia/Shanghai")
    for server in ntp_servers:
        try:
            print(col_y + f"\nDetermining current Beijing time" + Fore.RESET)
            response = client.request(server, version=3)
            ntp_time = datetime.fromtimestamp(response.tx_time, timezone.utc)
            beijing_time = ntp_time.astimezone(beijing_tz)
            print(col_g + f"[Beijing time]: " + Fore.RESET + f"{beijing_time.strftime('%Y-%m-%d %H:%M:%S.%f')}")
            return beijing_time
        except Exception as e:
            print(f"Connection error to {server}: {e}")
    print(f"Failed to connect to any NTP servers.")
    return None

# Synchronizes Beijing time
def get_synchronized_beijing_time(start_beijing_time, start_timestamp):
    elapsed = time.time() - start_timestamp
    current_time = start_beijing_time + timedelta(seconds=elapsed)
    return current_time

# Waits until target time considering ping
def wait_until_target_time(start_beijing_time, start_timestamp):
    next_day = start_beijing_time + timedelta(days=1)
    print(col_y + f"\nSubmitting bootloader unlock request" + Fore.RESET)
    print(col_g + f"[Specified offset]: " + Fore.RESET + f"{feed_time_shift:.2f} ms.")
    target_time = next_day.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(seconds=feed_time_shift_1)
    print(col_g + f"[Waiting until]: " + Fore.RESET + f"{target_time.strftime('%Y-%m-%d %H:%M:%S.%f')}")
    print(f"Do not close the window...")
    while True:
        current_time = get_synchronized_beijing_time(start_beijing_time, start_timestamp)
        time_diff = target_time - current_time
        if time_diff.total_seconds() > 1:
            time.sleep(min(1.0, time_diff.total_seconds() - 1))
        elif current_time >= target_time:
            print(f"Time reached: {current_time.strftime('%Y-%m-%d %H:%M:%S.%f')}. Starting requests...")
            break
        else:
            time.sleep(0.0001)

# Checks unlock possibility via API
def check_unlock_status(session, cookie_value, device_id):
    try:
        url = "https://sgp-api.buy.mi.com/bbs/api/global/user/bl-switch/state"
        headers = {
            "Cookie": f"new_bbs_serviceToken={cookie_value};versionCode=500419;versionName=5.4.19;deviceId={device_id};"
        }
        response = session.make_request('GET', url, headers=headers)
        if response is None:
            print(f"[Error] Failed to get unlock status.")
            return False
        response_data = json.loads(response.data.decode('utf-8'))
        response.release_conn()
        if response_data.get("code") == 100004:
            print(f"[Error] Cookie expired, update required!")
            input(f"Press Enter to close...")
            exit()
        data = response_data.get("data", {})
        is_pass = data.get("is_pass")
        button_state = data.get("button_state")
        deadline_format = data.get("deadline_format", "")
        if is_pass == 4:
            if button_state == 1:
                print(col_g + f"[Account status]: " + Fore.RESET + f"application submission is possible.")
                return True
            elif button_state == 2:
                print(col_g + f"[Account status]: " + Fore.RESET + f"application blocked until {deadline_format} (Month/Day).")
                status_2 = input(f"Continue (" + col_b + f"Yes/No" + Fore.RESET + f")?: ")
                if status_2.lower() in ['y', 'yes']:
                    return True
                else:
                    input(f"Press Enter to close...")
                    exit()
            elif button_state == 3:
                print(col_g + f"[Account status]: " + Fore.RESET + f"account created less than 30 days ago.")
                status_3 = input(f"Continue (" + col_b + f"Yes/No" + Fore.RESET + f")?: ")
                if status_3.lower() in ['y', 'yes']:
                    return True
                else:
                    input(f"Press Enter to close...")
                    exit()
        elif is_pass == 1:
            print(col_g + f"[Account status]: " + Fore.RESET + f"application approved, unlock possible until {deadline_format}.")
            input(f"Press Enter to close...")
            exit()
        else:
            print(col_g + f"[Account status]: " + Fore.RESET + f"unknown status.")
            input(f"Press Enter to close...")
            exit()
    except Exception as e:
        print(f"[Status check error] {e}")
        return False

# HTTP request wrapper
class HTTP11Session:
    def __init__(self):
        self.http = urllib3.PoolManager(
            maxsize=10,
            retries=True,
            timeout=urllib3.Timeout(connect=2.0, read=15.0),
            headers={}
        )
    
    def make_request(self, method, url, headers=None, body=None):
        try:
            request_headers = {}
            if headers:
                request_headers.update(headers)
            request_headers['Content-Type'] = 'application/json; charset=utf-8'
            if method == 'POST':
                if body is None:
                    body = '{"is_retry":true}'.encode('utf-8')
                request_headers['Content-Length'] = str(len(body))
            request_headers['Accept-Encoding'] = 'gzip, deflate, br'
            request_headers['User-Agent'] = 'okhttp/4.12.0'
            request_headers['Connection'] = 'keep-alive'
            response = self.http.request(
                method,
                url,
                headers=request_headers,
                body=body,
                preload_content=False
            )
            return response
        except Exception as e:
            print(f"[Network error] {e}")
            return None

def main():
    device_id = generate_device_id()
    session = HTTP11Session()
    if check_unlock_status(session, cookie_value, device_id):
        start_beijing_time = get_initial_beijing_time()
        if start_beijing_time is None:
            print(f"Failed to set initial time. Press Enter to close...")
            input()
            exit()
        start_timestamp = time.time()
        wait_until_target_time(start_beijing_time, start_timestamp)
        url = "https://sgp-api.buy.mi.com/bbs/api/global/apply/bl-auth"
        headers = {
            "Cookie": f"new_bbs_serviceToken={cookie_value};versionCode=500419;versionName=5.4.19;deviceId={device_id};"
        }
        try:
            while True:
                request_time = get_synchronized_beijing_time(start_beijing_time, start_timestamp)
                print(col_g + f"[Request]: " + Fore.RESET + f"Sending request at {request_time.strftime('%Y-%m-%d %H:%M:%S.%f')} (UTC+8)")
                response = session.make_request('POST', url, headers=headers)
                if response is None:
                    continue
                response_time = get_synchronized_beijing_time(start_beijing_time, start_timestamp)
                print(col_g + f"[Response]: " + Fore.RESET + f"Response received at {response_time.strftime('%Y-%m-%d %H:%M:%S.%f')} (UTC+8)")
                try:
                    response_data = response.data
                    response.release_conn()
                    json_response = json.loads(response_data.decode('utf-8'))
                    code = json_response.get("code")
                    data = json_response.get("data", {})
                    if code == 0:
                        apply_result = data.get("apply_result")
                        if apply_result == 1:
                            print(col_g + f"[Status]: " + Fore.RESET + f"Application approved, checking status...")
                            check_unlock_status(session, cookie_value, device_id)
                        elif apply_result == 3:
                            deadline_format = data.get("deadline_format", "Not specified")
                            print(col_g + f"[Status]: " + Fore.RESET + f"Application rejected, limit reached. Try again at {deadline_format} (Month/Day).")
                            input(f"Press Enter to close...")
                            exit()
                        elif apply_result == 4:
                            deadline_format = data.get("deadline_format", "Not specified")
                            print(col_g + f"[Status]: " + Fore.RESET + f"Application rejected, blocked until {deadline_format} (Month/Day).")
                            input(f"Press Enter to close...")
                            exit()
                    elif code == 100001:
                        print(col_g + f"[Status]: " + Fore.RESET + f"Application rejected, request error.")
                        print(col_g + f"[FULL RESPONSE]: " + Fore.RESET + f"{json_response}")
                    elif code == 100003:
                        print(col_g + f"[Status]: " + Fore.RESET + f"Application possibly approved, verifying...")
                        print(col_g + f"[Full response]: " + Fore.RESET + f"{json_response}")
                        check_unlock_status(session, cookie_value, device_id)
                    elif code is not None:
                        print(col_g + f"[Status]: " + Fore.RESET + f"Unknown application status: {code}")
                        print(col_g + f"[Full response]: " + Fore.RESET + f"{json_response}")
                    else:
                        print(col_g + f"[Error]: " + Fore.RESET + f"Response missing required code.")
                        print(col_g + f"[Full response]: " + Fore.RESET + f"{json_response}")
                except json.JSONDecodeError:
                    print(col_g + f"[Error]: " + Fore.RESET + f"Failed to decode JSON response.")
                    print(col_g + f"[Server response]: " + Fore.RESET + f"{response_data}")
                except Exception as e:
                    print(col_g + f"[Response processing error]: " + Fore.RESET + f"{e}")
                    continue
        except Exception as e:
            print(col_g + f"[Request error]: " + Fore.RESET + f"{e}")
            input(f"Press Enter to close...")
            exit()

if __name__ == "__main__":
    main()
