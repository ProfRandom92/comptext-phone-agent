#!/usr/bin/env fish
set ROOT (cd (dirname (status filename)); and pwd)
exec "$ROOT/.venv/bin/comptext-phone" $argv
