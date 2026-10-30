"""Coroutine cadence resolution and scheduler boundaries, without network traffic."""
import copy

import pytest
from hio.base import doing
from keri import kering
from keri.app import configing as keri_configing, habbing
from keri.db import basing
from keri.help import helping

from sally.app.bootstrapping import BootstrapRunner
from sally.core import configing, scheduling, serving


def test_defaults_and_precedence():
    """Scheduler resolution retains next-turn children and environment precedence."""
    defaults = scheduling.resolveTocks(environ={})
    assert defaults['root'] == .03125
    assert defaults['bootstrapRoot'] == .03125
    assert all(
        value == 0
        for key, value in defaults.items()
        if key not in ('root', 'bootstrapRoot')
    )
    config = {
        'mailboxEscrow': 0,
        'verifier': {
            'root': .005,
            'bootstrapOobi': .01,
            'bootstrapAuth': .02,
        },
    }
    original = copy.deepcopy(config)
    tocks = scheduling.resolveTocks(config, environ={'SALLY_ROOT_TOCK': '.002'})
    assert tocks['root'] == .002
    assert tocks['bootstrapOobi'] == .01
    assert tocks['bootstrapAuth'] == .02
    assert config == original


@pytest.mark.parametrize('tocks', [
    # Container errors and unknown keys fail before any scheduler starts.
    pytest.param(1, id='tocks-must-be-mapping'),
    pytest.param({'verifier': None}, id='verifier-tocks-must-be-mapping'),
    pytest.param({'verifier': {'typo': 0}}, id='unknown-verifier-tock'),
    # Both root clocks advance; children may be zero but must be finite numbers.
    pytest.param({'verifier': {'root': 0}}, id='root-must-be-positive'),
    pytest.param({'verifier': {'bootstrapRoot': 0}}, id='bootstrap-root-must-be-positive'),
    pytest.param({'verifier': {'presentation': True}}, id='child-tock-rejects-boolean'),
    pytest.param({'verifier': {'verifierMsg': float('nan')}}, id='child-tock-rejects-nan'),
])
def test_invalid_file_even_when_environment_overrides(tocks):
    """A valid environment root must not conceal malformed file cadence values."""
    with pytest.raises(kering.ConfigurationError):
        scheduling.resolveTocks(tocks, environ={'SALLY_ROOT_TOCK': '.005'})


@pytest.mark.parametrize('key,value', [
    pytest.param('SALLY_ROOT_TOCK', '0', id='root-rejects-zero'),
    pytest.param('SALLY_ROOT_TOCK', 'nan', id='root-rejects-nan'),
    pytest.param('SALLY_VERIFIER_TOCK', '-1', id='child-rejects-negative'),
])
def test_invalid_environment(key, value):
    """Scheduler environment strings must meet cadence-specific bounds."""
    with pytest.raises(kering.ConfigurationError):
        scheduling.resolveTocks(environ={key: value})


def test_scheduler_resolution_ignores_retry_and_timeout_settings():
    """Malformed verifier settings cannot interfere with cadence-only consumers."""
    with keri_configing.openCF(cls=configing.VerifierConfiger, temp=True) as cf:
        cf.put({'verifier': None})
        tocks = scheduling.loadTocks(
            cf,
            environ={'SALLY_RETRY_DELAY': 'invalid', 'SALLY_ESCROW_TIMEOUT': 'invalid'},
        )
        assert tocks['root'] == .03125


def test_null_tocks_in_file_are_rejected():
    """An explicit null block is an error, not an absent block using defaults."""
    with keri_configing.openCF(cls=configing.VerifierConfiger, temp=True) as cf:
        cf.put({'tocks': None})
        with pytest.raises(kering.ConfigurationError, match='tocks must be a mapping'):
            scheduling.loadTocks(cf, environ={})


def test_real_root_and_child_cadence(monkeypatch):
    """A zero child tock runs on successive ticks of the configured real root."""
    seen = []

    class Recorder(doing.Doer):
        """Record three scheduler turns, then finish the bounded real-clock run."""

        def recur(self, tyme):
            seen.append(tyme)
            return len(seen) == 3

    monkeypatch.setenv('SALLY_ROOT_TOCK', '.002')
    serving.run_doers([Recorder(tock=0)], expire=.02)
    assert seen == pytest.approx([0, .002, .004])


