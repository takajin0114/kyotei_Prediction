#!/bin/bash

python3 scripts/generate_run_report.py
echo "run_report.md updated"

python3 scripts/generate_chat_context.py
echo "chat_context.md updated"
