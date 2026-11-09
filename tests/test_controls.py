import pytest, pandas as pd
from openpyxl import load_workbook
from src import generate, tests_lib as T, report

@pytest.fixture(scope="module")
def data(tmp_path_factory):
    p = tmp_path_factory.mktemp("d") / "ap.csv"
    plant = generate.generate(str(p)); return T.load(str(p)), plant, p

def test_sod_finds_exactly_the_planted_breaches(data):
    df, plant, _ = data
    assert set(T.segregation_of_duties(df)) == set(plant["sod"])

def test_duplicates_catch_every_planted_duplicate(data):
    df, plant, _ = data
    found = set(T.duplicate_payments(df)); assert set(plant["duplicates"]) <= found
    assert len(found) <= 2 * len(plant["duplicates"]) + 6   # originals are also listed; few accidental matches

def test_split_purchases_catch_planted_groups(data):
    df, plant, _ = data
    assert set(plant["split"]) <= set(T.split_purchases(df))

def test_weekend_exact(data):
    df, plant, _ = data
    assert set(T.weekend_postings(df)) == set(plant["weekend"])

def test_benford_known_cases():
    natural = pd.DataFrame({"amount": [float(f"{10 ** (i / 997):.2f}") * 1000 for i in range(1, 997)]})   # log-uniform => Benford
    assert not T.benford(natural)["flag"]
    fabricated = pd.DataFrame({"amount": [5000.0 + i for i in range(1000)]})                              # all start with 5
    assert T.benford(fabricated)["flag"]

def test_sample_is_reproducible_and_covers_key_items(data):
    df, _, _ = data
    a, b = T.sample(df), T.sample(df)
    assert list(a["invoice_id"]) == list(b["invoice_id"])
    assert set(df[df["amount"] >= 5000]["invoice_id"]) <= set(a["invoice_id"])

def test_workbook_formulas_compute_and_match_python(data, tmp_path):
    df, _, _ = data
    out = tmp_path / "wp.xlsx"; res = report.build(df, str(out))
    wb = load_workbook(out)
    assert {"Summary", "Ledger", "Benford", "Sample", "C-01", "C-02", "C-03", "C-04"} <= set(wb.sheetnames)
    ws = wb["Summary"]
    assert ws["B2"].value.startswith("=COUNTA") and ws["D2"].value == "=B2/C2"       # live formulas, not pasted numbers
    assert wb["Ledger"].max_row - 1 == len(df)
    assert wb["C-02"].max_row - 1 == len(res["C-02 Segregation of duties"])
