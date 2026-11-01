#!/usr/bin/env python3
"""Split the template browser payload into lazily-loaded pieces.

The browser used to fetch the whole of `web/templates_data.json` (~3.2 MB) the
first time the template panel opened, before it could render a single card.
Nothing on that panel needs all 740 prompt bodies at once, so the payload is
generated into three layers instead:

  web/templates_index.json      category / subcategory tree + counts (~22 KB)
  web/templates/<category>.json full templates of one category (median 26 KB)
  web/templates_search.json     flat rows for keyword search (~330 KB, fetched
                                once, in the background, on first keystroke)

`web/templates_data.json` stays the single source of truth and is never
modified: it is the file to edit by hand. Run this script afterwards, then
commit the generated files together with it.

    python tools/split_templates.py            # regenerate
    python tools/split_templates.py --check    # exit 1 if out of date

The index records the sha256 of the source file it was built from, so --check
(and CI, if any) can tell a stale build from a fresh one.
"""

import argparse
import hashlib
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WEB = os.path.join(ROOT, "web")
SOURCE = os.path.join(WEB, "templates_data.json")
OUT_INDEX = os.path.join(WEB, "templates_index.json")
OUT_DIR = os.path.join(WEB, "templates")
OUT_SEARCH = os.path.join(WEB, "templates_search.json")

# Field order of a search row. Kept in the file so the JS does not hard-code
# magic indexes; adding a field here is backwards compatible as long as the JS
# looks names up through the `fields` array.
SEARCH_FIELDS = [
    "cat", "sub", "cat_zh", "cat_en", "sub_zh", "sub_en",
    "id", "name", "name_en", "desc", "desc_en", "tags", "tags_en",
]

SAFE_ID = re.compile(r"^[A-Za-z0-9_-]+$")


def die(msg):
    sys.stderr.write("error: %s\n" % msg)
    sys.exit(1)


def load_source():
    with io.open(SOURCE, encoding="utf-8") as f:
        return json.load(f)


def build(data):
    """Return (index, {catId: category_payload}, search_payload)."""
    cats = data.get("categories")
    if not isinstance(cats, list) or not cats:
        die("templates_data.json has no categories")

    index_cats = []
    payloads = {}
    rows = []
    total = 0

    for cat in cats:
        cid = cat.get("id")
        if not cid or not SAFE_ID.match(cid):
            die("category id is not filename-safe: %r" % (cid,))
        if cid in payloads:
            die("duplicate category id: %r" % (cid,))

        meta = {k: v for k, v in cat.items() if k != "subcategories"}
        sub_meta = []
        subs_payload = []

        for sub in cat.get("subcategories") or []:
            sid = sub.get("id")
            if not sid or not SAFE_ID.match(sid):
                die("subcategory id is not filename-safe in %s: %r" % (cid, sid))
            tpls = sub.get("templates") or []
            sm = {k: v for k, v in sub.items() if k != "templates"}
            sm["count"] = len(tpls)
            sub_meta.append(sm)
            subs_payload.append({"id": sid, "templates": tpls})
            total += len(tpls)
            for t in tpls:
                rows.append([
                    cid, sid,
                    cat.get("name", ""), cat.get("name_en", ""),
                    sub.get("name", ""), sub.get("name_en", ""),
                    t.get("id", ""), t.get("name", ""), t.get("name_en", ""),
                    t.get("description", ""), t.get("description_en", ""),
                    t.get("tags") or [], t.get("tags_en") or [],
                ])

        meta["subcategories"] = sub_meta
        index_cats.append(meta)
        payloads[cid] = {"id": cid, "subcategories": subs_payload}

    with io.open(SOURCE, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()

    index = {
        "version": data.get("version", "1.0.0"),
        "description": data.get("description", ""),
        "source": "templates_data.json",
        "source_sha256": digest,
        "count": total,
        "categories": index_cats,
    }
    search = {"count": len(rows), "fields": SEARCH_FIELDS, "rows": rows}
    return index, payloads, search, total


def dumps(obj, indent):
    return json.dumps(obj, ensure_ascii=False, indent=indent)


def write(path, text):
    parent = os.path.dirname(path)
    if not os.path.isdir(parent):
        os.makedirs(parent)
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def read(path):
    if not os.path.exists(path):
        return None
    with io.open(path, encoding="utf-8", newline="") as f:
        return f.read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="do not write; exit 1 if the generated files are stale")
    args = ap.parse_args()

    if not os.path.exists(SOURCE):
        die("missing %s" % SOURCE)

    index, payloads, search, total = build(load_source())

    outputs = [(OUT_INDEX, dumps(index, 1))]
    for cid in sorted(payloads):
        outputs.append((os.path.join(OUT_DIR, cid + ".json"), dumps(payloads[cid], 1)))
    outputs.append((OUT_SEARCH, dumps(search, None)))

    stale = [p for p, text in outputs if read(p) != text]
    orphans = []
    if os.path.isdir(OUT_DIR):
        keep = {os.path.basename(p) for p, _ in outputs if p.startswith(OUT_DIR)}
        orphans = [f for f in sorted(os.listdir(OUT_DIR)) if f not in keep]

    if args.check:
        if stale or orphans:
            for p in stale:
                sys.stderr.write("stale: %s\n" % os.path.relpath(p, ROOT))
            for f in orphans:
                sys.stderr.write("orphan: templates/%s\n" % f)
            sys.exit(1)
        sys.stdout.write("up to date: %d categories, %d templates\n" % (len(payloads), total))
        return

    changed = 0
    for path, text in outputs:
        if read(path) != text:
            write(path, text)
            changed += 1

    for f in orphans:
        os.remove(os.path.join(OUT_DIR, f))
        sys.stdout.write("removed orphan templates/%s\n" % f)

    print("wrote %d/%d files (%d changed)" % (len(outputs), len(outputs), changed))
    print("  index   %6.1f KB" % (len(outputs[0][1]) / 1024.0))
    print("  search  %6.1f KB" % (len(outputs[-1][1]) / 1024.0))
    per = sorted(((len(t) / 1024.0, os.path.basename(p)) for p, t in outputs[1:-1]), reverse=True)
    print("  categories: %d files, median %.1f KB, largest %s %.1f KB"
          % (len(per), per[len(per) // 2][0], per[0][1], per[0][0]))
    print("  templates: %d" % total)


if __name__ == "__main__":
    main()
