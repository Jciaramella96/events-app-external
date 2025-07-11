#!/usr/bin/env python3
"""
Config File Diff Tool

Compares two configuration files and reports differences to an Excel file.
Ignores comments, empty lines, and hostname variations.
"""

import argparse
import re
import sys
import pandas as pd
from typing import Dict, Tuple, List, Optional
from pathlib import Path


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
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file '{file_path}': {e}")
        sys.exit(1)
        
    return config_dict


def normalize_hostname(value: str) -> str:
    """
    Normalize hostname by replacing numeric suffixes with a placeholder.
    
    This helps identify when the only difference is hostname numbering.
    Examples:
        apesap-h-koc-1 -> apesap-h-koc-X
        apesap-h-top-2 -> apesap-h-top-X
    """
    # Pattern to match hostname with numeric suffix
    hostname_pattern = r'([a-zA-Z]+-[a-zA-Z]+-[a-zA-Z]+-)\d+$'
    match = re.match(hostname_pattern, value)
    
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
    normalized1 = normalize_hostname(value1)
    normalized2 = normalize_hostname(value2)
    
    return normalized1 == normalized2 and value1 != value2


def compare_configs(config1: Dict[str, str], config2: Dict[str, str]) -> List[Dict[str, str]]:
    """
    Compare two configuration dictionaries and find differences.
    
    Args:
        config1: First configuration dictionary
        config2: Second configuration dictionary
        
    Returns:
        List of dictionaries representing differences
    """
    differences = []
    
    # Get all unique keys from both configs
    all_keys = set(config1.keys()) | set(config2.keys())
    
    for key in sorted(all_keys):
        value1 = config1.get(key, '<MISSING>')
        value2 = config2.get(key, '<MISSING>')
        
        # If values are different
        if value1 != value2:
            # Check if it's only a hostname difference
            if value1 != '<MISSING>' and value2 != '<MISSING>':
                if is_hostname_only_difference(value1, value2):
                    continue  # Skip hostname-only differences
            
            # Record the difference
            differences.append({
                'Key': key,
                'File1_Value': value1,
                'File2_Value': value2,
                'Difference_Type': get_difference_type(value1, value2)
            })
    
    return differences


def get_difference_type(value1: str, value2: str) -> str:
    """
    Determine the type of difference between two values.
    
    Args:
        value1: First value
        value2: Second value
        
    Returns:
        String describing the type of difference
    """
    if value1 == '<MISSING>':
        return 'Missing in File1'
    elif value2 == '<MISSING>':
        return 'Missing in File2'
    else:
        return 'Value Changed'


def write_to_excel(differences: List[Dict[str, str]], file1_path: str, file2_path: str, output_path: str):
    """
    Write differences to an Excel file.
    
    Args:
        differences: List of difference dictionaries
        file1_path: Path to first file
        file2_path: Path to second file
        output_path: Path for output Excel file
    """
    try:
        # Create DataFrame
        df = pd.DataFrame(differences)
        
        # Create Excel writer
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Write differences to main sheet
            df.to_excel(writer, sheet_name='Differences', index=False)
            
            # Create summary sheet
            summary_data = {
                'Metric': [
                    'File 1 Path',
                    'File 2 Path',
                    'Total Differences',
                    'Missing in File 1',
                    'Missing in File 2',
                    'Value Changes'
                ],
                'Value': [
                    file1_path,
                    file2_path,
                    len(differences),
                    len([d for d in differences if d['Difference_Type'] == 'Missing in File1']),
                    len([d for d in differences if d['Difference_Type'] == 'Missing in File2']),
                    len([d for d in differences if d['Difference_Type'] == 'Value Changed'])
                ]
            }
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Format the sheets
            workbook = writer.book
            
            # Format Differences sheet
            if 'Differences' in workbook.sheetnames:
                worksheet = workbook['Differences']
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
        
        print(f"Excel report generated: {output_path}")
        print(f"Total differences found: {len(differences)}")
        
    except Exception as e:
        print(f"Error writing to Excel file: {e}")
        sys.exit(1)


def main():
    """Main function to run the config diff tool."""
    parser = argparse.ArgumentParser(
        description="Compare two configuration files and report differences to Excel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python config_diff_tool.py file1.conf file2.conf
  python config_diff_tool.py file1.conf file2.conf -o differences.xlsx
  
The tool will:
- Parse key=value pairs from each line
- Ignore lines starting with # or space
- Ignore hostname-only differences (e.g., server-1 vs server-2)
- Generate an Excel report with differences and summary
        """
    )
    
    parser.add_argument('file1', help='Path to first configuration file')
    parser.add_argument('file2', help='Path to second configuration file')
    parser.add_argument('-o', '--output', default='config_differences.xlsx',
                       help='Output Excel file path (default: config_differences.xlsx)')
    
    args = parser.parse_args()
    
    # Validate input files exist
    if not Path(args.file1).exists():
        print(f"Error: File '{args.file1}' does not exist.")
        sys.exit(1)
    
    if not Path(args.file2).exists():
        print(f"Error: File '{args.file2}' does not exist.")
        sys.exit(1)
    
    print(f"Comparing files:")
    print(f"  File 1: {args.file1}")
    print(f"  File 2: {args.file2}")
    print()
    
    # Parse configuration files
    print("Parsing configuration files...")
    config1 = parse_config_file(args.file1)
    config2 = parse_config_file(args.file2)
    
    print(f"File 1: {len(config1)} key-value pairs found")
    print(f"File 2: {len(config2)} key-value pairs found")
    print()
    
    # Compare configurations
    print("Comparing configurations...")
    differences = compare_configs(config1, config2)
    
    if differences:
        print(f"Found {len(differences)} differences (excluding hostname-only changes)")
        
        # Write to Excel
        write_to_excel(differences, args.file1, args.file2, args.output)
        
        # Print summary
        print("\nDifference Summary:")
        for diff in differences[:10]:  # Show first 10 differences
            print(f"  {diff['Key']}: '{diff['File1_Value']}' -> '{diff['File2_Value']}'")
        
        if len(differences) > 10:
            print(f"  ... and {len(differences) - 10} more differences (see Excel file)")
            
    else:
        print("No significant differences found (ignoring hostname variations)")
        
        # Still create Excel file with empty results
        write_to_excel([], args.file1, args.file2, args.output)


if __name__ == "__main__":
    main()