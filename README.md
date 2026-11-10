# Práctica P2 (evaluable) — Tema 2: autopsia de sistemas, herramientas y CI (versión local)

Arquitecturas Software para Robótica · UCJC · Tema 2 · trabajo **individual** y **evaluable**.
El enunciado completo (requisitos, entrega, rúbrica y plazo) está en `Practica_P2_Individual_Evaluable.docx`.
Este paquete es el material de trabajo. Une el kit de la S8 (diagnóstico con bags) y el de la S9 (Git + CI).

No necesita ROS2 (solo para la parte opcional del ejercicio 2). Requisitos: Python 3.9+, Git y

```bash
pip install -r requirements.txt          # rosbags, matplotlib, pyyaml
python3 -m unittest test_analiza_bag     # pruebas de la herramienta de la S8: deben pasar
python3 -m unittest test_mis_comprobaciones   # al principio FALLAN: son tu ejercicio 3
```

## Qué hay aquí

| Fichero / carpeta | Para qué |
|---|---|
| `analiza_bag.py`, `test_analiza_bag.py`, `bags/` | herramienta de autopsia de la S8, sus pruebas y los bags (el 5 es el del ejercicio 1) |
| `simulador_bags.py` | fábrica de bags sintéticos para los ejercicios 2, 3 y 4 (léete su cabecera) |
| `mis_comprobaciones.py`, `test_mis_comprobaciones.py` | **ejercicio 3**: implementa tu comprobación y tus pruebas |
| `empaquetar_reto.py`, `reto/` | ejercicio 4: preparar el bag para tu compañero, sin pistas |
| `esperado.json`, `regresion_bags.py` | **ejercicio 7**: contrato de regresión (qué debe diagnosticar la herramienta en cada bag) |
| `.github/workflows/ci.yml` | **ejercicio 7**: workflow de GitHub Actions (push a `main` y pull requests) |
| `simula_ci.py`, `ci_local.sh` | ejecutan en local los pasos del workflow (no son un runner real de GitHub) |
| `.gitignore` | qué NO se versiona (`build/`, `install/`, `log/`, caché de Python) |
| `evidencias/` | ejercicio 7: `git_log.txt`, `ci_rojo.*`, `ci_verde.*` |
| `plantilla_informe.md` | cópiala a `informe.md` y rellénala (los huecos son `<<RELLENAR>>`) |
| `entrega.py` | autocomprobación formal y creación del `.zip` de entrega |

## Flujo de trabajo sugerido

```bash
cp plantilla_informe.md informe.md
git init -b main && git add . && git commit -m "Punto de partida de la P2"      # empieza a versionar YA

# Ejercicio 1: caso 5 (hipótesis ANTES de ejecutar)
python3 analiza_bag.py bags/caso_5_casa --esperado /distancia=10 --png informe_caso5.png

# Ejercicio 2: tus propios bags
python3 -c "import simulador_bags as s; s.generar('mi_sano', 'bags'); s.generar('mi_float', 'bags', tipo_mensaje='Float32')"

# Ejercicio 3: la herramienta es ciega a los valores fuera de rango
python3 -c "import simulador_bags as s; s.generar('mi_rango', 'bags', fuera_de_rango=(10, 12, 9.9))"
python3 -m unittest -v test_mis_comprobaciones
python3 mis_comprobaciones.py bags/mi_rango /distancia              # ERROR RANGO_FUERA, salida 1

# Ejercicio 4: quinto fallo
python3 empaquetar_reto.py bags/mi_fallo reto/

# Ejercicio 7: la CI local (lo mismo que hará GitHub Actions) y el contrato
bash ci_local.sh                          # o: python3 simula_ci.py
python3 regresion_bags.py
git log --oneline --graph --all > evidencias/git_log.txt

# Entrega
python3 entrega.py                       # revisa que no falte nada
python3 entrega.py --zip Apellido_Nombre # crea entrega_Apellido_Nombre.zip
```

Estado inicial esperado: la CI local sale en **ROJO** hasta que implementes el ejercicio 3 (las pruebas de
`test_mis_comprobaciones.py` fallan a propósito). Es normal: ponerla en verde forma parte del trabajo.

## Qué garantiza y qué no

- `simula_ci.py` / `ci_local.sh` garantizan que los pasos `run:` funcionan **en tu ordenador**. No garantizan que
  GitHub Actions los ejecute igual (versiones de las acciones, permisos, red): eso solo se ve subiendo el repositorio.
  Las versiones de las acciones (`@v7`) hay que comprobarlas en su README: cambian.
- `entrega.py` comprueba ficheros, secciones, pruebas y CI local. **No** comprueba que tu repositorio exista ni que
  su CI esté en verde: eso se evalúa con las URL de tu informe.
- Los bags son **sintéticos**: modelan el comportamiento descrito pero no son capturas de un robot real.

## Seguridad

No subas tokens, contraseñas ni claves (ni en el código, ni en capturas). No publiques bags grandes ni datos personales.
Si usas un repositorio privado, dale acceso al profesor con el usuario que se indique en el campus.
