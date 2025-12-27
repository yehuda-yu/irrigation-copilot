"""
Pytest configuration and fixtures for token-safe testing.

CRITICAL: LLM tests are NEVER run by default, even if GOOGLE_API_KEY exists.
They require explicit opt-in via RUN_LLM_TESTS=1 environment variable.
"""

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

# Load .env file for tests (API keys, etc.)
# This is safe because LLM tests still require RUN_LLM_TESTS=1 opt-in
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

# =============================================================================
# TOKEN-SAFETY CONSTANTS
# =============================================================================

LLM_OPT_IN_ENV_VAR = "RUN_LLM_TESTS"
LLM_SKIP_REASON = (
    "LLM tests require explicit opt-in: set RUN_LLM_TESTS=1 to enable. "
    "This prevents accidental token burn."
)
RATE_LIMIT_SKIP_REASON = "Google Gemini rate limit hit - skipping to avoid token waste"
XDIST_LLM_ERROR = (
    "LLM tests cannot run with pytest-xdist parallel execution. "
    "Run without -n flag to avoid parallel token burn."
)


def is_llm_enabled() -> bool:
    """Check if LLM tests are explicitly enabled."""
    return os.environ.get(LLM_OPT_IN_ENV_VAR, "").strip() == "1"


def has_api_key() -> bool:
    """Check if Google API key is available."""
    return bool(os.environ.get("GOOGLE_API_KEY", "").strip())


def is_xdist_worker() -> bool:
    """Check if running under pytest-xdist parallel execution."""
    # pytest-xdist sets PYTEST_XDIST_WORKER env var for workers
    return bool(os.environ.get("PYTEST_XDIST_WORKER"))


def is_xdist_controller() -> bool:
    """Check if xdist is active (controller or worker)."""
    # Check both worker and controller indicators
    return is_xdist_worker() or bool(os.environ.get("PYTEST_XDIST_TESTRUNUID"))


# =============================================================================
# PYTEST HOOKS - Block LLM tests at collection time
# =============================================================================


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "llm: marks tests as requiring LLM API access (token-costing, requires RUN_LLM_TESTS=1)",
    )
    config.addinivalue_line(
        "markers",
        "network: marks tests as requiring network access",
    )


def pytest_collection_modifyitems(config, items):
    """
    Skip LLM tests unless explicitly opted in.

    This runs during test collection, BEFORE any tests execute.
    Provides a hard gate that cannot be bypassed by having OPENAI_API_KEY set.
    """
    llm_enabled = is_llm_enabled()
    api_key_present = has_api_key()
    xdist_active = is_xdist_controller()

    for item in items:
        # Check if test has 'llm' marker
        if "llm" in [marker.name for marker in item.iter_markers()]:
            # Gate 1: Must have explicit opt-in
            if not llm_enabled:
                item.add_marker(pytest.mark.skip(reason=LLM_SKIP_REASON))
                continue

            # Gate 2: Must have API key
            if not api_key_present:
                item.add_marker(
                    pytest.mark.skip(reason="GOOGLE_API_KEY not set (required for LLM tests)")
                )
                continue

            # Gate 3: No parallel execution for LLM tests
            if xdist_active:
                item.add_marker(pytest.mark.skip(reason=XDIST_LLM_ERROR))
                continue


# =============================================================================
# FIXTURES - Additional safety nets
# =============================================================================


@pytest.fixture(autouse=True)
def enforce_llm_safety(request):
    """
    Autouse fixture that enforces LLM safety at test runtime.

    This is a backup gate in case collection-time skip was bypassed.
    """
    # Check if this test has the llm marker
    markers = [marker.name for marker in request.node.iter_markers()]
    if "llm" not in markers:
        yield
        return

    # Double-check gates at runtime
    if not is_llm_enabled():
        pytest.skip(LLM_SKIP_REASON)

    if not has_api_key():
        pytest.skip("GOOGLE_API_KEY not set")

    if is_xdist_controller():
        pytest.skip(XDIST_LLM_ERROR)

    yield


# =============================================================================
# HELPER FIXTURES FOR LLM TESTS
# =============================================================================


@pytest.fixture
def require_llm_opt_in():
    """
    Fixture that explicitly requires LLM opt-in.

    Use this in tests that need LLM access but aren't marked with @pytest.mark.llm.
    """
    if not is_llm_enabled():
        pytest.skip(LLM_SKIP_REASON)
    if not has_api_key():
        pytest.skip("GOOGLE_API_KEY not set")
    if is_xdist_controller():
        pytest.skip(XDIST_LLM_ERROR)


@pytest.fixture
def llm_test_timeout():
    """
    Returns the timeout in seconds for LLM tests.

    Helps prevent runaway token usage from hung requests.
    """
    return 60  # 60 seconds max per LLM test

