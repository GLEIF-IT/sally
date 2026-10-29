# -*- encoding: utf-8 -*-
"""
SALLY
sally.core.httping module

Testing httping utils
"""
from base64 import urlsafe_b64decode as decodeB64
from types import SimpleNamespace

import falcon
import pytest
from hio.core import http
from hio.help import Hict
from http_sfv import Dictionary
from keri.app import habbing
from keri.end import ending

from sally.core import httping


@pytest.mark.parametrize("peer", [("192.0.2.10", 12345), ("2001:db8::10", 12345)])
@pytest.mark.parametrize("forwarded", [None, "203.0.113.1, 198.51.100.2"])
def test_wsgi_adapter_changes_only_peer_ip_metadata(peer, forwarded):
    body = b'{"credential":"fixture"}'
    headers = Hict([("Content-Type", "application/json"),
                    ("Signature-Input", 'sig0=("@method" "@path")'),
                    ("Signature", 'sig0="fixture-signature"')])
    if forwarded:
        headers["X-Forwarded-For"] = forwarded
    request = SimpleNamespace(body=body, method="POST", path="/credential", query="mode=test",
                              version=(1, 1), headers=headers, length=len(body),
                              remoter=SimpleNamespace(ca=peer))
    server = httping.WsgiServer(port=9723)
    original = http.Server.buildEnviron(server, request)
    adapted = server.buildEnviron(request)

    falcon_request = falcon.Request(adapted)
    assert falcon_request.remote_addr == peer[0]
    assert falcon_request.access_route == (forwarded.split(", ") if forwarded else []) + [peer[0]]
    assert request.remoter.ca == peer  # Transport still retains the port.
    assert original.pop("REMOTE_ADDR") == peer
    assert adapted.pop("REMOTE_ADDR") == peer[0]
    assert original.pop("wsgi.input").read() == adapted.pop("wsgi.input").read() == body
    assert adapted == original  # Includes method, path, query, headers, and WSGI flags.


def test_siginput(mockHelpingNowUTC):
    print()
    with habbing.openHab(name="test", base="test", temp=True, salt=b'0123456789abcdef') as (hby, hab):
        headers = Hict([
            ("Content-Type", "application/json"),
            ("Content-Length", "256"),
            ("Connection", "close"),
            ("Sally-Resource", "EWJkQCFvKuyxZi582yJPb0wcwuW3VXmFNuvbQuBpgmIs"),
            ("Sally-Timestamp", "2022-09-24T00:05:48.196795+00:00"),
        ])

        header, unq = httping.siginput(
            hab, "sig0", "POST", "/sally", headers,
            fields=[
                "Sally-Resource",
                "@method",
                "@path",
                "Sally-Timestamp"
            ],
            alg="ed25519", keyid=hab.pre)

        headers.extend(header)
        signage = ending.Signage(markers=dict(sig0=unq), indexed=False, signer=None, ordinal=None, digest=None,
                                 kind=None)
        headers.extend(ending.signature([signage]))

        assert dict(headers) == {
            'Content-Type': 'application/json',
            'Content-Length': '256',
            'Connection': 'close',
            'Sally-Resource': 'EWJkQCFvKuyxZi582yJPb0wcwuW3VXmFNuvbQuBpgmIs',
            'Sally-Timestamp': '2022-09-24T00:05:48.196795+00:00',
            'Signature-Input': 'sig0=("sally-resource" "@method" "@path" "sally-timestamp");created=1609459200;keyid="EIaGMMWJFPmtXznY1IIiKDIrg-vIyge6mBl2QV8dDjI3";alg="ed25519"',
            'Signature': 'indexed="?0";sig0="1G-ItA3IPA8g30--svDMxlWW7YG_6PFf1VsUaV445PLXDDM9tTL7PvnEW9Uv8y2mwaGOdpIojvBbGMOzdVccCg=="'
        }

        siginput = headers["Signature-Input"]
        signature = headers["Signature"]

        inputs = httping.desiginput(siginput.encode("utf-8"))
        assert len(inputs) == 1
        inputage = inputs[0]

        assert inputage.name == 'sig0'
        assert inputage.fields == ['sally-resource', "@method", "@path", "sally-timestamp"]
        assert inputage.created == 1609459200
        assert inputage.alg == "ed25519"
        assert inputage.keyid == hab.pre
        assert inputage.expires is None
        assert inputage.nonce is None
        assert inputage.context is None

        items = []
        for field in inputage.fields:
            if field.startswith("@"):
                if field == "@method":
                    items.append(f'"{field}": POST')
                elif field == "@path":
                    items.append(f'"{field}": /sally')

            else:
                field = field.lower()
                if field not in headers:
                    continue

                value = httping.normalize(headers[field])
                items.append(f'"{field}": {value}')

        values = [f"({' '.join(inputage.fields)})", f"created={inputage.created}"]
        if inputage.expires is not None:
            values.append(f"expires={inputage.expires}")
        if inputage.nonce is not None:
            values.append(f"nonce={inputage.nonce}")
        if inputage.keyid is not None:
            values.append(f"keyid={inputage.keyid}")
        if inputage.context is not None:
            values.append(f"context={inputage.context}")
        if inputage.alg is not None:
            values.append(f"alg={inputage.alg}")

        params = ';'.join(values)

        items.append(f'"@signature-params: {params}"')
        ser = "\n".join(items).encode("utf-8")

        signage = Dictionary()
        signage.parse(signature.encode("utf-8"))

        raw = decodeB64(signage["indexed"].params[inputage.name])
        assert hab.kever.verfers[0].verify(sig=raw, ser=ser) is True
