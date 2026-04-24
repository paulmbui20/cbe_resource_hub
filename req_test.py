"""
Endpoint Availability Tester
=============================
Polls a list of HTTP endpoints repeatedly, reports per-request status,
per-cycle summaries, and a full-run report at the end.

Usage:
    python req_test.py [--base-url URL] [--cycles N] [--delay SECONDS] [--timeout SECONDS]

Defaults:
    --base-url   http://localhost:8000
    --cycles     2
    --delay      4
    --timeout    10
"""

import argparse
import datetime
import sys
import time
from dataclasses import dataclass, field
from typing import Optional

import requests
from requests.exceptions import ConnectionError, Timeout, RequestException

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────

DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_CYCLES = 2
DEFAULT_DELAY = 4  # seconds between requests
DEFAULT_TIMEOUT = 10  # seconds before a request is considered timed-out

TARGET_PATHS = [
    "/",
    "/resources",
    "/resources/sitemap.xml",
    "/resources/type/exam",
    "/resources/type/schemes_of_work",
    "/resources/type/sitemap.xml",
    "/resources/learning-areas",
    "/resources/learning-areas/creative-arts",
    "/resources/learning-areas/sitemap.xml",
    "/resources/grades",
    "/resources/grades/grade-8",
    "/resources/grades/sitemap.xml",
    "/resources/education-levels/junior-school",
    "/resources/education-levels/sitemap.xml",
    "/resources/academic-sessions",
    "/resources/academic-sessions/2026-term-1",
    "/resources/academic-sessions/sitemap.xml",
    "/accounts/login",
    "/accounts/signup",
    "/accounts/password/reset",
    "/contact",
    "/partners",
]

# ──────────────────────────────────────────────
# ANSI colour helpers (disabled automatically on Windows / non-TTY)
# ──────────────────────────────────────────────

USE_COLOR = sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text


def green(t):  return _c("32", t)


def red(t):    return _c("31", t)


def yellow(t): return _c("33", t)


def cyan(t):   return _c("36", t)


def bold(t):   return _c("1", t)


def dim(t):    return _c("2", t)


# ──────────────────────────────────────────────
# Data structures
# ──────────────────────────────────────────────

@dataclass
class RequestResult:
    url: str
    status_code: Optional[int]  # None on network error
    response_time_ms: float
    error: Optional[str] = None  # set on exception

    @property
    def ok(self) -> bool:
        return self.status_code == 200

    @property
    def label(self) -> str:
        if self.error:
            return red(f"ERROR  ({self.error})")
        color = green if self.ok else red
        return color(str(self.status_code))


@dataclass
class CycleSummary:
    cycle_number: int
    results: list[RequestResult] = field(default_factory=list)
    start_time: datetime.datetime = field(default_factory=datetime.datetime.now)
    end_time: Optional[datetime.datetime] = None

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def ok_count(self) -> int:
        return sum(1 for r in self.results if r.ok)

    @property
    def error_count(self) -> int:
        return self.total - self.ok_count

    @property
    def success_rate(self) -> float:
        return round(self.ok_count / self.total * 100, 2) if self.total else 0.0

    @property
    def error_rate(self) -> float:
        return round(self.error_count / self.total * 100, 2) if self.total else 0.0

    @property
    def avg_response_ms(self) -> float:
        times = [r.response_time_ms for r in self.results if r.error is None]
        return round(sum(times) / len(times), 1) if times else 0.0

    @property
    def elapsed(self) -> str:
        if self.end_time:
            return str(self.end_time - self.start_time).split(".")[0]
        return "—"


# ──────────────────────────────────────────────
# Core logic
# ──────────────────────────────────────────────

def probe(url: str, timeout: int) -> RequestResult:
    """Send a single GET request and return a RequestResult."""
    t0 = time.perf_counter()
    try:
        resp = requests.get(url, timeout=timeout, allow_redirects=True)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return RequestResult(url=url, status_code=resp.status_code, response_time_ms=round(elapsed_ms, 1))
    except Timeout:
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return RequestResult(url=url, status_code=None, response_time_ms=round(elapsed_ms, 1), error="Timeout")
    except ConnectionError:
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return RequestResult(url=url, status_code=None, response_time_ms=round(elapsed_ms, 1), error="ConnectionError")
    except RequestException as exc:
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return RequestResult(url=url, status_code=None, response_time_ms=round(elapsed_ms, 1), error=str(exc)[:60])


