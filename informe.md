# Práctica P2 (Tema 2) — Informe

**Nombre:** Joel Cárdenas
**Fecha:** 10.11.2026
**Entorno usado:** local (Linux), Python 3.13, Git 2.43. Sin ROS2 (no he hecho las partes opcionales con ROS2).

> Regla de oro: **hipótesis escrita ANTES de medir**. Cada afirmación lleva su evidencia (comando + salida o gráfica).

---

## Declaración de autoría y uso de IA

Trabajo individual. Fuentes consultadas: <<RELLENAR>>
Uso de asistentes de IA (para qué, o «ninguno»): <<RELLENAR>>

## Ejercicio 1 — Caso 5 (`bags/caso_5_casa`)

**Paso 1 — solo `--info` (antes de analizar):**

```
$ python3 analiza_bag.py bags/caso_5_casa --info
Duration:          39.010s
Messages:          120
Topic information: Topic: /cmd_vel_demo | Type: geometry_msgs/msg/Twist | Count: 40
                   Topic: /distancia | Type: sensor_msgs/msg/Range | Count: 40
                   Topic: /distancia_filtrada | Type: sensor_msgs/msg/Range | Count: 40
```

Para comparar, el bag sano (`bags/caso_0_linea_base --info`) dura 39,9 s y tiene 400 mensajes por topic.

| Campo | Contenido |
|---|---|
| Síntoma (lo que se observa) | El bag dura lo mismo que el sano (39 s) pero tiene 10 veces menos mensajes: 40 por topic en vez de 400. El robot recibe la distancia muy pocas veces por segundo, así que reacciona tarde. |
| Hipótesis (escrita antes de ejecutar nada) | 40 mensajes en 39 s es más o menos 1 Hz. Como los **tres** topics tienen el mismo número de mensajes, el filtro y el controlador no pierden nada: publican todo lo que reciben. Por tanto creo que el fallo está en el origen: el sensor publica a 1 Hz en vez de a 10 Hz. Espero ver `RITMO_BAJO` en `/distancia`. **No** espero `CAIDA_EN_CADENA` (los tres van igual), ni `HUECOS` (los mensajes cubren los 39 s), ni `LATENCIA_ALTA` (si no hay cola llena, los datos llegan frescos), ni `SIN_DATOS` (los tres topics existen con su nombre y su tipo). |
| Comando(s) | `python3 analiza_bag.py bags/caso_5_casa --esperado /distancia=10 --png informe_caso5.png` |
| Evidencia (salida / gráfica) | Ver la salida debajo de la tabla y `informe_caso5.png`. Los tres topics van a 1,00 Hz, el periodo máximo es 1,00 s (ritmo regular, sin huecos) y la latencia es de 2 ms y 7 ms (normal). Único hallazgo: `RITMO_BAJO /distancia 1.00 Hz medidos frente a 10 Hz esperados`. La hipótesis se confirma. |
| Eslabón donde se rompe | El primero de la cadena: el nodo sensor que publica `/distancia`. El filtro y el controlador funcionan bien (mantienen el ritmo que les llega). |
| Familia (estructural / dinámico / tiempo / origen) | Dinámico (es un problema de ritmo) con origen aguas arriba: lo que se ve en `/distancia_filtrada` y `/cmd_vel_demo` es solo consecuencia de lo que pasa en el sensor. No es estructural (todo está conectado) ni de tiempo (latencia y reloj correctos). |
| Causa raíz probable | El sensor está configurado a 1 Hz: el periodo de su temporizador (o su parámetro de frecuencia) vale 1,0 s en lugar de 0,1 s. El ritmo es exactamente 1,00 Hz y muy regular, lo que apunta a una configuración y no a un sensor saturado o un cable malo (eso daría un ritmo irregular o huecos). |
| Arreglo concreto y cómo comprobarlo | En el nodo sensor, poner el periodo del temporizador a 0,1 s (`create_timer(0.1, ...)`) o corregir el parámetro de frecuencia en el launch/YAML si se pasa por parámetro. Comprobación: `ros2 topic hz /distancia` debe dar ≈ 10 Hz; después grabar un bag nuevo y ejecutar `python3 analiza_bag.py <bag> --esperado /distancia=10`, que debe dar `TODO_OK` y salida 0. |

```
$ python3 analiza_bag.py bags/caso_5_casa --esperado /distancia=10 --png informe_caso5.png
== Informe de caso_5_casa ==

topic                    tipo                           n      Hz  max dt  lat med
/cmd_vel_demo            Twist                         40    1.00    1.00        -
/distancia               Range                         40    1.00    1.00    0.002
/distancia_filtrada      Range                         40    1.00    1.00    0.007

Hallazgos:
  [ERROR] RITMO_BAJO        /distancia             1.00 Hz medidos frente a 10 Hz esperados

Graficas guardadas en informe_caso5.png
(código de salida: 1)
```

Nota sobre la gráfica: en el panel «Ritmo por topic», `/distancia` salta entre 0 y 2 mensajes por segundo. No es un fallo real: como publica justo una vez por segundo, un pequeño adelanto o retraso hace que un mensaje caiga en el segundo anterior o en el siguiente al contarlos. La media sigue siendo 1 Hz (columna `Hz` y `max dt` = 1,00 s).

**¿Qué dice el grafo del sistema y qué dice el bag?** El grafo (`rqt_graph`, `ros2 node list`, `ros2 topic info`) solo dice **quién está conectado con quién**: aquí saldría perfecto, con los tres nodos y los tres topics bien unidos. No dice nada de **cuántos** mensajes pasan ni cuándo. El bag sí: guarda cada mensaje con su instante, y por eso se ve que el ritmo es 1 Hz. Igual que en el caso D de la S7, el fallo no es de estructura sino de configuración en el origen, y un grafo correcto no garantiza que el sistema funcione: hay que medir (`ros2 topic hz` en vivo, o el bag después).

