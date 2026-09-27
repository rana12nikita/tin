"""Exercise the exact compiler shipped with the procedure, not simulated agent quality."""

import json
import re
from copy import deepcopy
from pathlib import Path

import pytest

from tin_lite.community import ContributedPackage, validate, validate_private_copy
from tin_lite.workflow_qualification import Qualification, assess_output, check_package

ROOT = Path(__file__).resolve().parents[1]
KEY = "content.team_trial"
PACKAGE = ROOT / "workflow_packages" / KEY
CHECK = PACKAGE / "skills/team-trial/CHECK.md"
CODE = re.findall(r"```python\n(.*?)\n```", CHECK.read_text(), re.S)
assert len(CODE) == 1
NAMESPACE = {}
exec(compile(CODE[0], str(CHECK), "exec"), NAMESPACE)  # noqa: S102
compile_brief = NAMESPACE["compile_brief"]


def evidence(identifier, kind, content, *, shareable=True):
    return {
        "id": identifier,
        "kind": kind,
        "text": content,
        "source": f"fixture-revision:docs/product.md#{identifier}",
        "public_url": f"https://example.com/docs#{identifier}" if shareable else "",
        "shareable": shareable,
    }


def candidate():
    return {
        "status": "ready",
        "product": "Briefboard",
        "reader": "A design-team lead",
        "hypothesis": "A reusable handoff checklist may make project handovers easier to review.",
        "evidence": [
            evidence("E1", "capability", "Briefboard exports a handoff checklist as a PDF."),
            evidence("E2", "access", "Creating a checklist requires a Briefboard account."),
            evidence("E3", "limitation", "The export does not include attached design files."),
            evidence("E4", "context", "INTERNAL_ONLY_CUSTOMER_SECRET", shareable=False),
        ],
        "capability_ids": ["E1"],
        "access_id": "E2",
        "limitation_ids": ["E3"],
        "price_id": "",
        "steps": [
            {"action": "Create a checklist for a fictional project.", "evidence_ids": ["E1", "E2"]},
            {
                "action": "Export the PDF and have a teammate review its contents.",
                "evidence_ids": ["E1", "E3"],
            },
        ],
        "success": "A teammate can identify every required handoff item in the exported PDF.",
        "stop": "An essential file or permission is missing, or paid access is required.",
        "notes": ["Synthetic fixture, not a real customer or live Tin run."],
    }


def diagnostic(status="needs_context"):
    value = candidate()
    value.update(
        status=status,
        product="",
        reader="",
        hypothesis="",
        evidence=[],
        capability_ids=[],
        access_id="",
        limitation_ids=[],
        price_id="",
        steps=[],
        success="",
        stop="",
        notes=["Complete the product Code map in Tin first."],
    )
    return value


def qualification():
    return Qualification.model_validate_json(
        (ROOT / "workflow_evals" / KEY / "qualification.json").read_bytes()
    )


async def test_public_and_private_package_contracts():
    package = ContributedPackage(key=KEY, path=PACKAGE)
    await validate(package, root=ROOT)
    await validate_private_copy(package, root=ROOT)


async def test_qualification_inputs_and_unmeasured_cost():
    files = {
        p.relative_to(ROOT).as_posix(): p.read_bytes() for p in PACKAGE.rglob("*") if p.is_file()
    }
    result = await check_package(files, f"workflow_packages/{KEY}/workflow.json", qualification())
    assert result["shape"]["status"] == "passed"
    assert result["cost"]["basis"] == "unmeasured"
    assert result["evaluation"]["status"] == "not_run"


def test_package_declares_all_resources_and_has_no_founder_fact_fields():
    spec = json.loads((PACKAGE / "workflow.json").read_text())["definition"]
    declared = {"workflow.json", "PROMPT.md", *spec["procedure"]["skill_files"]}
    actual = {p.relative_to(PACKAGE).as_posix() for p in PACKAGE.rglob("*") if p.is_file()}
    assert declared == actual
    assert set(spec["input_schema"]["properties"]) == {
        "project_id",
        "reader",
        "focus",
        "trial_minutes",
    }
    assert spec["procedure"]["workspace"]["capabilities"] == ["contents.read"]
    assert spec["human_review"]["eligible"] is True


def test_ready_output_preserves_facts_and_omits_internal_source_from_copy():
    source = candidate()
    result = compile_brief(source)
    copy = result["forwardable_markdown"]
    assert "Briefboard exports a handoff checklist as a PDF." in copy
    assert "Current price and ongoing spend are unverified" in copy
    assert "INTERNAL_ONLY_CUSTOMER_SECRET" not in copy
    assert "fixture-revision" not in copy
    assert "Proposed 30-minute trial" in copy
    assert "Continue if:" in copy and "Stop if:" in copy
    assert result["review"]["word_count"] <= 450
    assert result["review"]["selected_ids"] == ["E1", "E2", "E3"]
    assert source == candidate()  # No mutation of the evidence on retry.
    assert result == compile_brief(source)


@pytest.mark.parametrize("status", ["needs_context", "not_applicable"])
def test_diagnostics_have_no_forwardable_copy(status):
    result = compile_brief(diagnostic(status))
    assert result["status"] == status
    assert result["forwardable_markdown"] == ""
    assert result["review"]["word_count"] == 0


