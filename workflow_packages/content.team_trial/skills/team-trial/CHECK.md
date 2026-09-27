# Deterministic output compiler

Extract the single Python fence below into a scratch module and import `compile_brief`.
Use this code unchanged; the offline tests exercise these same bytes. Pass the candidate
object and the actual normalized `trial_minutes` input. Serialize the returned object with
`json.dumps(result, ensure_ascii=False, indent=2)` to the declared output, with a trailing
newline. Reject output over 48,000 UTF-8 bytes. Do not execute repository code.

This compiler checks structure, reference integrity, disclosure labels and output bounds.
It cannot prove a citation entails a natural-language claim or that a `shareable` label is
true. Perform the separate evidence/semantic review in SKILL.md before the human review.

```python
"""Deterministic contract and rendering for one forwardable buyer brief."""

import ipaddress
import re
from urllib.parse import urlsplit

FIELDS = {
    "status",
    "product",
    "reader",
    "hypothesis",
    "evidence",
    "capability_ids",
    "access_id",
    "limitation_ids",
    "price_id",
    "steps",
    "success",
    "stop",
    "notes",
}
KINDS = {"capability", "access", "limitation", "price", "context"}


def bounded(value, limit, *, empty=False):
    if not isinstance(value, str) or len(value) > limit:
        raise ValueError("Text type or bound is invalid")
    if not empty and not value.strip():
        raise ValueError("Required text is blank")
    if any(ord(c) < 32 for c in value):
        raise ValueError("Use single-line text without control characters")
    return value.strip()


def items(value, minimum, maximum):
    if not isinstance(value, list) or not minimum <= len(value) <= maximum:
        raise ValueError("List bound is invalid")
    return value


def exact(value, fields):
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError("Object fields do not match the contract")


def public_url(value):
    value = bounded(value, 500)
    parts = urlsplit(value)
    host = parts.hostname or ""
    if (
        parts.scheme != "https"
        or not host
        or "." not in host
        or parts.username
        or parts.password
        or parts.query
        or parts.port not in (None, 443)
        or host.endswith((".local", ".internal", ".localhost"))
        or any(c in value for c in '<>\\" ')
    ):
        raise ValueError("Use a public HTTPS documentation URL without a query or credentials")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        raise ValueError("Private-address source URL")
    return value


def escape(value):
    value = value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return re.sub(r"([\\`*_{}\[\]()#+!|])", r"\\\1", value)


