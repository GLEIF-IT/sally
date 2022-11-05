#!/bin/bash

kli init --name sally --nopasscode --config-dir ./scripts --config-file local-oobis-schema
kli incept --name sally --alias sally --file ./scripts/data/local.json

