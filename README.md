# SALLY
vLEI Audit Reporting Agent

The Sally vLEI Audit Reporting Agent receives presentations of credentials and notices of revocation, verifies the
structure and cryptographic integrity of the credential or revocation event and performs a POST to the configured 
webhook URL.  

# Usage

The below `sally server start` command shows how to use Sally.

```bash
sally server start \
  --name sally --alias sally \
  --salt 0AD45YWdzWSwNREuAoitH_CC \
  --passcode VVmRdBTe5YCyLMmYRqTAi \
  --web-hook http://127.0.0.1:9923 \
  --auth EMHY2SRWuqcqlKv2tNQ9nBXyZYqhJ-qrDX70faMcGujF
  --config-dir scripts \
  --config-file sally-habery.json \
  --incept-file sally-incept.json \
  --loglevel INFO
```

You must specify both the keystore (Habery) configuration file and the identifier (Hab) inception file. The `--config-dir` argument applies to both the
keystore and identifier files. For the keystore configuration the directory `keri/cf` is appended to the value of `--config-file` if it is not an absolute path.

You can specify the `--salt` and `--passcode` arguments to set the salt and passcode for the identifier. If you do not specify these arguments, 
Sally will use a random one by default.

# Sample Web Hook Call

All web hook POST HTTP calls will have the following HTTP header fields:

```text
   Content-Type: application/json
 Content-Length: <size of body>
 Sally-Resource: EWCeT9zTxaZkaC_3-amV2JtG6oUxNA36sCC0P5MI7Buw,
Sally-Timestamp: 2022-06-24T14:19:19.591808+00:00
```

With Sally resource being the SAID of one of the following credentials: 

| Schema                                       | Type                                       |
|----------------------------------------------|--------------------------------------------|
| EWCeT9zTxaZkaC_3-amV2JtG6oUxNA36sCC0P5MI7Buw | Qualified vLEI Issuer vLEI Credential      |
| EWJkQCFvKuyxZi582yJPb0wcwuW3VXmFNuvbQuBpgmIs | Legal Entity vLEI Credential               |
| E2RzmSCFmG2a5U2OqZF-yUobeSYkW-a3FsN82eZXMxY0 | Official Organization Role vLEI Credential |

The body of the POST to the web hook URL will be one of the following depending on event type (presentation or revocation)
 and credential involved.

## Web Hook body credential presentation types
The presentation API will be a POST to the configured web hook URL and will contain one of the following 3 payloads depending on the type of credential being presented.

**QVI Payload**
```json
{
 "action": "iss",
 "actor": "EPqeYsDPrYdb9HxJ0Yk9gH0VfspezBVLjxAzjfTGsgkY",
 "data": {
  "type": "QVI",
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
       "type": "LE",
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
       "type": "OOR",
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

| Field Label                   | Description                                                                               |
|-------------------------------|-------------------------------------------------------------------------------------------|
| action                        | the action that triggered the web hook call.  Value will be "iss" for issue presentations |
| actor                         | The AID of the presenter of the credential                                                |
| data                          | Attributes specific to the credential being presentedl                                    |
| data -> schema                | SAID of the schema of the credential that was presented                                   |
| data -> issuer                | Issuer of the credential presented                                                        |
| data -> issueTimestamp        | Issuance timestamp for the credential                                                     |
| data -> credential            | SAID of credential being presented                                                        |
| data -> recipient             | AID of the holder of the credential                                                       |
| data -> qviCredential         | SAID of a chained QVI credential (for LE and OOR credentials)                             |
| data -> legalEntityCredential | SAID of a chained legal entity credential (for OOR credentials)                           |
| data -> LEI                   | Legal Entity Identifier                                                                   |
| data -> personLegalName       | Person Legal Name data field of the OOR credential                                        |
| data -> officialRole          | Official Role Name data field of the OOR credential                                       |


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

| Field Label                 | Description                                                                                    |
|-----------------------------|------------------------------------------------------------------------------------------------|
| action                      | the action that triggered the web hook call.  Value will be "rev" for revocation presentations |
| actor                       | The AID of the presenter of the revocation                                                     |
| data                        | Attributes specific to the credential being presentedl                                         |
| data -> schema              | SAID of the schema of the credential that was revoked                                          |
| data -> revocationTimestamp | Revocation timestamp for the credential                                                        |
| data -> credential          | SAID of credential being revoked                                                               |


# Running

To properly test the Sally server, one needs to check out the `main` branch of `http://github.com/WebOfTrust/vLEI`, 
the `development` branch of `http://github.com/WebOfTrust/keripy` and the dev branch of this repo.  All repositories 
require python `3.10.4` to run as well as a local installation of `libsodium`.  We recommend using a virtual environment
technology(`pipenv` for example) for each repository.  Finally, many of the bash commands and shell scripts require an
installation of `jq` running locally.


