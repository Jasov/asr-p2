"""Pruebas del ejercicio 3. Al principio FALLAN (NotImplementedError): tu trabajo es hacer que pasen.
Despues, anade tus propias pruebas en la clase PruebasPropias (minimo dos)."""
import tempfile
import unittest

import mis_comprobaciones as mc
import simulador_bags as sim


def m(t, rango, mn=0.02, mx=4.0, frame='sensor_link'):
    return {'t': t, 'range': rango, 'min_range': mn, 'max_range': mx, 'frame_id': frame}


class PruebasRangos(unittest.TestCase):
    def test_todo_en_rango(self):
        self.assertEqual(mc.comprobar_rangos([m(0, 1.0), m(0.1, 3.9), m(0.2, 0.02)], '/d'), [])

    def test_sin_muestras(self):
        self.assertEqual(mc.comprobar_rangos([], '/d'), [])

    def test_por_encima_del_maximo(self):
        h = mc.comprobar_rangos([m(0, 1.0), m(1, 9.9), m(2, 9.9), m(3, 1.0)], '/d')
        self.assertEqual(len(h), 1)
        self.assertEqual((h[0].severidad, h[0].codigo, h[0].topic), ('ERROR', 'RANGO_FUERA', '/d'))
        self.assertIn('2', h[0].detalle)          # 2 muestras fallan

    def test_por_debajo_del_minimo(self):
        h = mc.comprobar_rangos([m(0, 0.001), m(1, 1.0)], '/d')
        self.assertEqual([x.codigo for x in h], ['RANGO_FUERA'])

    def test_margen_de_tolerancia(self):
        muestras = [m(0, 4.05)]
        self.assertEqual(len(mc.comprobar_rangos(muestras, '/d')), 1)
        self.assertEqual(mc.comprobar_rangos(muestras, '/d', margen=0.1), [])

    def test_con_bag_real_sano(self):
        with tempfile.TemporaryDirectory() as d:
            sim.generar('sano', d, duracion=5)
            self.assertEqual(mc.main([f'{d}/sano', '/distancia']), 0)

    def test_con_bag_real_fuera_de_rango(self):
        with tempfile.TemporaryDirectory() as d:
            sim.generar('malo', d, duracion=5, fuera_de_rango=(1, 2, 9.9))
            self.assertEqual(mc.main([f'{d}/malo', '/distancia']), 1)


class PruebasFrames(unittest.TestCase):
    """Ampliacion: se omiten mientras comprobar_frames no este implementada."""
    def setUp(self):
        try:
            mc.comprobar_frames([], '/d')
        except NotImplementedError:
            self.skipTest('comprobar_frames sin implementar (ampliacion)')

    def test_un_solo_frame(self):
        self.assertEqual(mc.comprobar_frames([m(0, 1, frame='a'), m(1, 1, frame='a')], '/d'), [])

    def test_dos_frames(self):
        h = mc.comprobar_frames([m(0, 1, frame='a'), m(1, 1, frame='b')], '/d')
        self.assertEqual(len(h), 1)
        self.assertEqual((h[0].severidad, h[0].codigo), ('WARN', 'FRAME_MIXTO'))
        self.assertIn('a', h[0].detalle)
        self.assertIn('b', h[0].detalle)


class PruebasPropias(unittest.TestCase):
    """TU TRABAJO: anade aqui al menos dos pruebas nuevas (casos limite, otro topic, tu propio fallo...)."""

    def test_valor_exactamente_en_el_limite(self):
        # 4.0 m con max_range = 4.0 y 0.02 m con min_range = 0.02: el limite cuenta como valido
        self.assertEqual(mc.comprobar_rangos([m(0, 4.0), m(1, 0.02)], '/d'), [])

    def test_malas_no_seguidas_un_solo_hallazgo(self):
        # Tres muestras malas separadas (t=1, t=3 y t=5): un unico hallazgo con el total y el intervalo
        muestras = [m(0, 1.0), m(1, 9.9), m(2, 1.0), m(3, 0.001), m(4, 1.0), m(5, 7.0)]
        h = mc.comprobar_rangos(muestras, '/d')
        self.assertEqual(len(h), 1)
        self.assertIn('3 de 6', h[0].detalle)
        self.assertIn('t=1.0 s', h[0].detalle)
        self.assertIn('t=5.0 s', h[0].detalle)

    def test_nan_cuenta_como_fuera_de_rango(self):
        # Un NaN no es una distancia valida: debe salir como RANGO_FUERA
        h = mc.comprobar_rangos([m(0, 1.0), m(1, float('nan'))], '/d')
        self.assertEqual([x.codigo for x in h], ['RANGO_FUERA'])

    def test_frames_con_topic_vacio(self):
        # Sin muestras no hay frames que comparar: lista vacia, sin excepcion
        self.assertEqual(mc.comprobar_frames([], '/d'), [])

    def test_mi_fallo_no_es_un_fallo_de_rango(self):
        # Mi bag del ejercicio 4 (el filtro se cae 10 s) tiene huecos, pero sus valores son validos:
        # esta comprobacion no debe confundir un fallo de ritmo con uno de rango
        # Copia de mi_fallo (mis_bags.py) para que la prueba no dependa de otro fichero
        def mi_fallo(msgs):
            resultado = []
            for topic, tipo, instante, mensaje in msgs:
                segundo = instante - sim.T0
                filtro_caido = 15.0 <= segundo < 25.0
                if filtro_caido and topic in ('/distancia_filtrada', '/cmd_vel_demo'):
                    continue
                resultado.append((topic, tipo, instante, mensaje))
            return resultado

        with tempfile.TemporaryDirectory() as d:
            sim.generar('caida', d, duracion=30, post=mi_fallo)
            self.assertEqual(mc.main([f'{d}/caida', '/distancia_filtrada']), 0)


if __name__ == '__main__':
    unittest.main()
