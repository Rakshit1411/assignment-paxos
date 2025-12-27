# Take-Home Coding Challenge: CloudWatch Log Analyzer
## Overview
We want you to build a log parsing and querying library for analyzing AWS CloudWatch logs from a Kubernetes-based application. This challenge tests your ability to work with structured data, design clean APIs, and handle real-world messiness.

## Background
You're building a debugging tool for engineers working with a microservices application running on Kubernetes. The application logs to AWS CloudWatch, which wraps application log messages in JSON metadata. Engineers need a better way to query and analyze these logs during incident response.

## Time Limit
We would like you to complete this challenge within 2 hours. We recognize you probably won't finish every aspect of this challenge in that time. We've included space in the documentation template (TEMPLATE_FOR_YOUR_README.md) for you to explain what you prioritized and why, and what you do next if you had more time.

## Language
We would like you to complete this challenge in Python if at all possible. A large majority of our codebase is in Python, and we'd like you to demonstrate your fluency with the language. If you are unable to complete the challenge in Python, then please complete it in a language you are comfortable with and document your decision to do so and how you would navigate our pythonic codebase.

## Contents
Below are:
1. Design requirements
2. Sample Data
3. Deliverables, submission guidelines, and evaluation criteria

## Design Requirements
### 1. Parse CloudWatch Logs
Create a parser that can:
- Read JSON log entries from a file **WITHOUT** loading the whole file in to memory.
  --- We need to support files that are too large for us to (efficiently) load into memory. Please implement a lazy / iterator based solution.
  --- In particular, let's aim to process a file w/ >100k lines with at most 75mb of memory usage
  ---- In OS X, you can use the "time" command to measure memory usage.
        First, set TIMEFMT=$'\nreal\t%E\nuser\t%U\nsys\t%S\nmax RSS\t%M KB'
        Then, you can run "time python3 my_program.py"
- Extract metadata: timestamp, pod name, namespace, container name
- Parse the application log message to identify:
  - Log level (`INFO`, `ERROR`, `WARNING`, `DEBUG`)
  - Component/module (e.g., `app.main`, `app.config`)
  - Key-value pairs commonly found in logs (e.g., `tenant=company_a`, `case_id=abc-123`)
- Allow for "or" filters; e.g. show me all logs matching `(pod_name='A' | case_id='abc' | tenant='company_a')` etc.

### 2. Provide a Query Interface
Design a clean, intuitive API for filtering logs:

```python
from log_parser import LogParser

# Load logs
logs = LogParser.from_file("sample_logs.txt")

# Basic filtering
errors = logs.filter(level="ERROR")
backend_logs = logs.filter(container="backend")
recent = logs.filter(after="2025-10-07T16:00:00Z")

# Chain filters
critical_issues = logs.filter(level="ERROR") \
                      .filter(tenant="company_a") \
                      .filter(after="2025-10-07T10:00:00Z")

# Get statistics
stats = logs.stats()
# Example output:
# {
#   "total": 1000,
#   "by_level": {"INFO": 800, "ERROR": 150, "WARNING": 50},
#   "by_container": {"backend": 600, "message-manager": 400},
#   "time_range": {"start": "2025-10-07T00:00:00Z", "end": "2025-10-07T23:59:59Z"}
# }

# Access parsed logs
for log in errors:
    print(log.timestamp, log.level, log.message)
```

### 3. Handle Real-World Data Issues
In general, your parser should graceuflly handle all sorts of real-world data messiness. This includes, but is not limited to:
- Malformed JSON (invalid syntax, missing fields)
- Missing or null metadata fields
- Various log message formats
- Empty lines or whitespace
- Large files (see above re memory)
- weird/annoying  keys (e.g. "company.a", "company-b", etc)
- other fun surprises :)

**Don't crash on bad data** — skip invalid entries and continue processing.

## Sample Data
### Sample Log Entry

```json
{
  "time": "2025-10-07T16:19:05.771609Z",
  "stream": "stderr",
  "log": "INFO:app.main:Resolved tenant: company_a",
  "kubernetes": {
    "pod_name": "backend-556457bfb4-p89sf",
    "namespace_name": "pax-dev",
    "container_name": "backend"
  }
}
```

We've provided a `sample_logs.txt` file with realistic log entries from a Kubernetes application. The file includes:
- Multiple log levels (INFO, ERROR, WARNING)
- Logs from different containers (backend, message-manager, ocr-processor, etc.)
- Various log message formats
- Some malformed/invalid entries to test error handling
- Real-world patterns like tenant identification, case IDs, retry counts, etc.

Use this file to develop and test your parser. Your solution should handle all entries in this file gracefully.

## Deliverables
Submit the following files:

### 1. `log_parser.py`
Your main implementation. Structure it however you think best, but it should be clean and well-organized.

### 2. `test_log_parser.py`
Unit tests demonstrating your parser works correctly. Include at least:
- Test parsing valid log entries
- Test filtering by various criteria
- Test handling of malformed data
- Test statistics generation
- Test edge cases (empty files, all errors filtered out, etc.)

### 3. `README.md`
Brief documentation including:
- **How to run**: Installation and usage instructions
- **Design decisions**: Why you structured your code this way
- **Assumptions**: What you assumed about the log format
- **Limitations**: Known issues or shortcuts due to time constraints
- **Future improvements**: What you'd add with more time

### Bonus Points (Optional)
If you finish early and want to show off, consider adding:

- **Regex support**: `logs.filter(message_contains=r"error.*timeout")`
- **Multiple output formats**: Export to JSON, CSV, or formatted text
- **Time-window queries**: `logs.filter(last_minutes=30)`

## Evaluation Criteria
We'll evaluate your submission on:
- **Code Quality**: Is your code clean, readable, and well-organized? Good variable names? Clear abstractions?
- **Functionality**: Does it work as specified? Does it handle edge cases?
- **API Design**: Is your API intuitive and easy to use? Good method names?
- **Testing**: Do you have meaningful tests? Good coverage?

## Submission Guidelines
1. **Time limit**: Spend no more than 2 hours on this challenge
3. **Include**: All files listed in Deliverables section
4. **Format**: ZIP file, tarball, or GitHub repository link
5. **Dependencies**: If you use external libraries, include a `requirements.txt`
6. **Send to**: ben@paxoshealth.com

## Questions?
If anything is unclear, make reasonable assumptions and document them in your README. We're interested in seeing how you handle ambiguity.

---

**Good luck! We're excited to see your solution.**