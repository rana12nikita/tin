# A small decision, not a sales deck

Someone can discover a useful tool on LinkedIn and still be unable to get a teammate to try
it. This workflow supplies the missing internal handoff: a forwardable trial proposal that
states the job, shows only supported capabilities, makes the access/cost uncertainty visible,
and specifies what evidence would justify continuing. It should save the discoverer from
writing a business case from scratch. It does not infer that this problem occurred for a
particular customer or that forwarding will cause conversion.

## Inputs and context

Only `project_id` is required. Optional `reader` and `focus` name an intended audience or
use case that Tin cannot know for this particular run. `trial_minutes` is the founder's
proposed evaluation time budget, default 30, bounded 15–60. Do not ask for feature lists,
social comments, CSVs or copied product facts. The native onboarding and product-map
workflows supply those facts; if they are absent, name the prerequisite to complete.

## Selection and refusal

Select one use case in this order:
1. Fits the primary audience in onboarding and the optional focus.
2. Has verified access/setup context, public-safe capability evidence and a material limitation.
3. Can be evaluated on synthetic/public data without switching the whole team.
4. Has an observable pass/fail outcome within a proposed bounded session.

Prefer fewer dependencies, then fewer trial steps. Do not invent a numerical opportunity
score. A source contradiction about access, a required feature or data handling blocks
`ready`; a newer timestamp alone does not resolve incompatible claims. Unknown optional
features can simply be omitted. Unverified current pricing is allowed only as an explicit
unknown and a hold on paid use. A plan price may be included only when a dated published
pricing source is available in project context and is no more than seven days old as of the
run; otherwise omit the price fact. Never call the product free because source code is open.

Publicly accessible source code may support a capability or limitation only after reconciling
the relevant implementation with the Tin Code map. Cite a revision-pinned public source URL
and label the conclusion as implemented code, for example, "The public code implements an
appointment-cancellation endpoint; runtime behavior is unverified." Preserve that qualifier
in the forwarded fact and do not turn it into a verified runtime claim. A runtime claim needs
separate recorded test evidence in project context, with its environment and scope stated.
Public source alone does not establish deployment availability, clinical suitability,
compliance, concurrency guarantees, actual performance or production readiness. These claims
must not be inferred from function names, tests present in the repository, or a Code map.

Code visibility is not a setup guide. Access requirements and a safe executable trial still
need real, verified setup instructions or project context: prerequisites, a test environment,
and how the intended reader can reach the selected feature. If those are missing, return
`needs_context`; do not invent a URL, working deployment or setup steps. Private source is
internal evidence unless the specific public claim has explicit approval and an established
public evidence URL. Missing disclosure permission remains a blocker.

Return `needs_context` when product identity, audience, access, capability, publication
permission or safe trial path is missing. Return `not_applicable` when existing context
establishes personal-only use and no meaningful teammate decision. Both diagnostics must
have empty forwarded copy and a precise next step, not a made-up asset.

## Candidate contract

The compiler in CHECK.md is the authoritative shape. Build a JSON object with:

- `status`: `ready`, `needs_context` or `not_applicable`.
- `product`, `reader`, `hypothesis`: plain text. The hypothesis states a proposed job to
  evaluate, not an observed customer result or quotation.
- `evidence`: up to 12 records with `id`, `kind` (`capability`, `access`, `limitation`,
  `price` or `context`), `text`, `source`, `public_url`, `shareable`. `source` is the internal
  file/section or repository revision/path/line locator; `public_url` is an established
  HTTPS public evidence URL without auth/session tokens. Internal context has an
  empty public URL and `shareable: false`. Publicly shareable records must have one.
- `capability_ids`: 1–3 capability IDs; `access_id`: one access ID; `limitation_ids`: 1–3
  limitation IDs; `price_id`: one price ID or empty. All must be shareable.
- `steps`: 2–4 records with `action` and `evidence_ids` (1–3 references). Actions are
  proposed experiment instructions; they must not imply unsupported product behavior.
- `success`: an observable proposed pass criterion; `stop`: a proposed stop rule. Neither
  promises results. `notes`: at most six internal review notes.

Diagnostics use the same keys but no product claims, no selected IDs or steps; `notes`
identifies the missing context/reason. They may retain unselected evidence for the reviewer.
All forwarded facts and source URLs are copied from the checked ledger by code; code
prevents internal-only records from being selected. Natural-language fields still need a
semantic review for unsupported assertions or accidental disclosure.

## Why this is a separate job

`content.public_article` is editorial long-form content; `creative.product_demo` is a
video; `qa.buyer_trust` audits a site/checkout; open PR #64 mines supplied sales objections
and recommends messaging changes. This package produces a finished peer-forwarded trial
proposal from existing context, without requiring an inbox or a customer interview corpus.
The ordinary artifact must contain usable copy; an advice-only output is a failure.

## Idea sources

- [Atlassian's lean business case](https://www.atlassian.com/software/confluence/templates/safe-lean-business-case)
  uses a benefit hypothesis and a bounded experiment instead of relying on speculative ROI.
- [Slack's migration guide](https://slack.com/blog/transformation/teams-to-slack-migration)
  shows that adoption involves a business case and people beyond the initial discoverer.

These are inspiration for the buyer handoff, not evidence that our workflow improves
conversion. We adapt it into a small vendor-prepared marketing asset, not an enterprise
migration plan. No source wording, customer data or claimed performance is reused.

## Measurement after distribution

The package writes the brief only. The founder can place the reviewed asset beside a demo
or trial link and observe qualified trials where a second teammate participates. A bounded
comparison of otherwise similar leads offered the brief vs the existing demo would be a
possible future experiment; no such experiment has been run. Do not put invented conversion
metrics or a measurement checklist into the forwardable copy.
