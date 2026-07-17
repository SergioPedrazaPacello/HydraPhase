"""Pestana 3 - Graficas (figuras 1 a 6 del paper + distribucion de perdidas)."""
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.ticker as ticker

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
                             QFileDialog)

from estilo import (GRAY_RES, GRAY_LBL, BORDER, TEXT_DIM, FONT_F,
                    QSS_COMBO, etiqueta, boton)
from engine_hidraulica import calcular, barrido_caudal, perfil_utube

# ── Tipografia y colores identicos a ThermoPhase ───────────────────────
# Se fuerza Arial Narrow en TODOS los elementos del grafico (titulo, ejes,
# ticks, leyenda y anotaciones), no solo en el texto por defecto.
matplotlib.rcParams['font.family']     = 'Arial Narrow'
matplotlib.rcParams['font.sans-serif'] = ['Arial Narrow', 'Arial', 'sans-serif']
matplotlib.rcParams['mathtext.fontset'] = 'custom'
matplotlib.rcParams['mathtext.rm']      = 'Arial Narrow'
matplotlib.rcParams['mathtext.it']      = 'Arial Narrow'
matplotlib.rcParams['axes.unicode_minus'] = False

ROJO  = "#a83218"   # escenario / serie secundaria
AZUL  = "#1a4fa8"   # escenario / serie principal
VERDE = "#2d9d2d"
GRIS  = "#888888"

# Barras: tonos mates de la misma paleta
B_SUP = "#a0a0a0"
B_INT = "#6b83b0"
B_BIT = "#b07a6b"
B_ANN = "#7fa07f"

LW    = 1.0   # lineas finas
MS    = 3.5   # marcadores pequenos

GRAFICAS = [
    "1. Presion de bomba vs Caudal",
    "2. Presion parasita vs Caudal",
    "3. Presion circulante vs Longitud U-Tube",
    "4. Presion hidrostatica y total vs Longitud U-Tube",
    "5. Caida de presion anular vs Caudal",
    "6. ECD vs Caudal",
    "7. Distribucion de las perdidas de presion",
]


