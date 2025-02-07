#!/bin/bash
# Example start command
# Warning: Use your own salt and passcode. Do not use the example values below.

# This will use the config file located at ./scripts/keri/cf/sally.json
sally server start \
  --name sally \
  --alias sally \
  --salt 0AD3GmJxuDbCs90qC0ipHfOD \
  --passcode bWuSoMabM6CSSJUqc97YS \
  --web-hook http://127.0.0.1:9923 \
  --auth EHOuGiHMxJShXHgSb6k_9pqxmRb8H-LT0R2hQouHp8pW \
  --config-dir scripts \
  --config-file sally.json \
  --loglevel INFO
