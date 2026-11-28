"""The consent purposes this service recognises.

The list lives in one place so the grant request schema and the route guards
cannot drift apart. `ConsentPurpose` is a `Literal`, so a typo in a
`ConsentRequired(...)` call fails pyright instead of silently creating a guard
nobody can ever satisfy, and the schema rejects anything outside the list.

The grant request field stays typed `str` rather than `ConsentPurpose` on
purpose: typing it `ConsentPurpose` would publish the enum in OpenAPI and
replace the single "Unknown consent purpose. Accepted values: ..." message with
per-variant validation errors. The explicit message won, so OpenAPI still
describes the field as a 1-80 character string and the four values live in this
module, in the data map (§4) and in the web consent page.
"""

from typing import Literal, get_args

# The four purposes described in docs/compliance/data-map.md §4. The strings
# are exact: no case folding, no truncation, no aliases. Surrounding whitespace
# is trimmed by the grant request schema before this check, so
# " documents.processing " is accepted; nothing else is normalised.
# tests/unit/test_consent_guard.py fails if this tuple and the §4 table
# disagree, in either direction.
ConsentPurpose = Literal[
    "documents.processing",
    "profile.storage",
    "applications.preparation",
    "locker.tracking",
]

CONSENT_PURPOSES: tuple[str, ...] = get_args(ConsentPurpose)
