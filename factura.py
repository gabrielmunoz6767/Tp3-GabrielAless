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