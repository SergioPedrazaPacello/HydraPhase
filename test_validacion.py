"""
Validacion de HydraPhase contra el pozo ejemplo del paper de University of
Calgary (2005). Reproduce las Tablas 2, 3 y 4.

Ejecutar:  python test_validacion.py
"""
from engine_hidraulica import (pozo_referencia, calcular, barrido_caudal,
                               perfil_utube)

TOL = 0.05  # % de tolerancia

# ── Referencias del paper ──────────────────────────────────────────────
T3_TRAMOS = {  # Tabla 3, Q = 400 gpm, sin washout  (psi, NO kPa)
    "Drill Pipe": 494.72,
    "Drill Collar": 104.32,
    "Drill Collar / Hoyo abierto": 37.30,
    "Drill Pipe / Hoyo abierto": 572.82,
    "Drill Pipe / Casing": 50.15,
}
T3_BROCA = 1150.21

T2_PBOMBA = {  # Tabla 2 - presion de bomba (psi)
    "sin": {100: 904.02, 200: 1281.87, 300: 1776.10, 400: 2459.52, 500: 3389.59},
    "con": {100: 721.05, 200: 1074.37, 300: 1552.76, 400: 2224.20, 500: 3144.55},
}
T2_PARAS = {
    "sin": {100: 832.14, 200: 994.32, 300: 1129.11, 400: 1309.31, 500: 1592.40},
    "con": {100: 649.16, 200: 786.82, 300: 905.77, 400: 1074.00, 500: 1347.36},
}
T4_ANN = {  # Tabla 4 - dP anular total (psi)
    "sin": {100: 549.49, 200: 623.14, 300: 670.72, 400: 660.27, 500: 699.16},
    "con": {100: 366.51, 200: 415.64, 300: 447.37, 400: 424.95, 500: 454.12},
}
T4_ECD = {
    "sin": {100: 9.4129, 200: 9.5218, 300: 9.5922, 400: 9.5767, 500: 9.6343},
    "con": {100: 9.1422, 200: 9.2148, 300: 9.2618, 400: 9.2286, 500: 9.2718},
}

fallos = []


def chk(nombre, calc, ref, tol=TOL):
    dif = abs(calc - ref) / abs(ref) * 100 if ref else 0.0
    ok = dif <= tol
    if not ok:
        fallos.append(nombre)
    print(f"  {'OK ' if ok else 'X  '} {nombre:<40s} "
          f"calc={calc:>11,.4f}  ref={ref:>11,.4f}  dif={dif:.4f}%")


print("=" * 84)
print("HydraPhase - VALIDACION contra el paper (University of Calgary, 2005)")
print("=" * 84)

# ── Tabla 3 : tramo por tramo, Q = 400 ────────────────────────────────
print("\n[TABLA 3]  Caidas de presion por tramo  (Q = 400 gpm, sin washout)")
p = pozo_referencia(False)
r = calcular(p, 400.0)
for t in r.tramos_int + r.tramos_ann:
    if t.nombre in T3_TRAMOS:
        chk(t.nombre, t.dP, T3_TRAMOS[t.nombre])
chk("Boquillas de la broca", r.broca.dP, T3_BROCA)

# ── Tablas 2 y 4 : barrido de caudal, ambos escenarios ────────────────
for esc, wo in [("sin", False), ("con", True)]:
    etiqueta = "SIN washout" if not wo else "CON washout"
    print(f"\n[TABLAS 2 y 4]  Barrido de caudal - {etiqueta}")
    pz = pozo_referencia(wo)
    for Q in [100, 200, 300, 400, 500]:
        rr = calcular(pz, float(Q))
        chk(f"P bomba   Q={Q}", rr.P_bomba, T2_PBOMBA[esc][Q])
        chk(f"P parasita Q={Q}", rr.dP_parasita, T2_PARAS[esc][Q])
        chk(f"dP anular  Q={Q}", rr.dP_ann, T4_ANN[esc][Q])
        chk(f"ECD        Q={Q}", rr.ECD, T4_ECD[esc][Q], tol=0.02)

# ── Coherencia del perfil U-Tube ──────────────────────────────────────
print("\n[COHERENCIA]  Perfil U-Tube")
pf = perfil_utube(p, r)
chk("Presion final en superficie (debe ser ~0)",
    pf["P_dyn"][-1] + 1000.0, 1000.0, tol=0.2)
suma = (r.dp_superficie + r.dP_int + r.broca.dP + r.dP_ann + r.dp_motor)
chk("Balance: suma de tramos = P bomba", suma, r.P_bomba, tol=1e-6)

print("\n" + "=" * 84)
if fallos:
    print(f"FALLARON {len(fallos)} PRUEBAS: {fallos}")
else:
    print("TODAS LAS PRUEBAS PASARON  (tolerancia 0.05 %)")
print("=" * 84)
