# Server Python Version Checker

This script checks Python versions, OSIPython versions, and Python executables in PATH on servers and saves the results to an XML file.

## Features

- Check local server or remote servers via SSH
- Retrieves 4 pieces of information per server:
  - Hostname
  - Python Version (`python --version`)
  - OSIPython Version (`osipython --version`)
  - Python executables found in PATH
- Appends results to XML file (`Server_Python_Versions.xml` by default)
- Supports both password and key-based SSH authentication

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Check Local Server
```bash
python server_python_checker.py --local
```

### Check Remote Server with Password
```bash
python server_python_checker.py --host 192.168.1.100 --username myuser --password mypassword
```

### Check Remote Server with SSH Key
```bash
python server_python_checker.py --host 192.168.1.100 --username myuser --key-file ~/.ssh/id_rsa
```

### Custom XML Output File
```bash
python server_python_checker.py --local --xml-file custom_output.xml
```

### Custom SSH Port
```bash
python server_python_checker.py --host 192.168.1.100 --username myuser --password mypassword --port 2222
```

## Command Line Arguments

- `--local`: Check the local server
- `--host`: Remote server hostname or IP address
- `--username`: SSH username for remote servers
- `--password`: SSH password for remote servers
- `--key-file`: SSH private key file path for remote servers
- `--port`: SSH port (default: 22)
- `--xml-file`: Output XML file name (default: Server_Python_Versions.xml)

## XML Output Format

The script generates an XML file with the following structure:

```xml
<?xml version='1.0' encoding='utf-8'?>
<ServerPythonVersions generated="2025-09-16T10:30:00.123456">
  <Server checked="2025-09-16T10:30:15.789012">
    <Hostname>server1.example.com</Hostname>
    <PythonVersion>Python 3.9.2</PythonVersion>
    <OSIPythonVersion>OSIPython 1.2.3</OSIPythonVersion>
    <PythonsInPath>/usr/bin/python; /usr/bin/python3; /usr/local/bin/python3.9</PythonsInPath>
  </Server>
</ServerPythonVersions>
```

## Error Handling

The script handles various error conditions gracefully:
- Network connectivity issues
- SSH authentication failures
- Missing commands (python, osipython)
- Command execution timeouts
- File permission issues

Errors are recorded in the XML output for troubleshooting.

## Examples

1. **Check multiple servers**: Run the script multiple times with different `--host` parameters to append data for multiple servers to the same XML file.

2. **Batch processing**: Create a shell script to check multiple servers:
```bash
#!/bin/bash
python server_python_checker.py --host server1.example.com --username admin --key-file ~/.ssh/id_rsa
python server_python_checker.py --host server2.example.com --username admin --key-file ~/.ssh/id_rsa
python server_python_checker.py --host server3.example.com --username admin --key-file ~/.ssh/id_rsa
```

## Notes

- The script appends data to the XML file, so you can run it multiple times to collect information from different servers
- Each server entry includes a timestamp of when it was checked
- The script automatically handles XML formatting and indentation
- SSH host key verification is automatically accepted (uses `AutoAddPolicy`)