# Config File Matrix Tool

A Python tool to process configuration files organized in hostname-based folders and create a matrix-style Excel report showing configuration values across different hostnames.

## Features

- **Hostname-Based Organization**: Processes files in `SERVER_TYPE/hostname/` folder structure
- **Multiple File Types**: Supports `.conf`, `.rc` (key=value format), and `.xml` files
- **Subdirectory Search**: Recursively searches subdirectories like `data_explorer/`, `rc/`, `site/`
- **Matrix View**: Creates Excel output with hostnames as columns and configuration keys as rows
- **File Tracking**: Shows relative file path in the leftmost column
- **Smart Parsing**: 
  - Key-value parsing for `.conf` and `.rc` files (extracts key=value pairs)
  - XML parsing with dot notation flattening (e.g., `server.database.host`)
- **Comment Filtering**: Ignores lines starting with "#" or space in key-value files
- **Excel Output**: Generates a comprehensive Excel report with matrix view and summary
- **Multi-Server Support**: Handles multiple server types (APP, DB, WEB, etc.)

## Installation

1. Ensure you have Python 3.6+ installed
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python config_diff_tool.py /path/to/configs
```

### Specify Custom Output File

```bash
python config_diff_tool.py /path/to/configs -o config_matrix.xlsx
```

### Help

```bash
python config_diff_tool.py --help
```

## Expected Folder Structure

The tool expects configuration files organized in this structure:

```
base_path/
├── APP/
│   ├── hostname1/
│   │   ├── application.conf
│   │   ├── data_explorer/
│   │   │   ├── settings.xml
│   │   │   └── config.xml
│   │   └── rc/
│   │       └── startup.rc
│   ├── hostname2/
│   │   ├── application.conf
│   │   ├── database.conf
│   │   └── site/
│   │       └── web.xml
│   └── hostname3/
│       ├── application.conf
│       └── database.conf
├── DB/
│   ├── hostname1/
│   │   ├── postgres.conf
│   │   └── data_explorer/
│   │       └── database.xml
│   ├── hostname2/
│   │   └── postgres.conf
│   └── hostname3/
│       └── postgres.conf
└── WEB/
    ├── hostname1/
    │   ├── nginx.conf
    │   ├── ssl.conf
    │   └── rc/
    │       └── server.rc
    └── hostname2/
        ├── nginx.conf
        └── ssl.conf
```

## Input File Formats

The tool supports multiple configuration file formats:

### .conf and .rc Files (Key-Value Format)
```
# This is a comment - will be ignored
 This line starts with space - will be ignored

# Valid key-value pairs:
database_host=apesap-h-koc-1
database_port=5432
application_name=MyApp
timeout=30
```

### .xml Files (XML Format)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <database>
        <host>apesap-h-koc-1</host>
        <port>5432</port>
        <ssl enabled="true">
            <cert_path>/etc/ssl/certs/db.crt</cert_path>
        </ssl>
    </database>
    <server host="apesap-h-web-1" port="8080"/>
</configuration>
```

XML files are flattened using dot notation:
- `database.host` = "apesap-h-koc-1"
- `database.port` = "5432"  
- `database.ssl.@enabled` = "true" (attributes use @)
- `database.ssl.cert_path` = "/etc/ssl/certs/db.crt"
- `server.@host` = "apesap-h-web-1"
- `server.@port` = "8080"

## Output

The tool generates an Excel file with two sheets:

### 1. Config_Matrix Sheet
A matrix view with:
- **File**: The source configuration filename (leftmost column)
- **Config_Key**: The configuration parameter name
- **hostname1, hostname2, etc.**: Columns for each hostname showing the value for that configuration key
- Empty cells indicate the configuration key is not present in that hostname's file

### 2. Summary Sheet
Contains overall statistics:
- Total number of hostnames processed
- Total number of unique configuration files
- Total number of configuration entries
- List of all hostnames found with file counts

## Example Output

For the folder structure above, the Excel matrix might look like:

| File           | Config_Key    | hostname1 | hostname2 | hostname3 |
|----------------|---------------|-----------|-----------|-----------|
| application.conf | app_name     | WebApp    | WebApp    | WebApp    |
| application.conf | app_port     | 8080      | 8081      | 8082      |
| application.conf | debug_mode   | false     | true      |           |
| database.conf    | db_host      | db-1      | db-2      | db-3      |
| database.conf    | db_port      | 5432      | 5432      | 5433      |
| logging.conf     | log_level    | INFO      | DEBUG     |           |

## Features in Detail

### Matrix Structure
- Each row represents a configuration key from a specific file
- Each column represents a hostname
- The intersection shows the value of that configuration key for that hostname
- Empty cells indicate the configuration is not present

### File Organization
- Automatically discovers all `.conf`, `.rc`, and `.xml` files in hostname folders and subdirectories
- Searches up to 3 levels deep in subdirectories (e.g., `hostname/data_explorer/settings.xml`)
- Groups configurations by relative file path across all hostnames
- Maintains source file tracking with full path hierarchy for easy identification

### Excel Formatting
- Auto-adjusts column widths for readability
- Freezes the first two columns (File and Config_Key) for easy navigation
- Provides a summary sheet with processing statistics

## Example Usage

```bash
$ python config_diff_tool.py /opt/configs

Scanning for configuration files in: /opt/configs

Found configuration files for 3 hostnames:
  hostname1: 3 files
  hostname2: 3 files
  hostname3: 2 files

Creating configuration matrix...

Excel matrix report generated: config_matrix.xlsx
Matrix contains 15 configuration entries across 3 hostnames

Processing Summary:
  Hostnames processed: 3
  Unique files found: 3
  Total config entries: 15
```

## Error Handling

The tool includes comprehensive error handling for:
- Missing base path
- Invalid folder structure
- File read errors
- Excel write errors
- Empty configuration files

## Requirements

- Python 3.6+
- pandas >= 1.3.0
- openpyxl >= 3.0.0

## License

This tool is provided as-is for configuration file matrix analysis purposes.