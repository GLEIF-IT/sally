#!/bin/bash

kli init --name kara --nopasscode --config-dir ../keripy/scripts --config-file demo-witness-oobis-schema
kli incept --name kara --alias kara --file ../keripy/scripts/demo/data/trans-wits-sample.json
kli oobi resolve --name kara --oobi-alias legal-entity --oobi http://127.0.0.1:5643/oobi/EKXPX7hWw8KK5Y_Mxs2TOuCrGdN45vPIZ78NofRlVBws/witness/BuyRFMideczFZoapylLIyCjSdhtqVb31wZkRKvPfNqkw
# kara server start --name kara --alias kara --web-hook http://127.0.0.1:9923
