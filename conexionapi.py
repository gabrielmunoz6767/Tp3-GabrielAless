import json
import urllib.request # importada para conseguir el url de la api

def obtenerVehiculosApi():
    """
    Se conecta directamente al link de la API en Mockaroo, descarga los 
    datos en tiempo real y arma las listas de atributos requeridas.
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