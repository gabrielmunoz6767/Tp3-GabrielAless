class Estacionamiento:
    def __init__(self, codigoEspacio, infoVehiculo, datosEstadia, registroPago):
        """
        Estructura el objeto de un espacio de estacionamiento según 
        los requerimientos de la especificación.
        """
        self.codigoEspacio = codigoEspacio
        self.infoVehiculo = infoVehiculo       # Diccionario con placa, marca, color, tipo
        self.datosEstadia = datosEstadia       # Diccionario con hora entrada y salida
        self.registroPago = registroPago       # Diccionario con monto y método de pago

    def mostrarDatos(self):
        """Muestra de forma limpia la información del espacio en consola."""
        print("Estado del Espacio: " + str(self.codigoEspacio))
        if self.infoVehiculo and "placa" in self.infoVehiculo:
            print("Vehículo: " + str(self.infoVehiculo["marca"]) + " | Placa: " + str(self.infoVehiculo["placa"]))
            print("Horario: " + str(self.datosEstadia["entrada"]) + " a " + str(self.datosEstadia["salida"]))
            print("Cobro: ₡" + str(self.registroPago["monto"]) + " (" + str(self.registroPago["estado"]) + ")")
        else:
            print("El espacio se encuentra actualmente libre.")