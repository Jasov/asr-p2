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

Bags entregados (en `bags/`, nombres que empiezan por `mi_`): `mi_sano`, `mi_lento` y `mi_lento_float` (más `mi_rango` y `mi_fallo`, que son de los ejercicios 3 y 4).

Cómo los generé (comandos): con `simulador_bags.py`, sin ROS2. Están todos en el fichero `mis_bags.py` para poder regenerarlos con un solo comando:

```
$ python3 mis_bags.py
mi_sano: 1200 mensajes -> bags/mi_sano
mi_lento: 718 mensajes -> bags/mi_lento
mi_lento_float: 718 mensajes -> bags/mi_lento_float
```

Las llamadas que hace son:

```python
sim.generar('mi_sano', 'bags')                                                    # sano
sim.generar('mi_lento', 'bags', retardo_filtro=0.25)                              # callback lento en el filtro
sim.generar('mi_lento_float', 'bags', retardo_filtro=0.25, tipo_mensaje='Float32') # mismo fallo, sin cabecera
```

El fallo elegido es un **callback lento en el filtro**: tarda 0,25 s en procesar cada mensaje.

**Hipótesis (antes de analizar):**
- `mi_sano`: 10 Hz en los tres topics y `TODO_OK`.
- `mi_lento`: si el filtro tarda 0,25 s por mensaje, como mucho puede sacar 1/0,25 = 4 mensajes por segundo. El sensor sigue a 10 Hz, así que espero `/distancia` a 10 Hz y `/distancia_filtrada` y `/cmd_vel_demo` a unos 4 Hz (`CAIDA_EN_CADENA`). Además, como entran más mensajes de los que salen, la cola del filtro se llena y los datos esperan dentro: espero `LATENCIA_ALTA`.
- `mi_lento_float`: los mismos ritmos (el fallo es el mismo), pero como `Float32` no lleva sello de tiempo, creo que la herramienta no podrá calcular la latencia y solo dará `CAIDA_EN_CADENA`.

**Comando de análisis** (el mismo para los tres): `python3 analiza_bag.py bags/<nombre> --esperado /distancia=10`

Tabla comparativa sano / con fallo (ritmos, latencia, hallazgos):

| | `mi_sano` | `mi_lento` (Range) | `mi_lento_float` (Float32) |
|---|---|---|---|
| Mensajes totales | 1200 | 718 | 718 |
| `/distancia` | 10,00 Hz | 10,00 Hz | 10,00 Hz |
| `/distancia_filtrada` | 10,00 Hz | 4,00 Hz | 4,00 Hz |
| `/cmd_vel_demo` | 10,00 Hz | 4,00 Hz | 4,00 Hz |
| Latencia mediana `/distancia` | 0,002 s | 0,002 s | no se puede medir (`-`) |
| Latencia mediana `/distancia_filtrada` | 0,007 s | 1,204 s | no se puede medir (`-`) |
| Hallazgos | `TODO_OK` | `CAIDA_EN_CADENA` + `LATENCIA_ALTA` | solo `CAIDA_EN_CADENA` |
| Código de salida | 0 | 1 | 1 |

Las tres hipótesis se cumplen. Salidas de la herramienta:

```
== Informe de mi_sano ==
topic                    tipo                           n      Hz  max dt  lat med
/cmd_vel_demo            Twist                        400   10.00    0.10        -
/distancia               Range                        400   10.00    0.10    0.002
/distancia_filtrada      Range                        400   10.00    0.10    0.007
Hallazgos:
  [INFO ] TODO_OK           -                      ritmos, huecos, latencias y reloj dentro de lo esperado

== Informe de mi_lento ==
topic                    tipo                           n      Hz  max dt  lat med
/cmd_vel_demo            Twist                        159    4.00    0.25        -
/distancia               Range                        400   10.00    0.10    0.002
/distancia_filtrada      Range                        159    4.00    0.25    1.204
Hallazgos:
  [ERROR] CAIDA_EN_CADENA   /distancia_filtrada    /distancia 10.0 Hz -> /distancia_filtrada 4.0 Hz: el ritmo cae en el nodo que une ambos topics
  [ERROR] LATENCIA_ALTA     /distancia_filtrada    latencia mediana 1.20 s (maxima 1.25 s) > 0.1 s: los datos llegan viejos (cola llena o callback lento aguas arriba)

== Informe de mi_lento_float ==
topic                    tipo                           n      Hz  max dt  lat med
/cmd_vel_demo            Twist                        159    4.00    0.25        -
/distancia               Float32                      400   10.00    0.10        -
/distancia_filtrada      Float32                      159    4.00    0.25        -
Hallazgos:
  [ERROR] CAIDA_EN_CADENA   /distancia_filtrada    /distancia 10.0 Hz -> /distancia_filtrada 4.0 Hz: el ritmo cae en el nodo que une ambos topics
```

