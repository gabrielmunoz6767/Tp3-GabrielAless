import json
def guardarEnDisco(diccionarioDatos):
    with open("parqueo.json", "w", encoding="utf-8") as archivo:
        json.dump(diccionarioDatos, archivo, indent=4)
    print("El estado actual del parqueo se guardó en parqueo.json")
def cargarDesdeDisco():
    try:
        with open("parqueo.json", "r", encoding="utf-8") as archivo:
            return json.load(archivo)
    except FileNotFoundError:
        print("No se encontró parqueo.json previo. Iniciando vacío.")
        return {}