# Ficha del reto

Bag: `reto/reto_1` (sistema de la S7: sensor -> filtro -> controlador; el sensor está diseñado para publicar a 10 Hz).

Sintoma observable: en mitad de la prueba el robot deja de recibir órdenes de velocidad durante varios segundos y después sigue funcionando como si no hubiera pasado nada. Nadie tocó el robot ni el sensor.

Que debes averiguar: (1) en qué eslabón de la cadena empieza el problema y cuándo; (2) a qué familia de fallo pertenece; (3) la causa raíz más probable y qué otras causas descartas; (4) un arreglo concreto y cómo comprobarías que funciona. Escribe tu hipótesis antes de ejecutar el análisis completo (mira primero solo `--info`).

Comando sugerido: `python3 analiza_bag.py reto/reto_1 --esperado /distancia=10 --png informe_reto.png`
