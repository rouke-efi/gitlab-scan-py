#!/bin/bash
set -e

if [ "$1" = "test" ]; then
    echo "Running unit tests..."
    python -m unittest test_gl_terraform_analyzer.py
elif [ "$1" = "modules" ]; then
    echo "Find all modules with current versions"
    python gl_fetch_modules_in_use.py
else
    echo "Find all modules in use with version"
    python gl_terraform_analyzer.py
fi