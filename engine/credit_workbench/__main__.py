"""Developer entry point. Fetches real raw SEC data; it does not claim full analysis."""
import argparse
import json
import os
from pathlib import Path

from .sec import SECClient, SECError


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    search = commands.add_parser("search", help="Search the SEC company index")
    search.add_argument("query")
    fetch = commands.add_parser("fetch", help="Download raw facts and filing metadata by CIK")
    fetch.add_argument("cik")
    args = parser.parse_args()
    try:
        client = SECClient(os.environ.get("SEC_USER_AGENT", ""))
        if args.command == "search":
            print(json.dumps(client.search(args.query), indent=2))
        else:
            cik = client._cik(args.cik)
            payload = {"submissions": client.submissions(cik), "companyfacts": client.company_facts(cik)}
            destination = Path(".cache/raw") / f"CIK{cik}.json"
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps(payload))
            print(f"Saved raw SEC data to {destination}; normalization has not run.")
    except (ValueError, SECError) as exc:
        parser.exit(2, str(exc) + "\n")


if __name__ == "__main__":
    main()
