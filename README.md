# Config File Diff Tool

A Python tool to compare two configuration files and report differences to an Excel file. The tool is designed to handle configuration files with key-value pairs and intelligently ignore hostname variations.

## Features

- **Key-Value Parsing**: Extracts key-value pairs from lines split by "=" character
- **Comment Filtering**: Ignores lines starting with "#" or space
- **Hostname Intelligence**: Ignores differences that are only hostname variations (e.g., `apesap-h-koc-1` vs `apesap-h-koc-2`)
- **Excel Output**: Generates a comprehensive Excel report with differences and summary
- **Detailed Reporting**: Shows what's missing in each file and what values have changed

## Installation

1. Ensure you have Python 3.6+ installed
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python config_diff_tool.py file1.conf file2.conf
```

### Specify Custom Output File

```bash
python config_diff_tool.py file1.conf file2.conf -o my_differences.xlsx
```

### Help

```bash
python config_diff_tool.py --help
```

## Input File Format

The tool expects configuration files with key-value pairs in this format:

```
# This is a comment - will be ignored
 This line starts with space - will be ignored

# Valid key-value pairs:
database_host=apesap-h-koc-1
database_port=5432
application_name=MyApp
timeout=30
```

## Hostname Intelligence

The tool automatically recognizes and ignores hostname variations such as:
- `apesap-h-koc-1` vs `apesap-h-koc-2`
- `apesap-h-top-1` vs `apesap-h-top-2`
- `server-web-1` vs `server-web-2`

This is useful when comparing configuration files from different environments where only the hostname numbers differ.

## Output

The tool generates an Excel file with two sheets:

### 1. Differences Sheet
Contains columns:
- **Key**: The configuration key
- **File1_Value**: Value from the first file (or `<MISSING>` if not present)
- **File2_Value**: Value from the second file (or `<MISSING>` if not present)
- **Difference_Type**: Type of difference (Missing in File1, Missing in File2, or Value Changed)

### 2. Summary Sheet
Contains overall statistics:
- File paths being compared
- Total number of differences
- Count of keys missing in each file
- Count of value changes

## Examples

### Example 1: Basic Configuration Files

**file1.conf:**
```
database_host=apesap-h-koc-1
database_port=5432
app_name=WebApp
debug_mode=false
```

**file2.conf:**
```
database_host=apesap-h-koc-2
database_port=3306
app_name=WebApp
ssl_enabled=true
```

**Output:**
- `database_host` difference ignored (hostname variation)
- `database_port` reported as changed (5432 → 3306)
- `app_name` not reported (identical)
- `debug_mode` reported as missing in File2
- `ssl_enabled` reported as missing in File1

### Example 2: Running the Tool

```bash
$ python config_diff_tool.py file1.conf file2.conf

Comparing files:
  File 1: file1.conf
  File 2: file2.conf

Parsing configuration files...
File 1: 4 key-value pairs found
File 2: 4 key-value pairs found

Comparing configurations...
Found 3 differences (excluding hostname-only changes)

Excel report generated: config_differences.xlsx
Total differences found: 3

Difference Summary:
  database_port: '5432' -> '3306'
  debug_mode: 'false' -> '<MISSING>'
  ssl_enabled: '<MISSING>' -> 'true'
```

## Error Handling

The tool includes comprehensive error handling for:
- Missing input files
- File read errors
- Invalid file formats
- Excel write errors

## Requirements

- Python 3.6+
- pandas >= 1.3.0
- openpyxl >= 3.0.0

## License

This tool is provided as-is for configuration file comparison purposes.