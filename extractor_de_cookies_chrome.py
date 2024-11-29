import os
import json
import base64
import sqlite3
import shutil
import subprocess  # para cerrar Chrome
from datetime import datetime, timedelta
import win32crypt  # pip install pypiwin32
from Crypto.Cipher import AES  # pip install pycryptodome

def close_chrome():
    """Cierra todas las ventanas de Google Chrome."""
    try:
        # Ejecutar el comando para cerrar Chrome en Windows
        subprocess.call("taskkill /IM chrome.exe /F", shell=True)
        print("Google Chrome ha sido cerrado.")
    except Exception as e:
        print(f"Error al intentar cerrar Google Chrome: {e}")

def get_chrome_datetime(chromedate):
    if chromedate != 86400000000 and chromedate:
        try:
            return datetime(1601, 1, 1) + timedelta(microseconds=chromedate)
        except Exception as e:
            print(f"Error: {e}, chromedate: {chromedate}")
            return chromedate
    else:
        return ""

def get_encryption_key():
    local_state_path = os.path.join(os.environ["USERPROFILE"],
                                    "AppData", "Local", "Google", "Chrome",
                                    "User Data", "Local State")
    with open(local_state_path, "r", encoding="utf-8") as f:
        local_state = f.read()
        local_state = json.loads(local_state)

    key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    key = key[5:]  # quitar la cadena 'DPAPI'
    return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]

def decrypt_data(data, key):
    if not data or len(data) < 15:  # Asegúrate de que hay suficientes bytes
        return ""

    try:
        iv = data[3:15]  # Vector de inicialización
        data = data[15:]  # Datos encriptados
        cipher = AES.new(key, AES.MODE_GCM, iv)
        decrypted = cipher.decrypt(data[:-16])  # Extrae el MAC
        try:
            return decrypted.decode('utf-8')  # Intenta decodificar a UTF-8
        except UnicodeDecodeError:
            # Manejo de caso de bytes no decodificables
            return f"[Valor desencriptado no legible: {list(decrypted)}]"  # Muestra los bytes en forma de lista
    except Exception as e:
        print(f"Error al desencriptar: {e}")  # Log de error
        return "[Error al desencriptar]"

def main():
    # Cerrar Google Chrome antes de iniciar
    close_chrome()

    # Nombre del archivo de salida
    output_filename = "cookies_output.txt"
    
    # Abrir archivo de salida en modo escritura
    with open(output_filename, "w", encoding="utf-8") as output_file:
        user_data_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "Google", "Chrome", "User Data")
        profiles = [f for f in os.listdir(user_data_path) if f.startswith("Profile") or f == "Default"]

        key = get_encryption_key()
        
        for profile in profiles:
            db_path = os.path.join(user_data_path, profile, "Network", "Cookies")
            if os.path.isfile(db_path):
                # Escribir encabezados en la terminal y en el archivo
                header = f"\n========================================\nRecuperando las cookies de {profile}...\n--------------------------------------------------------------------\n"
                print(header)
                output_file.write(header)
                
                filename = f"Cookies_{profile}.db"
                shutil.copyfile(db_path, filename)
                db = sqlite3.connect(filename)
                db.text_factory = lambda b: b.decode(errors="ignore")
                cursor = db.cursor()
                
                cursor.execute(""" 
                SELECT host_key, name, value, creation_utc, last_access_utc, expires_utc, encrypted_value 
                FROM cookies""")
                
                cookies_found = False
                for host_key, name, value, creation_utc, last_access_utc, expires_utc, encrypted_value in cursor.fetchall():
                    cookies_found = True
                    
                    # Intenta desencriptar solo si no hay valor
                    if not value:
                        decrypted_value = decrypt_data(encrypted_value, key)
                    else:
                        decrypted_value = value

                    # Si el valor desencriptado sigue vacío, maneja el caso
                    if not decrypted_value:
                        decrypted_value = "[Valor encriptado vacío o desencriptación fallida]"

                    # Construir la salida para la terminal y el archivo
                    cookie_info = (
                        f"Host: {host_key}\n"
                        f"Nombre de la Cookie: {name}\n"
                        f"Valor de la Cookie (Desencriptado): {decrypted_value}\n"
                        f"Fecha y Hora de Creación (UTC): {get_chrome_datetime(creation_utc)}\n"
                        f"Último Acceso (UTC): {get_chrome_datetime(last_access_utc)}\n"
                        f"Fecha de Expiración (UTC): {get_chrome_datetime(expires_utc)}\n"
                        "--------------------------------------------------------------------\n"
                    )
                    
                    # Imprimir en la terminal y escribir en el archivo
                    print(cookie_info)
                    output_file.write(cookie_info)

                if not cookies_found:
                    no_cookies_message = f"# No se encontraron cookies para el perfil: {profile}\n"
                    print(no_cookies_message)
                    output_file.write(no_cookies_message)
                
                # Escribir el separador final
                separator = "========================================\n"
                print(separator)
                output_file.write(separator)
                
                db.close()
                os.remove(filename)
            else:
                no_db_message = f"# No se encontró la base de datos de cookies para el perfil: {profile}\n"
                print(no_db_message)
                output_file.write(no_db_message)

if __name__ == "__main__":
    main()