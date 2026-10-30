"""Verifier settings, units and config-reader behavior, independently of scheduling."""
import copy
import datetime
import time
from contextlib import closing
from pathlib import Path

import falcon
import pytest
from hio.core import http, tcp
from keri import kering

from sally.core import configing, handling, scheduling


def test_defaults_and_precedence():
    """CLI > environment > file > defaults applies only to retry/deadline settings."""
    defaults = configing.resolveVerifierConfig(environ={})
    assert defaults.retry_delay_seconds == 3
    assert defaults.escrow_timeout_seconds == 600
    assert defaults.bootstrap_timeout_seconds == 30
    assert defaults.webhook_request_timeout_seconds == 0

    config = {
        'verifier': {
            'retryDelay': 2,
            'escrowTimeout': 4,
            'bootstrapTimeout': 9,
        },
    }
    original = copy.deepcopy(config)
    resolved = configing.resolveVerifierConfig(
        config,
        environ={'SALLY_RETRY_DELAY': '.25'},
        retry=.5,
    )
    assert resolved.retry_delay_seconds == .5
    assert resolved.escrow_timeout_seconds == 4
    assert resolved.bootstrap_timeout_seconds == 9
    assert config == original

    # Without a CLI value, environment wins; without either, file values win.
    assert configing.resolveVerifierConfig(
        config, environ={'SALLY_RETRY_DELAY': '.25'},
    ).retry_delay_seconds == .25
    assert configing.resolveVerifierConfig(config, environ={}).retry_delay_seconds == 2


@pytest.mark.parametrize('config', [
    pytest.param({'verifier': None}, id='verifier-must-be-mapping'),
    pytest.param({'verifier': {'typo': 1}}, id='unknown-verifier-setting'),
    pytest.param({'verifier': {'retryDelay': -1}}, id='negative-retry-delay'),
    pytest.param({'verifier': {'escrowTimeout': 0}}, id='zero-escrow-lifetime'),
    pytest.param({'verifier': {'bootstrapTimeout': 0}}, id='zero-bootstrap-lifetime'),
])
def test_invalid_file_even_when_environment_overrides(config):
    """A valid override must not conceal malformed retry or deadline file values."""
    with pytest.raises(kering.ConfigurationError):
        configing.resolveVerifierConfig(
            config,
            environ={
                'SALLY_RETRY_DELAY': '1',
                'SALLY_WEBHOOK_REQUEST_TIMEOUT': '1',
                'SALLY_ESCROW_TIMEOUT': '1',
                'SALLY_BOOTSTRAP_TIMEOUT': '1',
            },
        )


@pytest.mark.parametrize('key,value', [
    pytest.param('SALLY_RETRY_DELAY', '', id='empty-retry-string'),
    pytest.param('SALLY_ESCROW_TIMEOUT', '0', id='zero-escrow-lifetime'),
    pytest.param('SALLY_WEBHOOK_REQUEST_TIMEOUT', 'nan', id='nan-request-timeout'),
])
def test_invalid_environment(key, value):
    """Environment durations are finite numeric strings with setting-specific bounds."""
    with pytest.raises(kering.ConfigurationError):
        configing.resolveVerifierConfig(environ={key: value})


@pytest.mark.parametrize('value', [
    pytest.param(True, id='boolean'),
    pytest.param(-1, id='negative'),
    pytest.param(float('nan'), id='nan'),
    pytest.param(float('inf'), id='infinity'),
    pytest.param('1', id='file-string'),
])
def test_validate_duration_rejects_invalid_numbers(value):
    """The shared scalar validator does not parse units or accept booleans as numbers."""
    with pytest.raises(kering.ConfigurationError):
        configing.validateDuration(value, 'test interval')


def test_fractional_seconds_and_zero_semantics():
    """Zero disables request deadlines or retry waiting, but not escrow/bootstrap limits."""
    resolved = configing.resolveVerifierConfig(
        {
            'verifier': {
                'retryDelay': 0,
                'escrowTimeout': .5,
                'bootstrapTimeout': .25,
                'webhookRequestTimeout': 0,
            },
        },
        environ={},
    )
    assert resolved == configing.VerifierConfig(0, .5, .25, 0)
    with pytest.raises(kering.ConfigurationError):
        configing.validateDuration(0, 'positive interval', positive=True)


