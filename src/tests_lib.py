"""Control tests. Each returns a list of exception invoice ids (or a stats dict) so results are auditable and reproducible."""
import math, random, datetime as dt
import pandas as pd

APPROVAL_LIMIT = 10_000.00


def load(path):
    df = pd.read_csv(path, parse_dates=["post_date"]); df["amount"] = df["amount"].astype(float); return df


def duplicate_payments(df):
    """C-01: same vendor, same amount, same posting date, different invoice id."""
    g = df.groupby(["vendor_id", "amount", "post_date"])["invoice_id"]
    return sorted(df[g.transform("count") > 1]["invoice_id"])


def segregation_of_duties(df):
    """C-02: the person who created an entry must not approve it."""
    return sorted(df[df["created_by"] == df["approved_by"]]["invoice_id"])


def split_purchases(df, limit=APPROVAL_LIMIT, band=0.10, min_count=2):
    """C-03: several invoices from one vendor on one day, each just under the approval limit but together over it."""
    near = df[(df["amount"] < limit) & (df["amount"] >= limit * (1 - band))]
    g = near.groupby(["vendor_id", "post_date"])
    hit = g["amount"].transform(lambda s: len(s) >= min_count and s.sum() >= limit)
    return sorted(near[hit]["invoice_id"])


def weekend_postings(df):
    """C-04: postings on Saturday/Sunday."""
    return sorted(df[df["post_date"].dt.weekday >= 5]["invoice_id"])


BENFORD = {d: math.log10(1 + 1 / d) for d in range(1, 10)}


def benford(df):
    """C-05: first-digit distribution vs Benford's law. Returns observed shares, expected shares, chi-square (8 dof; 15.51 is the 5% critical value)."""
    first = df["amount"].apply(lambda x: int(str(f"{x:.2f}").lstrip("0.")[0]))
    n = len(first); obs = {d: (first == d).sum() for d in range(1, 10)}
    chi = sum((obs[d] - n * BENFORD[d]) ** 2 / (n * BENFORD[d]) for d in range(1, 10))
    return {"n": n, "observed": {d: obs[d] / n for d in obs}, "expected": BENFORD, "chi_square": chi, "critical_5pct": 15.51, "flag": chi > 15.51}


def sample(df, size=60, seed=2025, stratify_over=5000.0):
    """Reproducible audit sample: every item at/over the threshold (key items) plus a random sample of the remainder."""
    key = df[df["amount"] >= stratify_over]
    rest = df[df["amount"] < stratify_over]
    pick = rest.sample(n=min(size, len(rest)), random_state=seed)
    return pd.concat([key.assign(basis="key item"), pick.assign(basis="random")]).sort_values("invoice_id")


def run_all(df):
    res = {"C-01 Duplicate payments": duplicate_payments(df), "C-02 Segregation of duties": segregation_of_duties(df),
           "C-03 Split purchases": split_purchases(df), "C-04 Weekend postings": weekend_postings(df)}
    return res
