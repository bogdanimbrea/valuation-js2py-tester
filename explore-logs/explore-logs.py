#!/usr/bin/env python3

import argparse
import os
import re
from collections import defaultdict, Counter
from datetime import datetime, timedelta

def parse_log_line(log_line: str):
    """
    Parse a single nginx access.log line.
    Returns a tuple (client_ip: str, timestamp: datetime, request_path: str),
    or (None, None, None) if parsing fails.
    """
    # Regex to extract timestamp, request path, and client IP (last quoted field)
    regex_pattern = (
        r'\['
            r'(?P<timestamp>[0-9]{2}/[A-Za-z]{3}/[0-9]{4}:[0-9]{2}:[0-9]{2}:[0-9]{2} [+\-][0-9]{4})'
        r'\]\s+"[A-Z]+ '
            r'(?P<path>[^ ]+) '
            r'HTTP/[^"]+"'
        r'\s+\d+\s+\d+'
        r'\s+"[^"]*"\s+"[^"]*"'
        r'\s+"(?P<client_ip>[^"]+)"'
    )
    match = re.search(regex_pattern, log_line)
    if not match:
        return None, None, None

    timestamp_str = match.group('timestamp')
    request_path = match.group('path')
    client_ip = match.group('client_ip')
    timestamp = datetime.strptime(timestamp_str, "%d/%b/%Y:%H:%M:%S %z")
    return client_ip, timestamp, request_path

def round_down_to_five_minutes(timestamp: datetime):
    """
    Round a datetime down to the nearest 5-minute mark.
    """
    minute_floor = (timestamp.minute // 5) * 5
    return timestamp.replace(minute=minute_floor, second=0, microsecond=0)

def summarize_log_by_interval(log_file_path: str):
    """
    Read the log file, bucket entries into 5-minute intervals,
    count total/transcripts/valuation/other, and record per-client-IP timestamps.
    """
    tracked_segments = ['/transcripts', '/valuation']

    # Counters per interval
    counters_by_interval = defaultdict(lambda: Counter({
        'total': 0,
        '/transcripts': 0,
        '/valuation': 0,
        'other': 0
    }))
    # Per-interval → client_ip → [timestamps]
    ip_timestamps_by_interval = defaultdict(lambda: defaultdict(list))

    with open(log_file_path, 'r', encoding='utf-8') as log_file:
        for line in log_file:
            client_ip, timestamp, request_path = parse_log_line(line)
            if timestamp is None:
                continue

            interval_start = round_down_to_five_minutes(timestamp)
            interval_counters = counters_by_interval[interval_start]
            interval_counters['total'] += 1

            # classify path
            for segment in tracked_segments:
                if segment in request_path:
                    interval_counters[segment] += 1
                    break
            else:
                interval_counters['other'] += 1

            # record timestamp per client IP
            ip_timestamps_by_interval[interval_start][client_ip].append(timestamp)

    return counters_by_interval, ip_timestamps_by_interval

def compute_shortest_interval(sorted_timestamps):
    """
    Given a sorted list of datetimes, return the shortest delta in seconds
    between successive entries. If fewer than 2 timestamps, return None.
    """
    if len(sorted_timestamps) < 2:
        return None
    shortest_delta = None
    for previous, current in zip(sorted_timestamps, sorted_timestamps[1:]):
        delta_seconds = (current - previous).total_seconds()
        if shortest_delta is None or delta_seconds < shortest_delta:
            shortest_delta = delta_seconds
    return int(shortest_delta)

def print_summary(counters_by_interval, ip_timestamps_by_interval):
    """
    Print the counts for each 5-minute interval and top-5 client-IP frequency stats.
    """
    for interval_start in sorted(counters_by_interval):
        interval_end = interval_start + timedelta(minutes=5)
        counts = counters_by_interval[interval_start]

        print(f"{interval_start.strftime('%H:%M')}–{interval_end.strftime('%H:%M')}")
        print(f"  Total requests:    {counts['total']}")
        print(f"  '/transcripts':    {counts['/transcripts']}")
        print(f"  '/valuation':      {counts['/valuation']}")
        print(f"  Other paths:       {counts['other']}")

        # Gather per-IP stats
        ip_stats = []
        for client_ip, timestamps in ip_timestamps_by_interval[interval_start].items():
            request_count = len(timestamps)
            sorted_timestamps = sorted(timestamps)
            shortest_gap = compute_shortest_interval(sorted_timestamps)
            ip_stats.append((client_ip, request_count, shortest_gap))

        # Top 10 IPs by request_count
        top_five_ips = sorted(ip_stats, key=lambda item: item[1], reverse=True)[:10]
        if top_five_ips:
            print("  Top 10 client IPs:")
            for ip_address, request_count, shortest_gap in top_five_ips:
                gap_text = f"{shortest_gap}s" if shortest_gap is not None else "N/A"
                print(f"    • {ip_address}: {request_count} requests, "
                      f"shortest interval {gap_text}")
        print()

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

    if args.log_file:
        log_file_path = args.log_file
    else:
        script_directory = os.path.dirname(os.path.abspath(__file__))
        log_file_path = os.path.join(script_directory, 'access.log')

    if not os.path.isfile(log_file_path):
        raise FileNotFoundError(f"No log file found at {log_file_path!r}")

    counters_by_interval, ip_timestamps_by_interval = summarize_log_by_interval(log_file_path)
    print_summary(counters_by_interval, ip_timestamps_by_interval)

if __name__ == "__main__":
    main()
