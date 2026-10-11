"""Bounded, cited passages from the latest SEC annual filing."""
from __future__ import annotations

from dataclasses import dataclass
import re

from bs4 import BeautifulSoup


@dataclass(frozen=True)
class Passage:
    evidence_id: str
    heading: str
    text: str
    url: str
    accession: str


def annual_document(submissions: dict) -> tuple[str, str] | None:
    recent = submissions.get("filings", {}).get("recent", {})
    for form, accession, document in zip(recent.get("form", []),
                                         recent.get("accessionNumber", []),
                                         recent.get("primaryDocument", [])):
        if form in {"10-K", "20-F", "40-F"} and accession and document:
            cik = int(submissions["cik"])
            return (f"https://www.sec.gov/Archives/edgar/data/{cik}/"
                    f"{accession.replace('-', '')}/{document}", accession)
    return None


def extract_passages(html: str, url: str, accession: str) -> tuple[Passage, ...]:
    if len(html) > 25_000_000:
        raise ValueError("Filing document exceeds extraction limit")
    soup = BeautifulSoup(html, "html.parser")
    for node in soup(["script", "style", "header", "footer"]):
        node.decompose()
    text = re.sub(r"[ \t]+", " ", soup.get_text("\n", strip=True))
    text = re.sub(r"\n{3,}", "\n\n", text)
    if len(text) < 10_000:
        raise ValueError("Filing text is too short for reliable section extraction")
    # Anchor to filing section headings so references inside prose and table
    # of contents do not masquerade as the cited passage.
    body = text
    patterns = (
        ("MD&A", r"(?mi)^(?:item\s+7\.?\s+management.s\s+discussion\s+and\s+analysis|item\s+5\.?\s+operating\s+and\s+financial\s+review)[^\n]*$"),
        ("Risk factors", r"(?mi)^(?:item\s+1a\.?\s+)?risk\s+factors\s*$"),
        ("Debt note", r"(?mi)^note\s+\d+\s*[:.\-]?\s*(?:debt|borrowings|long.term debt|financing)[^\n]*$"),
    )
    passages = []
    # Standard tagged debt text blocks are stronger boundaries than a guessed
    # note heading. Preserve the actual inline element as a clickable anchor.
    for node in soup.find_all(lambda tag: tag.name and tag.name.lower().endswith('nonnumeric')):
        if node.get('name') in {'us-gaap:DebtDisclosureTextBlock', 'ifrs-full:DisclosureOfBorrowingsExplanatory'}:
            excerpt = re.sub(r'\s+', ' ', node.get_text(' ', strip=True))[:3200]
            if len(excerpt) >= 300:
                anchor = node.get('id', '')
                passages.append(Passage(f'{accession}:passage:debt-tag:{anchor}', 'Debt note', excerpt,
                                        url + (f'#{anchor}' if anchor else ''), accession))
                break
    for heading, pattern in patterns:
        if heading == 'Debt note' and any(p.heading == heading for p in passages):
            continue
        matches = list(re.finditer(pattern, body, re.IGNORECASE))
        # The first occurrence can be the table of contents; the last matching
        # standalone heading is the actual section in a standard annual filing.
        if not matches:
            continue
        match = matches[-1]
        excerpt = body[match.end():match.end() + 3200].strip()
        excerpt = re.sub(r"\s+", " ", excerpt)
        if len(excerpt) < 300:
            continue
        passages.append(Passage(f"{accession}:passage:{heading.lower().replace(' ', '-')}:"
                                f"{match.start()}", heading, excerpt, url, accession))
    return tuple(passages)
