import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app as app_module


def test_calculate_total_empty():
    assert app_module.calculate_total([]) == 0


def test_calculate_total_multiple():
    invoices = [{"amount": 10}, {"amount": 20}]
    assert app_module.calculate_total(invoices) == 30


def test_calculate_total_wrong_expectation():
    # Planted edge case: this assertion is simply wrong (expects 100 instead of
    # 10). calculate_total itself is correct -- the test is the bug.
    invoices = [{"amount": 5}, {"amount": 5}]
    assert app_module.calculate_total(invoices) == 100
