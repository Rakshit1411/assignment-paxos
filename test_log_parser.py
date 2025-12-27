import pytest
from log_parser import LogParser


SAMPLE_LOGS = """
{"time":"2025-10-07T16:19:05.771609Z","stream":"stderr","log":"INFO:app.main:Resolved tenant: company_a","kubernetes":{"pod_name":"backend-1","namespace_name":"pax-dev","container_name":"backend"}}
{"time":"2025-10-07T16:20:15+01:00","stream":"stderr","log":"ERROR:app.backend:Failed case_id=123 tenant=company_a","kubernetes":{"pod_name":"backend-1","namespace_name":"pax-dev","container_name":"backend"}}
{"time":"2025-10-07T16:22:00Z","stream":"stderr","log":"WARNING:ocr:Rate limit retry_count=3","kubernetes":{"pod_name":"ocr-1","namespace_name":"pax-dev","container_name":"ocr-processor"}}
{invalid-json}
{"time":"bad-time","log":"INFO:test:msg"}
{"time":"2025-10-07T16:25:00Z","stream":"stderr","log":"INFO:app.auth:User login user_id=u1","kubernetes":{"container_name":"auth"}}
"""


@pytest.fixture
def log_file(tmp_path):
    p = tmp_path / "test_logs.txt"
    p.write_text(SAMPLE_LOGS.strip())
    return str(p)


def test_parse_valid_entries(log_file):
    parser = LogParser(log_file)
    logs = list(parser)
    # 4 valid lines out of 6 (one invalid JSON, one bad time)
    assert len(logs) == 4

    assert logs[0].level == "INFO"
    assert logs[0].component == "app.main"
    assert logs[1].level == "ERROR"
    assert logs[1].kv_pairs["case_id"] == "123"


def test_filtering_level(log_file):
    parser = LogParser.from_file(log_file)
    errors = list(parser.filter_all(level="ERROR"))
    assert len(errors) == 1
    assert errors[0].level == "ERROR"


def test_filtering_container(log_file):
    parser = LogParser.from_file(log_file)
    backend = list(parser.filter_all(container="backend"))
    assert len(backend) == 2


def test_filtering_kv_pairs(log_file):
    parser = LogParser.from_file(log_file)
    tenant_logs = list(parser.filter_all(tenant="company_a"))
    assert len(tenant_logs) == 1
    assert tenant_logs[0].kv_pairs["tenant"] == "company_a"


def test_chaining_filters(log_file):
    parser = LogParser.from_file(log_file)
    results = list(parser.filter_all(level="ERROR").filter_all(tenant="company_a"))
    assert len(results) == 1
    results_empty = list(parser.filter_all(level="INFO").filter_all(tenant="company_a"))
    assert len(results_empty) == 0


def test_stats(log_file):
    parser = LogParser.from_file(log_file)
    stats = parser.stats()
    assert stats["total"] == 4
    assert stats["by_level"]["INFO"] == 2
    assert stats["by_level"]["ERROR"] == 1
    assert stats["by_container"]["backend"] == 2


def test_after_filter(log_file):
    parser = LogParser.from_file(log_file)

    recent = list(parser.filter_all(after="2025-10-07T16:23:00Z"))
    assert len(recent) == 1
    assert recent[0].timestamp.minute == 25


def test_filter_or(log_file):
    parser = LogParser.from_file(log_file)
    # Test OR logic: ERROR level OR container=backend
    # In sample logs:
    # 1. INFO, backend -> Matches container=backend
    # 2. ERROR, backend -> Matches level=ERROR (and container)
    # 3. WARNING, ocr -> Matches neither
    # 4. INFO, auth -> Matches neither

    results = list(parser.filter_any(level="ERROR", container="backend"))
    assert len(results) == 2
    assert results[0].component == "app.main"  # backend
    assert results[1].level == "ERROR"


def test_export_json(log_file, tmp_path):
    parser = LogParser.from_file(log_file)
    out_file = tmp_path / "out.json"
    parser.export(str(out_file), format="json")

    # Read back
    import json

    with open(out_file) as f:
        data = json.load(f)
    assert len(data) == 4
    assert data[0]["level"] == "INFO"


def test_export_csv(log_file, tmp_path):
    parser = LogParser.from_file(log_file)
    out_file = tmp_path / "out.csv"
    parser.export(str(out_file), format="csv")

    with open(out_file) as f:
        lines = f.readlines()
    # header + 4 rows
    assert len(lines) == 5
    assert "timestamp,level" in lines[0]


def test_export_text(log_file, tmp_path):
    parser = LogParser.from_file(log_file)
    out_file = tmp_path / "out.txt"
    parser.export(str(out_file), format="text")

    with open(out_file) as f:
        lines = f.readlines()
    assert len(lines) == 4
    assert "[INFO]" in lines[0]