def run_cycle(cycle_num: int, base_url: str, paths: list[str], delay: float, timeout: int) -> CycleSummary:
    """Run one full pass over all endpoints."""
    summary = CycleSummary(cycle_number=cycle_num)
    total = len(paths)

    print(f"\n{bold(f'── Cycle {cycle_num} ──')}  started {dim(summary.start_time.strftime('%H:%M:%S'))}")
    print(f"  {'#':<5} {'Status':<5} {'Time(ms)':>8}  URL")
    print(f"  {'─' * 5} {'─' * 5} {'─' * 8}  {'─' * 40}")

    for idx, path in enumerate(paths, start=1):
        full_url = f"{base_url}{path}"
        result = probe(full_url, timeout)
        summary.results.append(result)

        # Per-request line
        status_col = result.label.ljust(5)
        time_col = f"{result.response_time_ms:>9.1f}"
        url_col = dim(full_url)
        print(f"  {idx:<5} {status_col} {time_col}  {url_col}")

        if idx < total:
            time.sleep(delay)

    summary.end_time = datetime.datetime.now()
    _print_cycle_summary(summary)
    return summary


def _print_cycle_summary(s: CycleSummary):
    ok_bar = green("█" * s.ok_count)
    error_bar = red("█" * s.error_count)
    print(f"\n  {bold('Summary — Cycle')} {s.cycle_number}")
    print(f"  Requests : {s.total}")
    print(f"  Success  : {green(str(s.ok_count))} ({s.success_rate}%)  {ok_bar}")
    print(f"  Errors   : {red(str(s.error_count))} ({s.error_rate}%)  {error_bar}")
    print(f"  Avg resp : {s.avg_response_ms} ms")
    print(f"  Duration : {s.elapsed}")

    if s.error_count:
        print(f"\n  {yellow('Failed endpoints:')}")
        for r in s.results:
            if not r.ok:
                print(f"    {red('✗')} {r.url}  →  {r.label}")


def _print_final_report(cycles: list[CycleSummary], overall_start: datetime.datetime):
    overall_end = datetime.datetime.now()
    total_reqs = sum(c.total for c in cycles)
    total_ok = sum(c.ok_count for c in cycles)
    total_err = sum(c.error_count for c in cycles)
    success_pct = round(total_ok / total_reqs * 100, 2) if total_reqs else 0

    print(f"\n{'═' * 55}")
    print(bold("  FINAL REPORT"))
    print(f"{'═' * 55}")
    print(f"  Cycles run     : {len(cycles)}")
    print(f"  Total requests : {total_reqs}")
    print(f"  Total success  : {green(str(total_ok))} ({success_pct}%)")
    print(f"  Total errors   : {red(str(total_err))} ({round(100 - success_pct, 2)}%)")
    print(f"  Total duration : {str(overall_end - overall_start).split('.')[0]}")

    # Highlight any consistently failing endpoints
    all_results: dict[str, list[RequestResult]] = {}
    for cycle in cycles:
        for r in cycle.results:
            all_results.setdefault(r.url, []).append(r)

    persistent_failures = [url for url, results in all_results.items() if all(not r.ok for r in results)]
    if persistent_failures:
        print(f"\n  {bold(red('Persistently failing endpoints:'))}")
        for url in persistent_failures:
            print(f"    {red('✗')} {url}")
    else:
        print(f"\n  {green('✓ No endpoints failed across all cycles.')}")

    print(f"{'═' * 55}\n")


# ──────────────────────────────────────────────
# CLI entry point
# ──────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Test availability of HTTP endpoints over multiple cycles.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Base URL to test against")
    parser.add_argument("--cycles", type=int, default=DEFAULT_CYCLES, help="Number of polling cycles")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY, help="Seconds between requests")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Request timeout in seconds")
    return parser.parse_args()


def main():
    args = parse_args()

    print(bold(cyan("\n  ╔══════════════════════════════════════╗")))
    print(bold(cyan("  ║     Endpoint Availability Tester     ║")))
    print(bold(cyan("  ╚══════════════════════════════════════╝")))
    print(f"  Base URL : {args.base_url}")
    print(f"  Cycles   : {args.cycles}")
    print(f"  Delay    : {args.delay}s between requests")
    print(f"  Timeout  : {args.timeout}s per request")
    print(f"  Endpoints: {len(TARGET_PATHS)}")

    overall_start = datetime.datetime.now()
    all_cycles: list[CycleSummary] = []

    for cycle_num in range(1, args.cycles + 1):
        if cycle_num > 1:
            print(dim(f"\n  [Waiting {args.delay}s before next cycle…]"))
            time.sleep(args.delay)
        summary = run_cycle(cycle_num, args.base_url, TARGET_PATHS, args.delay, args.timeout)
        all_cycles.append(summary)

    _print_final_report(all_cycles, overall_start)


if __name__ == "__main__":
    main()