class TabGraficas(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f'background:{GRAY_RES};')
        self.datos = None
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

        self.fig = Figure(figsize=(9, 6), dpi=100, facecolor=GRAY_RES)
        # Borde que engloba el grafico completo (ejes, etiquetas y titulo)
        self.fig.patch.set_edgecolor(BORDER)
        self.fig.patch.set_linewidth(2.0)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setStyleSheet(f'border:1px solid {BORDER};')
        root.addWidget(self.canvas, 1)

        self._dibujar()

    # ──────────────────────────────────────────────────────────────
    def actualizar(self, pozo, Q_op, d_broca, caudales, pozo_alt=None,
                   etq="Escenario", etq_alt=None):
        self.datos = dict(
            pozo=pozo, Q_op=Q_op, d_broca=d_broca, caudales=caudales,
            barrido=barrido_caudal(pozo, caudales, d_broca) if caudales else [],
            res=calcular(pozo, Q_op, d_broca),
            etq=etq, etq_alt=etq_alt)
        if pozo_alt is not None and caudales:
            self.datos["barrido_alt"] = barrido_caudal(pozo_alt, caudales, d_broca)
            self.datos["pozo_alt"] = pozo_alt
            self.datos["res_alt"] = calcular(pozo_alt, Q_op, d_broca)
        self._dibujar()

    def _guardar(self):
        p, _ = QFileDialog.getSaveFileName(self, "Guardar grafica",
                                           "grafica.png", "PNG (*.png)")
        if p:
            self.fig.savefig(p, dpi=200,
                             facecolor=self.fig.get_facecolor(),
                             edgecolor=self.fig.get_edgecolor())

    # ──────────────────────────────────────────────────────────────
    def _estilo(self, ax):
        ax.set_facecolor('#FAFAFA')
        ax.grid(True, linestyle='--', alpha=0.4, color=GRAY_LBL)
        ax.tick_params(labelsize=8, colors=TEXT_DIM)
        for s in ax.spines.values():
            s.set_edgecolor(BORDER)
        ax.xaxis.label.set_fontsize(9)
        ax.yaxis.label.set_fontsize(9)
        ax.xaxis.label.set_color(TEXT_DIM)
        ax.yaxis.label.set_color(TEXT_DIM)
        ax.title.set_fontsize(10)
        ax.title.set_color(TEXT_DIM)

    def _anotar_valores(self, ax, xs, ys, fmt="{:,.0f}", color=None):
        """Escribe el valor de la variable sobre cada marcador."""
        col = color or TEXT_DIM
        for x, y in zip(xs, ys):
            ax.annotate(fmt.format(y), xy=(x, y), xytext=(0, 7),
                        textcoords="offset points", ha="center", va="bottom",
                        fontsize=7, color=col, fontfamily=FONT_F)

    def _dibujar(self):
        self.fig.clear()
        self.fig.patch.set_edgecolor(BORDER)
        self.fig.patch.set_linewidth(2.0)
        ax = self.fig.add_subplot(111)

        if not self.datos:
            ax.text(0.5, 0.5, "Sin resultados", ha="center", va="center",
                    fontsize=12, color=GRIS, transform=ax.transAxes)
            ax.set_xticks([]); ax.set_yticks([])
            ax.set_facecolor('#FAFAFA')
            self.fig.tight_layout()
            self.canvas.draw()
            return

        d = self.datos
        self._estilo(ax)

        bar = d["barrido"]
        Qs = [r.Q for r in bar]
        alt = "barrido_alt" in d
        Qa = [r.Q for r in d["barrido_alt"]] if alt else None
        i = self.cb.currentIndex()
        S  = lambda b, k: [getattr(r, k) for r in b]

        if i in (0, 1, 4, 5) and not bar:
            ax.text(0.5, 0.5, "No hay caudales cargados para el barrido",
                    ha="center", va="center", fontsize=10, color=GRIS,
                    transform=ax.transAxes)
            self.fig.tight_layout(); self.canvas.draw(); return

        if i == 0:
            ax.plot(Qs, S(bar, "P_bomba"), marker='o', ms=MS, lw=LW,
                    color=AZUL, label=d["etq"])
            self._anotar_valores(ax, Qs, S(bar, "P_bomba"), "{:,.0f}")
            if alt:
                ax.plot(Qa, S(d["barrido_alt"], "P_bomba"), marker='o', ms=MS,
                        lw=LW, ls='--', color=ROJO, label=d["etq_alt"])
            ax.set_xlabel("Caudal (gpm)")
            ax.set_ylabel("Presion de bomba (psi)")
            ax.set_title("Presion de bomba vs Caudal", loc="right")

        elif i == 1:
            ax.plot(Qs, S(bar, "dP_parasita"), marker='o', ms=MS, lw=LW,
                    color=AZUL, label=d["etq"])
            self._anotar_valores(ax, Qs, S(bar, "dP_parasita"), "{:,.0f}")
            if alt:
                ax.plot(Qa, S(d["barrido_alt"], "dP_parasita"), marker='o',
                        ms=MS, lw=LW, ls='--', color=ROJO, label=d["etq_alt"])
            ax.set_xlabel("Caudal (gpm)")
            ax.set_ylabel("Presion parasita (psi)")
            ax.set_title("Presion parasita vs Caudal", loc="right")

        elif i in (2, 3):
            pf = perfil_utube(d["pozo"], d["res"])
            if i == 2:
                ax.plot(pf["L"], pf["P_dyn"], lw=LW, marker='o', ms=MS,
                        color=AZUL, label=d["etq"])
                if alt:
                    pfa = perfil_utube(d["pozo_alt"], d["res_alt"])
                    ax.plot(pfa["L"], pfa["P_dyn"], lw=LW, marker='o', ms=MS,
                            ls='--', color=ROJO, label=d["etq_alt"])
                ax.set_ylabel("Presion circulante (psi)")
                ax.set_title(f"Presion circulante vs Longitud U-Tube  /  "
                             f"Q = {d['Q_op']:,.0f} gpm", loc="right")
            else:
                ax.plot(pf["L"], pf["P_hyd"], lw=LW, marker='o', ms=MS,
                        color=GRIS, label="Presion hidrostatica")
                ax.plot(pf["L"], pf["P_tot"], lw=LW, marker='o', ms=MS,
                        color=AZUL, label="Hidrostatica + dinamica")
                if alt:
                    pfa = perfil_utube(d["pozo_alt"], d["res_alt"])
                    ax.plot(pfa["L"], pfa["P_tot"], lw=LW, marker='o', ms=MS,
                            ls='--', color=ROJO,
                            label=f"Hidrostatica + dinamica ({d['etq_alt']})")
                ax.set_ylabel("Presion (psi)")
                ax.set_title(f"Perfil de presion a lo largo del circuito  /  "
                             f"Q = {d['Q_op']:,.0f} gpm", loc="right")
            ax.set_xlabel("Distancia desde el standpipe, longitud U-Tube (ft)")
            Lb = sum(t.longitud for t in d["res"].tramos_int)
            ax.axvline(Lb, color=VERDE, ls="-", lw=0.9)
            ax.annotate("Broca", xy=(Lb, ax.get_ylim()[1]),
                        xytext=(4, -10), textcoords="offset points",
                        fontsize=8, color=VERDE, va="top")

        elif i == 4:
            ax.plot(Qs, S(bar, "dP_ann"), marker='o', ms=MS, lw=LW,
                    color=AZUL, label=d["etq"])
            self._anotar_valores(ax, Qs, S(bar, "dP_ann"), "{:,.0f}")
            if alt:
                ax.plot(Qa, S(d["barrido_alt"], "dP_ann"), marker='o', ms=MS,
                        lw=LW, ls='--', color=ROJO, label=d["etq_alt"])
            ax.set_xlabel("Caudal (gpm)")
            ax.set_ylabel("Caida de presion anular total (psi)")
            ax.set_title("Caida de presion anular vs Caudal", loc="right")

        elif i == 5:
            ax.plot(Qs, S(bar, "ECD"), marker='o', ms=MS, lw=LW,
                    color=AZUL, label=d["etq"])
            self._anotar_valores(ax, Qs, S(bar, "ECD"), "{:.2f}")
            if alt:
                ax.plot(Qa, S(d["barrido_alt"], "ECD"), marker='o', ms=MS,
                        lw=LW, ls='--', color=ROJO, label=d["etq_alt"])
            rho = d["pozo"].fluido.rho
            ax.axhline(rho, color=GRIS, ls="-", lw=LW)
            ax.annotate(f"Densidad estatica = {rho:.2f} ppg",
                        xy=(Qs[0], rho), xytext=(4, 4),
                        textcoords="offset points", fontsize=8, color=TEXT_DIM)
            ax.set_xlabel("Caudal (gpm)")
            ax.set_ylabel("Densidad equivalente de circulacion (ppg)")
            ax.set_title("ECD vs Caudal", loc="right")

        else:
            r = d["res"]
            nombres = ["Superficie"] + [t.nombre for t in r.tramos_int] + \
                      ["Boquillas de la broca"] + [t.nombre for t in r.tramos_ann]
            vals = [r.dp_superficie] + [t.dP for t in r.tramos_int] + \
                   [r.broca.dP] + [t.dP for t in r.tramos_ann]
            cols = [B_SUP] + [B_INT] * len(r.tramos_int) + [B_BIT] + \
                   [B_ANN] * len(r.tramos_ann)
            y = list(range(len(vals)))
            ax.barh(y, vals, color=cols, edgecolor=BORDER, linewidth=0.5,
                    height=0.62)
            ax.set_yticks(y)
            ax.set_yticklabels(nombres, fontsize=8)
            ax.invert_yaxis()
            for k, v in enumerate(vals):
                ax.annotate(f"{v:,.1f} psi  ({v/r.P_bomba*100:.1f} %)",
                            xy=(v, k), xytext=(5, 0),
                            textcoords="offset points", va="center",
                            fontsize=8, color=TEXT_DIM)
            ax.set_xlabel("Caida de presion (psi)")
            ax.set_title(f"Distribucion de las perdidas de presion  /  "
                         f"Q = {d['Q_op']:,.0f} gpm  /  "
                         f"P bomba = {r.P_bomba:,.0f} psi", loc="right")
            ax.set_xlim(0, max(vals) * 1.45)
            ax.grid(True, axis="x", linestyle='--', alpha=0.4, color=GRAY_LBL)
            ax.grid(False, axis="y")

        if i != 6:
            ax.legend(fontsize=8, framealpha=0.9)
        self.fig.tight_layout()
        self.canvas.draw()
