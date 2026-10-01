# JASS Khewat Share Calculator v1.1

## Owner + Ratio copy workflow

The application supports both directions of the Owner + Share Ratio workflow.

### Import from the Jamabandi webpage
1. Copy the webpage rows.
2. Click **Paste Owner + Ratio**.
3. The app keeps only **Owner Full Name** and **Share Ratio**.
4. Other columns are ignored.

### Copy data from the project
- **Copy Selected** — copies selected Owner + Ratio rows.
- **Copy All Owner + Ratio** — copies the complete list.
- The copied format is tab-separated and can be pasted into another JASS
  project, Excel/LibreOffice, or the application's import function.

Example:

```text
OWNER FULL NAME    SHARE RATIO
अजय सिंह पुत्र ...    2/297
अमरीदीप सिंह ...     7/198
```

## Calculation
1 Kanal = 20 Marla  
1 Marla = 9 Sarshai  
1 Kanal = 180 Sarshai

`Owner Share = Total Khewat Area × (Numerator / Denominator)`

Results are displayed as integer Kanal-Marla-Sarshai with no decimals.

## Run

```bash
pip install PySide6
python JASS_Khewat_Share_Calculator.py
```
