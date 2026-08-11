# Identity model

## Current rules

The current identity key is:

`manufacturer + (model_number OR SKU OR family/name fallback) + region + connectivity + RAM + storage`

Model number is preferred, then manufacturer SKU. The fallback is intentionally conservative and may merge products when a source exposes no stable identifier; those cases require audit before production use.

## Variant semantics

- Product family: retained in `family`; it does not alone define identity.
- Product/model: `model_number` is the preferred stable hardware identity.
- Regional variant: `region` is part of the current key, so the same model in different regions is currently represented separately. This is conservative and does not yet distinguish regional appearance from genuinely different hardware.
- Wi-Fi/cellular: `connectivity` is part of the key.
- RAM/storage: both are part of the key when known, allowing configuration-level observations.
- Colour: retained as evidence/product data but does not split the current identity key.
- Store SKU: retained as `sku` and used only when a model number is unavailable.

## Apple Store iPad Pro experimental rule

For the experimental Apple Store sources, the regional Apple `partNumber` (for example `MDWK4LL/A` or `MDWK4HN/A`) is used as the stable source identifier/model-number field. The base part number is retained as `sku`. It is treated as a sellable Store configuration identity, not a global hardware identity. Storage, display size and connectivity are parsed as configuration evidence; colour is retained but does not independently split identity unless Apple assigns a different part number.

Repeated carrier/unlocked URLs with the same regional part number are deduplicated at collection time, preferring the non-carrier representation. Regional part numbers are suitable as regional variant/observation identifiers, not yet as global canonical product identifiers. Direct Store-SKU to Apple `A####` mapping remains UNRESOLVED and is not inferred.

## Unresolved questions

An Apple Store identity introduced after an existing product with the same base SKU, manufacturer and region is a repair/reconciliation candidate, not automatically an editorial new-product event. The current pipeline records this narrow case as `identity_correction`; a genuinely new base SKU remains `new_product`.

Real-world cross-region examples have not yet been audited. Before source promotion, determine whether region should remain in identity or become an observation dimension, how marketing aliases map to model numbers, and whether RAM/storage should define a variant entity separate from the canonical product.

## Lenovo PSREF research mapping (not implemented)

The 2026-08-11 PSREF identity review found that a Lenovo product/family name such as `TB370FU` can contain many country-specific model codes such as `ZACH0239AU` and `ZACL0045IN`, with repeated machine-type prefixes (`ZACH`, `ZACL`) and separate `Region`, `Country/Region`, EAN/UPC/JAN, RAM, storage, connectivity, colour and announcement-date fields.

- Use the exact PSREF model/MTM-like code as the narrow source observation identifier.
- Retain product/family name as `family`/product evidence, not as the sole identity.
- Keep PSREF region and country fields in the regional identity context; do not infer that country suffixes or machine types are globally equivalent.
- Preserve processor, display, OS, RAM, storage, connectivity, colour, accessories, EAN/UPC/JAN, `Announce Date`, revision/last-modified metadata and withdrawn/current state as evidence.
- Existing identity fields can support a conservative regional/configuration probe. Global canonical Lenovo identity remains `UNRESOLVED` until a broader cross-region equivalence audit proves how model code, machine type and product name relate.

This is a research mapping only. No Lenovo source, schema, or identity-code behavior is implemented.

The offline fixture/parser contract now proves the safe subset: exact PSREF model codes remain unchanged (`ZACH0239AU`, `ZACL0045IN`, `ZACL0046IN`, `ZACW0028IN`); rows with unavailable identifiers remain null; WLAN and WWAN rows remain distinct through the existing connectivity dimension; and exact repeated rows are removed only within the fixture snapshot. No global Lenovo canonical identity is created.

The independent Legion Tab cross-check adds eight exact regional model codes and confirms that the existing conservative mapping remains defensible. It does not resolve global Lenovo identity. Live implementation is blocked by source retrieval reliability, not by an identity-model failure.

## Xiaomi Mi Mall research probe (not implemented)

The 2026-08-11 offline Mi Mall probe preserves numeric China commerce IDs as requested source observations only. Direct official page inspection showed `10050031` and `19509` currently resolve to unrelated home-appliance pages despite stale search results naming Pad 7 and Pad 8. Numeric `product_id` is therefore not yet proven stable enough for repeated observation identity. No variant/SKU/configuration ID was captured, and no RAM/storage/colour/connectivity composite is safe to synthesize. China regional identity remains separate and global canonical identity remains `UNRESOLVED`.

## Honor China catalogue probe (offline only)

The China catalogue/comparison fixtures prove that exact product slugs `honor-magicpad-3`, `honor-magicpad-2` and `honor-pad-v9` are deterministic regional discovery identities across both surfaces. They are stored as `Candidate.source_identifier` with region `CN`; family values are taken from explicit catalogue grouping evidence (`MagicPad` and `Pad V`). Slugs are not global canonical hardware identities. No automatic relationship to Honor regulatory model identifiers is implemented; that mapping remains `UNRESOLVED`.

The 2026-08-11 live stability audit found the exact Honor China product slugs for MagicPad3, MagicPad 2, Pad V9 and Pad 9 unchanged across three reads each of both the catalogue and comparison pages. These slugs are now stable enough for a controlled regional observation probe, but remain source/surface-specific identifiers. The audit did not resolve model-number mapping, configuration identity or China-to-global equivalence.

Honor is experimentally landed only with those regional slugs. The catalogue and comparison surfaces are separate evidence sources, while exact slug identity prevents duplicate canonical products for the same China observation. No global merge is inferred.

## TCL global catalogue identity

TCL’s global tablet catalogue exposes product-specific path slugs such as `tcl-tab-a1-plus` and `tcl-nxtpaper-11-gen-2`. These are suitable source observation identifiers with region `GLOBAL`; family remains product evidence and model/configuration identity is not fabricated when absent. Global canonical equivalence across regional TCL catalogues remains `UNRESOLVED`.
