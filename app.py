#!/usr/bin/env python3
"""
Game Theory Explorer & Puzzle Simulator
A comprehensive PySide6 application for understanding game theory concepts
through interactive nonograms, logic puzzles, and simulations.
"""

import sys
import random
import math
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QComboBox, QSpinBox, QGroupBox,
    QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea,
    QFrame, QSizePolicy, QRadioButton, QButtonGroup, QSlider, QCheckBox
)
from PySide6.QtCore import Qt, QTimer, Signal, QRectF
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QBrush


# ════════════════════════════════════════════════════════════════
#  DATA
# ════════════════════════════════════════════════════════════════

def compute_clues(grid):
    rows, cols = len(grid), len(grid[0]) if grid else 0
    rc, cc = [], []
    for r in range(rows):
        c, run = [], 0
        for v in grid[r]:
            if v: run += 1
            elif run: c.append(run); run = 0
        if run: c.append(run)
        rc.append(c or [0])
    for c in range(cols):
        cl, run = [], 0
        for r in range(rows):
            if grid[r][c]: run += 1
            elif run: cl.append(run); run = 0
        if run: cl.append(run)
        cc.append(cl or [0])
    return rc, cc

NONOGRAM_PUZZLES = {
    "Heart (5×5)": {"grid": [[0,1,0,1,0],[1,1,1,1,1],[1,1,1,1,1],[0,1,1,1,0],[0,0,1,0,0]]},
    "Arrow (5×5)": {"grid": [[0,0,1,0,0],[0,1,1,1,0],[1,1,1,1,1],[0,0,1,0,0],[0,0,1,0,0]]},
    "Cross (7×7)": {"grid": [[0,0,0,1,0,0,0],[0,0,0,1,0,0,0],[0,0,0,1,0,0,0],[1,1,1,1,1,1,1],[0,0,0,1,0,0,0],[0,0,0,1,0,0,0],[0,0,0,1,0,0,0]]},
    "House (7×7)": {"grid": [[0,0,0,1,0,0,0],[0,0,1,1,1,0,0],[0,1,1,1,1,1,0],[1,1,1,1,1,1,1],[0,1,1,1,1,1,0],[0,1,1,0,1,1,0],[0,1,1,0,1,1,0]]},
}
for p in NONOGRAM_PUZZLES.values():
    p["rows"] = len(p["grid"]); p["cols"] = len(p["grid"][0])
    p["row_clues"], p["col_clues"] = compute_clues(p["grid"])

LOGIC_PUZZLES = {
    "The Pet Owners (Easy)": {
        "people": ["Alice", "Bob", "Carol", "Dave"],
        "attributes": {"Color": ["Red", "Blue", "Green", "Yellow"], "Pet": ["Cat", "Dog", "Fish", "Bird"]},
        "solution": {"Alice": {"Color": "Yellow", "Pet": "Fish"}, "Bob": {"Color": "Blue", "Pet": "Dog"}, "Carol": {"Color": "Green", "Pet": "Cat"}, "Dave": {"Color": "Red", "Pet": "Bird"}},
        "clues": ["1. Bob owns a Dog.", "2. The person in the Green house owns a Cat.", "3. The person in the Red house owns a Bird.", "4. Alice's house is not Red or Blue.", "5. Dave's house is not Green or Yellow.", "6. Carol does not own a Dog or a Fish.", "7. Alice owns a Fish."]
    },
}

PAYOFF_PRESETS = {
    "Prisoner's Dilemma": {"payoffs": [[(3,3),(0,5)],[(5,0),(1,1)]], "desc": "Both better off cooperating, incentive to defect."},
    "Battle of the Sexes": {"payoffs": [[(3,2),(0,0)],[(0,0),(2,3)]], "desc": "Prefer different but want togetherness."},
    "Stag Hunt": {"payoffs": [[(4,4),(0,3)],[(3,0),(2,2)]], "desc": "Cooperation is best but risky."},
    "Chicken": {"payoffs": [[(3,3),(1,5)],[(5,1),(0,0)]], "desc": "Brinkmanship."},
    "Matching Pennies": {"payoffs": [[(1,-1),(-1,1)],[(-1,1),(1,-1)]], "desc": "Zero-sum, no pure NE."},
}

# ════════════════════════════════════════════════════════════════
#  CUSTOM WIDGETS
# ════════════════════════════════════════════════════════════════

class LineChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self.series = {}; self.colors = {}
        self.setMinimumSize(460, 260); self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    def set_series(self, data, colors=None): self.series = data; self.colors = colors or {}; self.update()
    def clear(self): self.series.clear(); self.colors.clear(); self.update()
    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing); p.fillRect(self.rect(), QColor(18, 18, 32))
        if not self.series or not any(self.series.values()):
            p.setPen(QColor(90, 90, 110)); p.setFont(QFont("Segoe UI", 11)); p.drawText(self.rect(), Qt.AlignCenter, "No data yet"); p.end(); return
        ml, mr, mt, mb = 55, 130, 25, 35; pw = self.width()-ml-mr; ph = self.height()-mt-mb
        if pw < 40 or ph < 40: p.end(); return
        all_x = [pt[0] for s in self.series.values() for pt in s]; all_y = [pt[1] for s in self.series.values() for pt in s]
        if not all_x: p.end(); return
        xmn, xmx = min(all_x), max(all_x); ymn, ymx = 0, max(all_y) if all_y else 1
        
        if xmx == xmn: xmx = xmn + 1
        if ymx == ymn: ymx = ymn + 1
            
        p.setPen(QPen(QColor(45,45,65),1,Qt.DotLine))
        for i in range(5): y=mt+ph*i/4; p.drawLine(ml,int(y),ml+pw,int(y))
        p.setPen(QPen(QColor(110,110,140),1)); p.drawLine(ml,mt,ml,mt+ph); p.drawLine(ml,mt+ph,ml+pw,mt+ph)
        defaults=[QColor(100,200,255),QColor(255,120,120),QColor(120,255,120),QColor(255,210,80),QColor(200,130,255),QColor(255,160,100)]
        idx=0
        for name,pts in self.series.items():
            col=self.colors.get(name,defaults[idx%len(defaults)]); p.setPen(QPen(col,2))
            for i in range(1,len(pts)):
                x1=ml+(pts[i-1][0]-xmn)/(xmx-xmn)*pw; y1=mt+ph-(pts[i-1][1]-ymn)/(ymx-ymn)*ph
                x2=ml+(pts[i][0]-xmn)/(xmx-xmn)*pw; y2=mt+ph-(pts[i][1]-ymn)/(ymx-ymn)*ph
                p.drawLine(int(x1),int(y1),int(x2),int(y2))
            ly=mt+8+idx*22; p.fillRect(ml+pw+12,ly,12,12,col); p.setPen(QColor(200,200,220)); p.drawText(ml+pw+30,ly-2,110,16,Qt.AlignLeft|Qt.AlignVCenter,name); idx+=1
        p.end()

class NonogramCell(QFrame):
    clicked = Signal(int, int, int)
    def __init__(self, r, c):
        super().__init__(); self.r, self.c, self.state = r, c, 0
        self.setFixedSize(34, 34); self.setCursor(Qt.PointingHandCursor); self._style()
    def _style(self):
        if self.state == 1: self.setStyleSheet("background:#42a5f5;border:1px solid #1565c0;border-radius:2px;")
        elif self.state == 2: self.setStyleSheet("background:#263238;border:1px solid #37474f;border-radius:2px;color:#ef5350;font-weight:bold;")
        else: self.setStyleSheet("background:#0d1b2a;border:1px solid #1b2838;border-radius:2px;")
    def set_state(self, s): self.state = s; self._style()
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton: self.clicked.emit(self.r, self.c, 1)
        elif e.button() == Qt.RightButton: self.clicked.emit(self.r, self.c, 2)

class BeachWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(); self.p1 = 25; self.p2 = 75; self.setMinimumHeight(120); self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    def set_positions(self, p1, p2): self.p1 = p1; self.p2 = p2; self.update()
    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(26, 26, 46))
        beach_rect = QRectF(20, 20, w-40, h-40)
        p.setPen(QPen(QColor(255,255,255), 2)); p.drawRect(beach_rect)
        mid = (self.p1 + self.p2) / 2.0
        p1_start = 20; p1_end = 20 + (mid / 100.0) * (w - 40)
        p2_start = p1_end; p2_end = 20 + (w - 40)
        p.fillRect(QRectF(p1_start, 20, p1_end-p1_start, h-40), QColor(42, 157, 143, 100))
        p.fillRect(QRectF(p2_start, 20, p2_end-p2_start, h-40), QColor(230, 57, 70, 100))
        x1 = 20 + (self.p1 / 100.0) * (w - 40); x2 = 20 + (self.p2 / 100.0) * (w - 40)
        p.setPen(QPen(QColor(100,200,255), 3)); p.setBrush(QBrush(QColor(100,200,255)))
        p.drawRect(QRectF(x1-5, 10, 10, h-20))
        p.setPen(QPen(QColor(255,120,120), 3)); p.setBrush(QBrush(QColor(255,120,120)))
        p.drawRect(QRectF(x2-5, 10, 10, h-20))
        p.setPen(QColor(220,220,220)); p.setFont(QFont("Segoe UI", 10, QFont.Bold))
        p.drawText(int(x1-15), h-5, "P1"); p.drawText(int(x2-15), h-5, "P2")
        p.end()

# ════════════════════════════════════════════════════════════════
#  MAIN APPLICATION
# ════════════════════════════════════════════════════════════════

class GameTheoryApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Game Theory Explorer & Puzzle Simulator")
        self.setMinimumSize(1300, 900)
        tabs = QTabWidget(); self.setCentralWidget(tabs)
        self._build_theory_tab(tabs)
        self._build_nonogram_tab(tabs)
        self._build_logic_tab(tabs)
        self._build_pd_tab(tabs)
        self._build_payoff_tab(tabs)
        self._build_evo_tab(tabs)
        self._build_monty_hall_tab(tabs)
        self._build_ultimatum_tab(tabs)
        self._build_hotelling_tab(tabs)
        self._apply_styles()

    def _apply_styles(self):
        self.setStyleSheet("""
            QMainWindow{background:#0f0f23}
            QTabWidget::pane{border:1px solid #2a2a4a;background:#0f0f23}
            QTabBar::tab{background:#1a1a2e;color:#aac;padding:9px 18px;border:1px solid #2a2a4a;border-bottom:none;margin-right:2px;font-size:12px}
            QTabBar::tab:selected{background:#16213e;color:#64ffda;border-bottom:2px solid #64ffda}
            QTabBar::tab:hover{background:#1e1e3e}
            QLabel{color:#ccd}
            QGroupBox{color:#64ffda;border:1px solid #2a2a4a;border-radius:6px;margin-top:12px;padding-top:16px;font-weight:bold;font-size:12px}
            QGroupBox::title{subcontrol-origin:margin;left:10px;padding:0 5px}
            QPushButton{background:#16213e;color:#64ffda;border:1px solid #2a2a4a;padding:7px 14px;border-radius:4px;font-weight:bold;font-size:11px}
            QPushButton:hover{background:#1c2e4e;border-color:#64ffda}
            QPushButton:pressed{background:#0f1a3e}
            QPushButton:disabled{color:#556;border-color:#333}
            QComboBox{background:#1a1a2e;color:#ccd;border:1px solid #2a2a4a;padding:5px;border-radius:4px}
            QComboBox::drop-down{border:none}
            QComboBox QAbstractItemView{background:#1a1a2e;color:#ccd;selection-background-color:#16213e}
            QSpinBox{background:#1a1a2e;color:#ccd;border:1px solid #2a2a4a;padding:4px;border-radius:4px}
            QTextEdit{background:#1a1a2e;color:#ccd;border:1px solid #2a2a4a;border-radius:4px;font-size:13px}
            QSlider::groove:horizontal{height:6px;background:#2a2a4a;border-radius:3px}
            QSlider::handle:horizontal{background:#64ffda;width:14px;margin:-4px 0;border-radius:7px}
            QCheckBox{color:#ccd} QRadioButton{color:#ccd}
        """)

    # ══════════════════════════════════════════════════════════
    #  TAB 1 — THEORY
    # ══════════════════════════════════════════════════════════
    def _build_theory_tab(self, tabs):
        w = QWidget(); lay = QVBoxLayout(w); lay.setContentsMargins(8,8,8,8)
        te = QTextEdit(); te.setReadOnly(True)
        te.setHtml("""
        <h2 style='color:#64ffda'>🎮 Game Theory Explorer</h2>
        <p style='color:#aab;font-size:14px'>Game theory is the mathematical study of strategic interaction among rational decision-makers.
        It provides frameworks to analyze situations where the outcome for each participant depends on the choices of all others.</p>
        <h3 style='color:#64ffda'>📌 Core Concepts</h3>
        <ul style='color:#ccd;font-size:13px'>
        <li><b>Nash Equilibrium</b>: A state where no player can improve their payoff by unilaterally changing strategy.</li>
        <li><b>Dominant Strategy</b>: A strategy that yields a higher payoff regardless of what opponents choose.</li>
        <li><b>Pareto Optimality</b>: An outcome where no player can be made better off without making another worse off.</li>
        <li><b>Bayesian Updating</b>: Revising probabilities based on new evidence (featured in Monty Hall).</li>
        <li><b>Behavioral Game Theory</b>: How real humans deviate from pure rationality due to fairness/spite (Ultimatum Game).</li>
        <li><b>Spatial Competition</b>: How location choices affect market share (Hotelling's Game).</li>
        </ul>
        <h3 style='color:#64ffda'>🗺️ Application Map</h3>
        <table style='color:#ccd;font-size:13px' cellpadding=6>
        <tr><td style='color:#64ffda'>🔲 Nonogram</td><td>Constraint-satisfaction & deduction</td></tr>
        <tr><td style='color:#64ffda'>🧩 Logic Puzzle</td><td>Elimination and inference</td></tr>
        <tr><td style='color:#64ffda'>⚖️ Prisoner's Dilemma</td><td>Iterated strategic interaction</td></tr>
        <tr><td style='color:#64ffda'>📊 Payoff Matrix</td><td>Nash Equilibria & Dominant Strategies</td></tr>
        <tr><td style='color:#64ffda'>🧬 Evolution</td><td>Replicator dynamics & population survival</td></tr>
        <tr><td style='color:#64ffda'>🚪 Monty Hall</td><td>Bayesian probability & counter-intuition</td></tr>
        <tr><td style='color:#64ffda'>💰 Ultimatum</td><td>Bargaining, fairness & behavioral economics</td></tr>
        <tr><td style='color:#64ffda'>🏖️ Hotelling</td><td>Spatial competition & median voter theorem</td></tr>
        </table>
        """)
        lay.addWidget(te); tabs.addTab(w, "📚 Theory")

    # ══════════════════════════════════════════════════════════
    #  TAB 2 — NONOGRAM
    # ══════════════════════════════════════════════════════════
    def _build_nonogram_tab(self, tabs):
        w = QWidget(); outer = QHBoxLayout(w); outer.setContentsMargins(10,10,10,10)
        left = QVBoxLayout(); left.addWidget(QLabel("Select Puzzle:"))
        self.non_combo = QComboBox(); self.non_combo.addItems(NONOGRAM_PUZZLES.keys())
        self.non_combo.currentTextChanged.connect(self._non_load_puzzle); left.addWidget(self.non_combo)
        btn_row = QHBoxLayout()
        b1 = QPushButton("Check"); b1.clicked.connect(self._non_check)
        b2 = QPushButton("Reset"); b2.clicked.connect(self._non_reset)
        b3 = QPushButton("Hint");  b3.clicked.connect(self._non_hint)
        b4 = QPushButton("🤖 Auto-Solve"); b4.clicked.connect(self._non_auto_solve)
        btn_row.addWidget(b1); btn_row.addWidget(b2); btn_row.addWidget(b3); btn_row.addWidget(b4)
        left.addLayout(btn_row); self.non_status = QLabel(""); self.non_status.setWordWrap(True); left.addWidget(self.non_status)
        left.addStretch()
        self.non_grid_widget = QWidget(); self.non_grid_layout = QGridLayout(self.non_grid_widget); self.non_grid_layout.setSpacing(1); self.non_cells = {}
        outer.addLayout(left, 1); outer.addWidget(self.non_grid_widget, 3)
        tabs.addTab(w, "🔲 Nonogram"); self._non_load_puzzle(self.non_combo.currentText())

    def _non_load_puzzle(self, name):
        for c in self.non_cells.values(): c.deleteLater()
        self.non_cells.clear()
        while self.non_grid_layout.count():
            item = self.non_grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        if name not in NONOGRAM_PUZZLES: return
        p = NONOGRAM_PUZZLES[name]; R, C = p["rows"], p["cols"]; rc, cc = p["row_clues"], p["col_clues"]
        max_rc = max(len(x) for x in rc); max_cc = max(len(x) for x in cc)
        for ci, clue in enumerate(cc):
            for ri, val in enumerate(clue):
                lbl = QLabel(str(val)); lbl.setAlignment(Qt.AlignCenter); lbl.setFixedSize(34, 28); lbl.setStyleSheet("color:#ffcc80;font-weight:bold;font-size:13px;")
                self.non_grid_layout.addWidget(lbl, ri, ci + max_rc)
        for ri, clue in enumerate(rc):
            for ci, val in enumerate(clue):
                lbl = QLabel(str(val)); lbl.setAlignment(Qt.AlignCenter); lbl.setFixedSize(34, 28); lbl.setStyleSheet("color:#ffcc80;font-weight:bold;font-size:13px;")
                self.non_grid_layout.addWidget(lbl, ri + max_cc, ci)
        for r in range(R):
            for c in range(C):
                cell = NonogramCell(r, c); cell.clicked.connect(self._non_cell_clicked)
                self.non_cells[(r, c)] = cell; self.non_grid_layout.addWidget(cell, r + max_cc, c + max_rc)
        self.non_status.setText(""); self.non_puzzle_name = name

    def _non_cell_clicked(self, r, c, btn):
        cell = self.non_cells[(r, c)]
        if btn == 1: cell.set_state(1 if cell.state != 1 else 0)
        elif btn == 2: cell.set_state(2 if cell.state != 2 else 0)

    def _non_check(self):
        sol = NONOGRAM_PUZZLES[self.non_puzzle_name]["grid"]
        ok = all(self.non_cells[(r,c)].state == 1 for r in range(len(sol)) for c in range(len(sol[0])) if sol[r][c]) and \
             all(self.non_cells[(r,c)].state != 1 for r in range(len(sol)) for c in range(len(sol[0])) if not sol[r][c])
        self.non_status.setText('<span style="color:#69f0ae;font-size:15px;font-weight:bold">✓ Correct!</span>' if ok else '<span style="color:#ff5252;font-size:14px">✗ Not quite.</span>')

    def _non_reset(self):
        for cell in self.non_cells.values(): cell.set_state(0); self.non_status.setText("")

    def _non_hint(self):
        sol = NONOGRAM_PUZZLES[self.non_puzzle_name]["grid"]
        empties = [(r,c) for (r,c),cell in self.non_cells.items() if cell.state == 0]
        if empties: r, c = random.choice(empties); self.non_cells[(r,c)].set_state(1 if sol[r][c] else 2)

    def _non_auto_solve(self):
        sol = NONOGRAM_PUZZLES[self.non_puzzle_name]["grid"]
        for r in range(len(sol)):
            for c in range(len(sol[0])): self.non_cells[(r,c)].set_state(1 if sol[r][c] else 2)
        self.non_status.setText('<span style="color:#64ffda">Auto-solved!</span>')

    # ══════════════════════════════════════════════════════════
    #  TAB 3 — LOGIC PUZZLE
    # ══════════════════════════════════════════════════════════
    def _build_logic_tab(self, tabs):
        w = QWidget(); outer = QHBoxLayout(w); outer.setContentsMargins(10,10,10,10)
        left = QVBoxLayout(); left.addWidget(QLabel("Select Puzzle:"))
        self.log_combo = QComboBox(); self.log_combo.addItems(LOGIC_PUZZLES.keys())
        self.log_combo.currentTextChanged.connect(self._log_load_puzzle); left.addWidget(self.log_combo)
        self.log_clues_box = QGroupBox("Clues"); self.log_clues_layout = QVBoxLayout(self.log_clues_box); left.addWidget(self.log_clues_box)
        btn_row = QHBoxLayout()
        bc = QPushButton("Check"); bc.clicked.connect(self._log_check); br = QPushButton("Reset"); br.clicked.connect(self._log_reset)
        btn_row.addWidget(bc); btn_row.addWidget(br); left.addLayout(btn_row)
        self.log_status = QLabel(""); self.log_status.setWordWrap(True); left.addWidget(self.log_status); left.addStretch()
        self.log_grid_container = QWidget(); self.log_grid_layout = QVBoxLayout(self.log_grid_container)
        outer.addLayout(left, 1); outer.addWidget(self.log_grid_container, 3)
        tabs.addTab(w, "🧩 Logic Puzzle"); self.log_dropdowns = {}; self._log_load_puzzle(self.log_combo.currentText())

    def _log_load_puzzle(self, name):
        while self.log_clues_layout.count():
            item = self.log_clues_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        while self.log_grid_layout.count():
            item = self.log_grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        self.log_dropdowns.clear()
        if name not in LOGIC_PUZZLES: return
        p = LOGIC_PUZZLES[name]
        for clue in p["clues"]: lbl = QLabel(clue); lbl.setWordWrap(True); lbl.setStyleSheet("color:#ffcc80;font-size:13px;"); self.log_clues_layout.addWidget(lbl)
        grid = QGridLayout(); grid.setSpacing(6); attrs = list(p["attributes"].keys()); col = 1
        for attr in attrs: lbl = QLabel(f"<b>{attr}</b>"); lbl.setStyleSheet("color:#64ffda;"); lbl.setAlignment(Qt.AlignCenter); grid.addWidget(lbl, 0, col); col += 1
        row = 1
        for person in p["people"]:
            grid.addWidget(QLabel(f"<b>{person}</b>"), row, 0); col = 1
            for attr in attrs: cb = QComboBox(); cb.addItems(["—"] + p["attributes"][attr]); cb.setMinimumWidth(100); self.log_dropdowns[(person, attr)] = cb; grid.addWidget(cb, row, col); col += 1
            row += 1
        self.log_grid_layout.addLayout(grid); self.log_status.setText("")

    def _log_check(self):
        p = LOGIC_PUZZLES[self.log_combo.currentText()]; sol = p["solution"]; all_correct = True; incomplete = False
        for person in p["people"]:
            for attr in p["attributes"]:
                cb = self.log_dropdowns[(person, attr)]; val = cb.currentText()
                if val == "—": incomplete = True; all_correct = False; cb.setStyleSheet("")
                elif val != sol[person][attr]: all_correct = False; cb.setStyleSheet("background:#ff5252;color:white;")
                else: cb.setStyleSheet("background:#69f0ae;color:black;")
        if all_correct and not incomplete: self.log_status.setText('<span style="color:#69f0ae;font-weight:bold">✓ Correct!</span>')
        elif incomplete: self.log_status.setText('<span style="color:#ffcc80">Fill all fields.</span>')
        else: self.log_status.setText('<span style="color:#ff5252">✗ Incorrect cells highlighted.</span>')

    def _log_reset(self):
        for cb in self.log_dropdowns.values(): cb.setCurrentIndex(0); cb.setStyleSheet(""); self.log_status.setText("")

    # ══════════════════════════════════════════════════════════
    #  TAB 4 — PRISONER'S DILEMMA
    # ══════════════════════════════════════════════════════════
    def _build_pd_tab(self, tabs):
        w = QWidget(); outer = QHBoxLayout(w); outer.setContentsMargins(10,10,10,10)
        left = QVBoxLayout()
        mode_grp = QGroupBox("Mode"); ml = QVBoxLayout(mode_grp)
        self.pd_mode_ai = QRadioButton("AI vs AI"); self.pd_mode_ai.setChecked(True)
        self.pd_mode_human = QRadioButton("Human vs AI")
        ml.addWidget(self.pd_mode_ai); ml.addWidget(self.pd_mode_human)
        self.pd_mode_ai.toggled.connect(self._pd_mode_changed); left.addWidget(mode_grp)
        s1_grp = QGroupBox("Player 1 Strategy"); s1l = QVBoxLayout(s1_grp); self.pd_s1 = QComboBox()
        self.pd_s1.addItems(["Always Cooperate","Always Defect","Tit-for-Tat","Grim Trigger","Pavlov","Random"]); s1l.addWidget(self.pd_s1); left.addWidget(s1_grp)
        s2_grp = QGroupBox("Player 2 Strategy"); s2l = QVBoxLayout(s2_grp); self.pd_s2 = QComboBox()
        self.pd_s2.addItems(["Always Cooperate","Always Defect","Tit-for-Tat","Grim Trigger","Pavlov","Random"]); self.pd_s2.setCurrentIndex(2); s2l.addWidget(self.pd_s2); left.addWidget(s2_grp)
        rounds_grp = QGroupBox("Rounds"); rl = QHBoxLayout(rounds_grp); self.pd_rounds = QSpinBox(); self.pd_rounds.setRange(1,500); self.pd_rounds.setValue(50)
        rl.addWidget(QLabel("Count:")); rl.addWidget(self.pd_rounds); left.addWidget(rounds_grp)
        self.pd_human_choice_grp = QGroupBox("Your Move"); hcl = QHBoxLayout(self.pd_human_choice_grp)
        self.pd_btn_coop = QPushButton("🤝 Cooperate"); self.pd_btn_coop.clicked.connect(lambda: self._pd_human_move('C'))
        self.pd_btn_def = QPushButton("🗡 Defect"); self.pd_btn_def.clicked.connect(lambda: self._pd_human_move('D'))
        hcl.addWidget(self.pd_btn_coop); hcl.addWidget(self.pd_btn_def)
        self.pd_human_choice_grp.setVisible(False); left.addWidget(self.pd_human_choice_grp)
        btn_row = QHBoxLayout(); bp = QPushButton("▶ Play"); bp.clicked.connect(self._pd_play)
        brst = QPushButton("↺ Reset"); brst.clicked.connect(self._pd_reset); btn_row.addWidget(bp); btn_row.addWidget(brst); left.addLayout(btn_row)
        self.pd_score_label = QLabel("P1: 0 | P2: 0"); self.pd_score_label.setStyleSheet("font-size:14px;font-weight:bold;color:#64ffda;"); left.addWidget(self.pd_score_label); left.addStretch()
        center = QVBoxLayout(); self.pd_history = QTextEdit(); self.pd_history.setReadOnly(True); self.pd_history.setFont(QFont("Consolas", 10))
        center.addWidget(self.pd_history)
        right = QVBoxLayout(); self.pd_chart = LineChart(); right.addWidget(self.pd_chart)
        outer.addLayout(left, 1); outer.addLayout(center, 2); outer.addLayout(right, 2)
        tabs.addTab(w, "⚖️ Prisoner's Dilemma")
        self.pd_state = {"p1_score": 0, "p2_score": 0, "round": 0, "p1_history": [], "p2_history": [], "chart_p1": [], "chart_p2": []}

    def _pd_mode_changed(self):
        is_human = self.pd_mode_human.isChecked(); self.pd_s2.setEnabled(not is_human)
        self.pd_human_choice_grp.setVisible(is_human); self.pd_btn_coop.setEnabled(False); self.pd_btn_def.setEnabled(False)

    def _pd_get_action(self, strategy, my_history, opp_history):
        if strategy == "Always Cooperate": return 'C'
        if strategy == "Always Defect": return 'D'
        if strategy == "Tit-for-Tat": return opp_history[-1] if opp_history else 'C'
        if strategy == "Grim Trigger": return 'D' if 'D' in opp_history else 'C'
        if strategy == "Pavlov": return 'C' if not my_history else ('C' if my_history[-1] == opp_history[-1] else 'D')
        if strategy == "Random": return random.choice(['C', 'D'])
        return 'C'

    def _pd_payoff(self, a1, a2):
        if a1 == 'C' and a2 == 'C': return 3, 3
        if a1 == 'C' and a2 == 'D': return 0, 5
        if a1 == 'D' and a2 == 'C': return 5, 0
        return 1, 1

    def _pd_play_round(self, a1=None):
        st = self.pd_state; is_human = self.pd_mode_human.isChecked()
        if is_human: 
            if a1 is None: return
            a2 = self._pd_get_action(self.pd_s2.currentText(), st["p2_history"], st["p1_history"])
        else:
            a1 = self._pd_get_action(self.pd_s1.currentText(), st["p1_history"], st["p2_history"])
            a2 = self._pd_get_action(self.pd_s2.currentText(), st["p2_history"], st["p1_history"])
        p1p, p2p = self._pd_payoff(a1, a2); st["p1_score"] += p1p; st["p2_score"] += p2p
        st["p1_history"].append(a1); st["p2_history"].append(a2); st["round"] += 1
        st["chart_p1"].append((st["round"], st["p1_score"])); st["chart_p2"].append((st["round"], st["p2_score"]))
        sym = lambda a: "Coop" if a == 'C' else "Def"
        self.pd_history.append(f"R{st['round']:>3} | P1: {sym(a1):>4}  P2: {sym(a2):>4} | Pay: ({p1p},{p2p}) | Tot: ({st['p1_score']},{st['p2_score']})")
        self.pd_score_label.setText(f"P1: {st['p1_score']} | P2: {st['p2_score']} | Round: {st['round']}")
        self.pd_chart.set_series({"Player 1": st["chart_p1"], "Player 2": st["chart_p2"]}, {"Player 1": QColor(100,200,255), "Player 2": QColor(255,120,120)})

    def _pd_human_move(self, action):
        self._pd_play_round(a1=action)
        if self.pd_state["round"] >= self.pd_rounds.value(): self.pd_btn_coop.setEnabled(False); self.pd_btn_def.setEnabled(False)

    def _pd_play(self):
        self._pd_reset(); is_human = self.pd_mode_human.isChecked()
        if is_human: self.pd_btn_coop.setEnabled(True); self.pd_btn_def.setEnabled(True); self.pd_history.append("--- Click Cooperate or Defect ---"); return
        n = self.pd_rounds.value()
        for _ in range(n): self._pd_play_round()

    def _pd_reset(self):
        self.pd_state = {"p1_score": 0, "p2_score": 0, "round": 0, "p1_history": [], "p2_history": [], "chart_p1": [], "chart_p2": []}
        self.pd_history.clear(); self.pd_score_label.setText("P1: 0 | P2: 0"); self.pd_chart.clear()
        self.pd_btn_coop.setEnabled(False); self.pd_btn_def.setEnabled(False)

    # ══════════════════════════════════════════════════════════
    #  TAB 5 — PAYOFF MATRIX
    # ══════════════════════════════════════════════════════════
    def _build_payoff_tab(self, tabs):
        w = QWidget(); outer = QHBoxLayout(w); outer.setContentsMargins(10,10,10,10)
        left = QVBoxLayout(); left.addWidget(QLabel("Preset Game:"))
        self.pay_combo = QComboBox(); self.pay_combo.addItems(["Custom"] + list(PAYOFF_PRESETS.keys()))
        self.pay_combo.currentTextChanged.connect(self._pay_load_preset); left.addWidget(self.pay_combo)
        mat_grp = QGroupBox("2×2 Payoff Matrix"); mgl = QGridLayout(mat_grp)
        mgl.addWidget(QLabel(""), 0, 0); mgl.addWidget(QLabel("<b>P2: Left</b>"), 0, 1); mgl.addWidget(QLabel("<b>P2: Right</b>"), 0, 2)
        mgl.addWidget(QLabel("<b>P1: Top</b>"), 1, 0); mgl.addWidget(QLabel("<b>P1: Bottom</b>"), 2, 0)
        self.pay_cells = {}; self.pay_cell_widgets = {}
        positions = {(1,1): "TL", (1,2): "TR", (2,1): "BL", (2,2): "BR"}
        for (r,c), key in positions.items():
            frame = QFrame(); frame.setStyleSheet("background:#1a1a2e; border:1px solid #2a2a4a; border-radius:4px; padding:4px;")
            fl = QHBoxLayout(frame); fl.setContentsMargins(4,4,4,4)
            s1 = QSpinBox(); s1.setRange(-99,99); s1.setValue(0); s1.setPrefix("P1:")
            s2 = QSpinBox(); s2.setRange(-99,99); s2.setValue(0); s2.setPrefix("P2:")
            fl.addWidget(s1); fl.addWidget(s2); self.pay_cells[key] = (s1, s2); self.pay_cell_widgets[key] = frame; mgl.addWidget(frame, r, c)
        left.addWidget(mat_grp)
        ba = QPushButton("🔍 Analyze"); ba.clicked.connect(self._pay_analyze); left.addWidget(ba); left.addStretch()
        right = QVBoxLayout(); self.pay_results = QTextEdit(); self.pay_results.setReadOnly(True); self.pay_results.setFont(QFont("Consolas", 11)); right.addWidget(self.pay_results)
        outer.addLayout(left, 2); outer.addLayout(right, 3); tabs.addTab(w, "📊 Payoff Matrix")

    def _pay_load_preset(self, name):
        if name == "Custom" or name not in PAYOFF_PRESETS: return
        pr = PAYOFF_PRESETS[name]; vals = {"TL": pr["payoffs"][0][0], "TR": pr["payoffs"][0][1], "BL": pr["payoffs"][1][0], "BR": pr["payoffs"][1][1]}
        for key, (s1, s2) in self.pay_cells.items(): s1.setValue(vals[key][0]); s2.setValue(vals[key][1])
        for w in self.pay_cell_widgets.values(): w.setStyleSheet("background:#1a1a2e; border:1px solid #2a2a4a; border-radius:4px; padding:4px;")

    def _pay_analyze(self):
        TL = (self.pay_cells["TL"][0].value(), self.pay_cells["TL"][1].value()); TR = (self.pay_cells["TR"][0].value(), self.pay_cells["TR"][1].value())
        BL = (self.pay_cells["BL"][0].value(), self.pay_cells["BL"][1].value()); BR = (self.pay_cells["BR"][0].value(), self.pay_cells["BR"][1].value())
        a, b = TL; c, d = TR; e, f = BL; g, h = BR
        for w in self.pay_cell_widgets.values(): w.setStyleSheet("background:#1a1a2e; border:1px solid #2a2a4a; border-radius:4px; padding:4px;")
        results = ['<h3 style="color:#64ffda">📊 Analysis</h3>']
        sums = [a+b, c+d, e+f, g+h]
        if len(set(sums)) == 1 and sums[0] == 0: results.append('<p style="color:#ff8a80"><b>Zero-Sum Game</b></p>')
        elif len(set(sums)) == 1: results.append(f'<p style="color:#ffcc80"><b>Constant-Sum Game</b></p>')
        else: results.append('<p style="color:#69f0ae"><b>Non-Zero-Sum Game</b></p>')
        ne_pure = []
        if a >= e and b >= d: ne_pure.append(("TL", TL))
        if c >= g and d >= b: ne_pure.append(("TR", TR))
        if e >= a and f >= h: ne_pure.append(("BL", BL))
        if g >= c and h >= f: ne_pure.append(("BR", BR))
        for name, payoff in ne_pure: self.pay_cell_widgets[name].setStyleSheet("background:#1b5e20; border:2px solid #69f0ae; border-radius:4px; padding:4px;")
        results.append('<p style="color:#64ffda"><b>Pure Nash Equilibria:</b></p><ul>')
        if ne_pure:
            for name, payoff in ne_pure: results.append(f'<li style="color:#69f0ae">({name}) → {payoff}</li>')
        else: results.append('<li style="color:#ff5252">None</li>')
        results.append('</ul>')
        self.pay_results.setHtml("".join(results))

    # ══════════════════════════════════════════════════════════
    #  TAB 6 — EVOLUTIONARY SIMULATION
    # ══════════════════════════════════════════════════════════
    def _build_evo_tab(self, tabs):
        w = QWidget(); outer = QVBoxLayout(w); outer.setContentsMargins(10,10,10,10)
        top = QHBoxLayout()
        param_grp = QGroupBox("Parameters"); pl = QGridLayout(param_grp)
        pl.addWidget(QLabel("Population:"), 0, 0); self.evo_pop = QSpinBox(); self.evo_pop.setRange(10,1000); self.evo_pop.setValue(100); pl.addWidget(self.evo_pop, 0, 1)
        pl.addWidget(QLabel("Generations:"), 0, 2); self.evo_gens = QSpinBox(); self.evo_gens.setRange(10,2000); self.evo_gens.setValue(200); pl.addWidget(self.evo_gens, 0, 3)
        pl.addWidget(QLabel("Mutation %:"), 1, 0); self.evo_mut = QSpinBox(); self.evo_mut.setRange(0,50); self.evo_mut.setValue(2); self.evo_mut.setSuffix("%"); pl.addWidget(self.evo_mut, 1, 1)
        pl.addWidget(QLabel("Rounds/Match:"), 1, 2); self.evo_match = QSpinBox(); self.evo_match.setRange(1,200); self.evo_match.setValue(10); pl.addWidget(self.evo_match, 1, 3)
        top.addWidget(param_grp, 3)
        comp_grp = QGroupBox("Initial Population %"); cl = QGridLayout(comp_grp); self.evo_counts = {}
        strategies = ["AllC", "AllD", "TfT", "Grim", "Pavlov", "Rand"]; defaults = [20, 20, 25, 15, 15, 5]
        for i, (s, d) in enumerate(zip(strategies, defaults)): lbl = QLabel(s+":"); sb = QSpinBox(); sb.setRange(0,100); sb.setValue(d); sb.setSuffix("%"); self.evo_counts[s] = sb; cl.addWidget(lbl,i,0); cl.addWidget(sb,i,1)
        top.addWidget(comp_grp, 2); outer.addLayout(top)
        btn_row = QHBoxLayout()
        self.evo_btn_run = QPushButton("▶ Run"); self.evo_btn_run.clicked.connect(self._evo_run)
        self.evo_btn_step = QPushButton("⏭ Step"); self.evo_btn_step.clicked.connect(self._evo_step)
        self.evo_btn_stop = QPushButton("⏹ Stop"); self.evo_btn_stop.clicked.connect(self._evo_stop); self.evo_btn_stop.setEnabled(False)
        brst = QPushButton("↺ Reset"); brst.clicked.connect(self._evo_reset)
        btn_row.addWidget(self.evo_btn_run); btn_row.addWidget(self.evo_btn_step); btn_row.addWidget(self.evo_btn_stop); btn_row.addWidget(brst); outer.addLayout(btn_row)
        self.evo_status = QLabel("Ready"); self.evo_status.setStyleSheet("color:#64ffda;font-weight:bold;font-size:13px;"); outer.addWidget(self.evo_status)
        bottom = QHBoxLayout(); self.evo_chart = LineChart(); bottom.addWidget(self.evo_chart, 2)
        self.evo_pop_display = QTextEdit(); self.evo_pop_display.setReadOnly(True); self.evo_pop_display.setFont(QFont("Consolas",10)); self.evo_pop_display.setMaximumWidth(250); bottom.addWidget(self.evo_pop_display, 1)
        outer.addLayout(bottom); tabs.addTab(w, "🧬 Evolution")
        self.evo_timer = QTimer(); self.evo_timer.timeout.connect(self._evo_step); self.evo_state = {"pop": [], "gen": 0, "chart_data": {}}

    def _evo_get_action(self, strategy, my_hist, opp_hist):
        if strategy == "AllC": return 'C'
        if strategy == "AllD": return 'D'
        if strategy == "TfT": return opp_hist[-1] if opp_hist else 'C'
        if strategy == "Grim": return 'D' if 'D' in opp_hist else 'C'
        if strategy == "Pavlov": return 'C' if not my_hist else ('C' if my_hist[-1]==opp_hist[-1] else 'D')
        if strategy == "Rand": return random.choice(['C','D'])
        return 'C'

    def _evo_init_pop(self):
        pop_size = self.evo_pop.value(); counts = {s: sb.value() for s, sb in self.evo_counts.items()}; total = sum(counts.values()); pop = []
        for s, cnt in counts.items(): n = int(pop_size * cnt / total) if total > 0 else 0; pop.extend([s]*n)
        while len(pop) < pop_size: pop.append(random.choice(list(counts.keys())))
        while len(pop) > pop_size: pop.pop()
        random.shuffle(pop); return pop

    def _evo_play_match(self, s1, s2, rounds):
        h1, h2 = [], []; sc1, sc2 = 0, 0
        for _ in range(rounds):
            a1 = self._evo_get_action(s1, h1, h2); a2 = self._evo_get_action(s2, h2, h1)
            p1, p2 = (3,3) if a1=='C' and a2=='C' else (0,5) if a1=='C' and a2=='D' else (5,0) if a1=='D' and a2=='C' else (1,1)
            sc1 += p1; sc2 += p2; h1.append(a1); h2.append(a2)
        return sc1, sc2

    def _evo_step(self):
        st = self.evo_state; pop = st["pop"]; pop_size = len(pop)
        if not pop: return
        match_len = self.evo_match.value(); mut_rate = self.evo_mut.value()/100.0; strategies = list(self.evo_counts.keys())
        fitness = [0]*pop_size
        for i in range(pop_size):
            for j in range(pop_size):
                if i!=j: s1, _ = self._evo_play_match(pop[i], pop[j], match_len); fitness[i] += s1
        total_fit = sum(fitness); new_pop = []
        if total_fit == 0: new_pop = [random.choice(strategies) for _ in range(pop_size)]
        else:
            probs = [f/total_fit for f in fitness]
            for _ in range(pop_size):
                r = random.random(); cum = 0; chosen = pop[0]
                for idx, p in enumerate(probs):
                    cum += p
                    if r <= cum: chosen = pop[idx]; break
                if random.random() < mut_rate: chosen = random.choice(strategies)
                new_pop.append(chosen)
        st["pop"] = new_pop; st["gen"] += 1; counts = {s: 0 for s in strategies}
        for p in new_pop: counts[p] += 1
        for s in strategies:
            if s not in st["chart_data"]: st["chart_data"][s] = []
            st["chart_data"][s].append((st["gen"], counts.get(s,0)))
        colors = {"AllC": QColor(100,200,255), "AllD": QColor(255,120,120), "TfT": QColor(120,255,120), "Grim": QColor(255,210,80), "Pavlov": QColor(200,130,255), "Rand": QColor(180,180,180)}
        self.evo_chart.set_series({s: st["chart_data"][s] for s in strategies if st["chart_data"][s]}, colors)
        pop_str = f"Generation {st['gen']}\n{'='*20}\n"
        for s in strategies: pct = (counts.get(s,0)/pop_size)*100; pop_str += f"{s:>6}: {'█'*int(pct/5)} {pct:.1f}%\n"
        self.evo_pop_display.setText(pop_str); self.evo_status.setText(f"Running... Gen {st['gen']}")
        if st["gen"] >= self.evo_gens.value(): self._evo_stop()

    def _evo_run(self):
        if not self.evo_state["pop"]: self.evo_state["pop"] = self._evo_init_pop()
        self.evo_btn_run.setEnabled(False); self.evo_btn_step.setEnabled(False); self.evo_btn_stop.setEnabled(True); self.evo_timer.start(50)

    def _evo_stop(self):
        self.evo_timer.stop(); self.evo_btn_run.setEnabled(True); self.evo_btn_step.setEnabled(True); self.evo_btn_stop.setEnabled(False)
        self.evo_status.setText(f"Stopped at Gen {self.evo_state['gen']}")

    def _evo_reset(self):
        self._evo_stop(); self.evo_state = {"pop": [], "gen": 0, "chart_data": {}}; self.evo_chart.clear(); self.evo_pop_display.clear(); self.evo_status.setText("Ready")

    # ══════════════════════════════════════════════════════════
    #  TAB 7 — MONTY HALL PROBLEM
    # ══════════════════════════════════════════════════════════
    def _build_monty_hall_tab(self, tabs):
        w = QWidget(); outer = QHBoxLayout(w); outer.setContentsMargins(10,10,10,10)
        left = QVBoxLayout()
        grp = QGroupBox("Game Rules"); gl = QVBoxLayout(grp)
        gl.addWidget(QLabel("1. Pick a door (1, 2, or 3)\n2. Monty opens a goat door\n3. Choose to Stay or Switch"))
        left.addWidget(grp)
        
        btn_row = QHBoxLayout()
        b1 = QPushButton("▶ New Game"); b1.clicked.connect(self._mh_new_game)
        b2 = QPushButton("⚡ Auto-Sim 100"); b2.clicked.connect(lambda: self._mh_auto_sim(100))
        b3 = QPushButton("⚡ Auto-Sim 1000"); b3.clicked.connect(lambda: self._mh_auto_sim(1000))
        btn_row.addWidget(b1); btn_row.addWidget(b2); btn_row.addWidget(b3)
        left.addLayout(btn_row)
        
        self.mh_status = QLabel("Click 'New Game' to start"); self.mh_status.setStyleSheet("font-size:14px;font-weight:bold;color:#64ffda;"); left.addWidget(self.mh_status)
        
        stats_grp = QGroupBox("Statistics"); sl = QGridLayout(stats_grp)
        sl.addWidget(QLabel("Stay Wins:"), 0, 0); self.mh_stay_wins = QLabel("0"); self.mh_stay_wins.setStyleSheet("font-weight:bold;color:#ff5252;"); sl.addWidget(self.mh_stay_wins, 0, 1)
        sl.addWidget(QLabel("Stay Total:"), 0, 2); self.mh_stay_total = QLabel("0"); sl.addWidget(self.mh_stay_total, 0, 3)
        sl.addWidget(QLabel("Switch Wins:"), 1, 0); self.mh_switch_wins = QLabel("0"); self.mh_switch_wins.setStyleSheet("font-weight:bold;color:#69f0ae;"); sl.addWidget(self.mh_switch_wins, 1, 1)
        sl.addWidget(QLabel("Switch Total:"), 1, 2); self.mh_switch_total = QLabel("0"); sl.addWidget(self.mh_switch_total, 1, 3)
        left.addWidget(stats_grp); left.addStretch()

        right = QVBoxLayout()
        self.mh_doors_grp = QGroupBox("Doors"); dl = QHBoxLayout(self.mh_doors_grp)
        self.mh_doors = []
        for i in range(3):
            btn = QPushButton(f"Door {i+1}\n?"); btn.setFixedSize(100, 80); btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
            btn.clicked.connect(lambda checked, idx=i: self._mh_pick(idx))
            btn.setStyleSheet("background:#1a1a2e; border:2px solid #2a2a4a; border-radius:6px; color:#ccd;")
            self.mh_doors.append(btn); dl.addWidget(btn)
        right.addWidget(self.mh_doors_grp)

        self.mh_action_grp = QGroupBox("Decision"); al = QHBoxLayout(self.mh_action_grp); self.mh_action_grp.setVisible(False)
        self.mh_btn_stay = QPushButton("🚪 Stay"); self.mh_btn_stay.clicked.connect(lambda: self._mh_decision(False))
        self.mh_btn_switch = QPushButton("🔄 Switch"); self.mh_btn_switch.clicked.connect(lambda: self._mh_decision(True))
        self.mh_btn_stay.setStyleSheet("background:#ff5252; color:white; font-weight:bold; padding:10px;")
        self.mh_btn_switch.setStyleSheet("background:#69f0ae; color:black; font-weight:bold; padding:10px;")
        al.addWidget(self.mh_btn_stay); al.addWidget(self.mh_btn_switch); right.addWidget(self.mh_action_grp)
        
        note = QGroupBox("Game Theory Connection"); nl = QVBoxLayout(note)
        nl.addWidget(QLabel("Bayesian Updating:\nInitially, all doors have 1/3 chance of car.\nAfter Monty reveals a goat, the probability\nshifts: your door still has 1/3, but the\nother unopened door now has 2/3.\n\n<b>Always Switch!</b> It doubles your win rate."))
        right.addWidget(note); right.addStretch()

        outer.addLayout(left, 1); outer.addLayout(right, 2); tabs.addTab(w, "🚪 Monty Hall")
        self.mh_state = {"phase": "idle", "car": -1, "chosen": -1, "revealed": -1, "stats": {"stay_wins": 0, "stay_total": 0, "switch_wins": 0, "switch_total": 0}}

    def _mh_new_game(self):
        self.mh_state["phase"] = "pick"; self.mh_state["car"] = random.randint(0, 2); self.mh_state["chosen"] = -1; self.mh_state["revealed"] = -1
        for btn in self.mh_doors: btn.setText("?\n🚪"); btn.setStyleSheet("background:#1a1a2e; border:2px solid #2a2a4a; border-radius:6px; color:#ccd;"); btn.setEnabled(True)
        self.mh_action_grp.setVisible(False); self.mh_status.setText("Pick a door!")

    def _mh_pick(self, idx):
        if self.mh_state["phase"] != "pick": return
        self.mh_state["chosen"] = idx; self.mh_state["phase"] = "decide"
        self.mh_doors[idx].setStyleSheet("background:#16213e; border:3px solid #64ffda; border-radius:6px; color:#64ffda;")
        possibilities = [i for i in range(3) if i != idx and i != self.mh_state["car"]]
        reveal = random.choice(possibilities)
        self.mh_state["revealed"] = reveal
        self.mh_doors[reveal].setText("🐐\nGoat"); self.mh_doors[reveal].setEnabled(False)
        self.mh_doors[reveal].setStyleSheet("background:#263238; border:2px solid #37474f; border-radius:6px; color:#ef5350;")
        self.mh_action_grp.setVisible(True); self.mh_status.setText(f"You picked Door {idx+1}. Monty reveals a goat at Door {reveal+1}.\nStay or Switch?")

    def _mh_decision(self, do_switch):
        if self.mh_state["phase"] != "decide": return
        self.mh_state["phase"] = "done"; self.mh_action_grp.setVisible(False)
        final_choice = self.mh_state["chosen"] if not do_switch else [i for i in range(3) if i != self.mh_state["chosen"] and i != self.mh_state["revealed"]][0]
        won = final_choice == self.mh_state["car"]
        if do_switch:
            self.mh_state["stats"]["switch_total"] += 1
            if won: self.mh_state["stats"]["switch_wins"] += 1
        else:
            self.mh_state["stats"]["stay_total"] += 1
            if won: self.mh_state["stats"]["stay_wins"] += 1
        for i in range(3):
            if i == self.mh_state["car"]: self.mh_doors[i].setText("🚗\nCar!"); self.mh_doors[i].setStyleSheet("background:#1b5e20; border:2px solid #69f0ae; border-radius:6px; color:#69f0ae;")
            elif i == self.mh_state["revealed"]: pass
            else: self.mh_doors[i].setText("🐐\nGoat"); self.mh_doors[i].setStyleSheet("background:#263238; border:2px solid #37474f; border-radius:6px; color:#ef5350;")
            self.mh_doors[i].setEnabled(False)
        result_text = "🎉 You won the car!" if won else "😢 You got a goat."
        method = "Switched" if do_switch else "Stayed"
        self.mh_status.setText(f"You {method}. {result_text}")
        self._mh_update_stats()

    def _mh_update_stats(self):
        s = self.mh_state["stats"]
        self.mh_stay_wins.setText(str(s["stay_wins"])); self.mh_stay_total.setText(str(s["stay_total"]))
        self.mh_switch_wins.setText(str(s["switch_wins"])); self.mh_switch_total.setText(str(s["switch_total"]))
        if s["stay_total"] > 0: self.mh_stay_wins.setText(f"{s['stay_wins']} ({100*s['stay_wins']/s['stay_total']:.1f}%)")
        if s["switch_total"] > 0: self.mh_switch_wins.setText(f"{s['switch_wins']} ({100*s['switch_wins']/s['switch_total']:.1f}%)")

    def _mh_auto_sim(self, n):
        for _ in range(n):
            car = random.randint(0, 2); chosen = random.randint(0, 2)
            revealed = random.choice([i for i in range(3) if i != chosen and i != car])
            switch_choice = [i for i in range(3) if i != chosen and i != revealed][0]
            self.mh_state["stats"]["switch_total"] += 1
            if switch_choice == car: self.mh_state["stats"]["switch_wins"] += 1
            self.mh_state["stats"]["stay_total"] += 1
            if chosen == car: self.mh_state["stats"]["stay_wins"] += 1
        self._mh_update_stats()
        self.mh_status.setText(f"Simulated {n} games. Check stats!")

    # ══════════════════════════════════════════════════════════
    #  TAB 8 — ULTIMATUM GAME
    # ══════════════════════════════════════════════════════════
    def _build_ultimatum_tab(self, tabs):
        w = QWidget(); outer = QHBoxLayout(w); outer.setContentsMargins(10,10,10,10)
        left = QVBoxLayout()
        role_grp = QGroupBox("Your Role"); rl = QVBoxLayout(role_grp)
        self.ult_role_prop = QRadioButton("Proposer (Split $10)"); self.ult_role_prop.setChecked(True)
        self.ult_role_resp = QRadioButton("Responder (Accept/Reject)")
        rl.addWidget(self.ult_role_prop); rl.addWidget(self.ult_role_resp)
        left.addWidget(role_grp)

        ai_grp = QGroupBox("Opponent Personality"); al = QVBoxLayout(ai_grp)
        self.ult_ai = QComboBox(); self.ult_ai.addItems(["Rational (Accepts ≥$1)", "Fair (Accepts ≥$4)", "Spiteful (Accepts ≥$5)"])
        al.addWidget(self.ult_ai); left.addWidget(ai_grp)

        self.ult_offer_grp = QGroupBox("Propose a Split (P1 : P2)"); ol = QVBoxLayout(self.ult_offer_grp)
        self.ult_slider = QSlider(Qt.Horizontal); self.ult_slider.setRange(0, 10); self.ult_slider.setValue(5); self.ult_slider.setTickPosition(QSlider.TicksBelow); self.ult_slider.setTickInterval(1)
        self.ult_slider_label = QLabel("You: $5 | Opponent: $5"); self.ult_slider_label.setStyleSheet("font-weight:bold;font-size:14px;color:#64ffda;")
        self.ult_slider.valueChanged.connect(self._ult_update_slider_label)
        ol.addWidget(self.ult_slider_label); ol.addWidget(self.ult_slider)
        left.addWidget(self.ult_offer_grp)

        self.ult_offer_display = QLabel(""); self.ult_offer_display.setStyleSheet("font-weight:bold;font-size:14px;color:#ffcc80;"); left.addWidget(self.ult_offer_display)

        btn_row = QHBoxLayout()
        bp = QPushButton("▶ Play Round"); bp.clicked.connect(self._ult_play)
        brst = QPushButton("↺ Reset Stats"); brst.clicked.connect(self._ult_reset)
        btn_row.addWidget(bp); btn_row.addWidget(brst); left.addLayout(btn_row)

        self.ult_status = QLabel(""); self.ult_status.setWordWrap(True); self.ult_status.setStyleSheet("font-size:13px;"); left.addWidget(self.ult_status)
        left.addStretch()

        right = QVBoxLayout(); self.ult_history = QTextEdit(); self.ult_history.setReadOnly(True); self.ult_history.setFont(QFont("Consolas", 10)); right.addWidget(self.ult_history)
        note = QGroupBox("Game Theory Connection"); nl = QVBoxLayout(note)
        nl.addWidget(QLabel("Subgame perfect equilibrium:\nRational theory predicts the Proposer offers $1\nand the Responder accepts (since $1 > $0).\n\nHowever, behavioral economics shows humans\nreject unfair offers due to fairness/spite.\nThis violates pure rationality assumptions!"))
        right.addWidget(note)
        outer.addLayout(left, 1); outer.addLayout(right, 2); tabs.addTab(w, "💰 Ultimatum Game")
        self.ult_state = {"p1_total": 0, "p2_total": 0, "round": 0}

    def _ult_update_slider_label(self, val):
        self.ult_slider_label.setText(f"You: ${val} | Opponent: ${10-val}")

    def _ult_play(self):
        is_proposer = self.ult_role_prop.isChecked()
        ai_type = self.ult_ai.currentText()
        self.ult_state["round"] += 1
        r = self.ult_state["round"]
        
        if is_proposer:
            p1_offer = self.ult_slider.value(); p2_offer = 10 - p1_offer
            threshold = 1 if "Rational" in ai_type else 4 if "Fair" in ai_type else 5
            accepted = p2_offer >= threshold
            if accepted:
                self.ult_state["p1_total"] += p1_offer; self.ult_state["p2_total"] += p2_offer
                self.ult_status.setText(f"Opponent ACCEPTED your offer of ${p2_offer}.")
                self.ult_history.append(f"R{r:>3} | Offer: ${p1_offer}/${p2_offer} | ✅ Accepted | Tot: ${self.ult_state['p1_total']}/${self.ult_state['p2_total']}")
            else:
                self.ult_status.setText(f"Opponent REJECTED your offer of ${p2_offer}. Both get $0.")
                self.ult_history.append(f"R{r:>3} | Offer: ${p1_offer}/${p2_offer} | ❌ Rejected | Tot: ${self.ult_state['p1_total']}/${self.ult_state['p2_total']}")
        else:
            if "Rational" in ai_type: p1_offer = 9
            elif "Fair" in ai_type: p1_offer = 5
            else: p1_offer = random.choice([4, 5, 6])
            p2_offer = 10 - p1_offer
            self.ult_offer_display.setText(f"Opponent offers: You get ${p2_offer}, they keep ${p1_offer}.\nDo you accept?")
            accepted = True 
            if accepted:
                self.ult_state["p1_total"] += p1_offer; self.ult_state["p2_total"] += p2_offer
                self.ult_status.setText(f"You ACCEPTED offer of ${p2_offer}.")
                self.ult_history.append(f"R{r:>3} | Offer: ${p1_offer}/${p2_offer} | ✅ Accepted | Tot: ${self.ult_state['p1_total']}/${self.ult_state['p2_total']}")
            else:
                self.ult_history.append(f"R{r:>3} | Offer: ${p1_offer}/${p2_offer} | ❌ Rejected | Tot: ${self.ult_state['p1_total']}/${self.ult_state['p2_total']}")

    def _ult_reset(self):
        self.ult_state = {"p1_total": 0, "p2_total": 0, "round": 0}; self.ult_history.clear(); self.ult_status.setText("")

    # ══════════════════════════════════════════════════════════
    #  TAB 9 — HOTELLING'S GAME
    # ══════════════════════════════════════════════════════════
    def _build_hotelling_tab(self, tabs):
        w = QWidget(); outer = QVBoxLayout(w); outer.setContentsMargins(10,10,10,10)
        top = QHBoxLayout()
        p1_grp = QGroupBox("Vendor 1 (Blue)"); p1l = QVBoxLayout(p1_grp)
        self.hot_p1_slider = QSlider(Qt.Horizontal); self.hot_p1_slider.setRange(0, 100); self.hot_p1_slider.setValue(25)
        self.hot_p1_label = QLabel("Position: 25%"); self.hot_p1_label.setStyleSheet("color:#42a5f5;font-weight:bold;")
        self.hot_p1_slider.valueChanged.connect(lambda v: (self.hot_p1_label.setText(f"Position: {v}%"), self._hot_update_vis()))
        p1l.addWidget(self.hot_p1_label); p1l.addWidget(self.hot_p1_slider); top.addWidget(p1_grp)

        p2_grp = QGroupBox("Vendor 2 (Red)"); p2l = QVBoxLayout(p2_grp)
        self.hot_p2_slider = QSlider(Qt.Horizontal); self.hot_p2_slider.setRange(0, 100); self.hot_p2_slider.setValue(75)
        self.hot_p2_label = QLabel("Position: 75%"); self.hot_p2_label.setStyleSheet("color:#ef5350;font-weight:bold;")
        self.hot_p2_slider.valueChanged.connect(lambda v: (self.hot_p2_label.setText(f"Position: {v}%"), self._hot_update_vis()))
        p2l.addWidget(self.hot_p2_label); p2l.addWidget(self.hot_p2_slider); top.addWidget(p2_grp)

        mode_grp = QGroupBox("Mode"); ml = QVBoxLayout(mode_grp)
        self.hot_mode_manual = QRadioButton("Manual"); self.hot_mode_manual.setChecked(True)
        self.hot_mode_ai = QRadioButton("Play vs AI (AI adapts)")
        ml.addWidget(self.hot_mode_manual); ml.addWidget(self.hot_mode_ai); top.addWidget(mode_grp)

        btn_row = QHBoxLayout()
        bp = QPushButton("▶ Play Round"); bp.clicked.connect(self._hot_play_round)
        bn = QPushButton("🔬 Nash Equilibrium"); bn.clicked.connect(self._hot_nash)
        brst = QPushButton("↺ Reset Score"); brst.clicked.connect(self._hot_reset)
        btn_row.addWidget(bp); btn_row.addWidget(bn); btn_row.addWidget(brst)
        
        # BUG FIX: Use addLayout instead of addWidget for btn_row
        top.addLayout(btn_row); outer.addLayout(top)

        self.hot_beach = BeachWidget(); outer.addWidget(self.hot_beach)

        bottom = QHBoxLayout()
        self.hot_result = QLabel("Market Share: P1 50% | P2 50% | Score: P1 0 - P2 0")
        self.hot_result.setStyleSheet("font-size:15px;font-weight:bold;color:#64ffda;"); bottom.addWidget(self.hot_result)
        outer.addLayout(bottom)

        note = QGroupBox("Game Theory Connection"); nl = QVBoxLayout(note)
        nl.addWidget(QLabel("Hotelling's Law / Median Voter Theorem:\nTwo competitors on a line (beach, political spectrum)\nwill naturally cluster in the center to maximize\ntheir share. This explains why political parties\nconverge to the center and similar stores cluster.\n\nNash Equilibrium: Both at exactly 50%."))
        outer.addWidget(note)

        self.hot_state = {"p1_score": 0, "p2_score": 0}; self._hot_update_vis()
        tabs.addTab(w, "🏖️ Hotelling")

    def _hot_update_vis(self):
        self.hot_beach.set_positions(self.hot_p1_slider.value(), self.hot_p2_slider.value())

    def _hot_play_round(self):
        p1 = self.hot_p1_slider.value(); p2 = self.hot_p2_slider.value()
        if self.hot_mode_ai.isChecked():
            if p1 < 50: p2 = min(100, p1 + 1)
            elif p1 > 50: p2 = max(0, p1 - 1)
            else: p2 = 50
            self.hot_p2_slider.setValue(p2)
        
        mid = (p1 + p2) / 2.0
        share1 = mid if p1 < p2 else 100 - mid
        share2 = 100 - share1
        
        self.hot_state["p1_score"] += share1; self.hot_state["p2_score"] += share2
        self.hot_result.setText(f"Market Share: P1 {share1:.1f}% | P2 {share2:.1f}% | Score: P1 {self.hot_state['p1_score']:.0f} - P2 {self.hot_state['p2_score']:.0f}")
        self._hot_update_vis()

    def _hot_nash(self):
        self.hot_p1_slider.setValue(50); self.hot_p2_slider.setValue(50)
        self.hot_result.setText("Nash Equilibrium reached! Both at center. Share: 50% | 50%")
        self._hot_update_vis()

    def _hot_reset(self):
        self.hot_state = {"p1_score": 0, "p2_score": 0}; self._hot_play_round()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GameTheoryApp()
    window.show()
    sys.exit(app.exec())