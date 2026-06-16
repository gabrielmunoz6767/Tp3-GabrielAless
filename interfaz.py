import tkinter as tk
from tkinter import messagebox
# Importamos simpledialog para hacer la pregunta nativa al administrador
from tkinter import simpledialog
from conexionapi import obtenerVehiculosApi
from baseDatos import guardarEnDisco, cargarDesdeDisco

class VentanaParqueo:
    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title("Parqueo \"El TEC\"")
        self.ventana.geometry("750x450")
        self.ventana.config(bg="#f0f0f0")
        self.vehiculosActuales = cargarDesdeDisco()
        self.botonesMatriz = {}
        self.ventanaEmergente = None
        self.entradaPlaca = None
        self.entradaMarca = None
        self.entradaColor = None
        self.codigoEspacioActual = ""
        self.ventanaFactura = None
        self.entradaBusqueda = None
        self.btnBuscar = None
        self.placaPorFacturar = ""
        self.estructuraEspacios = []
        if len(self.vehiculosActuales) == 0:
            cantidadEspacios = simpledialog.askinteger(
                "Configuración Inicial", 
                "¿Cuántos parqueos tiene su estacionamiento?"    )
            if cantidadEspacios is None or cantidadEspacios <= 0:
                cantidadEspacios = 16
        else:
            cantidadEspacios = 16
        for i in range(1, cantidadEspacios + 1):
            if i <= 4:
                self.estructuraEspacios.append(("E" + str(i), "Eléctrico", "#add8e6"))
            elif i <= 12:
                self.estructuraEspacios.append(("R" + str(i - 4), "Regular", "#e0e0e0"))
            else:
                self.estructuraEspacios.append(("L" + str(i - 12), "Especial", "#ffeb3b"))
        self.crearContadoresSuperiores()
        
        frameInferior = tk.Frame(self.ventana, bg="#f0f0f0")
        frameInferior.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.crearMapaParqueo(frameInferior)
        self.crearMenuBotones(frameInferior)
        
        self.actualizarMapa()

    def crearContadoresSuperiores(self):
        """Crea las etiquetas numéricas superiores de control en tiempo real."""
        frameContadores = tk.Frame(self.ventana, bg="#f0f0f0", pady=10)
        frameContadores.pack(fill="x")
        totalInicial = str(len(self.estructuraEspacios))
        self.lblDisponibles = tk.Label(frameContadores, text="Disponibles: " + totalInicial, font=("Arial", 11, "bold"), fg="green", bg="#f0f0f0")
        self.lblDisponibles.pack(side=tk.LEFT, padx=40)
        
        self.lblOcupados = tk.Label(frameContadores, text="Ocupados: 0", font=("Arial", 11, "bold"), fg="red", bg="#f0f0f0")
        self.lblOcupados.pack(side=tk.LEFT, padx=40)

    def crearMapaParqueo(self, contenedorPadre):
        """Dibuja la cuadrícula de botones interactivos ordenados por sectores."""
        frameMapa = tk.LabelFrame(contenedorPadre, text="Distribución de Espacios", padx=15, pady=15, bg="#f0f0f0")
        frameMapa.pack(side=tk.LEFT, fill="both", expand=True, padx=5)
        
        posicion = 0
        totalEspacios = len(self.estructuraEspacios)
        filasNecesarias = (totalEspacios // 4) + 1
        
        for f in range(filasNecesarias):
            for c in range(4):
                if posicion < totalEspacios:
                    codigo, tipo, colorLibre = self.estructuraEspacios[posicion]
                    
                    btn = tk.Button(
                        frameMapa, 
                        text=codigo, 
                        font=("Arial", 10, "bold"),
                        width=8, 
                        height=3,
                        relief=tk.GROOVE,
                        command=lambda cod=codigo: self.eventoClickEspacio(cod)
                    )
                    btn.grid(row=f, column=c, padx=6, pady=6)
                    
                    self.botonesMatriz[codigo] = btn
                    posicion += 1

    def crearMenuBotones(self, contenedorPadre):
        """Construye el panel de acciones lateral derecho."""
        frameBotones = tk.LabelFrame(contenedorPadre, text="Menú Principal", padx=10, pady=15, bg="#f0f0f0", width=200)
        frameBotones.pack(side=tk.RIGHT, fill="y", padx=5)
        
        btnObtener = tk.Button(frameBotones, text="Obtener vehículos", width=18, pady=5, command=self.eventoCargarVehiculos)
        btnObtener.pack(pady=5)
        
        btnVer = tk.Button(frameBotones, text="Ver parqueo", width=18, pady=5, command=self.actualizarMapa)
        btnVer.pack(pady=5)
        
        btnReportes = tk.Button(frameBotones, text="Reportes", width=18, pady=5, command=self.eventoReportes)
        btnReportes.pack(pady=5)
        
        btnFacturar = tk.Button(frameBotones, text="Facturar", width=18, pady=5, command=self.eventoFacturar)
        btnFacturar.pack(pady=5)

    def eventoCargarVehiculos(self):
        """Ejecuta la lectura masiva de datos y despliega la alerta oficial."""
        self.vehiculosActuales = obtenerVehiculosApi()
        guardarEnDisco(self.vehiculosActuales)
        self.actualizarMapa()
        
        messagebox.showinfo(
            "Carga Masiva", 
            "Se cargaron los datos masivos, recuerde que los vehículos eléctricos y especiales no se cargan masivamente")

    def actualizarMapa(self):
        """Evalúa el estado de los espacios, aplica los colores y recalcula contadores."""
        contadorOcupados = 0
        
        for infoEspacio in self.estructuraEspacios:
            codigo, tipo, colorLibre = infoEspacio
            boton = self.botonesMatriz[codigo]
            
            estaOcupado = False
            for placa, datos in self.vehiculosActuales.items():
                if datos[3] == codigo:
                    estaOcupado = True
                    break
            
            if estaOcupado:
                boton.config(bg="red", fg="white")
                contadorOcupados += 1
            else:
                boton.config(bg=colorLibre, fg="black")
                
        contadorDisponibles = len(self.estructuraEspacios) - contadorOcupados
        self.lblDisponibles.config(text="Disponibles: " + str(contadorDisponibles))
        self.lblOcupados.config(text="Ocupados: " + str(contadorOcupados))

    def eventoClickEspacio(self, codigoEspacio):
        """Gestiona el clic en un espacio individual (Ver detalles o registro manual)."""
        self.codigoEspacioActual = codigoEspacio
        vehiculoEncontrado = None
        placaEncontrada = ""
        
        for placa, datos in self.vehiculosActuales.items():
            if datos[3] == codigoEspacio:
                vehiculoEncontrado = datos
                placaEncontrada = placa
                break
                
        self.ventanaEmergente = tk.Toplevel(self.ventana)
        self.ventanaEmergente.title("Espacio " + str(codigoEspacio))
        self.ventanaEmergente.geometry("320x280")
        
        if vehiculoEncontrado:
            tk.Label(self.ventanaEmergente, text="--- OCUPADO (" + str(codigoEspacio) + ") ---", font=("Arial", 11, "bold"), fg="red").pack(pady=10)
            tk.Label(self.ventanaEmergente, text="Placa: " + str(placaEncontrada)).pack(anchor="w", padx=20)
            tk.Label(self.ventanaEmergente, text="Marca: " + str(vehiculoEncontrado[0])).pack(anchor="w", padx=20)
            tk.Label(self.ventanaEmergente, text="Color: " + str(vehiculoEncontrado[1])).pack(anchor="w", padx=20)
            tk.Label(self.ventanaEmergente, text="Entrada: " + str(vehiculoEncontrado[4])).pack(anchor="w", padx=20)
            tk.Button(self.ventanaEmergente, text="Cerrar", command=self.ventanaEmergente.destroy).pack(pady=15)
        else:
            tk.Label(self.ventanaEmergente, text="--- REGISTRO MANUAL (" + str(codigoEspacio) + ") ---", font=("Arial", 11, "bold"), fg="green").pack(pady=10)
            
            tk.Label(self.ventanaEmergente, text="Placa:").pack(anchor="w", padx=20)
            self.entradaPlaca = tk.Entry(self.ventanaEmergente)
            self.entradaPlaca.pack(fill="x", padx=20)
            
            tk.Label(self.ventanaEmergente, text="Marca:").pack(anchor="w", padx=20)
            self.entradaMarca = tk.Entry(self.ventanaEmergente)
            self.entradaMarca.pack(fill="x", padx=20)
            
            tk.Label(self.ventanaEmergente, text="Color:").pack(anchor="w", padx=20)
            self.entradaColor = tk.Entry(self.ventanaEmergente)
            self.entradaColor.pack(fill="x", padx=20)
            
            tk.Button(self.ventanaEmergente, text="Registrar", command=self.guardarManual).pack(pady=15)

    def guardarManual(self):
        """Método independiente para procesar el formulario de registro manual."""
        p = self.entradaPlaca.get().strip().upper()
        m = self.entradaMarca.get().strip()
        c = self.entradaColor.get().strip()
        
        if p and m and c:
            self.vehiculosActuales[p] = [m, c, "Manual", self.codigoEspacioActual, "13:00", "14:00", 1000, "Efectivo"]
            guardarEnDisco(self.vehiculosActuales)
            self.actualizarMapa()
            self.ventanaEmergente.destroy()
        else:
            messagebox.showwarning("Atención", "Por favor llene todos los campos.")

    def eventoFacturar(self):
        """Abre la ventana flotante para buscar un vehículo."""
        self.ventanaFactura = tk.Toplevel(self.ventana)
        self.ventanaFactura.title("Facturación de Vehículo")
        self.ventanaFactura.geometry("350x200")
        
        tk.Label(self.ventanaFactura, text="--- SALIDA DE VEHÍCULO ---", font=("Arial", 11, "bold")).pack(pady=10)
        
        tk.Label(self.ventanaFactura, text="Digite la Placa del vehículo:").pack(anchor="w", padx=30)
        self.entradaBusqueda = tk.Entry(self.ventanaFactura, font=("Arial", 11))
        self.entradaBusqueda.pack(fill="x", padx=30, pady=5)
        
        self.btnBuscar = tk.Button(self.ventanaFactura, text="Buscar y Facturar", command=self.buscarYProcesar)
        self.btnBuscar.pack(pady=15)

    def buscarYProcesar(self):
        """Método independiente para buscar la placa en el diccionario."""
        placaBuscar = self.entradaBusqueda.get().strip().upper()
        
        if placaBuscar in self.vehiculosActuales:
            datosCarro = self.vehiculosActuales[placaBuscar]
            self.placaPorFacturar = placaBuscar
            
            self.entradaBusqueda.pack_forget()
            self.btnBuscar.pack_forget()
            
            tk.Label(self.ventanaFactura, text="Vehículo: " + str(datosCarro[0]) + " (" + str(datosCarro[1]) + ")", font=("Arial", 10)).pack(pady=2)
            tk.Label(self.ventanaFactura, text="Espacio Liberado: " + str(datosCarro[3]), font=("Arial", 10)).pack(pady=2)
            tk.Label(self.ventanaFactura, text="Monto Total a Pagar: ₡" + str(datosCarro[6]), font=("Arial", 11, "bold"), fg="darkgreen").pack(pady=5)
            
            tk.Button(self.ventanaFactura, text="Confirmar Pago y Salida", bg="green", fg="white", command=self.confirmarSalida).pack(pady=10)
        else:
            messagebox.showerror("Error", "La placa digitada no se encuentra activa en el parqueo.")

    def confirmarSalida(self):
        """Método independiente para eliminar el vehículo y refrescar la interfaz."""
        datosCarro = self.vehiculosActuales.pop(self.placaPorFacturar)
        guardarEnDisco(self.vehiculosActuales)
        self.actualizarMapa()
        
        mensaje = "Listo, el espacio " + str(datosCarro[3]) + " ya quedo libre."
        messagebox.showinfo("Salida", mensaje)
        
        self.ventanaFactura.destroy()

    def eventoReportes(self):
        """Procesa las estadísticas del parqueo con ciclos puros y abre la ventana."""
        totalDineroCaja = 0
        conteoMasivo = 0
        conteoManual = 0
        
        for placa in self.vehiculosActuales:
            datosCarro = self.vehiculosActuales[placa]
            montoVehiculo = datosCarro[6]
            totalDineroCaja = totalDineroCaja + montoVehiculo
            
            tipoIngreso = datosCarro[2]
            if tipoIngreso == "Masiva" or tipoIngreso == "Regular":
                conteoMasivo = conteoMasivo + 1
            elif tipoIngreso == "Manual":
                conteoManual = conteoManual + 1
                
        ventanaStats = tk.Toplevel(self.ventana)
        ventanaStats.title("Reportes Generales")
        ventanaStats.geometry("380x250")
        ventanaStats.config(bg="#f0f0f0")
        
        tk.Label(ventanaStats, text="--- ESTADÍSTICAS DEL PARQUEO ---", font=("Arial", 11, "bold"), bg="#f0f0f0").pack(pady=15)
        
        lblIngresos = tk.Label(
            ventanaStats, 
            text="Total de ingresos proyectados: ₡" + str(totalDineroCaja), 
            font=("Arial", 10, "bold"), 
            fg="darkgreen",
            bg="#f0f0f0"
        )
        lblIngresos.pack(anchor="w", padx=30, pady=5)
        
        lblMasivos = tk.Label(
            ventanaStats, 
            text="Vehículos ingresados por carga masiva: " + str(conteoMasivo), 
            font=("Arial", 10),
            bg="#f0f0f0"
        )
        lblMasivos.pack(anchor="w", padx=30, pady=5)
        
        lblManuales = tk.Label(
            ventanaStats, 
            text="Vehículos ingresados manualmente: " + str(conteoManual), 
            font=("Arial", 10),
            bg="#f0f0f0"
        )
        lblManuales.pack(anchor="w", padx=30, pady=5)
        
        btnCerrar = tk.Button(ventanaStats, text="Entendido", command=ventanaStats.destroy, width=12)
        btnCerrar.pack(pady=20)

    def mostrarVentana(self):
        self.ventana.mainloop()