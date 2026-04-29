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

from __future__ import annotations

import argparse
import datetime as dt
import sys
import time
from dataclasses import dataclass, field
from typing import Optional

import requests
from requests.exceptions import ConnectionError, RequestException, Timeout


DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_CYCLES = 2
DEFAULT_DELAY = 4
DEFAULT_TIMEOUT = 10

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

USE_COLOR = sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text


def green(text: str) -> str:
    return _c("32", text)


def red(text: str) -> str:
    return _c("31", text)


def yellow(text: str) -> str:
    return _c("33", text)


def cyan(text: str) -> str:
    return _c("36", text)


def bold(text: str) -> str:
    return _c("1", text)


def dim(text: str) -> str:
    return _c("2", text)


def _elapsed_ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 1)


def _now() -> dt.datetime:
    return dt.datetime.now()


@dataclass
class RequestResult:
    url: str
    status_code: Optional[int]
    response_time_ms: float
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.status_code == 200

    @property
    def label(self) -> str:
        if self.error:
            return red(f"ERROR  ({self.error})")
        return green(str(self.status_code)) if self.ok else red(str(self.status_code))


@dataclass
class CycleSummary:
    cycle_number: int
    results: list[RequestResult] = field(default_factory=list)
    start_time: dt.datetime = field(default_factory=_now)
    end_time: Optional[dt.datetime] = None

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
        return str(self.end_time - self.start_time).split(".")[0] if self.end_time else "—"


def probe(url: str, timeout: int) -> RequestResult:
    """Send a single GET request and return a RequestResult."""
    start = time.perf_counter()
    try:
        response = requests.get(url, timeout=timeout, allow_redirects=True)
        return RequestResult(
            url=url,
            status_code=response.status_code,
            response_time_ms=_elapsed_ms(start),
        )
    except Timeout:
        return RequestResult(url=url, status_code=None, response_time_ms=_elapsed_ms(start), error="Timeout")
    except ConnectionError:
        return RequestResult(url=url, status_code=None, response_time_ms=_elapsed_ms(start), error="ConnectionError")
    except RequestException as exc:
        return RequestResult(url=url, status_code=None, response_time_ms=_elapsed_ms(start), error=str(exc)[:60])


def run_cycle(cycle_num: int, base_url: str, paths: list[str], delay: float, timeout: int) -> CycleSummary:
    summary = CycleSummary(cycle_number=cycle_num)
    total = len(paths)

    print(f"\n{bold(f'── Cycle {cycle_num} ──')}  started {dim(summary.start_time.strftime('%H:%M:%S'))}")
    print(f"  {'#':<5} {'Status':<5} {'Time(ms)':>8}  URL")
    print(f"  {'─' * 5} {'─' * 5} {'─' * 8}  {'─' * 40}")

    for idx, path in enumerate(paths, start=1):
        full_url = f"{base_url}{path}"
        result = probe(full_url, timeout)
        summary.results.append(result)

        print(
            f"  {idx:<5} "
            f"{result.label.ljust(5)} "
            f"{result.response_time_ms:>9.1f}  "
            f"{dim(full_url)}"
        )

        if idx < total:
            time.sleep(delay)

    summary.end_time = _now()
    _print_cycle_summary(summary)
    return summary


def _print_cycle_summary(summary: CycleSummary) -> None:
    ok_bar = green("█" * summary.ok_count)
    error_bar = red("█" * summary.error_count)

    print(f"\n  {bold('Summary — Cycle')} {summary.cycle_number}")
    print(f"  Requests : {summary.total}")
    print(f"  Success  : {green(str(summary.ok_count))} ({summary.success_rate}%)  {ok_bar}")
    print(f"  Errors   : {red(str(summary.error_count))} ({summary.error_rate}%)  {error_bar}")
    print(f"  Avg resp : {summary.avg_response_ms} ms")
    print(f"  Duration : {summary.elapsed}")

    if summary.error_count:
        print(f"\n  {yellow('Failed endpoints:')}")
        for result in summary.results:
            if not result.ok:
                print(f"    {red('✗')} {result.url}  →  {result.label}")


def _print_final_report(cycles: list[CycleSummary], overall_start: dt.datetime) -> None:
    overall_end = _now()
    total_requests = sum(c.total for c in cycles)
    total_ok = sum(c.ok_count for c in cycles)
    total_errors = sum(c.error_count for c in cycles)
    success_pct = round(total_ok / total_requests * 100, 2) if total_requests else 0.0
    error_pct = round(100 - success_pct, 2)

    print(f"\n{'═' * 55}")
    print(bold("  FINAL REPORT"))
    print(f"{'═' * 55}")
    print(f"  Cycles run     : {len(cycles)}")
    print(f"  Total requests : {total_requests}")
    print(f"  Total success  : {green(str(total_ok))} ({success_pct}%)")
    print(f"  Total errors   : {red(str(total_errors))} ({error_pct}%)")
    print(f"  Total duration : {str(overall_end - overall_start).split('.')[0]}")

    results_by_url: dict[str, list[RequestResult]] = {}
    for cycle in cycles:
        for result in cycle.results:
            results_by_url.setdefault(result.url, []).append(result)

    persistent_failures = [url for url, results in results_by_url.items() if all(not r.ok for r in results)]
    if persistent_failures:
        print(f"\n  {bold(red('Persistently failing endpoints:'))}")
        for url in persistent_failures:
            print(f"    {red('✗')} {url}")
    else:
        print(f"\n  {green('✓ No endpoints failed across all cycles.')}")

    print(f"{'═' * 55}\n")


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


def main() -> None:
    args = parse_args()

    print(bold(cyan("\n  ╔══════════════════════════════════════╗")))
    print(bold(cyan("  ║     Endpoint Availability Tester     ║")))
    print(bold(cyan("  ╚══════════════════════════════════════╝")))
    print(f"  Base URL : {args.base_url}")
    print(f"  Cycles   : {args.cycles}")
    print(f"  Delay    : {args.delay}s between requests")
    print(f"  Timeout  : {args.timeout}s per request")
    print(f"  Endpoints: {len(TARGET_PATHS)}")

    overall_start = _now()
    all_cycles: list[CycleSummary] = []

    for cycle_num in range(1, args.cycles + 1):
        if cycle_num > 1:
            print(dim(f"\n  [Waiting {args.delay}s before next cycle…]"))
            time.sleep(args.delay)

        all_cycles.append(run_cycle(cycle_num, args.base_url, TARGET_PATHS, args.delay, args.timeout))

    _print_final_report(all_cycles, overall_start)


if __name__ == "__main__":
    main()
    