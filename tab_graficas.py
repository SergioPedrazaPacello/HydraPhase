"""Pestana 3 - Graficas (replica las figuras 1 a 6 del paper)."""
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavToolbar
from matplotlib.figure import Figure

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
                             QLabel, QFileDialog)
from PyQt6.QtCore import Qt

from estilo import (GRAY_RES, GRAY_LBL, BORDER, TEXT, TEXT_RES, FONT_F, FS,
                    QSS_COMBO, etiqueta, boton, seccion)
from engine_hidraulica import calcular, barrido_caudal, perfil_utube

GRAFICAS = [
    "1. Presion de bomba vs Caudal",
    "2. Presion parasita vs Caudal (log-log)",
    "3. Presion circulante vs Longitud U-Tube",
    "4. Presion hidrostatica y total vs Longitud U-Tube",
    "5. Caida de presion anular vs Caudal",
    "6. ECD vs Caudal",
    "7. Distribucion de perdidas (barras)",
]

C1, C2 = "#000080", "#8B0000"   # escenario A / escenario B


class TabGraficas(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f'background:{GRAY_RES};')
        self.datos = None       # dict con escenarios
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(5)

        barra = QHBoxLayout()
        barra.addWidget(etiqueta("Grafica:"))
        self.cb = QComboBox()
        self.cb.addItems(GRAFICAS)
        self.cb.setStyleSheet(QSS_COMBO)
        self.cb.setFixedWidth(340)
        self.cb.currentIndexChanged.connect(self._dibujar)
        barra.addWidget(self.cb)
        barra.addStretch()
        self.btn_png = boton("Guardar PNG", 110)
        self.btn_png.clicked.connect(self._guardar)
        barra.addWidget(self.btn_png)
        root.addLayout(barra)

        self.fig = Figure(figsize=(9, 6), dpi=100, facecolor="#FFFFFF")
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setStyleSheet(f'border:1px solid {BORDER};')
        root.addWidget(self.canvas, 1)

        self.tb = NavToolbar(self.canvas, self)
        self.tb.setStyleSheet(f'background:{GRAY_LBL};border:1px solid {BORDER};')
        root.addWidget(self.tb)

    # ──────────────────────────────────────────────────────────────
    def actualizar(self, pozo, Q_op, d_broca, caudales, pozo_alt=None,
                   etq="Escenario", etq_alt=None):
        """pozo_alt: escenario de comparacion opcional (p.ej. con washout)."""
        self.datos = dict(
            pozo=pozo, Q_op=Q_op, d_broca=d_broca, caudales=caudales,
            barrido=barrido_caudal(pozo, caudales, d_broca),
            res=calcular(pozo, Q_op, d_broca),
            etq=etq, etq_alt=etq_alt)
        if pozo_alt is not None:
            self.datos["barrido_alt"] = barrido_caudal(pozo_alt, caudales, d_broca)
            self.datos["res_alt"] = calcular(pozo_alt, Q_op, d_broca)
        self._dibujar()

    def _guardar(self):
        p, _ = QFileDialog.getSaveFileName(self, "Guardar grafica", "grafica.png",
                                           "PNG (*.png)")
        if p:
            self.fig.savefig(p, dpi=200, bbox_inches="tight")

    # ──────────────────────────────────────────────────────────────
    def _dibujar(self):
        self.fig.clear()
        if not self.datos:
            ax = self.fig.add_subplot(111)
            ax.text(0.5, 0.5, "Sin resultados", ha="center", va="center",
                    fontsize=13, color="#888888", transform=ax.transAxes)
            ax.set_xticks([]); ax.set_yticks([])
            self.canvas.draw()
            return

        d = self.datos
        ax = self.fig.add_subplot(111)
        ax.set_facecolor("#FAFAFA")
        ax.grid(True, ls=":", lw=0.7, color="#BBBBBB")

        Qs = [r.Q for r in d["barrido"]]
        alt = "barrido_alt" in d
        Qa = [r.Q for r in d["barrido_alt"]] if alt else None
        i = self.cb.currentIndex()

        def serie(clave):
            return [getattr(r, clave) for r in d["barrido"]]

        def serie_alt(clave):
            return [getattr(r, clave) for r in d["barrido_alt"]]

        if i == 0:
            ax.plot(Qs, serie("P_bomba"), "o-", color=C1, lw=1.8, ms=6,
                    label=d["etq"])
            if alt:
                ax.plot(Qa, serie_alt("P_bomba"), "s--", color=C2, lw=1.8, ms=6,
                        label=d["etq_alt"])
            ax.set_xlabel("Caudal, gpm"); ax.set_ylabel("Presion de bomba, psi")
            ax.set_title("Presion de bomba vs Caudal")

        elif i == 1:
            ax.loglog(Qs, serie("dP_parasita"), "o-", color=C1, lw=1.8, ms=6,
                      label=d["etq"])
            if alt:
                ax.loglog(Qa, serie_alt("dP_parasita"), "s--", color=C2, lw=1.8,
                          ms=6, label=d["etq_alt"])
            ax.set_xlabel("Caudal, gpm"); ax.set_ylabel("Presion parasita, psi")
            ax.set_title("Presion parasita vs Caudal (escala log-log)")
            ax.grid(True, which="both", ls=":", lw=0.7, color="#BBBBBB")

        elif i in (2, 3):
            pf = perfil_utube(d["pozo"], d["res"])
            if i == 2:
                ax.plot(pf["L"], pf["P_dyn"], "-", color=C1, lw=2, label=d["etq"])
                if alt:
                    pfa = perfil_utube(d["pozo"], d["res_alt"]) \
                        if False else None
                ax.set_ylabel("Presion circulante (dinamica), psi")
                ax.set_title(f"Presion circulante vs Longitud U-Tube "
                             f"(Q = {d['Q_op']:.0f} gpm)")
                for nm, L, P in pf["etiquetas"]:
                    ax.annotate(nm, (L, P), textcoords="offset points",
                                xytext=(6, 8), fontsize=7.5, color="#444444")
            else:
                ax.plot(pf["L"], pf["P_hyd"], "-", color="#888888", lw=1.6,
                        label="P hidrostatica (estatica)")
                ax.plot(pf["L"], pf["P_tot"], "-", color=C1, lw=2,
                        label="P hidrostatica + dinamica (circulando)")
                ax.set_ylabel("Presion, psi")
                ax.set_title(f"Perfil de presion a lo largo del circuito "
                             f"(Q = {d['Q_op']:.0f} gpm)")
            ax.set_xlabel("Distancia recorrida desde el standpipe "
                          "(longitud U-Tube), ft")
            # marcar la broca
            Lb = sum(t.longitud for t in d["res"].tramos_int)
            ax.axvline(Lb, color=C2, ls="--", lw=1, alpha=0.7)
            ax.text(Lb, ax.get_ylim()[1] * 0.97, " Broca", color=C2,
                    fontsize=8, va="top")

        elif i == 4:
            ax.plot(Qs, serie("dP_ann"), "o-", color=C1, lw=1.8, ms=6,
                    label=d["etq"])
            if alt:
                ax.plot(Qa, serie_alt("dP_ann"), "s--", color=C2, lw=1.8, ms=6,
                        label=d["etq_alt"])
            ax.set_xlabel("Caudal, gpm")
            ax.set_ylabel("Caida de presion anular total, psi")
            ax.set_title("Caida de presion anular vs Caudal")

        elif i == 5:
            ax.plot(Qs, serie("ECD"), "o-", color=C1, lw=1.8, ms=6, label=d["etq"])
            if alt:
                ax.plot(Qa, serie_alt("ECD"), "s--", color=C2, lw=1.8, ms=6,
                        label=d["etq_alt"])
            rho = d["pozo"].fluido.rho
            ax.axhline(rho, color="#888888", ls=":", lw=1.2)
            ax.text(Qs[0], rho, f" Densidad estatica = {rho:.2f} ppg",
                    fontsize=8, va="bottom", color="#555555")
            ax.set_xlabel("Caudal, gpm")
            ax.set_ylabel("Densidad equivalente de circulacion, ppg")
            ax.set_title("ECD vs Caudal")

        else:
            r = d["res"]
            nombres = ["Superficie"] + [t.nombre for t in r.tramos_int] + \
                      ["Boquillas"] + [t.nombre for t in r.tramos_ann]
            vals = [r.dp_superficie] + [t.dP for t in r.tramos_int] + \
                   [r.broca.dP] + [t.dP for t in r.tramos_ann]
            cols = ["#888888"] + ["#000080"] * len(r.tramos_int) + ["#8B0000"] + \
                   ["#006400"] * len(r.tramos_ann)
            y = range(len(vals))
            ax.barh(list(y), vals, color=cols, edgecolor="#333333", height=0.65)
            ax.set_yticks(list(y))
            ax.set_yticklabels(nombres, fontsize=8)
            ax.invert_yaxis()
            for k, v in enumerate(vals):
                ax.text(v, k, f"  {v:,.1f} psi  ({v/r.P_bomba*100:.1f}%)",
                        va="center", fontsize=8, color="#333333")
            ax.set_xlabel("Caida de presion, psi")
            ax.set_title(f"Distribucion de las perdidas de presion "
                         f"(Q = {d['Q_op']:.0f} gpm  |  "
                         f"P bomba = {r.P_bomba:,.0f} psi)")
            ax.set_xlim(0, max(vals) * 1.45)
            ax.grid(True, axis="x", ls=":", lw=0.7, color="#BBBBBB")

        if i != 6:
            ax.legend(fontsize=8.5, framealpha=0.95)
        for s in ax.spines.values():
            s.set_color("#666666")
        self.fig.tight_layout()
        self.canvas.draw()
