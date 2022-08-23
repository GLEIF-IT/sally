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
            b'{"$id":"EWCeT9zTxaZkaC_3-amV2JtG6oUxNA36sCC0P5MI7Buw",'
            b'"$schema":"http://json-schema.org/draft-07/schema#","title":"Qualified vLEI Issuer Credential",'
            b'"description":"A vLEI Credential issued by GLEIF to Qualified vLEI Issuers which allows the Qualified '
            b'vLEI Issuers to issue, verify and revoke Legal Entity vLEI Credentials and Legal Entity Official '
            b'Organizational Role vLEI Credentials","credentialType":"QualifiedvLEIIssuervLEICredential",'
            b'"properties":{"v":{"type":"string"},"d":{"type":"string"},"i":{"type":"string"},'
            b'"ri":{"description":"credential status registry","type":"string"},"s":{"description":"schema SAID",'
            b'"type":"string"},"a":{"description":"data block","properties":{"d":{"type":"string"},'
            b'"i":{"type":"string"},"dt":{"description":"issuance date time","format":"date-time","type":"string"},'
            b'"LEI":{"type":"string"},"gracePeriod":{"default":90,"type":"integer"}},"additionalProperties":false,'
            b'"required":["i","dt","LEI"],"type":"object"},"e":{"type":"object"}},"additionalProperties":false,'
            b'"required":["i","ri","s","d"],"type":"object"}')

        schemer = scheming.Schemer(raw=raw)
        db.schema.pin(schemer.said, schemer)

        raw = (
            b'{"$id":"EWJkQCFvKuyxZi582yJPb0wcwuW3VXmFNuvbQuBpgmIs",'
            b'"$schema":"http://json-schema.org/draft-07/schema#",'
            b'"title":"Legal Entity vLEI Credential","description":"A vLEI Credential issued by a Qualified vLEI '
            b'issuer '
            b'to a Legal Entity","credentialType":"LegalEntityvLEICredential","properties":{"v":{"type":"string"},'
            b'"d":{"type":"string"},"i":{"type":"string"},"ri":{"description":"credential status registry",'
            b'"type":"string"},"s":{"description":"schema SAID","type":"string"},"a":{"description":"data block",'
            b'"properties":{"d":{"type":"string"},"i":{"type":"string"},"dt":{"description":"issuance date time",'
            b'"format":"date-time","type":"string"},"LEI":{"type":"string"}},"additionalProperties":false,"required":['
            b'"i","dt","LEI"],"type":"object"},"e":{"description":"edges block","properties":{"d":{'
            b'"description":"SAID of '
            b'edges block","type":"string"},"qvi":{"description":"node SAID of issuer credential","properties":{"n":{'
            b'"type":"string"},"s":{"type":"string","description":"SAID of required schema of the credential pointed '
            b'to '
            b'by this node","const":"EWCeT9zTxaZkaC_3-amV2JtG6oUxNA36sCC0P5MI7Buw"}},"additionalProperties":false,'
            b'"required":["n","s"],"type":"object"}},"additionalProperties":false,"required":["d","qvi"],'
            b'"type":"object"},"r":{"type":"object","properties":{"d":{"type":"string","description":"SAID of rules '
            b'block"},"usageDisclaimer":{"type":"string","description":"Usage Disclaimer"},"issuanceDisclaimer":{'
            b'"type":"string","description":"Issuance Disclaimer"}},"additionalProperties":false,"required":["d",'
            b'"usageDisclaimer","issuanceDisclaimer"],"description":"rules block"}},"additionalProperties":false,'
            b'"required":["i","ri","s","d","e","r"],"type":"object"}')

        schemer = scheming.Schemer(raw=raw)
        db.schema.pin(schemer.said, schemer)

        raw = (
            b'{"$id":"E2RzmSCFmG2a5U2OqZF-yUobeSYkW-a3FsN82eZXMxY0",'
            b'"$schema":"http://json-schema.org/draft-07/schema#",'
            b'"title":"Legal Entity Official Organizational Role vLEI Credential","description":"A vLEI Role '
            b'Credential '
            b'issued by a Qualified vLEI issuer to official representatives of a Legal Entity",'
            b'"credentialType":"LegalEntityOfficialOrganizationalRolevLEICredential","properties":{"v":{'
            b'"type":"string"},'
            b'"d":{"type":"string"},"i":{"type":"string"},"ri":{"description":"credential status registry",'
            b'"type":"string"},"s":{"description":"schema SAID","type":"string"},"a":{"description":"data block",'
            b'"properties":{"d":{"type":"string"},"i":{"type":"string"},"dt":{"description":"issuance date time",'
            b'"format":"date-time","type":"string"},"LEI":{"type":"string"},"personLegalName":{"type":"string"},'
            b'"officialRole":{"type":"string"}},"additionalProperties":false,"required":["i","dt","LEI",'
            b'"personLegalName","officialRole"],"type":"object"},"e":{"description":"edges block","properties":{"d":{'
            b'"description":"said of edges block","type":"string"},"o":{"type":"string","description":"operator '
            b'indicating this node is not the issuer","enum":["AND","OR"]},"le":{"description":"chain to legal entity '
            b'vLEI credential","properties":{"n":{"type":"string"},"s":{"type":"string","description":"SAID of '
            b'required '
            b'schema of the credential pointed to by this node",'
            b'"const":"EWJkQCFvKuyxZi582yJPb0wcwuW3VXmFNuvbQuBpgmIs"},'
            b'"o":{"type":"string","description":"operator indicating this node is not the issuer","const":"NI2I"}},'
            b'"additionalProperties":false,"required":["n","s","o"],"type":"object"},"qvi":{"description":"chain to '
            b'legal '
            b'entity vLEI credential","properties":{"n":{"type":"string"},"s":{"type":"string","description":"SAID of '
            b'required schema of the credential pointed to by this node",'
            b'"const":"EWCeT9zTxaZkaC_3-amV2JtG6oUxNA36sCC0P5MI7Buw"},"o":{"type":"string","description":"operator '
            b'indicating this node is not the issuer","const":"I2I"}},"additionalProperties":false,"required":["n","s",'
            b'"o"],"type":"object"}},"additionalProperties":false,"required":["d","le","qvi"],"type":"object"},'
            b'"r":{"type":"object","properties":{"d":{"type":"string","description":"SAID of rules block"},'
            b'"usageDisclaimer":{"type":"string","description":"Usage Disclaimer"},"issuanceDisclaimer":{'
            b'"type":"string",'
            b'"description":"Issuance Disclaimer"}},"additionalProperties":false,"required":["d","usageDisclaimer",'
            b'"issuanceDisclaimer"],"description":"rules block"}},"additionalProperties":false,"required":["i","ri",'
            b'"s",'
            b'"d","e","r"],"type":"object"}')

        schemer = scheming.Schemer(raw=raw)
        db.schema.pin(schemer.said, schemer)
