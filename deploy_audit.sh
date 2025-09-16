#!/bin/bash

# Example deployment script for server_python_audit.py
# This script shows how you might deploy and run the audit across multiple servers

SCRIPT_NAME="server_python_audit.py"
XML_FILE="Server_Python_Versions.xml"

echo "Server Python Audit Deployment Script"
echo "======================================"

# Example server list - modify with your actual servers
SERVERS=(
    "user@server1.example.com"
    "user@server2.example.com" 
    "user@server3.example.com"
)

echo "Deploying audit script to ${#SERVERS[@]} servers..."

for server in "${SERVERS[@]}"; do
    echo
    echo "Processing server: $server"
    echo "----------------------------"
    
    # Copy the script to the server
    echo "1. Copying script to $server..."
    scp "$SCRIPT_NAME" "$server:~/" || {
        echo "   ERROR: Failed to copy script to $server"
        continue
    }
    
    # Run the audit on the server
    echo "2. Running audit on $server..."
    ssh "$server" "python3 ~/$SCRIPT_NAME --xml-file $XML_FILE --git-commit" || {
        echo "   ERROR: Failed to run audit on $server"
        continue
    }
    
    # Optionally copy results back (if not using git)
    # echo "3. Copying results from $server..."
    # scp "$server:~/$XML_FILE" "${server##*@}_$XML_FILE" || {
    #     echo "   ERROR: Failed to copy results from $server"
    # }
    
    echo "   SUCCESS: Completed audit for $server"
done

echo
echo "======================================"
echo "Deployment completed!"
echo
echo "If using git workflow:"
echo "  - Each server has committed its results to the git repository"
echo "  - Pull the latest changes to see all server results"
echo "  - Check git log for audit commits"
echo
echo "If copying files manually:"
echo "  - Check for *_$XML_FILE files in current directory"
echo "  - Merge results as needed"