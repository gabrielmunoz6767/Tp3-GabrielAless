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
        self.ventana.geometry("950x550")
        self.ventana.config(bg="#f0f0f0")
        self.ventana.withdraw() 
        
        cantidadEspacios = simpledialog.askinteger(
            "Configuracion Inicial", 
            "¿Cuantos parqueos tiene su estacionamiento?")
        if cantidadEspacios is None or cantidadEspacios <= 0:
            cantidadEspacios = 75
            
        tieneElectricos = messagebox.askyesno(
            "Configuracion Electrica",
            "¿Su parqueo posee espacios exclusivos para vehiculos electricos?")

        self.ventana.deiconify()
        
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
            self.estructuraEspacios.append(("E" + str(numEspacio), "Eléctrico", "#00fc2a"))
            numEspacio = numEspacio + 1
        numRegular = 1
        for i in range(cantidadRegulares):
            self.estructuraEspacios.append(("R" + str(numRegular), "Regular", "#00fc2a"))
            numRegular = numRegular + 1
        numEspecial = 1
        for i in range(cantidadEspeciales):
            self.estructuraEspacios.append(("L" + str(numEspecial), "Especial", "#00fc2a"))
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
        frameMapaEstructura = tk.Frame(contenedorPadre, bg="#f0f0f0")
        frameMapaEstructura.pack(side=tk.LEFT, fill="both", expand=True, padx=5)
        
        # Le damos un tamaño inicial razonable al Canvas para que no intente crecer al infinito
        canvasScroll = tk.Canvas(frameMapaEstructura, bg="#f0f0f0", highlightthickness=0, width=750, height=500)
        canvasScroll.pack(side=tk.LEFT, fill="both", expand=True)
        
        barraDesplazamiento = tk.Scrollbar(frameMapaEstructura, orient=tk.VERTICAL, command=canvasScroll.yview)
        barraDesplazamiento.pack(side=tk.RIGHT, fill="y")
        
        canvasScroll.configure(yscrollcommand=barraDesplazamiento.set)
        
        frameCuadricula = tk.Frame(canvasScroll, bg="#f0f0f0")
        idVentanaCanvas = canvasScroll.create_window((0, 0), window=frameCuadricula, anchor="nw")
        
        # Este evento se dispara cuando la cuadrícula interna cambia de tamaño (agrega botones)
        def ajustarRegionScroll(evento):
            # Forzamos al Canvas a reconocer el área total exacta de los botones
            canvasScroll.configure(scrollregion=canvasScroll.bbox("all"))
        frameCuadricula.bind("<Configure>", ajustarRegionScroll)
        
        def ajustarAnchoVentana(evento):
            canvasScroll.itemconfig(idVentanaCanvas, width=evento.width)
        canvasScroll.bind("<Configure>", ajustarAnchoVentana)

        frameElectricos = tk.LabelFrame(frameCuadricula, text="Vehículos Eléctricos", font=("Arial", 10, "bold"), padx=10, pady=10, bg="#f0f0f0")
        frameElectricos.pack(fill="x", padx=10, pady=10)
        
        frameRegulares = tk.LabelFrame(frameCuadricula, text="Vehículos Regulares", font=("Arial", 10, "bold"), padx=10, pady=10, bg="#f0f0f0")
        frameRegulares.pack(fill="x", padx=10, pady=10)
        
        frameEspeciales = tk.LabelFrame(frameCuadricula, text="Vehículos Especiales", font=("Arial", 10, "bold"), padx=10, pady=10, bg="#f0f0f0")
        frameEspeciales.pack(fill="x", padx=10, pady=10)
        
        contadorElectricos = 0
        contadorRegulares = 0
        contadorEspeciales = 0
        limitePorFila = 10
        
        for codigo, tipo, colorLibre in self.estructuraEspacios:
            if tipo == "Eléctrico":
                contenedorSeccion = frameElectricos
                indiceActual = contadorElectricos
                contadorElectricos += 1
            elif tipo == "Regular":
                contenedorSeccion = frameRegulares
                indiceActual = contadorRegulares
                contadorRegulares += 1
            else:
                contenedorSeccion = frameEspeciales
                indiceActual = contadorEspeciales
                contadorEspeciales += 1
                
            filaInterna = indiceActual // limitePorFila
            columnaInterna = indiceActual % limitePorFila
                
            btn = tk.Button(
                contenedorSeccion, 
                text=codigo, 
                font=("Arial", 9, "bold"),
                width=6,     
                height=7,
                relief=tk.FLAT,
                bd=0,
                command=lambda cod=codigo: self.eventoClickEspacio(cod))
            
            btn.grid(row=filaInterna, column=columnaInterna, padx=4, pady=(0, 80), sticky="nsew")
            self.botonesMatriz[codigo] = btn

        anchoCalculado = self.ventana.winfo_width()
        altoCalculado = self.ventana.winfo_height()
        
        anchoMaximo = 1050
        altoMaximo = 650
        
        nuevoAncho = min(anchoCalculado, anchoMaximo)
        nuevoAlto = min(altoCalculado, altoMaximo)
        
        self.ventana.geometry(str(nuevoAncho) + "x" + str(nuevoAlto))
        
        def scrollConMouse(evento):
            '''
            funcionamiento: esto esta buenisimo, esto lo que hace es que basicamente puedo usar el mouse para que pueda scrollear
            '''
            if evento.num == 5 or evento.delta == -120:  # Hacia abajo
                canvasScroll.yview_scroll(1, "units")
            elif evento.num == 4 or evento.delta == 120:  # Hacia arriba
                canvasScroll.yview_scroll(-1, "units")
                
        self.ventana.bind_all("<MouseWheel>", scrollConMouse)

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
        btnAcercaDe = tk.Button(frameBotones, text="Acerca de", width=18, pady=5, command=self.eventoAcercaDe)
        btnAcercaDe.pack(pady=5)
        btnConfiguracion = tk.Button(frameBotones, text="Configuración", width=18, pady=5, command=self.eventoConfiguracion)
        btnConfiguracion.pack(pady=5)
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
                boton.config(bg="#ff0000", fg="white", activebackground="#cc0000", activeforeground="white")
                contadorOcupados += 1
            else:
                boton.config(bg="#00fc2a", fg="black", activebackground="#00cc22", activeforeground="black")
                
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
            tk.Label(self.ventanaEmergente, text="Espacio Ocupado", font=("Arial", 12, "bold"), fg="#333333", bg="#f8f9fa").pack(pady=(15, 5))
            formFrame = tk.Frame(self.ventanaEmergente, bg="#f8f9fa")
            formFrame.pack(padx=30, fill="x", pady=10)
            
            tk.Label(formFrame, text=f"# Espacio: {codigoEspacio}", font=("Arial", 11, "bold"), bg="#f8f9fa", anchor="w").pack(fill="x", pady=3)
            tk.Label(formFrame, text=f"Placa: {placaEncontrada}", font=("Arial", 11), bg="#f8f9fa", anchor="w").pack(fill="x", pady=3)
            tk.Label(formFrame, text=f"Marca: {vehiculoEncontrado[0]}", font=("Arial", 11), bg="#f8f9fa", anchor="w").pack(fill="x", pady=3)
            tk.Label(formFrame, text=f"Color: {vehiculoEncontrado[1]}", font=("Arial", 11), bg="#f8f9fa", anchor="w").pack(fill="x", pady=3)
            tk.Label(formFrame, text=f"Hora entrada: {vehiculoEncontrado[4]}", font=("Arial", 11), bg="#f8f9fa", anchor="w").pack(fill="x", pady=3)
            
            self.placaPorFacturar = placaEncontrada
            
            btnFrame = tk.Frame(self.ventanaEmergente, bg="#f8f9fa")
            btnFrame.pack(fill="both", expand=True, padx=30, pady=(15, 20))
            
            btnPagar = tk.Button(
                btnFrame, 
                text="Pagar", 
                bg="#28a745",  
                fg="white", 
                font=("Arial", 14, "bold"), 
                relief=tk.FLAT,
                command=self.solicitarMetodoPago)
            btnPagar.pack(fill="both", expand=True)
            
        else:
            tk.Label(self.ventanaEmergente, text="REGISTRO DE INGRESO (" + str(codigoEspacio) + ")", font=("Arial", 11, "bold"), fg="green", bg="#f8f9fa").pack(pady=10)
            
            formFrame = tk.Frame(self.ventanaEmergente, bg="#f8f9fa")
            formFrame.pack(padx=20, fill="x")
            
            tk.Label(formFrame, text="Placa:", bg="#f8f9fa", font=("Arial", 9, "bold")).grid(row=0, column=0, sticky="w", pady=5)
            self.entradaPlaca = tk.Entry(formFrame, font=("Arial", 10), width=22)
            self.entradaPlaca.grid(row=0, column=1, pady=5)
            
            marcasDisponiblesApi = ["Toyota", "Hyundai", "Nissan", "Honda", "Suzuki", "Ford", "BYD"]
            tk.Label(formFrame, text="Marca:", bg="#f8f9fa", font=("Arial", 9, "bold")).grid(row=1, column=0, sticky="w", pady=5)
            self.comboMarca = ttk.Combobox(formFrame, values=marcasDisponiblesApi, state="readonly", width=20, font=("Arial", 10))
            self.comboMarca.set("Toyota")
            self.comboMarca.grid(row=1, column=1, pady=5)
            
            coloresPool = ["Gris", "Blanco", "Negro", "Rojo", "Azul", "Plata"]
            for p, v in self.vehiculosActuales.items():
                if v[1] not in coloresPool:
                    coloresPool.append(v[1])
            tk.Label(formFrame, text="Color:", bg="#f8f9fa", font=("Arial", 9, "bold")).grid(row=2, column=0, sticky="w", pady=5)
            self.comboColor = ttk.Combobox(formFrame, values=coloresPool, font=("Arial", 10), width=20, state="readonly")
            self.comboColor.set("Gris")
            self.comboColor.grid(row=2, column=1, pady=5)
            
            horaReloj = datetime.now().strftime("%H:%M")
            tk.Label(formFrame, text="Hora Entrada:", bg="#f8f9fa", font=("Arial", 9, "bold")).grid(row=3, column=0, sticky="w", pady=5)
            self.entradaHoraEntrada = tk.Entry(formFrame, font=("Arial", 10), width=22)
            self.entradaHoraEntrada.insert(0, horaReloj)
            self.entradaHoraEntrada.config(state="readonly")
            self.entradaHoraEntrada.grid(row=3, column=1, pady=5)
            
            btnFrame = tk.Frame(self.ventanaEmergente, bg="#f8f9fa")
            btnFrame.pack(pady=20)
            tk.Button(btnFrame, text="Estacionar", bg="#007bff", fg="white", font=("Arial", 10, "bold"), width=12, command=self.guardarManual).pack(side=tk.LEFT, padx=10)
            tk.Button(btnFrame, text="Regresar", bg="#6c757d", fg="white", font=("Arial", 10), width=12, command=self.ventanaEmergente.destroy).pack(side=tk.LEFT, padx=10)

    def solicitarMetodoPago(self):
        ventanaPadre = self.ventanaFactura if (self.ventanaFactura and self.ventanaFactura.winfo_exists()) else self.ventanaEmergente
        ventanaPago = tk.Toplevel(ventanaPadre)
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
        
        if self.ventanaFactura and self.ventanaFactura.winfo_exists(): # winfo_exist lo que hace genuinamente es que retornara true si la ventana de factura existe
            self.ventanaFactura.destroy()
        if self.ventanaEmergente and self.ventanaEmergente.winfo_exists():
            self.ventanaEmergente.destroy()

    def guardarManual(self):
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
        if not self.vehiculosActuales:
            messagebox.showinfo("Facturación", "No hay vehículos activos en el parqueo para facturar.")
            return
        self.ventanaFactura = tk.Toplevel(self.ventana)
        self.ventanaFactura.title("Facturación de Vehículo")
        self.ventanaFactura.geometry("350x220")
        self.ventanaFactura.config(bg="#f0f0f0")
        
        tk.Label(self.ventanaFactura, text="--- SALIDA DE VEHÍCULO ---", font=("Arial", 11, "bold"), bg="#f0f0f0").pack(pady=10)
        tk.Label(self.ventanaFactura, text="Seleccione la Placa del vehículo:", bg="#f0f0f0").pack(anchor="w", padx=30)
        
        placasActivas = sorted(list(self.vehiculosActuales.keys()))
        
        self.entradaBusqueda = ttk.Combobox(self.ventanaFactura, values=placasActivas, state="readonly", font=("Arial", 11))
        self.entradaBusqueda.pack(fill="x", padx=30, pady=5)
        self.entradaBusqueda.set(placasActivas[0]) 
        
        self.btnBuscar = tk.Button(self.ventanaFactura, text="Cargar Datos y Facturar", command=self.buscarYProcesar)
        self.btnBuscar.pack(pady=15)

    def buscarYProcesar(self):
        placaBuscar = self.entradaBusqueda.get()
        if not placaBuscar:
            messagebox.showwarning("Atención", "Por favor, seleccione una placa de la lista.")
            return
            
        if placaBuscar in self.vehiculosActuales:
            datosCarro = self.vehiculosActuales[placaBuscar]
            self.placaPorFacturar = placaBuscar
            
            confirmar = messagebox.askyesno(
                "Confirmar Selección", 
                "¿Está seguro de que desea procesar la salida del vehículo con placa " + placaBuscar + "?")
            if not confirmar:
                return 
                
            self.entradaBusqueda.pack_forget()
            self.btnBuscar.pack_forget()
            
            tk.Label(self.ventanaFactura, text="Vehículo: " + str(datosCarro[0]) + " (" + str(datosCarro[1]) + ")", font=("Arial", 10), bg="#f0f0f0").pack(pady=2)
            tk.Label(self.ventanaFactura, text="Espacio Liberado: " + str(datosCarro[3]), font=("Arial", 10), bg="#f0f0f0").pack(pady=2)
            tk.Label(self.ventanaFactura, text="Monto Total a Pagar: ₡" + str(datosCarro[6]), font=("Arial", 11, "bold"), fg="darkgreen", bg="#f0f0f0").pack(pady=5)
            
            tk.Button(self.ventanaFactura, text="Confirmar Pago y Salida", bg="green", fg="white", font=("Arial", 10, "bold"), command=self.solicitarMetodoPago).pack(pady=10)
        else:
            messagebox.showerror("Ha ocurrido un problema", "La placa seleccionada ya no se encuentra activa.")

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
        lblSeccionB = tk.Label(ventanaStats, text="b. Cierre por Tipo de Pago (XML)", font=("Arial", 10, "bold"), bg="#f8f9fa", fg="#0056b3")
        lblSeccionB.pack(anchor="w", padx=20, pady=(10, 5))
        
        btnXml = tk.Button(
            ventanaStats,
            text="Exportar XML por Tipo de Pago",
            font=("Arial", 10, "bold"),
            bg="#6f42c1",
            fg="white",
            width=25,
            pady=6,
            command=self.generarXmlPorTipoPago)
        btnXml.pack(pady=5)
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

    def eventoAcercaDe(self):
        ventanaInfo = tk.Toplevel(self.ventana)
        ventanaInfo.title("Acerca de")
        ventanaInfo.geometry("350x250")
        ventanaInfo.config(bg="#f0f0f0")
        tk.Label(ventanaInfo, text="Sistema de Parqueo", font=("Arial", 14, "bold"), bg="#f0f0f0", fg="#333333").pack(pady=15)
        tk.Label(ventanaInfo, text="Desarrollado por:", font=("Arial", 10), bg="#f0f0f0").pack()
        tk.Label(ventanaInfo, text="Gabriel, Alessandro Arias", font=("Arial", 11, "bold"), bg="#f0f0f0", fg="#007bff").pack(pady=5)
        tk.Label(ventanaInfo, text="Taller de Programación - I Semestre 2026", font=("Arial", 9), bg="#f0f0f0", fg="#666666").pack(pady=5)
        tk.Label(ventanaInfo, text="Escuela de Ingeniería en Computación", font=("Arial", 9), bg="#f0f0f0", fg="#666666").pack()
        tk.Label(ventanaInfo, text="TEC - Costa Rica", font=("Arial", 9), bg="#f0f0f0", fg="#666666").pack(pady=5)
        tk.Button(ventanaInfo, text="Regresar", bg="#6c757d", fg="white", width=12, command=ventanaInfo.destroy).pack(pady=15)

    def eventoConfiguracion(self):
        ventanaConfig = tk.Toplevel(self.ventana)
        ventanaConfig.title("Configuración del Parqueo")
        ventanaConfig.geometry("380x320")
        ventanaConfig.config(bg="#f0f0f0")
        
        tk.Label(ventanaConfig, text="CONFIGURACIÓN", font=("Arial", 12, "bold"), bg="#f0f0f0", fg="#333333").grid(row=0, column=0, columnspan=2, pady=12)
        
        tk.Label(ventanaConfig, text="Tamaño del estacionamiento:", bg="#f0f0f0", font=("Arial", 9, "bold")).grid(row=1, column=0, sticky="w", padx=20, pady=8)
        self.entTamano = tk.Entry(ventanaConfig, font=("Arial", 10), width=15)
        self.entTamano.insert(0, str(len(self.estructuraEspacios)))
        self.entTamano.grid(row=1, column=1, padx=10, pady=8)
        
        tk.Label(ventanaConfig, text="Tiempo de gracia (minutos):", bg="#f0f0f0", font=("Arial", 9, "bold")).grid(row=2, column=0, sticky="w", padx=20, pady=8)
        self.entGracia = tk.Entry(ventanaConfig, font=("Arial", 10), width=15)
        self.entGracia.insert(0, "5")
        self.entGracia.grid(row=2, column=1, padx=10, pady=8)
        
        tk.Label(ventanaConfig, text="Monto por hora (colones):", bg="#f0f0f0", font=("Arial", 9, "bold")).grid(row=3, column=0, sticky="w", padx=20, pady=8)
        self.entMonto = tk.Entry(ventanaConfig, font=("Arial", 10), width=15)
        self.entMonto.insert(0, "1000")
        self.entMonto.grid(row=3, column=1, padx=10, pady=8)
        
        self.ventanaConfig = ventanaConfig
        tk.Button(ventanaConfig, text="Guardar", bg="#28a745", fg="white", font=("Arial", 10, "bold"), width=12, command=self.guardarConfiguracion).grid(row=4, column=0, columnspan=2, pady=20)

    def guardarConfiguracion(self):
        confirmar = messagebox.askyesno("Confirmar", "¿Desea guardar los cambios de configuración?")
        if confirmar:
            messagebox.showinfo("Configuración", "Configuración guardada correctamente.")
            self.ventanaConfig.destroy()

    def generarXmlPorTipoPago(self):
        efectivo = ""
        sinpe = ""
        tarjeta = ""
        for placa in self.vehiculosActuales:
            datos = self.vehiculosActuales[placa]
            linea = ("<vehiculo>"
                + "<placa>" + placa + "</placa>"
                + "<marca>" + str(datos[0]) + "</marca>"
                + "<color>" + str(datos[1]) + "</color>"
                + "<tipo>" + str(datos[2]) + "</tipo>"
                + "<espacio>" + str(datos[3]) + "</espacio>"
                + "<horaEntrada>" + str(datos[4]) + "</horaEntrada>"
                + "<horaSalida>" + str(datos[5]) + "</horaSalida>"
                + "<monto>" + str(datos[6]) + "</monto>"
                + "<tipoPago>" + str(datos[7]) + "</tipoPago>"
                + "</vehiculo>\n")
            if str(datos[7]).lower() == "sinpe":
                sinpe = sinpe + linea
            elif str(datos[7]).lower() == "tarjeta":
                tarjeta = tarjeta + linea
            else:
                efectivo = efectivo + linea
        contenidoXml = ("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
            + "<cierrePorTipoPago>\n"
            + "  <efectivo>\n" + efectivo + "  </efectivo>\n"
            + "  <sinpe>\n" + sinpe + "  </sinpe>\n"
            + "  <tarjeta>\n" + tarjeta + "  </tarjeta>\n"
            + "</cierrePorTipoPago>")
        archivo = open("cierrePorTipoPago.xml", "w", encoding="utf-8")
        archivo.write(contenidoXml)
        archivo.close()
        messagebox.showinfo("XML Generado", "Archivo 'cierrePorTipoPago.xml' guardado correctamente.")
        
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