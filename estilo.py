"""Paleta y helpers de estilo - consistente con ThermoPhase."""
from PyQt6.QtWidgets import (QLabel, QTableWidget, QTableWidgetItem,
                             QHeaderView, QAbstractItemView, QPushButton,
                             QDoubleSpinBox, QSpinBox, QFrame)
from PyQt6.QtGui import QColor, QBrush
from PyQt6.QtCore import Qt

WHITE    = "#FFFFFF"
GRAY_TIT = "#A8A8A8"
GRAY_LBL = "#D0D0D0"
GRAY_RES = "#E8E8E8"
GRAY_HDR = "#C8C8C8"
BORDER   = "#888888"
TEXT     = "#000000"
TEXT_DIM = "#555555"
TEXT_RES = "#000080"
AZUL     = "#000080"
ROJO     = "#8B0000"
VERDE    = "#006400"
FONT_F   = "Arial Narrow"
FS       = 10

LBL_SEC = (f'background:{GRAY_LBL};color:{TEXT};font-family:"{FONT_F}";'
           f'font-size:{FS}pt;padding:0px 8px;border:1px solid {BORDER};')
LBL_TIT = (f'background:{GRAY_TIT};color:{TEXT};font-family:"{FONT_F}";'
           f'font-size:{FS}pt;padding:0px 6px;border:1px solid {BORDER};')
QSS_BTN = (f'QPushButton{{background:{GRAY_LBL};color:{TEXT};'
           f'font-family:"{FONT_F}";font-size:{FS}pt;padding:4px 14px;'
           f'border:2px outset {BORDER};}}'
           f'QPushButton:hover{{background:{GRAY_RES};}}'
           f'QPushButton:pressed{{border:2px inset {BORDER};}}'
           f'QPushButton:disabled{{color:{TEXT_DIM};background:{GRAY_RES};}}')
QSS_SPIN = (f'QDoubleSpinBox,QSpinBox{{background:{WHITE};color:{TEXT_RES};'
            f'font-family:"{FONT_F}";font-size:{FS}pt;'
            f'border:1px solid {BORDER};padding:1px 3px;}}')
QSS_TBL = (f'QTableWidget{{background:{WHITE};border:1px solid {BORDER};'
           f'font-family:"{FONT_F}";font-size:{FS}pt;gridline-color:{BORDER};}}'
           f'QHeaderView::section{{background:{GRAY_HDR};border:1px solid {BORDER};'
           f'font-family:"{FONT_F}";font-size:{FS}pt;padding:3px;}}'
           f'QTableWidget::item{{padding:2px 4px;}}')
QSS_COMBO = (f'QComboBox{{background:{WHITE};color:{TEXT};'
             f'font-family:"{FONT_F}";font-size:{FS}pt;'
             f'border:1px solid {BORDER};padding:2px 4px;}}')
QSS_GROUP = (f'QGroupBox{{background:{GRAY_RES};border:1px solid {BORDER};'
             f'font-family:"{FONT_F}";font-size:{FS}pt;margin-top:10px;'
             f'padding-top:8px;}}'
             f'QGroupBox::title{{subcontrol-origin:margin;left:8px;'
             f'padding:0 4px;background:{GRAY_LBL};border:1px solid {BORDER};}}')


def _brush(c):
    return QBrush(QColor(c), Qt.BrushStyle.SolidPattern)


def cell(text, bg=WHITE, color=TEXT,
         align=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
         editable=False):
    it = QTableWidgetItem(str(text))
    it.setTextAlignment(align)
    it.setBackground(_brush(bg))
    it.setForeground(_brush(color))
    if not editable:
        it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
    return it


def seccion(txt, alto=22):
    l = QLabel(txt)
    l.setStyleSheet(LBL_SEC)
    l.setFixedHeight(alto)
    l.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    return l


def titulo(txt, alto=22):
    l = QLabel(txt)
    l.setStyleSheet(LBL_TIT)
    l.setFixedHeight(alto)
    l.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return l


def etiqueta(txt, dim=False):
    l = QLabel(txt)
    l.setStyleSheet(f'background:transparent;color:{TEXT_DIM if dim else TEXT};'
                    f'font-family:"{FONT_F}";font-size:{FS}pt;')
    return l


def boton(txt, w=None):
    b = QPushButton(txt)
    b.setStyleSheet(QSS_BTN)
    if w:
        b.setFixedWidth(w)
    return b


def spin(vmin, vmax, val, dec=2, paso=1.0, w=90):
    s = QDoubleSpinBox()
    s.setRange(vmin, vmax)
    s.setDecimals(dec)
    s.setSingleStep(paso)
    s.setValue(val)
    s.setStyleSheet(QSS_SPIN)
    s.setFixedWidth(w)
    s.setAlignment(Qt.AlignmentFlag.AlignRight)
    return s


def ispin(vmin, vmax, val, w=60):
    s = QSpinBox()
    s.setRange(vmin, vmax)
    s.setValue(val)
    s.setStyleSheet(QSS_SPIN)
    s.setFixedWidth(w)
    s.setAlignment(Qt.AlignmentFlag.AlignRight)
    return s


def tabla(filas, cols, headers, stretch_col=0):
    t = QTableWidget(filas, cols)
    t.setHorizontalHeaderLabels(headers)
    t.verticalHeader().setVisible(False)
    t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    t.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
    t.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    t.setStyleSheet(QSS_TBL)
    hh = t.horizontalHeader()
    for c in range(cols):
        hh.setSectionResizeMode(
            c, QHeaderView.ResizeMode.Stretch if c == stretch_col
            else QHeaderView.ResizeMode.Fixed)
    t.setAlternatingRowColors(False)
    return t


def linea():
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet(f'color:{BORDER};')
    return f
