from estacionamiento import Estacionamiento
def arrancarPrograma():
    print("Sistema de Administración de Estacionamiento")
    infoPrueba = {"placa": "BCB-123", "marca": "Toyota"}
    estadiaPrueba = {"entrada": "08:00", "salida": "10:30"}
    pagoPrueba = {"monto": 2500, "estado": "Pagado"}
    unEstacionamiento = Estacionamiento("EST-001", infoPrueba, estadiaPrueba, pagoPrueba)
    unEstacionamiento.mostrarDatos()
arrancarPrograma()