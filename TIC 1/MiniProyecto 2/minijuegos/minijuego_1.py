import sys
import os
import random
from PyQt6 import QtWidgets
from PyQt6.QtCore import QTimer
import PyQt6.uic as uic

# Detección defensiva de librerías de hardware para el encoder
HAS_ENCODER = False
try:
    from gpiozero import RotaryEncoder
    HAS_ENCODER = True
except Exception:
    print("[AVISO] gpiozero no disponible. Se ejecutará sin hardware encoder.")

class Minijuego1(QtWidgets.QMainWindow):
    def __init__(self, callback_finalizar=None):
        super().__init__()
        self.game_id = 1
        self.callback_finalizar = callback_finalizar

        dir_actual = os.path.dirname(os.path.abspath(__file__))
        uic.loadUi(os.path.join(dir_actual, "minijuego1.ui"), self)

        if hasattr(self, 'tripulante'):
            self.nave = self.tripulante
        elif hasattr(self, 'nave'):
            self.nave = getattr(self, 'nave')
        else:
            for lbl in self.findChildren(QtWidgets.QLabel):
                nombre = lbl.objectName().lower()
                if not any(k in nombre for k in ['fondo', 'hud', 'asteroide']):
                    self.nave = lbl
                    break

        self.asteroides = [
            getattr(self, f"asteroide_{i}", None) for i in range(1, 5)
        ]
        self.asteroides = [a for a in self.asteroides if a is not None]

        if not self.asteroides:
            for lbl in self.findChildren(QtWidgets.QLabel):
                if 'asteroide' in lbl.objectName().lower():
                    self.asteroides.append(lbl)

        self.velocidades = [random.randint(7, 13) for _ in self.asteroides]

        self.time_left = 15
        self.score = 40

        self.encoder = None
        if HAS_ENCODER:
            try:
                self.encoder = RotaryEncoder(5, 6, max_steps=0)
            except Exception as e:
                print(f"[ERROR ENCODER] {e}")

        self.timer_juego = QTimer(self)
        self.timer_juego.timeout.connect(self.actualizar_juego)
        self.timer_juego.start(30)

        self.timer_reloj = QTimer(self)
        self.timer_reloj.timeout.connect(self.actualizar_tiempo)
        self.timer_reloj.start(1000)

    def actualizar_juego(self):
        if not self.nave:
            return

        if self.encoder:
            pos_x = (self.width() / 2) + (self.encoder.steps * 14)
            pos_x = max(10, min(pos_x, self.width() - self.nave.width() - 10))
            self.nave.move(int(pos_x), self.nave.y())

        rect_nave = self.nave.geometry().adjusted(10, 10, -10, -10)

        for i, ast in enumerate(self.asteroides):
            y_nueva = ast.y() + self.velocidades[i]

            if y_nueva > self.height():
                ast.move(random.randint(10, self.width() - ast.width() - 10), random.randint(-150, -60))
                self.velocidades[i] = random.randint(7, 14)
                self.score = min(100, self.score + 5)
                self.actualizar_hud()

                if self.score >= 100:
                    self.finalizar_juego("Win", 100)
                    return
            else:
                ast.move(ast.x(), int(y_nueva))

            if rect_nave.intersects(ast.geometry()):
                self.score -= 20
                self.actualizar_hud()
                ast.move(random.randint(10, self.width() - ast.width() - 10), random.randint(-200, -60))

                if self.score <= 0:
                    self.finalizar_juego("Lose", 0)
                    return

    def actualizar_hud(self):
        if hasattr(self, 'hud_info'):
            self.hud_info.setText(f"TIEMPO: {self.time_left}s  |  PTS: {max(0, self.score)}")

    def actualizar_tiempo(self):
        self.time_left -= 1
        self.actualizar_hud()

        if self.time_left <= 0:
            score_final = max(1, min(99, self.score))
            self.finalizar_juego("TimeOut", score_final)

    def finalizar_juego(self, result, score):
        self.timer_juego.stop()
        self.timer_reloj.stop()

        if self.encoder:
            self.encoder.close()

        self.close()

        if self.callback_finalizar:
            self.callback_finalizar(self.game_id, result, score)