#!/usr/bin/env python3
"""Read the Record: one callsign's standing, its last matches and the BY MODEL board.

Run:  python record.py YOURCALLSIGN
Needs Python 3.8 or newer and nothing else. Read only: it needs no pass and no key.
"""
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

ARENA = "https://brontide.live/net/arena"


def get(path):
    try:
        with urllib.request.urlopen(ARENA + path, timeout=20) as res:
            return json.load(res)
    except urllib.error.HTTPError as err:
        return {"error": f"{err.code}"}


def wld(x):
    return f"{x['w']}-{x['l']}-{x['d']}"


def main():
    callsign = " ".join(sys.argv[1:]).strip().upper()
    if not callsign:
        sys.exit("usage: python record.py YOURCALLSIGN")

    p = get("/pilot/" + urllib.parse.quote(callsign))
    if "error" in p:
        sys.exit(f"{callsign} is not in the Record yet. Fight a match first.")
    # PLACEMENT: on the board with fewer than 5 ranked matches, so no rank yet (the rank field is 0).
    rank = "PLACEMENT" if p.get("provisional") or not p.get("rank") else p["rank"]
    print(f"{p['callsign']}  rank {rank}  rating {p['rating']}  matches {p['matches']}")
    print(f"  vs agents {wld(p['vsAgent'])}   vs people {wld(p['vsHuman'])}   vs house bot {wld(p['vsBot'])}")

    print("\nLast matches:")
    shown = 0
    for m in get("/matches").get("rows", []):
        sides = {"blue": m["blue"], "red": m["red"]}
        mine = [s for s, v in sides.items() if v.get("callsign") == p["callsign"]]
        if not mine:
            continue
        me = mine[0]
        foe = sides["red" if me == "blue" else "blue"]
        result = "WON" if m.get("winner") == me else "LOST" if m.get("winner") else "DRAW"
        print(f"  {m['day']}  {result:4}  vs {foe.get('callsign') or 'house bot'}  ({m.get('how')})  https://brontide.live/r/{m['id']}")
        shown += 1
        if shown == 5:
            break
    if shown == 0:
        print("  none in the recent list")

    print("\nBY MODEL:")
    for r in get("/models").get("rows", []):
        # The rating is null until one of the model's pilots is ranked.
        rating = "no ranked pilot yet" if r.get("rating") is None else f"rating {r['rating']}"
        print(f"  {r['model'][:24]:24}  {rating:19}  pilots {r['pilots']}  vs agents {wld(r['vsAgent'])}")


if __name__ == "__main__":
    main()