Gráfica de apoyo: `informe_mi_lento.png` (generada con `--png informe_mi_lento.png`): en el panel de latencia se ve `/distancia_filtrada` en torno a 1,2 s frente a los milisegundos de `/distancia`.

Diagnóstico de `mi_lento`: eslabón = nodo filtro (entre `/distancia` y `/distancia_filtrada`); familia = dinámico; causa = callback que tarda más (0,25 s) que el periodo de llegada (0,1 s); arreglo = sacar el trabajo pesado del callback o hacerlo más rápido, y si interesa el dato más reciente, usar una cola de profundidad 1 para no acumular datos viejos.

**¿Qué no puede medir la herramienta con mensajes sin cabecera (`Float32`)? ¿Por qué?** No puede medir la **latencia** ni comprobar el **reloj**. La latencia se calcula como «instante en que se grabó el mensaje» menos «sello de tiempo que puso el nodo al crearlo» (`header.stamp`). Un `Float32` solo lleva un número (`data`): no tiene `header`, así que falta la segunda mitad de la resta. El bag solo sabe cuándo llegó el mensaje, no cuándo se midió el dato.

**¿Qué hallazgo se pierde frente al mismo fallo con `Range`?** Se pierde `LATENCIA_ALTA` (y también se perdería `RELOJ_DESFASADO` si el fallo fuera de reloj). Con `Float32` sabemos que el filtro saca menos mensajes, pero no que cada dato sale con 1,2 s de retraso, que es lo peligroso para un robot que se mueve.

**¿Qué haría en el sistema real para medir latencia sin cabecera?** Lo más sencillo es cambiar el tipo de mensaje por uno que lleve `header` (por ejemplo `Range`, o un tipo «Stamped») y rellenar el sello con la hora de la medida. Si no se puede cambiar el tipo, medir de extremo a extremo con una prueba: provocar un cambio brusco en la entrada (tapar el sensor) y medir en el bag cuánto tarda en aparecer el cambio en la salida.

## Ejercicio 3 — Extensión de la herramienta

Comprobación(es) implementada(s): <<RELLENAR>>
Decisiones de diseño (¿ERROR o WARN? ¿margen?, ¿qué falsos positivos hay?): <<RELLENAR>>
Pruebas propias añadidas (nombre y qué comprueban): <<RELLENAR>>
Salida de `python3 -m unittest -v test_mis_comprobaciones`: <<RELLENAR>>
Resultado sobre `bags/mi_rango` (antes: TODO_OK; ahora: ...): <<RELLENAR>>

## Ejercicio 4 — Un quinto fallo

Ficha del fallo (SIN la solución; es lo que recibirá tu compañero). Está en `reto/reto_1_ficha.md`:
- Nombre del bag: `reto/reto_1` (copia sin pistas de `bags/mi_fallo`, hecha con `python3 empaquetar_reto.py bags/mi_fallo reto/`).
- Síntoma observable: en mitad de la prueba el robot deja de recibir órdenes de velocidad durante varios segundos y después sigue funcionando como si no hubiera pasado nada. Nadie tocó el robot ni el sensor.
- Qué debe averiguar quien lo resuelva: en qué eslabón empieza el problema y cuándo, la familia del fallo, la causa raíz más probable (y cuáles descarta) y un arreglo concreto y comprobable.

**Solución (aparte, en sobre cerrado hasta que el compañero entregue):**

