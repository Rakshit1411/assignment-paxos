# CloudWatch Log Analyzer

A Python library for parsing and filtering AWS CloudWatch logs efficiently. This tool is designed to handle large log files with low memory footprint and robustness against malformed data.

## Installation

```bash
# Install dependencies
pip3 install -r requirements.txt
```

## Usage

```python
from log_parser import LogParser

# Load logs from file
logs = LogParser.from_file("sample_logs.txt")

# Filter by log level
errors = logs.filter_all(level="ERROR")

# Filter by time range
recent = logs.filter_all(after="2025-10-07T16:00:00Z")

# Filter by relative time window
last_hour = logs.filter_all(last_minutes=60)

# Filter by container
backend_logs = logs.filter_all(container="backend")

# Chain filters (AND logic)
critical = logs.filter_all(level="ERROR").filter_all(tenant="company_a")

# OR filters (Match ANY)
# Example: Match logs that are either ERROR level OR have tenant 'company_a'
important = logs.filter_any(level="ERROR", tenant="company_a")

# Get statistics
stats = logs.stats()
print(stats)

# Export logs
# Supported formats: json, csv, text
important.export("filtered_logs.json", format="json")
important.export("filtered_logs.csv", format="csv")
```

### Supported Filter Keys
The following keys have special handling in `filter_all` and `filter_any`:
- **Time**: `start`, `after`, `end`, `before` (ISO 8601 strings), `last_minutes` (float).
- **Metadata**: `level`, `container`, `pod`, `namespace`.
- **Custom**: Any other key (e.g., `tenant`, `case_id`) will be matched against `key=value` pairs extracted from the log message.

```python
# Iterate through results
for log in errors:
    print(f"{log.timestamp} - {log.level} - {log.message}")
```

## Running Tests

To run the provided unit tests:

```bash
python3 -m pytest test_log_parser.py
```

## Design Decisions

### Architecture
- **`LogEntry` Dataclass**: Provides a structured representation of a log line with typed fields (`timestamp`, `level`, `metadata`, etc.) for easy access and autocomplete support.
- **`LogParser` Class**: The main entry point. It handles file reading and filtering.
- **Lazy Loading**: The core design principle is to never load the entire file into memory. The `__iter__` method yields one `LogEntry` at a time. Filters are stored and applied during iteration.

### Key Choices
- **Generator Pattern**: Used `yield` to implement lazy loading. This ensures memory usage stays constant regardless of file size, meeting the <75MB requirement.
- **Regex Parsing**: Used regex to extract log levels, components, and key-value pairs (`key=value`) from the unstructured message part.
- **Chained Filtering**: The `filter_all()` and `filter_any()` methods return a new `LogParser` instance with the new filter condition added to the list. This allows for flexible chaining of both AND/OR conditions.
- **`python-dateutil`**: Chosen for date parsing because it handles a wide variety of ISO 8601 variations (like `Z`, `+00:00`, etc.) much better than the standard `datetime.strptime`.

### Assumptions
- Log files contain one valid JSON object per line.
- Invalid JSON lines should be skipped without raising errors.
- Timestamps are under the `"time"` key.
- Log messages loosely follow `LEVEL:component:message` format, but the parser is resilient if they don't.
- Key-value pairs in messages are space-separated `key=value`.

## Limitations
- **File Re-reading**: Because of lazy loading, iterating over the logs multiple times (e.g., once for stats, once for printing) requires reading the file from disk each time. This trades IO for Memory.
- **Nested Querying**: The current API supports a linear chain of AND/OR blocks. It does not yet support arbitrarily deep nested parenthetical logic (e.g. `(A OR B) AND (C OR D)` is supported, but `A OR (B AND C)` is not directly supported in a single call).

## Future Improvements
- **Regex Filtering**: Add support for `message_match=r"..."`.
- **Indexing**: For very large files, building a lightweight index of byte offsets for timestamps could speed up time-based queries without full scans.
- **Complex Query Language**: Improve filtering logic to support nested AND/OR combinations and a string-based query language (e.g. `level=ERROR AND (tenant=A OR tenant=B)`).
- **Compressed Files**: Transparent support for reading `.log.gz` files.
- **CLI Tool**: Wrapper to use the library directly from the command line.
