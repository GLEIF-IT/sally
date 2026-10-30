"""Sally configuration reading and retry/deadline settings, all in seconds."""
import math
import os
from collections.abc import Mapping
from dataclasses import dataclass

from keri import kering
from keri.app import configing as keri_configing


def validateDuration(value, source, positive=False):
    """Return a finite duration in seconds; no unit conversion is performed.

    Zero is allowed unless ``positive`` is set. Booleans are not durations.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise kering.ConfigurationError(f'{source} must be a finite number of seconds')
    value = float(value)
    if not math.isfinite(value) or value < 0 or (positive and value == 0):
        bound = 'positive' if positive else 'non-negative'
        raise kering.ConfigurationError(f'{source} must be finite and {bound} (seconds)')
    return value


@dataclass(frozen=True)
class VerifierConfig:
    """Resolved retry delay and deadlines, expressed exclusively in seconds."""

    retry_delay_seconds: float
    escrow_timeout_seconds: float
    bootstrap_timeout_seconds: float
    webhook_request_timeout_seconds: float


def resolveVerifierConfig(config=None, *, environ=None, retry=None, timeout=None, default_retry=3.0):
    """Resolve CLI > environment > verifier config > defaults, independently of tocks.

    All supplied values are validated even when overridden. Retry zero permits
    immediate retries; request timeout zero disables that deadline. Escrow and
    bootstrap lifetimes must be positive.
    """
    config = {} if config is None else config
    environ = os.environ if environ is None else environ
    if not isinstance(config, Mapping) or not isinstance(environ, Mapping):
        raise kering.ConfigurationError('Sally configuration and environment must be mappings')
    supplied = config.get('verifier', {})
    if not isinstance(supplied, Mapping):
        raise kering.ConfigurationError('verifier must be a mapping')
    unknown = supplied.keys() - {'retryDelay', 'escrowTimeout', 'bootstrapTimeout', 'webhookRequestTimeout'}
    if unknown:
        raise kering.ConfigurationError(f'Unknown verifier configuration keys: {sorted(unknown)}')

    values = {}
    for key, env, default, positive in (
            ('retryDelay', 'SALLY_RETRY_DELAY', default_retry, False),
            ('escrowTimeout', 'SALLY_ESCROW_TIMEOUT', 600.0, True),
            ('bootstrapTimeout', 'SALLY_BOOTSTRAP_TIMEOUT', 30.0, True),
            ('webhookRequestTimeout', 'SALLY_WEBHOOK_REQUEST_TIMEOUT', 0.0, False)):
        value = validateDuration(supplied.get(key, default), f'verifier.{key}', positive=positive)
        if env in environ:
            try:
                raw = environ[env]
                if not isinstance(raw, str):
                    raise TypeError('Environment durations must be strings')
                value = validateDuration(float(raw), env, positive=positive)
            except (ValueError, TypeError) as ex:
                raise kering.ConfigurationError(f'Invalid {env}') from ex
        values[key] = value

    if retry is not None:
        values['retryDelay'] = validateDuration(retry, '--retry-delay')
    if timeout is not None:
        values['escrowTimeout'] = validateDuration(timeout, '--escrow-timeout', positive=True)
    return VerifierConfig(
        retry_delay_seconds=values['retryDelay'],
        escrow_timeout_seconds=values['escrowTimeout'],
        bootstrap_timeout_seconds=values['bootstrapTimeout'],
        webhook_request_timeout_seconds=values['webhookRequestTimeout'],
    )


class VerifierConfiger(keri_configing.Configer):
    """Adapt Sally's config to KERIpy's strict tock validation.

    KERIpy 1.2.18 rejects ``tocks.verifier`` as an unknown subsection. Hide it
    from KERIpy's reads so Sally can share the config file without changing
    KERIpy's validator. Sally reads the complete config through
    ``getVerifierConfig``; neither read view changes the file on disk.
    """

    def get(self, human=None):
        config = self.getVerifierConfig(human=human)
        if isinstance(config, Mapping) and isinstance(config.get('tocks'), Mapping):
            return {
                **config,
                'tocks': {
                    key: value
                    for key, value in config['tocks'].items()
                    if key != 'verifier'
                },
            }
        return config

    def getVerifierConfig(self, human=None):
        return super().get(human=human)

def readConfig(cf):
    """Read the complete Sally config without changing the reader or its file."""
    if cf is None:
        return {}
    config = cf.getVerifierConfig() if isinstance(cf, VerifierConfiger) else cf.get()
    if not isinstance(config, Mapping):
        raise kering.ConfigurationError('Sally configuration must be a mapping')
    return config


def loadVerifierConfig(cf, **kwargs):
    """Read retry and timeout settings from a config reader."""
    return resolveVerifierConfig(readConfig(cf), **kwargs)
