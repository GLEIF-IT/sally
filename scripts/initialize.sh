#!/bin/bash

kli init --name sally --nopasscode --config-dir ./scripts --config-file vlei-sally-oobis-schema
kli incept --name sally --alias sally --file ./scripts/data/sally.json

