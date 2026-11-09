"""Synthetic accounts-payable ledger with planted control failures, so each test has a known answer."""
import random, datetime as dt, csv

APPROVAL_LIMIT = 10_000.00


def generate(path, n=5000, seed=11):
    rng = random.Random(seed)
    users = [f"u{i:02d}" for i in range(1, 13)]
    vendors = [f"V{i:03d}" for i in range(1, 121)]
    rows, inv = [], 1
    for _ in range(n):
        v = rng.choice(vendors)
        amt = round(min(rng.lognormvariate(6.2, 1.1), 9_500), 2)           # natural, Benford-like spread, under the limit
        d = dt.date(2025, 1, 1) + dt.timedelta(days=rng.randint(0, 364))
        while d.weekday() >= 5: d += dt.timedelta(days=1)                    # normal activity is on weekdays
        creator = rng.choice(users); approver = rng.choice([u for u in users if u != creator])
        rows.append([f"INV{inv:06d}", v, f"{v}-{rng.randint(1000,9999)}", amt, d.isoformat(), creator, approver]); inv += 1
    plant = {"duplicates": [], "sod": [], "split": [], "weekend": []}
    for _ in range(25):                                                      # duplicate payments (same vendor+amount+date, new invoice id)
        r = list(rng.choice(rows)); r[0] = f"INV{inv:06d}"; r[2] += "-D"; rows.append(r); plant["duplicates"].append(r[0]); inv += 1
    for _ in range(18):                                                      # segregation-of-duties breach: creator approves own entry
        r = list(rng.choice(rows)); r[0] = f"INV{inv:06d}"; r[2] = f"SOD-{inv}"; r[6] = r[5]; r[3] = round(rng.uniform(500, 9000), 2)
        rows.append(r); plant["sod"].append(r[0]); inv += 1
    for _ in range(10):                                                      # split purchases: three invoices just under the limit, same vendor and day
        v = rng.choice(vendors); d = dt.date(2025, rng.randint(1, 12), rng.randint(1, 27))
        while d.weekday() >= 5: d += dt.timedelta(days=1)
        u = rng.choice(users); ap = rng.choice([x for x in users if x != u])
        for _k in range(3):
            rows.append([f"INV{inv:06d}", v, f"SPL-{inv}", round(rng.uniform(9_300, 9_900), 2), d.isoformat(), u, ap]); plant["split"].append(f"INV{inv:06d}"); inv += 1
    for _ in range(14):                                                      # weekend postings
        r = list(rng.choice(rows)); d = dt.date.fromisoformat(r[4])
        d += dt.timedelta(days=(5 - d.weekday()) % 7 or 6)                   # move to next Saturday
        r[0] = f"INV{inv:06d}"; r[2] = f"WKD-{inv}"; r[4] = d.isoformat(); r[3] = round(rng.uniform(200, 9000), 2)
        rows.append(r); plant["weekend"].append(r[0]); inv += 1
    rng.shuffle(rows)
    with open(path, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["invoice_id", "vendor_id", "vendor_invoice_no", "amount", "post_date", "created_by", "approved_by"]); w.writerows(rows)
    return plant
