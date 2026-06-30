import json
import urllib.request # importada para conseguir el url de la api

def obtenerVehiculosApi():
    """
    Funcionalidad:
    Consulta la API de Mockaroo y transforma la respuesta en un diccionario
    con la informacion de vehiculos necesaria para el sistema.
    Entrada:
    - Ninguna
    Salida:
    - diccionarioResultado(dict): diccionario {placa: [marca, color, tipo, espacio, horaEntrada, horaSalida, monto, tipoPago]}, vacio si falla la conexion
    """
    urlApi = "https://my.api.mockaroo.com/vehiculos_api.json?key=82ae48d0"
    try:
        respuesta = urllib.request.urlopen(urlApi)
        contenidoWeb = respuesta.read()
        respuesta.close()
        datosPlanos = json.loads(contenidoWeb.decode("utf-8"))
        diccionarioResultado = {}
        for item in datosPlanos:
            placa = str(item["placa"]).strip().upper()
            listaAtributos = [
                str(item["marca"]),
                str(item["color"]),
                str(item["tipoIngreso"]),
                str(item["espacio"]),
                str(item["horaEntrada"]),
                str(item["horaSalida"]),
                int(item["monto"]),
                str(item["tipoPago"])]
            diccionarioResultado[placa] = listaAtributos
        return diccionarioResultado
    except:
        return {}