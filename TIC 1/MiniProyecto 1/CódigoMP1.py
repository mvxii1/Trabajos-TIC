#parte 1 base de datos de nuestros pokemon muejeje
import subprocess

subprocess.run(
    ["bash", "correct_sensor.sh"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)
import time
import random
import board
import busio
import atexit
import adafruit_ads1x15.ads1115 as ADS
import adafruit_dht
from gpiozero import Button, TonalBuzzer, LED, RGBLED
from gpiozero.tones import Tone         
from adafruit_ads1x15.analog_in import AnalogIn

sensor_dht = adafruit_dht.DHT11(board.D17)

i2c = busio.I2C(board.SCL, board.SDA)
#Crear el objeto del ADS1115
ads = ADS.ADS1115(i2c)
#Leer los canales A0(EJE X) y A1(EJE Y)
eje_x = AnalogIn(ads, 0)
eje_y = AnalogIn(ads, 1)
boton_joystick = Button(21)
led_verde = LED(4)   # pin físico 7
led_rojo = LED(23)   # pin físico 16
led_captura = RGBLED(red=9, green=11, blue=10)# pin físico 21; pin físico 23; pin físico 19

#Mantener los leds apagados
led_verde.off()
led_rojo.off()
led_captura.off()

def apagar_leds():
    led_verde.off()
    led_rojo.off()
    led_captura.off()
    
atexit.register(apagar_leds)

buzzer = TonalBuzzer(18,octaves=3)

def actualizar_led_habitat(pokemon_habitat):
    total = 0

    for pokemon in pokemon_habitat:
        total = total + pokemon["cantidad"]

    if total > 0:
        led_verde.on()
        led_rojo.off()
    else:
        led_verde.off()
        led_rojo.on()
        
def led_captura_exitosa():
    led_captura.color = (0, 1, 1)   # Cian
    time.sleep(1)
    led_captura.off()


def led_captura_fallida():
    led_captura.color = (1, 1, 0)   # Amarillo
    time.sleep(1)
    led_captura.off()


def sonido_desplazar():
    buzzer.play(Tone(880.0))
    time.sleep(0.08)
    buzzer.stop()

def sonido_seleccionar():
    buzzer.play(Tone(659.25))
    time.sleep(0.1)
    buzzer.play(Tone(1046.50))
    time.sleep(0.15)
    buzzer.stop()
    
def sonido_aparicion():
    buzzer.play(Tone(523.25))
    time.sleep(0.1)
    buzzer.play(Tone(783.99))
    time.sleep(0.15)
    buzzer.stop()


def sonido_comida():
    buzzer.play(Tone(659.25))
    time.sleep(0.08)
    buzzer.play(Tone(783.99))
    time.sleep(0.08)
    buzzer.stop()


def sonido_captura_exitosa():
    buzzer.play(Tone(523.25))
    time.sleep(0.1)
    buzzer.play(Tone(659.25))
    time.sleep(0.1)
    buzzer.play(Tone(1046.50))
    time.sleep(0.2)
    buzzer.stop()


def sonido_captura_fallida():
    buzzer.play(Tone(440.0))
    time.sleep(0.15)
    buzzer.play(Tone(329.63))
    time.sleep(0.2)
    buzzer.stop()


def sonido_escape():
    buzzer.play(Tone(659.25))
    time.sleep(0.1)
    buzzer.play(Tone(440.0))
    time.sleep(0.15)
    buzzer.stop()
    

bosque = {
    "nombre": "Bosque",
    "pokemon": [
        {
            "nombre": "Bulbasaur",
            "tipo": "Planta-veneno",
            "especie": "Especial",
            "vida": 45,
            "captura": 0.25,
            "cantidad": 1,
            "ataques":[{"nombre": "Placaje", "daño":40}, {"nombre": "Látigo cepa", "daño":45}]
        },
        {
            "nombre": "Oddish",
            "tipo": "Planta-veneno",
            "especie": "Poco común",
            "vida": 45,
            "captura": 0.45,
            "cantidad": 2,
            "ataques":[{"nombre": "Absorber", "daño":35}, {"nombre": "Ácido", "daño":40}]
        },
        {
            "nombre": "Caterpie",
            "tipo": "Bicho",
            "especie": "Común",
            "vida": 45,
            "captura": 0.65,
            "cantidad": 3,
            "ataques":[{"nombre": "Placaje", "daño":40}, {"nombre": "Disparo Demora", "daño":20}]
        }  
    ]
}

pradera = {
    "nombre": "Pradera",
    "pokemon": [
        {
            "nombre": "Pikachu",
            "tipo": "Eléctrico",
            "especie": "Especial",
            "vida": 35,
            "captura": 0.25,
            "cantidad": 1,
            "ataques":[{"nombre": "Impactrueno", "daño":40}, {"nombre": "Ataque Rápido", "daño":40}]
        },
        {
            "nombre": "Eevee",
            "tipo": "Normal",
            "especie": "Poco común",
            "vida": 55,
            "captura": 0.45,
            "cantidad": 2,
            "ataques":[{"nombre": "Placaje", "daño":40}, {"nombre": "Ataque Arena", "daño":20}]
        },
        {
            "nombre": "Meowth",
            "tipo": "Normal",
            "especie": "Común",
            "vida": 40,
            "captura": 0.65,
            "cantidad": 3,
            "ataques":[{"nombre": "Arañazo", "daño":35}, {"nombre": "Gruñido", "daño":15}]
        }
    ]
}

cueva = {
    "nombre": "Cueva",
    "pokemon": [
        {
            "nombre": "Geodude",
            "tipo": "Roca-Tierra",
            "especie": "Común",
            "vida": 40,
            "captura": 0.65,
            "cantidad": 3,
            "ataques":[{"nombre": "Placaje", "daño":40}, {"nombre": "Lanzarrocas", "daño":50}]
        },
        {
            "nombre": "Zubat",
            "tipo": "Veneno-volador",
            "especie": "Poco común",
            "vida": 40,
            "captura": 0.45,
            "cantidad": 2,
            "ataques":[{"nombre": "Chupavidas", "daño":35}, {"nombre": "Supersónico", "daño":15}]
        },
        {
            "nombre": "Onix",
            "tipo": "Roca-tierra",
            "especie": "Especial",
            "vida": 35,
            "captura": 0.25,
            "cantidad": 1,
            "ataques":[{"nombre": "Lanzarrocas", "daño":50}, {"nombre": "Furia", "daño":30}]
        }
    ]
}

pantano = {
    "nombre": "Pantano",
    "pokemon": [
        {
            "nombre": "Poliwag",
            "tipo": "Agua",
            "especie": "Poco común",
            "vida": 40,
            "captura": 0.45,
            "cantidad": 2,
            "ataques":[{"nombre": "Burbuja", "daño":40}, {"nombre": "Hipnosis", "daño":10}]
        },
        {
            "nombre": "Lotad",
            "tipo": "Agua-planta",
            "especie": "Especial",
            "vida": 40,
            "captura": 0.25,
            "cantidad": 1,
            "ataques":[{"nombre": "Impresionar", "daño":30}, {"nombre": "Absorber", "daño":35}]
        },
        {
            "nombre": "Psyduck",
            "tipo": "Agua",
            "especie": "Común",
            "vida": 50,
            "captura": 0.65,
            "cantidad": 3,
            "ataques":[{"nombre": "COnfusión", "daño":50}, {"nombre": "Arañazo", "daño":35}]
        }
    ]
}

safari = {
    "Bosque": bosque,
    "Pradera": pradera,
    "Cueva": cueva,
    "Pantano": pantano
}

def obtener_habitats_disponibles(temperatura, humedad):
    habitats =[]
    if temperatura < 20.0:
        habitats.append("Cueva")
    if temperatura >= 20.0:
        habitats.append("Pradera")
    if 50.0 <= humedad <= 75.0:
        habitats.append("Bosque")
    if humedad > 75.0:
        habitats.append("Pantano")
    if not habitats:
        habitats.append("Pradera")
    return habitats

def actualizar_clima():
    try:
        temp = sensor_dht.temperature
        hum = sensor_dht.humidity
        if temp is not None and hum is not None:
            print(f"\n[CLIMA ACTUAL] Temperatura: {temp}°C | Humedad: {hum}%")
            return obtener_habitats_disponibles(temp,hum)
    except RuntimeError as error:
        print("Error sensor: ", error)
        return None
    
    
def leer_joystick():
    voltaje_x = eje_x.voltage
    voltaje_y = eje_y.voltage
    direccion = "CENTRO"
    
    #Como el centro es ~1.65V, detectamos los extremos para el movimiento
    if voltaje_y < 0.5:
        direccion = "ARRIBA"
    elif voltaje_y > 2.8:
        direccion = "ABAJO"
    elif voltaje_x > 2.8:
        direccion = "DERECHA"
    elif voltaje_x < 0.5:
        direccion = "IZQUIERDA"
    
    return direccion

def seleccionar_habitat(zonas):
    posicion = 0
    posicion_anterior = -1
    
    while True:
        if posicion != posicion_anterior:
            print("\n===== HABITATS DISPONIBLES =====")
        
            for i in range(len(zonas)):
                if i == posicion:
                    print(">", zonas[i])
                else:
                    print(" ", zonas[i])
            posicion_anterior = posicion
                    
        direccion = leer_joystick()
        if direccion == "ABAJO":
            sonido_desplazar()  
            posicion = posicion + 1
            
            if posicion >= len(zonas):
                posicion = 0
            time.sleep(0.5)
        elif direccion == "ARRIBA":
            sonido_desplazar()  
            posicion = posicion - 1
            
            if posicion < 0:
                posicion = len(zonas) - 1
            time.sleep(0.5)
            
        if boton_joystick.is_pressed:
            sonido_seleccionar() 
            while boton_joystick.is_pressed:
                time.sleep(0.05)
            return zonas[posicion]
        
        time.sleep(0.1)

def seleccionar_pokemon(pokemon_habitat):
    posicion = 0
    posicion_anterior = -1
    
    while True:
        
        if posicion != posicion_anterior:
            print("\n===== POKEMON DISPONIBLES =====")
        
            for i in range(len(pokemon_habitat)):
                if i == posicion:
                    print(">", pokemon_habitat[i]["nombre"],
                          "- Disponibles:", pokemon_habitat[i]["cantidad"])
                else:
                    print(" ", pokemon_habitat[i]["nombre"],
                            "- Disponibles:", pokemon_habitat[i]["cantidad"])
            posicion_anterior = posicion
                    
        direccion = leer_joystick()
        
        if direccion == "ABAJO":
            sonido_desplazar()  
            posicion = posicion + 1
            
            if posicion >= len(pokemon_habitat):
                posicion = 0
                
            time.sleep(0.5)
            
        elif direccion == "ARRIBA":
            sonido_desplazar()  
            posicion = posicion - 1
            
            if posicion < 0:
                posicion = len(pokemon_habitat) - 1
                
            time.sleep(0.5)
            
        if boton_joystick.is_pressed:
            sonido_seleccionar()
            while boton_joystick.is_pressed:
                time.sleep(0.05)
            return pokemon_habitat[posicion]
        
def proxima_aventura():
    eventos = ["Descansar", "Atrapar"]
    evento = random.choice(eventos)

    return evento

def esperar_aventura():
    print("\nPresiona el botón para iniciar la próxima aventura...")

    while not boton_joystick.is_pressed:
        time.sleep(0.05)

    sonido_seleccionar()

    while boton_joystick.is_pressed:
        time.sleep(0.05)

    return proxima_aventura()

def descansar(habitat):
    frases = {
        "Bosque": [
            "Te sientas bajo un árbol mientras escuchas a los Pokémon del bosque.",
            "Descansas entre los árboles mientras una suave brisa mueve las hojas.",
            "Encuentras un lugar tranquilo en el bosque para recuperar energías."
        ],

        "Pradera": [
            "Te recuestas sobre el pasto mientras observas a los Pokémon de la pradera.",
            "Descansas un momento mientras el viento recorre la pradera.",
            "Encuentras un lugar tranquilo entre el pasto para recuperar energías."
        ],

        "Cueva": [
            "Decides descansar entre las rocas mientras escuchas sonidos en la cueva.",
            "Te sientas un momento mientras los Pokémon de la cueva sienten curiosidad por ti.",
            "Encuentras un rincón tranquilo de la cueva para recuperar energías."
        ],

        "Pantano": [
            "Descansas cerca del agua mientras escuchas a los Pokémon del pantano.",
            "Te detienes un momento mientras observas las plantas del pantano.",
            "Encuentras un lugar tranquilo para descansar junto al pantano."
        ]
    }

    frase = random.choice(frases[habitat])

    print("\n===== DESCANSAR =====")
    print(frase)
    
def pokemon_salvaje(pokemon_habitat):
    disponibles = []

    for pokemon in pokemon_habitat:
        if pokemon["cantidad"] > 0:
            disponibles.append(pokemon)

    if len(disponibles) == 0:
        print("\nNo quedan Pokemon disponibles en este habitat.")
        return None

    elegido = random.choice(disponibles)
    sonido_aparicion()

    print("\n===== POKEMON SALVAJE =====")
    print("¡Un", elegido["nombre"], "salvaje apareció!")
    print("Tipo:", elegido["tipo"])
    print("Vida:", elegido["vida"])

    return elegido

def menu_encuentro():
    opciones = ["Lanzar Poke Ball", "Dar de comer", "Escapar"]
    posicion = 0
    posicion_anterior = -1

    while True:

        if posicion != posicion_anterior:
            print("\n===== ¿QUE QUIERES HACER? =====")

            for i in range(len(opciones)):
                if i == posicion:
                    print(">", opciones[i])
                else:
                    print(" ", opciones[i])

            posicion_anterior = posicion

        direccion = leer_joystick()

        if direccion == "ABAJO":
            sonido_desplazar()
            posicion = posicion + 1

            if posicion >= len(opciones):
                posicion = 0

            time.sleep(0.5)

        elif direccion == "ARRIBA":
            sonido_desplazar()
            posicion = posicion - 1

            if posicion < 0:
                posicion = len(opciones) - 1

            time.sleep(0.5)

        if boton_joystick.is_pressed:
            sonido_seleccionar()

            while boton_joystick.is_pressed:
                time.sleep(0.05)

            return opciones[posicion]
        
def escapar(pokemon):
    print("\n===== ESCAPAR =====")
    print("Escapaste de", pokemon["nombre"], "salvaje.")
    
    sonido_escape()
    led_captura_fallida()
    
def dar_comida(probabilidad):
    probabilidad = probabilidad + 0.20

    if probabilidad > 1:
        probabilidad = 1
        
    sonido_comida()

    print("\n===== DAR DE COMER =====")
    print("Le diste comida al Pokemon.")
    print("La probabilidad de captura aumentó a", int(probabilidad * 100), "%")

    return probabilidad

def lanzar_pokeball(pokemon, probabilidad, equipo, pokemon_habitat):
    numero = random.random()

    print("\n===== LANZAR POKE BALL =====")
    print("Lanzaste una Poke Ball...")

    if numero < probabilidad:
        print("¡Capturaste a", pokemon["nombre"], "!")
        
        sonido_captura_exitosa()
        led_captura_exitosa()

        pokemon["cantidad"] = pokemon["cantidad"] - 1
        actualizar_led_habitat(pokemon_habitat)

        if len(equipo) < 6:
            equipo.append(pokemon)
            print(pokemon["nombre"], "fue agregado a tu equipo.")
        else:
            print("Tu equipo ya tiene 6 Pokemon.")

        return True

    else:
        print("¡La captura falló!")
        
        sonido_captura_fallida()
        led_captura_fallida()
        return False


equipo = []
print("===== ZONA SAFARI POKEMON =====")
zonas = None

while zonas is None:
    zonas = actualizar_clima()
    time.sleep(2)
    
habitat_elegido = seleccionar_habitat(zonas)

print("\nElegiste:", habitat_elegido)

pokemon_habitat = safari[habitat_elegido]["pokemon"]

actualizar_led_habitat(pokemon_habitat)

pokemon_elegido = seleccionar_pokemon(pokemon_habitat)

    
print("\n===== POKEDEX =====")
print("Nombre:",pokemon_elegido["nombre"])
print("Tipo:", pokemon_elegido["tipo"])
print("Vida Maxima:", pokemon_elegido["vida"])
print("Probabilidad de captura:", pokemon_elegido["captura"])
print("Cantidad disponibles:", pokemon_elegido["cantidad"])
print("Ataques")
print("-", pokemon_elegido["ataques"][0]["nombre"],
    "- Daño:", pokemon_elegido["ataques"][0]["daño"])
print("-", pokemon_elegido["ataques"][1]["nombre"],
    "- Daño:", pokemon_elegido["ataques"][1]["daño"])

while True:

    evento = esperar_aventura()

    if evento == "Descansar":
        descansar(habitat_elegido)

    elif evento == "Atrapar":
        pokemon_encontrado = pokemon_salvaje(pokemon_habitat)

        if pokemon_encontrado != None:
            probabilidad_actual = pokemon_encontrado["captura"]
            encuentro_activo = True

            while encuentro_activo:
                accion = menu_encuentro()

                print("\nElegiste:", accion)

                if accion == "Escapar":
                    escapar(pokemon_encontrado)
                    encuentro_activo = False

                elif accion == "Dar de comer":
                    probabilidad_actual = dar_comida(probabilidad_actual)

                elif accion == "Lanzar Poke Ball":
                    captura = lanzar_pokeball(
                        pokemon_encontrado,
                        probabilidad_actual,
                        equipo,
                        pokemon_habitat
                    )

                    if captura == True:
                        encuentro_activo = False

