# SALLY | Abydos Gatekeeper

The vLEI Audit Reporting Agent repurposed as the Abydos Gatekeeper Agent.

The Sally Abydos Gatekeeper Agent receives presentations of credentials and notices of revocation, verifies the
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

With the value of the Sally-Resource header being the SAID of one of the following credential schema types: 

| Schema                                        | Type                   |
|-----------------------------------------------|------------------------|
| EIxAox3KEhiQ_yCwXWeriQ3ruPWbgK94NDDkHAZCuP9l  | TreasureHuntingJourney |
| ELc8tMg_hhsAPfVbjUBBC-giEy5440oSb9EzFBZdAxHD  | JourneyMarkRequest     |
| EBEefH4LNQswHSrXanb-3GbjCZK7I_UCL6BdD-zwJ4my  | JourneyMark            | 
| EEq0AkHV-i5-aCc1JMBGsd7G85HlBzI3BfyuS5lHOGjr  | JourneyCharter         |


The body of the POST to the web hook URL will be one of the following depending on event type (presentation or revocation)
 and credential involved.

### Presentation
The presentation API will be a POST to the configured web hook URL and will contain one of the following 4 payload\
shapes depending on the type of credential being presented.

**Treasure Hunting Journey Payload**
```json
{
  "action": "iss",
  "actor": "EIaJ5gpHSL9nl1XIWDkfMth1uxbD-AfLkqdiZL6S7HkZ",
  "data": {
    "schema": "EIxAox3KEhiQ_yCwXWeriQ3ruPWbgK94NDDkHAZCuP9l",
    "issuer": "EIaJ5gpHSL9nl1XIWDkfMth1uxbD-AfLkqdiZL6S7HkZ",
    "issueTimestamp": "2023-03-16T00:22:51.571027+00:00",
    "credential": "EJQMx6eOAMGQ01w37bsJNDvo6rHhMysmidwJxD9ti1bu",
    "recipient": "EJS0-vv_OPAQCdJLmkd5dT0EW-mOfhn_Cje4yzRjTv8q",
    "destination": "Osireion",
    "treasureSplit": "50/50",
    "partyThreshold": 2,
    "journeyEndorser": "Ramiel"
  }
}
```

**Journey Mark Request**
```json
{
  "action": "iss",
  "actor": "EJS0-vv_OPAQCdJLmkd5dT0EW-mOfhn_Cje4yzRjTv8q",
  "data": {
    "schema": "ELc8tMg_hhsAPfVbjUBBC-giEy5440oSb9EzFBZdAxHD",
    "issuer": "EJS0-vv_OPAQCdJLmkd5dT0EW-mOfhn_Cje4yzRjTv8q",
    "issueTimestamp": "2023-03-16T00:22:51.571027+00:00",
    "credential": "EC2KirxTYEnw6IJFJAVXSeynOjZRFBpcDL-oqIVgQnP6",
    "recipient": "EIaJ5gpHSL9nl1XIWDkfMth1uxbD-AfLkqdiZL6S7HkZ",
    "requester": {
      "firstName": "",
      "lastName": "",
      "nickname": ""
    },
    "desiredPartySize": 2,
    "desiredSplit": 50.00,
    "journeyCredential": "EJQMx6eOAMGQ01w37bsJNDvo6rHhMysmidwJxD9ti1bu"
  }
}
```

**Journey Mark**
```json
{
  "action": "iss",
  "actor": "EIaJ5gpHSL9nl1XIWDkfMth1uxbD-AfLkqdiZL6S7HkZ",
  "data": {
    "schema": "EBEefH4LNQswHSrXanb-3GbjCZK7I_UCL6BdD-zwJ4my",
    "issuer": "EIaJ5gpHSL9nl1XIWDkfMth1uxbD-AfLkqdiZL6S7HkZ",
    "issueTimestamp": "2023-03-16T00:22:51.571027+00:00",
    "credential": "EPK9UORy9h29vJ4yiFVU5d_U80-6qbK3OwUJSYj5rb7h",
    "recipient": "EJS0-vv_OPAQCdJLmkd5dT0EW-mOfhn_Cje4yzRjTv8q",
    "journeyDestination": "Osireion",
    "gatekeeper": "Zaqiel",
    "negotiatedSplit": 50.00,
    "journeyCredential": "EJQMx6eOAMGQ01w37bsJNDvo6rHhMysmidwJxD9ti1bu"
  }
}
```

**Journey Charter**
```json
{
  "action": "iss",
  "actor": "EIaJ5gpHSL9nl1XIWDkfMth1uxbD-AfLkqdiZL6S7HkZ",
  "data": {
    "schema": "EEq0AkHV-i5-aCc1JMBGsd7G85HlBzI3BfyuS5lHOGjr",
    "issuer": "EIaJ5gpHSL9nl1XIWDkfMth1uxbD-AfLkqdiZL6S7HkZ",
    "issueTimestamp": "2023-03-16T00:22:51.571027+00:00",
    "credential": "ECn2kLVj_g4JYISLSXJ1YpvC8qW6YljE63dcc85ElAd7",
    "recipient": "EJS0-vv_OPAQCdJLmkd5dT0EW-mOfhn_Cje4yzRjTv8q",
    "partySize": 2,
    "authorizerName": "Zaqiel",
    "journeyCredential": "EJQMx6eOAMGQ01w37bsJNDvo6rHhMysmidwJxD9ti1bu",
    "markCredential": "EPK9UORy9h29vJ4yiFVU5d_U80-6qbK3OwUJSYj5rb7h",
    "destination": "Osireion",
    "treasureSplit": "50/50",
    "journeyEndorser": "Ramiel",
    "firstName": "Richard",
    "lastName": "Ayris",
    "nickname": "Dunkie"
  }
}
```

