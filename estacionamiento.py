class Estacionamiento:
    def __init__(self, codigoEspacio, infoVehiculo, datosEstadia, registroPago):
        """
        Funcionalidad:
        Inicializa un objeto que representa un espacio de estacionamiento ocupado.
        Entrada:
        - codigoEspacio(str): identificador del espacio (ej. "R1")
        - infoVehiculo(dict): datos del vehiculo (placa, marca, color, tipo)
        - datosEstadia(dict): datos de la estadia (hora de entrada y salida)
        - registroPago(dict): datos del pago (monto y estado)
        Salida:
        - Ninguna
        """
        self.codigoEspacio = codigoEspacio
        self.infoVehiculo = infoVehiculo       # Diccionario con placa, marca, color, tipo
        self.datosEstadia = datosEstadia       # Diccionario con hora entrada y salida
        self.registroPago = registroPago       # Diccionario con monto y método de pago

    def mostrarDatos(self):
        """
        Funcionalidad:
        Imprime en consola el estado actual del espacio de estacionamiento.
        Entrada:
        - Ninguna
        Salida:
        - Ninguna
        """

        print("Estado del Espacio: " + str(self.codigoEspacio))
        if self.infoVehiculo and "placa" in self.infoVehiculo:
            print("Vehículo: " + str(self.infoVehiculo["marca"]) + " | Placa: " + str(self.infoVehiculo["placa"]))
            print("Horario: " + str(self.datosEstadia["entrada"]) + " a " + str(self.datosEstadia["salida"]))
            print("Cobro: ₡" + str(self.registroPago["monto"]) + " (" + str(self.registroPago["estado"]) + ")")
        else:
            print("El espacio se encuentra actualmente libre.")