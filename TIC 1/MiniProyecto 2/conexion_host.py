"""Estructura recomendada para gestionar la comunicación SSH/SFTP con el host central."""

import json
from pathlib import Path
import os
import paramiko


class ConexionHost:
    def __init__(self, config: dict):
        self.host = config["host"]
        self.port = config.get("port", 22)
        self.username = config["username"]
        self.password = config["password"]
        self.remote_inbox = config.get("remote_inbox", "/inbox")
        self.remote_outbox = config.get("remote_outbox", "/outbox")

        self.ssh = None
        self.sftp = None
        self.mensajes_leidos = set()

    def conectar(self):
        """Establece la conexión SSH y abre el canal SFTP."""
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=10
            )
            self.sftp = self.ssh.open_sftp()
            print("[CONEXIÓN] Conexión SSH y canal SFTP establecidos exitosamente.")
        except Exception as e:
            print(f"[ERROR CONEXIÓN] No se pudo establecer la conexión: {e}")
            self.cerrar_conexion()

    def cerrar_conexion(self):
        """Cierra de forma ordenada las conexiones SFTP y SSH."""
        if self.sftp:
            try:
                self.sftp.close()
            except Exception:
                pass
            self.sftp = None

        if self.ssh:
            try:
                self.ssh.close()
            except Exception:
                pass
            self.ssh = None
        print("[CONEXIÓN] Conexión cerrada de forma ordenada.")

    def verificar_conexion(self):
        """Comprueba si la conexión SSH/SFTP se encuentra disponible."""
        if not self.ssh or not self.sftp:
            return False
        try:
            #Comprueba si el transporte sigue activo
            transport = self.ssh.get_transport()
            return transport is not None and transport.is_active()
        except Exception:
            return False
        
    def enviar_json(self, mensaje: dict):
        """Transfiere un mensaje JSON al directorio /inbox del host central."""
        if not self.sftp:
            print("[ERROR SFTP] NO hay una sesión SFTP abierta para enviar mensajes.")
            return
        #Generar nombre único usando el EventID 
        event_id = mensaje.get("EventID","msg")
        nombre_archivo = f"{event_id}.json"
        #Ruta temporal local
        ruta_local = os.path.join(os.path.dirname(__file__), "..", nombre_archivo)
        #Guardar diccionario localmente
        with open(ruta_local, "w", encoding="utf-8") as f:
            json.dump(mensaje, f, ensure_ascii=False, indent=4)

        #Ruta remota 
        ruta_remota_temporal = f"{self.remote_inbox}/{nombre_archivo}.tmp"
        ruta_remota_final = f"{self.remote_inbox}/{nombre_archivo}"

        try:
            self.sftp.put(ruta_local, ruta_remota_temporal)
            self.sftp.rename(ruta_remota_temporal, ruta_remota_final)
            print(f"[ENVIADO] Mensaje {nombre_archivo} enviado correctamente a /inbox.")
        except Exception as e:
            print(f"[ERROR ENVÍO] Falló la transferencia del archivo {nombre_archivo}: {e}")
        finally:
            if os.path.exists(ruta_local):
                os.remove(ruta_local)

    def leer_nuevos_json(self):
        """Lee los mensajes JSON nuevos de /outbox ordenándolos cronológicamente 
        según el tiempo real de modificación del archivo en el servidor (st_mtime)."""
        mensajes_nuevos = []
        if not self.sftp:
            return mensajes_nuevos
        try:
            archivos_remotos = self.sftp.listdir(self.remote_outbox)

            # Filtrar archivos .json no leídos y obtener su hora de modificación en el servidor
            archivos_con_tiempo = []
            for archivo in archivos_remotos:
                if archivo.endswith(".json") and archivo not in self.mensajes_leidos:
                    ruta_remota = f"{self.remote_outbox}/{archivo}"
                    try:
                        # Consultar los atributos del archivo remoto para obtener su mtime real
                        attrs = self.sftp.stat(ruta_remota)
                        archivos_con_tiempo.append((archivo, attrs.st_mtime))
                    except Exception:
                        archivos_con_tiempo.append((archivo, 0))

            # Ordenar los archivos del más antiguo al más nuevo según el servidor
            archivos_con_tiempo.sort(key=lambda x: x[1])

            # Procesar los archivos en el orden correcto
            for archivo, _ in archivos_con_tiempo:
                ruta_remota = f"{self.remote_outbox}/{archivo}"
                ruta_local = os.path.join(os.path.dirname(__file__), "..", f"temp_{archivo}")

                try:
                    self.sftp.get(ruta_remota, ruta_local)
                    with open(ruta_local, "r", encoding="utf-8") as f:
                        contenido = json.load(f)
                        mensajes_nuevos.append(contenido)

                    self.mensajes_leidos.add(archivo)
                    print(f"[RECIBIDO] Mensaje nuevo procesado: {archivo}")
                except Exception as ex:
                    print(f"[ERROR LECTURA] No se pudo procesar el archivo {archivo}: {ex}")
                finally:
                    if os.path.exists(ruta_local):
                        os.remove(ruta_local)

        except Exception as e:
            print(f"[ERROR OUTBOX] No se pudo listar el directorio {self.remote_outbox}: {e}")

        return mensajes_nuevos

if __name__ == "__main__":
    # Cargar la configuración desde config_grupo.json
    ruta_config = os.path.join(os.path.dirname(__file__), "..", "config_grupo.json")
    try:
        with open(ruta_config, "r", encoding="utf-8") as f:
            config = json.load(f)
            
        print(f"[TEST] Intentando conectar con el player_id: {config.get('player_id')}")
        
        # Instanciar y conectar
        cliente = ConexionHost(config)
        cliente.conectar()
        
        if cliente.verificar_conexion():
            print("[TEST] ¡Éxito! La conexión SSH y SFTP está activa.")
        else:
            print("[TEST] La conexión falló.")
            
        cliente.cerrar_conexion()
        
    except Exception as e:
        print(f"[ERROR] No se pudo leer el archivo de configuración: {e}")
