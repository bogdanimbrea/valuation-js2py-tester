#!/usr/bin/env python3
"""
test_bot_detection.py
---------------------
Quick check for your `is_bot_request` function against an Nginx/Apache-style
access.log that has the format:

    ip - - [date] "METHOD path HTTP/x" status bytes "referrer" "user-agent" "x-forwarded-for"

Place this script next to `access.log` and run:
    python test_bot_detection.py
"""

import re
from collections import Counter
from pathlib import Path

# ────────────────────────────────────────────────────────────
# Your original function (verbatim)
# ────────────────────────────────────────────────────────────
def is_bot_request(request):
    user_agent_string = request.META.get("HTTP_USER_AGENT", "").lower().strip()

    bot_keyword_signatures = [
        # ── Generic crawler verbs ──
        "bot", "crawl", "spider", "slurp", "reader", "fetch",
        "monitor", "analyzer", "healthcheck",

        # ── Programming languages / HTTP libraries ──
        "python", "requests", "urllib", "java",
        "okhttp", "curl", "wget", "libwww",
        "httpclient", "go-http-client", "axios",
        "got", "postman", "insomnia",

        # ── Headless browsers / testing tools ──
        "headlesschrome", "phantomjs", "puppeteer",
        "playwright", "selenium", "chromedp",
        "lighthouse", "pagespeed",

        # ── Major search / SEO crawlers (roots without “bot”) ──
        "ahrefs", "semrush", "yandex",

        # ── AI / LLM harvesters (roots without “bot”) ──
        "openai", "chatgpt", "oai-search", "perplexity",
        "googleother", "google-read-aloud",

        # ── Social-media link fetchers lacking “bot” ──
        "facebookexternalhit", "embedly", "whatsapp",

        # ── Uptime & infrastructure monitors ──
        "pingdom", "statuscake",

        # ── Misc keywords you already use ──
        "support", "feed", "spreadsheet", "script", "about",
    ]

    # Blank or missing User-Agent almost always means “bot”.
    if not user_agent_string or user_agent_string == "-":
        return True

    for bot_signature in bot_keyword_signatures:
        if bot_signature in user_agent_string:
            return True

    # Otherwise, looks like a human browser.
    return False


# ────────────────────────────────────────────────────────────
# Helper: pull the User-Agent out of an access-log line
# ────────────────────────────────────────────────────────────
UA_REGEX = re.compile(r'"([^"]*)"')       # grabs everything between quotes

def extract_user_agent(log_line: str) -> str:
    """
    Returns the second-to-last quoted substring, which is the User-Agent
    in the default Nginx/Apache combined log format. Returns an empty
    string if it cannot be found.
    """
    quoted_parts = UA_REGEX.findall(log_line)
    if len(quoted_parts) >= 2:
        return quoted_parts[-2]
    return ""


# ────────────────────────────────────────────────────────────
# Minimal Request object stand-in
# ────────────────────────────────────────────────────────────
class DummyRequest:
    """
    Mimics Django/DRF's request just enough for is_bot_request:
    - Holds a META dict with "HTTP_USER_AGENT".
    """
    __slots__ = ("META",)

    def __init__(self, user_agent: str):
        self.META = {"HTTP_USER_AGENT": user_agent}


# ────────────────────────────────────────────────────────────
# Main test routine
# ────────────────────────────────────────────────────────────
def main():
    log_path = Path("access.log")
    if not log_path.exists():
        raise SystemExit("⚠️  access.log not found in the current directory.")

    human_lines, bot_lines = [], []
    ua_counter = Counter()

    with log_path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            ua = extract_user_agent(line)
            ua_counter[ua] += 1

            dummy_request = DummyRequest(ua)
            if is_bot_request(dummy_request):
                bot_lines.append(line.rstrip())
            else:
                human_lines.append(line.rstrip())

    # ── Report ───────────────────────────────────────────────
    total = len(bot_lines) + len(human_lines)
    print(f"\nProcessed {total:,} log lines from {log_path}.\n")
    print(f"🔍  Classified as bots  : {len(bot_lines):>7}")
    print(f"👤  Classified as humans: {len(human_lines):>7}\n")

    # Show a quick sample (first 5 of each)
    def show_sample(tag: str, lines: list[str]):
        print(f"{tag} (showing up to 5)")
        print("-" * len(tag))
        for line in lines[:5]:
            print(line)
        if len(lines) > 5:
            print(f"... and {len(lines) - 5} more\n")
        else:
            print()

    show_sample("🚦 Bot-like requests", bot_lines)
    show_sample("✅ Human-like requests", human_lines)

    # ── Top 100 bot UAs only ─────────────────────────────────
    bot_ua_counter = Counter()
    for line in bot_lines:
        ua = extract_user_agent(line)
        if ua:  # skip blank strings
            bot_ua_counter[ua] += 1

    print("Top 100 Bot User-Agents by frequency")
    print("------------------------------------")
    for ua, count in bot_ua_counter.most_common(100):
        print(f"{count:>6} × {ua}")


    # ── Top 100 Human UAs only ───────────────────────────────
    human_ua_counter = Counter()
    for line in human_lines:
        ua = extract_user_agent(line)
        if ua:  # skip blank strings
            human_ua_counter[ua] += 1

    print("Top 100 Human User-Agents by frequency")
    print("---------------------------------------")
    for ua, count in human_ua_counter.most_common(100):
        print(f"{count:>6} × {ua}")


if __name__ == "__main__":
    main()