**Pregunta de control.** Sin `--esperado`, la herramienta supone 10 Hz para el primer topic de la cadena. Con un sensor diseñado a 1 Hz daría `RITMO_BAJO` aunque el sensor estuviera bien: un falso positivo. Lo he comprobado con este mismo bag diciéndole que lo esperado es 1 Hz:

```
$ python3 analiza_bag.py bags/caso_5_casa --esperado /distancia=1
Hallazgos:
  [INFO ] TODO_OK           -                      ritmos, huecos, latencias y reloj dentro de lo esperado
(código de salida: 0)
```

Es decir, el mismo bag es «sano» o «roto» según el requisito. Por eso el requisito «este sensor publica a N Hz» no debe estar escondido como valor por defecto dentro de la herramienta: debe estar escrito en un sitio versionado junto al sistema, como el contrato `esperado.json` (campo `esperado_hz`) o la configuración del propio robot, y pasarse a la herramienta de forma explícita.

## Ejercicio 2 — Mis propios bags

Bags entregados (en `bags/`, nombres que empiezan por `mi_`): <<RELLENAR>>
Cómo los generé (comandos): <<RELLENAR>>

Tabla comparativa sano / con fallo (ritmos, latencia, hallazgos): <<RELLENAR>>

**¿Qué no puede medir la herramienta con mensajes sin cabecera (`Float32`)? ¿Por qué?** <<RELLENAR>>

## Ejercicio 3 — Extensión de la herramienta

Comprobación(es) implementada(s): <<RELLENAR>>
Decisiones de diseño (¿ERROR o WARN? ¿margen?, ¿qué falsos positivos hay?): <<RELLENAR>>
Pruebas propias añadidas (nombre y qué comprueban): <<RELLENAR>>
Salida de `python3 -m unittest -v test_mis_comprobaciones`: <<RELLENAR>>
Resultado sobre `bags/mi_rango` (antes: TODO_OK; ahora: ...): <<RELLENAR>>

## Ejercicio 4 — Un quinto fallo

Ficha del fallo (SIN la solución; es lo que recibirá tu compañero):
- Nombre del bag: <<RELLENAR>>
- Síntoma observable: <<RELLENAR>>
- Qué debe averiguar quien lo resuelva: <<RELLENAR>>

**Solución (aparte, en sobre cerrado hasta que el compañero entregue):**
- Cómo se genera (parámetros o función `post`): <<RELLENAR>>
- Hallazgo(s) de `analiza_bag.py` que lo detectan, o por qué la herramienta no lo detecta: <<RELLENAR>>
- Eslabón, familia, causa y arreglo: <<RELLENAR>>

Resultado de la resolución del compañero (¿acertó? ¿qué le faltó? Si no hubo intercambio, «sin intercambio» y por qué): <<RELLENAR>>

## Ejercicio 5 — Lista de comprobación ampliada

Las 7 preguntas de la clase + 3 mías (cada una con su herramienta, qué detecta y un caso que la justifique):

| # | Pregunta | Herramienta | Detecta | Caso que la justifica |
|---|---|---|---|---|
| 8 | <<RELLENAR>> | | | |
| 9 | <<RELLENAR>> | | | |
| 10 | <<RELLENAR>> | | | |

## Ejercicio 6 — Autoformación guiada

Puntos de control de la *Guía de autoformación de la S8* (resumen de lo aprendido y dudas): <<RELLENAR>>

## Ejercicio 7 — Repositorio Git con integración continua

| Campo | Contenido |
|---|---|
| URL del repositorio (público, o privado con acceso para el profesor) | <<RELLENAR>> |
| Nº de commits y rama(s) de trabajo | <<RELLENAR>> |
| Pull Request (o merge) que integra una rama en `main` (URL) | <<RELLENAR>> |
| Ejecución de CI en **verde** (URL de la ejecución en Actions) | <<RELLENAR>> |
| Ejecución de CI en **rojo** provocada a propósito (URL) y commit que la arregla | <<RELLENAR>> |
| Qué rompí a propósito y cómo lo diagnostiqué en el log | <<RELLENAR>> |
| Bag(s) que añadí a `esperado.json` y por qué | <<RELLENAR>> |

Si **no** has podido usar GitHub, escribe aquí por qué y adjunta en `evidencias/` el `git_log.txt`, la salida de `simula_ci.py` y las capturas `ci_rojo` / `ci_verde` de la simulación local: la nota máxima del ejercicio baja (ver enunciado).

## Memoria conceptual (con tus palabras; máximo 1 página en total)

**M1.** Familias de fallo de arquitectura (estructural, dinámico, de tiempo, de origen aguas arriba): un ejemplo de cada una y la herramienta más barata que la detectaría. <<RELLENAR>>

**M2.** ¿Por qué una herramienta de análisis necesita pruebas unitarias, y qué significa que «un fallo no detectado es una especificación pendiente»? <<RELLENAR>>

**M3.** ¿Qué ocurre exactamente en un conflicto de fusión en Git, cómo se ve en el fichero y cómo se resuelve? ¿Por qué no se debe «aceptar el mío» sin leer? <<RELLENAR>>

**M4.** ¿Qué garantiza y qué NO garantiza una CI en verde? Usa como ejemplo el contrato de regresión con bags. <<RELLENAR>>

## Opcional — `ros2 bag play` y RViz2

<<RELLENAR o "No realizado">>

## Reflexión final (5 líneas)

¿Qué fue lo más difícil? ¿Qué cambiarías en la herramienta? ¿Qué le faltó al bag para estar seguro de la causa? <<RELLENAR>>