def test_verifier_resolution_ignores_tocks():
    """Invalid scheduler values belong to the scheduler resolver, not verifier config."""
    resolved = configing.resolveVerifierConfig(
        {'tocks': None}, environ={'SALLY_ROOT_TOCK': 'invalid'},
    )
    assert resolved.escrow_timeout_seconds == 600


def test_fast_processing_retains_failed_webhook_backoff(monkeypatch, open_communicator, geda_qvi):
    """A real signed webhook failure stays queued until its two-second retry deadline."""
    now = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
    monkeypatch.setattr(handling.helping, 'nowUTC', lambda: now)
    _, geda, qvi = geda_qvi
    requests = []

    class UnavailableWebhook:
        """Receive the actual HTTP request and reject it with a service-unavailable response."""

        def on_post(self, req, resp):
            requests.append(req.media)
            resp.status = falcon.HTTP_503

    app = falcon.App()
    app.add_route('/', UnavailableWebhook())
    # Supplying TCP explicitly permits an ephemeral port (HTTP maps port zero to 80).
    servant = tcp.Server(ha=('127.0.0.1', 0))
    with http.serving.openServer(servant=servant, app=app) as server:
        servant.eha = servant.ha  # HIO retains port zero in its advertised address.
        hook = f'http://127.0.0.1:{server.servant.ha[1]}/'
        with open_communicator(hook=hook, retry=2, escrow_tock=0) as (comm, credential):
            assert comm.timeout == 600  # The Python API's default escrow lifetime is in seconds.
            server.wind(comm.tymth)
            said = credential.said
            dates = handling.coring.Dater().qb64
            comm.cdb.recv.pin(keys=(said, dates), val=credential)
            comm.processReceived(comm.cdb.recv, 'iss')
            client, client_doer = comm.clients[said]

            # Drive real local HTTP I/O to a response, bounded independently of retry time.
            for _ in range(1000):
                client.service()
                server.service()
                if client.responses:
                    break
                time.sleep(.001)
            assert client.responses, 'local webhook did not produce its HTTP response'
            request = requests[0]
            assert request['actor'] == geda.pre
            assert request['data']['credential'] == said
            assert request['data']['issuer'] == geda.pre
            assert request['data']['recipient'] == qvi.pre
            comm.processReceived(comm.cdb.recv, 'iss')
            assert comm.cdb.recv.get(keys=(said, dates)).said == said
            assert not client.connector.opened
            assert client_doer not in comm.doers

            # Fast processing before backoff expires must not create another client.
            now += datetime.timedelta(seconds=.1)
            comm.processReceived(comm.cdb.recv, 'iss')
            assert said not in comm.clients

            # At two seconds, the failed delivery may be attempted again.
            now += datetime.timedelta(seconds=1.9)
            comm.processReceived(comm.cdb.recv, 'iss')
            assert said in comm.clients
            assert comm.clients[said][0] is not client
            assert said not in comm.retry_at


