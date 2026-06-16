import json

def guardarEnDisco(diccionarioDatos):
    """Guarda el estado actual del parqueo en un archivo JSON local."""
    try:
        archivo = open("parqueo_datos.json", "w")
        json.dump(diccionarioDatos, archivo, indent=4)
        archivo.close()
        return True
    except:
        return False

def cargarDesdeDisco():
    """Recupera los datos del JSON local al iniciar el sistema."""
    try:
        archivo = open("parqueo_datos.json", "r")
        diccionarioDatos = json.load(archivo)
        archivo.close()
        return diccionarioDatos
    except:
        return {}