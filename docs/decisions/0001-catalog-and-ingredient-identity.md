# 0001 — Catalog module and ingredient identity

- Status: accepted
- Date: 2026-09-28
- Supersedes: the product alias and Ania Gotuje tag models on `wip/ingredient-tags`
  (households migrations 0002–0007)

## Context

Recipes, inventory, shopping and promotions all need to know that a pantry product
such as "Jaja ściółkowe (opakowanie)" satisfies a recipe line such as "Jajko".
Two successive attempts left the production database in this state:

- `households.Product` is household-scoped and lives in `households`, so four
  features depend on the household bounded context for product identity.
- `households.IngredientTag` is a global vocabulary filled as a side effect of
  `GET` on external recipe search, and every row is labelled `ania_gotuje`.
  Of 282 rows, 243 look like provider tags (lower case, no digits or brackets),
  38 are byte-for-byte copies of product names, and 1 is ambiguous
  ("Dżem malinowy (słoik)"). Provider tags also contain non-ingredients
  ("dla dzieci") and duplicates ("jaja" / "jajka", "marchew" / "marchewka").
- `households.ProductTag` is a many-to-many link with `source` and `is_verified`.
  53 of its 105 rows reference product 11208, which does not exist; the dump was
  restored with foreign key checks disabled.
- `households.TagProposal` records recipe-name → product proposals and is empty.
- Matching is done three different ways: word containment plus tag equality in
  `shared.name_matching`, and prefix heuristics in the shopping repository.
- Two background LLM paths exist: a bounded management command behind the
  `IngredientMatcher` port, and an in-process thread in `households/tag_analysis_jobs.py`
  that also created products #56 and #57 with an empty unit and an unnormalized name.

## Decision

### Ownership

A new `catalog` feature owns `Ingredient`, `IngredientName`, `Product`,
`ProductIngredient` and `IngredientNameCandidate`. `households` keeps only the
household, membership, access and lifecycle. Other features reference catalog
tables with lazy Django references (`"catalog.Product"`) and reach catalog
behaviour only through its composition root.

### Model

```
Ingredient                 global, curated concept ("Jajka")
  IngredientName *         global; name, normalized_name UNIQUE, kind, source
Product                    household-scoped; name, normalized_name, unit, package content
  ProductIngredient *      product, ingredient, status, source, model_name?, proposed_at?, decided_at?
IngredientNameCandidate    name, normalized_name UNIQUE, source, reason, status
```

- `IngredientName.kind` is `canonical` or `alias`; `source` is `manual`,
  `ania_gotuje` or `legacy`. A provider never defines the domain vocabulary; its
  names enter as candidates or as names of an existing ingredient.
- `ProductIngredient.status` is `proposed`, `confirmed` or `rejected`;
  `source` is `manual`, `model` or `legacy`.
- `ProductIngredient` is the record of a classification process, not a plain
  many-to-many table. A product has one identity: what it *is*. Composition
  (what a mixed product *contains*) is a separate concept that does not exist yet
  and must not be expressed through this table.

### Invariants

1. A normalized name resolves to at most one ingredient
   (`IngredientName.normalized_name` is unique).
2. Every ingredient has exactly one canonical name. Enforced in the use case that
   creates it and by a unique stored generated column
   (`canonical_ingredient_id = ingredient_id when kind = 'canonical'`).
3. A product has at most one confirmed ingredient. Enforced by a unique stored
   generated column (`confirmed_product_id = product_id when status = 'confirmed'`);
   MariaDB has no partial unique indexes, and this was verified on 11.4.
4. There is at most one row per (product, ingredient). Rejections are kept, so a
   model never proposes a rejected pair again.
5. A pending shopping item and a purchased shopping item reference exactly one of
   `product_id`, `ingredient_id` or `free_text`.
6. Nothing writes to the catalog during a read request.
7. `confirmed_product_id` and `canonical_ingredient_id` are persistence mechanisms
   only. They are not part of the domain model or of the public `catalog` API.
8. `IngredientNameCandidate` never takes part in name resolution.
   `FindIngredientByName` searches accepted `IngredientName` rows only, so the
   quarantine cannot affect runtime behaviour.
9. Deleting or merging an `Ingredient` never leaves a `ProductIngredient` or a
   `RecipeIngredient` pointing at a semantically different ingredient. A merge is a
   dedicated transactional use case, not generic CRUD in Django admin; the admin
   does not offer ingredient deletion.

### Transitions of `ProductIngredient`

