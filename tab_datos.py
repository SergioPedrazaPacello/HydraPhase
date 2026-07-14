"""Pestana 1 - Datos de entrada del pozo, fluido y sarta."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QAbstractItemView, QComboBox, QGroupBox, QLabel)
from PyQt6.QtCore import Qt, pyqtSignal

from estilo import (WHITE, GRAY_LBL, GRAY_RES, GRAY_HDR, BORDER, TEXT, TEXT_RES,
                    TEXT_DIM, FONT_F, FS, QSS_TBL, QSS_GROUP, QSS_COMBO,
                    cell, seccion, titulo, etiqueta, boton, spin, ispin)
from engine_hidraulica import (Fluido, TramoSarta, TramoHoyo, Pozo,
                               pozo_referencia)
import dialogos as dlg


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
            fila = []
            for c in range(self.columnCount()):
                it = self.item(r, c)
                fila.append(it.text().strip() if it else "")
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
        self.cargar_pozo(pozo_referencia(con_washout=False))

    # ──────────────────────────────────────────────────────────────
    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(6)

        fila = QHBoxLayout()
        fila.setSpacing(8)
        fila.addWidget(self._grupo_fluido(), 1)
        fila.addWidget(self._grupo_broca(), 1)
        fila.addWidget(self._grupo_operacion(), 1)
        root.addLayout(fila)

        fila2 = QHBoxLayout()
        fila2.setSpacing(8)
        fila2.addWidget(self._grupo_sarta(), 1)
        fila2.addWidget(self._grupo_hoyo(), 1)
        root.addLayout(fila2, 1)

        # ── Barra inferior ────────────────────────────────────────
        barra = QHBoxLayout()
        self.lbl_params = QLabel("")
        self.lbl_params.setStyleSheet(
            f'background:{GRAY_LBL};border:1px solid {BORDER};'
            f'color:{TEXT_RES};font-family:"{FONT_F}";font-size:{FS}pt;'
            f'padding:4px 8px;')
        barra.addWidget(self.lbl_params, 1)

        self.btn_caso = boton("Cargar caso de referencia", 180)
        self.btn_caso.clicked.connect(self._cargar_referencia)
        barra.addWidget(self.btn_caso)

        self.btn_calc = boton("CALCULAR", 130)
        self.btn_calc.clicked.connect(lambda: self.datos_cambiados.emit())
        barra.addWidget(self.btn_calc)
        root.addLayout(barra)

        self._refrescar_params()

    # ── Grupos ────────────────────────────────────────────────────
    def _grupo_fluido(self):
        g = QGroupBox("Fluido de perforacion")
        g.setStyleSheet(QSS_GROUP)
        l = QGridLayout(g)
        l.setContentsMargins(8, 6, 8, 6)
        l.setVerticalSpacing(4)

        self.sp_rho = spin(6.0, 25.0, 8.6, 3, 0.1)
        l.addWidget(etiqueta("Densidad del lodo"), 0, 0)
        l.addWidget(self.sp_rho, 0, 1)
        l.addWidget(etiqueta("ppg", dim=True), 0, 2)

        l.addWidget(seccion("Lecturas de viscosimetro Fann"), 1, 0, 1, 3)

        self.sp_R600 = spin(0, 400, 68, 1, 1)
        self.sp_R300 = spin(0, 400, 50, 1, 1)
        self.sp_R100 = spin(0, 400, 34, 1, 1)
        self.sp_R3   = spin(0, 400, 18, 1, 1)
        for i, (t, s, uso) in enumerate([
                ("R600 (600 rpm)", self.sp_R600, "tuberia"),
                ("R300 (300 rpm)", self.sp_R300, "tuberia"),
                ("R100 (100 rpm)", self.sp_R100, "anular"),
                ("R3   (3 rpm)",   self.sp_R3,   "anular")]):
            l.addWidget(etiqueta(t), 2 + i, 0)
            l.addWidget(s, 2 + i, 1)
            l.addWidget(etiqueta(f"-> {uso}", dim=True), 2 + i, 2)
            s.valueChanged.connect(self._refrescar_params)

        l.setColumnStretch(0, 1)
        l.setRowStretch(6, 1)
        return g

    def _grupo_broca(self):
        g = QGroupBox("Broca / Trepano")
        g.setStyleSheet(QSS_GROUP)
        l = QGridLayout(g)
        l.setContentsMargins(8, 6, 8, 6)
        l.setVerticalSpacing(4)

        self.sp_dbroca = spin(3.0, 30.0, 7.875, 3, 0.125)
        l.addWidget(etiqueta("Diametro de broca"), 0, 0)
        l.addWidget(self.sp_dbroca, 0, 1)
        l.addWidget(etiqueta("in", dim=True), 0, 2)

        l.addWidget(seccion("Boquillas  (en 1/32 de pulgada)"), 1, 0, 1, 3)
        self.sp_boq = []
        for i in range(6):
            s = ispin(0, 40, 12 if i < 3 else 0, 60)
            self.sp_boq.append(s)
            r, c = 2 + i // 3, i % 3
            cont = QHBoxLayout()
            w = QWidget()
            w.setStyleSheet('background:transparent;')
            cont.setContentsMargins(0, 0, 0, 0)
            cont.addWidget(etiqueta(f"N{i+1}"))
            cont.addWidget(s)
            w.setLayout(cont)
            l.addWidget(w, r, c)
            s.valueChanged.connect(self._refrescar_params)

        l.addWidget(etiqueta("0 = boquilla ciega / no instalada", dim=True),
                    4, 0, 1, 3)
        l.setRowStretch(5, 1)
        return g

    def _grupo_operacion(self):
        g = QGroupBox("Operacion")
        g.setStyleSheet(QSS_GROUP)
        l = QGridLayout(g)
        l.setContentsMargins(8, 6, 8, 6)
        l.setVerticalSpacing(4)

        self.sp_psup = spin(0, 1000, 50, 1, 5)
        self.sp_pmot = spin(0, 3000, 0, 1, 10)
        self.sp_tvd  = spin(0, 40000, 13000, 0, 100, 100)

        for i, (t, s, u) in enumerate([
                ("Perdida en superficie", self.sp_psup, "psi"),
                ("Diferencial motor/MWD", self.sp_pmot, "psi"),
                ("TVD (0 = usar MD)", self.sp_tvd, "ft")]):
            l.addWidget(etiqueta(t), i, 0)
            l.addWidget(s, i, 1)
            l.addWidget(etiqueta(u, dim=True), i, 2)

        l.addWidget(seccion("Caudales a evaluar (gpm)"), 3, 0, 1, 3)
        self.sp_Q = []
        for i in range(5):
            s = spin(10, 2000, [100, 200, 300, 400, 500][i], 0, 25, 70)
            self.sp_Q.append(s)
            l.addWidget(s, 4 + i // 3, i % 3)

        self.sp_Qop = spin(10, 2000, 400, 0, 25, 90)
        l.addWidget(etiqueta("Caudal de operacion"), 6, 0)
        l.addWidget(self.sp_Qop, 6, 1)
        l.addWidget(etiqueta("gpm", dim=True), 6, 2)
        l.setColumnStretch(0, 1)
        l.setRowStretch(7, 1)
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
        b1 = boton("+ Agregar", 90)
        b2 = boton("- Eliminar", 90)
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
        b1 = boton("+ Agregar", 90)
        b2 = boton("- Eliminar", 90)
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
        self.tb_hoyo.agregar_fila(["Washout", 19.686, 6000, 11000, "washout"])
        dlg.info(self, "Tramo de washout agregado.\n\n"
                       "Ajuste el diametro, tope y base. Los tramos de hoyo\n"
                       "adyacentes deben recortarse para no solaparse.")

    def _cargar_referencia(self):
        self.cargar_pozo(pozo_referencia(con_washout=False))
        dlg.info(self, "Caso de referencia cargado.\n\n"
                       "Pozo ejemplo del paper de University of Calgary (2005).\n"
                       "Tabla 1: 13000 ft, lodo 8.6 ppg, 3 boquillas de 12/32\".")

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

        for i, s in enumerate(self.sp_boq):
            s.setValue(p.boquillas[i] if i < len(p.boquillas) else 0)

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
        boq = [s.value() for s in self.sp_boq if s.value() > 0]
        return Pozo(fluido=f, sarta=sarta, hoyo=hoyo, boquillas=boq,
                    dp_superficie=self.sp_psup.value(),
                    dp_motor=self.sp_pmot.value(),
                    tvd=self.sp_tvd.value())

    def get_caudales(self):
        return sorted({s.value() for s in self.sp_Q})

    def get_Q_operacion(self):
        return self.sp_Qop.value()

    def get_d_broca(self):
        return self.sp_dbroca.value()

    # ── Validacion ────────────────────────────────────────────────
    def validar(self):
        """Devuelve lista de mensajes de error (vacia si todo esta OK)."""
        errs = []
        p = self.get_pozo()
        if not p.sarta:
            errs.append("La sarta esta vacia.")
        if not p.hoyo:
            errs.append("La geometria del hoyo esta vacia.")
        if not p.boquillas:
            errs.append("No hay boquillas definidas.")

        for t in p.sarta:
            if t.ID >= t.OD:
                errs.append(f"'{t.nombre}': el ID ({t.ID}) debe ser menor "
                            f"que el OD ({t.OD}).")
            if t.longitud <= 0:
                errs.append(f"'{t.nombre}': longitud invalida.")

        md = p.prof_broca()
        # cobertura del hoyo
        cubierto = 0.0
        for h in p.hoyo:
            if h.prof_base <= h.prof_tope:
                errs.append(f"'{h.nombre}': base <= tope.")
            cubierto += max(0.0, min(h.prof_base, md) - max(h.prof_tope, 0.0))
        if abs(cubierto - md) > 1.0:
            errs.append(f"Los tramos de hoyo cubren {cubierto:.0f} ft pero la "
                        f"broca esta a {md:.0f} ft. Revise solapes o vacios.")

        # OD de sarta vs ID de hoyo
        for (nm, D2, D1, L, a, b) in p.tramos_anulares():
            if D1 >= D2:
                errs.append(f"Anular '{nm}': OD de sarta ({D1}) >= "
                            f"ID de hoyo ({D2}).")

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
            f = p.fluido
            n_t, K_t = f.n_tuberia(), f.K_tuberia()
            n_a, K_a = f.n_anular(), f.K_anular()
            md = p.prof_broca()
            at = p.area_boquillas()
            self.lbl_params.setText(
                f"  Ley de Potencia    "
                f"TUBERIA: n = {n_t:.4f}   K = {K_t:.2f} eq cp        "
                f"ANULAR: n = {n_a:.4f}   K = {K_a:.2f} eq cp        "
                f"TFA = {at:.4f} in\u00b2        MD broca = {md:,.0f} ft")
            self.lbl_md.setText(f"Profundidad de broca: {md:,.0f} ft")
            if p.hoyo:
                self.lbl_hoyo.setText(
                    f"Cobertura: 0 - {max(h.prof_base for h in p.hoyo):,.0f} ft")
        except Exception:
            self.lbl_params.setText("  Datos incompletos o invalidos")
