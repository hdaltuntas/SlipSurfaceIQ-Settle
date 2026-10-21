#!/usr/bin/env bash
# SlipSurfaceIQ Settle - Linux/macOS: creates/updates the virtual environment and starts the app.
set -e
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    .venv/bin/python -m pip install --upgrade pip
fi
# Reinstall packages if requirements.txt changed (new release)
if ! cmp -s requirements.txt .venv/requirements.stamp; then
    echo "Installing / updating required packages..."
    .venv/bin/python -m pip install -r requirements.txt
    cp requirements.txt .venv/requirements.stamp
fi
.venv/bin/python -c "import sys; sys.path.insert(0, '.'); import slipsurface.settle as s, os; print('SlipSurfaceIQ Settle', s.__version__, '-', os.path.dirname(s.__file__))"
exec .venv/bin/python main.py "$@"
