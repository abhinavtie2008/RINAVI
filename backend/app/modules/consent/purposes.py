"""The consent purposes this service recognises.

The list lives in one place so the grant request schema and the route guards
cannot drift apart. `ConsentPurpose` is a `Literal`, so a typo in a
`ConsentRequired(...)` call fails pyright instead of silently creating a guard
nobody can ever satisfy, and the schema rejects anything outside the list.
"""

from typing import Literal, get_args

# The four purposes described in docs/compliance/data-map.md §4. Exact
# strings: no case folding, no truncation, no aliases.
ConsentPurpose = Literal[
    "documents.processing",
    "profile.storage",
    "applications.preparation",
    "locker.tracking",
]

CONSENT_PURPOSES: tuple[str, ...] = get_args(ConsentPurpose)
