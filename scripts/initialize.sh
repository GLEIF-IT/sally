#!/bin/bash

kli init --name sally --nopasscode --config-dir ../keripy/scripts --config-file demo-witness-oobis-schema --salt 0ACDXyMzq1Nxc4OWxtbm9fle
kli incept --name sally --alias sally --file ../keripy/scripts/demo/data/trans-wits-sample.json