def test_verifier_generator_tocks_are_independent(open_verification_agent):
    """Real KEL/TEL/reply/exchange processors run at their independent child cadences."""
    with open_verification_agent(tock=.1, msg_tock=.02, escrow_tock=.03) as agent:
        assert [doer.tock for doer in agent.doers] == [.02, .03]

        # Prime each loop, then exercise one actual parser/escrow processing pass.
        message = agent.msgDo(tymth=lambda: 0, tock=.02)
        escrow = agent.escrowDo(tymth=lambda: 0, tock=.03)
        try:
            assert next(message) == .02
            assert next(message) == .02
            assert next(escrow) == .03
            assert next(escrow) == .03
            assert agent.tock == .1
        finally:
            message.close()
            escrow.close()


@pytest.mark.parametrize('options, expected_cadence', [
    pytest.param({}, 0, id='default-next-turn'),
    pytest.param({'escrow_tock': .005}, .005, id='configured-cadence'),
])
def test_communicator_cadence_does_not_rewrite_retry(open_communicator, options, expected_cadence):
    """Default/configured processing cadences stay independent of ten-second retry backoff."""
    with open_communicator(retry=10, tock=.01, **options) as (comm, _):
        gen = comm.escrowDo(tymth=lambda: 0, tock=0)
        try:
            assert next(gen) == 0  # Prime the generator with its initial yield.
            assert next(gen) == expected_cadence  # Process real empty LMDB escrows.
            assert comm.retry == 10
            assert comm.tock == .01
        finally:
            gen.close()


@pytest.mark.parametrize('filename', [
    pytest.param('sally.json', id='canonical-sally-config'),
    pytest.param('direct-sally.json', id='canonical-direct-config'),
])
def test_canonical_habery_configuration_remains_compatible(filename):
    """Canonical fixtures support default cadences and a separate tuned configuration."""
    import json
    from pathlib import Path

    canonical = json.loads(
        (Path(__file__).parents[2] / 'scripts/keri/cf' / filename).read_text(),
    )
    tuned_config = {
        **canonical,
        'tocks': {
            **canonical.get('tocks', {}),
            'verifier': {
                'root': .002,
                'communicatorEscrow': .01,
            },
        },
    }

    defaults = scheduling.resolveTocks(canonical.get('tocks', {}), environ={})
    tuned = scheduling.resolveTocks(tuned_config['tocks'], environ={})
    assert defaults['root'] == .03125
    assert tuned['root'] == .002
    assert tuned['communicatorEscrow'] == .01


@pytest.mark.parametrize('phase', [
    pytest.param('oobi', id='oobi-resolution'),
    pytest.param('auth', id='well-known-authentication'),
])
def test_bootstrap_completes_after_resolution(phase):
    """The real runner stays pending, then finishes once its bootstrap phase is resolved."""
    with habbing.openHby(name='bootstrap-lifecycle') as hby:
        url = 'http://127.0.0.1:1/oobi'
        pending = hby.db.oobis if phase == 'oobi' else hby.db.woobi
        pending.pin(keys=(url,), val=basing.OobiRecord())
        clock = doing.Doist(real=False, tock=.001, limit=.01)
        runner = BootstrapRunner(
            hby=hby, tymth=clock.tymen(), tocks=scheduling.resolveTocks(environ={}),
        )
        assert not runner.complete

        # Record the phase's successful outcome before running any network doers.
        if phase == 'oobi':
            hby.db.roobi.pin(keys=(url,), val=basing.OobiRecord(state='resolved'))
        else:
            hby.db.wkas.add(
                keys=(hby.makeHab(name='auth').pre,),
                val=basing.WellKnownAuthN(url=url, dt=helping.nowIso8601()),
            )

        # Let the runner finish through its normal scheduler lifecycle.
        clock.do(doers=[runner])
        assert runner.complete
        assert runner.done
