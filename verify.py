from log_parser import LogParser


def verify():
    print("Parsing sample_logs.txt...")
    logs = LogParser.from_file("sample_logs.txt")
    # Force iteration to count
    count = sum(1 for _ in logs)
    print(f"Total valid logs parsed: {count}")

    # Check AND filtering
    errors = logs.filter_all(level="ERROR", container="backend")
    err_count = sum(1 for _ in errors)
    print(f"Error logs: {err_count}")

    # Check OR filtering
    # Match logs that are ERROR level OR have tenant='company_a'
    important = logs.filter_any(level="ERROR", tenant="company_a")
    imp_count = sum(1 for _ in important)
    print(f"Important logs (ERROR or tenant=company_a): {imp_count}")

    # Check stats
    stats = logs.stats()
    print("Stats:")
    print(stats)

    # Check Export
    print("Exporting important logs to 'important_logs.json'...")
    important.export("important_logs.json", format="json")
    print("Done.")

    print("Verification complete.")


if __name__ == "__main__":
    verify()
