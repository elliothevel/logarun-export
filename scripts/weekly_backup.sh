#!/usr/bin/env bash

python logarun_export.py $(date --date='6 days ago' +%F) >/dev/null 2>&1
