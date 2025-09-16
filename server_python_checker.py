#!/usr/bin/env python3
"""
Server Python Version Checker

This script connects to servers and checks:
1. Python version (python --version)
2. OSIPython version (osipython --version)
3. Python executables in PATH
4. Hostname

Results are saved to an XML file called Server_Python_Versions.xml
"""

import subprocess
import socket
import xml.etree.ElementTree as ET
import os
import sys
from datetime import datetime
import argparse
import paramiko
from typing import List, Dict, Optional


class ServerPythonChecker:
    def __init__(self, xml_file: str = "Server_Python_Versions.xml"):
        self.xml_file = xml_file
        self.root = None
        self.tree = None
        self._load_or_create_xml()
    
    def _load_or_create_xml(self):
        """Load existing XML file or create a new one"""
        if os.path.exists(self.xml_file):
            try:
                self.tree = ET.parse(self.xml_file)
                self.root = self.tree.getroot()
            except ET.ParseError:
                print(f"Warning: {self.xml_file} is corrupted. Creating new file.")
                self._create_new_xml()
        else:
            self._create_new_xml()
    
    def _create_new_xml(self):
        """Create a new XML structure"""
        self.root = ET.Element("ServerPythonVersions")
        self.root.set("generated", datetime.now().isoformat())
        self.tree = ET.ElementTree(self.root)
    
    def _execute_command_local(self, command: str) -> str:
        """Execute command on local machine"""
        try:
            # Use shell=True for commands that need shell features like pipes, redirects, etc.
            result = subprocess.run(
                command, 
                shell=True,
                capture_output=True, 
                text=True, 
                timeout=30
            )
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"Error: {result.stderr.strip()}"
        except subprocess.TimeoutExpired:
            return "Error: Command timed out"
        except FileNotFoundError:
            return "Error: Command not found"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _execute_command_remote(self, ssh_client: paramiko.SSHClient, command: str) -> str:
        """Execute command on remote server via SSH"""
        try:
            stdin, stdout, stderr = ssh_client.exec_command(command, timeout=30)
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status == 0:
                return stdout.read().decode().strip()
            else:
                error_msg = stderr.read().decode().strip()
                return f"Error: {error_msg}" if error_msg else "Error: Command failed"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _get_hostname_local(self) -> str:
        """Get hostname of local machine"""
        try:
            return socket.gethostname()
        except Exception as e:
            return f"Error getting hostname: {str(e)}"
    
    def _get_hostname_remote(self, ssh_client: paramiko.SSHClient) -> str:
        """Get hostname of remote server"""
        return self._execute_command_remote(ssh_client, "hostname")
    
    def _get_python_version(self, ssh_client: Optional[paramiko.SSHClient] = None) -> str:
        """Get Python version"""
        # Try python first, then python3
        commands = ["python --version", "python3 --version"]
        
        for command in commands:
            if ssh_client:
                result = self._execute_command_remote(ssh_client, command)
            else:
                result = self._execute_command_local(command)
            
            if not result.startswith("Error:"):
                return result
        
        return "Error: Neither python nor python3 found"
    
    def _get_osipython_version(self, ssh_client: Optional[paramiko.SSHClient] = None) -> str:
        """Get OSIPython version"""
        command = "osipython --version"
        if ssh_client:
            return self._execute_command_remote(ssh_client, command)
        else:
            return self._execute_command_local(command)
    
    def _get_pythons_in_path(self, ssh_client: Optional[paramiko.SSHClient] = None) -> str:
        """Get all Python executables in PATH"""
        # Use which command to find python executables
        python_commands = ["python", "python3", "python2", "python3.13", "python3.12", "python3.11", "python3.10", "python3.9", "python3.8"]
        
        pythons = []
        for cmd in python_commands:
            if ssh_client:
                result = self._execute_command_remote(ssh_client, f"which {cmd} 2>/dev/null || true")
            else:
                result = self._execute_command_local(f"which {cmd} 2>/dev/null || true")
            
            if result and not result.startswith("Error:") and result.strip():
                pythons.append(result.strip())
        
        # Remove duplicates while preserving order
        unique_pythons = []
        for python in pythons:
            if python not in unique_pythons:
                unique_pythons.append(python)
        
        return "; ".join(unique_pythons) if unique_pythons else "No Python executables found in PATH"
    
    def check_local_server(self) -> Dict[str, str]:
        """Check Python versions on local server"""
        print("Checking local server...")
        
        hostname = self._get_hostname_local()
        python_version = self._get_python_version()
        osipython_version = self._get_osipython_version()
        pythons_in_path = self._get_pythons_in_path()
        
        return {
            "hostname": hostname,
            "python_version": python_version,
            "osipython_version": osipython_version,
            "pythons_in_path": pythons_in_path
        }
    
    def check_remote_server(self, host: str, username: str, password: str = None, 
                          key_file: str = None, port: int = 22) -> Dict[str, str]:
        """Check Python versions on remote server via SSH"""
        print(f"Checking remote server: {host}")
        
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            # Connect to the server
            if key_file:
                ssh_client.connect(host, port=port, username=username, key_filename=key_file)
            else:
                ssh_client.connect(host, port=port, username=username, password=password)
            
            hostname = self._get_hostname_remote(ssh_client)
            python_version = self._get_python_version(ssh_client)
            osipython_version = self._get_osipython_version(ssh_client)
            pythons_in_path = self._get_pythons_in_path(ssh_client)
            
            return {
                "hostname": hostname,
                "python_version": python_version,
                "osipython_version": osipython_version,
                "pythons_in_path": pythons_in_path
            }
        
        except Exception as e:
            return {
                "hostname": f"Error connecting to {host}",
                "python_version": f"Error: {str(e)}",
                "osipython_version": f"Error: {str(e)}",
                "pythons_in_path": f"Error: {str(e)}"
            }
        finally:
            ssh_client.close()
    
    def append_server_data(self, server_data: Dict[str, str]):
        """Append server data to XML file"""
        server_element = ET.SubElement(self.root, "Server")
        server_element.set("checked", datetime.now().isoformat())
        
        # Add the four columns as sub-elements
        hostname_elem = ET.SubElement(server_element, "Hostname")
        hostname_elem.text = server_data["hostname"]
        
        python_version_elem = ET.SubElement(server_element, "PythonVersion")
        python_version_elem.text = server_data["python_version"]
        
        osipython_version_elem = ET.SubElement(server_element, "OSIPythonVersion")
        osipython_version_elem.text = server_data["osipython_version"]
        
        pythons_in_path_elem = ET.SubElement(server_element, "PythonsInPath")
        pythons_in_path_elem.text = server_data["pythons_in_path"]
        
        # Save to file
        self._save_xml()
        
        print(f"Added data for server: {server_data['hostname']}")
    
    def _save_xml(self):
        """Save XML tree to file with proper formatting"""
        # Pretty print the XML
        self._indent(self.root)
        self.tree.write(self.xml_file, encoding='utf-8', xml_declaration=True)
    
    def _indent(self, elem, level=0):
        """Add indentation to XML elements for pretty printing"""
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for child in elem:
                self._indent(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i


def main():
    parser = argparse.ArgumentParser(description="Check Python versions on servers")
    parser.add_argument("--local", action="store_true", help="Check local server")
    parser.add_argument("--host", help="Remote server hostname/IP")
    parser.add_argument("--username", help="SSH username")
    parser.add_argument("--password", help="SSH password")
    parser.add_argument("--key-file", help="SSH private key file")
    parser.add_argument("--port", type=int, default=22, help="SSH port (default: 22)")
    parser.add_argument("--xml-file", default="Server_Python_Versions.xml", 
                       help="XML output file (default: Server_Python_Versions.xml)")
    
    args = parser.parse_args()
    
    checker = ServerPythonChecker(args.xml_file)
    
    if args.local:
        # Check local server
        server_data = checker.check_local_server()
        checker.append_server_data(server_data)
    
    elif args.host:
        # Check remote server
        if not args.username:
            print("Error: --username is required for remote servers")
            sys.exit(1)
        
        if not args.password and not args.key_file:
            print("Error: Either --password or --key-file is required for remote servers")
            sys.exit(1)
        
        server_data = checker.check_remote_server(
            args.host, args.username, args.password, args.key_file, args.port
        )
        checker.append_server_data(server_data)
    
    else:
        print("Error: Specify either --local or --host")
        parser.print_help()
        sys.exit(1)
    
    print(f"Results saved to {args.xml_file}")


if __name__ == "__main__":
    main()