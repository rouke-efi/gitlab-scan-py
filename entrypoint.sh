#!/bin/bash
set -e

if [ "$1" = "test" ]; then
    echo "Running unit tests..."
    python -m unittest discover -v
elif [ "$1" = "compare" ]; then
    echo "Running comparison..."
    python test_out.py
else
    echo "Running application..."
    python gl-terraform-analyzer.py
fi