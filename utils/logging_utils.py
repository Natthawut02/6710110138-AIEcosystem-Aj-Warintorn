"""
Logging Utility Module.
Provides helper functions for formatting log records and parsing log history.
"""

from pathlib import Path
from typing import List, Dict


def read_latest_logs(log_file: Path, num_lines: int = 50) -> List[str]:
    """
    Reads the last `num_lines` from a log file (tail behavior).
    """
    if not log_file.exists():
        return []
    
    with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
        return lines[-num_lines:]


def parse_log_line(line: str) -> Dict[str, str]:
    """
    Parses a pipe-delimited log entry (YYYY-MM-DD HH:MM:SS | LEVEL | Module | Message).
    """
    parts = [p.strip() for p in line.split("|", 3)]
    if len(parts) == 4:
        return {
            "timestamp": parts[0],
            "level": parts[1],
            "module": parts[2],
            "message": parts[3]
        }
    return {"raw": line.strip()}
