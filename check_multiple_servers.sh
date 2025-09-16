#!/bin/bash

# Example script to check multiple servers
# Modify the server details according to your environment

XML_FILE="Server_Python_Versions.xml"

echo "Starting server Python version checks..."
echo "Results will be saved to: $XML_FILE"
echo

# Check local server
echo "Checking local server..."
python3 server_python_checker.py --local --xml-file "$XML_FILE"
echo

# Example remote server checks (uncomment and modify as needed)
# Replace with your actual server details

# echo "Checking server1.example.com..."
# python3 server_python_checker.py --host server1.example.com --username admin --key-file ~/.ssh/id_rsa --xml-file "$XML_FILE"
# echo

# echo "Checking server2.example.com..."
# python3 server_python_checker.py --host server2.example.com --username admin --password your_password --xml-file "$XML_FILE"
# echo

# echo "Checking server3.example.com on port 2222..."
# python3 server_python_checker.py --host server3.example.com --username admin --key-file ~/.ssh/id_rsa --port 2222 --xml-file "$XML_FILE"
# echo

echo "All server checks completed!"
echo "Results saved to: $XML_FILE"
echo
echo "To view the results:"
echo "  cat $XML_FILE"
echo "  # or"
echo "  xmllint --format $XML_FILE"