@pytest.mark.parametrize('config_file', [
    pytest.param('test', id='explicit-config-name'),
    pytest.param(None, id='default-keystore-config-name'),
])
def test_reopen_uses_selected_config_for_bootstrap_and_service(monkeypatch, tmp_path, config_file):
    """Real startup reopens the same habitat and reads its selected config into both domains."""
    from keri.app import habbing, keeping
    from sally.app.cli.commands.server import start

    # Isolate the CLI's persistent paths without replacing any KERI object or method.
    monkeypatch.setattr(keeping.Keeper, 'HeadDirPath', str(tmp_path))
    monkeypatch.setattr(habbing.basing.Baser, 'HeadDirPath', str(tmp_path))
    config = {
        'tocks': {
            'mailboxEscrow': .125,
            'verifier': {
                'root': .002,
                'bootstrapRoot': .005,
            },
        },
        'verifier': {
            'bootstrapTimeout': 7,
            'webhookRequestTimeout': 20,
        },
    }
    with closing(configing.VerifierConfiger(
        name=config_file or 'sally', base='', headDirPath=str(tmp_path), temp=False,
        reopen=True,
    )) as cf:
        cf.put(config)
        contents = Path(cf.path).read_bytes()

    prefix = None
    for reopening in (False, True):
        hby = start.init_habery('sally', '', None, config_file, str(tmp_path), None)
        try:
            if not reopening:
                prefix = hby.makeHab(name='sally').pre
            else:
                assert hby.habByName('sally').pre == prefix
            # KERIpy reads its own cadences; Sally reads the complete shared file.
            assert hby.tocks['mailboxEscrow'] == .125
            assert 'verifier' not in hby.tocks
            assert hby.sally_tocks['root'] == .002
            assert hby.sally_tocks['bootstrapRoot'] == .005
            # Exercise the actual server default, with no file or CLI retry override.
            assert hby.verifier_config.retry_delay_seconds == 10
            assert hby.verifier_config.escrow_timeout_seconds == 600
            assert hby.verifier_config.webhook_request_timeout_seconds == 20
            assert hby.verifier_config.bootstrap_timeout_seconds == 7
            assert hby.cf.getVerifierConfig() == config
            assert Path(hby.cf.path).read_bytes() == contents
        finally:
            hby.close()


@pytest.mark.parametrize('expired, enabled', [
    # Expiry decides retry versus drop only when request deadlines are enabled.
    pytest.param(False, True, id='deadline-cleans-up-and-retries-live-escrow'),
    pytest.param(True, True, id='deadline-cleans-up-and-drops-expired-escrow'),
    pytest.param(False, False, id='disabled-deadline-keeps-pending-client'),
])
def test_silent_webhook_deadline_cleans_up_and_respects_escrow_lifetime(
        monkeypatch, open_communicator, expired, enabled):
    """A request deadline releases its client and retries or drops the two-second escrow."""
    # Calendar time controls escrow age; elapsed request time controls the HTTP deadline.
    now = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
    request_clock_seconds = 10.0
    monkeypatch.setattr(handling.helping, 'nowUTC', lambda: now)
    monkeypatch.setattr(handling.time, 'monotonic', lambda: request_clock_seconds)
    settings = configing.resolveVerifierConfig(
        {'verifier': {'escrowTimeout': 2}}, environ={},
    )
    with open_communicator(
        timeout=settings.escrow_timeout_seconds, retry=2, request_timeout=1 if enabled else 0,
    ) as (comm, credential):
        said = credential.said
        # Straddle two seconds, so interpreting the lifetime as minutes fails this test.
        queued = now - datetime.timedelta(seconds=2.1 if expired else 1.9)
        dates = handling.coring.Dater(dts=queued.isoformat(timespec='microseconds')).qb64
        comm.cdb.recv.pin(keys=(said, dates), val=credential)
        # Leave real client I/O unserviced: the queued request has no response.
        comm.processReceived(comm.cdb.recv, 'iss')
        client, client_doer = comm.clients[said]
        assert client_doer in comm.doers

        comm.processReceived(comm.cdb.recv, 'iss')
        assert client.connector.opened
        # Reach the HTTP deadline while keeping the credential's age unchanged.
        request_clock_seconds += 1
        comm.processReceived(comm.cdb.recv, 'iss')

        if not enabled:
            # Opting out leaves the live escrow's unanswered request active.
            assert client.connector.opened
            assert client_doer in comm.doers
            assert said in comm.clients
            assert comm.cdb.recv.get(keys=(said, dates)) is not None
            return

        # Release the timed-out request; escrow age determines drop versus retry.
        assert not client.connector.opened
        assert client_doer not in comm.doers
        assert said not in comm.clients
        assert said not in comm.requested_at
        assert comm.metrics.get('sally_exceptions_total', kind='webhook_request_timeout') == 1
        if expired:
            assert comm.cdb.recv.get(keys=(said, dates)) is None
            assert said not in comm.retry_at
        else:
            assert comm.cdb.recv.get(keys=(said, dates)).said == said
            assert comm.retry_at[said] == now + datetime.timedelta(seconds=2)


