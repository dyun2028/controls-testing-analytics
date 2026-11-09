"""Write the audit workpaper as an Excel workbook: live formulas for the summary, one sheet per exception list."""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from . import tests_lib as T

HDR = PatternFill("solid", fgColor="DDE3EC")


def _sheet(wb, name, df, cols):
    ws = wb.create_sheet(name)
    ws.append(cols)
    for c in ws[1]: c.font = Font(bold=True); c.fill = HDR
    for r in df[cols].itertuples(index=False):
        ws.append([v.date() if hasattr(v, "date") else v for v in r])
    for i, c in enumerate(cols, 1): ws.column_dimensions[get_column_letter(i)].width = 20
    ws.freeze_panes = "A2"
    return ws


def build(df, path):
    wb = Workbook(); ws = wb.active; ws.title = "Summary"
    results = T.run_all(df)
    cols = ["invoice_id", "vendor_id", "vendor_invoice_no", "amount", "post_date", "created_by", "approved_by"]
    _sheet(wb, "Ledger", df, cols)
    ws.append(["Control test", "Exceptions", "Population", "Exception rate", "Amount at issue", "Risk rating"])
    for c in ws[1]: c.font = Font(bold=True); c.fill = HDR
    n_ledger = len(df) + 1
    for i, (name, ids) in enumerate(results.items(), start=2):
        sh = _sheet(wb, name[:4], df[df["invoice_id"].isin(ids)], cols)
        r = ws.max_row + 1
        ws.cell(r, 1, name)
        ws.cell(r, 2, f"=COUNTA('{sh.title}'!A2:A{max(sh.max_row,2)})-IF('{sh.title}'!A2=\"\",1,0)")
        ws.cell(r, 3, f"=COUNTA(Ledger!A2:A{n_ledger})")
        ws.cell(r, 4, f"=B{r}/C{r}"); ws.cell(r, 4).number_format = "0.00%"
        ws.cell(r, 5, f"=SUM('{sh.title}'!D2:D{max(sh.max_row,2)})"); ws.cell(r, 5).number_format = '#,##0.00'
        ws.cell(r, 6, f'=IF(D{r}>=0.01,"High",IF(D{r}>=0.003,"Medium","Low"))')
    b = T.benford(df); bs = wb.create_sheet("Benford")
    bs.append(["First digit", "Observed", "Expected", "Chi-square term"]); [setattr(c, "font", Font(bold=True)) for c in bs[1]]
    for d in range(1, 10):
        r = d + 1; bs.append([d, b["observed"][d], b["expected"][d], f"=({len(df)}*(B{r}-C{r})^2)/C{r}"])
        bs.cell(r, 2).number_format = bs.cell(r, 3).number_format = "0.0%"
    bs.append(["Total chi-square", "", "", "=SUM(D2:D10)"]); bs.append(["5% critical value (8 dof)", "", "", 15.51])
    bs.append(["Result", "", "", '=IF(D11>D12,"Departs from Benford","Consistent with Benford")'])
    smp = T.sample(df); _sheet(wb, "Sample", smp, cols + ["basis"])
    ws.column_dimensions["A"].width = 30
    for L in "BCDEF": ws.column_dimensions[L].width = 16
    wb.save(path)
    return results
