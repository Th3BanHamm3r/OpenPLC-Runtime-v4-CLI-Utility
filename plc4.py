#!/usr/bin/env python3
import sys
import json
import requests

# Suppress warnings from urllib3 for insecure/self-signed SSL connections
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

BASE_URL = ""
API_URL = ""

def login(session, username, password):
    login_url = f"{API_URL}/login"
    login_payload = {'username': username, 'password': password}
    try:
        print(f"Attempting to log in as '{username}'...")
        response = session.post(login_url, json=login_payload, verify=False, timeout=10)
        if response.status_code == 200:
            access_token = response.json().get('access_token')
            if access_token:
                print("Login successful.")
                session.headers.update({'Authorization': f'Bearer {access_token}'})
                return True
            else:
                print("Error: Login successful, but no access token was provided by the server.", file=sys.stderr)
                return False
        else:
            print(f"Error: Login failed. HTTP {response.status_code}.", file=sys.stderr)
            print("\n HINT: If this is a fresh setup or your credentials are invalid,", file=sys.stderr)
            print("   you must create a user account first using the 'create-user' command.\n", file=sys.stderr)
            try:
                print(response.json(), file=sys.stderr)
            except:
                print(response.text, file=sys.stderr)
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error during login: {e}", file=sys.stderr)
        return False

def make_request(session, method, endpoint, params=None, files=None, json_payload=None, special_codes=None):
    url = f"{API_URL}/{endpoint}"
    if special_codes is None:
        special_codes = []
    try:
        if method.upper() == 'GET':
            response = session.get(url, params=params, verify=False, timeout=10)
        elif method.upper() == 'POST':
            response = session.post(url, params=params, json=json_payload, files=files, verify=False, timeout=30)
        else:
            print(f"Error: Unsupported HTTP method '{method}'", file=sys.stderr)
            return None
        if response.status_code not in special_codes:
            response.raise_for_status()
        if response.text:
            return response.json()
        return {}
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print(f"Error: 401 Unauthorized. Your session may have expired or login failed.", file=sys.stderr)
        else:
            print(f"HTTP Error: {e}", file=sys.stderr)
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to the API: {e}", file=sys.stderr)
        return None


def get_version(session):
    print("Fetching OpenPLC version...")
    response = make_request(session, 'GET', 'version')
    if response:
        print(json.dumps(response, indent=2))

def get_status(session, stats=False):
    print("Fetching PLC status...")
    params = {"include_stats": "true"} if stats else None
    response = make_request(session, 'GET', 'status', params=params)
    if response:
        print(json.dumps(response, indent=2))

def start_plc(session):
    print("Sending START command to PLC...")
    response = make_request(session, 'GET', 'start-plc')
    if response:
        print(json.dumps(response, indent=2))

def stop_plc(session):
    print("Sending STOP command to PLC...")
    response = make_request(session, 'GET', 'stop-plc')
    if response:
        print(json.dumps(response, indent=2))

def upload_program(session, file_path, clean=False):
    print(f"Uploading program '{file_path}'...")
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_path, f, 'application/zip')}
            params = {'clean': '1'} if clean else None
            response = make_request(session, 'POST', 'upload-file', params=params, files=files)
            if response:
                print("Upload response:")
                print(json.dumps(response, indent=2))
    except FileNotFoundError:
        print(f"Error: File not found at '{file_path}'", file=sys.stderr)
    except Exception as e:
        print(f"An error occurred during file upload: {e}", file=sys.stderr)

def create_user(new_user, new_pass, role="user"):
    print(f"Attempting to create new user '{new_user}' with role '{role}'...")
    url = f"{API_URL}/create-user"
    payload = { "username": new_user, "password": new_pass, "role": role }
    try:
        response = requests.post(url, json=payload, verify=False, timeout=10)
        if response.status_code == 201:
            print("User created successfully (201 Created).")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Error: Failed to create user. HTTP {response.status_code}", file=sys.stderr)
            print(f"Response: {response.text}", file=sys.stderr)
    except Exception as e:
        print(f"An error occurred during user creation: {e}", file=sys.stderr)

def get_users(session):
    print("Fetching user list...")
    response = make_request(session, 'GET', 'get-users-info', special_codes=[404])
    if response:
        if isinstance(response, dict) and response.get("msg") == "No users found":
            print("No users found on the server.")
        else:
            print("Found users:")
            print(json.dumps(response, indent=2))

def get_logs(session, file_path):
    print(f"Fetching runtime logs to save to '{file_path}'...")
    response = make_request(session, 'GET', 'runtime-logs')
    if response:
        try:
            with open(file_path, 'w') as f:
                for log_entry in response['runtime-logs']:
                    log_id = log_entry.get('id', 'N/A')
                    level = log_entry.get('level', 'INFO')
                    timestamp = log_entry.get('timestamp', '')
                    message = log_entry.get('message', '')
                    f.write(f"[ID: {log_id}] [{level}] {timestamp}: {message}\n")
            print(f"Successfully saved {len(response['runtime-logs'])} log entries to {file_path}")
        except IOError as e:
            print(f"Error: Could not write to file '{file_path}'. Reason: {e}", file=sys.stderr)
    elif response is not None:
        print("Received Somthing? Dumping raw response:")
        print(json.dumps(response, indent=2))

