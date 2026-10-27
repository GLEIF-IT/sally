# -*- encoding: utf-8 -*-
"""
SALLY
sally.core.inspecting module

Read-only inspection and export of the credential state held by a Sally instance.
Used by the `sally debug state` command to compare two deployments and to migrate
credentials from one instance to another.
"""
import json

from keri import kering
from keri.app import signing
from keri.core import serdering
from keri.db import basing as kbasing, dbing
from keri.vdr import viring

from sally import ogler, log_name
from sally.core import basing, handling

logger = ogler.getLogger(log_name)

ISSUED = "issued"
REVOKED = "revoked"
NO_TEL = "no-tel-events"
UNKNOWN_REGISTRY = "unknown-registry"


def openStores(name, base, alias, readonly=True):
    """
    Open the three LMDB stores a running Sally instance uses, mirroring how `sally server start`
    names them: the Baser (KEL store) uses name and base, while the Reger (credential and TEL store)
    is named after the identifier alias and the CueBaser (escrow pipeline) after the keystore name.
    Neither of the latter two honours base.

    Parameters:
        name (str): keystore (Habery) name, the --name passed to `sally server start`
        base (str): optional keystore path prefix, the --base passed to `sally server start`
        alias (str): identifier alias, the --alias passed to `sally server start`
        readonly (bool): open LMDB environments read-only so a running instance is never modified

    Returns:
        tuple: (Baser, Reger, CueBaser)
    """
    # Opening a path that does not exist would create an empty database (even read-only), which
    # would look like an empty instance, so check first.
    missing = [f"{label} name={n} base={b!r}" for label, klas, n, b in (
        ("KEL store", kbasing.Baser, name, base),
        ("credential store", viring.Reger, alias, ""),
        ("escrow store", basing.CueBaser, name, ""),
    ) if not klas(name=n, base=b, temp=False, reopen=False).exists(name=n, base=b)]
    if missing:
        raise FileNotFoundError("database not found for " + "; ".join(missing))

    db = kbasing.Baser(name=name, base=base, temp=False, reopen=True, readonly=readonly)
    reger = viring.Reger(name=alias, db=db, temp=False, reopen=True, readonly=readonly)
    cdb = basing.CueBaser(name=name, temp=False, reopen=True, readonly=readonly)
    return db, reger, cdb


def credentialStatus(reger, creder):
    """
    Return the TEL status of a credential as seen by this instance's Reger.

    Returns:
        dict: status plus the TEL timestamp and sequence number when the TEL is known
    """
    regk = creder.regi
    try:
        tever = reger.tevers[regk]
    except KeyError:
        return dict(status=UNKNOWN_REGISTRY, telTimestamp=None, telSn=None)

    state = tever.vcState(creder.said)
    if state is None:
        return dict(status=NO_TEL, telTimestamp=None, telSn=None)

    status = ISSUED if state.et in (kering.Ilks.iss, kering.Ilks.bis) else REVOKED
    return dict(status=status, telTimestamp=state.dt, telSn=int(state.s, 16))


def edgeSaids(creder):
    """Return a mapping of edge name to chained credential SAID for a credential."""
    edges = creder.edge or {}
    return {k: v["n"] for k, v in edges.items() if isinstance(v, dict) and "n" in v}


def credentialRecord(reger, creder):
    """Build the inspection record for one credential."""
    attrib = creder.attrib or {}
    edges = edgeSaids(creder)
    record = dict(
        said=creder.said,
        type=handling.type_to_name.get(creder.schema, "unknown"),
        schema=creder.schema,
        issuer=creder.issuer,
        issuee=attrib.get("i"),
        LEI=attrib.get("LEI"),
        registry=creder.regi,
        verified=reger.saved.get(keys=(creder.said,)) is not None,
        edges=edges,
        missingEdges=[said for said in edges.values() if reger.creds.get(keys=(said,)) is None],
    )
    record.update(credentialStatus(reger, creder))
    return record


def snKeyParts(key):
    """Split a TEL escrow key of the form b'<pre>.<sn hex>' into (pre, sn)."""
    pre, _, sn = bytes(key).rpartition(b'.')
    try:
        return pre.decode("utf-8"), int(sn, 16)
    except ValueError:
        return bytes(key).decode("utf-8", errors="replace"), None


