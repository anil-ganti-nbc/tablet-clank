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

## Unresolved questions

Real-world cross-region examples have not yet been audited. Before source promotion, determine whether region should remain in identity or become an observation dimension, how marketing aliases map to model numbers, and whether RAM/storage should define a variant entity separate from the canonical product.