## vLEI

The vLEI server provides endpoints for Data OOBIs for the credential schema for the vLEI ecosystem.  To run the server,
you must run:

```bash
pip install -r requirements.txt
vLEI-server -s schema/acdc -c samples/acdc -o samples/oobis
```

And leave the server running to is accessible to Sally and the agents running from KERIpy.

## KERIpy

From KERIpy you will run 1 server that provide witnesses. In addition, you will run a shell script which uses `kli` to
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

## Sally

Now that you have a sample vLEI ecosystem running you will need to configure and run the Sally server.  

In order to start Sally you will need to either:
1. Use the `--incept-file` and `--salt` arguments to instruct the `sally server start` command to create a new identifier, or
2. Use the `kli init` and `kli incept` commands to create an AID for Sally to use.

Both options require the following configuration files:

### Configuration Files

#### keystore (Habery) configuration file

This configuration is keystore-wide, meaning available to all identifiers used in this keystore. We will only have one identifier in this
keystore, the Sally identifier. Configuring this keystore (Habery) requires a configuration file set up similar to the following example. 
The "iurls" section corresponds to "introduction URLs" and should contain the out-of-band identifier (OOBI) URLs for the witnesses that will be used.
The "durls" section should contain "data URLs" or OOBI URLs for the vLEI ACDC credential schema files.

This file must be located at the path specified by the combination of the `--config-dir` and `--config-file` arguments along with the
path segment of "keri/cf" for an end result of "config dir" / keri / cf / "config file" unless an absolute path is specified for the `--config-file` argument
in which case the absolute path to the file is used and the `--config-dir` argument is disregarded..

```json
{
  "dt": "2022-10-31T12:59:57.823350+00:00",
  "iurls": [
    "http://127.0.0.1:5642/oobi/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha/controller",
    "http://127.0.0.1:5644/oobi/BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX/controller",
    "http://127.0.0.1:5643/oobi/BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM/controller"
  ],
  "durls": [
    "http://127.0.0.1:7723/oobi/EBNaNu-M9P5cgrnfl2Fvymy4E_jvxxyjb70PRtiANlJy",
    "http://127.0.0.1:7723/oobi/EH6ekLjSr8V32WyFbGe1zXjTzFs9PkTYmupJ9H65O14g",
    "http://127.0.0.1:7723/oobi/EKA57bKBKxr_kN7iN5i7lMUxpMG-s19dRcmov1iDxz-E",
    "http://127.0.0.1:7723/oobi/ENPXp1vQzRF6JwIuS-mp2U8Uf1MoADoP_GqQ62VsDZWY",
    "http://127.0.0.1:7723/oobi/EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao",
    "http://127.0.0.1:7723/oobi/EEy9PkikFcANV1l7EHukCeXqrzT1hNZjGlUk7wuMO5jw"
  ]
}
```

#### Identifier (Hab) Inception File

Creating an identifier requires a configuration file set up similar to the following example. This file must be located at the path specified by
the combination of the `--config-dir` and `--config-file` arguments for an end result of "config dir" / "config file" unless an absolute path is
specified for the `--config-file` argument in which case the absolute path to the file is used and the `--config-dir` argument is disregarded.

