from datetime import datetime
from fpdf import FPDF
import qrcode
def generarComprobantePago(placaVehiculo, datosCarro, metodoPago):
    """
    Genera un archivo PDF legítimo con FPDF e inserta un QR dinámico real.
    No utiliza importación OS ni f-strings. Todas las variables usan camelCase.
    """
    ahora = datetime.now()
    fechaStr = ahora.strftime("%d-%m-%Y")
    horaSalidaStr = ahora.strftime("%H_%M")
    nombreFactura = "factura_#" + placaVehiculo + "_" + fechaStr + "_" + horaSalidaStr + ".pdf"
    contenidoQr = "Placa: " + placaVehiculo + " | Total: " + str(datosCarro[6]) + " | Espacio: " + str(datosCarro[3])
    imgQr = qrcode.make(contenidoQr)
    imgQr.save("temp_qr.png")
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.set_font("Arial", style="B", size=12)
    pdf.cell(200, 10, txt="COMPROBANTE DIGITAL DE PARQUEO", ln=1, align="L")
    pdf.set_font("Arial", size=11)
    pdf.ln(4)
    
    pdf.cell(200, 7, txt="Placa Vehículo: " + placaVehiculo, ln=1)
    pdf.cell(200, 7, txt="Marca: " + str(datosCarro[0]) + " | Color: " + str(datosCarro[1]), ln=1)
    pdf.cell(200, 7, txt="Espacio Liberado: " + str(datosCarro[3]), ln=1)
    pdf.cell(200, 7, txt="Hora Entrada: " + str(datosCarro[4]), ln=1)
    pdf.cell(200, 7, txt="Hora Salida: " + ahora.strftime("%H:%M"), ln=1)
    pdf.cell(200, 7, txt="Método de Pago: " + str(metodoPago), ln=1)
    pdf.cell(200, 7, txt="Monto Cobrado: " + str(datosCarro[6]), ln=1)
    pdf.ln(10)
    pdf.cell(200, 7, txt="Código QR de Validación:", ln=1)
    pdf.image("temp_qr.png", x=10, y=110, w=40, h=40)
    pdf.output(nombreFactura)
    return nombreFactura

def generarVoucherEntrada(placaVehiculo, marcaVehiculo, colorVehiculo, tipoEspacio, codigoEspacio):
    """
    Genera un archivo PDF tipo Voucher al parquear un vehículo en un espacio verde.
    Crea un código QR dinámico con el formato Placa-Marca-Tipo-FechaHoraEntrada.
    """
    ahora = datetime.now()
    fechaStr = ahora.strftime("%d-%m-%Y")
    horaEntradaStr = ahora.strftime("%H_%M")
    horaPantalla = ahora.strftime("%H:%M")
    nombreVoucher = "voucher_#" + placaVehiculo + "_" + fechaStr + "_" + horaEntradaStr + ".pdf"
    fechaHoraEntradaCombo = fechaStr + " " + horaPantalla
    contenidoQr = placaVehiculo + "-" + marcaVehiculo + "-" + tipoEspacio + "-" + fechaHoraEntradaCombo
    imgQr = qrcode.make(contenidoQr)
    imgQr.save("temp_voucher_qr.png")
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", style="B", size=14)
    pdf.cell(200, 10, txt="PARQUEADERO", ln=1, align="C")
    
    pdf.set_font("Arial", size=11)
    pdf.cell(200, 8, txt="su mejor eleccion", ln=1, align="C")
    pdf.ln(10)
    
    pdf.set_font("Arial", style="B", size=12)
    pdf.cell(200, 10, txt=" VOUCHER DE INGRESO A PARQUEO", ln=1, align="L")
    pdf.set_font("Arial", size=11)
    pdf.ln(4)
    
    pdf.cell(200, 7, txt="Placa Vehiculo: " + placaVehiculo, ln=1)
    pdf.cell(200, 7, txt="Marca Seleccionada: " + marcaVehiculo, ln=1)
    pdf.cell(200, 7, txt="Color: " + colorVehiculo, ln=1)
    pdf.cell(200, 7, txt="Tipo de Espacio Asignado: " + tipoEspacio + " (" + codigoEspacio + ")", ln=1)
    pdf.cell(200, 7, txt="Fecha y Hora Ingreso: " + fechaHoraEntradaCombo, ln=1)
    pdf.ln(10)
    
    pdf.cell(200, 7, txt="Codigo QR de Entrada (Escanear al salir):", ln=1)
    pdf.image("temp_voucher_qr.png", x=10, y=95, w=40, h=40)
    
    pdf.output(nombreVoucher)
    return nombreVoucher
def generarReporteCierreDiario(listaRegistros, totalesPorTipoPago, montoTotalDia):
    """
    Funcionalidad:
    Genera el reporte oficial de cierre diario en PDF, usando 3 colores y 3
    tamanos de letra distintos para el titulo, la tabla y los totales.
    Entrada:
    - listaRegistros(list): lista de tuplas (ubicacion, placa, horaEntrada, horaSalida, tipoPago, monto)
    - totalesPorTipoPago(dict): diccionario {tipoPago: montoAcumulado}
    - montoTotalDia(int): monto total recaudado en el dia
    Salida:
    - nombreArchivo(str): nombre del archivo PDF generado
    """
    ahora = datetime.now()
    fechaStr = ahora.strftime("%d-%m-%Y")
    nombreArchivo = "reporte_cierre_diario_" + fechaStr + ".pdf"

    pdf = FPDF()
    pdf.add_page()

    pdf.set_text_color(0, 51, 102)
    pdf.set_font("Arial", style="B", size=18)
    pdf.cell(0, 12, txt="REPORTE DE CIERRE DIARIO", ln=1, align="C")

    pdf.set_text_color(80, 80, 80)
    pdf.set_font("Arial", style="I", size=11)
    pdf.cell(0, 8, txt="Fecha: " + fechaStr, ln=1, align="C")
    pdf.ln(6)

    anchos = [25, 25, 25, 25, 30, 25]
    encabezados = ["Ubicacion", "Placa", "H.Entrada", "H.Salida", "TipoPago", "Monto"]
    pdf.set_text_color(255, 255, 255)
    pdf.set_fill_color(0, 51, 102)
    pdf.set_font("Arial", style="B", size=9)
    for i in range(len(encabezados)):
        pdf.cell(anchos[i], 8, txt=encabezados[i], border=1, fill=True, align="C")
    pdf.ln()

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=9)
    for fila in listaRegistros:
        for i in range(len(fila)):
            pdf.cell(anchos[i], 7, txt=str(fila[i]), border=1, align="C")
        pdf.ln()

    pdf.ln(8)
    pdf.set_text_color(0, 102, 51)
    pdf.set_font("Arial", style="B", size=11)
    for tipoPago in totalesPorTipoPago:
        pdf.cell(0, 7, txt="Total " + tipoPago + ": C" + str(totalesPorTipoPago[tipoPago]), ln=1)

    pdf.ln(4)
    pdf.set_text_color(153, 0, 0)
    pdf.set_font("Arial", style="B", size=14)
    pdf.cell(0, 10, txt="TOTAL RECAUDADO DEL DIA: C" + str(montoTotalDia), ln=1)

    pdf.output(nombreArchivo)
    return nombreArchivo