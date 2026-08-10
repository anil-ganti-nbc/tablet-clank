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
