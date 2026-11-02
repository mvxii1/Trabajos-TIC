import sys
import os
import random
from PyQt6 import QtWidgets
from PyQt6.QtCore import QTimer
import PyQt6.uic as uic

# Detección defensiva de librerías de hardware para el micrófono
HAS_ADS = False
try:
    import board
    import busio
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
    HAS_ADS = True
except Exception:
    print("[AVISO] adafruit_ads1x15 no disponible. Se ejecutará sin hardware micrófono.")

class Minijuego2(QtWidgets.QMainWindow):
    def __init__(self, callback_finalizar=None):
        super().__init__()
        self.game_id = 2
        self.callback_finalizar = callback_finalizar

        dir_actual = os.path.dirname(os.path.abspath(__file__))
        uic.loadUi(os.path.join(dir_actual, "minijuego2.ui"), self)

        self.time_left = 15
        self.score = 40

        # Vincular tripulante
        if hasattr(self, 'tripulante'):
            self.personaje = self.tripulante
        elif hasattr(self, 'nave'):
            self.personaje = getattr(self, 'nave')
        else:
            for lbl in self.findChildren(QtWidgets.QLabel):
                nombre = lbl.objectName().lower()
                if not any(k in nombre for k in ['fondo', 'hud', 'pilar']):
                    self.personaje = lbl
                    break

        # Pilares desde Qt Designer
        self.pilares = [
            getattr(self, f"pilar_{i}", None) for i in range(1, 5)
        ]
        self.pilares = [p for p in self.pilares if p is not None]

        if not self.pilares:
            for lbl in self.findChildren(QtWidgets.QLabel):
                if 'pilar' in lbl.objectName().lower():
                    self.pilares.append(lbl)

        # Dimensiones de la pantalla y física
        self.alto_pantalla = 640
        self.char_w = self.personaje.width() if self.personaje else 70
        self.char_h = self.personaje.height() if self.personaje else 84
        self.pos_x_fija = 80

        # --- UMBRALES DE FILTRADO DE RUIDO AMBIENTAL ---
        self.ruido_ambiente = 2.10
        self.umbral_caminar = 2.15 
        self.umbral_gritar  = 2.40

        self.gravedad = 1.2
        self.velocidad_y = 0.0
        self.en_el_aire = False
        self.pilar_actual = None

        self.inicializar_pilares()

        # Hardware: Micrófono ADS1115 en A0
        self.microfono = None
        if HAS_ADS:
            try:
                i2c = busio.I2C(board.SCL, board.SDA)
                ads = ADS.ADS1115(i2c)
                ads.data_rate = 860
                self.microfono = AnalogIn(ads, 0)
            except Exception as ex:
                print(f"[ERROR MICRÓFONO] {ex}")

        self.timer_juego = QTimer(self)
        self.timer_juego.timeout.connect(self.actualizar_juego)
        self.timer_juego.start(30)

        self.timer_reloj = QTimer(self)
        self.timer_reloj.timeout.connect(self.actualizar_tiempo)
        self.timer_reloj.start(1000)

    def inicializar_pilares(self):
        # Acomodar capas visuales para que nada oculte los pilares
        if hasattr(self, 'fondo'):
            self.fondo.lower()

        x_pos = 0
        estilo_pilar = """
            background-color: #2563eb;
            border: 3px solid #60a5fa;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
        """

        for i, pilar in enumerate(self.pilares):
            if i == 0:
                w = 180
                top_y = 420
            else:
                w = random.randint(95, 145)
                top_y = random.randint(360, 470)

            pilar.setStyleSheet(estilo_pilar)
            pilar.setGeometry(x_pos, top_y, w, self.alto_pantalla - top_y)
            pilar.show()
            pilar.raise_()
            x_pos += w + random.randint(95, 145)

        # Garantizar que el personaje y el HUD estén al frente
        if self.personaje:
            self.personaje.raise_()
        if hasattr(self, 'hud_info'):
            self.hud_info.raise_()

        p0 = self.pilares[0]
        self.pos_y = float(p0.y() - self.char_h)
        self.pilar_actual = p0
        self.velocidad_y = 0.0
        self.en_el_aire = False
        if self.personaje:
            self.personaje.move(self.pos_x_fija, int(self.pos_y))

    def leer_amplitud_mic(self):
        if not self.microfono:
            return 0.0

        muestras = []
        for _ in range(10):
            try:
                muestras.append(self.microfono.voltage)
            except Exception:
                break

        if muestras:
            return max(muestras)
        return 0.0

    def actualizar_juego(self):
        if not self.personaje:
            return

        v_max = self.leer_amplitud_mic()
        avanzar_x = 0.0

        # 1. EVALUAR VOLTAJE RESPECTO AL RUIDO DE LA SALA
        if v_max >= self.umbral_gritar:
            # GRITO / RUÍDO FUERTE (> 2.40V)
            exceso = v_max - self.umbral_gritar
            avanzar_x = 6.0 + min(exceso * 8.0, 6.0)
            
            if not self.en_el_aire:
                # Impulso de salto escalar según la fuerza del grito
                impulso_salto = 13.0 + min(exceso * 15.0, 11.0)
                self.velocidad_y = -impulso_salto
                self.en_el_aire = True

        elif v_max >= self.umbral_caminar:
            # HABLAR INTENCIONAL (2.15V a 2.40V)
            avanzar_x = 4.5

        else:
            # RUIDO AMBIENTAL DE LA SALA (< 2.15V)
            # Se ignora completamente y el personaje se queda quieto
            avanzar_x = 0.0

        # 2. MOVER Y RECICLAR PILARES
        if avanzar_x > 0:
            for pilar in self.pilares:
                pilar.move(int(pilar.x() - avanzar_x), pilar.y())

            max_x = max(p.x() + p.width() for p in self.pilares)
            for pilar in self.pilares:
                if pilar.x() + pilar.width() < -20:
                    w = random.randint(95, 145)
                    top_y = random.randint(360, 470)
                    gap = random.randint(95, 145)
                    pilar.setGeometry(max_x + gap, top_y, w, self.alto_pantalla - top_y)
                    pilar.show()
                    max_x = pilar.x() + pilar.width()

            if self.personaje:
                self.personaje.raise_()
            if hasattr(self, 'hud_info'):
                self.hud_info.raise_()

        # 3. FÍSICA VERTICAL
        pie_x = self.pos_x_fija + (self.char_w // 2)

        if self.en_el_aire:
            self.velocidad_y += self.gravedad
            self.pos_y += self.velocidad_y
        else:
            sobre_pilar = any(p.x() <= pie_x <= p.x() + p.width() for p in self.pilares)
            if not sobre_pilar:
                self.en_el_aire = True

        # 4. ATERRIZAJE EN PILAR
        base_y_prev = self.pos_y + self.char_h - self.velocidad_y
        base_y_curr = self.pos_y + self.char_h

        if self.velocidad_y >= 0:
            for pilar in self.pilares:
                if pilar.x() <= pie_x <= pilar.x() + pilar.width():
                    if base_y_prev <= pilar.y() + 12 and base_y_curr >= pilar.y() - 12:
                        self.pos_y = float(pilar.y() - self.char_h)
                        self.velocidad_y = 0.0

                        if self.en_el_aire:
                            self.en_el_aire = False
                            if self.pilar_actual != pilar:
                                self.pilar_actual = pilar
                                self.score = min(100, self.score + 15)
                                self.actualizar_hud()

                                if self.score >= 100:
                                    self.finalizar_juego("Win", 100)
                                    return
                        break

        # 5. CAÍDA AL VACÍO
        if self.pos_y > self.alto_pantalla:
            self.penalizar_caida()
            return

        self.personaje.move(self.pos_x_fija, int(self.pos_y))

    def penalizar_caida(self):
        self.score -= 20
        self.actualizar_hud()
        self.inicializar_pilares()

        if self.score <= 0:
            self.finalizar_juego("Lose", 0)

    def actualizar_hud(self):
        if hasattr(self, 'hud_info'):
            self.hud_info.setText(f"TIEMPO: {self.time_left}s  |  PTS: {max(0, self.score)}")

    def actualizar_tiempo(self):
        """Resta 1 segundo al reloj del juego en cada tick del timer."""
        if self.time_left > 0:
            self.time_left -= 1
            self.actualizar_hud()
            
            #if self.time_left <= 0:
                # Se acabó el tiempo
                #self.finalizar_juego("Timeout", self.score)
            if self.time_left <= 0:
                # Se acabó el tiempo
                score_final = max(1, min(99, self.score))
                self.finalizar_juego("TimeOut", score_final)

    def finalizar_juego(self, result, score):
        self.timer_juego.stop()
        self.timer_reloj.stop()

        self.close()

        if self.callback_finalizar:
            self.callback_finalizar(self.game_id, result, score)