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
            b'{"$id":"EE4R4HtygsIDdW-XJiA3CJEs5Yrb2eK5YeohAy_rdyZB",'
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
            b'{"$id":"EEZoJ34aN10GtRMEqMW7ZHoa3KagEiO_fnirxQAsNs8j","description":"Rules block","type":"object",'
            b'"properties":{"d":{"description":"Rules block SAID","type":"string"},"usageDisclaimer":{'
            b'"description":"Usage Disclaimer","type":"object","properties":{"l":{"description":"Associated legal '
            b'language","type":"string","const":"Usage of a valid Legal Entity vLEI Credential does not assert that '
            b'the Legal Entity is trustworthy, honest, reputable in its business dealings, safe to do business with, '
            b'or compliant with any laws."}}},"issuanceDisclaimer":{"description":"Issuance Disclaimer",'
            b'"type":"object","properties":{"l":{"description":"Associated legal language","type":"string",'
            b'"const":"Issuance of a valid Legal Entity vLEI Credential only establishes that the information in the '
            b'requirements in the Identity Verification section 6.3 of the Credential Governance Framework were met '
            b'in accordance with the vLEI Ecosystem Governance Framework."}}}},"additionalProperties":false,'
            b'"required":["d","usageDisclaimer","issuanceDisclaimer"]}]}},"additionalProperties":false,"required":['
            b'"i","ri","s","d"]}')

        schemer = scheming.Schemer(raw=raw)
        db.schema.pin(schemer.said, schemer)

        raw = (
            b'{"$id":"EDM9E_arYaIBSCJc1AK4alHW53_wWav9iEEcZ-ryQ373",'
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
            b'SAID","type":"string"},{"$id":"EDzok85gpP7EIa64ejXuDhz4euQgA_G5_tW0q7bt99tQ","description":"Edges '
            b'block","type":"object","properties":{"d":{"description":"Edges block SAID","type":"string"},'
            b'"qvi":{"description":"QVI node","type":"object","properties":{"n":{"description":"Issuer credential '
            b'SAID","type":"string"},"s":{"description":"SAID of required schema of the credential pointed to by this '
            b'node","type":"string","const":"EE4R4HtygsIDdW-XJiA3CJEs5Yrb2eK5YeohAy_rdyZB"}},'
            b'"additionalProperties":false,"required":["n","s"]}},"additionalProperties":false,"required":["d",'
            b'"qvi"]}]},"r":{"oneOf":[{"description":"Rules block SAID","type":"string"},'
            b'{"$id":"EEZoJ34aN10GtRMEqMW7ZHoa3KagEiO_fnirxQAsNs8j","description":"Rules block","type":"object",'
            b'"properties":{"d":{"description":"Rules block SAID","type":"string"},"usageDisclaimer":{'
            b'"description":"Usage Disclaimer","type":"object","properties":{"l":{"description":"Associated legal '
            b'language","type":"string","const":"Usage of a valid Legal Entity vLEI Credential does not assert that '
            b'the Legal Entity is trustworthy, honest, reputable in its business dealings, safe to do business with, '
            b'or compliant with any laws."}}},"issuanceDisclaimer":{"description":"Issuance Disclaimer",'
            b'"type":"object","properties":{"l":{"description":"Associated legal language","type":"string",'
            b'"const":"Issuance of a valid Legal Entity vLEI Credential only establishes that the information in the '
            b'requirements in the Identity Verification section 6.3 of the Credential Governance Framework were met '
            b'in accordance with the vLEI Ecosystem Governance Framework."}}}},"additionalProperties":false,'
            b'"required":["d","usageDisclaimer","issuanceDisclaimer"]}]}},"additionalProperties":false,"required":['
            b'"i","ri","s","d","e","r"]}')

        schemer = scheming.Schemer(raw=raw)
        db.schema.pin(schemer.said, schemer)

        raw = (
            b'{"$id":"ECVvJA-DJao9cVJc0jdOow1GpKhDRTNuBF73l5JR52kn",'
            b'"$schema":"http://json-schema.org/draft-07/schema#","title":"OOR Authorization vLEI Credential",'
            b'"description":"A vLEI Authorization Credential issued by a Legal Entity to a QVI for the authorization '
            b'of OOR credentials","type":"object","credentialType":"OORAuthorizationvLEICredential","properties":{'
            b'"v":{"description":"Version","type":"string"},"d":{"description":"Credential SAID","type":"string"},'
            b'"u":{"description":"One time use nonce","type":"string"},"i":{"description":"LE Issuer AID",'
            b'"type":"string"},"ri":{"description":"Credential status registry","type":"string"},'
            b'"s":{"description":"Schema SAID","type":"string"},"a":{"oneOf":[{"description":"Attributes block SAID",'
            b'"type":"string"},{"$id":"EA8VL0-UcLBl8DlxluWhgo2pIgcW1R8nxXK5MNWQBg7_","description":"Attributes '
            b'block","type":"object","properties":{"d":{"description":"Attributes block SAID","type":"string"},'
            b'"i":{"description":"QVI Issuee AID","type":"string"},"dt":{"description":"Issuance date time",'
            b'"format":"date-time","type":"string"},"AID":{"description":"AID of the intended recipient of the ECR '
            b'credential","type":"string"},"LEI":{"description":"LEI of the requesting Legal Entity","type":"string",'
            b'"format":"ISO 17442"},"personLegalName":{"description":"Requested recipient name as provided during '
            b'identity assurance","type":"string"},"officialRole":{"description":"Requested role description i.e. '
            b'Head of Standards","type":"string"}},"additionalProperties":false,"required":["i","dt","AID","LEI",'
            b'"personLegalName","officialRole"]}]},"e":{"oneOf":[{"description":"Edges block SAID","type":"string"},'
            b'{"$id":"EO4xYEvi-Z76prNXrBJYcXnpadzS9aEZbuvnWMi1Gd6R","description":"Edges block","type":"object",'
            b'"properties":{"d":{"description":"Edges block SAID","type":"string"},"le":{"description":"Chain to '
            b'legal entity vLEI credential","type":"object","properties":{"n":{"description":"QVI Issuer credential '
            b'SAID","type":"string"},"s":{"description":"SAID of required schema of the credential pointed to by this '
            b'node","type":"string","const":"EDM9E_arYaIBSCJc1AK4alHW53_wWav9iEEcZ-ryQ373"}},'
            b'"additionalProperties":false,"required":["n","s"]}},"additionalProperties":false,"required":["d",'
            b'"le"]}]},"r":{"oneOf":[{"description":"Rules block SAID","type":"string"},'
            b'{"$id":"EEZoJ34aN10GtRMEqMW7ZHoa3KagEiO_fnirxQAsNs8j","description":"Rules block","type":"object",'
            b'"properties":{"d":{"description":"Rules block SAID","type":"string"},"usageDisclaimer":{'
            b'"description":"Usage Disclaimer","type":"object","properties":{"l":{"description":"Associated legal '
            b'language","type":"string","const":"Usage of a valid Legal Entity vLEI Credential does not assert that '
            b'the Legal Entity is trustworthy, honest, reputable in its business dealings, safe to do business with, '
            b'or compliant with any laws."}}},"issuanceDisclaimer":{"description":"Issuance Disclaimer",'
            b'"type":"object","properties":{"l":{"description":"Associated legal language","type":"string",'
            b'"const":"Issuance of a valid Legal Entity vLEI Credential only establishes that the information in the '
            b'requirements in the Identity Verification section 6.3 of the Credential Governance Framework were met '
            b'in accordance with the vLEI Ecosystem Governance Framework."}}}},"additionalProperties":false,'
            b'"required":["d","usageDisclaimer","issuanceDisclaimer"]}]}},"additionalProperties":false,"required":['
            b'"i","ri","s","d","e","r"]}')

        schemer = scheming.Schemer(raw=raw)
        db.schema.pin(schemer.said, schemer)

        raw = (
            b'{"$id":"EG6cu7XSKRvz8TZCJ7RFa-g2tkrk5n_FW3eVa4R0rdKm",'
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
            b'{"$id":"EPwDqvdPQxVAPlaAfec8s1Eqq0BGEg2Yw_Ggn-rHj9Zd","description":"Edges block","type":"object",'
            b'"properties":{"d":{"description":"Edges block SAID","type":"string"},"auth":{"description":"Chain to '
            b'Auth vLEI credential from legal entity","type":"object","properties":{"n":{"description":"SAID of the '
            b'ACDC to which the edge connects","type":"string"},"s":{"description":"SAID of required schema of the '
            b'credential pointed to by this node","type":"string",'
            b'"const":"ECVvJA-DJao9cVJc0jdOow1GpKhDRTNuBF73l5JR52kn"},"o":{"description":"Operator indicating this '
            b'node is the issuer","type":"string","const":"I2I"}},"additionalProperties":false,"required":["n","s",'
            b'"o"]}},"additionalProperties":false,"required":["d","auth"]}]},"r":{"oneOf":[{"description":"Rules '
            b'block SAID","type":"string"},{"$id":"EEZoJ34aN10GtRMEqMW7ZHoa3KagEiO_fnirxQAsNs8j","description":"Rules '
            b'block","type":"object","properties":{"d":{"description":"Rules block SAID","type":"string"},'
            b'"usageDisclaimer":{"description":"Usage Disclaimer","type":"object","properties":{"l":{'
            b'"description":"Associated legal language","type":"string","const":"Usage of a valid Legal Entity vLEI '
            b'Credential does not assert that the Legal Entity is trustworthy, honest, reputable in its business '
            b'dealings, safe to do business with, or compliant with any laws."}}},"issuanceDisclaimer":{'
            b'"description":"Issuance Disclaimer","type":"object","properties":{"l":{"description":"Associated legal '
            b'language","type":"string","const":"Issuance of a valid Legal Entity vLEI Credential only establishes '
            b'that the information in the requirements in the Identity Verification section 6.3 of the Credential '
            b'Governance Framework were met in accordance with the vLEI Ecosystem Governance Framework."}}}},'
            b'"additionalProperties":false,"required":["d","usageDisclaimer","issuanceDisclaimer"]}]}},'
            b'"additionalProperties":false,"required":["i","ri","s","d","e","r"]}')

        schemer = scheming.Schemer(raw=raw)
        db.schema.pin(schemer.said, schemer)

