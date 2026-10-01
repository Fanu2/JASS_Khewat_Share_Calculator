# -*- coding: utf-8 -*-
"""
JASS Khewat Share Calculator
PySide6 desktop application for calculating each owner's land share
from a Khewat share ratio and a user-entered total area.

Land units used:
    1 Kanal = 20 Marla
    1 Marla = 9 Sarshai
    1 Kanal = 180 Sarshai

The application intentionally uses only:
    Owner Full Name
    Share Ratio

Jamabandi period, ownership type and the source table's displayed total
area are not used for calculation.
"""

import csv
import json
import re
import sys
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QSpinBox, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFileDialog, QFrame, QCheckBox, QSplitter,
    QAbstractItemView, QToolButton
)


APP_TITLE = "JASS Khewat Share Calculator"
SARSHARI_PER_MARLA = 9
MARLA_PER_KANAL = 20
SARSHARI_PER_KANAL = 180


# Sample owner/ratio pairs transcribed from the supplied screenshots.
# The app does not use any other columns from the source webpage.
SAMPLE_ROWS = [
    ("अमरदीप सिंह पुत्र सुखपाल सिंह पुत्र गुरबचन सिंह", "589/92784"),
    ("कुलदीप सिंह पुत्र सुखदेव सिंह पुत्र गुरबचन सिंह", "5/3806"),
    ("गुरदीप सिंह पुत्र बलदेव सिंह पुत्र जोगिंदर सिंह", "919/34254"),
    ("गुरमीत कौर पत्नी जसवीर सिंह पुत्र मोहन सिंह", "21/7612"),
    ("गुरमीत सिंह पुत्र गुरचरन सिंह पुत्र गुरबचन सिंह", "5/3806"),
    ("गुरमीत सिंह पुत्र सुखदेव सिंह पुत्र जोगिंदर सिंह", "2577/15464"),
    ("गोरा कुमार पुत्र सुखराज राज पुत्र बलविंदर सिंह", "1625/309280"),
    ("जसवीर सिंह पुत्र अमरदेव सिंह पुत्र मोहन सिंह पुत्र जोगिंदर सिंह", "646/1993"),
    ("जगा सिंह पुत्र भूरा सिंह पुत्र हाकम सिंह पुत्र केहर सिंह", "25/3806"),
    ("जगा सिंह पुत्र भूरा सिंह पुत्र हाकम सिंह पुत्र केहर सिंह", "25/3806"),

    ("जसकीरत सिंह पुत्र बलजिंदर सिंह पुत्र सतपाल सिंह", "391/23196"),
    ("जसपाल कौर पत्नी भोला सिंह पुत्र हरनाम सिंह", "17/3806"),
    ("जसवीर कौर पत्नी रमा सिंह पुत्र गुरबचन सिंह", "20/1903"),
    ("जसवीर सिंह पुत्र गुरबचन सिंह पुत्र गुरबचन सिंह", "9662/1.00323e+006"),
    ("जसवीर सिंह पुत्र सुखदेव सिंह पुत्र जोगिंदर सिंह", "153129/2.9428e+007"),
    ("तेज कौर विधवा बलदेव सिंह पुत्र जोगिंदर सिंह", "2.94057e+007/1.05941e+009"),
    ("भमजीत कौर पत्नी गुरमीत सिंह पुत्र सुखदेव सिंह", "40/7612"),
    ("परमजीत कौर पत्नी बलवीर सिंह पुत्र जसवंत सिंह", "27/3806"),
    ("परमजीत कौर विधवा सुखदेव सिंह पुत्र सुखदेव सिंह", "633/92784"),
    ("परमजीत सिंह पुत्र सुखदेव सिंह पुत्र जोगिंदर सिंह", "2577/15464"),

    ("भोला सिंह पुत्र हंसराज सिंह पुत्र बलदेव सिंह", "3/3806"),
    ("भोला सिंह पुत्र हंसराज सिंह पुत्र बलदेव सिंह", "5/3806"),
    ("मनजीत कौर पत्नी भोला सिंह पुत्र हंसराज", "160967/3.35054e+006"),
    ("मनजीत कौर पत्नी भोला सिंह पुत्र हंसराज", "10/1903"),
    ("मनजीत सिंह पुत्र हंसराज सिंह पुत्र सुखदेव सिंह", "211/30928"),
    ("रणजीत सिंह पुत्र हंसराज सिंह पुत्र सुखदेव सिंह", "633/92784"),
    ("वीरपाल कौर पत्नी मनजीत सिंह पुत्र सुखदेव सिंह", "10/1903"),
    ("सुखपाल सिंह पुत्र गुरबचन सिंह पुत्र गुरबचन सिंह", "5/692"),
    ("सुखविंदर कौर पत्नी जोगिंदर सिंह पुत्र बलवन सिंह", "325/61856"),
    ("सुखविंदर कौर पत्नी हरनाम सिंह पुत्र हाकम सिंह", "10/1903"),

    ("सतनाम कौर पत्नी मैंगल सिंह पुत्र जंगीर सिंह", "61/7732"),
    ("सुरजीत शर्मा पुत्र लखवीर चन्द पुत्र हंसराज सिंह", "975/309280"),
    ("सुमनलता पत्नी गणनदीप शर्मा पुत्र गणनदीप", "65/30928"),
]