def get_compilation_status(session, file_path):
    print(f"Fetching compilation status to save to '{file_path}'...")
    response = make_request(session, 'GET', 'compilation-status')
    if response:
        try:
            with open(file_path, 'w') as f:
                f.write(f"Status: {response.get('status', 'N/A')}\n")
                f.write(f"Exit Code: {response.get('exit_code', 'N/A')}\n")
                f.write("---\n")
                logs = response.get('logs', [])
                if logs:
                    for line in logs:
                        f.write(f"{line}\n")
                else:
                    f.write("(No compilation logs found)\n")
            print(f"Successfully saved the most compilation status to {file_path}")
        except IOError as e:
            print(f"Error: Could not write to file '{file_path}'. Reason: {e}", file=sys.stderr)
    elif response is not None:
        print("Received Somthing? Dumping raw response:")
        print(json.dumps(response, indent=2))

def send_plugin_command(session, plugin_name, command, params_str="{}"):
    print(f"Sending command '{command}' to plugin '{plugin_name}'...")
    try:
        params_dict = json.loads(params_str)
    except json.JSONDecodeError:
        print("Error: params must be a valid JSON string.", file=sys.stderr)
        sys.exit(1)
        
    payload = {
        "plugin": plugin_name,
        "command": command,
        "params": params_dict
    }
    response = make_request(session, 'POST', 'plugin-command', json_payload=payload)
    if response is not None:
        print("Plugin response:")
        print(json.dumps(response, indent=2))

def print_help():
    print("""A command-line tool to interact with the OpenPLCv4 Runtime web API.

Usage:
  python3 plc4.py [global options] <command> [command options]

Global Options (must precede the command):
  -l, --url <runtime_URL>    Web location of an active Runtime
  -u, --user <username>      Username for login
  -p, --password <password>  Password for login
  -h, --help                 Show this help message and exit

CRITICAL WARNING:
  If this is a fresh OpenPLC installation, you MUST run the 'create-user'
  command first before attempting to log in or use any other API requests.

Available Commands:
  create-user  Create a new user account.
                 Usage: python3 plc4.py create-user <username> <password> [role]
  get-users    List all registered users.
  version      Get the OpenPLC version.
  start        Start the PLC program.
  stop         Stop the PLC program.
  status       Get the current status of the PLC.
                 Options: --stats   Include detailed timing statistics.
  compilation  Get the status and logs of the last compilation.
                 Usage: python3 plc4.py compilation [output_file.log]
  logs         Fetch the latest runtime logs.
                 Usage: python3 plc_tool.py logs [output_file.log]
  upload       Upload a new PLC program.
                 Usage: python3 plc4.py upload <file_path> [--clean]
                 Options: --clean Wipes compilation caches and performs a
                                  clean recompilation of the PLC program.
  plugin-command  Send a command to a specific plugin.
                    Usage: python3 plc4.py plugin-command <plugin_name> <command> ['{"param1":"val1"}']

Examples:
  python3 plc4.py -l https://192.168.1.50:8443 -u admin -p admin create-user admin admin
  python3 plc4.py -l https://192.168.1.50:8443 -u admin -p admin start
  python3 plc4.py -l https://192.168.1.50:8443 -u admin -p admin upload my_prog.zip --clean
  python3 plc4.py -l https://192.168.1.50:8443 -u admin -p admin plugin-command ethercat status""")

def main():
    global BASE_URL, API_URL
    args = sys.argv[1:]
    if not args or '-h' in args or '--help' in args:
        print_help()
        sys.exit(0)
    username = ''
    password = ''
    url=''
    command = None
    command_args = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ('-l', '--url'):
            if i + 1 < len(args): custom_url = args[i+1]; i += 2;
            else: print("Error: --url requires a target URL argument.", file=sys.stderr); sys.exit(1)
        elif arg in ('-u', '--user'):
            if i + 1 < len(args): username = args[i+1]; i += 2;
            else: print("Error: --user requires an argument.", file=sys.stderr); sys.exit(1)
        elif arg in ('-p', '--password'):
            if i + 1 < len(args): password = args[i+1]; i += 2;
            else: print("Error: --password requires an argument.", file=sys.stderr); sys.exit(1)
        else:
            command = arg.lower()
            command_args = args[i+1:]
            break

    BASE_URL = custom_url.rstrip('/')
    API_URL = f"{BASE_URL}/api"

    if command == 'create-user':
        if len(command_args) < 2:
            print("Error: create-user requires at least <username> and <password>.", file=sys.stderr)
            sys.exit(1)
        create_user(command_args[0], command_args[1], command_args[2] if len(command_args) > 2 else "user")
        sys.exit(0)
        
    if not command:
        print("Error: No command provided.", file=sys.stderr)
        print_help()
        sys.exit(1)

    # Establish authenticated session
    session = requests.Session()
    if not login(session, username, password):
        sys.exit(1)

    # Dispatch commands
    if command == 'version':
        get_version(session)
    elif command == "get-users":
        get_users(session)
    elif command == 'status':
        get_status(session, stats='--stats' in command_args)
    elif command == 'start':
        start_plc(session)
    elif command == 'stop':
        stop_plc(session)
    elif command == 'logs':
        log_file = command_args[0] if command_args else 'openplc_runtime.log'
        get_logs(session, log_file)
    elif command == 'compilation':
        log_file = command_args[0] if command_args else 'compilation.log'
        get_compilation_status(session, log_file)
    elif command == 'upload':
        file_path = next((arg for arg in command_args if arg != '--clean'), None)
        if not file_path:
            print("Error: Missing file path for upload.", file=sys.stderr)
            sys.exit(1)
        upload_program(session, file_path, clean='--clean' in command_args)
    elif command == 'plugin-command':
        if len(command_args) < 2:
            print("Error: plugin-command requires <plugin_name> and <command>.", file=sys.stderr)
            sys.exit(1)
        send_plugin_command(session, command_args[0], command_args[1], command_args[2] if len(command_args) > 2 else "{}")
    else:
        print(f"Error: Unknown command '{command}'", file=sys.stderr)
        print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
