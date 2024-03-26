# SALLY
vLEI Audit Reporting Agent

The Sally vLEI Audit Reporting Agent receives presentations of credentials and notices of revocation, verifies the
structure and cryptographic integrity of the credential or revocation event and performs a POST to the configured 
webhook URL.  

All web hook POSTs will have the following header fields:

```json
{
   "Content-Type": "application/json",
   "Content-Length": <size of body>,
   "Sally-Resource": "EWCeT9zTxaZkaC_3-amV2JtG6oUxNA36sCC0P5MI7Buw",
   "Sally-Timestamp": "2022-06-24T14:19:19.591808+00:00"
}
```

With Sally resource being the SAID of one of the following credentials: 

| Schema | Type |
|-----|-------|
| EWCeT9zTxaZkaC_3-amV2JtG6oUxNA36sCC0P5MI7Buw | Qualified vLEI Issuer vLEI Credential |
| EWJkQCFvKuyxZi582yJPb0wcwuW3VXmFNuvbQuBpgmIs | Legal Entity vLEI Credential |
| E2RzmSCFmG2a5U2OqZF-yUobeSYkW-a3FsN82eZXMxY0 | Official Organization Role vLEI Credential |


The body of the POST to the web hook URL will be one of the following depending on event type (presentation or revocation)
 and credential involved.

### Presentation
The presentation API will be a POST to the configured web hook URL and will contain one of the following 3 payloads depending on the type of credential being presented.

**QVI Payload**
```json
{
 "action": "iss",
 "actor": "EPqeYsDPrYdb9HxJ0Yk9gH0VfspezBVLjxAzjfTGsgkY",
 "data": {
  "schema": "EWCeT9zTxaZkaC_3-amV2JtG6oUxNA36sCC0P5MI7Buw",
  "issuer": "EPqeYsDPrYdb9HxJ0Yk9gH0VfspezBVLjxAzjfTGsgkY",
  "issueTimestamp": "2022-06-24T14:19:19.591808+00:00",
  "credential": "EnR0SI1z7gwUYvnRUSwSLvP8O5oWZ_uzuFKSQGmanR9w",
  "recipient": "EGhyphY8VJwvliB0ZeX6-8kkyS9L_eGZE-TkPifM29HY",
  "LEI": "506700GE1G29325QX363"
 }
}
```

**Legal Entity Payload**
```json
{
   "action": "iss",
   "actor": "EGhyphY8VJwvliB0ZeX6-8kkyS9L_eGZE-TkPifM29HY",
   "data": { 
       "schema": "EWJkQCFvKuyxZi582yJPb0wcwuW3VXmFNuvbQuBpgmIs",
       "issuer": "EGhyphY8VJwvliB0ZeX6-8kkyS9L_eGZE-TkPifM29HY",
       "issueTimestamp": "2022-06-24T14:19:19.591808+00:00",
       "credential": "EHcRiSahoTAKNWZRLNN7MGtUfbMJgUldvPjpc3NCWxsQ",
       "recipient": "EkjlNRao4AZEmasi2jb9E3u4xnLD5Oe2qkHS_JWCIq-U",
       "qviCredential": "EnR0SI1z7gwUYvnRUSwSLvP8O5oWZ_uzuFKSQGmanR9w",
       "LEI": "506700GE1G29325QX363"
    }
}
```

**Official Organization Role Payload**
```json
{
   "action": "iss",
   "actor": "EGhyphY8VJwvliB0ZeX6-8kkyS9L_eGZE-TkPifM29HY",
   "data": { 
       "schema": "E2RzmSCFmG2a5U2OqZF-yUobeSYkW-a3FsN82eZXMxY0",
       "issuer": "EGhyphY8VJwvliB0ZeX6-8kkyS9L_eGZE-TkPifM29HY",
       "issueTimestamp": "2022-06-24T14:19:19.591808+00:00",
       "credential": "EecctjiS0dFyohgz0GBC6O9NlJJ7-pSJ3U5ZFEvzm48A",
       "recipient": "ECRi-yUy_bq2YrgTKI-VbG1MdvWsNstdyjvfx1ZEHJOY",
       "legalEntityCredential": "EHcRiSahoTAKNWZRLNN7MGtUfbMJgUldvPjpc3NCWxsQ"
       "qviCredential": "EnR0SI1z7gwUYvnRUSwSLvP8O5oWZ_uzuFKSQGmanR9w",
       "LEI": "506700GE1G29325QX363" ,
       "personLegalName": "Stephan Wolf",
       "officialRole": "Chief Executive Officer"
    }
}
```

**Presentation Payload Field Key**
The following table contains a description for every field in all the credential presentation payloads defined above:

| Field Label | Description |
|----|----|
| action | the action that triggered the web hook call.  Value will be "iss" for issue presentations |
| actor | The AID of the presenter of the credential |
| data | Attributes specific to the credential being presentedl |
| data -> schema | SAID of the schema of the credential that was presented |
| data -> issuer | Issuer of the credential presented |
| data -> issueTimestamp | Issuance timestamp for the credential |
| data -> credential | SAID of credential being presented |
| data -> recipient | AID of the holder of the credential |
| data -> qviCredential | SAID of a chained QVI credential (for LE and OOR credentials) |
| data -> legalEntityCredential | SAID of a chained legal entity credential (for OOR credentials) |
| data -> LEI | Legal Entity Identifier |
| data -> personLegalName | Person Legal Name data field of the OOR credential |
| data -> officialRole | Official Role Name data field of the OOR credential |


### Revocation
All revocation web hook requests will have the same format as follows:

