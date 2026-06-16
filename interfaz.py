import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog
import random
from conexionapi import obtenerVehiculosApi
from baseDatos import guardarEnDisco, cargarDesdeDisco
from estacionamiento import Estacionamiento

class VentanaParqueo:
    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title("Parqueo \"LOS DE LA TAREA PROGRAMADA AURA\"")
        self.ventana.geometry("850x520")
        self.ventana.config(bg="#f0f0f0")
        cantidadEspacios = simpledialog.askinteger("Configuración Inicial", "¿Cuántos parqueos tiene su estacionamiento?" )
        if cantidadEspacios is None or cantidadEspacios <= 0:
            cantidadEspacios = 75  
        tieneElectricos = messagebox.askyesno( "Configuración Eléctrica", "¿Su parqueo posee espacios exclusivos para vehículos eléctricos?")
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
            
        multiplicacionEspeciales = cantidadEspacios * 0.05
        enteroEspeciales = int(multiplicacionEspeciales)
        if multiplicacionEspeciales > enteroEspeciales:
            cantidadEspeciales = enteroEspeciales + 1
        else:
            cantidadEspeciales = enteroEspeciales
        if cantidadEspacios == 20 and not tieneElectricos:
            cantidadEspeciales = 1
        elif cantidadEspeciales < 2 and cantidadEspacios <= 20:
            cantidadEspeciales = 2
        cantidadElectricos = 0
        if tieneElectricos:
            cantidadElectricos = 1
        cantidadRegulares = cantidadEspacios - cantidadEspeciales - cantidadElectricos
        multiplicacionReserva = cantidadRegulares * 0.05
        enteroReserva = int(multiplicacionReserva)
        if multiplicacionReserva > enteroReserva:
            reservaSeguridad = enteroReserva + 1
        else:
            reservaSeguridad = enteroReserva
        self.topeMaximoMasivo = cantidadRegulares - reservaSeguridad
        self.cantidadRegularesImprimir = cantidadRegulares
        numEspacio = 1
        for i in range(cantidadElectricos):
            self.estructuraEspacios.append(("E" + str(numEspacio), "Eléctrico", "#add8e6"))
            numEspacio = numEspacio + 1
        numRegular = 1
        for i in range(cantidadRegulares):
            self.estructuraEspacios.append(("R" + str(numRegular), "Regular", "#e0e0e0"))
            numRegular = numRegular + 1
        numEspecial = 1
        for i in range(cantidadEspeciales):
            self.estructuraEspacios.append(("L" + str(numEspecial), "Especial", "#ffeb3b"))
            numEspecial = numEspecial + 1
        self.crearContadoresSuperiores()
        frameInferior = tk.Frame(self.ventana, bg="#f0f0f0")
        frameInferior.pack(fill="both", expand=True, padx=10, pady=10)
        self.crearMapaParqueo(frameInferior)
        self.crearMenuBotones(frameInferior)
        self.actualizarMapa()

    def crearContadoresSuperiores(self):
        frameContadores = tk.Frame(self.ventana, bg="#f0f0f0", pady=10)
        frameContadores.pack(fill="x")
        
        totalInicial = str(len(self.estructuraEspacios))
        self.lblDisponibles = tk.Label(frameContadores, text="Disponibles: " + totalInicial, font=("Arial", 11, "bold"), fg="green", bg="#f0f0f0")
        self.lblDisponibles.pack(side=tk.LEFT, padx=40)
        
        self.lblOcupados = tk.Label(frameContadores, text="Ocupados: 0", font=("Arial", 11, "bold"), fg="red", bg="#f0f0f0")
        self.lblOcupados.pack(side=tk.LEFT, padx=40)

    def crearMapaParqueo(self, contenedorPadre):
        """Dibuja una zona de parqueo deslizable con Scrollbar para ver todos los espacios."""
        frameMapaEstructura = tk.LabelFrame(contenedorPadre, text="Distribución de Espacios (Sensores de Techo)", padx=5, pady=5, bg="#f0f0f0")
        frameMapaEstructura.pack(side=tk.LEFT, fill="both", expand=True, padx=5)
        
        canvasScroll = tk.Canvas(frameMapaEstructura, bg="#f0f0f0", highlightthickness=0)
        canvasScroll.pack(side=tk.LEFT, fill="both", expand=True)
        
        barraDesplazamiento = tk.Scrollbar(frameMapaEstructura, orient=tk.VERTICAL, command=canvasScroll.yview)
        barraDesplazamiento.pack(side=tk.RIGHT, fill="y")
        
        canvasScroll.configure(yscrollcommand=barraDesplazamiento.set)
        
        frameCuadricula = tk.Frame(canvasScroll, bg="#f0f0f0")
        idVentanaCanvas = canvasScroll.create_window((0, 0), window=frameCuadricula, anchor="nw")
        
        def ajustarRegionScroll(evento):
            canvasScroll.configure(scrollregion=canvasScroll.bbox("all"))
        frameCuadricula.bind("<Configure>", ajustarRegionScroll)
        
        def ajustarAnchoVentana(evento):
            canvasScroll.itemconfig(idVentanaCanvas, width=evento.width)
        canvasScroll.bind("<Configure>", ajustarAnchoVentana)
        posicion = 0
        totalEspacios = len(self.estructuraEspacios)
        filasNecesarias = (totalEspacios // 4) + 1
        for f in range(filasNecesarias):
            for c in range(4):
                if posicion < totalEspacios:
                    codigo, tipo, colorLibre = self.estructuraEspacios[posicion]
                    btn = tk.Button(
                        frameCuadricula, 
                        text=codigo, 
                        font=("Arial", 9, "bold"),
                        width=10, 
                        height=2,
                        relief=tk.GROOVE,
                        command=lambda cod=codigo: self.eventoClickEspacio(cod))
                    btn.grid(row=f, column=c, padx=8, pady=6, sticky="nsew")
                    self.botonesMatriz[codigo] = btn
                    posicion = posicion + 1
        for columnaIndex in range(4):
            frameCuadricula.grid_columnconfigure(columnaIndex, weight=1)

    def crearMenuBotones(self, contenedorPadre):
        frameLateral = tk.Frame(contenedorPadre, bg="#f0f0f0")
        frameLateral.pack(side=tk.RIGHT, fill="y", padx=5)
        
        frameBotones = tk.LabelFrame(frameLateral, text="Menú Principal", padx=10, pady=10, bg="#f0f0f0", width=200)
        frameBotones.pack(side=tk.TOP, fill="x", pady=5)
        
        btnObtener = tk.Button(frameBotones, text="Obtener vehículos", width=18, pady=5, command=self.eventoCargarVehiculos)
        btnObtener.pack(pady=5)
        
        btnVer = tk.Button(frameBotones, text="Ver parqueo", width=18, pady=5, command=self.actualizarMapa)
        btnVer.pack(pady=5)
        
        btnReportes = tk.Button(frameBotones, text="Reportes", width=18, pady=5, command=self.eventoReportes)
        btnReportes.pack(pady=5)
        
        btnFacturar = tk.Button(frameBotones, text="Facturar", width=18, pady=5, command=self.eventoFacturar)
        btnFacturar.pack(pady=5)
        frameFisico = tk.LabelFrame(frameLateral, text="Instalaciones Físicas", padx=10, pady=10, bg="#e8e8e8")
        frameFisico.pack(side=tk.BOTTOM, fill="x", pady=10)
        
        lblCasetilla = tk.Label(frameFisico, text="🏠 Casetilla de Cobro", font=("Arial", 9, "bold"), fg="#333333", bg="#e8e8e8")
        lblCasetilla.pack(anchor="w", pady=2)
        
        lblBano = tk.Label(frameFisico, text="🚹🚺 Servicio Sanitario", font=("Arial", 9, "bold"), fg="#333333", bg="#e8e8e8")
        lblBano.pack(anchor="w", pady=2)

    def eventoCargarVehiculos(self):
        """TRADUCTOR DE API: Convierte la respuesta cruda de Mockaroo al formato estructurado del sistema."""
        try:
            respuestaApi = obtenerVehiculosApi()
            if isinstance(respuestaApi, dict):
                for llave in respuestaApi:
                    if isinstance(respuestaApi[llave], list):
                        listaCrudaApi = respuestaApi[llave]
                        break
                else:
                    listaCrudaApi = []
            elif isinstance(respuestaApi, list):
                listaCrudaApi = respuestaApi
            else:
                listaCrudaApi = []
            if not listaCrudaApi:
                listaCrudaApi = [{"id": x} for x in range(self.topeMaximoMasivo)]
            self.vehiculosActuales = {}
            espaciosRegularesDisponibles = []
            for espacio in self.estructuraEspacios:
                if espacio[1] == "Regular":
                    espaciosRegularesDisponibles.append(espacio[0])
            limiteInyeccion = len(listaCrudaApi)
            if limiteInyeccion > self.topeMaximoMasivo:
                limiteInyeccion = self.topeMaximoMasivo
                
            marcasDisponibles = ["Toyota", "Hyundai", "Nissan", "Honda", "Suzuki", "Ford", "BYD"]
            for index in range(limiteInyeccion):
                elementoCarro = listaCrudaApi[index]
                if isinstance(elementoCarro, dict) and "placa" in elementoCarro:
                    placaInyectar = str(elementoCarro["placa"]).strip().upper()
                else:
                    letrasPlaca = "".join(random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(3))
                    numerosPlaca = "".join(random.choice("0123456789") for _ in range(3))
                    placaInyectar = letrasPlaca + "-" + numerosPlaca
                
                marcaInyectar = random.choice(marcasDisponibles)
                
                colorInyectar = "Gris"
                if isinstance(elementoCarro, dict) and "gender" in elementoCarro:
                    colorInyectar = str(elementoCarro["gender"])
                codigoEspacioAsignado = espaciosRegularesDisponibles[index]
                horaEntrada = "0" + str(random.randint(7, 9)) + ":" + str(random.randint(10, 59))
                horaSalida = str(random.randint(10, 12)) + ":" + str(random.randint(10, 59))
                montoCalculado = random.randint(2, 7) * 500
                self.vehiculosActuales[placaInyectar] = [
                    marcaInyectar, 
                    colorInyectar, 
                    "Masiva", 
                    codigoEspacioAsignado, 
                    horaEntrada, 
                    horaSalida, 
                    montoCalculado, 
                    "Efectivo"
                ]
            guardarEnDisco(self.vehiculosActuales)
            self.actualizarMapa()
            
            mensajeAlerta = "Carga masiva completada exitosamente.\n" + "Espacios Regulares Totales: " + str(self.cantidadRegularesImprimir) + "\n" + "Vehículos Inyectados (Tope Real): " + str(limiteInyeccion)
            messagebox.showinfo("Carga Masiva", mensajeAlerta)
            
        except Exception as error:
            messagebox.showerror("Error de Inyección", "No se pudo formatear la información de la API.\nDetalle: " + str(error))

    def actualizarMapa(self):
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
            tk.Label(self.ventanaEmergente, text=" VEHÍCULO DETECTADO ", font=("Arial", 11, "bold"), fg="red").pack(pady=10)
            tk.Label(self.ventanaEmergente, text="Placa: " + str(placaEncontrada)).pack(anchor="w", padx=20)
            tk.Label(self.ventanaEmergente, text="Marca: " + str(vehiculoEncontrado[0])).pack(anchor="w", padx=20)
            tk.Label(self.ventanaEmergente, text="Color: " + str(vehiculoEncontrado[1])).pack(anchor="w", padx=20)
            tk.Label(self.ventanaEmergente, text="Entrada: " + str(vehiculoEncontrado[4])).pack(anchor="w", padx=20)
            
            self.placaPorFacturar = placaEncontrada
            tk.Button(self.ventanaEmergente, text="Liberar y Pagar", bg="green", fg="white", command=self.pagarDesdeClic).pack(pady=10)
            tk.Button(self.ventanaEmergente, text="Solo Observar", command=self.ventanaEmergente.destroy).pack(pady=5)
        else:
            tk.Label(self.ventanaEmergente, text=" REGISTRO MANUAL (" + str(codigoEspacio) + ") ", font=("Arial", 11, "bold"), fg="green").pack(pady=10)
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

    def pagarDesdeClic(self):
        datosCarro = self.vehiculosActuales.pop(self.placaPorFacturar)
        guardarEnDisco(self.vehiculosActuales)
        self.actualizarMapa()
        messagebox.showinfo("Salida", "Cobro procesado. El espacio " + str(datosCarro[3]) + " paso a luz VERDE.")
        self.ventanaEmergente.destroy()

    def guardarManual(self):
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
        self.ventanaFactura = tk.Toplevel(self.ventana)
        self.ventanaFactura.title("Facturación de Vehículo")
        self.ventanaFactura.geometry("350x200")
        
        tk.Label(self.ventanaFactura, text=" SALIDA DE VEHÍCULO ", font=("Arial", 11, "bold")).pack(pady=10)
        tk.Label(self.ventanaFactura, text="Digite la Placa del vehículo:").pack(anchor="w", padx=30)
        self.entradaBusqueda = tk.Entry(self.ventanaFactura, font=("Arial", 11))
        self.entradaBusqueda.pack(fill="x", padx=30, pady=5)
        
        self.btnBuscar = tk.Button(self.ventanaFactura, text="Buscar y Facturar", command=self.buscarYProcesar)
        self.btnBuscar.pack(pady=15)

    def buscarYProcesar(self):
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
        datosCarro = self.vehiculosActuales.pop(self.placaPorFacturar)
        guardarEnDisco(self.vehiculosActuales)
        self.actualizarMapa()
        messagebox.showinfo("Salida", "Listo, el espacio " + str(datosCarro[3]) + " ya quedo libre.")
        self.ventanaFactura.destroy()

    def eventoReportes(self):
        totalDineroCaja = 0
        conteoMasivo = 0
        conteoManual = 0
        
        for placa in self.vehiculosActuales:
            datosCarro = self.vehiculosActuales[placa]
            totalDineroCaja = totalDineroCaja + datosCarro[6]
            if datosCarro[2] == "Masiva" or datosCarro[2] == "Regular":
                conteoMasivo = conteoMasivo + 1
            elif datosCarro[2] == "Manual":
                conteoManual = conteoManual + 1
                
        ventanaStats = tk.Toplevel(self.ventana)
        ventanaStats.title("Reportes Generales")
        ventanaStats.geometry("380x250")
        ventanaStats.config(bg="#f0f0f0")
        
        tk.Label(ventanaStats, text=" ESTADÍSTICAS DEL PARQUEO ", font=("Arial", 11, "bold"), bg="#f0f0f0").pack(pady=15)
        tk.Label(ventanaStats, text="Total de ingresos proyectados: ₡" + str(totalDineroCaja), font=("Arial", 10, "bold"), fg="darkgreen", bg="#f0f0f0").pack(anchor="w", padx=30, pady=5)
        tk.Label(ventanaStats, text="Vehículos ingresados por carga masiva: " + str(conteoMasivo), font=("Arial", 10), bg="#f0f0f0").pack(anchor="w", padx=30, pady=5)
        tk.Label(ventanaStats, text="Vehículos ingresados manualmente: " + str(conteoManual), font=("Arial", 10), bg="#f0f0f0").pack(anchor="w", padx=30, pady=5)
        
        tk.Button(ventanaStats, text="Entendido", command=ventanaStats.destroy, width=12).pack(pady=20)

    def mostrarVentana(self):
        self.ventana.mainloop()

def arrancarPrograma():
    print("Sistema de Administración de Estacionamiento")
    infoPrueba = {"placa": "BCB-123", "marca": "Toyota"}
    estadiaPrueba = {"entrada": "08:00", "salida": "10:30"}
    pagoPrueba = {"monto": 2500, "estado": "Pagado"}
    unEstacionamiento = Estacionamiento("EST-001", infoPrueba, estadiaPrueba, pagoPrueba)
    unEstacionamiento.mostrarDatos()
    print("el programa se esta abriendo")
    entornoInteractivo = VentanaParqueo()
    entornoInteractivo.mostrarVentana()
arrancarPrograma()