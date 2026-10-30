"""Sally coroutine cadences resolved through KERIpy's tock configuration."""
from collections.abc import Mapping

from keri import kering
from keri.app import tocking

from sally.core.configing import readConfig, validateDuration

# Child work runs on the next root turn unless explicitly slowed.
TOCKS = {
    'root': tocking.Tock('SALLY_ROOT_TOCK', 0.03125),
    'bootstrapRoot': tocking.Tock('SALLY_BOOTSTRAP_ROOT_TOCK', 0.03125),
    'bootstrap': tocking.Tock('SALLY_BOOTSTRAP_TOCK', 0.0),
    'bootstrapOobi': tocking.Tock('SALLY_BOOTSTRAP_OOBI_TOCK', 0.0),
    'bootstrapAuth': tocking.Tock('SALLY_BOOTSTRAP_AUTH_TOCK', 0.0),
    'httpServer': tocking.Tock('SALLY_HTTP_SERVER_TOCK', 0.0),
    'communicator': tocking.Tock('SALLY_COMMUNICATOR_TOCK', 0.0),
    'communicatorEscrow': tocking.Tock('SALLY_COMMUNICATOR_ESCROW_TOCK', 0.0),
    'webhookClient': tocking.Tock('SALLY_WEBHOOK_CLIENT_TOCK', 0.0),
    'presentation': tocking.Tock('SALLY_PRESENTATION_TOCK', 0.0),
    'revocation': tocking.Tock('SALLY_REVOCATION_TOCK', 0.0),
    'verifier': tocking.Tock('SALLY_VERIFIER_TOCK', 0.0),
    'verifierMsg': tocking.Tock('SALLY_VERIFIER_MSG_TOCK', 0.0),
    'verifierEscrow': tocking.Tock('SALLY_VERIFIER_ESCROW_TOCK', 0.0),
}



def resolveTocks(cfTocks=None, *, environ=None):
    """Resolve the Sally subsection of a tocks block, independently of deadlines."""
    cfTocks = {} if cfTocks is None else cfTocks
    if not isinstance(cfTocks, Mapping):
        raise kering.ConfigurationError('tocks must be a mapping')
    supplied = cfTocks.get('verifier', {})
    if not isinstance(supplied, Mapping):
        raise kering.ConfigurationError('tocks.verifier must be a mapping')
    tocks = tocking.resolveTocks(
        supplied, tocks=TOCKS, aliases={}, environ=environ, reserved=(),
    )
    # Reject a stopped root even if a valid environment override masks it.
    for key in ('root', 'bootstrapRoot'):
        if key in supplied:
            validateDuration(supplied[key], f'tocks.verifier.{key}', positive=True)
        validateDuration(tocks[key], f'tocks.verifier.{key}', positive=True)
    return tocks


def loadTocks(cf, **kwargs):
    """Read only coroutine cadences from the complete configuration file."""
    config = readConfig(cf)
    if 'tocks' in config and config['tocks'] is None:
        raise kering.ConfigurationError('tocks must be a mapping')
    return resolveTocks(config.get('tocks', {}), **kwargs)