| operation | from | to | notes |
|---|---|---|---|
| `ProposeProductIngredient` | (none) | proposed | only when the product has no confirmed ingredient and the pair has no row |
| `ConfirmProductIngredient` | none, proposed, rejected | confirmed | explicit user decision; a previously confirmed row for the product becomes rejected in the same transaction, stored before the new confirmation; the row keeps its original `source` and `proposed_at` |
| `ConfirmProductIngredient` | confirmed (same ingredient) | unchanged | no-op, nothing is written |
| `RejectProductIngredient` | proposed, confirmed | rejected | rejecting a rejected row is an invalid transition |

### Application contract

`catalog` exposes semantically distinct operations instead of one resolver:

- `FindIngredientByName(name) -> Ingredient | None`: deterministic.
  `normalize_text`, then exact lookup on `IngredientName.normalized_name`. No
  fuzzy matching, no model and no side effects.
- `ListIngredientCandidates(product_id) -> list[Ingredient]`: explicitly
  heuristic preselection for the classifier and the UI.
- `GetConfirmedProductIngredients(household_id) -> mapping product_id -> ingredient_id`.
- `ProposeProductIngredient`, `ConfirmProductIngredient`, `RejectProductIngredient`.

The LLM sits behind a catalog-owned port that chooses at most one ingredient from
a candidate list for a product. It runs only from a bounded management command,
never inside a web worker.

### Consumers

- `recipes`: `RecipeIngredient` gains `ingredient` → `catalog.Ingredient`, null when
  the line could not be resolved, and keeps its original text for display. An
  unresolved line is an explicit state that never matches stock. External recipes
  resolve provider names with `FindIngredientByName` at read time and write nothing.
  A requirement is satisfied by stock of products whose confirmed ingredient equals
  the requirement's ingredient, followed by the existing unit and package conversion.
  No name heuristics on the request path.
- `inventory`: snapshots carry `product_id` only, without tag names.
- `shopping`: items resolve their variant when they are added, not while being read.
- `promotions`: builds search queries from product or ingredient names and owns no identity.

Each consumer defines its own port and DTO; the adapter maps from the catalog contract.

### Vocabulary curation

An administrator curates `Ingredient` and `IngredientName` in Django admin. An
explicit management command imports provider names as `IngredientNameCandidate`
rows (`reason = provider_import`). Accepting a candidate creates an ingredient or
adds an alias.

## Migration of existing data

Forward-only from households 0007. Schema moves use `SeparateDatabaseAndState`
so rows stay where they are, followed by table renames. The data migration is
deterministic and does not guess meaning:

| legacy data | rule | result |
|---|---|---|
| tag, lower case, no digits or brackets, not equal to a product name | trusted provider vocabulary | `Ingredient` + canonical `IngredientName(source=ania_gotuje)` |
| tag byte-equal to a product name | product pollution | `IngredientNameCandidate(reason=legacy_product_copy)` |
| any other tag | ambiguous | `IngredientNameCandidate(reason=legacy_ambiguous)` |
| link to a missing product | orphan | recorded in `LegacyProductTagReview(reason=orphan_product)` |
| link to a quarantined tag | cannot map | recorded in `LegacyProductTagReview(reason=quarantined_tag)` |
| the only `manual` + verified link of a product to a trusted tag | explicit past decision | `ProductIngredient(confirmed, source=legacy)` |
| several such links on one product | no single identity | all `proposed`, recorded for review |
| `ollama` + unverified link to a trusted tag | past model output | `ProductIngredient(proposed, source=model)` |
| `TagProposal` rows | table is empty | dropped; the migration fails if any row exists |

`LegacyProductTagReview` is read-only residue of this migration, visible in Django
admin, and is removed once reviewed.

Known bad data is not repaired by the migration. A separate, audited data-repair
command handles products #56 and #57, the confirmed link "Dżem morelowy" →
"dżem malinowy", non-ingredient provider tags ("dla dzieci") and duplicate
ingredients (a merge operation that moves names and links).

## Removed

`households/tag_analysis_jobs.py` and its endpoints, `_remember_ania_tags`,
matching in the shopping repository, the `Alias*` compatibility modules,
`TagProposal`, `ProductTag`, `IngredientTag`, and the tag branch of
`shared.name_matching`.

## Consequences

- Product identity has one owner. inventory, shopping and recipes no longer import
  `households.models`.
- Recipe matching becomes set membership by ingredient id and is testable without names.
- Right after the migration, fewer products match than before: links to polluted
  tags and products with several links wait for review. This is accepted over
  migrating guesses.
- Recipe lines that cannot be resolved are visible as such, which feeds curation.
- The frontend endpoints for tags and analysis jobs change and must be rebuilt
  after the backend.