- Cómo se genera (parámetros o función `post`): el fallo es **un nodo que se cae y vuelve a arrancar**. El nodo filtro está caído entre el segundo 15 y el 25. La función `mi_fallo(msgs)` de `mis_bags.py` recorre todos los mensajes y **no guarda** los de `/distancia_filtrada` ni los de `/cmd_vel_demo` cuyo instante cae en ese intervalo (el controlador solo publica cuando recibe un dato filtrado, así que también calla). El sensor no se toca.

  ```python
  def mi_fallo(msgs):
      resultado = []
      for topic, tipo, instante, mensaje in msgs:
          segundo = instante - sim.T0          # segundos desde el inicio del bag
          filtro_caido = 15.0 <= segundo < 25.0
          if filtro_caido and topic in ('/distancia_filtrada', '/cmd_vel_demo'):
              continue                         # este mensaje nunca se publico: no se guarda
          resultado.append((topic, tipo, instante, mensaje))
      return resultado

  sim.generar('mi_fallo', 'bags', post=mi_fallo)      # o: python3 mis_bags.py
  ```

- Hipótesis antes de analizar: `/distancia` normal (400 mensajes, 10 Hz); un hueco de unos 10 s en `/distancia_filtrada` y en `/cmd_vel_demo` (300 mensajes cada uno); la herramienta debería dar `HUECOS` en esos dos topics y ninguno en `/distancia`.

- Hallazgo(s) de `analiza_bag.py` que lo detectan, o por qué la herramienta no lo detecta:

  ```
  $ python3 analiza_bag.py bags/mi_fallo --esperado /distancia=10 --png informe_mi_fallo.png
  topic                    tipo                           n      Hz  max dt  lat med
  /cmd_vel_demo            Twist                        300    7.49   10.10        -
  /distancia               Range                        400   10.00    0.10    0.002
  /distancia_filtrada      Range                        300    7.49   10.10    0.007

  Hallazgos:
    [ERROR] CAIDA_EN_CADENA   /distancia_filtrada    /distancia 10.0 Hz -> /distancia_filtrada 7.5 Hz: el ritmo cae en el nodo que une ambos topics
    [ERROR] HUECOS            /cmd_vel_demo          sin mensajes entre 14.9 s y 25.0 s (10.1 s)
    [ERROR] HUECOS            /distancia_filtrada    sin mensajes entre 14.9 s y 25.0 s (10.1 s)
    [INFO ] HUECO_ORIGEN      /distancia_filtrada    el hueco empieza primero en /distancia_filtrada (14.9 s): mirad aguas arriba (sensor, driver, cable), el resto es consecuencia
  (código de salida: 1)
  ```

  **Qué ve la herramienta:** el hueco de 10,1 s en los dos topics (`HUECOS`), y que el primer topic afectado es `/distancia_filtrada` (`HUECO_ORIGEN`). Eso localiza bien el eslabón.

  **Qué no ve o dice mal:**
  1. El texto de `HUECO_ORIGEN` aconseja «mirad aguas arriba (sensor, driver, cable)». Aquí ese consejo es engañoso: lo que hay aguas arriba (`/distancia`) está perfecto, 10 Hz y sin huecos. El problema es el nodo que **publica** el topic donde empieza el hueco, o sea el filtro. El mensaje está pensado para un hueco que nace en el sensor (caso 3) y no distingue este caso.
  2. `CAIDA_EN_CADENA` (10 → 7,5 Hz) es verdad en media, pero confunde: hace pensar en un filtro lento como en el caso 1. No es eso: fuera del hueco el filtro va a 10 Hz y la latencia es de 7 ms. El 7,5 sale de dividir 300 mensajes entre 40 s.
  3. La herramienta no puede saber **por qué** calló el nodo: una caída y reinicio, un callback bloqueado 10 s o una red cortada dejan el mismo hueco en el bag. Para distinguirlo harían falta los logs (`/rosout`), que este bag no tiene.

