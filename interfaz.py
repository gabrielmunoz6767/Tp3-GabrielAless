import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog
from tkinter import ttk
import random
import re
from datetime import datetime  
from conexionapi import obtenerVehiculosApi
from baseDatos import guardarEnDisco, cargarMemoria
from estacionamiento import Estacionamiento
from factura import generarComprobantePago, generarVoucherEntrada, generarReporteCierreDiario
import math

class Vehiculo:
    def __init__(self, placa, marca, color, tipoIngreso, codigoEspacio, horaEntrada, horaSalida="00:00", monto=0, tipoPago="Pendiente"):
        self.placa = placa
        self.marca = marca
        self.color = color
        self.tipoIngreso = tipoIngreso
        self.codigoEspacio = codigoEspacio
        self.horaEntrada = horaEntrada
        self.horaSalida = horaSalida
        self.monto = monto
        self.tipoPago = tipoPago

class VentanaParqueo:
    def __init__(self):
        """
        Funcionalidad:
        Construye la ventana principal del sistema, solicita la configuracion
        inicial del parqueo y arma la estructura de espacios disponibles.
        """
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
        
        datosCargados = cargarMemoria()
        self.vehiculosActuales = [] 
        if isinstance(datosCargados, list):
            for v in datosCargados:
                self.vehiculosActuales.append(
                    Vehiculo(v[0], v[1], v[2], v[3], v[4], v[5], v[6], v[7], v[8])) # v es una lista: [placa, marca, color, tipoIngreso, codigoEspacio, horaEntrada, horaSalida, monto, tipoPago]

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
        self.tiempoGracia = 15  
        self.montoPorHora = 1000 
        
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
        self.frameInferior = tk.Frame(self.ventana, bg="#f0f0f0")
        self.frameInferior.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.crearMapaParqueo(self.frameInferior)
        self.crearMenuBotones(self.frameInferior)
        self.actualizarMapa()

    def guardarEnMemoria(self):
        matrizMemoria = []
        for vehiculo in self.vehiculosActuales:
            datosCarro = [
                vehiculo.placa,
                vehiculo.marca,
                vehiculo.color,
                vehiculo.tipoIngreso,
                vehiculo.codigoEspacio,
                vehiculo.horaEntrada,
                vehiculo.horaSalida,
                vehiculo.monto,
                vehiculo.tipoPago
            ]
            matrizMemoria.append(datosCarro)
        guardarEnDisco(matrizMemoria)

    def crearContadoresSuperiores(self):
        frameContadores = tk.Frame(self.ventana, bg="#f0f0f0", pady=10)
        frameContadores.pack(fill="x")
        
        totalInicial = str(len(self.estructuraEspacios))
        self.lblDisponibles = tk.Label(frameContadores, text="Disponibles: " + totalInicial, font=("Arial", 11, "bold"), fg="green", bg="#f0f0f0")
        self.lblDisponibles.pack(side=tk.LEFT, padx=40)
        
        self.lblOcupados = tk.Label(frameContadores, text="Ocupados: 0", font=("Arial", 11, "bold"), fg="red", bg="#f0f0f0")
        self.lblOcupados.pack(side=tk.LEFT, padx=40)

    def crearMapaParqueo(self, contenido):
        frameMapaEstructura = tk.Frame(contenido, bg="#f0f0f0")
        frameMapaEstructura.pack(side=tk.LEFT, fill="both", expand=True, padx=5)
        
        canvasScroll = tk.Canvas(frameMapaEstructura, bg="#f0f0f0", highlightthickness=0, width=750, height=500)
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
        nuevoAncho = min(anchoCalculado, 1050)
        nuevoAlto = min(altoCalculado, 650)
        self.ventana.geometry(str(nuevoAncho) + "x" + str(nuevoAlto))
        
        def scrollConMouse(evento):
            """
            funcionalidad: permite el scroll vertical con la rueda del mouse
            basicamente ni entradas ni salidas
            """
            if evento.num == 5 or evento.delta == -120:  
                canvasScroll.yview_scroll(1, "units")
            elif evento.num == 4 or evento.delta == 120:  
                canvasScroll.yview_scroll(-1, "units")
        self.ventana.bind_all("<MouseWheel>", scrollConMouse)

    def crearMenuBotones(self, contenido):
        ''' 
        funcionalidad: crea el menu lateral con botones de accion y la seccion de instalaciones fisicas
        '''
        frameLateral = tk.Frame(contenido, bg="#f0f0f0")
        frameLateral.pack(side=tk.RIGHT, fill="y", padx=5)
        
        frameBotones = tk.LabelFrame(frameLateral, text="Menú Principal", padx=10, pady=10, bg="#f0f0f0", width=200)
        frameBotones.pack(side=tk.TOP, fill="x", pady=5)
        
        btnObtener = tk.Button(frameBotones, text="Obtener vehículos", width=18, pady=5, command=self.cargaDeCarros)
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

    def cargaDeCarros(self):
        '''
        Funcionalidad:
        Carga los vehículos desde la API y los muestra en la interfaz.
        Entrada:
        - Ninguna
        Salida:
        - Ninguna
        '''
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
            self.vehiculosActuales = [] 
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
                monto = random.randint(2, 7) * 500
                
                nuevoVehiculo = Vehiculo(placaInyectar, marcaInyectar, colorInyectar, "Masiva", codigoEspacioAsignado, horaEntrada, horaSalida, monto, "Efectivo")
                self.vehiculosActuales.append(nuevoVehiculo)
            self.guardarEnMemoria()
            self.actualizarMapa()
            mensajeAlerta = "Carga masiva completada exitosamente.\n" + "Espacios Regulares Totales: " + str(self.cantidadRegularesImprimir) + "\n" + "Vehículos Inyectados (Tope Real): " + str(limiteInyeccion)
            messagebox.showinfo("Carga Masiva", mensajeAlerta)
        except Exception as error:
            messagebox.showerror("No se pudo formatear la información de la API \nDetalle: " + str(error))

    def actualizarMapa(self):
        """
        Funcionalidad:
        Recorre todos los espacios del parqueo y actualiza el color de cada boton
        segun si esta ocupado o libre, junto con los contadores superiores.
        Entrada:
        - Ninguna
        Salida:
        - Ninguna
        """
        contadorOcupados = 0
        for infoEspacio in self.estructuraEspacios:
            codigo, tipo, colorLibre = infoEspacio
            boton = self.botonesMatriz[codigo]
            estaOcupado = False
            for vehiculo in self.vehiculosActuales:
                if vehiculo.codigoEspacio == codigo:
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
        """
        Funcionalidad:
        Abre la ventana de "Observar espacio", mostrando los datos del vehiculo
        si esta ocupado, o el formulario de ingreso si esta libre.
        Entrada:
        - codigoEspacio(str): codigo del espacio seleccionado
        Salida:
        - Ninguna
        """
        self.codigoEspacioActual = codigoEspacio
        vehiculoEncontrado = None
        tipoEspacioTexto = "Regular"
        for espacio in self.estructuraEspacios:
            if espacio[0] == codigoEspacio:
                tipoEspacioTexto = espacio[1]
                break
        self.tipoEspacioActualSeleccionado = tipoEspacioTexto
        
        for vehiculo in self.vehiculosActuales:
            if vehiculo.codigoEspacio == codigoEspacio:
                vehiculoEncontrado = vehiculo
                break
                
        self.ventanaEmergente = tk.Toplevel(self.ventana)
        self.ventanaEmergente.title("Espacio " + str(codigoEspacio))
        self.ventanaEmergente.geometry("380x360")
        self.ventanaEmergente.config(bg="#f8f9fa")
        
        if vehiculoEncontrado:
            tk.Label(self.ventanaEmergente, text="Espacio Ocupado", font=("Arial", 12, "bold"), fg="#333333", bg="#f8f9fa").pack(pady=(15, 5))
            formFrame = tk.Frame(self.ventanaEmergente, bg="#f8f9fa")
            formFrame.pack(padx=30, fill="x", pady=10)
            
            tk.Label(formFrame, text="# Espacio: " + str(codigoEspacio), font=("Arial", 11, "bold"), bg="#f8f9fa", anchor="w").pack(fill="x", pady=3)
            tk.Label(formFrame, text="Placa: " + str(vehiculoEncontrado.placa), font=("Arial", 11), bg="#f8f9fa", anchor="w").pack(fill="x", pady=3)
            tk.Label(formFrame, text="Marca: " + str(vehiculoEncontrado.marca), font=("Arial", 11), bg="#f8f9fa", anchor="w").pack(fill="x", pady=3)
            tk.Label(formFrame, text="Color: " + str(vehiculoEncontrado.color), font=("Arial", 11), bg="#f8f9fa", anchor="w").pack(fill="x", pady=3)
            tk.Label(formFrame, text="Hora entrada: " + str(vehiculoEncontrado.horaEntrada), font=("Arial", 11), bg="#f8f9fa", anchor="w").pack(fill="x", pady=3)
            
            self.placaPorFacturar = vehiculoEncontrado.placa
            
            btnFrame = tk.Frame(self.ventanaEmergente, bg="#f8f9fa")
            btnFrame.pack(fill="x", padx=30, pady=(15, 20))
            
            botonPagar = tk.Button(
                btnFrame, text="Pagar", bg="#28a745", fg="white", font=("Arial", 12, "bold"), relief=tk.FLAT, command=self.solicitarMetodoPago)
            botonPagar.pack(side=tk.LEFT, fill="both", expand=True, padx=(0, 5))
            
            btnRegresar = tk.Button(
                btnFrame, text="Regresar", bg="#6c757d", fg="white", font=("Arial", 12, "bold"), relief=tk.FLAT, command=self.ventanaEmergente.destroy)
            btnRegresar.pack(side=tk.LEFT, fill="both", expand=True, padx=(5, 0))
            
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
            for vehiculo in self.vehiculosActuales:
                if vehiculo.color not in coloresPool:
                    coloresPool.append(vehiculo.color)
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
        """
        Funcionalidad:
        Crea una ventana emergente para que el usuario elija el método de pago
        con el que desea cancelar el monto del parqueo.
        Entrada:
        - Ninguna
        Salida:
        - Ninguna
        """
        if self.ventanaFactura and self.ventanaFactura.winfo_exists():
            ventanaPadre = self.ventanaFactura
        else:
            ventanaPadre = self.ventanaEmergente

        ventanaPago = tk.Toplevel(ventanaPadre)
        ventanaPago.title("Seleccionar Método de Pago")
        ventanaPago.geometry("300x180")

        tk.Label(ventanaPago, text="Seleccione el método de pago:", font=("Arial", 10, "bold")).pack(pady=15)
        
        comboPago = ttk.Combobox(ventanaPago, values=["Efectivo", "SINPE", "Tarjeta"], state="readonly")
        comboPago.set("Efectivo")
        comboPago.pack(pady=10)
        
        tk.Button(
            ventanaPago, text="Procesar Factura", bg="green", fg="white", command=lambda: self.procesarPago(comboPago, ventanaPago)).pack(pady=15)
    
    def procesarPago(self, comboPago, ventanaPago):
        """
        Funcionalidad:
        Obtiene la opción seleccionada en el combobox, ejecuta la facturación
        y destruye la ventana de selección de pago.
        Entrada:
        - comboPago (Combobox): Componente gráfico que contiene el método elegido.
        - ventanaPago (Toplevel): Ventana de pago que se debe cerrar.
        Salida:
        - Ninguna
        """
        metodo = comboPago.get()
        self.ejecutarLiberacionYFactura(metodo)
        ventanaPago.destroy()

    def ejecutarLiberacionYFactura(self, metodoPago):
        """
        Funcionalidad:
        Ejecuta la liberación del vehículo y genera la factura correspondiente.
        Entrada:
        - metodoPago (str): Método de pago seleccionado.
        Salida:
        - Ninguna
        """
        carroObjeto = None
        for vehiculo in self.vehiculosActuales:
            if vehiculo.placa == self.placaPorFacturar:
                carroObjeto = vehiculo
                break
        if carroObjeto:
            carroObjeto.monto = self.calcularMontoCobro(carroObjeto)
            carroObjeto.horaSalida = datetime.now().strftime("%H:%M")
            carroObjeto.tipoPago = metodoPago
            EsctructuraDeLosDatos = [carroObjeto.marca, carroObjeto.color, carroObjeto.tipoIngreso, carroObjeto.codigoEspacio, carroObjeto.horaEntrada, carroObjeto.horaSalida, carroObjeto.monto, carroObjeto.tipoPago]
            self.vehiculosActuales.remove(carroObjeto)
            self.guardarEnMemoria()
            self.actualizarMapa()
            try:
                nombreFacturaEmitida = generarComprobantePago(self.placaPorFacturar, EsctructuraDeLosDatos, metodoPago)
                messagebox.showinfo(
                    "Factura Generada",
                    "Cobro procesado por " + str(metodoPago) + " (C" + str(carroObjeto.monto) + ").\nEspacio " + str(carroObjeto.codigoEspacio) + " pasó a luz VERDE.\n\nDocumento emitido: " + nombreFacturaEmitida)
            except Exception as error:
                messagebox.showerror(
                    "Error en Facturación",
                    "No se pudo compilar el archivo PDF con su respectivo código QR.\nDetalle: " + str(error))
        if self.ventanaFactura and self.ventanaFactura.winfo_exists():
            self.ventanaFactura.destroy()
        if self.ventanaEmergente and self.ventanaEmergente.winfo_exists():
            self.ventanaEmergente.destroy()       

    def calcularMontoCobro(self, carroObjeto):
        ahora = datetime.now()
        try:
            horaDeEntrada = datetime.strptime(carroObjeto.horaEntrada, "%H:%M")
            entradaCompleta = ahora.replace(hour=horaDeEntrada.hour, minute=horaDeEntrada.minute, second=0, microsecond=0)
        except ValueError:
            entradaCompleta = ahora
        minutosTranscurridos = (ahora - entradaCompleta).total_seconds() / 60
        if minutosTranscurridos < 0:
            minutosTranscurridos = 0
        if minutosTranscurridos <= self.tiempoGracia:
            return 0
        horasCobrables = math.ceil(minutosTranscurridos / 60)
        return int(horasCobrables * self.montoPorHora)
    
    def guardarManual(self):
        """
        Funcionalidad:
        Valida y registra el ingreso manual de un vehiculo en el espacio
        seleccionado, generando su voucher de entrada en PDF.
        Entrada:
        - Ninguna
        Salida:
        - Ninguna
        """
        placaIngresada = self.entradaPlaca.get().strip().upper()
        marcaSeleccionada = self.comboMarca.get()
        colorSeleccionado = self.comboColor.get() 
        horaEntrada = self.entradaHoraEntrada.get()
        if placaIngresada == "":
            messagebox.showwarning("Error", "El campo de la placa no puede quedar vacío.")
            return
        for vehiculo in self.vehiculosActuales:
            if vehiculo.placa == placaIngresada:
                messagebox.showwarning(
                    "Placa Duplicada",
                    "La placa " + placaIngresada + " ya está registrada en el espacio " + str(vehiculo.codigoEspacio) + ".\nNo se puede ingresar el mismo auto dos veces.")
                return
        patronLetrasNum = r"^[A-Z]{3}-\d{3}$"
        patronSoloNum = r"^\d{1,8}$"
        if not (re.match(patronLetrasNum, placaIngresada) or re.match(patronSoloNum, placaIngresada)):
            mensajeErrorPlaca = ("El formato de la placa es incorrecto.\n\n" + 
                                 "Formatos válidos:\n" + 
                                 "- 3 letras, guion y 3 números (Ej: ABC-123)\n" + 
                                 "- Solo números de máximo 8 dígitos (Ej: 582491)")
            messagebox.showwarning("Placa Inválida", mensajeErrorPlaca)
            return
        nuevoManual = Vehiculo(placaIngresada, marcaSeleccionada, colorSeleccionado, "Manual", self.codigoEspacioActual, horaEntrada, "00:00", self.montoPorHora, "Pendiente")
        self.vehiculosActuales.append(nuevoManual)
        try:
            nombreVoucher = generarVoucherEntrada(
                placaIngresada, marcaSeleccionada, colorSeleccionado, self.tipoEspacioActualSeleccionado, self.codigoEspacioActual)
            self.guardarEnMemoria()
            self.actualizarMapa()
            mensajeExito = ("Vehículo registrado\n\n" + 
                            "El espacio " + self.codigoEspacioActual + " cambió a ROJO.\n" + 
                            "Costo por hora: ₡" + str(self.montoPorHora) + ".\n\n" + 
                            "Archivo generado: " + nombreVoucher)
            messagebox.showinfo("Espacio Reservado", mensajeExito)
            self.ventanaEmergente.destroy()
        except Exception as error:
            messagebox.showerror("Error", "No se pudo crear el archivo PDF del Voucher.\nDetalle: " + str(error))

    def eventoFacturar(self):
        """
        Funcionalidad:
        Muestra la interfaz gráfica para gestionar la salida de un automóvil. 
        Verifica si existen vehículos en el estacionamiento, genera una ventana 
        emergente con un menú desplegable ordenado alfabéticamente con las placas 
        activas y habilita la opción de procesar el cobro.
        Entrada:
        - Ninguna
        Salida:
        - Ninguna
        """
        if not self.vehiculosActuales:
            messagebox.showinfo("Facturación", "No hay vehículos activos en el parqueo para facturar.")
            return
        self.ventanaFactura = tk.Toplevel(self.ventana)
        self.ventanaFactura.title("Facturación de Vehículo")
        self.ventanaFactura.geometry("350x220")
        self.ventanaFactura.config(bg="#f0f0f0")
        
        tk.Label(self.ventanaFactura, text="SALIDA DE VEHÍCULO", font=("Arial", 11, "bold"), bg="#f0f0f0").pack(pady=10)
        tk.Label(self.ventanaFactura, text="Seleccione la Placa del vehículo:", bg="#f0f0f0").pack(anchor="w", padx=30)
        
        placasActivas = sorted([vehiculo.placa for vehiculo in self.vehiculosActuales])
        
        self.entradaBusqueda = ttk.Combobox(self.ventanaFactura, values=placasActivas, state="readonly", font=("Arial", 11))
        self.entradaBusqueda.pack(fill="x", padx=30, pady=5)
        self.entradaBusqueda.set(placasActivas[0]) 
        
        self.btnBuscar = tk.Button(self.ventanaFactura, text="Cargar Datos y Facturar", command=self.buscarYProcesar)
        self.btnBuscar.pack(pady=15)

    def buscarYProcesar(self):
        """
        Funcionalidad:
        Busca los datos de la placa seleccionada en el menú de facturación. Si el
        vehículo está activo, solicita confirmación al usuario, oculta los componentes
        de búsqueda de la ventana y despliega en pantalla el desglose del cobro.
        Entrada:
        - Ninguna
        Salida:
        - Ninguna
        """
        placaBuscar = self.entradaBusqueda.get()
        if not placaBuscar:
            messagebox.showwarning("Error", "seleccione una placa de la lista.")
            return
        carroObjeto = None
        for vehiculo in self.vehiculosActuales:
            if vehiculo.placa == placaBuscar:
                carroObjeto = vehiculo
                break
        if carroObjeto:
            self.placaPorFacturar = placaBuscar
            confirmar = messagebox.askyesno(
                "Confirmar Selección", 
                "¿Está seguro de que desea procesar la salida del vehículo con placa " + placaBuscar + "?")
            if not confirmar:
                return 
            self.entradaBusqueda.pack_forget() 
            self.btnBuscar.pack_forget()
            
            tk.Label(self.ventanaFactura, text="Vehículo: " + str(carroObjeto.marca) + " (" + str(carroObjeto.color) + ")", font=("Arial", 10), bg="#f0f0f0").pack(pady=2)
            tk.Label(self.ventanaFactura, text="Espacio Liberado: " + str(carroObjeto.codigoEspacio), font=("Arial", 10), bg="#f0f0f0").pack(pady=2)
            tk.Label(self.ventanaFactura, text="Monto Total a Pagar: ₡" + str(carroObjeto.monto), font=("Arial", 11, "bold"), fg="darkgreen", bg="#f0f0f0").pack(pady=5)
            
            tk.Button(self.ventanaFactura, text="Confirmar Pago y Salida", bg="green", fg="white", font=("Arial", 10, "bold"), command=self.solicitarMetodoPago).pack(pady=10)
        else:
            messagebox.showerror("Ha ocurrido un problema", "La placa seleccionada ya no se encuentra activa.")

    def eventoReportes(self):
        """
        Funcionalidad:
        Abre el panel de reportes con el resumen de ingresos actuales y los
        accesos a cierre diario y cierre por tipo de pago.
        Entrada:
        - Ninguna
        Salida:
        - Ninguna
        """
        totalDineroCaja = 0
        conteoMasivo = 0
        conteoManual = 0
        
        for vehiculo in self.vehiculosActuales:
            totalDineroCaja = totalDineroCaja + vehiculo.monto
            if vehiculo.tipoIngreso in ["Masiva", "Regular"]:
                conteoMasivo = conteoMasivo + 1
            elif vehiculo.tipoIngreso == "Manual":
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
            ventanaStats, text="Exportar XML por Tipo de Pago", font=("Arial", 10, "bold"), bg="#6f42c1", fg="white", width=25, pady=6, command=self.generarXmlPorTipoPago)
        btnXml.pack(pady=5)
        btnCierre = tk.Button(
            ventanaStats, text="Ejecutar Cierre Diario", font=("Arial", 10, "bold"), bg="#dc3545", fg="white", width=25, pady=6, command=lambda: self.ejecutarCierreDiarioYFacturacionEnMasa(ventanaStats))
        btnCierre.pack(pady=5)
        btnVerParqueo = tk.Button(
            ventanaStats, text="Ver Parqueo", font=("Arial", 10), bg="#007bff", fg="white", width=25, pady=4, command=ventanaStats.destroy)
        btnVerParqueo.pack(pady=5)
        tk.Button(ventanaStats, text="Cerrar Panel", command=ventanaStats.destroy, width=12, font=("Arial", 9)).pack(pady=(15, 0))

    def ejecutarCierreDiarioYFacturacionEnMasa(self, ventanaEstadisticas):
        """
        Funcionalidad:
        Factura automaticamente todos los vehiculos pendientes, genera el CSV
        manual, el reporte oficial en PDF y libera todos los espacios del parqueo.
        Entrada:
        - ventanaEstadisticas(Toplevel): ventana de reportes que se cierra al finalizar
        Salida:
        - Ninguna
        """
        if not self.vehiculosActuales:
            messagebox.showinfo("Cierre Diario", "No hay vehiculos activos en el parqueo para facturar.")
            return
        confirmar = messagebox.askyesno(
            "Confirmar Cierre Diario",
            "¿Esta seguro de que desea realizar el cierre diario?\n" +
            "Esto exportara el archivo CSV, el reporte PDF y vaciara el parqueo.")
        if not confirmar:
            return
            
        cantCarros = len(self.vehiculosActuales)
        totalCierre = 0
        datosReporte = []
        pagosDicc = {}
        try:
            archivo = open("cierreDiario.csv", "w", encoding="utf-8")
            for vehiculo in self.vehiculosActuales:
                fila = vehiculo.placa + "," + vehiculo.marca + "," + vehiculo.color + "," + vehiculo.tipoIngreso + "," + vehiculo.codigoEspacio + "," + vehiculo.horaEntrada + "," + str(vehiculo.monto) + "\n"
                archivo.write(fila)
            archivo.close()
        except Exception as errorArchivo:
            messagebox.showerror("Error", "No se pudo exportar el archivo CSV manual: " + str(errorArchivo))
            return
        listaCierreCopia = list(self.vehiculosActuales)
        for vehiculo in listaCierreCopia:
            tipoPago = "Efectivo (Cierre)"
            totalCierre = totalCierre + vehiculo.monto
            pagosDicc[tipoPago] = pagosDicc.get(tipoPago, 0) + vehiculo.monto
            datosReporte.append((vehiculo.codigoEspacio, vehiculo.placa, vehiculo.horaEntrada, datetime.now().strftime("%H:%M"), tipoPago, vehiculo.monto))
            try:
                carroTradicional = [vehiculo.marca, vehiculo.color, vehiculo.tipoIngreso, vehiculo.codigoEspacio, vehiculo.horaEntrada, vehiculo.horaSalida, vehiculo.monto, tipoPago]
                generarComprobantePago(vehiculo.placa, carroTradicional, tipoPago)
                self.vehiculosActuales.remove(vehiculo)
            except Exception as e:
                print("Error procesando factura en lote para " + str(vehiculo.placa) + ": " + str(e))
                
        nombreReporte = generarReporteCierreDiario(datosReporte, pagosDicc, totalCierre)
        self.guardarEnMemoria()
        self.actualizarMapa()
        ventanaEstadisticas.destroy()
        mensajeExito = ("CIERRE DIARIO\n\n" + "Archivo 'cierreDiario.csv' generado con exito.\n" + "Reporte oficial: " + nombreReporte + "\n" + "Total vehiculos facturados en masa: " + str(cantCarros) + "\n" + "Total recaudado en el cierre: C" + str(totalCierre) + "\n\n" + "Todos los espacios pasaron a estar disponibles.")
        messagebox.showinfo("Cierre Diario Exitoso", mensajeExito)

    def eventoAcercaDe(self):
        """
        Funcionalidad:
        Despliega una ventana emergente de información con los créditos del sistema,
        especificando el nombre del software, los autores del proyecto, el curso,
        el ciclo lectivo actual y la institución académica correspondiente.
        Entrada:
        - Ninguna
        Salida:
        - Ninguna
        """
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
        """
        Funcionalidad:
        Despliega la interfaz gráfica de la ventana secundaria de configuración. 
        Inicializa el contenedor visual, los títulos correspondientes y el marco 
        donde se organizan las opciones para modificar el tamaño del parqueo, 
        el tiempo de gracia y las tarifas.
        Entrada:
        - Ninguna
        Salida:
        - Ninguna
        """
        ventanaMenu = tk.Toplevel(self.ventana)
        ventanaMenu.title("Menú de Configuración")
        ventanaMenu.geometry("360x280")
        ventanaMenu.config(bg="#f8f9fa")
        ventanaMenu.resizable(False, False)
        tk.Label(ventanaMenu, text="CONFIGURACIÓN DEL SISTEMA", font=("Arial", 11, "bold"), bg="#f8f9fa", fg="#333333").pack(pady=15)
        frameOpciones = tk.Frame(ventanaMenu, bg="#f8f9fa")
        frameOpciones.pack(fill="both", expand=True, padx=40)
        
        def modificarEspacios():
            """
            Funcionalidad:
            Abre un diálogo emergente para capturar la nueva cantidad de espacios 
            totales del parqueo. Valida que el dato no sea nulo ni negativo, actualiza 
            el atributo correspondiente del sistema y destruye el menú secundario.
            Entrada:
            - Ninguna
            Salida:
            - Ninguna
            """
            cantidadActual = len(self.estructuraEspacios)
            nuevaCantidad = simpledialog.askinteger(
                "Modificar Tamaño", 
                "Espacios actuales: " + str(cantidadActual) + "\n\nIngrese la nueva cantidad de espacios totales:",
                initialvalue=cantidadActual)
            if nuevaCantidad is not None and nuevaCantidad > 0:
                self.recalcularEstructuraParqueo(nuevaCantidad)
                ventanaMenu.destroy()

        def modificarGracia():
            """
            Funcionalidad:
            Abre un diálogo emergente para capturar el nuevo tiempo de gracia del 
            parqueo en minutos. Valida que el dato no sea nulo ni negativo, actualiza 
            el atributo correspondiente del sistema y destruye el menú secundario.
            Entrada:
            - Ninguna
            Salida:
            - Ninguna
            """
            nuevoTiempo = simpledialog.askinteger(
                "Modificar Tiempo de Gracia", 
                "Tiempo actual: " + str(self.tiempoGracia) + " minutos.\n\nIngrese el nuevo tiempo de gracia (en minutos):",
                initialvalue=self.tiempoGracia)
            if nuevoTiempo is not None and nuevoTiempo >= 0:
                self.tiempoGracia = nuevoTiempo
                messagebox.showinfo("Configuración", "Tiempo de gracia actualizado a: " + str(self.tiempoGracia) + " minutos.")
                ventanaMenu.destroy()

        def modificarTarifa():
            """
        Funcionalidad:
        Despliega un diálogo emergente para solicitar al usuario una nueva tarifa 
        por hora. Si el monto ingresado es válido y positivo, actualiza la variable 
        global del costo, muestra una confirmación y cierra el menú de configuración.
        Entrada:
        - Ninguna
        Salida:
        - Ninguna
        """
            nuevoMonto = simpledialog.askinteger(
                "Modificar Tarifa", 
                "Monto actual: ₡" + str(self.montoPorHora) + " por hora.\n\nIngrese el nuevo monto por hora (en colones):",
                initialvalue=self.montoPorHora)
            if nuevoMonto is not None and nuevoMonto >= 0:
                self.montoPorHora = nuevoMonto
                messagebox.showinfo("Configuración", "Tarifa por hora actualizada a: ₡" + str(self.montoPorHora))
                ventanaMenu.destroy()

        cantidadActualTotal = len(self.estructuraEspacios)
        btnEspacios = tk.Button(
            frameOpciones, text="1. Tamaño del Parqueo (" + str(cantidadActualTotal) + " espacios)", anchor="w", font=("Arial", 10), pady=4, command=modificarEspacios)
        btnEspacios.pack(fill="x", pady=6)
        
        btnGracia = tk.Button(
            frameOpciones, text="2. Tiempo de Gracia (" + str(self.tiempoGracia) + " min)", anchor="w", font=("Arial", 10), pady=4, command=modificarGracia)
        btnGracia.pack(fill="x", pady=6)
        
        btnTarifa = tk.Button(
            frameOpciones, text="3. Monto por Hora (₡" + str(self.montoPorHora) + ")", anchor="w", font=("Arial", 10), pady=4, command=modificarTarifa)
        btnTarifa.pack(fill="x", pady=6)
        
        btnSalir = tk.Button(
            frameOpciones, text="Regresar al Mapa", bg="#6c757d", fg="white", font=("Arial", 10, "bold"), command=ventanaMenu.destroy)
        btnSalir.pack(fill="x", pady=15)

    def recalcularEstructuraParqueo(self, nuevaCantidad):
        tieneElectricos = messagebox.askyesno(
            "Configuración Eléctrica",
            "¿Su parqueo posee espacios exclusivos para vehículos eléctricos?")
        
        self.estructuraEspacios = []
        self.botonesMatriz = {}
        
        multiplicacionEspeciales = nuevaCantidad * 0.05
        enteroEspeciales = int(multiplicacionEspeciales)
        if multiplicacionEspeciales > enteroEspeciales:
            cantidadEspeciales = enteroEspeciales + 1
        else:
            cantidadEspeciales = enteroEspeciales
        if nuevaCantidad == 20 and not tieneElectricos:
            cantidadEspeciales = 1
        elif cantidadEspeciales < 2 and nuevaCantidad <= 20:
            cantidadEspeciales = 2
        cantidadElectricos = 1 if tieneElectricos else 0
        cantidadRegulares = nuevaCantidad - cantidadEspeciales - cantidadElectricos
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
            numEspacio += 1
        numRegular = 1
        for i in range(cantidadRegulares):
            self.estructuraEspacios.append(("R" + str(numRegular), "Regular", "#00fc2a"))
            numRegular += 1
        numEspecial = 1
        for i in range(cantidadEspeciales):
            self.estructuraEspacios.append(("L" + str(numEspecial), "Especial", "#00fc2a"))
            numEspecial += 1
        for elemento in self.frameInferior.winfo_children():
            elemento.destroy()
        self.crearMapaParqueo(self.frameInferior)
        self.crearMenuBotones(self.frameInferior)
        self.actualizarMapa()
        messagebox.showinfo("Configuración", "El tamaño del parqueo se ha reconfigurado a " + str(nuevaCantidad) + " espacios exitosamente.")

    def generarXmlPorTipoPago(self):
        """
        Funcionalidad:
        Genera un archivo XML con los vehiculos activos agrupados en 3 secciones
        segun su tipo de pago: efectivo, sinpe y tarjeta.
        Entrada:
        - Ninguna
        Salida:
        - Ninguna
        """
        efectivo = ""
        sinpe = ""
        tarjeta = ""
        
        for vehiculo in self.vehiculosActuales:
            linea = ("<vehiculo>"
                + "<placa>" + vehiculo.placa + "</placa>"
                + "<marca>" + str(vehiculo.marca) + "</marca>"
                + "<color>" + str(vehiculo.color) + "</color>"
                + "<tipo>" + str(vehiculo.tipoIngreso) + "</tipo>"
                + "<espacio>" + str(vehiculo.codigoEspacio) + "</espacio>"
                + "<horaEntrada>" + str(vehiculo.horaEntrada) + "</horaEntrada>"
                + "<horaSalida>" + str(vehiculo.horaSalida) + "</horaSalida>"
                + "<monto>" + str(vehiculo.monto) + "</monto>"
                + "<tipoPago>" + str(vehiculo.tipoPago) + "</tipoPago>"
                + "</vehiculo>\n")
            if str(vehiculo.tipoPago).lower() == "sinpe":
                sinpe = sinpe + linea
            elif str(vehiculo.tipoPago).lower() == "tarjeta":
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
        messagebox.showinfo("XML generado", "Archivo 'cierrePorTipoPago.xml' guardado correctamente.")
        
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