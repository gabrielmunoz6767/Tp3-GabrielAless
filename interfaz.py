import tkinter as tk
from conexionapi import obtenerVehiculosApi

class VentanaParqueo:
    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title("Sistema de Estacionamiento")
        self.ventana.geometry("600x500")
        self.vehiculosActuales = {}
        self.botonesMatriz = {}
        self.crearMenuSuperior()
        self.crearMapaEstacionamiento()

    def crearMenuSuperior(self):
        frameMenu = tk.Frame(self.ventana, pady=10)
        frameMenu.pack()
        btnCargar = tk.Button(frameMenu, text="Obtener vehículos", command=self.eventoCargarVehiculos)
        btnCargar.pack(side=tk.LEFT, padx=5)
        btnVer = tk.Button(frameMenu, text="Ver estacionamiento", command=self.actualizarMapa)
        btnVer.pack(side=tk.LEFT, padx=5)

    def crearMapaEstacionamiento(self):
        self.frameMapa = tk.Frame(self.ventana, bd=2, relief=tk.SUNKEN, padx=20, pady=20)
        self.frameMapa.pack(pady=20)
        filas = ["A", "B", "C", "D"]
        for r in range(len(filas)):
            for c in range(1, 6):
                codigoEspacio = f"{filas[r]}{c}"
                btnEspacio = tk.Button(
                    self.frameMapa, 
                    text=codigoEspacio, 
                    bg="green", 
                    fg="white", 
                    width=6, 
                    height=2,
                    command=lambda cod=codigoEspacio: self.eventoClickEspacio(cod))
                btnEspacio.grid(row=r, column=c-1, padx=5, pady=5)
                self.botonesMatriz[codigoEspacio] = btnEspacio

    def eventoCargarVehiculos(self):
        self.vehiculosActuales = obtenerVehiculosApi()
        print("Datos cargados exitosamente desde el API.")
        self.actualizarMapa()

    def actualizarMapa(self):
        for codigoEspacio, boton in self.botonesMatriz.items():
            estaOcupado = False
            for placa, datos in self.vehiculosActuales.items():
                if datos[3] == codigoEspacio: # El índice 3 es la ubicación
                    estaOcupado = True
                    break
            if estaOcupado:
                boton.config(bg="red")
            else:
                boton.config(bg="green")
    def eventoClickEspacio(self, codigoEspacio):
        encontrado = False
        for placa, datos in self.vehiculosActuales.items():
            if datos[3] == codigoEspacio:
                print(f"Espacio {codigoEspacio} ocupado por: Placa {placa}, Marca {datos[0]}, Color {datos[1]}")
                encontrado = True
                break
        if not encontrado:
            print(f"Espacio {codigoEspacio} está libre.")
    def mostrarVentana(self):
        self.ventana.mainloop()