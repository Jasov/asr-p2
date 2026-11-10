#!/usr/bin/env python3
"""mis_bags.py - regenera todos mis bags de la practica con un solo comando.

Uso:  python3 mis_bags.py
Los bags salen siempre iguales porque el simulador usa una semilla fija.
"""
import simulador_bags as sim


def generar_ejercicio_2():
    # Sistema sano: 10 Hz durante 40 s
    sim.generar('mi_sano', 'bags')
    # Fallo elegido: el callback del filtro tarda 0,25 s por mensaje
    sim.generar('mi_lento', 'bags', retardo_filtro=0.25)
    # El mismo fallo, pero con mensajes sin cabecera (Float32)
    sim.generar('mi_lento_float', 'bags', retardo_filtro=0.25, tipo_mensaje='Float32')


def mi_fallo(msgs):
    """Ejercicio 4: el nodo filtro se cae en el segundo 15 y vuelve a arrancar en el 25.

    Mientras esta caido no publica /distancia_filtrada. El controlador solo publica
    cuando recibe un dato filtrado, asi que /cmd_vel_demo tambien se queda callado.
    El sensor sigue publicando /distancia con normalidad.
    """
    resultado = []
    for topic, tipo, instante, mensaje in msgs:
        segundo = instante - sim.T0          # segundos desde el inicio del bag
        filtro_caido = 15.0 <= segundo < 25.0
        if filtro_caido and topic in ('/distancia_filtrada', '/cmd_vel_demo'):
            continue                         # este mensaje nunca se publico: no se guarda
        resultado.append((topic, tipo, instante, mensaje))
    return resultado


def generar_ejercicio_4():
    sim.generar('mi_fallo', 'bags', post=mi_fallo)


if __name__ == '__main__':
    generar_ejercicio_2()
    generar_ejercicio_4()
