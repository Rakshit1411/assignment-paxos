#  Log Analyzer
Brief description of what your solution does.

## Installation
Example:
```bash
# Install dependencies (if any)
pip3 install -r requirements.txt
```

## Usage
Example:
```python
from log_parser import LogParser

# Load logs from file
logs = LogParser.from_file("sample_logs.txt")

# Filter by log level
errors = logs.filter(level="ERROR")

# Filter by time range
recent = logs.filter(after="2025-10-07T16:00:00Z")

# Filter by container
backend_logs = logs.filter(container="backend")

# Chain filters
critical = logs.filter(level="ERROR").filter(tenant="company_a")

# Get statistics
stats = logs.stats()
print(stats)

# Iterate through results
for log in errors:
    print(f"{log.timestamp} - {log.level} - {log.message}")
```

## Running Tests
Example:
```bash
python3 -m pytest test_log_parser.py
# or
python3 test_log_parser.py
```

## Design Decisions
### Architecture
Explain your main classes/modules and why you structured them that way.

### Key Choices
- **Why X instead of Y**: Explain major technical decisions
- **Data structures**: What you used and why (e.g., lists vs generators)
- **Parsing strategy**: How you extract information from log messages
- **Priority Decisons**: Explain why you chose to implement the features that you did in the time available instead of others, and the relative priority of any additional features you'd want to implement.


## Assumptions
List key assumptions you made.

Example:
- Log files have one JSON object per line
- Timestamps are in ISO 8601 format
- Application logs follow the pattern: `LEVEL:module:message`
- Key-value pairs in messages use `=` separator (e.g., `tenant=company_a`)

## Limitations
Be honest about shortcuts or known issues.

Example:
- Timestamp parsing assumes UTC timezone
- Regex filtering not implemented

## Future Improvements

What would you add with more time.