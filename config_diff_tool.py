#!/usr/bin/env python3
"""
Config File Matrix Tool

Processes configuration files organized in hostname-based folders and creates
a matrix-style Excel report showing configuration values across different hostnames.
Includes hostname intelligence to identify when differences are only due to hostname numbering.
"""

import argparse
import re
import sys
import pandas as pd
from typing import Dict, List, Optional, Set, Tuple
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


def normalize_hostname(value: str) -> str:
    """
    Normalize hostname by replacing numeric suffixes with a placeholder.
    
    This helps identify when the only difference is hostname numbering.
    Examples:
        apesap-h-koc-1 -> apesap-h-koc-X
        apesap-h-top-2 -> apesap-h-top-X
        server-web-01 -> server-web-X
        db-cluster-03 -> db-cluster-X
    """
    # Pattern to match hostname with numeric suffix (more flexible patterns)
    patterns = [
        r'([a-zA-Z]+-[a-zA-Z]+-[a-zA-Z]+-)\d+$',  # Original pattern: word-word-word-number
        r'([a-zA-Z]+-[a-zA-Z]+-)\d+$',            # word-word-number
        r'([a-zA-Z]+)\d+$',                       # word+number
        r'([a-zA-Z]+-[a-zA-Z]+-[a-zA-Z]+-[a-zA-Z]+-)\d+$'  # word-word-word-word-number
    ]
    
    for pattern in patterns:
        match = re.match(pattern, value)
        if match:
            return match.group(1) + 'X'
    
    return value


def is_hostname_only_difference(value1: str, value2: str) -> bool:
    """
    Check if the only difference between two values is the hostname numbering.
    
    Args:
        value1: First value to compare
        value2: Second value to compare
        
    Returns:
        True if only difference is hostname numbering, False otherwise
    """
    if value1 == value2:
        return False
        
    normalized1 = normalize_hostname(value1)
    normalized2 = normalize_hostname(value2)
    
    return normalized1 == normalized2 and value1 != value2


def analyze_hostname_differences(hostname_configs: Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, List[str]]]:
    """
    Analyze configurations across hostnames to identify hostname-only differences.
    
    Args:
        hostname_configs: Dictionary mapping hostname to config dict
        
    Returns:
        Dictionary with analysis results: {
            'hostname_only_differences': {config_key: [list of hostnames with differences]},
            'significant_differences': {config_key: [list of hostnames with differences]}
        }
    """
    result = {
        'hostname_only_differences': {},
        'significant_differences': {}
    }
    
    if len(hostname_configs) < 2:
        return result
    
    # Get all config keys
    all_keys = set()
    for config in hostname_configs.values():
        all_keys.update(config.keys())
    
    hostnames = list(hostname_configs.keys())
    
    for key in all_keys:
        # Get all values for this key across hostnames
        values = {}
        for hostname in hostnames:
            if hostname in hostname_configs and key in hostname_configs[hostname]:
                values[hostname] = hostname_configs[hostname][key]
        
        if len(values) < 2:
            continue
            
        # Check if all differences are hostname-only
        hostname_only = True
        significant_diff = False
        
        hostnames_with_values = list(values.keys())
        for i in range(len(hostnames_with_values)):
            for j in range(i + 1, len(hostnames_with_values)):
                host1, host2 = hostnames_with_values[i], hostnames_with_values[j]
                val1, val2 = values[host1], values[host2]
                
                if val1 != val2:
                    significant_diff = True
                    if not is_hostname_only_difference(val1, val2):
                        hostname_only = False
        
        if significant_diff:
            if hostname_only:
                result['hostname_only_differences'][key] = hostnames_with_values
            else:
                result['significant_differences'][key] = hostnames_with_values
    
    return result


def find_config_files(base_path: str) -> Dict[str, Dict[str, str]]:
    """
    Find all configuration files in the hostname-based folder structure.
    
    Args:
        base_path: Base path containing server type folders
        
    Returns:
        Dictionary mapping hostname to dict of {filename: filepath}
    """
    hostname_files = {}
    
    # Directories to exclude from scanning (common non-hostname directories)
    excluded_dirs = {
        'node_modules', '.git', '__pycache__', '.venv', 'venv', 
        'env', '.env', 'build', 'dist', 'target', 'logs', 'log',
        'tmp', 'temp', '.cache', 'cache'
    }
    
    # Look for folders in the pattern SERVER_TYPE/hostname
    pattern = os.path.join(base_path, "*", "*")
    folders = glob.glob(pattern)
    
    for folder_path in folders:
        if os.path.isdir(folder_path):
            # Extract hostname from path (last part)
            hostname = os.path.basename(folder_path)
            server_type = os.path.basename(os.path.dirname(folder_path))
            
            # Skip excluded directories
            if server_type in excluded_dirs or hostname in excluded_dirs:
                continue
            
            # Find all .conf files in this hostname folder
            conf_files = glob.glob(os.path.join(folder_path, "*.conf"))
            
            if conf_files:
                if hostname not in hostname_files:
                    hostname_files[hostname] = {}
                
                for conf_file in conf_files:
                    filename = os.path.basename(conf_file)
                    hostname_files[hostname][filename] = conf_file
    
    return hostname_files