def test_config_reader_keeps_keripy_validation_strict(tmp_path):
    """Hiding Sally's namespace must not hide misspelled KERIpy configuration keys."""
    from keri.app import configing as keri_configing, tocking

    with keri_configing.openCF(
        cls=configing.VerifierConfiger,
        name='timing',
        headDirPath=str(tmp_path),
        temp=True,
    ) as cf:
        cf.put({
            'tocks': {
                'misspelledKeriTock': 0,
                'verifier': {'root': .002},
            },
        })
        with pytest.raises(kering.ConfigurationError, match='misspelledKeriTock'):
            tocking.resolveTocks(cf.get()['tocks'], environ={})


def test_cli_escrow_timeout_uses_seconds():
    """An explicit CLI lifetime reaches the verifier resolver without minute conversion."""
    from sally.app.cli.commands.server import start

    args = start.parser.parse_args([
        '--alias', 'test', '--web-hook', 'http://example.test/', '--auth', 'authority',
        '--escrow-timeout', '2',
    ])
    assert configing.resolveVerifierConfig(environ={}, timeout=args.escrow_timeout).escrow_timeout_seconds == 2


@pytest.mark.parametrize('method, escrow', [
    pytest.param('processPresentations', 'iss', id='presentation-expiry'),
    pytest.param('processRevocations', 'rev', id='revocation-expiry'),
])
def test_pending_credential_expiry_uses_seconds(monkeypatch, open_communicator, method, escrow):
    """Intake escrows retain a pending credential before two seconds and drop it after."""
    now = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
    monkeypatch.setattr(handling.helping, 'nowUTC', lambda: now)
    with open_communicator(timeout=2) as (comm, credential):
        # The ACDC is not yet verified/stored in Reger, so intake must wait for it.
        pending = getattr(comm.cdb, escrow)
        pending.pin(keys=(credential.said,), val=handling.coring.Dater())
        process = getattr(comm, method)

        now += datetime.timedelta(seconds=1.9)
        process()
        assert pending.get(keys=(credential.said,)) is not None

        # Cross the same escrow deadline without sleeping.
        now += datetime.timedelta(seconds=.2)
        process()
        assert pending.get(keys=(credential.said,)) is None


def test_service_setup_uses_resolved_domains(monkeypatch, tmp_path, open_communicator):
    """Real service components receive cached cadence and deadline settings independently."""
    from keri.app import notifying, storing
    from keri.vdr import viring
    from sally.core import basing, serving

    # Service setup owns persistent auxiliary stores; keep every one inside this test.
    for store in (basing.CueBaser, storing.Mailboxer, notifying.Noter, viring.Reger):
        monkeypatch.setattr(store, 'HeadDirPath', str(tmp_path))
    tocks = scheduling.resolveTocks({
        'verifier': {
            'communicatorEscrow': .005,
            'webhookClient': .002,
        },
    }, environ={})
    settings = configing.VerifierConfig(
        retry_delay_seconds=.25,
        escrow_timeout_seconds=2,
        bootstrap_timeout_seconds=7,
        webhook_request_timeout_seconds=1,
    )
    with open_communicator() as (context, _):
        doers = serving.setupDoers(
            context.hby, context.hab, alias=context.hab.name, http_port=0,
            hook=context.hook, auth=context.auth, direct=True,
            tocks=tocks, verifier_config=settings,
        )
        comm = next(doer for doer in doers if isinstance(doer, handling.Communicator))
        handler = next(doer for doer in doers if isinstance(doer, handling.PresentationProofHandler))
        server = next(doer.server for doer in doers if isinstance(doer, http.ServerDoer))
        mailbox = server.app._router.find('/')[0].mbx
        try:
            assert comm.escrow_tock == .005
            assert comm.client_tock == .002
            assert comm.retry == .25
            assert comm.timeout == 2
            assert comm.request_timeout == 1
        finally:
            # Close the independently opened service stores as well as fixture state.
            server.close()
            mailbox.close(clear=True)
            handler.notifier.noter.close(clear=True)
            comm.cdb.close(clear=True)
            comm.reger.close(clear=True)