def telOnlyCredentials(reger):
    """
    Credentials this instance has TEL events for but no ACDC. This is the state left behind when a
    revocation (with its issuance) arrives for a credential that was never presented here: the TEL
    records it as revoked, but there is nothing to report to the webhook.
    """
    registries = {keys[-1] for keys, _ in reger.states.getItemIter()}
    prefixes = set()
    for key, _ in reger.getTopItemIter(reger.tels):
        pre, _ = snKeyParts(key)
        prefixes.add(pre)

    out = []
    for pre in sorted(prefixes):
        if pre in registries or reger.creds.get(keys=(pre,)) is not None:
            continue
        digs = [dig for _, _, dig in reger.getTelItemPreIter(pre=pre.encode("utf-8"))]
        if not digs:
            continue
        raw = reger.getTvt(dbing.dgKey(pre, bytes(digs[-1])))
        serder = serdering.SerderKERI(raw=bytes(raw))
        ilk = serder.ked["t"]
        status = ISSUED if ilk in (kering.Ilks.iss, kering.Ilks.bis) else REVOKED
        out.append(dict(prefix=pre, registry=serder.ked.get("ri"), status=status,
                        telSn=len(digs) - 1, telTimestamp=serder.ked.get("dt")))
    return out


def collect(db, reger, cdb, saids=None):
    """
    Collect everything this instance knows about credentials, registries, and escrows.

    Parameters:
        db (Baser): KEL store
        reger (Reger): credential and TEL store
        cdb (CueBaser): webhook escrow pipeline store
        saids (list[str] | None): restrict the credential listing to these SAIDs

    Returns:
        dict: JSON serializable inspection report
    """
    identifiers = [dict(name=rec.name or keys[-1], prefix=rec.hid) for keys, rec in db.habs.getItemIter()]

    registries = [dict(registry=keys[-1], issuer=rsr.ii, sn=int(rsr.s, 16), lastEvent=rsr.et)
                  for keys, rsr in reger.states.getItemIter()]

    credentials = []
    for (said,), creder in reger.creds.getItemIter():
        if saids and said not in saids:
            continue
        credentials.append(credentialRecord(reger, creder))

    telOnly = telOnlyCredentials(reger)

    telOutOfOrder = []
    for key, _ in reger.getTopItemIter(reger.oots):
        pre, sn = snKeyParts(key)
        telOutOfOrder.append(dict(prefix=pre, sn=sn, knownCredential=reger.creds.get(keys=(pre,)) is not None))

    escrows = dict(
        telOutOfOrder=telOutOfOrder,
        telPartialWitness=sum(1 for _ in reger.getTopItemIter(reger.twes)),
        telAnchorless=sum(1 for _ in reger.getTopItemIter(reger.taes)),
        acdcMissingRegistry=[keys[-1] for keys, _ in reger.mre.getItemIter()],
        acdcMissingChain=[keys[-1] for keys, _ in reger.mce.getItemIter()],
        acdcMissingSchema=[keys[-1] for keys, _ in reger.mse.getItemIter()],
        acdcMissingSignature=[keys[-1] for keys, _ in reger.cmse.getItemIter()],
    )

    pipeline = dict(
        counts=cdb.getCounts(),
        iss=[keys[0] for keys, _ in cdb.iss.getItemIter()],
        rev=[keys[0] for keys, _ in cdb.rev.getItemIter()],
        recv=[keys[0] for keys, _ in cdb.recv.getItemIter()],
        revk=[keys[0] for keys, _ in cdb.revk.getItemIter()],
        ack=[keys[0] for keys, _ in cdb.ack.getItemIter()],
    )

    return dict(
        identifiers=identifiers,
        registries=registries,
        credentials=credentials,
        telOnly=telOnly,
        escrows=escrows,
        pipeline=pipeline,
    )


def exportCredential(db, reger, said, seen=None):
    """
    Serialize one credential and everything needed to verify it elsewhere as a CESR stream:
    the issuer KEL, the registry TEL, the credential TEL, every chained credential (recursively),
    and finally the ACDC with its anchoring attachment.

    Parameters:
        db (Baser): KEL store
        reger (Reger): credential and TEL store
        said (str): SAID of the credential to export
        seen (set | None): prefixes already written to the stream, used to avoid duplicates

    Returns:
        bytes: CESR stream suitable for PUT to a direct-mode Sally at '/'
    """
    seen = set() if seen is None else seen
    creder, prefixer, seqner, saider = reger.cloneCred(said=said)

    msgs = bytearray()
    for label, pre, cloner in (("issuer KEL", creder.issuer, db.clonePreIter),
                               ("registry TEL", creder.regi, reger.clonePreIter)):
        if pre in seen:
            continue
        seen.add(pre)
        count = 0
        for msg in cloner(pre=pre):
            msgs.extend(msg)
            count += 1
        if count == 0:
            logger.error(f"{label} {pre} for credential {said} is not in this instance; export is incomplete")

    for esaid in edgeSaids(creder).values():
        if esaid in seen:
            continue
        if reger.creds.get(keys=(esaid,)) is None:
            logger.error(f"chained credential {esaid} of {said} is not in this instance; export is incomplete")
            continue
        msgs.extend(exportCredential(db, reger, esaid, seen=seen))

    if creder.said in seen:
        return bytes(msgs)
    seen.add(creder.said)

    for msg in reger.clonePreIter(pre=creder.said):
        msgs.extend(msg)
    msgs.extend(creder.raw)
    msgs.extend(signing.serialize(creder, prefixer, seqner, saider))
    return bytes(msgs)


