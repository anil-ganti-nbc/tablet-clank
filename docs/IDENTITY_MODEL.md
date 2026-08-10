# Identity model

The canonical identity is manufacturer + model number (preferred), otherwise manufacturer SKU, otherwise a conservative family/name fallback, combined with region, connectivity and RAM/storage when present. Region is evidence context, not automatically a separate product. Wi-Fi/cellular and materially different configurations are represented as variants through the identity dimensions; colour is retained but does not split identity in the current key.

Original source values are stored in JSON on each observation. Unknown values remain null. URL query strings and fragments are removed deterministically. This is intentionally conservative and should be audited with real regional examples before expanding the key.
