"""Opt-in Sentry setup and shutdown for the Sally CLI."""
import logging
import os
from contextlib import contextmanager


@contextmanager
def session():
    """No DSN means no SDK import; flush enabled reporting before CLI exit."""
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        yield
        return
    log_level = os.getenv("SALLY_SENTRY_LOG_LEVEL", "").upper()
    if log_level and log_level not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
        raise ValueError(f"SALLY_SENTRY_LOG_LEVEL expects DEBUG, INFO, WARNING, ERROR, CRITICAL or empty, got {log_level!r}")
    trace_rate = os.getenv("SENTRY_TRACES_SAMPLE_RATE")
    try:
        traces_sample_rate = float(trace_rate) if trace_rate is not None else None
    except ValueError as error:
        raise ValueError(f"SENTRY_TRACES_SAMPLE_RATE expects a number between 0 and 1, got {trace_rate!r}") from error
    if traces_sample_rate is not None and not 0 <= traces_sample_rate <= 1:
        raise ValueError(f"SENTRY_TRACES_SAMPLE_RATE expects a number between 0 and 1, got {trace_rate!r}")
    try:
        import sentry_sdk
    except ModuleNotFoundError as error:
        if error.name != "sentry_sdk": raise
        raise RuntimeError("SENTRY_DSN requires sally[sentry]; got no sentry-sdk installed") from error
    from sentry_sdk.integrations.falcon import FalconIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration

    sentry_sdk.init(
        dsn=dsn,
        default_integrations=False,
        integrations=[FalconIntegration(), LoggingIntegration(
            level=logging.DEBUG,
            sentry_logs_level=getattr(logging, log_level, None),
        )],
        # Startup frame locals include passcode and salt arguments.
        include_local_variables=False,
        in_app_include=["sally"],
        enable_logs=bool(log_level),
        traces_sample_rate=traces_sample_rate,
    )
    try:
        yield
    except Exception as error:
        sentry_sdk.capture_exception(error, tags={"component": "cli"})
        raise
    finally:
        sentry_sdk.get_client().close()
