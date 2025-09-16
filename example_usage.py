#!/usr/bin/env python3
"""
Example usage of ServerPythonChecker class

This script demonstrates how to use the ServerPythonChecker class
programmatically instead of using the command line interface.
"""

from server_python_checker import ServerPythonChecker

def main():
    # Create an instance of the checker
    checker = ServerPythonChecker("Example_Server_Python_Versions.xml")
    
    # Check local server
    print("Checking local server...")
    local_data = checker.check_local_server()
    checker.append_server_data(local_data)
    
    # Example of checking remote servers (uncomment and modify as needed)
    """
    # Check remote server with password
    remote_data1 = checker.check_remote_server(
        host="192.168.1.100",
        username="admin",
        password="your_password"
    )
    checker.append_server_data(remote_data1)
    
    # Check remote server with SSH key
    remote_data2 = checker.check_remote_server(
        host="192.168.1.101",
        username="admin",
        key_file="/home/user/.ssh/id_rsa"
    )
    checker.append_server_data(remote_data2)
    
    # Check remote server on custom port
    remote_data3 = checker.check_remote_server(
        host="192.168.1.102",
        username="admin",
        password="your_password",
        port=2222
    )
    checker.append_server_data(remote_data3)
    """
    
    print("Data collection complete!")
    print("Check Example_Server_Python_Versions.xml for results")

if __name__ == "__main__":
    main()