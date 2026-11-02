"""Módulo para estructurar y validar los mensajes JSON según el protocolo del proyecto."""

from datetime import datetime

class ProtocoloMensajes:
    
    @staticmethod
    def crear_mensaje_join(player_id: str, event_id: str) -> dict:
        """Crea la estructura del mensaje para unirse al Lobby."""
        return {
            "timestamp": datetime.now().isoformat(),
            "player_id": player_id,
            "Action": "Join",
            "EventID": event_id,
            "Stage": "Lobby"
        }

    @staticmethod
    def crear_mensaje_ready(player_id: str, event_id: str, stage: str) -> dict:
        """Crea el mensaje StageReady para confirmar que estamos listos para la etapa."""
        return {
            "timestamp": datetime.now().isoformat(),
            "player_id": player_id,
            "Action": "StageReady",
            "EventID": event_id,
            "Stage": stage
        }

    @staticmethod
    def crear_mensaje_resultado(player_id: str, event_id: str, stage: str, game_id: int, attempt: int, result: str, score: int) -> dict:
        """Crea el mensaje Result al terminar un minijuego."""
        return {
            "timestamp": datetime.now().isoformat(),
            "player_id": player_id,
            "Action": "Result",
            "EventID": event_id,
            "Stage": stage,
            "GameID": game_id,
            "Attempt": attempt,
            "Result": result,
            "Score": score
        }

    @staticmethod
    def crear_mensaje_recover(player_id: str, event_id: str, stage: str) -> dict:
        """Crea el mensaje Recover para la Ronda Final."""
        return {
            "timestamp": datetime.now().isoformat(),
            "player_id": player_id,
            "Action": "Recover",
            "EventID": event_id,
            "Stage": stage
        }