def exportCredentials(db, reger, saids=None):
    """
    Export every verified credential this instance holds, or just the given SAIDs, as one CESR stream.

    Returns:
        bytes: concatenated CESR stream
    """
    if not saids:
        saids = [keys[0] for keys, _ in reger.saved.getItemIter()]

    seen = set()
    msgs = bytearray()
    for said in saids:
        if reger.creds.get(keys=(said,)) is None:
            logger.error(f"credential {said} is not in this instance; skipping")
            continue
        msgs.extend(exportCredential(db, reger, said, seen=seen))
    return bytes(msgs)


def formatReport(report):
    """Render an inspection report as human readable text."""
    lines = []
    lines.append("Identifiers")
    for ident in report["identifiers"]:
        lines.append(f"  {ident['name']}: {ident['prefix']}")

    lines.append("")
    lines.append(f"Registries ({len(report['registries'])})")
    for reg in report["registries"]:
        lines.append(f"  {reg['registry']} issuer={reg['issuer']} sn={reg['sn']} last={reg['lastEvent']}")

    lines.append("")
    lines.append(f"Credentials ({len(report['credentials'])})")
    for cred in report["credentials"]:
        lines.append(f"  {cred['said']} {cred['type']} {cred['status']} verified={cred['verified']}")
        lines.append(f"    issuer={cred['issuer']}")
        lines.append(f"    issuee={cred['issuee']} LEI={cred['LEI']}")
        lines.append(f"    registry={cred['registry']} telSn={cred['telSn']} telTimestamp={cred['telTimestamp']}")
        for name, esaid in cred["edges"].items():
            missing = " (MISSING)" if esaid in cred["missingEdges"] else ""
            lines.append(f"    edge {name}={esaid}{missing}")

    lines.append("")
    lines.append(f"TEL only, no ACDC ({len(report['telOnly'])})")
    for item in report["telOnly"]:
        lines.append(f"  {item['prefix']} {item['status']} registry={item['registry']} telSn={item['telSn']} "
                     f"telTimestamp={item['telTimestamp']}")

    esc = report["escrows"]
    lines.append("")
    lines.append("Escrows")
    lines.append(f"  TEL out of order ({len(esc['telOutOfOrder'])})")
    for item in esc["telOutOfOrder"]:
        known = "known" if item["knownCredential"] else "unknown"
        lines.append(f"    {item['prefix']} sn={item['sn']} credential={known}")
    lines.append(f"  TEL partial witness: {esc['telPartialWitness']}")
    lines.append(f"  TEL anchorless: {esc['telAnchorless']}")
    for label, key in (("ACDC missing registry", "acdcMissingRegistry"),
                       ("ACDC missing chain", "acdcMissingChain"),
                       ("ACDC missing schema", "acdcMissingSchema"),
                       ("ACDC missing signature", "acdcMissingSignature")):
        lines.append(f"  {label} ({len(esc[key])})")
        for said in esc[key]:
            lines.append(f"    {said}")

    pipe = report["pipeline"]
    lines.append("")
    lines.append("Webhook pipeline")
    for key in ("iss", "rev", "recv", "revk", "ack"):
        lines.append(f"  {key} ({len(pipe[key])})")
        for said in pipe[key]:
            lines.append(f"    {said}")

    return "\n".join(lines)


def toJson(report):
    """Render an inspection report as indented JSON."""
    return json.dumps(report, indent=2)


def summarize(report):
    """
    Reduce a collect() report to counts suitable for metrics.

    Parameters:
        report (dict): output of collect()

    Returns:
        dict: credentials -> {(type, status): count}, unverified, missingEdges, telOnly,
              telOutOfOrderUnknown, registries
    """
    credentials = {}
    unverified = 0
    missingEdges = 0
    for cred in report["credentials"]:
        key = (cred["type"], cred["status"])
        credentials[key] = credentials.get(key, 0) + 1
        if not cred["verified"]:
            unverified += 1
        if cred["missingEdges"]:
            missingEdges += 1

    escrows = report["escrows"]
    return dict(
        credentials=credentials,
        unverified=unverified,
        missingEdges=missingEdges,
        telOnly=len(report["telOnly"]),
        telOutOfOrderUnknown=sum(1 for e in escrows["telOutOfOrder"] if not e["knownCredential"]),
        registries=len(report["registries"]),
    )
