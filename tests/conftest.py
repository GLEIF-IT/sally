"""
Configure PyTest

Use this module to configure pytest
https://docs.pytest.org/en/latest/pythonpath.html

"""

import pytest

from keri.core import scheming, coring
from keri.help import helping


@pytest.fixture()
def mockHelpingNowUTC(monkeypatch):
    """
    Replace nowUTC universally with fixed value for testing
    """

    def mockNowUTC():
        """
        Use predetermined value for now (current time)
        '2021-01-01T00:00:00.000000+00:00'
        """
        return helping.fromIso8601("2021-01-01T00:00:00.000000+00:00")

    monkeypatch.setattr(helping, "nowUTC", mockNowUTC)


@pytest.fixture()
def mockCoringRandomNonce(monkeypatch):
    """ Replay randomNonce with fixed falue for testing"""

    def mockRandomNonce():
        return "A9XfpxIl1LcIkMhUSCCC8fgvkuX8gG9xK3SM-S8a8Y_U"

    monkeypatch.setattr(coring, "randomNonce", mockRandomNonce)


@pytest.fixture
def seeder():
    return DbSeed


class DbSeed:

    @staticmethod
    def load_schema(db):
        raw = (
            b'{"$id":"ELqriXX1-lbV9zgXP4BXxqJlpZTgFchll3cyjaCyVKiz",'
            b'"$schema":"http://json-schema.org/draft-07/schema#","title":"Qualified vLEI Issuer Credential",'
            b'"description":"A vLEI Credential issued by GLEIF to Qualified vLEI Issuers which allows the Qualified '
            b'vLEI Issuers to issue, verify and revoke Legal Entity vLEI Credentials and Legal Entity Official '
            b'Organizational Role vLEI Credentials","type":"object",'
            b'"credentialType":"QualifiedvLEIIssuervLEICredential","properties":{"v":{"description":"Version",'
            b'"type":"string"},"d":{"description":"Credential SAID","type":"string"},"u":{"description":"One time use '
            b'nonce","type":"string"},"i":{"description":"GLEIF Issuee AID","type":"string"},'
            b'"ri":{"description":"Credential status registry","type":"string"},"s":{"description":"Schema SAID",'
            b'"type":"string"},"a":{"oneOf":[{"description":"Attributes block SAID","type":"string"},'
            b'{"$id":"ELGgI0fkloqKWREXgqUfgS0bJybP1LChxCO3sqPSFHCj","description":"Attributes block","type":"object",'
            b'"properties":{"d":{"description":"Attributes block SAID","type":"string"},"i":{"description":"QVI '
            b'Issuee AID","type":"string"},"dt":{"description":"Issuance date time","type":"string",'
            b'"format":"date-time"},"LEI":{"description":"LEI of the requesting Legal Entity","type":"string",'
            b'"format":"ISO 17442"},"gracePeriod":{"description":"Allocated grace period","type":"integer",'
            b'"default":90}},"additionalProperties":false,"required":["i","dt","LEI"]}]},"r":{"oneOf":[{'
            b'"description":"Rules block SAID","type":"string"},'
            b'{"$id":"EPfyEVH-Ch3NtAAApTmmSs4casNk1g7DPSXIcJXqfFfb","description":"Rules block","type":"object",'
            b'"properties":{"d":{"description":"Rules block SAID","type":"string"},"usageDisclaimer":{'
            b'"description":"Usage Disclaimer","type":"object","properties":{"l":{"description":"Associated legal '
            b'language","type":"string","const":"Usage of a valid, unexpired, and non-revoked vLEI Credential, '
            b'as defined in the associated Ecosystem Governance Framework, does not assert that the Legal Entity is '
            b'trustworthy, honest, reputable in its business dealings, safe to do business with, or compliant with '
            b'any laws or that an implied or expressly intended purpose will be fulfilled."}}},"issuanceDisclaimer":{'
            b'"description":"Issuance Disclaimer","type":"object","properties":{"l":{"description":"Associated legal '
            b'language","type":"string","const":"All information in a valid, unexpired, and non-revoked vLEI '
            b'Credential, as defined in the associated Ecosystem Governance Framework, is accurate as of the date the '
            b'validation process was complete. The vLEI Credential has been issued to the legal entity or individual '
            b'named in the vLEI Credential as the subject; and the qualified vLEI Issuer exercised reasonable care to '
            b'perform the validation process set forth in the vLEI Ecosystem Governance Framework."}}}},'
            b'"additionalProperties":false,"required":["d","usageDisclaimer","issuanceDisclaimer"]}]}},'
            b'"additionalProperties":false,"required":["i","ri","s","d"]}')

        schemer = scheming.Schemer(raw=raw)
        db.schema.pin(schemer.said, schemer)

        raw = (
            b'{"$id":"EK0jwjJbtYLIynGtmXXLO5MGJ7BDuX2vr2_MhM9QjAxZ",'
            b'"$schema":"http://json-schema.org/draft-07/schema#","title":"Legal Entity vLEI Credential",'
            b'"description":"A vLEI Credential issued by a Qualified vLEI issuer to a Legal Entity","type":"object",'
            b'"credentialType":"LegalEntityvLEICredential","properties":{"v":{"description":"Version",'
            b'"type":"string"},"d":{"description":"Credential SAID","type":"string"},"u":{"description":"One time use '
            b'nonce","type":"string"},"i":{"description":"QVI Issuer AID","type":"string"},'
            b'"ri":{"description":"Credential status registry","type":"string"},"s":{"description":"Schema SAID",'
            b'"type":"string"},"a":{"oneOf":[{"description":"Attributes block SAID","type":"string"},'
            b'{"$id":"EJ6bFDLrv50bHmIDg-MSummpvYWsPa9CFygPUZyHoESj","description":"Attributes block","type":"object",'
            b'"properties":{"d":{"description":"Attributes block SAID","type":"string"},"i":{"description":"LE Issuer '
            b'AID","type":"string"},"dt":{"description":"issuance date time","type":"string","format":"date-time"},'
            b'"LEI":{"description":"LE Issuer AID","type":"string","format":"ISO 17442"}},'
            b'"additionalProperties":false,"required":["i","dt","LEI"]}]},"e":{"oneOf":[{"description":"Edges block '
            b'SAID","type":"string"},{"$id":"ECpGlTKMvrxVJp9z96IGO4y_JHbk1_5-D0IFEEW61vV9","description":"Edges '
            b'block","type":"object","properties":{"d":{"description":"Edges block SAID","type":"string"},'
            b'"qvi":{"description":"QVI node","type":"object","properties":{"n":{"description":"Issuer credential '
            b'SAID","type":"string"},"s":{"description":"SAID of required schema of the credential pointed to by this '
            b'node","type":"string","const":"ELqriXX1-lbV9zgXP4BXxqJlpZTgFchll3cyjaCyVKiz"}},'
            b'"additionalProperties":false,"required":["n","s"]}},"additionalProperties":false,"required":["d",'
            b'"qvi"]}]},"r":{"oneOf":[{"description":"Rules block SAID","type":"string"},'
            b'{"$id":"EPfyEVH-Ch3NtAAApTmmSs4casNk1g7DPSXIcJXqfFfb","description":"Rules block","type":"object",'
            b'"properties":{"d":{"description":"Rules block SAID","type":"string"},"usageDisclaimer":{'
            b'"description":"Usage Disclaimer","type":"object","properties":{"l":{"description":"Associated legal '
            b'language","type":"string","const":"Usage of a valid, unexpired, and non-revoked vLEI Credential, '
            b'as defined in the associated Ecosystem Governance Framework, does not assert that the Legal Entity is '
            b'trustworthy, honest, reputable in its business dealings, safe to do business with, or compliant with '
            b'any laws or that an implied or expressly intended purpose will be fulfilled."}}},"issuanceDisclaimer":{'
            b'"description":"Issuance Disclaimer","type":"object","properties":{"l":{"description":"Associated legal '
            b'language","type":"string","const":"All information in a valid, unexpired, and non-revoked vLEI '
            b'Credential, as defined in the associated Ecosystem Governance Framework, is accurate as of the date the '
            b'validation process was complete. The vLEI Credential has been issued to the legal entity or individual '
            b'named in the vLEI Credential as the subject; and the qualified vLEI Issuer exercised reasonable care to '
            b'perform the validation process set forth in the vLEI Ecosystem Governance Framework."}}}},'
            b'"additionalProperties":false,"required":["d","usageDisclaimer","issuanceDisclaimer"]}]}},'
            b'"additionalProperties":false,"required":["i","ri","s","d","e","r"]}')

        schemer = scheming.Schemer(raw=raw)
        db.schema.pin(schemer.said, schemer)

        raw = (b'{"$id":"EDqjl80uP0r_SNSp-yImpLGglTEbOwgO77wsOPjyRVKy",'
               b'"$schema":"http://json-schema.org/draft-07/schema#","title":"OOR Authorization vLEI Credential",'
               b'"description":"A vLEI Authorization Credential issued by a Legal Entity to a QVI for the '
               b'authorization of OOR credentials","type":"object","credentialType":"OORAuthorizationvLEICredential",'
               b'"properties":{"v":{"description":"Version","type":"string"},"d":{"description":"Credential SAID",'
               b'"type":"string"},"u":{"description":"One time use nonce","type":"string"},"i":{"description":"LE '
               b'Issuer AID","type":"string"},"ri":{"description":"Credential status registry","type":"string"},'
               b'"s":{"description":"Schema SAID","type":"string"},"a":{"oneOf":[{"description":"Attributes block '
               b'SAID","type":"string"},{"$id":"EPli-kppZ4gj8g4i3-FUx3ZG1H_UrMhXwzyP1E6uAot6",'
               b'"description":"Attributes block","type":"object","properties":{"d":{"description":"Attributes block '
               b'SAID","type":"string"},"i":{"description":"QVI Issuee AID","type":"string"},'
               b'"dt":{"description":"Issuance date time","format":"date-time","type":"string"},'
               b'"AID":{"description":"AID of the intended recipient of the ECR credential","type":"string"},'
               b'"LEI":{"description":"LEI of the requesting Legal Entity","type":"string","format":"ISO 17442"},'
               b'"personLegalName":{"description":"Requested recipient name as provided during identity assurance",'
               b'"type":"string"},"officialRole":{"description":"Requested role description i.e. \'Head of '
               b'Standards\'","type":"string"}},"additionalProperties":false,"required":["i","dt","AID","LEI",'
               b'"personLegalName","officialRole"]}]},"e":{"oneOf":[{"description":"Edges block SAID",'
               b'"type":"string"},{"$id":"EJavGIGF-D7nPo5a0mXOkVOvIqrmesc8hmfzrGnt1wWC","description":"Edges block",'
               b'"type":"object","properties":{"d":{"description":"Edges block SAID","type":"string"},'
               b'"le":{"description":"Chain to legal entity vLEI credential","type":"object","properties":{"n":{'
               b'"description":"QVI Issuer credential SAID","type":"string"},"s":{"description":"SAID of required '
               b'schema of the credential pointed to by this node","type":"string",'
               b'"const":"EK0jwjJbtYLIynGtmXXLO5MGJ7BDuX2vr2_MhM9QjAxZ"}},"additionalProperties":false,"required":['
               b'"n","s"]}},"additionalProperties":false,"required":["d","le"]}]},"r":{"oneOf":[{"description":"Rules '
               b'block SAID","type":"string"},{"$id":"EPfyEVH-Ch3NtAAApTmmSs4casNk1g7DPSXIcJXqfFfb",'
               b'"description":"Rules block","type":"object","properties":{"d":{"description":"Rules block SAID",'
               b'"type":"string"},"usageDisclaimer":{"description":"Usage Disclaimer","type":"object","properties":{'
               b'"l":{"description":"Associated legal language","type":"string","const":"Usage of a valid, unexpired, '
               b'and non-revoked vLEI Credential, as defined in the associated Ecosystem Governance Framework, '
               b'does not assert that the Legal Entity is trustworthy, honest, reputable in its business dealings, '
               b'safe to do business with, or compliant with any laws or that an implied or expressly intended '
               b'purpose will be fulfilled."}}},"issuanceDisclaimer":{"description":"Issuance Disclaimer",'
               b'"type":"object","properties":{"l":{"description":"Associated legal language","type":"string",'
               b'"const":"All information in a valid, unexpired, and non-revoked vLEI Credential, as defined in the '
               b'associated Ecosystem Governance Framework, is accurate as of the date the validation process was '
               b'complete. The vLEI Credential has been issued to the legal entity or individual named in the vLEI '
               b'Credential as the subject; and the qualified vLEI Issuer exercised reasonable care to perform the '
               b'validation process set forth in the vLEI Ecosystem Governance Framework."}}}},'
               b'"additionalProperties":false,"required":["d","usageDisclaimer","issuanceDisclaimer"]}]}},'
               b'"additionalProperties":false,"required":["i","ri","s","d","e","r"]}')

        schemer = scheming.Schemer(raw=raw)
        db.schema.pin(schemer.said, schemer)

        raw = (
            b'{"$id":"EIL-RWno8cEnkGTi9cr7-PFg_IXTPx9fZ0r9snFFZ0nm",'
            b'"$schema":"http://json-schema.org/draft-07/schema#","title":"Legal Entity Official Organizational Role '
            b'vLEI Credential","description":"A vLEI Role Credential issued by a Qualified vLEI issuer to official '
            b'representatives of a Legal Entity","type":"object",'
            b'"credentialType":"LegalEntityOfficialOrganizationalRolevLEICredential","properties":{"v":{'
            b'"description":"Version","type":"string"},"d":{"description":"Credential SAID","type":"string"},'
            b'"u":{"description":"One time use nonce","type":"string"},"i":{"description":"QVI Issuer AID",'
            b'"type":"string"},"ri":{"description":"Credential status registry","type":"string"},'
            b'"s":{"description":"Schema SAID","type":"string"},"a":{"oneOf":[{"description":"Attributes block SAID",'
            b'"type":"string"},{"$id":"ELDXjQ-FnKApK1DJhzmtKDcnfoJ9qusQr1Qz5g9MFt0o","description":"Attributes '
            b'block","type":"object","properties":{"d":{"description":"Attributes block SAID","type":"string"},'
            b'"i":{"description":"Person Issuee AID","type":"string"},"dt":{"description":"Issuance date time",'
            b'"type":"string","format":"date-time"},"LEI":{"description":"LEI of the Legal Entity","type":"string",'
            b'"format":"ISO 17442"},"personLegalName":{"description":"Recipient name as provided during identity '
            b'assurance","type":"string"},"officialRole":{"description":"Official role title","type":"string"}},'
            b'"additionalProperties":false,"required":["i","dt","LEI","personLegalName","officialRole"]}]},'
            b'"e":{"oneOf":[{"description":"Edges block SAID","type":"string"},'
            b'{"$id":"EHNH4Pz2oRBav1d2T9fnw-3GFBgtfipvttCh_rh9YeSf","description":"Edges block","type":"object",'
            b'"properties":{"d":{"description":"Edges block SAID","type":"string"},"auth":{"description":"Chain to '
            b'Auth vLEI credential from legal entity","type":"object","properties":{"n":{"description":"SAID of the '
            b'ACDC to which the edge connects","type":"string"},"s":{"description":"SAID of required schema of the '
            b'credential pointed to by this node","type":"string",'
            b'"const":"EDqjl80uP0r_SNSp-yImpLGglTEbOwgO77wsOPjyRVKy"},"o":{"description":"Operator indicating this '
            b'node is the issuer","type":"string","const":"I2I"}},"additionalProperties":false,"required":["n","s",'
            b'"o"]}},"additionalProperties":false,"required":["d","auth"]}]},"r":{"oneOf":[{"description":"Rules '
            b'block SAID","type":"string"},{"$id":"EPfyEVH-Ch3NtAAApTmmSs4casNk1g7DPSXIcJXqfFfb","description":"Rules '
            b'block","type":"object","properties":{"d":{"description":"Rules block SAID","type":"string"},'
            b'"usageDisclaimer":{"description":"Usage Disclaimer","type":"object","properties":{"l":{'
            b'"description":"Associated legal language","type":"string","const":"Usage of a valid, unexpired, '
            b'and non-revoked vLEI Credential, as defined in the associated Ecosystem Governance Framework, '
            b'does not assert that the Legal Entity is trustworthy, honest, reputable in its business dealings, '
            b'safe to do business with, or compliant with any laws or that an implied or expressly intended purpose '
            b'will be fulfilled."}}},"issuanceDisclaimer":{"description":"Issuance Disclaimer","type":"object",'
            b'"properties":{"l":{"description":"Associated legal language","type":"string","const":"All information '
            b'in a valid, unexpired, and non-revoked vLEI Credential, as defined in the associated Ecosystem '
            b'Governance Framework, is accurate as of the date the validation process was complete. The vLEI '
            b'Credential has been issued to the legal entity or individual named in the vLEI Credential as the '
            b'subject; and the qualified vLEI Issuer exercised reasonable care to perform the validation process set '
            b'forth in the vLEI Ecosystem Governance Framework."}}}},"additionalProperties":false,"required":["d",'
            b'"usageDisclaimer","issuanceDisclaimer"]}]}},"additionalProperties":false,"required":["i","ri","s","d",'
            b'"e","r"]}')

        schemer = scheming.Schemer(raw=raw)
        db.schema.pin(schemer.said, schemer)
