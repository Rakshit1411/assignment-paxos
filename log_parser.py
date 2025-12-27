import json
import re
import csv
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Iterator, List
from dateutil import parser as date_parser


@dataclass
class LogEntry:
    """
    A dataclass representing a log entry.
    """

    timestamp: datetime
    level: str
    component: str
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    kv_pairs: Dict[str, Any] = field(default_factory=dict)


class LogParser:
    """
    A class for parsing and filtering log files.
    """

    def __init__(
        self, file_path: str, filters: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """
        Initialize a LogParser instance.
        """
        self.file_path = file_path
        self._filters = filters if filters is not None else []

    @classmethod
    def from_file(cls, file_path: str) -> "LogParser":
        """
        Create a LogParser instance from a file.
        """
        return cls(file_path)

    def filter_all(self, **kwargs) -> "LogParser":
        """
        Returns a new LogParser instance with the additional filters.
        Implements AND logic: existing filters AND new filters must match.
        The constraints within 'kwargs' are also ANDed together.
        """
        current_filters = self._filters.copy()
        current_filters.append(kwargs)
        return LogParser(self.file_path, current_filters)

    def filter_any(self, **kwargs) -> "LogParser":
        """
        Returns a new LogParser instance with the additional filters.
        Implements OR logic for the constraints provided in 'kwargs'.
        The log must match AT LEAST ONE of the conditions in 'kwargs'.
        This entire block is ANDed with previous filters (chaining).
        """
        current_filters = self._filters.copy()
        # Use a tuple ('OR', dict) to distinguish OR groups
        current_filters.append(("OR", kwargs))
        return LogParser(self.file_path, current_filters)

    def _matches_filters(self, entry: LogEntry) -> bool:
        """
        Check if a log entry matches all the filters.
        """
        if not self._filters:
            return True

        for filter_item in self._filters:
            if isinstance(filter_item, tuple) and filter_item[0] == "OR":
                # OR Logic: Match ANY condition in the dictionary
                or_criteria = filter_item[1]
                if not any(
                    self._check_condition(entry, k, v) for k, v in or_criteria.items()
                ):
                    return False
            else:
                # AND Logic (default for dict): Match ALL conditions
                # filter_item is a dict here
                if not all(
                    self._check_condition(entry, k, v) for k, v in filter_item.items()
                ):
                    return False
        return True

    def _check_condition(self, entry: LogEntry, key: str, value: Any) -> bool:
        """
        Check if a log entry matches a single filter condition.
        """
        if key == "level":
            return entry.level == value
        elif key == "container":
            return entry.metadata.get("kubernetes", {}).get("container_name") == value
        elif key == "pod_name":
            return entry.metadata.get("kubernetes", {}).get("pod_name") == value
        elif key == "namespace":
            return entry.metadata.get("kubernetes", {}).get("namespace_name") == value
        elif key == "start" or key == "after":
            # value is ISO string
            try:
                dt = date_parser.parse(value)
                return entry.timestamp >= dt
            except Exception:
                return False
        elif key == "end" or key == "before":
            try:
                dt = date_parser.parse(value)
                return entry.timestamp <= dt
            except Exception:
                return False
        elif key == "last_minutes":
            try:
                cutoff = datetime.now(timezone.utc) - timedelta(minutes=float(value))
                return entry.timestamp >= cutoff
            except Exception:
                return False

        if key in entry.kv_pairs:
            return entry.kv_pairs[key] == value

        return False

    def __iter__(self) -> Iterator[LogEntry]:
        """
        Iterate over the log entries.
        """
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                # iterating line by line
                for line in f:
                    # skipping empty lines
                    if not line.strip():
                        continue

                    entry = self._parse_line(line)
                    if entry:
                        if self._matches_filters(entry):
                            yield entry

        except FileNotFoundError:
            return

    @staticmethod
    def _parse_line(line: str) -> Optional[LogEntry]:
        """
        Parse a log line.
        """
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            # invalid json
            return None

        if not isinstance(data, dict):
            # invalid json
            return None

        if "time" not in data or "log" not in data:
            # invalid log
            return None

        raw_time = data.get("time")
        if not raw_time:
            # invalid log
            return None

        try:
            timestamp = date_parser.parse(raw_time)
        except (ValueError, TypeError):
            # invalid timestamp
            return None

        raw_log = data.get("log", "")

        level = "UNKNOWN"
        component = "UNKNOWN"
        message = raw_log

        match = re.match(r"^([A-Z]+):([\w\.]+):(.*)$", raw_log)
        if match:
            level = match.group(1)
            component = match.group(2)
            message = match.group(3).strip()
        kv_pairs = {}

        kv_matches = re.finditer(r"([\w\.-]+)=([^\s]+)", message)
        for m in kv_matches:
            k, v = m.groups()
            kv_pairs[k] = v
        return LogEntry(
            timestamp=timestamp,
            level=level,
            component=component,
            message=message,
            metadata=data,
            kv_pairs=kv_pairs,
        )

    def stats(self) -> Dict[str, Any]:
        """
        Get statistics about the log entries.
        """
        count = 0
        by_level = {}
        by_container = {}
        min_time = None
        max_time = None

        for entry in self:
            count += 1

            # Level stats
            by_level[entry.level] = by_level.get(entry.level, 0) + 1

            # Container stats
            k8s = entry.metadata.get("kubernetes")
            if k8s and isinstance(k8s, dict):
                c_name = k8s.get("container_name")
                if c_name:
                    by_container[c_name] = by_container.get(c_name, 0) + 1

            # Time range
            if min_time is None or entry.timestamp < min_time:
                min_time = entry.timestamp
            if max_time is None or entry.timestamp > max_time:
                max_time = entry.timestamp

        return {
            "total": count,
            "by_level": by_level,
            "by_container": by_container,
            "time_range": {
                "start": (
                    min_time.astimezone(timezone.utc).isoformat() if min_time else None
                ),
                "end": (
                    max_time.astimezone(timezone.utc).isoformat() if max_time else None
                ),
            },
        }

    def export(self, output_path: str, format: str = "json") -> None:
        """
        Export filtered logs to a file in the specified format (json, csv, text).
        Args:
            output_path: Path to the output file.
            format: Format to export the logs in (json, csv, text).
        Returns:
            None
        Raises:
            ValueError: If the specified format is not supported.
        """
        if format == "json":
            self._export_json(output_path)
        elif format == "csv":
            self._export_csv(output_path)
        elif format == "text":
            self._export_text(output_path)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _export_json(self, output_path: str) -> None:
        # Stream valid JSON array: [obj, obj, ...]
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("[\n")
            first = True
            for entry in self:
                if not first:
                    f.write(",\n")
                first = False

                # Convert entry to dict
                data = {
                    "timestamp": entry.timestamp.isoformat(),
                    "level": entry.level,
                    "component": entry.component,
                    "message": entry.message,
                    "metadata": entry.metadata,  # Original metadata
                    "kv_pairs": entry.kv_pairs,
                }
                f.write(json.dumps(data))
            f.write("\n]")

    def _export_csv(self, output_path: str) -> None:
        fieldnames = ["timestamp", "level", "component", "message", "container", "pod"]

        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()

            for entry in self:
                row = {
                    "timestamp": entry.timestamp.isoformat(),
                    "level": entry.level,
                    "component": entry.component,
                    "message": entry.message,
                    "container": entry.metadata.get("kubernetes", {}).get(
                        "container_name", ""
                    ),
                    "pod": entry.metadata.get("kubernetes", {}).get("pod_name", ""),
                }
                writer.writerow(row)

    def _export_text(self, output_path: str) -> None:
        with open(output_path, "w", encoding="utf-8") as f:
            for entry in self:
                ts = entry.timestamp.isoformat()
                f.write(f"[{ts}] [{entry.level}] {entry.component}: {entry.message}\n")
