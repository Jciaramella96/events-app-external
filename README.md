# Server Python Audit Script

A single, self-contained Python script that audits Python installations on servers and saves results to XML. Designed for deployment to multiple servers with git integration for centralized result collection.

## Features

- **Single Script**: No external dependencies, runs with standard Python 3
- **Local Execution**: Runs locally on each server (no SSH complexity)
- **Complete Audit**: Collects 4 key pieces of information per server:
  - Hostname
  - Python Version (`python --version` or `python3 --version`)
  - OSIPython Version (`osipython --version`)
  - Python executables found in PATH
- **XML Output**: Creates/updates XML file with audit results
- **Git Integration**: Automatically commits results to git repository
- **Smart Updates**: Updates existing entries for same hostname or adds new ones

## Installation

No installation required! The script uses only Python standard library modules.

## Usage

### Basic Usage
```bash
python3 server_python_audit.py
```

### Custom XML File
```bash
python3 server_python_audit.py --xml-file custom_audit.xml
```

### With Git Integration
```bash
python3 server_python_audit.py --git-commit
```

### With Git Commit and Push
```bash
python3 server_python_audit.py --git-commit --git-push
```

### Custom Commit Message
```bash
python3 server_python_audit.py --git-commit --commit-message "Monthly Python audit"
```

## Command Line Arguments

- `--xml-file`: Output XML file name (default: Server_Python_Versions.xml)
- `--git-commit`: Commit changes to git repository
- `--git-push`: Push changes to remote git repository (implies --git-commit)
- `--commit-message`: Custom git commit message

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

## Deployment Workflow

### Recommended Git-Based Workflow

1. **Setup**: Initialize a git repository in a shared location
2. **Deploy**: Copy `server_python_audit.py` to each server
3. **Execute**: Run the script on each server with `--git-commit`
4. **Collect**: Pull changes from the git repository to see all results

```bash
# On each server:
python3 server_python_audit.py --git-commit

# On management machine:
git pull  # Get all server results
```

### Alternative File-Based Workflow

1. **Deploy**: Copy script to servers
2. **Execute**: Run script on each server
3. **Collect**: Copy XML files back to central location

```bash
# On each server:
python3 server_python_audit.py --xml-file $(hostname)_audit.xml

# Copy files back for analysis
```

## Examples

### Single Server Audit
```bash
python3 server_python_audit.py
```

### Production Deployment with Git
```bash
# Deploy to servers and run with git integration
for server in server1 server2 server3; do
    scp server_python_audit.py $server:~/
    ssh $server "cd /path/to/git/repo && python3 ~/server_python_audit.py --git-commit"
done

# Collect results
git pull
```

### Scheduled Audits
```bash
# Add to crontab for monthly audits
0 0 1 * * cd /path/to/git/repo && python3 /path/to/server_python_audit.py --git-commit --git-push
```