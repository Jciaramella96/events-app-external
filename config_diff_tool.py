#!/usr/bin/env python3
"""
Config File Matrix Tool

Processes configuration files organized in hostname-based folders and creates
a matrix-style Excel report showing configuration values across different hostnames.
"""

import argparse
import re
import sys
import pandas as pd
from typing import Dict, List, Optional, Set
from pathlib import Path
import glob
import os


def parse_config_file(file_path: str) -> Dict[str, str]:
    """
    Parse a configuration file and extract key-value pairs.
    
    Args:
        file_path: Path to the configuration file
        
    Returns:
        Dictionary of key-value pairs
    """
    config_dict = {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line_num, line in enumerate(file, 1):
                line = line.strip()
                
                # Skip empty lines, lines starting with # or space
                if not line or line.startswith('#') or line.startswith(' '):
                    continue
                
                # Split on first '=' character
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    config_dict[key] = value
                    
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return {}
    except Exception as e:
        print(f"Error reading file '{file_path}': {e}")
        return {}
        
    return config_dict


def find_config_files(base_path: str) -> Dict[str, Dict[str, str]]:
    """
    Find all configuration files in the hostname-based folder structure.
    
    Args:
        base_path: Base path containing server type folders
        
    Returns:
        Dictionary mapping hostname to dict of {filename: filepath}
    """
    hostname_files = {}
    
    # Look for folders in the pattern SERVER_TYPE/hostname
    pattern = os.path.join(base_path, "*", "*")
    folders = glob.glob(pattern)
    
    for folder_path in folders:
        if os.path.isdir(folder_path):
            # Extract hostname from path (last part)
            hostname = os.path.basename(folder_path)
            server_type = os.path.basename(os.path.dirname(folder_path))
            
            # Find all .conf files in this hostname folder
            conf_files = glob.glob(os.path.join(folder_path, "*.conf"))
            
            if conf_files:
                if hostname not in hostname_files:
                    hostname_files[hostname] = {}
                
                for conf_file in conf_files:
                    filename = os.path.basename(conf_file)
                    hostname_files[hostname][filename] = conf_file
    
    return hostname_files


def create_matrix_data(hostname_files: Dict[str, Dict[str, str]]) -> pd.DataFrame:
    """
    Create matrix data with filenames as rows and hostnames as columns.
    
    Args:
        hostname_files: Dictionary mapping hostname to {filename: filepath}
        
    Returns:
        DataFrame with matrix structure
    """
    # Get all unique filenames across all hostnames
    all_filenames = set()
    all_hostnames = list(hostname_files.keys())
    
    for hostname_data in hostname_files.values():
        all_filenames.update(hostname_data.keys())
    
    all_filenames = sorted(list(all_filenames))
    all_hostnames = sorted(all_hostnames)
    
    # Create matrix structure
    matrix_data = []
    
    for filename in all_filenames:
        # Get all config keys from this filename across all hostnames
        all_keys = set()
        hostname_configs = {}
        
        for hostname in all_hostnames:
            if hostname in hostname_files and filename in hostname_files[hostname]:
                config = parse_config_file(hostname_files[hostname][filename])
                hostname_configs[hostname] = config
                all_keys.update(config.keys())
        
        # Create rows for each config key in this file
        for key in sorted(all_keys):
            row = {'File': filename, 'Config_Key': key}
            
            for hostname in all_hostnames:
                if hostname in hostname_configs and key in hostname_configs[hostname]:
                    row[hostname] = hostname_configs[hostname][key]
                else:
                    row[hostname] = ''
            
            matrix_data.append(row)
    
    return pd.DataFrame(matrix_data)


def write_matrix_to_excel(matrix_df: pd.DataFrame, output_path: str, hostname_files: Dict[str, Dict[str, str]]):
    """
    Write matrix data to an Excel file with proper formatting.
    
    Args:
        matrix_df: DataFrame containing the matrix data
        output_path: Path for output Excel file
        hostname_files: Original hostname files mapping for summary
    """
    try:
        # Create Excel writer
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Write matrix to main sheet
            matrix_df.to_excel(writer, sheet_name='Config_Matrix', index=False)
            
            # Create summary sheet
            summary_data = []
            summary_data.append(['Metric', 'Value'])
            summary_data.append(['Total Hostnames', len(hostname_files)])
            summary_data.append(['Total Unique Files', len(matrix_df['File'].unique()) if not matrix_df.empty else 0])
            summary_data.append(['Total Config Keys', len(matrix_df) if not matrix_df.empty else 0])
            summary_data.append(['', ''])
            summary_data.append(['Hostnames Found:', ''])
            
            for hostname in sorted(hostname_files.keys()):
                summary_data.append([f'  {hostname}', f"{len(hostname_files[hostname])} files"])
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False, header=False)
            
            # Format the sheets
            workbook = writer.book
            
            # Format Config_Matrix sheet
            if 'Config_Matrix' in workbook.sheetnames:
                worksheet = workbook['Config_Matrix']
                
                # Auto-adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
                
                # Freeze the first two columns (File and Config_Key)
                worksheet.freeze_panes = worksheet['C2']
            
            # Format Summary sheet
            if 'Summary' in workbook.sheetnames:
                worksheet = workbook['Summary']
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
        
        print(f"Excel matrix report generated: {output_path}")
        print(f"Matrix contains {len(matrix_df)} configuration entries across {len(hostname_files)} hostnames")
        
    except Exception as e:
        print(f"Error writing to Excel file: {e}")
        sys.exit(1)


