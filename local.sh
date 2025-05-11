#!/bin/bash
source .venv/bin/activate
watchmedo auto-restart --patterns="*.py" --recursive -- python bolt.py
