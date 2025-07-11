#!/usr/bin/env python3

import argparse
import os
import re
from collections import defaultdict, Counter
from datetime import datetime, timedelta

def parse_log_line(log_line: str):
    # … same as before …
    match = re.search(
        r'\[(?P<timestamp>[0-9]{2}/[A-Za-z]{3}/[0-9]{4}:[0-9]{2}:[0-9]{2}:[0-9]{2} [+\-][0-9]{4})\] '
        r'"[A-Z]+ (?P<path>[^ ]+) HTTP',
        log_line
    )
    if not match:
        return None, None
    timestamp_str = match.group('timestamp')
    request_path = match.group('path')
    timestamp = datetime.strptime(timestamp_str, "%d/%b/%Y:%H:%M:%S %z")
    return timestamp, request_path

def round_down_to_five_minutes(timestamp: datetime):
    # … same as before …
    minute_floor = (timestamp.minute // 5) * 5
    return timestamp.replace(minute=minute_floor, second=0, microsecond=0)

def summarize_log_by_interval(log_file_path: str):
    tracked_segments = ['/transcripts', '/valuation']
    counters_by_interval = defaultdict(lambda: Counter({
        'total': 0,
        '/transcripts': 0,
        '/valuation': 0,
        'other': 0
    }))

    with open(log_file_path, 'r', encoding='utf-8') as log_file:
        for line in log_file:
            timestamp, request_path = parse_log_line(line)
            if not timestamp:
                continue
            interval_start = round_down_to_five_minutes(timestamp)
            counts = counters_by_interval[interval_start]
            counts['total'] += 1
            for segment in tracked_segments:
                if segment in request_path:
                    counts[segment] += 1
                    break
            else:
                counts['other'] += 1

    return counters_by_interval

def print_summary(counters_by_interval):
    for interval_start in sorted(counters_by_interval):
        interval_end = interval_start + timedelta(minutes=5)
        counts = counters_by_interval[interval_start]
        print(f"{interval_start.strftime('%H:%M')} – {interval_end.strftime('%H:%M')}")
        print(f"  Total requests:    {counts['total']}")
        print(f"  '/transcripts':    {counts['/transcripts']}")
        print(f"  '/valuation':      {counts['/valuation']}")
        print(f"  Other paths:       {counts['other']}\n")

def main():
    parser = argparse.ArgumentParser(
        description="Summarize nginx access.log by 5-minute intervals."
    )
    parser.add_argument(
        'log_file',
        nargs='?',
        help="Path to nginx access.log (defaults to ./access.log)"
    )
    args = parser.parse_args()

    # Determine the log file: either the one passed in, or access.log next to this script
    if args.log_file:
        log_file_path = args.log_file
    else:
        script_directory = os.path.dirname(os.path.abspath(__file__))
        log_file_path = os.path.join(script_directory, 'access.log')

    if not os.path.isfile(log_file_path):
        raise FileNotFoundError(f"No log file found at {log_file_path!r}")

    counters_by_interval = summarize_log_by_interval(log_file_path)
    print_summary(counters_by_interval)

if __name__ == "__main__":
    main()
