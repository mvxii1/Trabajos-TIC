"""Archivo principal del cliente para la comunicación, Lobby, control de etapas y minijuegos."""

import json
import os
import sys
import time
from PyQt6 import QtWidgets
from PyQt6.QtCore import QEventLoop, QTimer

from conexion_host import ConexionHost
from estado_juego import EstadoJuego
from protocolo import ProtocoloMensajes
from uuid import uuid4
from datetime import datetime

# Importar los minijuegos
from minijuegos import minijuego_1, minijuego_2



def main():
    print("\n--- INICIANDO CLIENTE DEL JUEGO ---")

    # 1. Cargar la configuración desde config_grupo.json
    ruta_config = os.path.join(os.path.dirname(__file__), "..", "config_grupo.json")
    try:
        with open(ruta_config, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        print(f"[ERROR] No se pudo cargar el archivo de configuración: {e}")
        return

    # 2. Inicializar los módulos de Conexión y Estado
    conexion = ConexionHost(config)
    estado = EstadoJuego(config)

    # 3. Conectar al servidor mediante SSH/SFTP
    conexion.conectar()
    if not conexion.verificar_conexion():
        print("[ERROR CRÍTICO] La conexión falló. Saliendo del programa.")
        return

    # 4. Enviar el mensaje JOIN para registrarse en el Lobby utilizando protocolo.py
    event_id = f"{estado.player_id}-{uuid4().hex[:12]}"
    mensaje_join = ProtocoloMensajes.crear_mensaje_join(estado.player_id, event_id)

    print(f"[LOBBY] Enviando solicitud de ingreso al Lobby (EventID: {event_id})...")
    conexion.enviar_json(mensaje_join)

    # 5. Bucle estricto para asegurar el ingreso al Lobby (Esperar el Accepted)
    print("[LOBBY] Esperando confirmación de ingreso (Accepted)...")
    ingreso_al_lobby_aceptado = False
    mensajes_pendientes = []

    try:
        while estado.partida_activa and not ingreso_al_lobby_aceptado:
            mensajes_nuevos = conexion.leer_nuevos_json()
            print(mensajes_nuevos)
            for mensaje in mensajes_nuevos:
                accion = mensaje.get("Action")
                reply_to = mensaje.get("ReplyTo")

                if accion == "Accepted" and reply_to == event_id:
                    print(f"[LOBBY] ¡Aceptado recibido! ReplyTo coincide ({reply_to}).")
                    ingreso_al_lobby_aceptado = True
                
                elif accion != "Accepted":
                    mensajes_pendientes.append(mensaje)
            
            if not ingreso_al_lobby_aceptado:
                time.sleep(0.3)

        # Inicializar la aplicación de PyQt6 para los minijuegos
        app_qt = QtWidgets.QApplication(sys.argv)
        app_qt.setQuitOnLastWindowClosed(False)
        bucle_minijuego = None
        intento_actual = None
        event_id_resultado_pendiente = None

        # Consultar el servidor mientras un minijuego está abierto
        def consultar_durante_minijuego():
            nuevos = conexion.leer_nuevos_json()

            if nuevos:
                mensajes_pendientes.extend(nuevos)
                print(f"[SFTP] {len(nuevos)} mensaje(s) recibido(s) durante el minijuego.")

        # Crear el temporizador
        timer_consulta = QTimer()
        timer_consulta.timeout.connect(consultar_durante_minijuego)

        # Función callback que se ejecuta al terminar el minijuego para enviar el resultado al servidor
        def al_terminar_minijuego(game_id, result, score):
            nonlocal event_id_resultado_pendiente

            print(f"[MINIJUEGO] Finalizado. GameID: {game_id} | Resultado: {result} | Puntaje: {score}")
            
            # Crear y enviar el mensaje de resultado usando protocolo.py
            ev_id_res = f"{estado.player_id}-RES-{uuid4().hex[:12]}"
            msg_resultado = ProtocoloMensajes.crear_mensaje_resultado(
                player_id=estado.player_id,
                event_id=ev_id_res,
                stage=estado.stage,
                game_id=game_id,
                attempt=intento_actual,
                result=result,
                score=score
            )
            event_id_resultado_pendiente = ev_id_res
            conexion.enviar_json(msg_resultado)

            # Finalizar la espera del minijuego
            if bucle_minijuego is not None:
                bucle_minijuego.quit()

        # 6. Bucle de control de etapas y secuencia de la Figura 5
        event_id_ready = None
        ready_aceptado = False
        stage_active_recibido = False
        ronda_activa = False
        fecha_inicio = datetime.now().date().isoformat()
        print("[LOBBY] En el Lobby. Esperando la orden de inicio de ronda (StageStart)...")
        
        while estado.partida_activa:
            mensajes_nuevos = mensajes_pendientes + conexion.leer_nuevos_json() #Cambiar el leer_nuevos_json para que lea el más antiguo, ya que se lee instantaneo
            mensajes_pendientes = []  
            print(mensajes_nuevos)
            for mensaje in mensajes_nuevos:
                accion = mensaje.get("Action")

                # Ignorar mensajes pertenecientes a días anteriores
                fecha_mensaje = mensaje.get("timestamp", "")[:10]

                if fecha_mensaje and fecha_mensaje < fecha_inicio:
                    print(f"[AVISO] Ignorando mensaje antiguo: {accion}")
                    continue

                # FASE 1: El servidor anuncia una nueva ronda
                if accion == "StageStart":
                    stage_actual = mensaje.get("Stage", "R1")

                    # Evitar repetir StageReady para la misma ronda
                    if event_id_ready is not None and stage_actual == estado.stage:
                        print(f"[ETAPA] StageStart repetido para {stage_actual}. Se ignora.")
                        continue

                    estado.actualizar_etapa(stage_actual)

                    print(f"[ETAPA] StageStart recibido: {stage_actual}")

                    # Preparar las variables para la nueva ronda
                    ready_aceptado = False
                    stage_active_recibido = False
                    ronda_activa = False

                    # Crear un EventID nuevo para StageReady
                    event_id_ready = f"{estado.player_id}-READY-{uuid4().hex[:8]}"

                    msg_ready = ProtocoloMensajes.crear_mensaje_ready(
                        estado.player_id,
                        event_id_ready,
                        stage_actual
                    )

                    conexion.enviar_json(msg_ready)
                    print("[ETAPA] StageReady enviado. Esperando confirmación...")


                # FASE 2: El servidor confirma StageReady
                elif accion == "StageReadyAccepted":

                    if mensaje.get("ReplyTo") == event_id_ready:
                        ready_aceptado = True
                        print("[ETAPA] StageReadyAccepted recibido correctamente.")

                        if stage_active_recibido:
                            ronda_activa = True
                            print("[ETAPA] Ronda activa. Ya podemos ejecutar minijuegos.")


                # FASE 3: El servidor anuncia que la ronda comenzó
                elif accion == "StageActive":

                    if mensaje.get("Stage") == estado.stage:
                        stage_active_recibido = True
                        print("[ETAPA] StageActive recibido.")

                        if ready_aceptado:
                            ronda_activa = True
                            print("[ETAPA] Ronda activa. Ya podemos ejecutar minijuegos.")


                # FASE 4: Confirmar que el servidor recibió el resultado
                elif accion == "ResultAccepted":

                    reply_to = mensaje.get("ReplyTo")

                    if event_id_resultado_pendiente is not None and reply_to == event_id_resultado_pendiente:
                        print("[RESULTADO] ResultAccepted recibido correctamente.")
                        print(f"[RESULTADO] Confirmado EventID: {reply_to}")

                        event_id_resultado_pendiente = None

                    else:
                        print(f"[AVISO] ResultAccepted no corresponde al resultado pendiente: {reply_to}")


                elif accion == "Assign":

                    game_id = mensaje.get("GameID")
                    attempt = mensaje.get("Attempt", 1)
                    intento_actual = attempt

                    # Esperar hasta que la ronda esté oficialmente activa
                    if not ronda_activa:
                        print("[JUEGO] La ronda todavía no está activa. Guardando Assign.")
                        mensajes_pendientes.append(mensaje)
                        continue

                    # Esperar la confirmación del resultado anterior
                    if event_id_resultado_pendiente is not None:
                        print("[JUEGO] Esperando ResultAccepted antes de abrir otro minijuego.")
                        mensajes_pendientes.append(mensaje)
                        continue


                    print(f"[JUEGO] Abriendo Minijuego {game_id}, intento {attempt}")

                    # Crear el minijuego que solicitó el servidor
                    if game_id == 1:
                        juego_actual = minijuego_1.Minijuego1(
                            callback_finalizar=al_terminar_minijuego
                        )

                    elif game_id == 2:
                        juego_actual = minijuego_2.Minijuego2(
                            callback_finalizar=al_terminar_minijuego
                        )

                    else:
                        print(f"[ERROR] GameID desconocido: {game_id}")
                        continue

                    # Crear el bucle de espera
                    bucle_minijuego = QEventLoop()

                    # Mostrar la ventana del minijuego
                    juego_actual.show()

                    # Consultar el servidor cada 300 milisegundos mientras jugamos
                    timer_consulta.start(300)

                    try:
                        # Esperar hasta que el minijuego termine
                        bucle_minijuego.exec()

                    finally:
                        # Detener las consultas cuando termine el minijuego
                        timer_consulta.stop()
                        bucle_minijuego = None

                    print("[JUEGO] Minijuego terminado. Continuando con la partida.")

                elif accion == "GameOver":
                    print("[JUEGO] El servidor ha finalizado la partida.")
                    estado.partida_activa = False
                    break

            app_qt.processEvents()
            time.sleep(0.3)

    except KeyboardInterrupt:
        print("\n[SALIDA] Desconexión manual solicitada por el usuario.")
    finally:
        conexion.cerrar_conexion()
        print("--- CLIENTE FINALIZADO ---")

if __name__ == "__main__":
    main()