def compile_brief(candidate, *, trial_minutes=30):
    exact(candidate, FIELDS)
    if type(trial_minutes) is not int or not 15 <= trial_minutes <= 60:
        raise ValueError("Proposed timebox must be 15–60 minutes")
    status = candidate["status"]
    if status not in {"ready", "needs_context", "not_applicable"}:
        raise ValueError("Unknown status")
    notes = [bounded(n, 500) for n in items(candidate["notes"], 0, 6)]
    ledger = {}
    for row in items(candidate["evidence"], 0, 12):
        exact(row, {"id", "kind", "text", "source", "public_url", "shareable"})
        identifier = bounded(row["id"], 12)
        if not re.fullmatch(r"E[1-9][0-9]?", identifier) or identifier in ledger:
            raise ValueError("Evidence IDs must be unique E1–E99 identifiers")
        if row["kind"] not in KINDS or type(row["shareable"]) is not bool:
            raise ValueError("Invalid evidence classification")
        entry = {**row, "text": bounded(row["text"], 350), "source": bounded(row["source"], 500)}
        if row["shareable"]:
            entry["public_url"] = public_url(row["public_url"])
        elif row["public_url"] != "":
            raise ValueError("Internal evidence must not carry a forwarded URL")
        ledger[identifier] = entry
    for name, limit in [
        ("product", 80),
        ("reader", 120),
        ("hypothesis", 400),
        ("success", 300),
        ("stop", 300),
    ]:
        bounded(candidate[name], limit, empty=status != "ready")
    if status != "ready":
        if not notes or any(
            candidate[k]
            for k in [
                "product",
                "reader",
                "hypothesis",
                "capability_ids",
                "access_id",
                "limitation_ids",
                "price_id",
                "steps",
                "success",
                "stop",
            ]
        ):
            raise ValueError("Diagnostic requires a reason and no invented brief")
        return {
            "status": status,
            "forwardable_markdown": "",
            "review": {
                "notes": notes,
                "sources": list(ledger.values()),
                "selected_ids": [],
                "word_count": 0,
                "proposed_minutes": trial_minutes,
            },
        }

    selected = []

    def select(identifier, kind=None):
        if not isinstance(identifier, str) or identifier not in ledger:
            raise ValueError("Unknown evidence reference")
        entry = ledger[identifier]
        if not entry["shareable"] or entry["kind"] == "context":
            raise ValueError("Internal context cannot enter forwarded copy")
        if kind is not None and entry["kind"] != kind:
            raise ValueError("Evidence reference has the wrong kind")
        if identifier not in selected:
            selected.append(identifier)
        return entry

    def references(value, kind):
        values = items(value, 1, 3)
        if any(not isinstance(v, str) for v in values) or len(set(values)) != len(values):
            raise ValueError("Repeated or invalid evidence reference")
        return [select(v, kind) for v in values]

    capabilities = references(candidate["capability_ids"], "capability")
    access = select(candidate["access_id"], "access")
    limitations = references(candidate["limitation_ids"], "limitation")
    price = select(candidate["price_id"], "price") if candidate["price_id"] != "" else None
    actions = []
    for step in items(candidate["steps"], 2, 4):
        exact(step, {"action", "evidence_ids"})
        action = bounded(step["action"], 280)
        ids = items(step["evidence_ids"], 1, 3)
        if any(not isinstance(i, str) for i in ids) or len(set(ids)) != len(ids):
            raise ValueError("Invalid step references")
        for identifier in ids:
            select(identifier)
        actions.append(action)
    if len(set(actions)) != len(actions):
        raise ValueError("Trial actions must not repeat")

    def fact(entry):
        return f"{escape(entry['text'])} ([source](<{entry['public_url']}>))"

    lines = [
        f"# A small team trial of {escape(candidate['product'])}",
        "",
        f"For: {escape(candidate['reader'])}",
        "",
        "## Why consider it",
        "",
        f"Working hypothesis: {escape(candidate['hypothesis'])}",
        "",
        "## What the product supports",
        "",
        *[f"- {fact(e)}" for e in capabilities],
        "",
        "## What access requires",
        "",
        fact(access),
        "",
        fact(price)
        if price
        else (
            "Current price and ongoing spend are unverified. Agree a spending limit "
            "before enabling any paid use."
        ),
        "",
        f"## Proposed {trial_minutes}-minute trial",
        "",
        "Use synthetic or public material. This is a proposed evaluation timebox, "
        "not a measured setup or completion promise.",
        "",
        *[f"{n}. {escape(action)}" for n, action in enumerate(actions, 1)],
        "",
        f"**Continue if:** {escape(candidate['success'])}",
        "",
        f"**Stop if:** {escape(candidate['stop'])}",
        "",
        "## Limits to know",
        "",
        *[f"- {fact(e)}" for e in limitations],
        "",
        "## The decision",
        "",
        "Would you be open to this small evaluation before we consider wider use? "
        "Please agree who will run it and the allowed data and spend first. "
        "No purchase, migration or rollout is being requested here.",
        "",
    ]
    copy = "\n".join(lines)
    # Ignore link destinations for the reader-facing word limit.
    word_count = len(re.sub(r"\]\(<[^>]+>\)", "]", copy).split())
    if word_count > 450 or len(copy.encode()) > 16000:
        raise ValueError("Brief exceeds the 450-word / 16000-byte budget")
    return {
        "status": "ready",
        "forwardable_markdown": copy,
        "review": {
            "notes": notes,
            "sources": list(ledger.values()),
            "selected_ids": selected,
            "word_count": word_count,
            "proposed_minutes": trial_minutes,
        },
    }
```
