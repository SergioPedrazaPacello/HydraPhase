"""Pestana 1 - Datos de entrada del pozo, fluido y sarta."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QAbstractItemView, QGroupBox, QLabel)
from PyQt6.QtCore import Qt, pyqtSignal

from estilo import (WHITE, GRAY_LBL, GRAY_RES, BORDER, TEXT, TEXT_RES,
                    TEXT_DIM, FONT_F, FS, QSS_TBL, QSS_GROUP,
                    seccion, etiqueta, boton, spin, campo, leer_campo)
from engine_hidraulica import (Fluido, TramoSarta, TramoHoyo, Pozo,
                               pozo_referencia, pozo_hcy2)
import dialogos as dlg

# Tamano fijo de los tres grupos superiores.
# El ancho de cada uno se ajusta a su contenido real (etiqueta mas larga
# + campo), sin espacio sobrante. Los campos van alineados a la derecha.
W_FLUIDO, W_BROCA, W_OPER = 232, 262, 278
ALTO_GRUPO = 200
W_CAMPO    = 78     # ancho de los campos numericos
W_CHICO    = 56     # ancho de boquillas y caudales


class _TablaEditable(QTableWidget):
    """Tabla con celdas editables, estilo consistente."""
    def __init__(self, cols, headers, anchos):
        super().__init__(0, cols)
        self.setHorizontalHeaderLabels(headers)
        self.verticalHeader().setVisible(False)
        self.setStyleSheet(QSS_TBL)
        self.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        hh = self.horizontalHeader()
        for c, w in enumerate(anchos):
            if w is None:
                hh.setSectionResizeMode(c, QHeaderView.ResizeMode.Stretch)
            else:
                hh.setSectionResizeMode(c, QHeaderView.ResizeMode.Fixed)
                self.setColumnWidth(c, w)

    def agregar_fila(self, valores):
        r = self.rowCount()
        self.insertRow(r)
        self.setRowHeight(r, 22)
        for c, v in enumerate(valores):
            al = (Qt.AlignmentFlag.AlignLeft if c == 0
                  else Qt.AlignmentFlag.AlignRight)
            it = QTableWidgetItem(str(v))
            it.setTextAlignment(al | Qt.AlignmentFlag.AlignVCenter)
            it.setForeground(Qt.GlobalColor.black if c == 0
                             else Qt.GlobalColor.darkBlue)
            self.setItem(r, c, it)

    def leer(self):
        out = []
        for r in range(self.rowCount()):
            fila = [self.item(r, c).text().strip() if self.item(r, c) else ""
                    for c in range(self.columnCount())]
            out.append(fila)
        return out

    def limpiar(self):
        self.setRowCount(0)


class TabDatos(QWidget):
    datos_cambiados = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f'background:{GRAY_RES};')
        self._build()
        self.limpiar_todo()          # arranca vacio

    # ──────────────────────────────────────────────────────────────
    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(6)

        fila = QHBoxLayout()
        fila.setSpacing(8)
        fila.addWidget(self._grupo_fluido())
        fila.addWidget(self._grupo_broca())
        fila.addWidget(self._grupo_operacion())
        fila.addStretch(1)          # el espacio sobrante va a la derecha
        root.addLayout(fila)

        fila2 = QHBoxLayout()
        fila2.setSpacing(8)
        fila2.addWidget(self._grupo_sarta(), 1)
        fila2.addWidget(self._grupo_hoyo(), 1)
        root.addLayout(fila2, 1)

        barra = QHBoxLayout()
        barra.addStretch(1)

        self.btn_limpiar = boton("Limpiar", 90)
        self.btn_limpiar.clicked.connect(self.limpiar_todo)
        barra.addWidget(self.btn_limpiar)

        self.btn_caso = boton("Cargar caso de referencia", 170)
        self.btn_caso.clicked.connect(self._cargar_referencia)
        barra.addWidget(self.btn_caso)

        self.btn_hcy2 = boton("Cargar pozo HCY-2", 150)
        self.btn_hcy2.clicked.connect(self._cargar_hcy2)
        barra.addWidget(self.btn_hcy2)

        self.btn_calc = boton("Calcular", 120)
        self.btn_calc.clicked.connect(lambda: self.datos_cambiados.emit())
        barra.addWidget(self.btn_calc)
        root.addLayout(barra)

    # ── Grupos ────────────────────────────────────────────────────
    def _grupo_fluido(self):
        g = QGroupBox("Fluido de perforacion")
        g.setStyleSheet(QSS_GROUP)
        g.setFixedSize(W_FLUIDO, ALTO_GRUPO)
        v = QVBoxLayout(g)
        v.setContentsMargins(8, 6, 8, 6)
        v.setSpacing(4)

        top = QGridLayout()
        top.setVerticalSpacing(4)
        top.setHorizontalSpacing(6)
        self.sp_rho = spin(0.0, 25.0, 0.0, 3, 0.1, W_CAMPO)
        top.addWidget(etiqueta("Densidad del lodo (ppg)"), 0, 0)
        top.addWidget(self.sp_rho, 0, 1)
        top.setColumnStretch(0, 1)          # empuja el campo a la derecha
        v.addLayout(top)

        v.addWidget(seccion("Lecturas de viscosimetro Fann"))

        gf = QGridLayout()
        gf.setVerticalSpacing(4)
        gf.setHorizontalSpacing(6)
        self.sp_R600 = spin(0, 400, 0, 1, 1, W_CAMPO)
        self.sp_R300 = spin(0, 400, 0, 1, 1, W_CAMPO)
        self.sp_R100 = spin(0, 400, 0, 1, 1, W_CAMPO)
        self.sp_R3   = spin(0, 400, 0, 1, 1, W_CAMPO)
        for i, (t, s) in enumerate([("R600 (600 rpm)", self.sp_R600),
                                    ("R300 (300 rpm)", self.sp_R300),
                                    ("R100 (100 rpm)", self.sp_R100),
                                    ("R3   (3 rpm)",   self.sp_R3)]):
            gf.addWidget(etiqueta(t), i, 0)
            gf.addWidget(s, i, 1)
            s.valueChanged.connect(self._refrescar_params)
        gf.setColumnStretch(0, 1)
        v.addLayout(gf)
        v.addStretch(1)
        return g

    def _grupo_broca(self):
        g = QGroupBox("Broca / Trepano")
        g.setStyleSheet(QSS_GROUP)
        g.setFixedSize(W_BROCA, ALTO_GRUPO)
        v = QVBoxLayout(g)
        v.setContentsMargins(8, 6, 8, 6)
        v.setSpacing(4)

        top = QGridLayout()
        top.setVerticalSpacing(4)
        top.setHorizontalSpacing(6)
        self.sp_dbroca = spin(0.0, 30.0, 0.0, 3, 0.125, W_CAMPO)
        top.addWidget(etiqueta("Diametro de broca (in)"), 0, 0)
        top.addWidget(self.sp_dbroca, 0, 1)
        top.setColumnStretch(0, 1)
        v.addLayout(top)

        v.addWidget(seccion("Boquillas  (en 1/32 de pulgada)"))

        gb = QGridLayout()
        gb.setVerticalSpacing(4)
        gb.setHorizontalSpacing(6)
        self.ed_boq = []
        for i in range(6):
            e = campo("", W_CHICO, decimales=False, vmin=0, vmax=64)
            self.ed_boq.append(e)
            e.textChanged.connect(self._refrescar_params)
            r, c = i // 2, i % 2
            gb.addWidget(etiqueta(f"Boquilla N{i+1}"), r, c * 2)
            gb.addWidget(e, r, c * 2 + 1)
        gb.setColumnStretch(0, 1)
        gb.setColumnStretch(2, 1)
        v.addLayout(gb)
        v.addStretch(1)
        return g

    def _grupo_operacion(self):
        g = QGroupBox("Operacion")
        g.setStyleSheet(QSS_GROUP)
        g.setFixedSize(W_OPER, ALTO_GRUPO)
        v = QVBoxLayout(g)
        v.setContentsMargins(8, 6, 8, 6)
        v.setSpacing(4)

        self.sp_psup = spin(0, 1000, 0, 1, 5, W_CAMPO)
        self.sp_pmot = spin(0, 3000, 0, 1, 10, W_CAMPO)
        self.sp_tvd  = spin(0, 40000, 0, 0, 100, W_CAMPO)

        top = QGridLayout()
        top.setVerticalSpacing(4)
        top.setHorizontalSpacing(6)
        for i, (t, s) in enumerate([
                ("Perdida en superficie (psi)", self.sp_psup),
                ("Diferencial motor / MWD (psi)", self.sp_pmot),
                ("TVD, 0 = usar MD (ft)", self.sp_tvd)]):
            top.addWidget(etiqueta(t), i, 0)
            top.addWidget(s, i, 1)
        top.setColumnStretch(0, 1)
        v.addLayout(top)

        v.addWidget(seccion("Caudales a evaluar  (gpm)"))

        gq = QGridLayout()
        gq.setVerticalSpacing(4)
        gq.setHorizontalSpacing(6)
        self.ed_Q = []
        for i in range(6):
            e = campo("", W_CHICO, vmin=0, vmax=5000)
            self.ed_Q.append(e)
            r, c = i // 2, i % 2
            gq.addWidget(etiqueta(f"Caudal N{i+1}"), r, c * 2)
            gq.addWidget(e, r, c * 2 + 1)
        gq.setColumnStretch(0, 1)
        gq.setColumnStretch(2, 1)
        v.addLayout(gq)

        bot = QGridLayout()
        bot.setVerticalSpacing(4)
        bot.setHorizontalSpacing(6)
        self.sp_Qop = spin(0, 5000, 0, 0, 25, W_CAMPO)
        bot.addWidget(etiqueta("Caudal de operacion (gpm)"), 0, 0)
        bot.addWidget(self.sp_Qop, 0, 1)
        bot.setColumnStretch(0, 1)
        v.addLayout(bot)
        v.addStretch(1)
        return g

    def _grupo_sarta(self):
        g = QGroupBox("Sarta de perforacion  (de superficie hacia el fondo)")
        g.setStyleSheet(QSS_GROUP)
        l = QVBoxLayout(g)
        l.setContentsMargins(8, 6, 8, 6)
        l.setSpacing(4)

        self.tb_sarta = _TablaEditable(
            4, ["Componente", "OD (in)", "ID (in)", "Longitud (ft)"],
            [None, 75, 75, 95])
        l.addWidget(self.tb_sarta)
        self.tb_sarta.itemChanged.connect(self._refrescar_params)

        b = QHBoxLayout()
        b1 = boton("Agregar", 90)
        b2 = boton("Eliminar", 90)
        b1.clicked.connect(
            lambda: self.tb_sarta.agregar_fila(["Nuevo", 5.0, 4.276, 1000]))
        b2.clicked.connect(lambda: self._eliminar(self.tb_sarta))
        b.addWidget(b1); b.addWidget(b2); b.addStretch()
        self.lbl_md = etiqueta("", dim=True)
        b.addWidget(self.lbl_md)
        l.addLayout(b)
        return g

    def _grupo_hoyo(self):
        g = QGroupBox("Geometria del hoyo  (revestimientos, hoyo abierto, washout)")
        g.setStyleSheet(QSS_GROUP)
        l = QVBoxLayout(g)
        l.setContentsMargins(8, 6, 8, 6)
        l.setSpacing(4)

        self.tb_hoyo = _TablaEditable(
            5, ["Tramo", "ID (in)", "Tope (ft)", "Base (ft)", "Tipo"],
            [None, 70, 80, 80, 80])
        l.addWidget(self.tb_hoyo)
        self.tb_hoyo.itemChanged.connect(self._refrescar_params)

        b = QHBoxLayout()
        b1 = boton("Agregar", 90)
        b2 = boton("Eliminar", 90)
        b3 = boton("Insertar washout", 130)
        b1.clicked.connect(
            lambda: self.tb_hoyo.agregar_fila(["Nuevo", 8.5, 0, 1000, "hoyo"]))
        b2.clicked.connect(lambda: self._eliminar(self.tb_hoyo))
        b3.clicked.connect(self._insertar_washout)
        b.addWidget(b1); b.addWidget(b2); b.addWidget(b3); b.addStretch()
        self.lbl_hoyo = etiqueta("", dim=True)
        b.addWidget(self.lbl_hoyo)
        l.addLayout(b)
        return g

    # ── Acciones ──────────────────────────────────────────────────
    def _eliminar(self, tabla):
        r = tabla.currentRow()
        if r >= 0:
            tabla.removeRow(r)
            self._refrescar_params()

    def _insertar_washout(self):
        self.tb_hoyo.agregar_fila(["Washout", 12.0, 0, 0, "washout"])
        dlg.info(self, "Tramo de washout agregado.\n\n"
                       "Ajuste el diametro, el tope y la base. Los tramos de\n"
                       "hoyo adyacentes deben recortarse para no solaparse.")

    def limpiar_todo(self):
        """Deja todos los campos vacios / en cero."""
        for s in (self.sp_rho, self.sp_R600, self.sp_R300, self.sp_R100,
                  self.sp_R3, self.sp_dbroca, self.sp_psup, self.sp_pmot,
                  self.sp_tvd, self.sp_Qop):
            s.setValue(0.0)
        for e in self.ed_boq + self.ed_Q:
            e.setText("")
        self.tb_sarta.limpiar()
        self.tb_hoyo.limpiar()
        self._refrescar_params()

    def _cargar_referencia(self):
        self.cargar_pozo(pozo_referencia(con_washout=False))
        for i, q in enumerate([100, 200, 300, 400, 500]):
            self.ed_Q[i].setText(str(q))
        self.sp_Qop.setValue(400)
        dlg.info(self, "Caso de referencia cargado.\n\n"
                       "Pozo ejemplo del paper de University of Calgary (2005).\n"
                       "13000 ft / lodo 8.6 ppg / 3 boquillas de 12/32 in.")

    def _cargar_hcy2(self):
        self.cargar_pozo(pozo_hcy2())
        for i, q in enumerate([390, 450, 500, 550, 600, 650]):
            self.ed_Q[i].setText(str(q))
        self.sp_Qop.setValue(550)
        dlg.info(self, "Caso de campo cargado.\n\n"
                       "Pozo Huacaya-2 (HCY-2) - fase 12 1/4\".\n"
                       "Los Monos / Huamampampa, 3570 - 4290 m MD.\n"
                       "Lodo 14.5 ppg / BHA completo con Power Drive.\n"
                       "Boquillas 4x15 + 2x14 (1/32 in).\n\n"
                       "Calibrado a 550 gpm: 2453 psi, 177 ft/s, HSI 1.1.")

    # ── Serializacion ─────────────────────────────────────────────
    def cargar_pozo(self, p: Pozo):
        f = p.fluido
        self.sp_rho.setValue(f.rho)
        self.sp_R600.setValue(f.R600); self.sp_R300.setValue(f.R300)
        self.sp_R100.setValue(f.R100); self.sp_R3.setValue(f.R3)

        self.tb_sarta.limpiar()
        for t in p.sarta:
            self.tb_sarta.agregar_fila([t.nombre, t.OD, t.ID, t.longitud])

        self.tb_hoyo.limpiar()
        for h in p.hoyo:
            self.tb_hoyo.agregar_fila(
                [h.nombre, h.ID, h.prof_tope, h.prof_base, h.tipo])

        for i, e in enumerate(self.ed_boq):
            e.setText(str(p.boquillas[i]) if i < len(p.boquillas) else "")

        self.sp_psup.setValue(p.dp_superficie)
        self.sp_pmot.setValue(p.dp_motor)
        self.sp_tvd.setValue(p.tvd)
        if p.hoyo:
            self.sp_dbroca.setValue(p.hoyo[-1].ID)
        self._refrescar_params()

    def get_pozo(self) -> Pozo:
        f = Fluido(rho=self.sp_rho.value(),
                   R600=self.sp_R600.value(), R300=self.sp_R300.value(),
                   R100=self.sp_R100.value(), R3=self.sp_R3.value())
        sarta = []
        for fila in self.tb_sarta.leer():
            try:
                sarta.append(TramoSarta(fila[0], float(fila[1]),
                                        float(fila[2]), float(fila[3])))
            except (ValueError, IndexError):
                continue
        hoyo = []
        for fila in self.tb_hoyo.leer():
            try:
                hoyo.append(TramoHoyo(fila[0], float(fila[1]), float(fila[2]),
                                      float(fila[3]),
                                      fila[4] if len(fila) > 4 else "hoyo"))
            except (ValueError, IndexError):
                continue
        hoyo.sort(key=lambda h: h.prof_tope)

        # Boquillas: los campos vacios o en cero NO se instalan
        boq = []
        for e in self.ed_boq:
            v = leer_campo(e)
            if v is not None and v > 0:
                boq.append(int(v))

        return Pozo(fluido=f, sarta=sarta, hoyo=hoyo, boquillas=boq,
                    dp_superficie=self.sp_psup.value(),
                    dp_motor=self.sp_pmot.value(),
                    tvd=self.sp_tvd.value())

    def get_caudales(self):
        """Los campos vacios se ignoran: ese caudal no se analiza."""
        qs = []
        for e in self.ed_Q:
            v = leer_campo(e)
            if v is not None and v > 0:
                qs.append(v)
        return sorted(set(qs))

    def get_Q_operacion(self):
        return self.sp_Qop.value()

    def get_d_broca(self):
        return self.sp_dbroca.value()

    # ── Validacion ────────────────────────────────────────────────
    def validar(self):
        errs = []
        p = self.get_pozo()
        if not p.sarta:
            errs.append("La sarta esta vacia.")
        if not p.hoyo:
            errs.append("La geometria del hoyo esta vacia.")
        if not p.boquillas:
            errs.append("No hay ninguna boquilla definida.")
        if self.sp_Qop.value() <= 0:
            errs.append("El caudal de operacion debe ser mayor que cero.")
        if p.fluido.rho <= 0:
            errs.append("La densidad del lodo debe ser mayor que cero.")
        if self.sp_dbroca.value() <= 0:
            errs.append("El diametro de la broca debe ser mayor que cero.")

        for t in p.sarta:
            if t.ID >= t.OD:
                errs.append(f"'{t.nombre}': el ID ({t.ID}) debe ser menor "
                            f"que el OD ({t.OD}).")
            if t.longitud <= 0:
                errs.append(f"'{t.nombre}': longitud invalida.")

        md = p.prof_broca()
        cubierto = 0.0
        for h in p.hoyo:
            if h.prof_base <= h.prof_tope:
                errs.append(f"'{h.nombre}': la base debe ser mayor que el tope.")
            cubierto += max(0.0, min(h.prof_base, md) - max(h.prof_tope, 0.0))
        if md > 0 and abs(cubierto - md) > 1.0:
            errs.append(f"Los tramos de hoyo cubren {cubierto:,.0f} ft pero la "
                        f"broca esta a {md:,.0f} ft. Revise solapes o vacios.")

        for (nm, D2, D1, L, a, b) in p.tramos_anulares():
            if D1 >= D2:
                errs.append(f"Anular '{nm}': el OD de la sarta ({D1}) es mayor "
                            f"o igual al ID del hoyo ({D2}).")

        f = p.fluido
        if f.R600 <= f.R300:
            errs.append("R600 debe ser mayor que R300.")
        if f.R100 <= f.R3:
            errs.append("R100 debe ser mayor que R3.")
        return errs

    # ── Panel de parametros reologicos ────────────────────────────
    def _refrescar_params(self):
        try:
            p = self.get_pozo()
            md = p.prof_broca()
            self.lbl_md.setText(f"Profundidad de broca: {md:,.0f} ft"
                                if md > 0 else "")
            self.lbl_hoyo.setText(
                f"Cobertura: 0 - {max(h.prof_base for h in p.hoyo):,.0f} ft"
                if p.hoyo else "")
        except Exception:
            pass