def create_matrix_data(hostname_files: Dict[str, Dict[str, str]], enable_hostname_intelligence: bool = True) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """
    Create matrix data with filenames as rows and hostnames as columns.
    
    Args:
        hostname_files: Dictionary mapping hostname to {filename: filepath}
        enable_hostname_intelligence: Whether to enable hostname intelligence analysis
        
    Returns:
        Tuple of (DataFrame with matrix structure, Dictionary with hostname analysis)
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
    hostname_analysis = {}
    
    for filename in all_filenames:
        # Get all config keys from this filename across all hostnames
        all_keys = set()
        hostname_configs = {}
        
        for hostname in all_hostnames:
            if hostname in hostname_files and filename in hostname_files[hostname]:
                config = parse_config_file(hostname_files[hostname][filename])
                hostname_configs[hostname] = config
                all_keys.update(config.keys())
        
        # Analyze hostname differences for this file (if enabled)
        if enable_hostname_intelligence:
            file_analysis = analyze_hostname_differences(hostname_configs)
        else:
            file_analysis = {'hostname_only_differences': {}, 'significant_differences': {}}
        
        # Create rows for each config key in this file
        for key in sorted(all_keys):
            row = {'File': filename, 'Config_Key': key}
            
            # Determine if this config key has hostname-only differences (if enabled)
            if enable_hostname_intelligence:
                difference_type = ''
                if key in file_analysis['hostname_only_differences']:
                    difference_type = 'Hostname-Only'
                elif key in file_analysis['significant_differences']:
                    difference_type = 'Significant'
                else:
                    difference_type = 'Same'
                
                row['Difference_Type'] = difference_type
            
            for hostname in all_hostnames:
                if hostname in hostname_configs and key in hostname_configs[hostname]:
                    row[hostname] = hostname_configs[hostname][key]
                else:
                    row[hostname] = ''
            
            matrix_data.append(row)
            
            # Store analysis for summary (if enabled)
            if enable_hostname_intelligence:
                full_key = f"{filename}:{key}"
                hostname_analysis[full_key] = difference_type
    
    return pd.DataFrame(matrix_data), hostname_analysis


def write_matrix_to_excel(matrix_df: pd.DataFrame, output_path: str, hostname_files: Dict[str, Dict[str, str]], hostname_analysis: Dict[str, str]):
    """
    Write matrix data to an Excel file with proper formatting and hostname intelligence.
    
    Args:
        matrix_df: DataFrame containing the matrix data
        output_path: Path for output Excel file
        hostname_files: Original hostname files mapping for summary
        hostname_analysis: Dictionary with hostname difference analysis
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
            
            # Add hostname intelligence analysis
            if hostname_analysis:
                hostname_only_count = sum(1 for v in hostname_analysis.values() if v == 'Hostname-Only')
                significant_count = sum(1 for v in hostname_analysis.values() if v == 'Significant')
                same_count = sum(1 for v in hostname_analysis.values() if v == 'Same')
                
                summary_data.append(['Hostname Intelligence Analysis:', ''])
                summary_data.append(['  Same across hostnames', same_count])
                summary_data.append(['  Hostname-only differences', hostname_only_count])
                summary_data.append(['  Significant differences', significant_count])
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
                
                # Add conditional formatting for hostname intelligence
                from openpyxl.styles import PatternFill
                hostname_only_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")  # Light yellow
                significant_fill = PatternFill(start_color="FFE6E6", end_color="FFE6E6", fill_type="solid")   # Light red
                
                # Apply formatting based on Difference_Type column
                if 'Difference_Type' in matrix_df.columns:
                    diff_type_col = matrix_df.columns.get_loc('Difference_Type') + 1  # +1 for Excel 1-indexing
                    
                    for row_idx in range(2, len(matrix_df) + 2):  # Skip header row
                        cell_value = worksheet.cell(row=row_idx, column=diff_type_col).value
                        if cell_value == 'Hostname-Only':
                            # Highlight the entire row with light yellow
                            for col_idx in range(1, worksheet.max_column + 1):
                                worksheet.cell(row=row_idx, column=col_idx).fill = hostname_only_fill
                        elif cell_value == 'Significant':
                            # Highlight the entire row with light red
                            for col_idx in range(1, worksheet.max_column + 1):
                                worksheet.cell(row=row_idx, column=col_idx).fill = significant_fill
                
                # Freeze the first three columns (File, Config_Key, Difference_Type)
                worksheet.freeze_panes = worksheet['D2']
            
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
    parser.add_argument('--disable-hostname-intelligence', action='store_true',
                       help='Disable hostname intelligence analysis and highlighting')
    
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
    enable_hostname_intelligence = not args.disable_hostname_intelligence
    if enable_hostname_intelligence:
        print("Creating configuration matrix with hostname intelligence...")
    else:
        print("Creating configuration matrix...")
    matrix_df, hostname_analysis = create_matrix_data(hostname_files, enable_hostname_intelligence)
    
    if matrix_df.empty:
        print("No configuration data found to process.")
        sys.exit(1)
    
    # Write to Excel
    write_matrix_to_excel(matrix_df, args.output, hostname_files, hostname_analysis)
    
    # Print summary
    print(f"\nProcessing Summary:")
    print(f"  Hostnames processed: {len(hostname_files)}")
    print(f"  Unique files found: {len(matrix_df['File'].unique())}")
    print(f"  Total config entries: {len(matrix_df)}")
    
    # Print hostname intelligence summary
    if hostname_analysis:
        hostname_only_count = sum(1 for v in hostname_analysis.values() if v == 'Hostname-Only')
        significant_count = sum(1 for v in hostname_analysis.values() if v == 'Significant')
        same_count = sum(1 for v in hostname_analysis.values() if v == 'Same')
        
        print(f"\nHostname Intelligence Analysis:")
        print(f"  Same across hostnames: {same_count}")
        print(f"  Hostname-only differences: {hostname_only_count}")
        print(f"  Significant differences: {significant_count}")
        
        if hostname_only_count > 0:
            print(f"\nNote: {hostname_only_count} configuration entries differ only by hostname numbering.")
            print("These are highlighted in yellow in the Excel output.")


if __name__ == "__main__":
    main()