**Presentation Payload Field Key**
The following table contains a description for every field in all the credential presentation payloads defined above:

| Field Label                    | Description                                                                                        |
|--------------------------------|----------------------------------------------------------------------------------------------------|
| action                         | the action that triggered the web hook call.  Value will be "iss" for issue presentations          |
| actor                          | The AID of the presenter of the credential                                                         |
| data                           | Attributes specific to the credential being presented                                              |
| data -> schema                 | SAID of the schema of the credential that was presented                                            |
| data -> issuer                 | Issuer of the credential presented                                                                 |
| data -> issueTimestamp         | Issuance timestamp for the credential                                                              |
| data -> credential             | SAID of credential being presented                                                                 |
| data -> recipient              | AID of the holder of the credential                                                                |
| data -> destination            | The destination of the treasure hunting journey.                                                   |
| data -> journeyDestination     | Same as data -> destination                                                                        |
| data -> treasureSplit          | The percentage split of the treasure for each party member.                                        |
| data -> partyThreshold         | The party count at which the journey can be chartered.                                             |
| data -> journeyEndorser        | The name of the official ATHENA member endorsing the journey.                                      |
| data -> requester              | Data of the explorer making a journey request to ATHENA.                                           |
| data -> requester -> firstName | The first name of the requester.                                                                   |
| data -> firstName              | Same as data -> requester -> firstName                                                             |
| data -> requester -> lastName  | The last name of the requester.                                                                    |
| data -> lastName               | Same as data -> requester -> lastName                                                              |
| data -> requester -> nickname  | The nickname of the requester to be used at all times unless otherwise required.                   |
| data -> nickname               | Same as data -> requester -> nickname                                                              |
| data -> desiredPartySize       | The desired party count for the explorer making the request. Helps with matchmaking.               |
| data -> desiredSplit           | The desired treasure percentage split for the explorer making the request. Helps with matchmaking. |
| data -> journeyCredential      | The SAID of the journey credential chained to the credential being presented.                      |
| data -> gatekeeper             | The ATHENA member at the journey site to verify the Journey Charter.                               |
| data -> negotiatedSplit        | The actual negotiated split after matchmaking.                                                     |
| data -> authorizerName         | The ATHENA member authorizing a JourneyCharter.                                                    |
| data -> markCredential         | The SAID of the JourneyMark credential chained to the credential being presented.                  |



### Revocation
All revocation web hook requests will have the same format as follows:

**Revocation Payload**
```json
{
   "action": "rev",
   "actor": "EIaJ5gpHSL9nl1XIWDkfMth1uxbD-AfLkqdiZL6S7HkZ",
   "data": { 
       "schema": "EEq0AkHV-i5-aCc1JMBGsd7G85HlBzI3BfyuS5lHOGjr",
       "credential": "ECn2kLVj_g4JYISLSXJ1YpvC8qW6YljE63dcc85ElAd7",
       "revocationTimestamp": "2023-03-31T00:22:51.571027+00:00"
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


## Running

To properly test the Sally Abydos Gatekeeper server, one needs to check out the `master` branch of `https://github.com/TetraVeda/abydos-tutorial`, 
and follow the instructions in the README there.\
All repositories require python `3.10.4` to run as well as a local installation of `libsodium`.\
We recommend using a virtual environment technology(`pipenv` for example) for each repository.\
Finally, many of the bash commands and shell scripts require an installation of `jq` running locally.


### Abydos Tutorial Workflow

The Abydos Tutorial provides a script called `workflow.sh` you can run to start the entire network up and to initialize
all keystores.

```bash
# from within the root directory of abydos-tutorial
./workflow.sh
```

Leave the script running to be accessible to Sally.

The workflow script starts the following components for you:


## TODOs

TODO: Finish updating the rest of the readme
TODO: Update all of the tests to work with the new validation and payload functions.

# Warning

WARNING: Everything below this line is not revised and you can ignore it.

_________________________________________


### KERIpy

From KERIpy you will run 1 server that provide witnesses.  In addition, you will run a shell script which uses `kli` to
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
kli vc present --name qvi --alias qvi --said ${LE_SAID} --recipient sally --include
```

### Revoking Credentials
To revoke a credential from the command line, use the `kli vc revoke` command as follows.  Note the use of the `---send` 
command line option to specify additional parties (AIDs or aliases) to send the revocation events to:

```bash
LE_SAID=`kli vc list --name legal-entity --alias legal-entity --said`
kli vc revoke --name qvi --alias qvi --registry-name vLEI-qvi --said "$LE_SAID" --send sally
```

The SAID value (after the --said option) is the SAID of the credential to revoke.  Specifying the `sally` alias will result
in the revocation events being sent to Sally which will process them and report to the web hook the revocation.
