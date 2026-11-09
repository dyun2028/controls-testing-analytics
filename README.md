# Controls Testing Analytics

Python tools that run internal-control tests over an accounts-payable ledger and write an Excel audit workpaper
with live formulas. Built as a study project on a **synthetic** ledger (5,087 invoices) with known planted control failures,
so every test has a verifiable expected answer. Not based on any real company data.

## Control tests
| ID | Test | Result on the synthetic ledger |
|---|---|---|
| C-01 | Duplicate payments (same vendor, amount, date; different invoice id) | all 25 planted duplicates caught (50 rows listed with their originals) |
| C-02 | Segregation of duties (creator = approver) | exactly the 18 planted breaches |
| C-03 | Split purchases just under the $10,000 approval limit | all 30 planted invoices (10 groups of 3) caught |
| C-04 | Weekend postings | exactly the 14 planted |
| C-05 | Benford's law first-digit analysis (chi-square vs 15.51 critical value) | not flagged on the natural data; flags fabricated data in a unit test |

Plus a reproducible audit sample: every key item at or above $5,000 plus a seeded random sample of the rest.

## Workpaper (`data/workpaper.xlsx`)
Summary sheet uses formulas (`COUNTA`, `SUM`, exception rate, nested `IF` risk rating), one sheet per control test,
the full ledger, a Benford sheet with the chi-square computed in-sheet, and the sample. Formulas were recalculated in LibreOffice to confirm they evaluate.

## Run
```
pip install pandas openpyxl pytest
python -m pytest -q     # 7 tests
python -c "from src import generate, tests_lib as T, report; generate.generate('data/ap.csv'); report.build(T.load('data/ap.csv'),'data/workpaper.xlsx')"
```
