# HydraPhase v1.0
Simulador de hidraulica de perforacion — Modelo de Ley de Potencia (Power Law)

## Ejecutar
```
pip install PyQt6 matplotlib numpy
python app_hidra.py
```

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
| `tab_esquema.py` | Esquema del pozo: corte 2D a escala + vista 3D |
| `app_hidra.py` | Ventana principal |
| `test_validacion.py` | Suite de regresion |

## Unidades internas
psi · ft · in · gpm · ppg · ft/s · cp · boquillas en 1/32"

## NOTA sobre el paper de referencia
Las tablas 2, 3, 4 y 5 rotulan las presiones como "KPa". Es un error:
los valores son **psi**. Verificado reproduciendo la Tabla 3 digito por digito.

---

## Compilar el ejecutable de Windows

### Local
```
pip install -r requirements.txt pyinstaller
pyinstaller HydraPhase.spec --noconfirm --clean
```
El binario queda en `dist/HydraPhase.exe`.

### GitHub Actions
El workflow `.github/workflows/build.yml` tiene tres jobs encadenados:

1. **test** (ubuntu) — corre `test_validacion.py`. Si el motor deja de reproducir
   las tablas del paper, la compilacion **no se ejecuta**.
2. **build** (windows) — PyInstaller `--onefile --windowed`, sube `HydraPhase.exe`
   como artefacto (90 dias de retencion).
3. **release** — solo al empujar un tag `v*`; publica el .exe en Releases.

```
git tag v1.0
git push --tags       # -> dispara el release automatico
```

Tambien se puede lanzar a mano desde la pestana **Actions** (`workflow_dispatch`).

### Icono
Si colocas un `hydraphase.ico` en la raiz, el `.spec` lo detecta y lo embebe
automaticamente. Si no existe, compila igual sin icono.
