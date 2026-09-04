#!/bin/bash
# Deploy skill-opt in an independent subdirectory with its own Python venv
set -e

SKILLOPT_DIR="/data/yjh/skill-opt"
REPO_DIR="$SKILLOPT_DIR/repo"
VENV_DIR="$SKILLOPT_DIR/venv"

echo "=== Step 1: Clean and clone skill-opt ==="
rm -rf "$REPO_DIR"
mkdir -p "$SKILLOPT_DIR"
cd "$SKILLOPT_DIR"
git clone --depth 1 https://github.com/microsoft/SkillOpt.git repo 2>&1
echo "Clone done."

echo "=== Step 2: Check repo contents ==="
ls "$REPO_DIR/" | head -20
echo "---"

echo "=== Step 3: Create independent Python venv ==="
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip setuptools wheel 2>&1 | tail -3
echo "venv created at $VENV_DIR"

echo "=== Step 4: Install dependencies ==="
if [ -f "$REPO_DIR/requirements.txt" ]; then
    pip install -r "$REPO_DIR/requirements.txt" 2>&1 | tail -5
elif [ -f "$REPO_DIR/setup.py" ]; then
    cd "$REPO_DIR" && pip install -e . 2>&1 | tail -5
elif [ -f "$REPO_DIR/pyproject.toml" ]; then
    cd "$REPO_DIR" && pip install -e . 2>&1 | tail -5
else
    echo "No requirements found, installing common ML deps"
    pip install numpy pandas scikit-learn 2>&1 | tail -3
fi
echo "Dependencies installed."

echo "=== Step 5: Summary ==="
echo "Repo: $REPO_DIR"
echo "Venv: $VENV_DIR"
echo "To activate: source $VENV_DIR/bin/activate"
echo "=== Deploy complete ==="