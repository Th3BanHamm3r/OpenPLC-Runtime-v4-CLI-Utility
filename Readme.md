# plc4.py - OpenPLC Runtime v4 CLI Utility

## Overview
The **OpenPLC Runtime v4 CLI Utility** is a Python-based Command-Line Interface (CLI) and REST API Client designed for orchestrating, automating, and managing an OpenPLCv4 Runtime environment via CLI. Key features include:
*   User management (create, list)
*   PLC control (start, stop)
*   Program deployment (upload)
*   Status and log retrieval (version, status, logs, compilation status)
*   Plugin interaction

Last tested with Runtime **v4.1.3**

## Installation
1.  **Prerequisites:** Python 3.x is required.
2.  **Dependencies:** The script requires the `requests` library. You can install the dependency using pip.
    ```bash
    pip install requests
    ```

## Usage
See Autonomy Logic's installation guide for [OpenPLCv4 Runtime](https://github.com/Autonomy-Logic/openplc-runtime). After initial setup a user must first be created. This can be done through the [OpenPLC Editor](https://github.com/Autonomy-Logic/openplc-editor) or via: 

```
python3 plc4.py -l <URL> create-user <username> <password>
```
For all other commands after user creation, credentials must be provided.
```
python3 plc4.py [global options] <command> [command options]
```
These options must precede the command:

    -l, --url <full URL path>  Web location of an active Runtime.
    -u, --user <username>      Username for API login.
    -p, --password <password>  Password for API login.
    -h, --help                 Show the help message and exit.

Available Commands:
```
create-user:    Creates a new user account.
                Usage: python3 plc4.py [global options] create-user <username> <password> [role]
get-users:      Lists all registered users.
version:        Gets the OpenPLC version.
start:          Starts the PLC program.
stop:           Stops the PLC program.
status:         Gets the current status of the PLC.
                Options: --stats (Includes detailed timing statistics)
compilation:    Gets the status and logs of the last compilation.
                Usage: python3 plc4.py [global options] compilation [output_file.log]
logs:           Fetches the latest runtime logs.
                Usage: python3 plc4.py [global options] logs [output_file.log]
upload:         Uploads a new PLC program (.zip file).
                Usage: python3 plc4.py [global options] upload <file_path> [--clean]
                Options: --clean (Wipes compilation caches for a clean build)
plugin-command: Sends a command to a specific plugin.
                Usage: python3 plc4.py [global options] plugin-command <plugin_name> <command> ['{"param1":"val1"}']
```

## Scripting Example
This is an example bash script that executes initialization and setup instructions for the OpenPLC Runtime v4. An example `Relay_Blink_PLC.zip` program has been provided.
```bash
PLC_USER="admin"
PLC_PASS="admin"
ULR="https://127.0.0.1:8443"
PROGRAM="Relay_Blink_PLC.zip"

python3 plc4.py -l "$URL" create-user "$PLC_USER" "$PLC_PASS"
python3 plc4.py -l "$URL" -u "$PLC_USER" -p "$PLC_PASS" get-users
python3 plc4.py -l "$URL" -u "$PLC_USER" -p "$PLC_PASS" version
python3 plc4.py -l "$URL" -u "$PLC_USER" -p "$PLC_PASS" upload "$PROGRAM" --clean
sleep 10 # Allow time for server-side compilation
python3 plc4.py -l "$URL" -u "$PLC_USER" -p "$PLC_PASS" start
python3 plc4.py -l "$URL" -u "$PLC_USER" -p "$PLC_PASS" status --stats
```

## Uploading Logic to Runtime
When deploying logic on OpenPLC Runtime v4 the standard method for doing so is through the [OpenPLC Editor](https://github.com/Autonomy-Logic/openplc-editor). However, When deploying via this script the logic must already be compiled specifically for the runtime. 
* Open or create a program in OpenPLC Editor.
* Connect to the Runtime in the program's `Configuration`.
* Run `Clean Build and Upload` in the left tool bar.

In the project's directory, everything in `./build/OpenPLC Runtime v4/src` will become the uploadable `.zip`.\
   ⚠️ Note: If an upload is unsuccessful, the PLC `status` command will show as `EMPTY`. The `compilation` command can also extract the last compile log for error checking/verification if needed.

A typical `program.zip` will look like:

```
program.zip
├── c_blocks.h
├── configuration.cpp
├── debug-map.json
├── defines.h
├── generated.hpp
├── generated_debug.cpp
├── plc.xml
├── pou_MAIN.cpp
├── pou_RELAY_CONTROLLER.cpp
├── pou_STATE_DISPALY.cpp
├── program.st
├── program.st.map.json
├── conf
│   └── ethercat.json
└── strucpp_runtime
    └── include
        ├── debug_dispatch.hpp
        ├── debug_table.hpp
        ├── iec_array.hpp
        ...
```