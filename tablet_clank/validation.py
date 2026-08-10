import re

TABLET_TERMS = ("tablet", "ipad", "galaxy tab", "tab ", "pad ", "pad 6", "pad 7")
EXCLUDED = ("phone", "iphone", "watch", "laptop", "notebook", "case", "keyboard", "stylus", "pencil", "charger", "cover", "support", "manual", "accessory")

def validate(candidate) -> tuple[bool, str | None]:
    text = f"{candidate.title} {candidate.url}".lower()
    if any(term in text for term in EXCLUDED): return False, "excluded_product_or_support_term"
    if not any(term in text for term in TABLET_TERMS): return False, "no_tablet_signal"
    if re.search(r"/support/|/help/|/manual", candidate.url.lower()): return False, "support_surface"
    return True, None
