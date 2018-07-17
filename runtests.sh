python3 -m paranoid tests/testauto.py
PYTHONPATH=$(pwd):$PYTHONPATH python3 -m pytest tests/tests.py