@pytest.mark.parametrize(
    "field,value",
    [
        ("capability_ids", ["E99"]),
        ("capability_ids", ["E4"]),
        ("capability_ids", ["E2"]),
        ("capability_ids", ["E1", "E1"]),
        ("limitation_ids", []),
        ("access_id", ""),
        ("price_id", "E1"),
        ("status", "completed"),
        ("steps", []),
        ("notes", ["x"] * 7),
    ],
)
def test_plausible_but_unusable_candidate_is_rejected(field, value):
    source = candidate()
    source[field] = value
    with pytest.raises(ValueError):
        compile_brief(source)


@pytest.mark.parametrize("change", ["unknown", "internal", "empty", "duplicate"])
def test_trial_actions_require_valid_public_evidence(change):
    source = candidate()
    source["steps"][0]["evidence_ids"] = {
        "unknown": ["E99"],
        "internal": ["E4"],
        "empty": [],
        "duplicate": ["E1", "E1"],
    }[change]
    with pytest.raises(ValueError):
        compile_brief(source)


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com",
        "javascript:alert(1)",
        "https://user:pass@example.com/",
        "https://example.com/?token=secret",
        "https://127.0.0.1/docs",
        "https://docs.local/path",
        "https://example.com/<script>",
    ],
)
def test_unsafe_public_links_are_rejected(url):
    source = candidate()
    source["evidence"][0]["public_url"] = url
    with pytest.raises(ValueError):
        compile_brief(source)


@pytest.mark.parametrize("minutes", [True, 0, 14, 61, "30", 30.0])
def test_timebox_is_a_bounded_integer(minutes):
    with pytest.raises(ValueError):
        compile_brief(candidate(), trial_minutes=minutes)


def test_wrongly_marked_private_source_does_not_pass_as_a_public_reference():
    source = candidate()
    source["evidence"][0]["shareable"] = False
    with pytest.raises(ValueError):
        compile_brief(source)


def test_known_price_is_copied_only_from_a_price_record():
    source = candidate()
    source["evidence"].append(evidence("E5", "price", "Synthetic example price: $8 per seat."))
    source["price_id"] = "E5"
    result = compile_brief(source)["forwardable_markdown"]
    assert "Synthetic example price: $8 per seat." in result
    assert "Current price and ongoing spend are unverified" not in result


def test_overlong_copy_is_rejected_instead_of_truncated():
    source = candidate()
    source["hypothesis"] = "word " * 79
    source["success"] = "word " * 59
    source["stop"] = "word " * 59
    for row in source["evidence"][:3]:
        row["text"] = "word " * 69
    with pytest.raises(ValueError, match="450-word"):
        compile_brief(source)


def test_html_and_markdown_in_product_text_cannot_become_active_markup():
    source = candidate()
    source["product"] = "<img src=x> [click](https://evil.example)"
    result = compile_brief(source)["forwardable_markdown"]
    assert "<img" not in result
    assert "[click](https://evil.example)" not in result


def test_duplicate_evidence_ids_and_diagnostic_with_copy_fail():
    source = candidate()
    source["evidence"][1]["id"] = "E1"
    with pytest.raises(ValueError):
        compile_brief(source)
    source = diagnostic()
    source["product"] = "Unsupported product"
    with pytest.raises(ValueError):
        compile_brief(source)


def test_ordinary_qualification_rejects_diagnostic_or_advice_only_output():
    case = next(c for c in qualification().cases if c.id == "ordinary")
    useful = compile_brief(candidate())
    assert (
        assess_output(case, status="succeeded", content=json.dumps(useful).encode())["status"]
        == "passed"
    )
    for bad in [compile_brief(diagnostic()), {**useful, "forwardable_markdown": "Write a brief."}]:
        assert (
            assess_output(case, status="succeeded", content=json.dumps(bad).encode())["status"]
            == "failed"
        )


def test_shape_validation_does_not_claim_to_prove_entailment():
    # A referenced but exaggerated claim is structurally valid. The rubric/live review
    # must reject it; this test preserves that known boundary instead of claiming safety.
    source = candidate()
    source["evidence"][0]["text"] = "Briefboard guarantees a 90% reduction in handoff time."
    result = compile_brief(source)
    assert "90%" in result["forwardable_markdown"]
    assert any(r.id == "entailment" for r in qualification().rubric)


def test_alternative_product_does_not_retain_fixture_product_or_use_case():
    source = deepcopy(candidate())
    source.update(
        product="Scheduleboard",
        reader="An operations teammate",
        hypothesis="A shared availability link may simplify choosing a meeting time.",
        success="A teammate can choose an available time from the test link.",
        stop="The proposed time conflicts with the test calendar.",
    )
    source["evidence"] = [
        evidence("E1", "capability", "Scheduleboard creates a shared availability link."),
        evidence("E2", "access", "Creating a link requires connecting a calendar."),
        evidence(
            "E3", "limitation", "The link exposes only the availability configured by its owner."
        ),
    ]
    source["steps"] = [
        {"action": "Create a link from a synthetic test calendar.", "evidence_ids": ["E1", "E2"]},
        {"action": "Have one teammate choose a time from that link.", "evidence_ids": ["E1", "E3"]},
    ]
    result = compile_brief(source)["forwardable_markdown"]
    assert "Scheduleboard" in result
    assert "Briefboard" not in result and "PDF" not in result and "handoff" not in result
