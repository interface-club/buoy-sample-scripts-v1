#!/usr/bin/env python3
"""Create a Ramp fund through POST /developer/v1/funds.

Inputs:
- Simple mode: USER_ID is required. Optional DISPLAY_NAME, SPEND_PROGRAM_ID,
  IS_SHAREABLE, PERMITTED_SPEND_TYPES_JSON, SPENDING_RESTRICTIONS_JSON, and
  ACCOUNTING_RULES_JSON are assembled into the request body.
- Advanced mode: BODY_JSON is sent as the exact fund create request body.

Important JSON shapes for fund creation:
- permitted_spend_types must use request keys:
  {"physical_card": bool, "virtual_card": bool, "reimbursements": bool}
  Do not use response keys physical_card_enabled, virtual_card_enabled, or
  reimbursements_enabled.
- spending_restrictions.limit and transaction_amount_limit use request money
  objects such as {"amount": 50000, "currency_code": "USD"}. Amount is in the
  smallest currency unit, such as cents for USD. Do not include
  minor_unit_conversion_rate; it is a read-only response field.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _lib.runner import run

if __name__ == "__main__":
    run(Path(__file__).resolve())
