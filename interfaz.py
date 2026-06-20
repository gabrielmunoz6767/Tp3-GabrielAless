import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog
from tkinter import ttk
import random
import re
from datetime import datetime  
from conexionapi import obtenerVehiculosApi
from baseDatos import guardarEnDisco, cargarDesdeDisco
from estacionamiento import Estacionamiento
from factura import generarComprobantePago, generarVoucherEntrada

class VentanaParqueo:
    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title("Parqueo \"LOS QUE TENEMOS BASTANTE AURILLA\"")
        self.ventana.geometry("850x520")
        self.ventana.config(bg="#f0f0f0")
        self.ventana.withdraw() # aqui se oculta temporal mente la ventana 
        
        cantidadEspacios = simpledialog.askinteger(
            "Configuracion Inicial", 
            "¿Cuantos parqueos tiene su estacionamiento?")
        if cantidadEspacios is None or cantidadEspacios <= 0:
            cantidadEspacios = 75
            
        tieneElectricos = messagebox.askyesno(
            "Configuracion Electrica",
            "¿Su parqueo posee espacios exclusivos para vehiculos electricos?")

        self.ventana.deiconify() # aqui se muestra de nuevo
        
        self.vehiculosActuales = cargarDesdeDisco()
        self.botonesMatriz = {}
        self.ventanaEmergente = None
        self.entradaPlaca = None
        self.comboMarca = None  
        self.comboColor = None  
        self.entradaHoraEntrada = None  
        self.tipoEspacioActualSeleccionado = ""  
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
            self.estructuraEspacios.append(("R" + str(numRegular), "Regular", "#00fc2a"))
            numRegular = numRegular + 1
        numEspecial = 1
        for i in range(cantidadEspeciales):
            self.estructuraEspacios.append(("L" + str(numEspecial), "Especial", "#1c05ed"))
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
            messagebox.showerror("No se pudo formatear la información de la API.\nDetalle: " + str(error))

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
        tipoEspacioTexto = "Regular"
        for espacio in self.estructuraEspacios:
            if espacio[0] == codigoEspacio:
                tipoEspacioTexto = espacio[1]
                break
        self.tipoEspacioActualSeleccionado = tipoEspacioTexto
        
        for placa, datos in self.vehiculosActuales.items():
            if datos[3] == codigoEspacio:
                vehiculoEncontrado = datos
                placaEncontrada = placa
                break
                
        self.ventanaEmergente = tk.Toplevel(self.ventana)
        self.ventanaEmergente.title("Espacio " + str(codigoEspacio))
        self.ventanaEmergente.geometry("380x360")
        self.ventanaEmergente.config(bg="#f8f9fa")
        
        if vehiculoEncontrado:
            tk.Label(self.ventanaEmergente, text="OBSERVANDO ESPACIO", font=("Arial", 11, "bold"), fg="red", bg="#f8f9fa").pack(pady=10)
            formFrame = tk.Frame(self.ventanaEmergente, bg="#f8f9fa")
            formFrame.pack(padx=20, fill="x")
            tk.Label(formFrame, text="Placa:", bg="#f8f9fa", font=("Arial", 9, "bold")).grid(row=0, column=0, sticky="w", pady=4)
            entPlaca = tk.Entry(formFrame, width=20, font=("Arial", 10))
            entPlaca.insert(0, placaEncontrada)
            entPlaca.config(state="readonly")
            entPlaca.grid(row=0, column=1, padx=10, pady=4)
            
            tk.Label(formFrame, text="Marca:", bg="#f8f9fa", font=("Arial", 9, "bold")).grid(row=1, column=0, sticky="w", pady=4)
            entMarca = tk.Entry(formFrame, width=20, font=("Arial", 10))
            entMarca.insert(0, vehiculoEncontrado[0])
            entMarca.config(state="readonly")
            entMarca.grid(row=1, column=1, padx=10, pady=4)
            
            tk.Label(formFrame, text="Color:", bg="#f8f9fa", font=("Arial", 9, "bold")).grid(row=2, column=0, sticky="w", pady=4)
            entColor = tk.Entry(formFrame, width=20, font=("Arial", 10))
            entColor.insert(0, vehiculoEncontrado[1])
            entColor.config(state="readonly")
            entColor.grid(row=2, column=1, padx=10, pady=4)
            
            tk.Label(formFrame, text="Hora entrada:", bg="#f8f9fa", font=("Arial", 9, "bold")).grid(row=3, column=0, sticky="w", pady=4)
            entEntrada = tk.Entry(formFrame, width=20, font=("Arial", 10))
            entEntrada.insert(0, vehiculoEncontrado[4])
            entEntrada.config(state="readonly")
            entEntrada.grid(row=3, column=1, padx=10, pady=4)
            
            self.placaPorFacturar = placaEncontrada
            
            btnFrame = tk.Frame(self.ventanaEmergente, bg="#f8f9fa")
            btnFrame.pack(pady=15)
            
            tk.Button(btnFrame, text="Pagar", bg="#28a745", fg="white", font=("Arial", 10, "bold"), width=10, command=self.solicitarMetodoPago).pack(side=tk.LEFT, padx=10)
            tk.Button(btnFrame, text="Regresar", bg="#6c757d", fg="white", font=("Arial", 10), width=10, command=self.ventanaEmergente.destroy).pack(side=tk.LEFT, padx=10)
            
        else:
            tk.Label(self.ventanaEmergente, text="REGISTRO DE INGRESO (" + str(codigoEspacio) + ")", font=("Arial", 11, "bold"), fg="green", bg="#f8f9fa").pack(pady=10)
            
            formFrame = tk.Frame(self.ventanaEmergente, bg="#f8f9fa")
            formFrame.pack(padx=20, fill="x")
            
            # 1. Caja de Texto para Placa 
            tk.Label(formFrame, text="Placa:", bg="#f8f9fa", font=("Arial", 9, "bold")).grid(row=0, column=0, sticky="w", pady=5)
            self.entradaPlaca = tk.Entry(formFrame, font=("Arial", 10), width=22)
            self.entradaPlaca.grid(row=0, column=1, pady=5)
            
            # 2. Caja de Seleccion para Marcas 
            marcasDisponiblesApi = ["Toyota", "Hyundai", "Nissan", "Honda", "Suzuki", "Ford", "BYD"]
            tk.Label(formFrame, text="Marca:", bg="#f8f9fa", font=("Arial", 9, "bold")).grid(row=1, column=0, sticky="w", pady=5)
            self.comboMarca = ttk.Combobox(formFrame, values=marcasDisponiblesApi, state="readonly", width=20, font=("Arial", 10))
            self.comboMarca.set("Toyota")
            self.comboMarca.grid(row=1, column=1, pady=5)
            
            # 3. Caja de Seleccion para Colores 
            coloresPool = ["Gris", "Blanco", "Negro", "Rojo", "Azul", "Plata"]
            for p, v in self.vehiculosActuales.items():
                if v[1] not in coloresPool:
                    coloresPool.append(v[1])
            tk.Label(formFrame, text="Color:", bg="#f8f9fa", font=("Arial", 9, "bold")).grid(row=2, column=0, sticky="w", pady=5)
            self.comboColor = ttk.Combobox(formFrame, values=coloresPool, font=("Arial", 10), width=20, state="readonly")
            self.comboColor.set("Gris")
            self.comboColor.grid(row=2, column=1, pady=5)
            
            # 4. Hora entrada 
            horaReloj = datetime.now().strftime("%H:%M")
            tk.Label(formFrame, text="Hora Entrada:", bg="#f8f9fa", font=("Arial", 9, "bold")).grid(row=3, column=0, sticky="w", pady=5)
            self.entradaHoraEntrada = tk.Entry(formFrame, font=("Arial", 10), width=22)
            self.entradaHoraEntrada.insert(0, horaReloj)
            self.entradaHoraEntrada.config(state="readonly")
            self.entradaHoraEntrada.grid(row=3, column=1, pady=5)
            
            # Botones de estacionar regresar
            btnFrame = tk.Frame(self.ventanaEmergente, bg="#f8f9fa")
            btnFrame.pack(pady=20)
            tk.Button(btnFrame, text="Estacionar", bg="#007bff", fg="white", font=("Arial", 10, "bold"), width=12, command=self.guardarManual).pack(side=tk.LEFT, padx=10)
            tk.Button(btnFrame, text="Regresar", bg="#6c757d", fg="white", font=("Arial", 10), width=12, command=self.ventanaEmergente.destroy).pack(side=tk.LEFT, padx=10)

    def solicitarMetodoPago(self):
        ventanaPago = tk.Toplevel(self.ventanaEmergente)
        ventanaPago.title("Seleccionar Método de Pago")
        ventanaPago.geometry("300x180")
        
        tk.Label(ventanaPago, text="Seleccione el método de pago:", font=("Arial", 10, "bold")).pack(pady=15)
        
        comboPago = ttk.Combobox(ventanaPago, values=["Efectivo", "SINPE", "Tarjeta"], state="readonly")
        comboPago.set("Efectivo")
        comboPago.pack(pady=10)
        
        def procesar():
            metodo = comboPago.get()
            self.ejecutarLiberacionYFactura(metodo)
            ventanaPago.destroy()
            
        tk.Button(ventanaPago, text="Procesar Factura", bg="green", fg="white", command=procesar).pack(pady=15)

    def ejecutarLiberacionYFactura(self, metodoPago):
        datosCarro = self.vehiculosActuales.pop(self.placaPorFacturar)
        guardarEnDisco(self.vehiculosActuales)
        self.actualizarMapa()
        
        try:
            nombreFacturaEmitida = generarComprobantePago(self.placaPorFacturar, datosCarro, metodoPago)
            
            messagebox.showinfo(
                "Factura Generada", 
                "Cobro procesado por " + str(metodoPago) + ".\nEspacio " + str(datosCarro[3]) + " pasó a luz VERDE.\n\nDocumento emitido: " + nombreFacturaEmitida)
        except Exception as error:
            messagebox.showerror(
                "Error en Facturación", 
                "No se pudo compilar el archivo PDF con su respectivo código QR.\nDetalle: " + str(error))
        self.ventanaEmergente.destroy()

    def guardarManual(self):
        """Procesa el boton Estacionar, actualiza la estructura, guarda en disco y llama a generarVoucherEntrada"""
        p = self.entradaPlaca.get().strip().upper()
        m = self.comboMarca.get()
        c = self.comboColor.get() 
        horaIn = self.entradaHoraEntrada.get()
        if not p or not c:
            messagebox.showwarning("Atencion", "Por favor ingrese la placa y seleccione un color.")
            return
        patronLetrasNum = r"^[A-Z]{3}-\d{3}$"
        patronSoloNum = r"^\d{1,8}$"
        if not (re.match(patronLetrasNum, p) or re.match(patronSoloNum, p)):
            mensajeErrorPlaca = ("Formato de placa invalido o contiene caracteres especiales.\n\n" + "Formatos permitidos:\n" + " Tres letras, guion y tres numeros (Ej: ABC-123)\n" + " Solo numeros de hasta 8 digitos (Ej: 582491)" )
            messagebox.showwarning("Placa Incorrecta", mensajeErrorPlaca)
            return
        self.vehiculosActuales[p] = [m, c, "Manual", self.codigoEspacioActual, horaIn, "00:00", 1000, "Pendiente"]
        try:
            nombreVoucher = generarVoucherEntrada(p, m, c, self.tipoEspacioActualSeleccionado, self.codigoEspacioActual)
            guardarEnDisco(self.vehiculosActuales)
            self.actualizarMapa()
            mensajeExito = ("Vehiculo Estacionado!\n\n" + "El espacio " + self.codigoEspacioActual + " paso a color ROJO.\n" + "Se informa verbalmente que el costo es de C1000 por hora.\n\n" + "Voucher creado: " + nombreVoucher )
            messagebox.showinfo("Espacio Reservado", mensajeExito)
            self.ventanaEmergente.destroy()
        except Exception as error:
            messagebox.showerror("Error de Voucher", "No se pudo compilar el archivo del Voucher PDF.\nDetalle: " + str(error))

    def eventoFacturar(self):
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
        placaBuscar = self.entradaBusqueda.get().strip().upper()
        if placaBuscar in self.vehiculosActuales:
            datosCarro = self.vehiculosActuales[placaBuscar]
            self.placaPorFacturar = placaBuscar
            
            self.entradaBusqueda.pack_forget()
            self.btnBuscar.pack_forget()
            
            tk.Label(self.ventanaFactura, text="Vehículo: " + str(datosCarro[0]) + " (" + str(datosCarro[1]) + ")", font=("Arial", 10)).pack(pady=2)
            tk.Label(self.ventanaFactura, text="Espacio Liberado: " + str(datosCarro[3]), font=("Arial", 10)).pack(pady=2)
            tk.Label(self.ventanaFactura, text="Monto Total a Pagar: ₡" + str(datosCarro[6]), font=("Arial", 11, "bold"), fg="darkgreen").pack(pady=5)
            tk.Button(self.ventanaFactura, text="Confirmar Pago y Salida", bg="green", fg="white", command=self.solicitarMetodoPago).pack(pady=10)
        else:
            messagebox.showerror("ha ocurrido un problema", "La placa digitada no se encuentra activa en el parqueo.")

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
        ventanaStats.title("Modulo de Reportes y Cierre")
        ventanaStats.geometry("400x380")
        ventanaStats.config(bg="#f8f9fa")
        
        tk.Label(ventanaStats, text="PANEL DE REPORTES", font=("Arial", 12, "bold"), bg="#f8f9fa", fg="#333333").pack(pady=12)
        
        frameDatos = tk.LabelFrame(ventanaStats, text=" Estado Actual ", bg="#f8f9fa", padx=15, pady=10, font=("Arial", 9, "bold"))
        frameDatos.pack(fill="x", padx=20)
        
        tk.Label(frameDatos, text="Ingresos acumulados en parqueo: C" + str(totalDineroCaja), font=("Arial", 10, "bold"), fg="darkgreen", bg="#f8f9fa").pack(anchor="w", pady=4)
        tk.Label(frameDatos, text="Vehiculos por carga masiva activos: " + str(conteoMasivo), font=("Arial", 10), bg="#f8f9fa", fg="#555555").pack(anchor="w", pady=2)
        tk.Label(frameDatos, text="Vehiculos por ingreso manual activos: " + str(conteoManual), font=("Arial", 10), bg="#f8f9fa", fg="#555555").pack(anchor="w", pady=2)
        
        lblSeccionA = tk.Label(ventanaStats, text="a. Cierre Diario y Facturacion en Masa", font=("Arial", 10, "bold"), bg="#f8f9fa", fg="#0056b3")
        lblSeccionA.pack(anchor="w", padx=20, pady=(15, 5))
        
        btnCierre = tk.Button(
            ventanaStats, 
            text="Ejecutar Cierre Diario", 
            font=("Arial", 10, "bold"),
            bg="#dc3545", 
            fg="white", 
            width=25,
            pady=6,
            command=lambda: self.ejecutarCierreDiarioYFacturacionEnMasa(ventanaStats))
        btnCierre.pack(pady=5)
        btnVerParqueo = tk.Button(
            ventanaStats,
            text="Ver Parqueo",
            font=("Arial", 10),
            bg="#007bff",
            fg="white",
            width=25,
            pady=4,
            command=ventanaStats.destroy)
        btnVerParqueo.pack(pady=5)
        tk.Button(ventanaStats, text="Cerrar Panel", command=ventanaStats.destroy, width=12, font=("Arial", 9)).pack(pady=(15, 0))

    def ejecutarCierreDiarioYFacturacionEnMasa(self, ventanaEstadisticas):
        """
        Recorre todos los vehiculos estacionados, calcula sus montos, 
        guarda un reporte manual en formato CSV, genera 
        facturas individuales en masa y libera el parqueo completo.
        """
        if not self.vehiculosActuales:
            messagebox.showinfo("Cierre Diario", "No hay vehiculos activos en el parqueo para facturar.")
            return
        confirmar = messagebox.askyesno(
            "Confirmar Cierre Diario", 
            "¿Esta seguro de que desea realizar el cierre diario?\n" +
            "Esto exportara el archivo CSV y vaciara el parqueo.")
        if not confirmar:
            return
        placasActivas = list(self.vehiculosActuales.keys())
        totalVehiculosFacturados = len(placasActivas)
        montoTotalCierre = 0
        try:
            archivo = open("cierreDiario.csv", "w", encoding="utf-8")
            for placa in placasActivas:
                datos = self.vehiculosActuales[placa]
                marca = str(datos[0])
                color = str(datos[1])
                tipo = str(datos[2])
                espacio = str(datos[3])
                horaIn = str(datos[4])
                monto = str(datos[6])
                fila = placa + "," + marca + "," + color + "," + tipo + "," + espacio + "," + horaIn + "," + monto + "\n"
                archivo.write(fila)
            archivo.close()
        except Exception as errorArchivo:
            messagebox.showerror("No se pudo exportar el archivo CSV manual: " + str(errorArchivo))
            return
        for placa in placasActivas:
            datosCarro = self.vehiculosActuales[placa]
            montoTotalCierre = montoTotalCierre + datosCarro[6]
            try:
                generarComprobantePago(placa, datosCarro, "Efectivo (Cierre)")
                self.vehiculosActuales.pop(placa)
            except Exception as e:
                print("Error procesando factura en lote para " + str(placa) + ": " + str(e))
        guardarEnDisco(self.vehiculosActuales)
        self.actualizarMapa()
        ventanaEstadisticas.destroy()
        mensajeExito = ("CIERRE DIARIO\n\n" + "Archivo 'cierre_diario.csv' generado con exito.\n" +"Total vehiculos facturados en masa: " + str(totalVehiculosFacturados) + "\n" + "Total recaudado en el cierre: C" + str(montoTotalCierre) + "\n\n" + "Todos los espacios pasaron a estar disponibles.")
        messagebox.showinfo("Cierre Diario Exitoso", mensajeExito)

    def mostrarWindow(self):
        self.ventana.mainloop()
        
def arrancarPrograma():
    print("Sistema de Administración de Estacionamiento")
    infoPrueba = {"placa": "BCB-123", "marca": "Toyota"}
    estadiaPrueba = {"entrada": "08:00", "salida": "10:30"}
    pagoPrueba = {"monto": 2500, "estado": "Pagado"}
    unEstacionamiento = Estacionamiento("EST-001", infoPrueba, estadiaPrueba, pagoPrueba)
    unEstacionamiento.mostrarDatos()
    
    print("Abriendo interfaz")
    entornoInteractivo = VentanaParqueo()
    entornoInteractivo.mostrarWindow()
arrancarPrograma()