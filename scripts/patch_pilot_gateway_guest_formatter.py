"""Write a fail-closed candidate that fixes the legacy guest-result formatter.

The gateway already stores the representative source image server-side and exposes
it only through its same-origin image endpoint.  A legacy formatter used by the
guest polling route was replacing that safe path with ``None`` and regenerating
offer identifiers.  This helper changes only those serialization rules; it
never installs the candidate itself.
"""
from __future__ import annotations

import sys
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise SystemExit(f"REFUSED_{label}: expected one exact source marker")
    return text.replace(old, new, 1)
def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_pilot_gateway_guest_formatter.py /path/to/pilot_gateway.py")

    source = Path(sys.argv[1])
    text = source.read_text(encoding="utf-8").replace("\r\n", "\n")

    text = replace_once(
        text,
        "'public_offer_id':job_id[:8]+'-'+str(i),",
        "'public_offer_id':txt(o.get('public_offer_id'),64) or ('GTO-'+job_id[:8].upper()+'-'+str(i)),",
        "public-offer-id",
    )
    text = replace_once(
        text,
        "offers.append({k:v for k,v in q.items() if v})",
        "offers.append({k:v for k,v in q.items() if v and k != 'item'})",
        "offer-allowlist",
    )
    image_marker = next(
        (line for line in text.splitlines()
         if "if not isinstance(image,str)" in line and "startswith('https://')" in line),
        "",
    )
    if not image_marker:
        raise SystemExit("REFUSED_protected-image-path: source marker missing")
    image_indent = image_marker[:len(image_marker) - len(image_marker.lstrip())]
    text = replace_once(
        text,
        image_marker,
        f"{image_indent}# Customer JSON may use only our protected, same-origin image route.\n"
        f"{image_indent}if not isinstance(image,str) or not image.startswith('/api/v1/guest/research/') or not image.endswith('/image'):image=None\n"
        f"{image_indent}if image: product['image']=image",
        "protected-image-path",
    )

    candidate = source.with_name(source.name + ".guest-formatter.new")
    candidate.write_text(text, encoding="utf-8")
    print(f"CANDIDATE_WRITTEN={candidate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