- Eslabón, familia, causa y arreglo:
  - **Eslabón:** el nodo filtro (entre `/distancia` y `/distancia_filtrada`). El hueco de `/cmd_vel_demo` es consecuencia.
  - **Familia:** dinámico (huecos). No es de origen aguas arriba, porque el sensor nunca deja de publicar; ni de tiempo, porque la latencia es normal antes y después.
  - **Causa:** el proceso del filtro se cae (por ejemplo, una excepción sin capturar) y alguien o algo lo vuelve a lanzar 10 s después. Descarto filtro lento (latencia de 7 ms y 10 Hz fuera del hueco) y fallo del sensor (`/distancia` sin huecos).
  - **Arreglo:** (1) mirar el log del filtro para encontrar la excepción y corregirla; (2) poner `respawn=True` (con `respawn_delay` corto) en el `Node` del filtro en el fichero launch, para que se relance solo en vez de tardar 10 s; (3) añadir en el controlador un temporizador de seguridad que pare el robot si lleva más de, por ejemplo, 0,5 s sin recibir `/distancia_filtrada`.
  - **Comprobación:** matar el filtro a mano durante una prueba (`kill` del proceso), grabar un bag y analizarlo: el hueco debe durar lo que tarde el `respawn` (menos de 1 s para que no salga como ERROR) y `/cmd_vel_demo` debe mostrar la orden de parada.

Resultado de la resolución del compañero (¿acertó? ¿qué le faltó? Si no hubo intercambio, «sin intercambio» y por qué): **sin intercambio**. No encontré pareja para intercambiar el reto dentro del plazo. El reto queda preparado en `reto/` (bag + ficha sin solución) por si se quiere asignar a un compañero. Una nota honesta sobre las pistas: `empaquetar_reto.py` cambia el nombre de la carpeta, del `.mcap` y de `metadata.yaml`, pero dentro del `.mcap` queda una copia de los metadatos con el nombre original (`strings reto/reto_1/reto_1.mcap | grep mi_`). Por eso llamé al bag `mi_fallo`, que no dice de qué fallo se trata.

## Ejercicio 5 — Lista de comprobación ampliada

Las 7 preguntas de la clase + 3 mías (cada una con su herramienta, qué detecta y un caso que la justifique). Las ordeno igual que en clase, de barata a cara:

| # | Pregunta | Herramienta | Detecta | Caso que la justifica |
|---|---|---|---|---|
| 8 | ¿Los valores que se publican son físicamente posibles (dentro de `min_range`/`max_range`, sin `NaN`)? | En vivo: `ros2 topic echo /distancia --field range`. Con bag: `python3 mis_comprobaciones.py <bag> /distancia` (`RANGO_FUERA`). | Un sensor o driver que publica a buen ritmo y a tiempo, pero con datos imposibles. Las preguntas 1-7 miran si los mensajes llegan y cuándo, no qué llevan dentro. | Mi bag `mi_rango` (ejercicio 3): el sensor publica 9,9 m con `max_range` = 4 m durante 2 s y `analiza_bag.py` dice `TODO_OK`. El filtro promedia ese valor y el controlador decide con un dato falso. |
| 9 | ¿Cada topic tiene el número de publicadores que espero (ni un nodo de más, ni uno de menos)? | `ros2 topic info -v /distancia_filtrada` (Publisher count) y `ros2 node list` (avisa si hay nombres de nodo repetidos). Con bag: buscar huecos o el doble del ritmo esperado. | Un nodo lanzado dos veces (dos terminales con el mismo launch): el topic va al doble de ritmo y los datos se mezclan. O un nodo que se ha caído: 0 publicadores aunque el topic siga existiendo porque queda el suscriptor. | Mi bag `mi_fallo` (ejercicio 4): el filtro se cae 10 s. En vivo, `ros2 topic info` habría mostrado «Publisher count: 0» al momento, mucho antes de analizar un bag. |
| 10 | ¿El `frame_id` de los mensajes es siempre el mismo y existe en el árbol de transformadas? | `ros2 topic echo /distancia --field header.frame_id`, `ros2 run tf2_tools view_frames` y `ros2 run tf2_ros tf2_echo base_link sensor_link`. Con bag: `comprobar_frames` (`FRAME_MIXTO`). | Datos correctos pero colocados en el sitio equivocado: un `frame_id` mal escrito, dos nodos que usan frames distintos en el mismo topic o un frame que nadie publica en `/tf`. | En RViz2 el display «Range» no dibuja nada y da error de transformada si `sensor_link` no está conectado con el frame fijo, aunque `ros2 topic hz` diga que todo va a 10 Hz. Lo cubre la prueba `test_dos_frames`. |

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
