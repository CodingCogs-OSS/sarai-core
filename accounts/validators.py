"""Phone number normalization and validation for Iranian mobile numbers.

Customer identity is keyed on the phone number, so the stored value must be in a
single canonical form. Everything is normalized to E.164 (``+989121234567``)
before it reaches the database; the validator then guards the stored form.
"""

import re

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

# Canonical stored form: +98 followed by a 10-digit mobile number starting with 9.
E164_IRANIAN_MOBILE = r"^\+989\d{9}$"

validate_iranian_mobile = RegexValidator(
    regex=E164_IRANIAN_MOBILE,
    message="Enter a valid Iranian mobile number in E.164 format, e.g. +989121234567.",
    code="invalid_iranian_mobile",
)

# Iranian users routinely paste numbers containing Persian or Arabic-Indic
# digits, which are numerically correct but not ASCII.
_NON_ASCII_DIGITS = str.maketrans(
    "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
    "01234567890123456789",
)

# Separators people type or that get pasted in from contact lists.
_SEPARATORS = re.compile(r"[\s\-().]")

_INVALID_MESSAGE = "Enter a valid Iranian mobile number, e.g. 09121234567."


def normalize_iranian_mobile(value):
    """Return ``value`` as an E.164 Iranian mobile number.

    Accepts the formats users actually type: ``09121234567``, ``9121234567``,
    ``+989121234567``, ``00989121234567``, with or without spaces, dashes and
    parentheses, in ASCII or Persian/Arabic-Indic digits.

    Raises ``ValidationError`` if the value cannot be interpreted as an Iranian
    mobile number.
    """
    if value is None:
        raise ValidationError(_INVALID_MESSAGE, code="invalid_iranian_mobile")

    digits = _SEPARATORS.sub("", str(value).strip()).translate(_NON_ASCII_DIGITS)
    digits = digits.removeprefix("+")

    if not digits.isdigit():
        raise ValidationError(_INVALID_MESSAGE, code="invalid_iranian_mobile")

    # Strip whichever country/trunk prefix is present. Length is part of the
    # test because a bare subscriber number can itself start with "98".
    if digits.startswith("0098") and len(digits) == 14:
        subscriber = digits[4:]
    elif digits.startswith("98") and len(digits) == 12:
        subscriber = digits[2:]
    elif digits.startswith("0") and len(digits) == 11:
        subscriber = digits[1:]
    else:
        subscriber = digits

    if len(subscriber) != 10 or not subscriber.startswith("9"):
        raise ValidationError(_INVALID_MESSAGE, code="invalid_iranian_mobile")

    return f"+98{subscriber}"
