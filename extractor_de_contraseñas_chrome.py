# Importación de módulos necesarios
import os  # Proporciona una forma de interactuar con el sistema de archivos
import json  # Permite trabajar con datos en formato JSON (JavaScript Object Notation)
import base64  # Utilizado para codificar y decodificar datos en Base64
import sqlite3  # Permite interactuar con bases de datos SQLite
import win32crypt  # Módulo específico de Windows para funciones de cifrado
from Crypto.Cipher import AES  # Proporciona funcionalidad de cifrado y descifrado AES (Advanced Encryption Standard)
import shutil  # Facilita operaciones de archivo como copiar o mover archivos
from datetime import timezone, datetime, timedelta  # Permite manejar fechas y horas


# Función que convierte la fecha de Chrome (almacenada en microsegundos desde el 1 de enero de 1601) a un objeto datetime
def get_chrome_datetime(chromedate):
    # Suma el tiempo transcurrido desde el 1 de enero de 1601 a partir de los microsegundos
    return datetime(1601, 1, 1) + timedelta(microseconds=chromedate)


# Función que obtiene la clave de cifrado utilizada por Chrome para las contraseñas
def get_encryption_key():
    # Construye la ruta al archivo Local State de Chrome donde se almacena la clave de cifrado
    local_state_path = os.path.join(os.environ["USERPROFILE"],
                                     "AppData", "Local", "Google", "Chrome",
                                     "User Data", "Local State")
    # Abre el archivo Local State para leer su contenido
    with open(local_state_path, "r", encoding="utf-8") as f:
        local_state = f.read()  # Lee todo el contenido del archivo
        local_state = json.loads(local_state)  # Convierte el contenido JSON en un diccionario de Python
    
    # Obtiene la clave cifrada de la sección os_crypt
    key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])  # Decodifica la clave de Base64
    key = key[5:]  # Elimina los primeros 5 bytes de la clave que son un prefijo
    # Desencripta la clave utilizando la función CryptUnprotectData
    return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]


# Función que desencripta una contraseña utilizando la clave proporcionada
def decrypt_password(password, key):
    try:
        iv = password[3:15]  # Extrae el vector de inicialización (IV) de la contraseña cifrada
        password = password[15:]  # Obtiene la parte cifrada de la contraseña
        # Crea un objeto cifrador AES en modo GCM (Galois/Counter Mode) usando la clave y el IV
        cipher = AES.new(key, AES.MODE_GCM, iv)  
        # Desencripta la contraseña y elimina los últimos 16 bytes (que son parte del proceso de cifrado)
        return cipher.decrypt(password)[:-16].decode()  # Devuelve la contraseña desencriptada
    except:
        # Si hay un error, intenta desencriptar utilizando win32crypt
        try:
            # Desencripta la contraseña usando CryptUnprotectData
            return str(win32crypt.CryptUnprotectData(password, None, None, None, 0)[1])
        except:
            return ""  # Devuelve una cadena vacía si hay un error


# Función que escribe contenido en un archivo de texto
def write_to_file(content):
    # Abre (o crea) el archivo passwords.txt en modo append (agregar al final)
    with open("passwords.txt", "a", encoding="utf-8") as f:
        f.write(content + "\n")  # Escribe el contenido en el archivo, seguido de un salto de línea


