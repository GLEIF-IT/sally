# SALLY
vLEI Audit Reporting Agent

## Example Usage

### Example invocation

```bash
sally server start \
  --name sally \
  --alias sally \
  --salt 0AD3GmJxuDbCs90qC0ipHfOD \
  --passcode bWuSoMabM6CSSJUqc97YS \
  --web-hook http://127.0.0.1:9923 \
  --auth EHOuGiHMxJShXHgSb6k_9pqxmRb8H-LT0R2hQouHp8pW \
  --config-file sally.json \
  --config-dir scripts \
  --loglevel INFO
```

### Configuration Options

You must specify the below required configuration file in order to have the SallyAgent listen to the specified port and accept presentation requests.

The environment variables are optional.

#### Required configuration file

You must have an attribute of your configuration file named either the same name that you pass to the `--alias` arg or that is the value of your 
AID. Below the configuration file uses the `"sally"` property to specify the controller URLs ("curls") section. This is what allows 
the Sally server to bind to the specified port so it can listen to presentation requests.

```json
{
  "dt": "2022-10-31T12:59:57.823350+00:00",
  "sally": {
    "dt": "2022-01-20T12:57:59.823350+00:00",
    "curls": ["http://127.0.0.1:9723/"]
  },
  "iurls": [],
  "durls": []
}
```

#### Environment Variables

- `SALLY_LOG_LEVEL` may be used to set the log level for the server. Defaults to `"INFO"`.


### Command Options

See command options with `sally server start --help`. A summary of the options is below:

- `-p` | `--http` - The HTTP port to bind the Sally server to.
- `-n` | `--name` - The name of the Sally server.
- `-b` | `--base` - Optional prefix to the file location for the KERI keystore.
- `-c` | `--config-dir` - Directory override for configuration data
- `-f` | `--config-file` - Configuration filename override
- `-a` | `--alias` - The alias of the Sally server.
- `-s` | `--salt` - Qualified base64 salt for creating key pairs
-      | `--passcode` - 21 character encryption passcode for keystore
- `-w` | `--web-hook` - The URL to POST to when a credential is presented or revoked.
-      | `--auth` - The authorized AID that must be the issuer of the QVI credential at the root of the credential chain.
- `-e` | `--escrow-timeout` - Timeout in minutes for escrowed events that have not yet been delivered to the webhook. Defaults to 10 minutes.
- `-r` | `--retry-delay` - Retry delay in seconds for failed webhook attempts.
- `-l` | `--loglevel` - The log level for the server. Defaults to INFO. Can be set with `SALLY_LOG_LEVEL`

## Overview

The Sally vLEI Audit Reporting Agent receives presentations of credentials and notices of revocation, verifies the
structure and cryptographic integrity of the credential or revocation event and performs a POST to the configured 
webhook URL.  

All web hook POSTs will have the following header fields:

```json
{
   "Content-Type": "application/json",
   "Content-Length": "<size of body>",
   "Sally-Resource": "EWCeT9zTxaZkaC_3-amV2JtG6oUxNA36sCC0P5MI7Buw",
   "Sally-Timestamp": "2022-06-24T14:19:19.591808+00:00"
}
```

With Sally resource being the SAID of one of the following credentials: 

| Schema                                       | Type                                       |
|----------------------------------------------|--------------------------------------------|
| EWCeT9zTxaZkaC_3-amV2JtG6oUxNA36sCC0P5MI7Buw | Qualified vLEI Issuer vLEI Credential      |
| EWJkQCFvKuyxZi582yJPb0wcwuW3VXmFNuvbQuBpgmIs | Legal Entity vLEI Credential               |
| E2RzmSCFmG2a5U2OqZF-yUobeSYkW-a3FsN82eZXMxY0 | Official Organization Role vLEI Credential |


The body of the POST to the web hook URL will be one of the following depending on event type (presentation or revocation)
 and credential involved.

### Presentation

Sally, upon receiving a credential presentation through the Issuance and Presentation Exchange (IPEX) protocol, will make a POST HTTP request to the configured web hook URL with one of the following 3 payloads depending on the type of presented credential.

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
       "legalEntityCredential": "EHcRiSahoTAKNWZRLNN7MGtUfbMJgUldvPjpc3NCWxsQ",
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


## Running - Dependencies

To properly test the Sally server, one needs to check out the `main` branch of the following two repositories:
- `http://github.com/WebOfTrust/vLEI` - this repository 
- `http://github.com/WebOfTrust/keripy` - for the demonstration witnesses.

All repositories 
require python `3.12.2`+ to run as well as a local installation of `libsodium`.  We recommend using a virtual environment
technology(`pipenv` for example) for each repository. 

