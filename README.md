# HydraPhase v1.0
Simulador de hidraulica de perforacion — Modelo de Ley de Potencia (Power Law)

## Ejecutar
```
pip install -r requirements.txt
python app_hidra.py
```
El programa arranca **sin datos cargados**. Use el boton "Cargar caso de
referencia" para el pozo ejemplo del paper, o ingrese los suyos.

## Validacion
```
python test_validacion.py
```
Reproduce las Tablas 2, 3 y 4 del paper de University of Calgary (2005).
42/42 pruebas pasan con error maximo de 0.006 %.

## Modulos
| Archivo | Contenido |
|---|---|
| `engine_hidraulica.py` | Motor: reologia, segmentacion del anular, dP por tramo, boquillas, ECD, perfil U-Tube |
| `estilo.py` | Paleta y helpers (Win95 / Arial Narrow) |
| `dialogos.py` | info / advertencia / error / confirmar |
| `tab_datos.py` | Entrada: fluido, sarta, hoyo, boquillas, caudales |
| `tab_resultados.py` | Tabla de dP por tramo, balance, hidraulica de broca, ECD, barrido |
| `tab_graficas.py` | 7 graficas (figuras 1-6 del paper + distribucion de perdidas) |
| `app_hidra.py` | Ventana principal |
| `test_validacion.py` | Suite de regresion |
| `_archivado/tab_esquema.py` | Esquema del pozo 2D/3D — desactivado por ahora |

## Campos vacios
- **Boquilla Nx vacia** = boquilla no instalada (no entra en el area de flujo).
- **Caudal Nx vacio** = ese caudal no se evalua en el barrido.

## Unidades internas
psi · ft · in · gpm · ppg · ft/s · cp · boquillas en 1/32"

## Compilar el ejecutable de Windows
```
pyinstaller HydraPhase.spec --noconfirm --clean
```
En GitHub Actions: `.github/workflows/build.yml` (test → build → release por tag).

## NOTA sobre el paper de referencia
Las tablas 2, 3, 4 y 5 rotulan las presiones como "KPa". Es un error de
rotulado: los valores son **psi**. Verificado reproduciendo la Tabla 3
digito por digito.
