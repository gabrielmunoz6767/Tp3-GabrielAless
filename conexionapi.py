import urllib.request
import json
def procesarDatosJson(listaObjetos):
    diccionarioVehiculos = {}
    filas = ["A", "B", "C", "D"]
    posicionActual = 0
    for item in listaObjetos:
        placa = item.get("reg_number", "SINDATO") # asi viene tal cual en el json, por ende se usa las mismas variables con este simbolito _
        marca = item.get("vehicle_make", "Genérico")
        color = item.get("color", "Blanco")
        fila = filas[(posicionActual // 5) % len(filas)]
        columna = (posicionActual % 5) + 1
        ubicacion = f"{fila}{columna}"
        posicionActual += 1
        diccionarioVehiculos[placa] = [
            marca,
            color,
            "Regular",          # Tipo por defecto
            ubicacion,          # Ubicación asignada
            "08:00",            # Hora entrada por defecto
            "12:00",            # Hora salida por defecto
            2000,               # Monto por defecto
            "Efectivo"          # Tipo pago por defecto
        ]
    return diccionarioVehiculos
def obtenerVehiculosApi():
    urlApi = "https://api.mockaroo.com/api/v1/vehiculos?key=tu_api_key_aqui"
    try:
        with urllib.request.urlopen(urlApi, timeout=3) as respuesta:
            datosRaw = json.loads(respuesta.read().decode())
            return procesarDatosJson(datosRaw)
    except:
        print("No se pudo conectar al API")
        try:
            with open("vehicle_data.json", "r", encoding="utf-8") as archivo:
                datosRaw = json.load(archivo)
                return procesarDatosJson(datosRaw)
        except:
            return {}