Finally, many of the bash commands and shell scripts require an installation of `jq` running locally.

## Running - Components Overview

You will run the following components to test the Sally server:
- `vLEI-server` - provides endpoints for retrieving Data OOBIs for the credential schema for the vLEI ecosystem.
- `witnesses` - provides witnesses for KERIpy keystores to use.
- `kli` - used to create KERI keystores 
  - You will use the `kli` command line tool to create identifiers and issue and present credentials. 

### vLEI-server

The `vLEI-server` provides endpoints for retrieving Data OOBIs for the credential schema for the vLEI ecosystem.  

To run the server, in a separate terminal change directories to the `WebOfTrust/vLEI` repository and then run:

```bash
pip install -r requirements.txt
vLEI-server -s schema/acdc -c samples/acdc -o samples/oobis
```

And leave the server running so it is accessible to Sally and the keystores running from KERIpy.

### Witnesses

From KERIpy you will run one server that provide witnesses.  In addition, you will run a shell script which uses `kli` to
execute KERI commands to create identifiers and issue credentials.

First, to install all required dependencies run:

```bash
pip install -r requirements.txt
```

Then in a separate terminal to start the witness servers run and leave running:

```bash
kli witness demo
```

### kli keystores

Now that the vLEI-server and witnesses are running, you will use the shell script in the KERIpy repository 
located at `scripts/demo/vLEI/issue-xbrl-attestation.sh` to create several sample vLEI participants 
including GLEIF External, a Qualified vLEI Issuer, a Legal Entity and a person representing the 
Legal Entity in an Official Role and issue them vLEI credentials.  Simply execute the script and wait 
for it to complete creating all identifiers and issuing all credentials.

```bash
# from the root of the KERIpy repository, after both vLEI-server and witnesses are running
KERI_SCRIPT_DIR=./scripts KERI_DEMO_SCRIPT_DIR=./scripts/demo ./scripts/demo/vLEI/issue-xbrl-attestation.sh
```

### Sally

Now that you have a sample vLEI ecosystem running you will need to configure and run the Sally server. 
To start the Sally server then you use a start command like the one at the top of this README.
This command will create the Sally KERIpy keystore based on the salt and provided passcode. The 
configuration file you send in will be used to configure the Sally server to listen on the specified port
and to resolve any included OOBIs in the `iurls` or `durls` sections of the configuration file.

An important concept here is the `--auth` option.  This option specifies the AID of the authorized issuer of the
QVI credentials that must be at the root of the credential chain for any presented credentials.
This is a security feature to ensure that only authorized issuers can present credentials to the Sally server.

In a separate terminal run the following command to start the Sally server, with your own 
salt, passcode, configuration file, auth AID, and web hook URL:

```bash
sally server start \
  --name sally \
  --alias sally \
  --salt 0AD3GmJxuDbCs90qC0ipHfOD \
  --passcode bWuSoMabM6CSSJUqc97YS \
  --web-hook http://127.0.0.1:9923 \
  --auth EHOuGiHMxJShXHgSb6k_9pqxmRb8H-LT0R2hQouHp8pW \
  --config-file sally.json \
  --config-dir scripts \
  --loglevel INFO
```

If you require a sample web hook to receive the notifications from the Sally server one is provided in this repo.  You
can run the sample hook server in a separate terminal with the following command (the above Sally command assumes this 
server and port). 

```bash
sally hook demo
```

Once all servers are running, the final step before you can present credentials is to connect the servers together using 
OOBI resolution, and then you will be able to present the credentials from the vLEI agents to the Sally server.  To
connect the vLEI issuer, the QVI, set up in the `issue-xbrl-attestation.sh `script above to the Sally server, 
run the following curl command:

```bash
kli oobi resolve --name qvi --oobi-alias sally --oobi http://127.0.0.1:9723/oobi
```

This uses what is called a "blind OOBI" to connect the QVI to the Sally server. This is because there
is no AID nor controller role specified in the OOBI URL. The OOBI resolver assumes that the response from
the blind OOBI URL will have a `/loc/scheme` and `/end/role/add` specified of the kind of OOBI that will be
resolved which in this case will be a `controller` OOBI that corresponds to the Sally AID that was set
up when the Sally server was started.

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
kli vc revoke --name qvi --alias qvi --registry-name vLEI-qvi --said "$LE_SAID"
kli ipex grant --name qvi --alias qvi --said ${LE_SAID} --recipient sally
```

The SAID value (after the --said option) is the SAID of the credential to revoke. The `IPEX Grant` 
following the revocation will present the current state of the credential to the Sally server which
is how the Sally server learns of the revocation and reports it to the web hook as a revocation.
