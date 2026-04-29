#!/usr/bin/env python3
"""
Docker health check script using Python
No external dependencies needed - uses only stdlib
"""
import json
import sys
import time
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

HEALTH_ENDPOINT = "http://localhost:8000/health/ready/"
MAX_RETRIES = 3
RETRY_DELAY = 2
TIMEOUT = 30


def log(message):
    """Print log message with timestamp"""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)


def check_health():
    """Perform health check"""
    try:
        log(f"Checking health endpoint: {HEALTH_ENDPOINT} (timeout: {TIMEOUT}s)")

        req = Request(HEALTH_ENDPOINT)
        req.add_header('User-Agent', 'Docker-Health-Check/1.0')

        with urlopen(req, timeout=TIMEOUT) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))

                log(f"Response received: {json.dumps(data, indent=2)}")

                if data.get('ready') is True:
                    log("✓ Health check PASSED - service is ready")
                    return True
                else:
                    log("✗ Health check FAILED - service not ready")
                    log(f"Details: {json.dumps(data.get('checks', {}), indent=2)}")
                    return False
            else:
                log(f"✗ Unexpected status code: {response.status}")
                return False

    except HTTPError as e:
        log(f"✗ HTTP Error: {e.code} - {e.reason}")
        return False
    except URLError as e:
        log(f"✗ Connection Error: {e.reason}")
        return False
    except json.JSONDecodeError as e:
        log(f"✗ Invalid JSON response: {e}")
        return False
    except Exception as e:
        log(f"✗ Unexpected error: {type(e).__name__}: {e}")
        return False


def main():
    """Main health check loop with retries"""
    log(f"Starting health check (max retries: {MAX_RETRIES}, timeout: {TIMEOUT}s)")

    for attempt in range(1, MAX_RETRIES + 1):
        log(f"Attempt {attempt}/{MAX_RETRIES}")

        if check_health():
            log("SUCCESS: Container is healthy")
            sys.exit(0)

        if attempt < MAX_RETRIES:
            log(f"Retrying in {RETRY_DELAY}s...")
            time.sleep(RETRY_DELAY)

    log(f"FAILURE: Health check failed after {MAX_RETRIES} attempts")
    sys.exit(1)


if __name__ == "__main__":
    main()