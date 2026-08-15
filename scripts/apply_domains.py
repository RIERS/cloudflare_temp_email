#!/usr/bin/env python3
"""Overwrite DOMAINS / DEFAULT_DOMAINS / RANDOM_SUBDOMAIN_DOMAINS in wrangler.toml
from a JSON source of truth (domains.json). Keeps every other line intact.

Usage: python3 apply_domains.py <wrangler.toml> <domains.json>
"""
import json
import re
import sys


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    toml_path, json_path = sys.argv[1], sys.argv[2]

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    keys = ["DOMAINS", "DEFAULT_DOMAINS", "RANDOM_SUBDOMAIN_DOMAINS"]
    values = {k: data[k] for k in keys}
    for k in keys:
        if not isinstance(values[k], list) or not values[k]:
            print("error: %s must be a non-empty array" % k, file=sys.stderr)
            return 1

    with open(toml_path, encoding="utf-8") as f:
        text = f.read()

    def fmt(key: str) -> str:
        return "%s = [%s]" % (key, ", ".join('"%s"' % d for d in values[key]))

    new_text, _ = re.subn(
        r"^[ \t]*(DOMAINS|DEFAULT_DOMAINS|RANDOM_SUBDOMAIN_DOMAINS)[ \t]*=[ \t]*\[[^\]]*\][ \t]*$",
        lambda m: fmt(m.group(1)),
        text,
        flags=re.M,
    )

    missing = [k for k in keys if not re.search(r"^[ \t]*%s[ \t]*=" % re.escape(k), new_text, flags=re.M)]
    if missing:
        m = re.search(r"^\[vars\][ \t]*$", new_text, flags=re.M)
        if not m:
            print("error: no [vars] section found in %s" % toml_path, file=sys.stderr)
            return 1
        insert = "\n" + "\n".join(fmt(k) for k in missing)
        new_text = new_text[: m.end()] + insert + new_text[m.end():]

    with open(toml_path, "w", encoding="utf-8") as f:
        f.write(new_text)

    print("applied: " + ", ".join("%s=%d" % (k, len(values[k])) for k in keys))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
