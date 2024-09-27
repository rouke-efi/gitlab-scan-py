#!/bin/bash
set -e

if [ "$1" = "test" ]; then
    echo "Running unit tests..."
    python -m unittest test_gl_terraform_analyzer.py
elif [ "$1" = "compare" ]; then
    echo "Running comparison..."
    python test_out.py
else
    echo "Running application..."
    python gl_terraform_analyzer.py
fi