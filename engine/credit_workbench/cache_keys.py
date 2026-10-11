"""Pure content addressing; persistent cache storage is a subsequent integration."""
from __future__ import annotations

import hashlib
import json


def analysis_key(*, cik: str, accessions: list[str], normalized_data: dict,
                 disclosure_hash: str, extractor_version: str, methodology_version: str,
                 prompt_version: str, model: str) -> str:
    if not cik.isdigit() or not accessions or not all((disclosure_hash, extractor_version,
                                                     methodology_version, prompt_version, model)):
        raise ValueError("Cache identity requires filings, content and all transformation versions")
    payload = {
        "cik": cik.zfill(10), "accessions": sorted(set(accessions)),
        "data": normalized_data, "disclosures": disclosure_hash,
        "extractor": extractor_version, "methodology": methodology_version,
        "prompt": prompt_version, "model": model,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()
