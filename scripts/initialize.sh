#!/bin/bash

kli init --name sally --nopasscode --config-dir ./scripts --config-file sally.json
kli incept --name sally --alias sally --file ./scripts/sally-incept.json

