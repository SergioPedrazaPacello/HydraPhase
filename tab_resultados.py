"""Pestana 2 - Resultados: caidas de presion por tramo, broca, ECD."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QGroupBox, QLabel)
from PyQt6.QtCore import Qt

from estilo import (WHITE, GRAY_LBL, GRAY_RES, GRAY_HDR, BORDER, TEXT,
                    TEXT_RES, TEXT_DIM, AZUL, ROJO, VERDE, FONT_F, FS,
                    QSS_GROUP, cell, seccion, etiqueta, tabla)
from engine_hidraulica import calcular, barrido_caudal

COLS = ["Tramo", "Regimen", "Diametro\n(in)", "Longitud\n(ft)",
        "Velocidad\n(ft/s)", "Viscosidad\nefectiva (cp)",
        "Numero de\nReynolds", "Factor de\nfriccion",
        "Gradiente\n(psi/ft)", "Caida de\npresion (psi)"]


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

        root.addWidget(seccion("Perdidas de presion por friccion, tramo por tramo"))
        self.tbl = tabla(0, len(COLS), COLS, col_ancha=0, ancho=100)
        # Anchos por columna para que los nombres completos se lean bien.
        for c, w in [(1, 80), (2, 82), (3, 80), (4, 90), (5, 120),
                     (6, 98), (7, 92), (8, 96), (9, 112)]:
            self.tbl.setColumnWidth(c, w)
        self.tbl.horizontalHeader().setFixedHeight(38)
        root.addWidget(self.tbl, 1)

        fila = QHBoxLayout()
        fila.setSpacing(8)
        fila.addWidget(self._grupo_balance(), 1)
        fila.addWidget(self._grupo_broca(), 1)
        fila.addWidget(self._grupo_ecd(), 1)
        root.addLayout(fila)

        root.addWidget(seccion("Barrido de caudal"))
        self.tbl_q = tabla(0, 8, ["Caudal\n(gpm)", "Presion de\nbomba (psi)",
                                  "Caida de presion\nen broca (psi)",
                                  "Presion\nparasita (psi)",
                                  "Caida de presion\nanular (psi)",
                                  "ECD (ppg)", "HHP bomba\n(hp)",
                                  "HSI (hp/in\u00b2)"])
        self.tbl_q.horizontalHeader().setFixedHeight(38)
        self.tbl_q.setMaximumHeight(200)
        root.addWidget(self.tbl_q)

    # ── Grupos de resumen ─────────────────────────────────────────
    def _kv(self, layout, fila, texto):
        layout.addWidget(etiqueta(texto), fila, 0)
        v = QLabel("")
        v.setStyleSheet(f'background:{WHITE};border:1px solid {BORDER};'
                        f'color:{TEXT_RES};font-family:"{FONT_F}";font-size:{FS}pt;'
                        f'padding:2px 6px;')
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
        self.v_par = self._kv(l, 5, "Presion parasita (psi)")
        self.v_bom = self._kv(l, 6, "Presion de bomba (psi)")
        l.setColumnStretch(0, 1)
        l.setRowStretch(7, 1)
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
        self.v_hsi  = self._kv(l, 3, "HSI (hp/in\u00b2)")
        self.v_fj   = self._kv(l, 4, "Fuerza de impacto (lbf)")
        self.v_pct  = self._kv(l, 5, "Porcentaje de P bomba en la broca")
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
        self.v_ecd  = self._kv(l, 1, "ECD (ppg)")
        self.v_decd = self._kv(l, 2, "Incremento por circulacion (ppg)")
        self.v_phid = self._kv(l, 3, "Presion hidrostatica (psi)")
        self.v_pfon = self._kv(l, 4, "Presion de fondo circulando (psi)")
        self.v_tvd  = self._kv(l, 5, "TVD (ft)")
        self.v_vmax = self._kv(l, 6, "Velocidad anular maxima (ft/s)")
        l.setColumnStretch(0, 1)
        l.setRowStretch(7, 1)
        return g

    # ── Actualizacion ─────────────────────────────────────────────
    def actualizar(self, pozo, Q_op, d_broca, caudales):
        self.res = calcular(pozo, Q_op, d_broca)
        self.barrido = barrido_caudal(pozo, caudales, d_broca) if caudales else []
        r = self.res
        f = pozo.fluido

        self.tbl.setRowCount(0)

        def add(t, bg):
            i = self.tbl.rowCount()
            self.tbl.insertRow(i)
            self.tbl.setRowHeight(i, 21)
            vals = [(t.nombre, Qt.AlignmentFlag.AlignLeft, TEXT),
                    (t.regimen, Qt.AlignmentFlag.AlignCenter, TEXT_RES),
                    (f"{t.D:.3f}", None, TEXT_RES),
                    (f"{t.longitud:,.0f}", None, TEXT_RES),
                    (f"{t.V:.3f}", None, TEXT_RES),
                    (f"{t.mu_e:.2f}", None, TEXT_RES),
                    (f"{t.NRe:,.0f}", None, TEXT_RES),
                    (f"{t.f:.6f}", None, TEXT_RES),
                    (f"{t.gradiente:.6f}", None, TEXT_RES),
                    (f"{t.dP:.2f}", None, TEXT_RES)]
            for c, (v, al, col) in enumerate(vals):
                a = al or (Qt.AlignmentFlag.AlignRight |
                           Qt.AlignmentFlag.AlignVCenter)
                self.tbl.setItem(i, c, cell(v, bg=bg, color=col, align=a))

        for t in r.tramos_int:
            add(t, WHITE)

        rb = self.tbl.rowCount()
        self.tbl.insertRow(rb)
        self.tbl.setRowHeight(rb, 21)
        for c in range(len(COLS)):
            txt = ""
            if c == 0:
                txt = "Boquillas de la broca"
            elif c == 9:
                txt = f"{r.broca.dP:.2f}"
            al = (Qt.AlignmentFlag.AlignLeft if c == 0 else
                  Qt.AlignmentFlag.AlignRight) | Qt.AlignmentFlag.AlignVCenter
            self.tbl.setItem(rb, c, cell(txt, bg=GRAY_HDR, color=TEXT_RES, align=al))

        for t in r.tramos_ann:
            add(t, GRAY_RES)

        self.v_sup.setText(f"{r.dp_superficie:,.2f}")
        self.v_int.setText(f"{r.dP_int:,.2f}")
        self.v_bit.setText(f"{r.broca.dP:,.2f}")
        self.v_ann.setText(f"{r.dP_ann:,.2f}")
        self.v_mot.setText(f"{r.dp_motor:,.2f}")
        self.v_par.setText(f"{r.dP_parasita:,.2f}")
        self.v_bom.setText(f"{r.P_bomba:,.2f}")

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
        self.v_vmax.setText(f"{max((t.V for t in r.tramos_ann), default=0.0):.2f}")

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
                self.tbl_q.setItem(i, c, cell(v, bg=bg, color=TEXT_RES,
                                              align=al))
