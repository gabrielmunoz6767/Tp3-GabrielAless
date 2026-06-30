import json

def guardarEnDisco(diccionarioDatos):
    """
    Funcionalidad:
    Guarda el estado actual del parqueo en un archivo JSON en disco.
    Entrada:
    - diccionarioDatos(dict): diccionario con la informacion de todos los vehiculos activos
    Salida:
    - resultado(bool): True si se guardo correctamente, False si ocurrio un error
"""
    try:
        archivo = open("parqueo_datos.json", "w")
        json.dump(diccionarioDatos, archivo, indent=4)
        archivo.close()
        return True
    except:
        return False

def cargarDesdeDisco():
    """
    Funcionalidad:
    Recupera el diccionario de vehiculos guardado en disco al iniciar el sistema.
    Entrada:
    - Ninguna
    Salida:
    - diccionarioDatos(dict): datos recuperados del archivo, o un diccionario vacio si no existe
"""
    try:
        archivo = open("parqueo_datos.json", "r")
        diccionarioDatos = json.load(archivo)
        archivo.close()
        return diccionarioDatos
    except:
        return {}