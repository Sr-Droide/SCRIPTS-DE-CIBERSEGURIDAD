import pyperclip
import requests
import random
import string
import time
import sys
import re
import os

API = 'https://www.1secmail.com/api/v1/'
listaDeDominios = ['1secmail.com', '1secmail.net', '1secmail.org']
dominio = random.choice(listaDeDominios)

def generarNombreDeUsuario():
    caracteres = string.ascii_lowercase + string.digits
    nombreDeUsuario = ''.join(random.choice(caracteres) for i in range(10))
    return nombreDeUsuario

def extraer():
    obtenerNombreDeUsuario = re.search(r'login=(.*)&', nuevoCorreo).group(1)
    obtenerDominio = re.search(r'domain=(.*)', nuevoCorreo).group(1)
    return [obtenerNombreDeUsuario, obtenerDominio]

def imprimir_estado(msg: str):
    longitud_ultimo_msg = len(imprimir_estado.ultimo_msg) if hasattr(imprimir_estado, 'ultimo_msg') else 0
    print(' ' * longitud_ultimo_msg, end='\r')
    print(msg, end='\r')
    sys.stdout.flush()
    imprimir_estado.ultimo_msg = msg

def eliminarCorreo():
    url = 'https://www.1secmail.com/mailbox'
    datos = {
        'action': 'deleteMailbox',
        'login': f'{extraer()[0]}',
        'domain': f'{extraer()[1]}'
    }

    imprimir_estado("Eliminando tu dirección de correo - " + correo + '\n')
    req = requests.post(url, data=datos)

def verificarCorreos():
    enlaceReq = f'{API}?action=getMessages&login={extraer()[0]}&domain={extraer()[1]}'
    req = requests.get(enlaceReq).json()
    longitud = len(req)
    if longitud == 0:
        imprimir_estado("Tu buzón está vacío. Espera. El buzón se actualiza automáticamente cada 5 segundos.")
    else:
        listaId = []
        for i in req:
            for k, v in i.items():
                if k == 'id':
                    idCorreo = v
                    listaId.append(idCorreo)

        x = 'correos' if longitud > 1 else 'correo'
        imprimir_estado(f"Recibiste {longitud} {x}. (El buzón se actualiza automáticamente cada 5 segundos.)")

        directorio_actual = os.getcwd()
        directorio_final = os.path.join(directorio_actual, r'Todos los Correos')
        if not os.path.exists(directorio_final):
            os.makedirs(directorio_final)

        for i in listaId:
            msgLeido = f'{API}?action=readMessage&login={extraer()[0]}&domain={extraer()[1]}&id={i}'
            req = requests.get(msgLeido).json()
            for k, v in req.items():
                if k == 'from':
                    remitente = v
                if k == 'subject':
                    asunto = v
                if k == 'date':
                    fecha = v
                if k == 'textBody':
                    contenido = v

            ruta_archivo_correo = os.path.join(directorio_final, f'{i}.txt')

            with open(ruta_archivo_correo, 'w') as archivo:
                archivo.write("Remitente: " + remitente + '\n' + "Para: " + correo + '\n' + "Asunto: " + asunto + '\n' + "Fecha: " + fecha + '\n' + "Contenido: " + contenido + '\n')

entradaUsuario1 = input("¿Deseas usar un nombre de dominio personalizado (S/N): ").capitalize()

try:
    if entradaUsuario1 == 'S' or entradaUsuario1 == 's':
        entradaUsuario2 = input("\nIntroduce el nombre que deseas usar como tu nombre de dominio: ")
        nuevoCorreo = f"{API}?login={entradaUsuario2}&domain={dominio}"
        reqCorreo = requests.get(nuevoCorreo)
        correo = f"{extraer()[0]}@{extraer()[1]}"
        pyperclip.copy(correo)
        print("\nTu correo temporal es " + correo + " (Dirección de correo copiada al portapapeles.)" + "\n")
        print(f"---------------------------- | Buzón de {correo} | ----------------------------\n")
        while True:
            verificarCorreos()
            time.sleep(5)

    if entradaUsuario1 == 'N' or entradaUsuario1 == 'n':
        nuevoCorreo = f"{API}?login={generarNombreDeUsuario()}&domain={dominio}"
        reqCorreo = requests.get(nuevoCorreo)
        correo = f"{extraer()[0]}@{extraer()[1]}"
        pyperclip.copy(correo)
        print("\nTu correo temporal es " + correo + " (Dirección de correo copiada al portapapeles.)" + "\n")
        print(f"---------------------------- | Buzón de {correo} | ----------------------------\n")
        while True:
            verificarCorreos()
            time.sleep(5)

except (KeyboardInterrupt):
    eliminarCorreo()
    print("\nPrograma Interrumpido")
    os.system('cls' if os.name == 'nt' else 'clear')