```json
{
  "transferable": true,
  "wits": [
    "BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha"
  ],
  "toad": 1,
  "icount": 1,
  "ncount": 1,
  "isith": "1",
  "nsith": "1"
}

```

### Option 1 - `sally server start` command

The following command will start the Sally server with a new identifier and salt:

```bash
sally server start \
  --name sally --alias sally \
  --salt 0AD45YWdzWSwNREuAoitH_CC \
  --passcode VVmRdBTe5YCyLMmYRqTAi \
  --web-hook http://127.0.0.1:9923 \
  --auth EMHY2SRWuqcqlKv2tNQ9nBXyZYqhJ-qrDX70faMcGujF
  --config-dir scripts \
  --config-file sally-habery.json \
  --incept-file sally-incept.json \
  --loglevel INFO
```

### Option 2 - `kli` commands
 
Creating an identifier with the `kli init` and `kli incept` commands requires the following two commands to be run from an activated 
Python virtual environment that has `keripy` configured to run so that the `kli` command is available. 

We usually accomplish this by running `pip install -e .` from inside the keripy directory with the virtual environment configured
for `Sally` though you can also run this command from a Python virtual environment created from this repository, the "sally" repository.

You will need to adjust the paths in the commands below to point to the correct location of `keripy` or `sally` depending on what you use.

```bash
kli init --name sally --passcode VVmRdBTe5YCyLMmYRqTAi --salt 0AD45YWdzWSwNREuAoitH_CC \
  --config-dir scripts --config-file sally-habery.json
kli incept --name sally --passcode VVmRdBTe5YCyLMmYRqTAi --alias sally \
  --file /scripts/sally-incept.json
kli oobi resolve --name sally --passcode VVmRdBTe5YCyLMmYRqTAi \
  --oobi-alias qvi --oobi http://127.0.0.1:5642/oobi/EHLWiN8Q617zXqb4Se4KfEGteHbn_way2VG5mcHYh5bm/witness/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha
```

Finally, you can start (and leave running) the Sally server with:

```bash
sally server start --name sally --alias sally --passcode VVmRdBTe5YCyLMmYRqTAi \
  --web-hook http://127.0.0.1:9923 \
  --auth EHOuGiHMxJShXHgSb6k_9pqxmRb8H-LT0R2hQouHp8pW
```

If you require a sample web hook to receive the notifications from the Sally server one is provided in this repo.  You
can run the sample hook server in a separate terminal with the following command. The above Sally command assumes this 
server and port by default. 

## Sample Web Hook
```bash
sally hook demo
```

Once all servers are running, the final step before you can present credentials is to connect the servers together using 
OOBI resolution, and then you will be able to present the credentials from the vLEI agents to the Sally server.  

To connect the vLEI issuer to the Sally server, run the following curl command:

```bash
kli oobi resolve --name qvi --oobi-alias sally --oobi http://127.0.0.1:9723/oobi
```

# Presenting Credentials
To present the Legal Entity credential created above, you need to use the `kli` to retrieve the SAID of that credential
from the Agent of the Legal Entity and then use the `kli` to tell that agent to present the credential to Sally
server.  The following two commands will perform those steps and can be repeated multiple times to test Sally 
integration:

```bash
LE_SAID=`kli vc list --name legal-entity --alias legal-entity --said`
kli ipex grant --name qvi --alias qvi --said ${LE_SAID} --recipient sally
```

# Revoking Credentials
To revoke a credential from the command line, use the `kli vc revoke` command as follows.  Note the use of the `---send` 
command line option to specify additional parties (AIDs or aliasa) to send the revocation events to:

```bash
LE_SAID=`kli vc list --name legal-entity --alias legal-entity --said`
kli vc revoke --name qvi --alias qvi --registry-name vLEI-qvi --said "$LE_SAID" --send sally
```

The SAID value (after the --said option) is the SAID of the credential to revoke.  Specifying the `sally` alias will result
in the revocation events being sent to Sally which will process them and report to the web hook the revocation.
