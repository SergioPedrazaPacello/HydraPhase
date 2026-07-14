"""Pestana 4 - Esquema del pozo: corte 2D a escala + vista 3D."""
import numpy as np
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavToolbar
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle, Polygon
import matplotlib.patches as mpatches

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QRadioButton,
                             QButtonGroup, QCheckBox, QFileDialog)
from PyQt6.QtCore import Qt

from estilo import GRAY_RES, GRAY_LBL, BORDER, FONT_F, FS, etiqueta, boton

# ── Colores del esquema ────────────────────────────────────────────────
C_FORM   = "#C8BFA8"   # formacion
C_CSG    = "#9AA5B1"   # revestimiento
C_CEM    = "#D9D2C0"   # cemento / anular
C_PIPE   = "#7A8B99"   # sarta
C_DC     = "#5C6B78"   # portamechas
C_LODO   = "#D6E4F0"   # lodo en el anular
C_WASH   = "#E8C9C9"   # zona de washout
C_BIT    = "#3A4750"


class TabEsquema(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f'background:{GRAY_RES};')
        self.pozo = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(5)

        barra = QHBoxLayout()
        barra.addWidget(etiqueta("Vista:"))
        self.rb2d = QRadioButton("Corte 2D a escala")
        self.rb3d = QRadioButton("Vista 3D")
        self.rb2d.setChecked(True)
        for rb in (self.rb2d, self.rb3d):
            rb.setStyleSheet(f'font-family:"{FONT_F}";font-size:{FS}pt;'
                             f'background:transparent;')
            rb.toggled.connect(self._dibujar)
            barra.addWidget(rb)

        self.ck_cotas = QCheckBox("Mostrar cotas")
        self.ck_cotas.setChecked(True)
        self.ck_cotas.setStyleSheet(f'font-family:"{FONT_F}";font-size:{FS}pt;'
                                    f'background:transparent;')
        self.ck_cotas.stateChanged.connect(self._dibujar)
        barra.addSpacing(14)
        barra.addWidget(self.ck_cotas)

        self.ck_metros = QCheckBox("Profundidad en metros")
        self.ck_metros.setStyleSheet(f'font-family:"{FONT_F}";font-size:{FS}pt;'
                                     f'background:transparent;')
        self.ck_metros.stateChanged.connect(self._dibujar)
        barra.addWidget(self.ck_metros)

        barra.addStretch()
        b = boton("Guardar PNG", 110)
        b.clicked.connect(self._guardar)
        barra.addWidget(b)
        root.addLayout(barra)

        self.fig = Figure(figsize=(8, 8), dpi=100, facecolor="#FFFFFF")
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setStyleSheet(f'border:1px solid {BORDER};')
        root.addWidget(self.canvas, 1)

        self.tb = NavToolbar(self.canvas, self)
        self.tb.setStyleSheet(f'background:{GRAY_LBL};border:1px solid {BORDER};')
        root.addWidget(self.tb)

        self._dibujar()

    def actualizar(self, pozo):
        self.pozo = pozo
        self._dibujar()

    def _guardar(self):
        p, _ = QFileDialog.getSaveFileName(self, "Guardar esquema",
                                           "esquema_pozo.png", "PNG (*.png)")
        if p:
            self.fig.savefig(p, dpi=200, bbox_inches="tight")

    # ──────────────────────────────────────────────────────────────
    def _dibujar(self):
        self.fig.clear()
        if self.pozo is None or not self.pozo.sarta or not self.pozo.hoyo:
            ax = self.fig.add_subplot(111)
            ax.text(0.5, 0.5, "Sin datos de pozo", ha="center", va="center",
                    color="#888888", fontsize=13, transform=ax.transAxes)
            ax.set_xticks([]); ax.set_yticks([])
            self.canvas.draw()
            return
        if self.rb3d.isChecked():
            self._dibujar_3d()
        else:
            self._dibujar_2d()
        self.canvas.draw()

    # ══════════════════════════════════════════════════════════════
    # CORTE 2D
    # ══════════════════════════════════════════════════════════════
    def _dibujar_2d(self):
        p = self.pozo
        ax = self.fig.add_subplot(111)
        md = p.prof_broca()
        k = 0.3048 if self.ck_metros.isChecked() else 1.0
        u = "m" if self.ck_metros.isChecked() else "ft"

        Dmax = max(h.ID for h in p.hoyo)
        xlim = Dmax * 0.62

        # ── Formacion ─────────────────────────────────────────────
        ax.add_patch(Rectangle((-xlim, 0), 2 * xlim, md * 1.03,
                               fc=C_FORM, ec="none", zorder=0))
        ax.axhline(0, color="#4A7C1F", lw=2.5, zorder=6)
        ax.text(-xlim * 0.97, -md * 0.012, "Superficie", fontsize=8,
                color="#2E5A12", va="bottom")

        # ── Hoyo / revestimientos ─────────────────────────────────
        for h in p.hoyo:
            r = h.ID / 2.0
            z0, z1 = h.prof_tope, min(h.prof_base, md)
            if z1 <= z0:
                continue
            fc = C_WASH if h.tipo == "washout" else C_LODO
            ax.add_patch(Rectangle((-r, z0), 2 * r, z1 - z0,
                                   fc=fc, ec="none", zorder=1))
            if h.tipo == "casing":
                esp = max(Dmax * 0.020, 0.12)
                for s in (-1, 1):
                    ax.add_patch(Rectangle((s * r, 0), s * esp, z1,
                                           fc=C_CSG, ec="#4A5560",
                                           lw=0.7, zorder=3))
                # zapata
                ax.plot([-r - esp, -r], [z1, z1], color="#333333", lw=2.5, zorder=5)
                ax.plot([r, r + esp], [z1, z1], color="#333333", lw=2.5, zorder=5)
                ax.text(r + esp * 1.6, z1, f"  Zapata {h.ID:.3f}\" @ "
                                           f"{z1*k:,.0f} {u}",
                        fontsize=7.5, va="center", color="#333333")
            else:
                for s in (-1, 1):
                    ax.plot([s * r, s * r], [z0, z1], color="#8A7F66",
                            lw=1.2, zorder=3)
            if h.tipo == "washout":
                ax.text(r * 1.02, (z0 + z1) / 2,
                        f"  WASHOUT\n  {h.ID:.2f}\"", fontsize=7.5,
                        color="#8B0000", va="center", weight="bold")

        # ── Sarta ─────────────────────────────────────────────────
        z = 0.0
        for t in p.sarta:
            ro, ri = t.OD / 2.0, t.ID / 2.0
            col = C_DC if ("collar" in t.nombre.lower() or
                           "porta" in t.nombre.lower()) else C_PIPE
            for s in (-1, 1):
                ax.add_patch(Rectangle((s * ri, z), s * (ro - ri), t.longitud,
                                       fc=col, ec="#2F3A42", lw=0.6, zorder=4))
            # interior (lodo bajando)
            ax.add_patch(Rectangle((-ri, z), 2 * ri, t.longitud,
                                   fc="#EAF2FA", ec="none", zorder=3.5))
            ax.text(0, z + t.longitud / 2,
                    f"{t.nombre}\n{t.OD:.3f}\" x {t.ID:.3f}\"",
                    fontsize=7.5, ha="center", va="center",
                    color="#1B242B", rotation=90, zorder=6)
            z += t.longitud

        # ── Broca ─────────────────────────────────────────────────
        db = p.hoyo[-1].ID
        rb = db / 2.0
        h_bit = md * 0.012
        ax.add_patch(Polygon([(-rb, md - h_bit), (rb, md - h_bit),
                              (rb * 0.55, md), (-rb * 0.55, md)],
                             closed=True, fc=C_BIT, ec="#1B242B",
                             lw=0.8, zorder=6))
        nb = "/".join(str(b) for b in p.boquillas)
        ax.text(rb * 1.15, md, f"  Broca {db:.3f}\"\n  Boquillas {nb} (1/32\")",
                fontsize=7.5, va="center", color="#1B242B")

        # ── Cotas ─────────────────────────────────────────────────
        if self.ck_cotas.isChecked():
            cotas = sorted({0.0, md} |
                           {h.prof_base for h in p.hoyo if h.prof_base <= md} |
                           {h.prof_tope for h in p.hoyo})
            xc = xlim * 0.80
            ax.annotate("", xy=(xc, 0), xytext=(xc, md),
                        arrowprops=dict(arrowstyle="<->", color="#555555", lw=0.9))
            for c in cotas:
                if c <= 0:
                    continue
                ax.plot([xc - xlim * 0.03, xc + xlim * 0.03], [c, c],
                        color="#555555", lw=0.9)
                ax.text(xc + xlim * 0.05, c, f"{c*k:,.0f} {u}",
                        fontsize=7.5, va="center", color="#333333")

        # ── Ejes ──────────────────────────────────────────────────
        ax.set_xlim(-xlim, xlim * 1.35)
        ax.set_ylim(md * 1.05, -md * 0.045)
        ax.set_xlabel("Diametro, in")
        ax.set_ylabel(f"Profundidad medida, {u}")
        ax.set_title(f"Esquema del pozo  |  MD = {md*k:,.0f} {u}  |  "
                     f"Escala vertical exagerada", fontsize=10)
        ax.set_aspect("auto")
        ax.grid(True, axis="y", ls=":", lw=0.6, color="#999999", alpha=0.6)

        leg = [mpatches.Patch(fc=C_CSG, ec="#4A5560", label="Revestimiento"),
               mpatches.Patch(fc=C_PIPE, ec="#2F3A42", label="Drill Pipe"),
               mpatches.Patch(fc=C_DC, ec="#2F3A42", label="Drill Collar"),
               mpatches.Patch(fc=C_LODO, ec="#8A7F66", label="Anular (lodo)"),
               mpatches.Patch(fc=C_WASH, ec="#8B0000", label="Washout"),
               mpatches.Patch(fc=C_FORM, ec="none", label="Formacion")]
        ax.legend(handles=leg, fontsize=7.5, loc="lower left", framealpha=0.95)
        self.fig.tight_layout()

    # ══════════════════════════════════════════════════════════════
    # VISTA 3D
    # ══════════════════════════════════════════════════════════════
    def _cilindro(self, ax, r, z0, z1, color, alpha=1.0, th0=np.pi/2,
                  th1=3*np.pi/2, nt=40):
        """Media superficie cilindrica (corte) para revelar el interior."""
        th = np.linspace(th0, th1, nt)
        zz = np.linspace(z0, z1, 2)
        T, Z = np.meshgrid(th, zz)
        X, Y = r * np.cos(T), r * np.sin(T)
        ax.plot_surface(X, Y, Z, color=color, alpha=alpha, linewidth=0,
                        antialiased=True, shade=True, rcount=2, ccount=nt)

    def _dibujar_3d(self):
        p = self.pozo
        ax = self.fig.add_subplot(111, projection="3d")
        md = p.prof_broca()
        k = 0.3048 if self.ck_metros.isChecked() else 1.0
        u = "m" if self.ck_metros.isChecked() else "ft"

        # Del exterior al interior: el algoritmo del pintor de mplot3d
        # ordena por profundidad media; con medias cañas orientadas hacia
        # atras la oclusion resulta correcta desde la vista frontal.
        for h in sorted(p.hoyo, key=lambda x: -x.ID):
            z1 = min(h.prof_base, md)
            if z1 <= h.prof_tope:
                continue
            col = C_WASH if h.tipo == "washout" else (
                C_CSG if h.tipo == "casing" else "#B8AC90")
            self._cilindro(ax, h.ID / 2.0, h.prof_tope, z1, col, 0.85)

        z = 0.0
        for t in p.sarta:
            col = C_DC if ("collar" in t.nombre.lower() or
                           "porta" in t.nombre.lower()) else C_PIPE
            self._cilindro(ax, t.OD / 2.0, z, z + t.longitud, col, 1.0)
            self._cilindro(ax, t.ID / 2.0, z, z + t.longitud, "#EAF2FA", 1.0)
            z += t.longitud

        Dmax = max(h.ID for h in p.hoyo)
        L = Dmax / 2.0 * 1.2
        ax.set_xlim(-L, L); ax.set_ylim(-L, L)
        ax.set_zlim(md, 0)
        ax.set_xlabel("x, in", fontsize=8)
        ax.set_ylabel("y, in", fontsize=8)
        ax.set_zlabel(f"Profundidad, {u}", fontsize=8)
        ax.set_box_aspect((1, 1, 2.6))
        ax.view_init(elev=12, azim=-72)
        ax.tick_params(labelsize=7)
        ax.set_zticks(np.linspace(0, md, 6))
        ax.set_zticklabels([f"{v*k:,.0f}" for v in np.linspace(0, md, 6)])
        ax.set_title(f"Vista 3D del pozo (seccion cortada)  |  MD = "
                     f"{md*k:,.0f} {u}", fontsize=10)
        ax.grid(False)
        self.fig.subplots_adjust(left=0.02, right=0.98, top=0.94, bottom=0.03)