# Función que recupera contraseñas de la base de datos de Chrome
def recuperar_contrasenas(db_path):
    key = get_encryption_key()  # Llama a la función para obtener la clave de cifrado
    filename = "ChromeData.db"  # Nombre temporal para la base de datos de Chrome
    # Copia la base de datos de contraseñas de Chrome a un archivo temporal
    shutil.copyfile(db_path, filename)

    # Conecta a la base de datos SQLite
    db = sqlite3.connect(filename)
    cursor = db.cursor()  # Crea un cursor para ejecutar consultas en la base de datos
    # Ejecuta una consulta SQL para seleccionar las columnas relevantes de la tabla de inicios de sesión
    cursor.execute("SELECT origin_url, action_url, username_value, password_value, date_created, date_last_used FROM logins ORDER BY date_created")

    passwords_found = False  # Bandera para verificar si se encontraron contraseñas

    # Itera sobre las filas de resultados de la consulta
    for row in cursor.fetchall():
        origin_url = row[0]  # URL de origen donde se almacenó la contraseña
        action_url = row[1]  # URL donde se utiliza la contraseña
        username = row[2]  # Nombre de usuario asociado a la contraseña
        password = decrypt_password(row[3], key)  # Desencripta la contraseña almacenada
        date_created = row[4]  # Fecha de creación de la entrada
        date_last_used = row[5]  # Fecha de último uso de la entrada

        if username or password:  # Verifica si hay un nombre de usuario o una contraseña
            passwords_found = True  # Se encontraron contraseñas
            output = "--------------------------------------------------------------------\n"  # Encabezado
            output += f"Origin URL: {origin_url}\n"  # Agrega la URL de origen al resultado
            output += f"Action URL: {action_url}\n"  # Agrega la URL de acción al resultado
            output += f"Username: {username}\n"  # Agrega el nombre de usuario al resultado
            output += f"Password: {password}\n"  # Agrega la contraseña desencriptada al resultado

            # Si la fecha de creación es válida, agrega la fecha de creación al resultado
            if date_created != 86400000000 and date_created:
                output += f"Creation date: {str(get_chrome_datetime(date_created))}\n"
            # Si la fecha de último uso es válida, agrega la fecha de último uso al resultado
            if date_last_used != 86400000000 and date_last_used:
                output += f"Last Used: {str(get_chrome_datetime(date_last_used))}\n"
            
            print(output)  # Imprime el resultado en la consola
            write_to_file(output.strip())  # Escribe el resultado en el archivo

    # Si no se encontraron contraseñas, imprime y escribe un mensaje correspondiente
    if not passwords_found:  
        no_passwords_output = "--------------------------------------------------------------------\n"
        no_passwords_output += f"No se encontraron contraseñas para el perfil en {db_path}.\n"
        print(no_passwords_output)  # Imprime el mensaje en la consola
        write_to_file(no_passwords_output.strip())  # Escribe el mensaje en el archivo

    cursor.close()  # Cierra el cursor de la base de datos
    db.close()  # Cierra la conexión a la base de datos
    try:
        os.remove(filename)  # Intenta eliminar el archivo temporal
    except:
        pass  # Ignora cualquier error al intentar eliminar el archivo


# Función que busca en los perfiles de Chrome y recupera contraseñas
def buscar_en_perfiles(base_path):
    # Itera sobre las carpetas en el directorio de perfiles de Chrome
    for folder in os.listdir(base_path):  
        # Procesa solo carpetas que comienzan con 'Profile' o son 'Default'
        if folder.startswith('Profile') or folder == 'Default':  
            path = os.path.join(base_path, folder, 'Login Data')  # Construye la ruta a la base de datos de contraseñas
            # Verifica si la base de datos existe en la ruta
            if os.path.exists(path):  
                print("========================================")  
                print(f"Recuperando contraseñas de {folder}...")  # Imprime el nombre del perfil que se está procesando
                write_to_file(f"========================================")  # Escribe un encabezado en el archivo
                write_to_file(f"Recuperando contraseñas de {folder}...")  # Escribe el nombre del perfil en el archivo
                recuperar_contrasenas(path)  # Llama a la función para recuperar contraseñas del perfil


# Función principal que inicia el proceso de recuperación de contraseñas
def main():
    # Construye la ruta base a los datos del usuario de Chrome
    base_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "Google", "Chrome", "User Data")  
    buscar_en_perfiles(base_path)  # Llama a la función para buscar y recuperar contraseñas en los perfiles


# Ejecuta la función principal al correr el script
if __name__ == "__main__":  
    main()  # Llama a la función principal
    input("Presiona Enter para salir...")  # Espera a que el usuario presione Enter antes de cerrar