def main():
    """Main function to run the config matrix tool."""
    parser = argparse.ArgumentParser(
        description="Create a matrix view of configuration files organized by hostname folders",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python config_diff_tool.py /path/to/configs
  python config_diff_tool.py /path/to/configs -o config_matrix.xlsx
  
Expected folder structure:
  base_path/
    ├── APP/
    │   ├── hostname1/
    │   │   ├── config1.conf
    │   │   └── config2.conf
    │   └── hostname2/
    │       ├── config1.conf
    │       └── config2.conf
    └── DB/
        ├── hostname1/
        │   └── db.conf
        └── hostname2/
            └── db.conf

The tool will:
- Parse key=value pairs from each .conf file
- Ignore lines starting with # or space
- Create a matrix with hostnames as columns and config keys as rows
- Show filename in the leftmost column
        """
    )
    
    parser.add_argument('base_path', help='Base path containing hostname folders')
    parser.add_argument('-o', '--output', default='config_matrix.xlsx',
                       help='Output Excel file path (default: config_matrix.xlsx)')
    
    args = parser.parse_args()
    
    # Validate base path exists
    if not Path(args.base_path).exists():
        print(f"Error: Path '{args.base_path}' does not exist.")
        sys.exit(1)
    
    print(f"Scanning for configuration files in: {args.base_path}")
    print()
    
    # Find all config files organized by hostname
    hostname_files = find_config_files(args.base_path)
    
    if not hostname_files:
        print("No configuration files found in the expected folder structure.")
        print("Expected structure: SERVER_TYPE/hostname/*.conf")
        sys.exit(1)
    
    print(f"Found configuration files for {len(hostname_files)} hostnames:")
    for hostname, files in hostname_files.items():
        print(f"  {hostname}: {len(files)} files")
    print()
    
    # Create matrix data
    print("Creating configuration matrix...")
    matrix_df = create_matrix_data(hostname_files)
    
    if matrix_df.empty:
        print("No configuration data found to process.")
        sys.exit(1)
    
    # Write to Excel
    write_matrix_to_excel(matrix_df, args.output, hostname_files)
    
    # Print summary
    print(f"\nProcessing Summary:")
    print(f"  Hostnames processed: {len(hostname_files)}")
    print(f"  Unique files found: {len(matrix_df['File'].unique())}")
    print(f"  Total config entries: {len(matrix_df)}")


if __name__ == "__main__":
    main()