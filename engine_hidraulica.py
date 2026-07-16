"""
HydraPhase - Motor de calculo de hidraulica de perforacion
==========================================================
Modelo reologico : Ley de Potencia (Power Law)
Referencia       : Alinejad Mofrad, M. "Drilling Hydraulics Simulation Analysis
                   and Comparison to a Field Case", University of Calgary, 2005.
                   Bourgoyne et al., "Applied Drilling Engineering", SPE Vol.2, Cap.4

UNIDADES INTERNAS (sistema de campo / API):
    Presion .............. psi
    Gradiente ............ psi/ft
    Longitud, profundidad. ft
    Diametro ............. in
    Caudal ............... gal/min (gpm)
    Densidad ............. lbm/gal (ppg)
    Velocidad ............ ft/s
    Viscosidad efectiva .. cp (centipoise equivalente)
    Boquillas ............ 1/32 in  (entero, p.ej. 12 = 12/32")

NOTA IMPORTANTE SOBRE EL PAPER DE REFERENCIA:
    Las tablas 2, 3, 4 y 5 del paper rotulan las presiones como "KPa".
    Es un error de rotulado: los valores son psi. Verificado reproduciendo
    la Tabla 3 digito por digito con las formulas del Apendice A.
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import List, Tuple

# ── Constantes del modelo ──────────────────────────────────────────────
NRE_CRIT   = 2100.0      # Reynolds critico laminar/turbulento
C_BOQ      = 156.0       # constante de boquillas (embebe Cd = 0.95)
GRAD_PSI   = 0.052       # psi/(ppg*ft)  -> presion hidrostatica
CD_BOQ     = 0.95        # coeficiente de descarga implicito en C_BOQ



# ══════════════════════════════════════════════════════════════════════
# MODELO DE DATOS
# ══════════════════════════════════════════════════════════════════════
@dataclass
class Fluido:
    """Lodo de perforacion caracterizado por lecturas de viscosimetro Fann."""
    rho: float = 8.6          # ppg
    R600: float = 68.0
    R300: float = 50.0
    R100: float = 34.0
    R3:   float = 18.0
    nombre: str = "Lodo base agua"

    # ── Parametros de Ley de Potencia ──────────────────────────────
    def n_tuberia(self) -> float:
        """Indice de comportamiento de flujo (interior de tuberia). 600/300 rpm."""
        return 3.32 * math.log10(self.R600 / self.R300)

    def K_tuberia(self) -> float:
        """Indice de consistencia (interior de tuberia), eq cp."""
        return 5.11 * self.R600 / (1022.0 ** self.n_tuberia())

    def n_anular(self) -> float:
        """Indice de comportamiento de flujo (espacio anular). 100/3 rpm."""
        return 0.657 * math.log10(self.R100 / self.R3)

    def K_anular(self) -> float:
        """Indice de consistencia (espacio anular), eq cp."""
        return 5.11 * self.R100 / (170.2 ** self.n_anular())


@dataclass
class TramoSarta:
    """Componente de la sarta de perforacion (de arriba hacia abajo)."""
    nombre: str
    OD: float          # in
    ID: float          # in
    longitud: float    # ft


@dataclass
class TramoHoyo:
    """Tramo de hoyo o revestimiento (de superficie hacia el fondo)."""
    nombre: str
    ID: float          # in  (ID del casing o diametro del hoyo abierto)
    prof_tope: float   # ft
    prof_base: float   # ft
    tipo: str = "hoyo"   # "casing" | "hoyo" | "washout"


@dataclass
class Pozo:
    fluido: Fluido = field(default_factory=Fluido)
    sarta: List[TramoSarta] = field(default_factory=list)
    hoyo:  List[TramoHoyo]  = field(default_factory=list)
    boquillas: List[int] = field(default_factory=lambda: [12, 12, 12])  # 1/32 in
    dp_superficie: float = 50.0     # psi  (perdida en equipo de superficie)
    dp_motor: float = 0.0           # psi  (diferencial motor de fondo / MWD)
    tvd: float = 0.0                # ft; si 0 -> se usa la profundidad de la broca

    # ── Derivados ──────────────────────────────────────────────────
    def prof_broca(self) -> float:
        return sum(t.longitud for t in self.sarta)

    def tvd_efectiva(self) -> float:
        return self.tvd if self.tvd > 0 else self.prof_broca()

    def area_boquillas(self) -> float:
        """Area total de flujo de las boquillas, in^2."""
        return sum(math.pi / 4.0 * (d / 32.0) ** 2 for d in self.boquillas)

    def sum_dn2(self) -> float:
        """Suma de Dn^2 con Dn en 1/32 de pulgada (para la formula del paper)."""
        return sum(float(d) ** 2 for d in self.boquillas)

    # ── Segmentacion del espacio anular ────────────────────────────
    def tramos_anulares(self) -> List[Tuple[str, float, float, float, float, float]]:
        """
        Interseca la particion de la sarta con la particion del hoyo.

        Devuelve lista de tuplas:
            (nombre, D_hoyo, OD_sarta, longitud, prof_tope, prof_base)
        ordenada de superficie hacia el fondo.
        """
        # Rangos de profundidad de cada componente de sarta
        rangos_sarta = []
        z = 0.0
        for t in self.sarta:
            rangos_sarta.append((z, z + t.longitud, t))
            z += t.longitud
        z_broca = z

        # Puntos de quiebre: extremos de sarta + extremos de hoyo
        quiebres = {0.0, z_broca}
        for a, b, _ in rangos_sarta:
            quiebres.add(a); quiebres.add(b)
        for h in self.hoyo:
            if 0.0 <= h.prof_tope <= z_broca: quiebres.add(h.prof_tope)
            if 0.0 <= h.prof_base <= z_broca: quiebres.add(h.prof_base)
        qs = sorted(q for q in quiebres if -1e-9 <= q <= z_broca + 1e-9)

        tramos = []
        for i in range(len(qs) - 1):
            a, b = qs[i], qs[i + 1]
            if b - a < 1e-6:
                continue
            mid = 0.5 * (a + b)
            # componente de sarta que ocupa este intervalo
            comp = next((t for (za, zb, t) in rangos_sarta if za <= mid < zb), None)
            # tramo de hoyo que ocupa este intervalo
            hh = next((h for h in self.hoyo if h.prof_tope <= mid < h.prof_base), None)
            if comp is None or hh is None:
                continue
            nombre = f"{comp.nombre} / {hh.nombre}"
            tramos.append((nombre, hh.ID, comp.OD, b - a, a, b))
        return tramos


# ══════════════════════════════════════════════════════════════════════
# CORRELACIONES DE FACTOR DE FRICCION
# ══════════════════════════════════════════════════════════════════════
def factor_friccion_turbulento(n: float, NRe: float) -> float:
    """
    Correlacion de Dodge-Metzner en la forma f = a / NRe^b
        a = (log10(n) + 3.93) / 50
        b = (1.75 - log10(n)) / 7
    Valida tanto para tuberia como para espacio anular.
    """
    log_n = math.log10(n)
    a = (log_n + 3.93) / 50.0
    b = (1.75 - log_n) / 7.0
    return a / (NRe ** b)


# ══════════════════════════════════════════════════════════════════════
# HIDRAULICA POR TRAMO
# ══════════════════════════════════════════════════════════════════════
@dataclass
class ResultadoTramo:
    nombre: str
    tipo: str            # "tuberia" | "anular"
    D: float             # in : ID (tuberia) o hidraulico D2-D1 (anular)
    longitud: float      # ft
    V: float             # ft/s
    mu_e: float          # cp
    NRe: float
    regimen: str         # "Laminar" | "Turbulento"
    f: float
    gradiente: float     # psi/ft
    dP: float            # psi
    prof_tope: float = 0.0
    prof_base: float = 0.0


def tramo_tuberia(nombre: str, ID: float, L: float, Q: float,
                  fl: Fluido, prof_tope=0.0, prof_base=0.0) -> ResultadoTramo:
    """Perdida de presion por friccion dentro de tuberia (DP, HWDP, DC)."""
    n, K, rho = fl.n_tuberia(), fl.K_tuberia(), fl.rho

    V = 0.408 * Q / ID ** 2                                     # ft/s
    mu_e = 100.0 * K * (96.0 * V / ID) ** (n - 1.0) \
                 * ((3.0 * n + 1.0) / (4.0 * n)) ** n           # cp
    NRe = 928.0 * rho * ID * V / mu_e

    if NRe < NRE_CRIT:
        f, reg = 16.0 / NRe, "Laminar"
    else:
        f, reg = factor_friccion_turbulento(n, NRe), "Turbulento"

    grad = f * V ** 2 * rho / (25.81 * ID)                      # psi/ft
    return ResultadoTramo(nombre, "tuberia", ID, L, V, mu_e, NRe, reg,
                          f, grad, grad * L, prof_tope, prof_base)


def tramo_anular(nombre: str, D2: float, D1: float, L: float, Q: float,
                 fl: Fluido, prof_tope=0.0, prof_base=0.0) -> ResultadoTramo:
    """
    Perdida de presion por friccion en espacio anular.
    D2 = diametro del hoyo/casing (in), D1 = OD de la sarta (in)
    Aproximacion de ranura (slot flow): f_laminar = 24/NRe
    """
    n, K, rho = fl.n_anular(), fl.K_anular(), fl.rho
    Dh = D2 - D1                                                # diametro hidraulico

    V = 0.408 * Q / (D2 ** 2 - D1 ** 2)                          # ft/s
    mu_e = 100.0 * K * (144.0 * V / Dh) ** (n - 1.0) \
                 * ((2.0 * n + 1.0) / (3.0 * n)) ** n            # cp
    NRe = 928.0 * rho * Dh * V / mu_e

    if NRe < NRE_CRIT:
        f, reg = 24.0 / NRe, "Laminar"
    else:
        f, reg = factor_friccion_turbulento(n, NRe), "Turbulento"

    grad = f * V ** 2 * rho / (25.81 * Dh)                       # psi/ft
    return ResultadoTramo(nombre, "anular", Dh, L, V, mu_e, NRe, reg,
                          f, grad, grad * L, prof_tope, prof_base)


# ══════════════════════════════════════════════════════════════════════
# HIDRAULICA DE LA BROCA
# ══════════════════════════════════════════════════════════════════════
@dataclass
class ResultadoBroca:
    dP: float          # psi
    v_boq: float       # ft/s  velocidad en las boquillas
    At: float          # in^2  area total de flujo
    HHP: float         # hp    potencia hidraulica en la broca
    HSI: float         # hp/in^2
    Fj: float          # lbf   fuerza de impacto del chorro
    pct_dP: float      # %     de la presion de bomba consumida en la broca


def hidraulica_broca(pozo: Pozo, Q: float, dP_total: float,
                     d_broca: float) -> ResultadoBroca:
    rho = pozo.fluido.rho
    sd2 = pozo.sum_dn2()
    if sd2 <= 0:
        return ResultadoBroca(0, 0, 0, 0, 0, 0, 0)

    dP = C_BOQ * rho * Q ** 2 / sd2 ** 2                      # psi
    At = pozo.area_boquillas()                                # in^2
    v_boq = 0.32086 * Q / At                                  # ft/s
    HHP = dP * Q / 1714.0                                     # hp
    A_broca = math.pi / 4.0 * d_broca ** 2
    HSI = HHP / A_broca if A_broca > 0 else 0.0
    Fj = 0.01823 * CD_BOQ * Q * math.sqrt(rho * dP)           # lbf
    pct = 100.0 * dP / dP_total if dP_total > 0 else 0.0
    return ResultadoBroca(dP, v_boq, At, HHP, HSI, Fj, pct)


# ══════════════════════════════════════════════════════════════════════
# CALCULO GLOBAL
# ══════════════════════════════════════════════════════════════════════
@dataclass
class ResultadoHidraulica:
    Q: float
    tramos_int: List[ResultadoTramo]
    tramos_ann: List[ResultadoTramo]
    broca: ResultadoBroca
    dp_superficie: float
    dp_motor: float
    dP_int: float          # suma interior
    dP_ann: float          # suma anular
    dP_parasita: float     # todo excepto la broca
    P_bomba: float         # psi
    P_hidrostatica: float  # psi  (columna estatica)
    ECD: float             # ppg
    HHP_bomba: float       # hp


def calcular(pozo: Pozo, Q: float, d_broca: float = None) -> ResultadoHidraulica:
    """Calculo hidraulico completo para un caudal Q (gpm)."""
    fl = pozo.fluido
    if d_broca is None:
        d_broca = pozo.hoyo[-1].ID if pozo.hoyo else 8.5

    # ── Interior de la sarta ──────────────────────────────────────
    tramos_int, z = [], 0.0
    for t in pozo.sarta:
        r = tramo_tuberia(t.nombre, t.ID, t.longitud, Q, fl, z, z + t.longitud)
        tramos_int.append(r)
        z += t.longitud

    # ── Espacio anular ────────────────────────────────────────────
    tramos_ann = []
    for (nm, D2, D1, L, za, zb) in pozo.tramos_anulares():
        tramos_ann.append(tramo_anular(nm, D2, D1, L, Q, fl, za, zb))
    # Se reporta de fondo hacia superficie (sentido del flujo de retorno)
    tramos_ann.reverse()

    dP_int = sum(r.dP for r in tramos_int)
    dP_ann = sum(r.dP for r in tramos_ann)

    # ── Broca ─────────────────────────────────────────────────────
    sd2 = pozo.sum_dn2()
    dP_bit = C_BOQ * fl.rho * Q ** 2 / sd2 ** 2 if sd2 > 0 else 0.0

    dP_parasita = pozo.dp_superficie + dP_int + dP_ann + pozo.dp_motor
    P_bomba = dP_parasita + dP_bit

    broca = hidraulica_broca(pozo, Q, P_bomba, d_broca)

    # ── Hidrostatica y ECD ────────────────────────────────────────
    tvd = pozo.tvd_efectiva()
    P_hid = GRAD_PSI * fl.rho * tvd
    ECD = fl.rho + dP_ann / (GRAD_PSI * tvd) if tvd > 0 else fl.rho

    HHP_bomba = P_bomba * Q / 1714.0

    return ResultadoHidraulica(Q, tramos_int, tramos_ann, broca,
                               pozo.dp_superficie, pozo.dp_motor,
                               dP_int, dP_ann, dP_parasita, P_bomba,
                               P_hid, ECD, HHP_bomba)


# ══════════════════════════════════════════════════════════════════════
# PERFIL U-TUBE  (presion vs distancia recorrida desde el standpipe)
# ══════════════════════════════════════════════════════════════════════
def perfil_utube(pozo: Pozo, res: ResultadoHidraulica):
    """
    Construye el perfil de presion a lo largo del recorrido del lodo:
    standpipe -> interior de sarta -> broca -> anular -> superficie.

    Devuelve dict con listas paralelas:
        L      : longitud U-Tube acumulada (ft)
        z      : profundidad vertical (ft)
        P_dyn  : presion dinamica / circulante (psi)
        P_hyd  : presion hidrostatica (psi)
        P_tot  : P_hyd + P_dyn (psi)
        etiquetas : nodos notables
    """
    rho = pozo.fluido.rho
    L_ac, z_ac = [0.0], [0.0]
    P_dyn = [res.P_bomba - res.dp_superficie]   # despues del equipo de superficie
    etiquetas = [("Standpipe", 0.0, P_dyn[0])]

    # Descenso por la sarta
    for r in res.tramos_int:
        L_ac.append(L_ac[-1] + r.longitud)
        z_ac.append(z_ac[-1] + r.longitud)
        P_dyn.append(P_dyn[-1] - r.dP)
    etiquetas.append(("Broca (entrada)", L_ac[-1], P_dyn[-1]))

    # Caida a traves de la broca (vertical, misma L y z)
    L_ac.append(L_ac[-1])
    z_ac.append(z_ac[-1])
    P_dyn.append(P_dyn[-1] - res.broca.dP)
    etiquetas.append(("Broca (salida)", L_ac[-1], P_dyn[-1]))

    # Ascenso por el anular (de fondo a superficie)
    for r in res.tramos_ann:
        L_ac.append(L_ac[-1] + r.longitud)
        z_ac.append(z_ac[-1] - r.longitud)
        P_dyn.append(P_dyn[-1] - r.dP)
    etiquetas.append(("Retorno superficie", L_ac[-1], P_dyn[-1]))

    P_hyd = [GRAD_PSI * rho * z for z in z_ac]
    P_tot = [h + d for h, d in zip(P_hyd, P_dyn)]
    return dict(L=L_ac, z=z_ac, P_dyn=P_dyn, P_hyd=P_hyd,
                P_tot=P_tot, etiquetas=etiquetas)


def barrido_caudal(pozo: Pozo, caudales, d_broca=None):
    """Calcula la hidraulica para una lista de caudales."""
    return [calcular(pozo, Q, d_broca) for Q in caudales]


# ══════════════════════════════════════════════════════════════════════
# CASO DE REFERENCIA (pozo ejemplo del paper - Tabla 1)
# ══════════════════════════════════════════════════════════════════════
def pozo_referencia(con_washout: bool = False) -> Pozo:
    fl = Fluido(rho=8.6, R600=68, R300=50, R100=34, R3=18)
    sarta = [TramoSarta("Drill Pipe", 5.0, 4.26, 12400.0),
             TramoSarta("Drill Collar", 6.5, 3.0, 600.0)]
    if con_washout:
        hoyo = [TramoHoyo("Casing", 8.75, 0.0, 1400.0, "casing"),
                TramoHoyo("Hoyo abierto", 7.875, 1400.0, 6000.0, "hoyo"),
                TramoHoyo("Washout", 19.686, 6000.0, 11000.0, "washout"),
                TramoHoyo("Hoyo abierto", 7.875, 11000.0, 13000.0, "hoyo")]
    else:
        hoyo = [TramoHoyo("Casing", 8.75, 0.0, 1400.0, "casing"),
                TramoHoyo("Hoyo abierto", 7.875, 1400.0, 13000.0, "hoyo")]
    return Pozo(fluido=fl, sarta=sarta, hoyo=hoyo, boquillas=[12, 12, 12],
                dp_superficie=50.0, dp_motor=0.0, tvd=13000.0)


# ══════════════════════════════════════════════════════════════════════
# CASO DE CAMPO - Pozo Huacaya-2 (HCY-2), fase 12 1/4"
# ══════════════════════════════════════════════════════════════════════
def pozo_hcy2() -> Pozo:
    """
    Caso de campo: Pozo Huacaya-2 (HCY-2, REPSOL E&P Bolivia).
    Fase 12 1/4" - Formaciones Los Monos / Huamampampa.
    Intervalo perforado 3570 - 4290 m MD  (11 713 - 14 075 ft).

    Fuente: Programa de Perforacion HCY-2, seccion 12 1/4".

    REOLOGIA (bloque "Propiedades del Lodo", lodo OBM Megadril):
        Densidad 13.5-14.8 ppg  ->  se toma 14.0 ppg (valor representativo)
        VP 35-60 cp   -> 47 cp
        YP 20-35 lb/100ft2 -> 27 lb/100ft2
            R600 = 2*VP + YP = 121
            R300 =   VP + YP =  74
        R100  estimada con API RP 13D:  R300 - (2/3)*VP = 43
        R3    = 10   (lectura R3/R6 = 10/20 del programa)

    ARREGLO:
        0      - 11 713 ft : Casing 13 3/8" 72 ppf  (ID nominal 12.347")
        11 713 - 14 075 ft : Hoyo abierto 12 1/4"   (broca PDC 12.25")

    SARTA (BHA con Power Drive, de superficie hacia el fondo):
        Drill Pipe 6 5/8", HWDP 6 5/8", Drill Collar 8", RSS/near-bit 9".
        La longitud del Drill Pipe rellena hasta la profundidad de broca.

    BOQUILLAS:
        No listadas de forma explicita en el programa; se infieren de la
        velocidad de chorro reportada (177 ft/s a 550 gpm -> TFA ~ 1.0 in2),
        lo que corresponde a 6 x 15/32".
    """
    fl = Fluido(rho=14.0, R600=121, R300=74, R100=43, R3=10,
                nombre="Lodo OBM Megadril (HCY-2 12 1/4\")")

    sarta = [
        TramoSarta("Drill Pipe 6 5/8\"", 6.625, 5.901, 13596.0),
        TramoSarta("HWDP 6 5/8\"",       6.625, 4.500,    93.0),
        TramoSarta("Drill Collar 8\"",   8.000, 3.000,   372.0),
        TramoSarta("RSS / near-bit 9\"", 9.000, 5.125,    14.0),
    ]

    hoyo = [
        TramoHoyo("Casing 13 3/8\" 72 ppf", 12.347,     0.0, 11713.0, "casing"),
        TramoHoyo("Hoyo abierto 12 1/4\"",  12.250, 11713.0, 14075.0, "hoyo"),
    ]

    return Pozo(fluido=fl, sarta=sarta, hoyo=hoyo,
                boquillas=[15, 15, 15, 15, 15, 15],
                dp_superficie=50.0, dp_motor=0.0, tvd=14038.0)
