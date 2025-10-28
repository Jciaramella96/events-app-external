#!/usr/bin/env python3
"""
Server Python Audit Script

This script runs locally on each server to check:
1. Hostname
2. Python version (python --version)
3. OSIPython version (osipython --version)
4. Python executables in PATH

Results are saved to Server_Python_Versions.xml and optionally committed to git.

Usage:
    python3 server_python_audit.py [--xml-file filename] [--git-commit] [--git-push]

Deploy this script to multiple servers and run it on each to collect Python version data.
"""

import subprocess
import socket
import xml.etree.ElementTree as ET
import os
import sys
import argparse
from datetime import datetime
from typing import List, Dict


class ServerPythonAuditor:
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
                print(f"Loaded existing XML file: {self.xml_file}")
            except ET.ParseError:
                print(f"Warning: {self.xml_file} is corrupted. Creating new file.")
                self._create_new_xml()
        else:
            print(f"Creating new XML file: {self.xml_file}")
            self._create_new_xml()
    
    def _create_new_xml(self):
        """Create a new XML structure"""
        self.root = ET.Element("ServerPythonVersions")
        self.root.set("generated", datetime.now().isoformat())
        self.tree = ET.ElementTree(self.root)
    
    def _execute_command(self, command: str) -> str:
        """Execute command on local machine"""
        try:
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
                stderr = result.stderr.strip()
                return f"Error: {stderr}" if stderr else f"Error: Command failed with exit code {result.returncode}"
        except subprocess.TimeoutExpired:
            return "Error: Command timed out"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def get_hostname(self) -> str:
        """Get hostname of local machine"""
        try:
            return socket.gethostname()
        except Exception as e:
            return f"Error getting hostname: {str(e)}"
    
    def get_python_version(self) -> str:
        """Get Python version - try python first, then python3"""
        commands = ["python --version", "python3 --version"]
        
        for command in commands:
            result = self._execute_command(command)
            if not result.startswith("Error:"):
                return result
        
        return "Error: Neither python nor python3 found"
    
    def get_osipython_version(self) -> str:
        """Get OSIPython version"""
        return self._execute_command("osipython --version")
    
    def get_pythons_in_path(self) -> str:
        """Get all Python executables in PATH"""
        python_commands = [
            "python", "python3", "python2", 
            "python3.13", "python3.12", "python3.11", "python3.10", 
            "python3.9", "python3.8", "python3.7", "python2.7"
        ]
        
        pythons = []
        for cmd in python_commands:
            result = self._execute_command(f"which {cmd} 2>/dev/null")
            if result and not result.startswith("Error:") and result.strip():
                pythons.append(result.strip())
        
        # Remove duplicates while preserving order
        unique_pythons = []
        for python in pythons:
            if python not in unique_pythons:
                unique_pythons.append(python)
        
        return "; ".join(unique_pythons) if unique_pythons else "No Python executables found in PATH"
    
    def audit_server(self) -> Dict[str, str]:
        """Audit the local server for Python information"""
        print("Auditing local server...")
        
        hostname = self.get_hostname()
        python_version = self.get_python_version()
        osipython_version = self.get_osipython_version()
        pythons_in_path = self.get_pythons_in_path()
        
        print(f"  Hostname: {hostname}")
        print(f"  Python Version: {python_version}")
        print(f"  OSIPython Version: {osipython_version}")
        print(f"  Pythons in PATH: {pythons_in_path}")
        
        return {
            "hostname": hostname,
            "python_version": python_version,
            "osipython_version": osipython_version,
            "pythons_in_path": pythons_in_path
        }
    
    def update_xml_with_server_data(self, server_data: Dict[str, str]):
        """Update XML with server data, replacing existing entry for same hostname or adding new"""
        hostname = server_data["hostname"]
        
        # Check if server already exists in XML
        existing_server = None
        for server in self.root.findall("Server"):
            hostname_elem = server.find("Hostname")
            if hostname_elem is not None and hostname_elem.text == hostname:
                existing_server = server
                break
        
        if existing_server is not None:
            print(f"Updating existing entry for hostname: {hostname}")
            # Update existing server entry
            server_element = existing_server
            # Clear existing data
            for child in list(server_element):
                server_element.remove(child)
        else:
            print(f"Adding new entry for hostname: {hostname}")
            # Create new server entry
            server_element = ET.SubElement(self.root, "Server")
        
        # Set timestamp
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
        print(f"Updated XML file: {self.xml_file}")
    
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
    
    def git_commit_and_push(self, commit_message: str = None, push: bool = False):
        """Commit changes to git and optionally push"""
        if not commit_message:
            hostname = self.get_hostname()
            commit_message = f"Update Python audit data from {hostname} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        try:
            # Check if git repo exists
            result = self._execute_command("git status")
            if result.startswith("Error:"):
                print("Warning: Not in a git repository. Skipping git operations.")
                return False
            
            # Add the XML file
            add_result = self._execute_command(f"git add {self.xml_file}")
            if add_result.startswith("Error:"):
                print(f"Warning: Failed to add {self.xml_file} to git: {add_result}")
                return False
            
            # Check if there are changes to commit
            status_result = self._execute_command("git status --porcelain")
            if not status_result.strip():
                print("No changes to commit.")
                return True
            
            # Commit changes
            commit_result = self._execute_command(f'git commit -m "{commit_message}"')
            if commit_result.startswith("Error:"):
                print(f"Warning: Failed to commit changes: {commit_result}")
                return False
            
            print(f"Successfully committed changes: {commit_message}")
            
            # Push if requested
            if push:
                push_result = self._execute_command("git push")
                if push_result.startswith("Error:"):
                    print(f"Warning: Failed to push changes: {push_result}")
                    return False
                print("Successfully pushed changes to remote repository")
            
            return True
            
        except Exception as e:
            print(f"Error during git operations: {str(e)}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Audit Python versions on local server and save to XML",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 server_python_audit.py
  python3 server_python_audit.py --xml-file custom_audit.xml
  python3 server_python_audit.py --git-commit
  python3 server_python_audit.py --git-commit --git-push
  python3 server_python_audit.py --xml-file audit.xml --git-commit --git-push

Deployment workflow:
  1. Deploy this script to multiple servers
  2. Run on each server: python3 server_python_audit.py --git-commit
  3. Collect results from git repository
        """
    )
    
    parser.add_argument(
        "--xml-file", 
        default="Server_Python_Versions.xml", 
        help="XML output file (default: Server_Python_Versions.xml)"
    )
    
    parser.add_argument(
        "--git-commit", 
        action="store_true", 
        help="Commit changes to git repository"
    )
    
    parser.add_argument(
        "--git-push", 
        action="store_true", 
        help="Push changes to remote git repository (implies --git-commit)"
    )
    
    parser.add_argument(
        "--commit-message", 
        help="Custom git commit message"
    )
    
    args = parser.parse_args()
    
    # If git-push is specified, enable git-commit as well
    if args.git_push:
        args.git_commit = True
    
    print("=" * 60)
    print("SERVER PYTHON AUDIT")
    print("=" * 60)
    
    # Create auditor and run audit
    auditor = ServerPythonAuditor(args.xml_file)
    server_data = auditor.audit_server()
    auditor.update_xml_with_server_data(server_data)
    
    print("\nAudit completed successfully!")
    print(f"Results saved to: {args.xml_file}")
    
    # Git operations if requested
    if args.git_commit:
        print("\nPerforming git operations...")
        success = auditor.git_commit_and_push(args.commit_message, args.git_push)
        if success:
            print("Git operations completed successfully!")
        else:
            print("Git operations completed with warnings.")
    
    print("\n" + "=" * 60)
    print("AUDIT SUMMARY")
    print("=" * 60)
    print(f"Hostname: {server_data['hostname']}")
    print(f"Python Version: {server_data['python_version']}")
    print(f"OSIPython Version: {server_data['osipython_version']}")
    print(f"Pythons in PATH: {server_data['pythons_in_path']}")
    print(f"Results file: {args.xml_file}")
    print("=" * 60)


if __name__ == "__main__":
    main()