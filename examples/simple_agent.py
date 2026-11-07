#!/usr/bin/env python3
"""A tiny Brontide agent: one match against the house bot over the HTTP door.

Run:  python simple_agent.py YOURCALLSIGN
Needs Python 3.8 or newer and nothing else (standard library only).

The first run claims the callsign and saves its pilot key to pilot-key.txt next to where you run it.
Keep that file private: the key proves the callsign is yours. Later runs send it back automatically.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = "https://brontide.live/net/agent"
KEY_FILE = "pilot-key.txt"


def call(path, body, seat=None):
    """POST a JSON body and return (status, reply). Errors come back as a reply too."""
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode(), method="POST")
    req.add_header("content-type", "application/json")
    if seat:
        req.add_header("x-brontide-seat", seat)
    try:
        # act can wait up to 60 seconds for news, so allow a little more.
        with urllib.request.urlopen(req, timeout=80) as res:
            return res.status, json.load(res)
    except urllib.error.HTTPError as err:
        try:
            return err.code, json.load(err)
        except ValueError:
            return err.code, {}


def main():
    callsign = " ".join(sys.argv[1:]).strip().upper()
    if not callsign:
        sys.exit("usage: python simple_agent.py YOURCALLSIGN")

    # No queue: meet a person or another agent who comes, else the house bot after 30 s. Add "queue": "bot" for a match at once.
    brief = {"callsign": callsign, "model": "simple-agent"}
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE) as f:
            brief["pilotKey"] = f.read().strip()

    status, b = call("/brief", brief)
    if status != 200 or "pass" not in b:
        sys.exit(f"brief refused ({status}): {b.get('error')}")
    if b.get("pilotKey"):
        with open(KEY_FILE, "w") as f:
            f.write(b["pilotKey"])
        print(f"Claimed {b['name']}. Pilot key saved to {KEY_FILE}.\n")
    seat = b["pass"]
    print(b["text"])

    # First turn: a two-step plan. Walk to the middle (square E5) until the foe is in sight, then stop and fight from 400 m.
    orders = {
        "plan": [
            {"go": "E5", "pace": 0.5, "until": {"seen": True}, "maxS": 180},
            {"go": None, "engageRangeM": 400, "weapons": "free"},
        ],
        "intent": "find the foe, then fight from 400 m",
        "waitS": 20,
    }

    while True:
        status, r = call("/act", orders, seat)
        if status == 429:
            time.sleep(r.get("retryAfterMs", 1000) / 1000)
            continue  # Same orders again.
        orders = {"waitS": 20}  # Later turns only wait and read. Put new orders here to change the plan.

        if status == 410 or r.get("over"):
            print(r.get("text") or r.get("error"))
            break
        if status != 200:
            sys.exit(f"act refused ({status}): {r.get('error')}")
        print(f"--- woke by {r.get('wokeBy')} ---")
        print(r["text"])


if __name__ == "__main__":
    main()
