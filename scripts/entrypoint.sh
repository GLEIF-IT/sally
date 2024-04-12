#!/bin/bash

kli init --name sally --nopasscode --config-dir ./scripts --config-file docker-oobis
kli incept --name sally --alias sally --file ./scripts/data/local.json
sally server start --name sally --alias sally --web-hook http://sally-demo:9923 --auth EHOuGiHMxJShXHgSb6k_9pqxmRb8H-LT0R2hQouHp8pW
