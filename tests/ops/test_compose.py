"""Compose/ops integration tests.

These tests require Docker and are skipped unless RUN_OPS_TESTS=1.
See TESTING.md and docs/deployment/local.md for the manual verify-compose script
used when these are skipped in default CI unit jobs.
"""

from __future__ import annotations

import os
import subprocess
import time
import urllib.error
import urllib.request

import pytest

pytestmark = pytest.mark.ops

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _ops_enabled() -> bool:
    return os.environ.get("RUN_OPS_TESTS", "").lower() in {"1", "true", "yes"}


@pytest.fixture(scope="module")
def compose_stack() -> None:
    if not _ops_enabled():
        pytest.skip("Set RUN_OPS_TESTS=1 to run Compose ops tests")
    env = os.environ.copy()
    env.setdefault("COMPOSE_PROJECT_NAME", "nova_ops_test")
    subprocess.run(
        ["docker", "compose", "down", "-v", "--remove-orphans"],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
    )
    up = subprocess.run(
        ["docker", "compose", "up", "--build", "-d"],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    if up.returncode != 0:
        pytest.fail(f"compose up failed:\n{up.stdout}\n{up.stderr}")
    try:
        _wait_http("http://127.0.0.1:8000/health", timeout=120)
        yield
    finally:
        subprocess.run(
            ["docker", "compose", "down", "-v", "--remove-orphans"],
            cwd=ROOT,
            env=env,
            check=False,
            capture_output=True,
        )


def _wait_http(url: str, timeout: float) -> None:
    deadline = time.time() + timeout
    last: Exception | None = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=3) as resp:
                if 200 <= resp.status < 300:
                    return
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            last = exc
            time.sleep(2)
    raise AssertionError(f"Timed out waiting for {url}: {last}")


def test_api_health_and_ready(compose_stack: None) -> None:
    with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=5) as resp:
        assert resp.status == 200
    with urllib.request.urlopen("http://127.0.0.1:8000/ready", timeout=5) as resp:
        assert resp.status == 200
        body = resp.read().decode()
        assert "ready" in body


def test_restart_behavior(compose_stack: None) -> None:
    env = os.environ.copy()
    env.setdefault("COMPOSE_PROJECT_NAME", "nova_ops_test")
    restart = subprocess.run(
        ["docker", "compose", "restart", "api"],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert restart.returncode == 0, restart.stderr
    _wait_http("http://127.0.0.1:8000/health", timeout=90)
    with urllib.request.urlopen("http://127.0.0.1:8000/ready", timeout=5) as resp:
        assert resp.status == 200
