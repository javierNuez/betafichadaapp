
import base64

class QRProcessor:
    @staticmethod
    def codificar(algo):
        return base64.b64encode(algo.encode('utf-8')).decode('utf-8')

    @staticmethod
    def decodificar(codificada):
        return base64.b64decode(codificada).decode('utf-8')

 

    @staticmethod
    def normalizar_codigo(codigo):
        if codigo.isdigit() and int(codigo) < 10000:
            return codigo.zfill(4)
        return codigo

    @staticmethod
    def validar_numero_en_rango(cadena):
        try:
            numero = int(cadena)
            return 700 <= numero <= 9999 or numero == 0000
        except ValueError:
            return False

    @staticmethod
    def validar(qr_data):
        destino, legajo, nombre = qr_data.split('@')
        return destino == "beta" and QRProcessor.validar_numero_en_rango(legajo)