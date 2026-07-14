"""Pestana 2 - Resultados: caidas de presion por tramo, broca, ECD."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QGroupBox, QLabel, QComboBox)
from PyQt6.QtCore import Qt

from estilo import (WHITE, GRAY_LBL, GRAY_RES, GRAY_HDR, BORDER, TEXT,
                    TEXT_RES, TEXT_DIM, AZUL, ROJO, VERDE, FONT_F, FS,
                    QSS_GROUP, QSS_COMBO, cell, seccion, etiqueta, tabla)
from engine_hidraulica import (calcular, barrido_caudal, PSI_A_KPA,
                               ResultadoHidraulica)

COLS = ["Tramo", "Reg.", "D (in)", "L (ft)", "V (ft/s)", "\u03bce (cp)",
        "NRe", "f", "Grad (psi/ft)", "\u0394P (psi)", "\u0394P (kPa)"]
ANCHOS = [None, 78, 62, 72, 68, 66, 78, 76, 88, 82, 82]


class TabResultados(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f'background:{GRAY_RES};')
        self.res = None
        self.barrido = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(6)

        # ── Cabecera ──────────────────────────────────────────────
        self.lbl_cab = QLabel("Sin resultados. Presione CALCULAR en la "
                              "pestana de datos.")
        self.lbl_cab.setStyleSheet(
            f'background:{GRAY_LBL};border:1px solid {BORDER};color:{TEXT_RES};'
            f'font-family:"{FONT_F}";font-size:{FS}pt;padding:4px 8px;')
        root.addWidget(self.lbl_cab)

        # ── Tabla de tramos ───────────────────────────────────────
        root.addWidget(seccion("Perdidas de presion por friccion, tramo por tramo"))
        self.tbl = tabla(0, len(COLS), COLS, 0)
        for c, w in enumerate(ANCHOS):
            if w:
                self.tbl.setColumnWidth(c, w)
        root.addWidget(self.tbl, 1)

        # ── Resumen ───────────────────────────────────────────────
        fila = QHBoxLayout()
        fila.setSpacing(8)
        fila.addWidget(self._grupo_balance(), 1)
        fila.addWidget(self._grupo_broca(), 1)
        fila.addWidget(self._grupo_ecd(), 1)
        root.addLayout(fila)

        # ── Barrido de caudal ─────────────────────────────────────
        root.addWidget(seccion("Barrido de caudal"))
        self.tbl_q = tabla(0, 8, ["Q (gpm)", "P bomba (psi)", "\u0394P broca (psi)",
                                  "P parasita (psi)", "\u0394P anular (psi)",
                                  "ECD (ppg)", "HHP bomba", "HSI"], 0)
        for c, w in enumerate([None, 110, 110, 110, 110, 90, 90, 80]):
            if w:
                self.tbl_q.setColumnWidth(c, w)
        self.tbl_q.setMaximumHeight(190)
        root.addWidget(self.tbl_q)

    # ── Grupos de resumen ─────────────────────────────────────────
    def _kv(self, layout, fila, texto, color=TEXT_RES, negrita=False):
        layout.addWidget(etiqueta(texto), fila, 0)
        v = QLabel("--")
        peso = "bold" if negrita else "normal"
        v.setStyleSheet(f'background:{WHITE};border:1px solid {BORDER};'
                        f'color:{color};font-family:"{FONT_F}";font-size:{FS}pt;'
                        f'font-weight:{peso};padding:2px 6px;')
        v.setAlignment(Qt.AlignmentFlag.AlignRight |
                       Qt.AlignmentFlag.AlignVCenter)
        v.setFixedWidth(110)
        layout.addWidget(v, fila, 1)
        return v

    def _grupo_balance(self):
        g = QGroupBox("Balance de presiones")
        g.setStyleSheet(QSS_GROUP)
        l = QGridLayout(g)
        l.setContentsMargins(8, 6, 8, 6)
        l.setVerticalSpacing(3)
        self.v_sup = self._kv(l, 0, "Equipo de superficie (psi)")
        self.v_int = self._kv(l, 1, "Interior de la sarta (psi)")
        self.v_bit = self._kv(l, 2, "Boquillas de la broca (psi)")
        self.v_ann = self._kv(l, 3, "Espacio anular (psi)")
        self.v_mot = self._kv(l, 4, "Motor de fondo / MWD (psi)")
        self.v_par = self._kv(l, 5, "Presion parasita (psi)", ROJO)
        self.v_bom = self._kv(l, 6, "PRESION DE BOMBA (psi)", AZUL, True)
        self.v_bom_k = self._kv(l, 7, "Presion de bomba (kPa)", TEXT_DIM)
        l.setColumnStretch(0, 1)
        return g

    def _grupo_broca(self):
        g = QGroupBox("Hidraulica en la broca")
        g.setStyleSheet(QSS_GROUP)
        l = QGridLayout(g)
        l.setContentsMargins(8, 6, 8, 6)
        l.setVerticalSpacing(3)
        self.v_tfa  = self._kv(l, 0, "Area total de flujo (in\u00b2)")
        self.v_vboq = self._kv(l, 1, "Velocidad en boquillas (ft/s)")
        self.v_hhp  = self._kv(l, 2, "Potencia hidraulica (hp)")
        self.v_hsi  = self._kv(l, 3, "HSI (hp/in\u00b2)", VERDE, True)
        self.v_fj   = self._kv(l, 4, "Fuerza de impacto (lbf)")
        self.v_pct  = self._kv(l, 5, "% de P bomba en la broca")
        self.v_hhpb = self._kv(l, 6, "HHP total de bomba (hp)")
        l.setColumnStretch(0, 1)
        l.setRowStretch(7, 1)
        return g

    def _grupo_ecd(self):
        g = QGroupBox("Densidad y presiones de fondo")
        g.setStyleSheet(QSS_GROUP)
        l = QGridLayout(g)
        l.setContentsMargins(8, 6, 8, 6)
        l.setVerticalSpacing(3)
        self.v_rho  = self._kv(l, 0, "Densidad del lodo (ppg)")
        self.v_ecd  = self._kv(l, 1, "ECD (ppg)", AZUL, True)
        self.v_decd = self._kv(l, 2, "Incremento por circulacion (ppg)")
        self.v_phid = self._kv(l, 3, "Presion hidrostatica (psi)")
        self.v_pfon = self._kv(l, 4, "Presion de fondo circulando (psi)")
        self.v_tvd  = self._kv(l, 5, "TVD (ft)")
        self.v_vmax = self._kv(l, 6, "Vel. anular maxima (ft/s)")
        l.setColumnStretch(0, 1)
        l.setRowStretch(7, 1)
        return g

    # ── Actualizacion ─────────────────────────────────────────────
    def actualizar(self, pozo, Q_op, d_broca, caudales):
        self.res = calcular(pozo, Q_op, d_broca)
        self.barrido = barrido_caudal(pozo, caudales, d_broca)
        r = self.res

        f = pozo.fluido
        self.lbl_cab.setText(
            f"  Q = {Q_op:,.0f} gpm    |    Lodo {f.rho:.2f} ppg    |    "
            f"n_tub = {f.n_tuberia():.4f}  K_tub = {f.K_tuberia():.2f}    |    "
            f"n_ann = {f.n_anular():.4f}  K_ann = {f.K_anular():.2f}    |    "
            f"MD = {pozo.prof_broca():,.0f} ft")

        # ── Tabla de tramos ───────────────────────────────────────
        self.tbl.setRowCount(0)
        def add(t, bg):
            r_ = self.tbl.rowCount()
            self.tbl.insertRow(r_)
            self.tbl.setRowHeight(r_, 21)
            col_reg = ROJO if t.regimen == "Turbulento" else VERDE
            vals = [(t.nombre, Qt.AlignmentFlag.AlignLeft, TEXT),
                    (t.regimen, Qt.AlignmentFlag.AlignCenter, col_reg),
                    (f"{t.D:.3f}", None, TEXT_RES),
                    (f"{t.longitud:,.0f}", None, TEXT_RES),
                    (f"{t.V:.3f}", None, TEXT_RES),
                    (f"{t.mu_e:.2f}", None, TEXT_RES),
                    (f"{t.NRe:,.0f}", None, TEXT_RES),
                    (f"{t.f:.6f}", None, TEXT_RES),
                    (f"{t.gradiente:.6f}", None, TEXT_RES),
                    (f"{t.dP:.2f}", None, AZUL),
                    (f"{t.dP*PSI_A_KPA:.1f}", None, TEXT_DIM)]
            for c, (v, al, col) in enumerate(vals):
                a = al or (Qt.AlignmentFlag.AlignRight |
                           Qt.AlignmentFlag.AlignVCenter)
                self.tbl.setItem(r_, c, cell(v, bg=bg, color=col, align=a))

        for t in r.tramos_int:
            add(t, WHITE)
        # Fila de la broca
        rb = self.tbl.rowCount()
        self.tbl.insertRow(rb)
        self.tbl.setRowHeight(rb, 21)
        for c in range(len(COLS)):
            txt = ""
            if c == 0: txt = "  >> BOQUILLAS DE LA BROCA"
            elif c == 9: txt = f"{r.broca.dP:.2f}"
            elif c == 10: txt = f"{r.broca.dP*PSI_A_KPA:.1f}"
            al = (Qt.AlignmentFlag.AlignLeft if c == 0 else
                  Qt.AlignmentFlag.AlignRight) | Qt.AlignmentFlag.AlignVCenter
            self.tbl.setItem(rb, c, cell(txt, bg=GRAY_HDR, color=ROJO, align=al))
        for t in r.tramos_ann:
            add(t, GRAY_RES)

        # ── Balance ───────────────────────────────────────────────
        self.v_sup.setText(f"{r.dp_superficie:,.2f}")
        self.v_int.setText(f"{r.dP_int:,.2f}")
        self.v_bit.setText(f"{r.broca.dP:,.2f}")
        self.v_ann.setText(f"{r.dP_ann:,.2f}")
        self.v_mot.setText(f"{r.dp_motor:,.2f}")
        self.v_par.setText(f"{r.dP_parasita:,.2f}")
        self.v_bom.setText(f"{r.P_bomba:,.2f}")
        self.v_bom_k.setText(f"{r.P_bomba*PSI_A_KPA:,.1f}")

        b = r.broca
        self.v_tfa.setText(f"{b.At:.4f}")
        self.v_vboq.setText(f"{b.v_boq:,.1f}")
        self.v_hhp.setText(f"{b.HHP:,.1f}")
        self.v_hsi.setText(f"{b.HSI:.2f}")
        self.v_fj.setText(f"{b.Fj:,.1f}")
        self.v_pct.setText(f"{b.pct_dP:.1f} %")
        self.v_hhpb.setText(f"{r.HHP_bomba:,.1f}")

        self.v_rho.setText(f"{f.rho:.3f}")
        self.v_ecd.setText(f"{r.ECD:.4f}")
        self.v_decd.setText(f"{r.ECD - f.rho:.4f}")
        self.v_phid.setText(f"{r.P_hidrostatica:,.1f}")
        self.v_pfon.setText(f"{r.P_hidrostatica + r.dP_ann:,.1f}")
        self.v_tvd.setText(f"{pozo.tvd_efectiva():,.0f}")
        vmax = max((t.V for t in r.tramos_ann), default=0.0)
        self.v_vmax.setText(f"{vmax:.2f}")

        # ── Barrido ───────────────────────────────────────────────
        self.tbl_q.setRowCount(0)
        for rr in self.barrido:
            i = self.tbl_q.rowCount()
            self.tbl_q.insertRow(i)
            self.tbl_q.setRowHeight(i, 21)
            destaca = abs(rr.Q - Q_op) < 1e-6
            bg = GRAY_HDR if destaca else WHITE
            vals = [f"{rr.Q:,.0f}", f"{rr.P_bomba:,.2f}", f"{rr.broca.dP:,.2f}",
                    f"{rr.dP_parasita:,.2f}", f"{rr.dP_ann:,.2f}",
                    f"{rr.ECD:.4f}", f"{rr.HHP_bomba:,.1f}",
                    f"{rr.broca.HSI:.2f}"]
            for c, v in enumerate(vals):
                al = (Qt.AlignmentFlag.AlignLeft if c == 0 else
                      Qt.AlignmentFlag.AlignRight) | Qt.AlignmentFlag.AlignVCenter
                self.tbl_q.setItem(i, c, cell(v, bg=bg,
                                              color=AZUL if destaca else TEXT_RES,
                                              align=al))