def decimal_fraction(value: str) -> Fraction:
    """Parse an integer/decimal/scientific-notation string exactly."""
    value = value.strip().replace(",", "")
    if not value:
        raise ValueError("empty number")
    try:
        return Fraction(Decimal(value))
    except (InvalidOperation, ValueError, ZeroDivisionError) as exc:
        raise ValueError(f"invalid number: {value}") from exc


def parse_ratio(text: str) -> Fraction:
    """Parse ratios such as 589/92784 or 9662/1.00323e+006."""
    text = text.strip().replace(" ", "")
    if "/" not in text:
        raise ValueError("ratio must be written as numerator/denominator")
    left, right = text.split("/", 1)
    a = decimal_fraction(left)
    b = decimal_fraction(right)
    if b == 0:
        raise ValueError("denominator cannot be zero")
    return a / b


def round_fraction_half_up(value: Fraction) -> int:
    """Positive Fraction -> nearest integer, with .5 rounded upward."""
    if value < 0:
        return -round_fraction_half_up(-value)
    return (2 * value.numerator + value.denominator) // (2 * value.denominator)


def area_to_text(sarshai: int) -> str:
    """Format integer Sarshai as Kanal-Marla-Sarshai with no decimals."""
    sarshai = max(0, int(sarshai))
    kanal, rem = divmod(sarshai, SARSHARI_PER_KANAL)
    marla, sar = divmod(rem, SARSHARI_PER_MARLA)
    return f"{kanal} K - {marla} M - {sar} S"


def parse_area_from_text(text: str):
    """Optional helper for pasted/imported total area like 12-8."""
    m = re.fullmatch(r"\s*(\d+)\s*[-:]\s*(\d+)\s*", text or "")
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def extract_ratio(token: str):
    """Return a ratio-looking token from arbitrary cell text."""
    token = token.strip()
    # Allow spaces and scientific notation in either side.
    pattern = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[-+]?\d+)?\s*/\s*[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[-+]?\d+)?"
    m = re.search(pattern, token, re.I)
    return m.group(0) if m else None


def parse_clipboard_rows(text: str):
    """
    Pick only owner name + ratio from copied webpage rows.

    Works with tab-separated rows, pipe-separated rows, or whitespace-ish
    pasted text. The first ratio-looking cell is treated as the share ratio;
    the longest non-numeric text before it is treated as the owner name.
    """
    result = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        cells = [c.strip() for c in re.split(r"\t|\|", line) if c.strip()]
        ratio = None
        ratio_index = -1
        for i, cell in enumerate(cells):
            r = extract_ratio(cell)
            if r:
                ratio, ratio_index = r, i
                break
        if not ratio:
            r = extract_ratio(line)
            if r:
                ratio = r
                before = line[:line.lower().find(r.lower())].strip()
                owner = before
                owner = re.sub(r"^\d{4}[-–]\d{4}\s*", "", owner)
            else:
                continue
        else:
            candidates = []
            for c in cells[:ratio_index]:
                if re.search(r"[A-Za-z\u0900-\u097F]", c):
                    if not re.fullmatch(r"\d{4}[-–]\d{4}", c):
                        candidates.append(c)
            owner = max(candidates, key=len) if candidates else ""
        if owner and owner.lower() not in {"owner full name", "share ratio"}:
            result.append((owner, ratio))
    return result


