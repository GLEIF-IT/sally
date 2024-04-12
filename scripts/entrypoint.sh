#!/bin/bash

if [ -z "$AUTH" ]; then
    echo "No auth"
    exit 1;
fi;

kli init --name sally --nopasscode --config-dir ./scripts --config-file docker-oobis
kli incept --name sally --alias sally --file ./scripts/data/local.json

sally server start --name sally --alias sally --web-hook http://sally-demo:9923 --auth "$AUTH"
