#!/bin/bash
# Deploy skill-opt — remaining steps (clone + venv already done)
set -e

SKILLOPT_DIR="/data/yjh/skill-opt"
VENV_PYTHON="$SKILLOPT_DIR/venv/bin/python3"
VENV_PIP="$SKILLOPT_DIR/venv/bin/pip"
REPO_DIR="$SKILLOPT_DIR/repo"

echo "=== Step 1: Install pip in venv ==="
curl -sL https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
$VENV_PYTHON /tmp/get-pip.py --break-system-packages 2>&1 | tail -3
echo "pip installed."

echo "=== Step 2: Install core dependencies ==="
$VENV_PIP install -r "$REPO_DIR/requirements.txt" 2>&1 | tail -10
echo "core deps done."

echo "=== Step 3: Install skillopt package in dev mode ==="
cd "$REPO_DIR"
$VENV_PIP install -e . 2>&1 | tail -5
echo "skillopt installed."

echo "=== Step 4: Verify ==="
$VENV_PIP list 2>&1 | head -15
echo "---"
echo "Python: $($VENV_PYTHON --version)"
echo "Pip: $($VENV_PIP --version)"

echo "=== DEPLOYMENT COMPLETE ==="
echo "Repo: $REPO_DIR"
echo "Venv: $SKILLOPT_DIR/venv"
echo "Activate: source $SKILLOPT_DIR/venv/bin/activate"