class KhewatShareCalculator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1280, 820)
        self.setMinimumSize(980, 680)
        self.rows = []
        self.build_ui()
        self.load_sample_rows()

    # ---------- UI ----------
    def build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        main = QVBoxLayout(root)
        main.setContentsMargins(18, 16, 18, 18)
        main.setSpacing(12)

        title = QLabel("JASS KHEWAT SHARE CALCULATOR")
        title.setObjectName("title")
        subtitle = QLabel(
            "Calculate each owner's share from the Khewat total area and the recorded share ratio"
        )
        subtitle.setObjectName("subtitle")
        main.addWidget(title)
        main.addWidget(subtitle)

        details = QFrame()
        details.setObjectName("details")
        grid = QGridLayout(details)
        grid.setContentsMargins(16, 12, 16, 12)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(8)

        self.village = QLineEdit()
        self.village.setPlaceholderText("e.g. Village name")
        self.year = QLineEdit()
        self.year.setPlaceholderText("e.g. 2023-2024")

        self.kanal = QSpinBox()
        self.kanal.setRange(0, 10_000_000)
        self.kanal.setSuffix(" K")
        self.marla = QSpinBox()
        self.marla.setRange(0, 19)
        self.marla.setSuffix(" M")

        grid.addWidget(QLabel("Village Name"), 0, 0)
        grid.addWidget(self.village, 0, 1)
        grid.addWidget(QLabel("Jamabandi Year"), 0, 2)
        grid.addWidget(self.year, 0, 3)
        grid.addWidget(QLabel("Total Area"), 1, 0)
        area_box = QHBoxLayout()
        area_box.setContentsMargins(0, 0, 0, 0)
        area_box.addWidget(self.kanal)
        area_box.addWidget(self.marla)
        area_box.addStretch()
        grid.addLayout(area_box, 1, 1)
        self.total_label = QLabel("0 K - 0 M - 0 S")
        self.total_label.setObjectName("totalArea")
        grid.addWidget(QLabel("Total in K-M-S"), 1, 2)
        grid.addWidget(self.total_label, 1, 3)

        main.addWidget(details)

        cards = QHBoxLayout()
        self.card_owners = self.make_card("OWNERS", "0")
        self.card_total = self.make_card("INPUT AREA", "0 K - 0 M - 0 S")
        self.card_alloc = self.make_card("CALCULATED", "0 K - 0 M - 0 S")
        self.card_diff = self.make_card("DIFFERENCE", "0 S")
        for card in (self.card_owners, self.card_total, self.card_alloc, self.card_diff):
            cards.addWidget(card)
        main.addLayout(cards)

        toolbar = QHBoxLayout()
        buttons = [
            ("＋ Add Owner", self.add_row),
            ("− Remove Selected", self.remove_selected),
            ("⧉ Paste Owner + Ratio", self.paste_rows),
            ("⧷ Copy Selected", lambda: self.copy_owner_ratio(True)),
            ("⧷ Copy All Owner + Ratio", lambda: self.copy_owner_ratio(False)),
            ("↺ Sample Rows", self.load_sample_rows),
            ("✓ Calculate", self.calculate),
            ("⇩ Export CSV", self.export_csv),
            ("Save Project", self.save_project),
            ("Open Project", self.open_project),
        ]
        for text, slot in buttons:
            b = QPushButton(text)
            b.clicked.connect(slot)
            toolbar.addWidget(b)
        toolbar.addStretch()

        self.round_check = QCheckBox("Round to nearest Sarshai")
        self.round_check.setChecked(True)
        self.round_check.stateChanged.connect(lambda _: self.calculate())
        toolbar.addWidget(self.round_check)
        main.addLayout(toolbar)

        hint = QLabel(
            "Browser → copy table rows → click Paste Owner + Ratio. "
            "Use Copy Selected or Copy All Owner + Ratio to copy clean Owner + Ratio data "
            "for another project or spreadsheet."
        )
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        main.addWidget(hint)

        splitter = QSplitter(Qt.Vertical)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(
            ["#", "OWNER FULL NAME", "SHARE RATIO", "CALCULATED SHARE (K-M-S)"]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(False)
        self.table.setEditTriggers(
            QAbstractItemView.DoubleClicked |
            QAbstractItemView.EditKeyPressed |
            QAbstractItemView.SelectedClicked
        )
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        splitter.addWidget(self.table)

        notes = QLabel(
            "Unit conversion: 1 Kanal = 20 Marla; 1 Marla = 9 Sarshai. "
            "Calculated share = Total Khewat area × (Numerator ÷ Denominator)."
        )
        notes.setObjectName("notes")
        notes.setWordWrap(True)
        splitter.addWidget(notes)
        splitter.setSizes([620, 45])
        main.addWidget(splitter, 1)

        self.kanal.valueChanged.connect(self.calculate)
        self.marla.valueChanged.connect(self.calculate)

        self.create_menu()
        self.apply_style()

    def make_card(self, label, value):
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 10, 14, 10)
        l = QLabel(label)
        l.setObjectName("cardLabel")
        v = QLabel(value)
        v.setObjectName("cardValue")
        v.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(l)
        layout.addWidget(v)
        frame.value_label = v
        return frame

    def create_menu(self):
        menu = self.menuBar().addMenu("File")
        save = QAction("Save Project", self)
        save.setShortcut(QKeySequence.Save)
        save.triggered.connect(self.save_project)
        menu.addAction(save)

        open_ = QAction("Open Project", self)
        open_.setShortcut(QKeySequence.Open)
        open_.triggered.connect(self.open_project)
        menu.addAction(open_)

        menu.addSeparator()
        export = QAction("Export CSV", self)
        export.triggered.connect(self.export_csv)
        menu.addAction(export)

        menu.addSeparator()
        quit_ = QAction("Exit", self)
        quit_.triggered.connect(self.close)
        menu.addAction(quit_)

    def apply_style(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background: #f4f7fb;
                color: #172033;
                font-family: "Nirmala UI", "Noto Sans Devanagari", "Segoe UI";
                font-size: 13px;
            }
            QMenuBar {
                background: #14264f;
                color: white;
                padding: 5px;
            }
            QMenuBar::item:selected, QMenu::item:selected {
                background: #28477f;
            }
            QMenu {
                background: white;
                color: #172033;
            }
            #title {
                color: #14264f;
                font-size: 25px;
                font-weight: 800;
                letter-spacing: 1px;
            }
            #subtitle {
                color: #63708a;
                font-size: 13px;
                padding-bottom: 2px;
            }
            #details {
                background: white;
                border: 1px solid #d9e1ef;
                border-radius: 12px;
            }
            QLineEdit, QSpinBox {
                background: #fbfcff;
                border: 1px solid #cbd5e5;
                border-radius: 7px;
                padding: 7px 9px;
                min-height: 30px;
            }
            QLineEdit:focus, QSpinBox:focus {
                border: 1px solid #3f67b1;
            }
            #totalArea {
                font-size: 17px;
                font-weight: 800;
                color: #173b79;
            }
            #card {
                background: white;
                border: 1px solid #d9e1ef;
                border-radius: 11px;
            }
            #cardLabel {
                color: #728099;
                font-size: 10px;
                font-weight: 800;
                letter-spacing: 1px;
            }
            #cardValue {
                color: #173b79;
                font-size: 17px;
                font-weight: 800;
            }
            QPushButton {
                background: #17376d;
                color: white;
                border: none;
                border-radius: 7px;
                padding: 8px 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #27518f;
            }
            QCheckBox {
                color: #47556e;
                padding-left: 5px;
            }
            #hint, #notes {
                color: #66748d;
                background: #edf3fb;
                border: 1px solid #d8e4f4;
                border-radius: 7px;
                padding: 7px 10px;
            }
            QTableWidget {
                background: white;
                alternate-background-color: #f7f9fc;
                border: 1px solid #d9e1ef;
                border-radius: 9px;
                gridline-color: #e7ecf3;
                selection-background-color: #dce8fb;
                selection-color: #10254d;
            }
            QHeaderView::section {
                background: #14264f;
                color: white;
                padding: 9px 7px;
                border: none;
                font-size: 11px;
                font-weight: 800;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """)

    # ---------- Data ----------
    def load_sample_rows(self):
        self.table.setRowCount(0)
        for owner, ratio in SAMPLE_ROWS:
            self.add_row(owner, ratio)
        self.calculate()

    def add_row(self, owner="", ratio=""):
        row = self.table.rowCount()
        self.table.insertRow(row)
        n = QTableWidgetItem(str(row + 1))
        n.setFlags(n.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(row, 0, n)
        self.table.setItem(row, 1, QTableWidgetItem(owner))
        self.table.setItem(row, 2, QTableWidgetItem(ratio))
        result = QTableWidgetItem("")
        result.setFlags(result.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(row, 3, result)
        self.table.scrollToBottom()

    def remove_selected(self):
        rows = sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True)
        for row in rows:
            self.table.removeRow(row)
        self.renumber()
        self.calculate()

    def renumber(self):
        for row in range(self.table.rowCount()):
            self.table.item(row, 0).setText(str(row + 1))

    def paste_rows(self):
        cb = QApplication.clipboard()
        text = cb.text()
        rows = parse_clipboard_rows(text)
        if not rows:
            QMessageBox.information(
                self, "Nothing found",
                "No Owner + Share Ratio pairs were found in the clipboard.\n\n"
                "Copy the webpage rows including the owner and share-ratio columns."
            )
            return
        for owner, ratio in rows:
            self.add_row(owner, ratio)
        self.calculate()
        QMessageBox.information(
            self, "Imported",
            f"{len(rows)} owner/ratio rows were added. Other webpage columns were ignored."
        )

    def copy_owner_ratio(self, selected_only=False):
        """Copy only Owner Full Name + Share Ratio as tab-separated text."""
        if selected_only:
            row_numbers = sorted({idx.row() for idx in self.table.selectedIndexes()})
        else:
            row_numbers = list(range(self.table.rowCount()))

        if not row_numbers:
            QMessageBox.information(
                self, "Nothing selected",
                "Select one or more owner rows first."
            )
            return

        lines = ["OWNER FULL NAME\tSHARE RATIO"]
        for row in row_numbers:
            owner = self.table.item(row, 1).text().strip()
            ratio = self.table.item(row, 2).text().strip()
            if owner or ratio:
                lines.append(f"{owner}\t{ratio}")

        QApplication.clipboard().setText("\n".join(lines))
        self.statusBar().showMessage(
            f"Copied {len(lines)-1} owner + ratio row(s) to clipboard."
        )

    def copy_current_row(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "No row", "Select an owner row first.")
            return
        owner = self.table.item(row, 1).text().strip()
        ratio = self.table.item(row, 2).text().strip()
        QApplication.clipboard().setText(f"{owner}\t{ratio}")
        self.statusBar().showMessage("Copied current Owner + Share Ratio.")

    def total_sarshai(self):
        return self.kanal.value() * SARSHARI_PER_KANAL + self.marla.value() * SARSHARI_PER_MARLA

    def calculate(self):
        total = self.total_sarshai()
        self.total_label.setText(area_to_text(total))
        self.card_owners.value_label.setText(str(self.table.rowCount()))
        self.card_total.value_label.setText(area_to_text(total))

        calculated_total = 0
        errors = []
        for row in range(self.table.rowCount()):
            owner = self.table.item(row, 1).text().strip()
            ratio_text = self.table.item(row, 2).text().strip()
            result_item = self.table.item(row, 3)
            if not ratio_text:
                result_item.setText("—")
                result_item.setToolTip("Enter a ratio such as 589/92784")
                continue
            try:
                ratio = parse_ratio(ratio_text)
                exact = Fraction(total) * ratio
                if self.round_check.isChecked():
                    share_s = round_fraction_half_up(exact)
                else:
                    # Display mode is still integer-only; floor is used only
                    # when the checkbox is off.
                    share_s = exact.numerator // exact.denominator
                calculated_total += share_s
                result_item.setText(area_to_text(share_s))
                result_item.setToolTip(
                    f"{owner}\nRatio: {ratio_text}\n"
                    f"Exact Sarshai: {float(exact):,.4f}\n"
                    f"Displayed: {area_to_text(share_s)}"
                )
            except Exception as exc:
                result_item.setText("INVALID RATIO")
                result_item.setToolTip(str(exc))
                errors.append(row + 1)

        self.card_alloc.value_label.setText(area_to_text(calculated_total))
        diff = total - calculated_total
        self.card_diff.value_label.setText(f"{diff:+,} S")
        self.card_diff.value_label.setToolTip(
            "Input total Sarshai minus the sum of displayed owner shares."
        )

        if errors:
            # Do not pop up repeatedly while the user is typing.
            self.statusBar().showMessage(
                "Invalid ratio in row(s): " + ", ".join(map(str, errors))
            )
        else:
            self.statusBar().showMessage("Calculation updated.")

    # ---------- Project / export ----------
    def project_dict(self):
        rows = []
        for row in range(self.table.rowCount()):
            rows.append({
                "owner": self.table.item(row, 1).text(),
                "ratio": self.table.item(row, 2).text(),
            })
        return {
            "application": APP_TITLE,
            "version": "1.0",
            "village": self.village.text(),
            "jamabandi_year": self.year.text(),
            "total_kanal": self.kanal.value(),
            "total_marla": self.marla.value(),
            "round_to_sarshai": self.round_check.isChecked(),
            "rows": rows,
        }

    def save_project(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Khewat Project", "", "Khewat Project (*.khewat.json);;JSON (*.json)"
        )
        if not path:
            return
        try:
            Path(path).write_text(
                json.dumps(self.project_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            self.statusBar().showMessage(f"Saved: {path}")
        except Exception as exc:
            QMessageBox.critical(self, "Save Error", str(exc))

    def open_project(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Khewat Project", "", "Khewat Project (*.khewat.json *.json);;JSON (*.json)"
        )
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            self.village.setText(str(data.get("village", "")))
            self.year.setText(str(data.get("jamabandi_year", "")))
            self.kanal.setValue(int(data.get("total_kanal", 0)))
            self.marla.setValue(int(data.get("total_marla", 0)))
            self.round_check.setChecked(bool(data.get("round_to_sarshai", True)))
            self.table.setRowCount(0)
            for row in data.get("rows", []):
                self.add_row(str(row.get("owner", "")), str(row.get("ratio", "")))
            self.calculate()
            self.statusBar().showMessage(f"Opened: {path}")
        except Exception as exc:
            QMessageBox.critical(self, "Open Error", str(exc))

    def export_csv(self):
        self.calculate()
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Calculation", "", "CSV (*.csv)"
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["JASS Khewat Share Calculator"])
                w.writerow(["Village", self.village.text()])
                w.writerow(["Jamabandi Year", self.year.text()])
                w.writerow(["Total Area", area_to_text(self.total_sarshai())])
                w.writerow([])
                w.writerow(["No.", "Owner Full Name", "Share Ratio", "Calculated Share"])
                for row in range(self.table.rowCount()):
                    w.writerow([
                        self.table.item(row, 0).text(),
                        self.table.item(row, 1).text(),
                        self.table.item(row, 2).text(),
                        self.table.item(row, 3).text(),
                    ])
            self.statusBar().showMessage(f"Exported: {path}")
        except Exception as exc:
            QMessageBox.critical(self, "Export Error", str(exc))


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)
    app.setOrganizationName("JASS Digital Lab")
    app.setStyle("Fusion")
    window = KhewatShareCalculator()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