**Revocation Payload**
```json
{
   "action": "rev",
   "actor": "EGhyphY8VJwvliB0ZeX6-8kkyS9L_eGZE-TkPifM29HY",
   "data": { 
       "schema": "EWCeT9zTxaZkaC_3-amV2JtG6oUxNA36sCC0P5MI7Buw",
       "credential": "EZBfSGG5k1CZYk1QH3GXFPtEwLHf0H06zuDUEJRyar1E",
       "revocationTimestamp": "2022-06-24T14:19:19.591808+00:00"
    }
}
```

**Revocation Payload Field Key**
The following table contains a description for every field in all the credential revocation payloads defined above:

| Field Label | Description |
|----|----|
| action | the action that triggered the web hook call.  Value will be "rev" for revocation presentations |
| actor | The AID of the presenter of the revocation |
| data | Attributes specific to the credential being presentedl |
| data -> schema | SAID of the schema of the credential that was revoked |
| data -> revocationTimestamp | Revocation timestamp for the credential |
| data -> credential | SAID of credential being revoked |


## Running

To properly test the Sally server, one needs to check out the `main` branch of `http://github.com/WebOfTrust/vLEI`, 
the `development` branch of `http://github.com/WebOfTrust/keripy` and the dev branch of this repo.  All repositories 
require python `3.10.4` to run as well as a local installation of `libsodium`.  We recommend using a virtual environment
technology(`pipenv` for example) for each repository.  Finally, many of the bash commands and shell scripts require an
installation of `jq` running locally.


### vLEI

The vLEI server provides endpoints for Data OOBIs for the credential schema for the vLEI ecosystem.  To run the server,
you must run:

```bash
pip install -r requirements.txt
vLEI-server -s schema/acdc -c samples/acdc -o samples/oobis
```

And leave the server running to is is accessible to Sally and the agents running from KERIpy.

### KERIpy

From KERIpy you will run 1 server that provide witnesses.  In addition you will run a shell script which uses `kli` to
execute KERI commands to create identifiers and issue credentials.

First, to install all required dependencies run:

```bash
pip install -r requirements.txt
```

Then in one terminal to start the witness servers run and leave running:

```bash
kli witness demo
```


Now that the servers are running, you will use the shell script `scripts/demo/vLEI/issue-xbrl-attestation.sh` to
create several sample vLEI participants including GLEIF External, a Qualified vLEI Issuer, a Legal Entity and a person 
representing the Legal Entity in an Official Role and issue them vLEI credentals.  Simply execute the script and wait 
for it to complete creating all identifiers and issuing all credentuals.

```bash
KERI_SCRIPT_DIR=./scripts KERI_DEMO_SCRIPT_DIR=./scripts/demo ./scripts/demo/vLEI/issue-xbrl-attestation.sh
```

### Sally

Now that you have a sample vLEI ecosystem running you will need to configure and run the Sally server.  In order to start
Sally you will need to create an AID that uses our local witnesses for Sally to use.  The following two commands need to 
be run from a virtual environment that has `keripy` configured to run so the `kli` command is available.  (We usually 
accomplish this by running `pip install -e .` from inside the keripy directory with the virtual environment configured
for `Sally`).  You will need to adjust the paths in the script to point to the correct location of `keripy`.

```bash
export KERIPY=../keripy
kli init --name sally --nopasscode --config-dir ${KERIPY}/scripts --config-file demo-witness-oobis-schema --salt 0ACDXyMzq1Nxc4OWxtbm9fle
kli incept --name sally --alias sally --file ${KERIPY}/scripts/demo/data/trans-wits-sample.json
kli oobi resolve --name sally --oobi-alias qvi --oobi http://127.0.0.1:5642/oobi/EHMnCf8_nIemuPx-cUHaDQq8zSnQIFAurdEpwHpNbnvX/witness/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha
```

Finally, you can start (and leave running) the Sally server with:

```bash
sally server start --name sally --alias sally --web-hook http://127.0.0.1:9923 --auth EHOuGiHMxJShXHgSb6k_9pqxmRb8H-LT0R2hQouHp8pW
```

If you require a sample web hook to receive the notifications from the Sally server one is provided in this repo.  You
can run the sample hook server in a seperate terminal with the following command (the above Sally command assumes this 
server and port). 

```bash
sally hook demo
```

Once all servers are running, the final step before you can present credentials is to connect the servers together using 
OOBI resolution and then you will be able to present the credentials from the vLEI agents to the Sally server.  To
connect the vLEI issuer to the Sally server, run the following curl command:

```bash
kli oobi resolve --name qvi --oobi-alias sally --oobi http://127.0.0.1:9723/oobi
```

### Presenting Credentials
To present the Legal Entity credential created above, you need to use the `kli` to retrieve the SAID of that credential
from the Agent of the Legal Entity and then use the `kli` to tell that agent to present the credential to Sally
server.  The following two commands will perform those steps and can be repeated multiple times to test Sally 
integration:

```bash
LE_SAID=`kli vc list --name legal-entity --alias legal-entity --said`
kli ipex grant --name qvi --alias qvi --said ${LE_SAID} --recipient sally
```

### Revoking Credentials
To revoke a credential from the command line, use the `kli vc revoke` command as follows.  Note the use of the `---send` 
command line option to specify additional parties (AIDs or aliasa) to send the revocation events to:

```bash
LE_SAID=`kli vc list --name legal-entity --alias legal-entity --said`
kli vc revoke --name qvi --alias qvi --registry-name vLEI-qvi --said "$LE_SAID" --send sally
```

The SAID value (after the --said option) is the SAID of the credential to revoke.  Specifying the `sally` alias will result
in the revocation events being sent to Sally which will process them and report to the web hook the revocation.
