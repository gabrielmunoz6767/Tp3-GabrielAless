import json

def guardarEnDisco(listaDeListasVehicos):
    """
    Funcionalidad:
    Guarda la matriz de vehículos en un archivo JSON en disco utilizando únicamente listas.
    Entrada:
    - listaDeListasVehicos (list): Matriz donde cada elemento es una lista con los datos de un vehículo.
    Salida:
    - resultado (bool): True si se guardó correctamente, False si ocurrió un error.
    """
    try:
        archivo = open("parqueo_datos.json", "w", encoding="utf-8")
        json.dump(listaDeListasVehicos, archivo, indent=4) 
        archivo.close()
        return True
    except:
        return False

def cargarMemoria():
    """
    Funcionalidad:
    Recupera la matriz de vehículos guardada en disco al iniciar el sistema.
    Entrada:
    - Ninguna
    Salida:
    - listaDatos (list): Matriz con los datos recuperados, o una lista vacía si no existe.
    """
    try:
        archivo = open("parqueo_datos.json", "r", encoding="utf-8")
        listaDatos = json.load(archivo) 
        archivo.close()
        if isinstance(listaDatos, list):
            return listaDatos
        return []
    except:
        return []