class Estacionamiento:
    def __init__(self, idRegistro, infoVehiculo, datosEstadia, datosPago):
        self.id = idRegistro          # Identificador único
        self.info = infoVehiculo      # Diccionario o texto con info del vehículo (placa, marca, etc.)
        self.estadia = datosEstadia    # Diccionario o texto con tiempos (entrada, salida)
        self.pago = datosPago          # Diccionario o texto con montos y estado del pago
    
    def mostrarDatos(self):
        print("ID Registro:", self.id)
        print("Información:", self.info)
        print("Estadía:", self.estadia)
        print("Pago:", self.pago)