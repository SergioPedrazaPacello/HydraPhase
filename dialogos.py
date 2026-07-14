"""Dialogos con estilo unificado (equivalente al dialogos.py de ThermoPhase)."""
from PyQt6.QtWidgets import QMessageBox
from estilo import GRAY_RES, BORDER, FONT_F, FS, TEXT, QSS_BTN

_QSS = (f'QMessageBox{{background:{GRAY_RES};}}'
        f'QLabel{{color:{TEXT};font-family:"{FONT_F}";font-size:{FS}pt;'
        f'background:transparent;}}') + QSS_BTN


def _base(parent, icono, titulo, texto):
    m = QMessageBox(parent)
    m.setIcon(icono)
    m.setWindowTitle(titulo)
    m.setText(texto)
    m.setStyleSheet(_QSS)
    return m


def info(parent, texto, titulo="Informacion"):
    _base(parent, QMessageBox.Icon.Information, titulo, texto).exec()


def advertencia(parent, texto, titulo="Advertencia"):
    _base(parent, QMessageBox.Icon.Warning, titulo, texto).exec()


def error(parent, texto, titulo="Error"):
    _base(parent, QMessageBox.Icon.Critical, titulo, texto).exec()


def confirmar(parent, texto, titulo="Confirmar") -> bool:
    m = _base(parent, QMessageBox.Icon.Question, titulo, texto)
    m.setStandardButtons(QMessageBox.StandardButton.Yes |
                         QMessageBox.StandardButton.No)
    m.setDefaultButton(QMessageBox.StandardButton.No)
    return m.exec() == QMessageBox.StandardButton.Yes
