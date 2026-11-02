#!/usr/bin/env python3
"""Check that a callsign really fought the match it names. Every tale in tales/ must pass this.

Run:  python tools/check_tale.py CALLSIGN MATCH
MATCH is a match id (32 letters and digits) or its page, https://brontide.live/r/<id>.
Needs Python 3.8 or newer and nothing else.
"""
import json
import re
import sys
import urllib.error
import urllib.request


def main():
    if len(sys.argv) < 3:
        sys.exit("usage: python tools/check_tale.py CALLSIGN MATCH")
    callsign = " ".join(sys.argv[1:-1]).strip().upper()
    found = re.search(r"[0-9a-f]{32}", sys.argv[-1].lower())
    if not found:
        sys.exit("NO: that is not a match id or a match page.")
    match_id = found.group(0)
    try:
        with urllib.request.urlopen(f"https://brontide.live/net/arena/match/{match_id}", timeout=20) as res:
            m = json.load(res)
    except urllib.error.HTTPError as err:
        sys.exit(f"NO: the Record has no match {match_id} ({err.code}).")
    pilots = [m[s].get("callsign") for s in ("blue", "red")]
    if callsign not in pilots:
        sys.exit(f"NO: {callsign} did not fight match {match_id}.")
    print(f"YES: {callsign} fought match {match_id} on {m['day']} ({m.get('how')}).")


if __name__ == "__main__":
    main()
