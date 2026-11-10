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


if __name__ == '__main__':
    generar_ejercicio_2()
