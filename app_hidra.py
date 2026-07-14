"""
HydraPhase - Simulador de Hidraulica de Perforacion
Modelo reologico: Ley de Potencia (Power Law)

Ejecutar:  python app_hidra.py
"""
import sys, os, copy

import matplotlib
matplotlib.use('QtAgg')

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QTabWidget, QStatusBar, QLabel,
                             QCheckBox)
from PyQt6.QtGui import QFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from estilo import WHITE, GRAY_LBL, BORDER, TEXT, FONT_F, FS
from tab_datos import TabDatos
from tab_resultados import TabResultados
from tab_graficas import TabGraficas
import dialogos as dlg

VERSION = "1.0"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"HydraPhase {VERSION}  /  Hidraulica de Perforacion")
        self.resize(1280, 860)
        self.setMinimumSize(1120, 760)
        self._build()

    def _build(self):
        cw = QWidget()
        self.setCentralWidget(cw)
        lay = QVBoxLayout(cw)
        lay.setContentsMargins(4, 4, 4, 2)
        lay.setSpacing(3)

        barra = QHBoxLayout()
        self.ck_comp = QCheckBox(
            "Comparar con el mismo pozo sin washout  "
            "(agrega un segundo escenario a las graficas)")
        self.ck_comp.setStyleSheet(
            f'font-family:"{FONT_F}";font-size:{FS}pt;color:{TEXT};')
        self.ck_comp.setChecked(True)
        barra.addWidget(self.ck_comp)
        barra.addStretch()
        lay.addLayout(barra)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(
            f'QTabWidget::pane{{border:1px solid {BORDER};}}'
            f'QTabBar::tab{{background:{GRAY_LBL};color:{TEXT};'
            f'padding:5px 16px;border:1px solid {BORDER};border-bottom:none;'
            f'margin-right:1px;font-family:"{FONT_F}";font-size:{FS}pt;}}'
            f'QTabBar::tab:selected{{background:{WHITE};'
            f'border-bottom:1px solid {WHITE};}}')

        self.tab_dat = TabDatos()
        self.tab_res = TabResultados()
        self.tab_gra = TabGraficas()

        self.tabs.addTab(self.tab_dat, "Datos de entrada")
        self.tabs.addTab(self.tab_res, "Resultados")
        self.tabs.addTab(self.tab_gra, "Graficas")
        lay.addWidget(self.tabs)

        self.tab_dat.datos_cambiados.connect(self.calcular)

        sb = QStatusBar()
        sb.setStyleSheet(f'background:{GRAY_LBL};border-top:1px solid {BORDER};')
        self.lbl_sb = QLabel("  Modelo: Ley de Potencia  /  "
                             "Unidades de campo: psi, ft, in, gpm, ppg  /  "
                             "Sin datos cargados")
        self.lbl_sb.setStyleSheet(f'font-family:"{FONT_F}";font-size:9pt;'
                                  f'background:transparent;')
        sb.addPermanentWidget(self.lbl_sb, 1)
        self.setStatusBar(sb)

    # ──────────────────────────────────────────────────────────────
    def calcular(self):
        errs = self.tab_dat.validar()
        if errs:
            dlg.advertencia(self, "No se puede calcular:\n\n  \u2022 " +
                            "\n  \u2022 ".join(errs[:8]))
            self.lbl_sb.setText("  Error en los datos de entrada")
            return

        try:
            pozo = self.tab_dat.get_pozo()
            Q_op = self.tab_dat.get_Q_operacion()
            dbr  = self.tab_dat.get_d_broca()
            Qs   = self.tab_dat.get_caudales()

            self.tab_res.actualizar(pozo, Q_op, dbr, Qs)

            pozo_alt, etq_alt = None, None
            tiene_w = any(h.tipo == "washout" for h in pozo.hoyo)
            if self.ck_comp.isChecked() and tiene_w:
                pozo_alt = self._sin_washout(pozo)
                etq, etq_alt = "Con washout", "Sin washout"
            else:
                etq = "Con washout" if tiene_w else "Sin washout"

            self.tab_gra.actualizar(pozo, Q_op, dbr, Qs,
                                    pozo_alt=pozo_alt, etq=etq, etq_alt=etq_alt)

            r = self.tab_res.res
            self.lbl_sb.setText(
                f"  Ley de Potencia  /  Q = {Q_op:,.0f} gpm  /  "
                f"P bomba = {r.P_bomba:,.1f} psi  /  "
                f"\u0394P broca = {r.broca.dP:,.1f} psi ({r.broca.pct_dP:.1f} %)"
                f"  /  ECD = {r.ECD:.3f} ppg  /  HSI = {r.broca.HSI:.2f}")
        except Exception as e:
            dlg.error(self, f"Error durante el calculo:\n\n"
                            f"{type(e).__name__}: {e}")
            self.lbl_sb.setText("  Error durante el calculo")

    @staticmethod
    def _sin_washout(pozo):
        """Reemplaza los tramos de washout por el diametro del hoyo vecino."""
        p = copy.deepcopy(pozo)
        for i, h in enumerate(p.hoyo):
            if h.tipo == "washout":
                vecino = None
                for j in range(i - 1, -1, -1):
                    if p.hoyo[j].tipo == "hoyo":
                        vecino = p.hoyo[j]; break
                if vecino is None:
                    for j in range(i + 1, len(p.hoyo)):
                        if p.hoyo[j].tipo == "hoyo":
                            vecino = p.hoyo[j]; break
                if vecino:
                    h.ID = vecino.ID
                    h.tipo = "hoyo"
                    h.nombre = "Hoyo abierto"
        return p


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont(FONT_F, FS))
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
