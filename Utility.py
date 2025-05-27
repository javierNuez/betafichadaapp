from datetime import datetime
import os
import platform
import socket
import subprocess
import pandas as pd
import re
import time

import DataBaseInitializer
import DataBaseManager
import FichadaService


def obtener_nombre_equipo(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except socket.herror:
        return "Desconocido"
    
def esta_en_linea(ip):
    """Realiza un ping para verificar si la IP está activa"""
    param = "-n" if platform.system().lower() == "windows" else "-c"
    try:
        resultado = subprocess.run(["ping", param, "1", ip], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return resultado.returncode == 0  # Si el código de salida es 0, el host responde
    except Exception:
        return False

def generarFichadas():

    # Cargar los archivos Excel
    df_legajo = pd.read_excel("LegajoTarjeta.xlsx")
    df_fichadas = pd.read_excel("Fichadas.xlsx")

    # Unir los DataFrames por el campo 'Tarjeta'
    df_unido = pd.merge(df_fichadas, df_legajo, on="Tarjeta", how="inner")

    # Combinar Fecha y Hora en una nueva columna FechaHora
    df_unido["FechaHora"] = df_unido["Fecha"].astype(str) + " " + df_unido["Hora"].astype(str)

    # Seleccionar solo las columnas necesarias
    df_resultado = df_unido[["Legajo", "Nombre", "FechaHora"]]

    # Guardar como archivo CSV
    df_resultado.to_csv("Resultado.csv", index=False, encoding='utf-8')

    print("Archivo Resultado.csv generado correctamente.")

def procesar_fichadas_desde_csv(ruta_csv="Resultado.csv"):
    df = pd.read_csv(ruta_csv)

    for index, fila in df.iterrows():
        legajo = int(fila["Legajo"])
        nombre = str(fila["Nombre"])
        fechaHora_str = str(fila["FechaHora"])

        # Intentar parsear distintos formatos de entrada
        formatos = [
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y %H:%M",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M"
        ]

        fechaHora_obj = None
        for fmt in formatos:
            try:
                fechaHora_obj = datetime.strptime(fechaHora_str, fmt)
                break
            except ValueError:
                continue

        if fechaHora_obj is None:
            print(f"Error de formato de fechaHora en la fila {index + 1}: {fechaHora_str}")
            continue

        # Convertir a string con milisegundos
        fechaHora_formateada = fechaHora_obj.strftime("%Y-%m-%d %H:%M:%S.%f")

        # Llamar al método de registro con fechaHora como string formateada
        FichadaService.registrar_fichada_manual_sin_repetir(legajo, nombre, fechaHora_formateada)




def generarFichadasDesdeCro(ruta_cro="Fichadas.cro", ruta_legajo="LegajoTarjeta.xlsx"):
    import pandas as pd

    tarjetas = []
    fechas = []
    horas = []

    with open(ruta_cro, "r", encoding="utf-8") as archivo:
        for linea in archivo:
            tarjeta = linea[0:5].strip()
            fecha = linea[6:16].strip()
            hora = linea[17:22].strip()

            tarjetas.append(tarjeta)
            fechas.append(fecha)
            horas.append(hora)

    df_fichadas = pd.DataFrame({
        "Tarjeta": tarjetas,
        "Fecha": fechas,
        "Hora": horas
    })

    df_legajo = pd.read_excel(ruta_legajo)

    # Convertir a entero
    df_fichadas["Tarjeta"] = df_fichadas["Tarjeta"].astype(int)
    df_legajo["Tarjeta"] = df_legajo["Tarjeta"].astype(int)

    df_unido = pd.merge(df_fichadas, df_legajo, on="Tarjeta", how="inner")

    df_unido["FechaHora"] = df_unido["Fecha"] + " " + df_unido["Hora"]

    df_resultado = df_unido[["Legajo", "Nombre", "FechaHora"]]

    df_resultado.to_csv("Resultado.csv", index=False, encoding="utf-8")

    print("Archivo Resultado.csv generado correctamente desde archivo .cro.")


    
def calcularDiferenciaParaLlegadasTarde(t1, t2):
    try:
        # Asegurarse de que t1 y t2 estén en formato HH:MM
        t1 = f"{t1}:00"
        t2 = f"{t2}:00"
        tiempo1 = datetime.strptime(t1, "%H:%M:%S")
        tiempo2 = datetime.strptime(t2, "%H:%M:%S")

        if tiempo1 < tiempo2:
            diferencia = tiempo2 - tiempo1 
            horas, resto = divmod(diferencia.seconds, 3600)
            minutos, segundos = divmod(resto, 60)

            # Formatear con ceros a la izquierda
            return f"{horas:02}:{minutos:02}:{segundos:02}"
        else:
            return "No"
    except ValueError:
        return "Sin info"
    
def calcularDiferenciaParasalidasDespuesHora(t1, t2):
    try:
        # Asegurarse de que t1 y t2 estén en formato HH:MM
        t1 = f"{t1}:00"
        t2 = f"{t2}:00"
        tiempo1 = datetime.strptime(t1, "%H:%M:%S")
        tiempo2 = datetime.strptime(t2, "%H:%M:%S")

        if tiempo1 < tiempo2:
            diferencia = tiempo2 - tiempo1 
            horas, resto = divmod(diferencia.seconds, 3600)
            minutos, segundos = divmod(resto, 60)

            # Formatear con ceros a la izquierda
            return f"{horas:02}:{minutos:02}:{segundos:02}"
        else:
            return "No"
    except ValueError:
        return "Sin info"


def calcularHorasTrabajadas(t1, t2):
    try:
        # Asegurarse de que t1 y t2 estén en formato HH:MM
        t1 = f"{t1}:00"
        t2 = f"{t2}:00"
        tiempo1 = datetime.strptime(t1, "%H:%M:%S")
        tiempo2 = datetime.strptime(t2, "%H:%M:%S")

        if tiempo1 < tiempo2:
            diferencia = tiempo2 - tiempo1 
            horas, resto = divmod(diferencia.seconds, 3600)
            minutos, segundos = divmod(resto, 60)

            # Formatear con ceros a la izquierda
            return f"{horas:02}:{minutos:02}:{segundos:02}"
        else:
            return "No"
    except ValueError:
        return "Sin info."
    


# Mapeo de abreviaturas a índices de días (Lunes = 0, ..., Domingo = 6)
dias_abrev = {
    'L': 0, 'Lu': 0,
    'M': 1, 'Ma': 1,
    'X': 2, 'Mi': 2,
    'J': 3, 'Ju': 3,
    'V': 4, 'Vi': 4,
    'S': 5, 'Sa': 5,
    'D': 6, 'Do': 6,
}

dias_orden = ['L', 'Ma', 'Mi', 'Ju', 'Vi', 'Sa', 'Do']


def normalizar_hora(hora_str):
    """Convierte strings como '7.15', '815', '7' en formato 'HH:MM'."""
    hora_str = hora_str.replace('.', ':')
    if 'a' in hora_str:  # separar por 'a'
        partes = hora_str.split('a')
    elif '-' in hora_str:
        partes = hora_str.split('-')
    else:
        return []

    def formatear(h):
        h = h.strip()
        if ':' in h:
            hh, mm = h.split(':')
        elif len(h) > 2:
            hh, mm = h[:-2], h[-2:]
        else:
            hh, mm = h, '00'
        return f"{int(hh):02d}:{int(mm):02d}"

    if len(partes) == 2:
        return [formatear(partes[0]), formatear(partes[1])]
    return []


def expandir_dias(bloque):
    """Devuelve una lista de índices de días a partir de abreviaturas o rangos."""
    dias = []
    partes = re.findall(r'[A-Z][a-z]?(?:-[A-Z][a-z]?)?', bloque)

    for parte in partes:
        if '-' in parte:  # rango como Ma-Vi
            ini_abrev, fin_abrev = parte.split('-')
            ini = dias_abrev.get(ini_abrev, -1)
            fin = dias_abrev.get(fin_abrev, -1)
            if ini != -1 and fin != -1:
                if ini <= fin:
                    dias.extend(range(ini, fin + 1))
                else:
                    dias.extend(list(range(ini, 7)) + list(range(0, fin + 1)))
        else:  # día único
            idx = dias_abrev.get(parte, -1)
            if idx != -1 and idx not in dias:
                dias.append(idx)

    return dias


def parsear_horarios(texto):
    resultado = [[] for _ in range(7)]  # Lunes a Domingo

    # Separar en bloques que contengan días seguidos de horarios
    bloques = re.findall(r'([A-Z][a-zA-Z\-]*)\s*([0-9:.]+ *[a\-] *[0-9:.]+)', texto)

    for dias_raw, horas_raw in bloques:
        dias = expandir_dias(dias_raw)
        horas = normalizar_hora(horas_raw)
        for d in dias:
            resultado[d] = horas

    return resultado

def borrarResultado():
    archivo = "Resultado.csv"

# Verificar que el archivo exista
    if os.path.exists(archivo):
        # Obtener la fecha de última modificación del archivo
        timestamp_modificacion = os.path.getmtime(archivo)
        fecha_modificacion = datetime.fromtimestamp(timestamp_modificacion).date()

        # Obtener la fecha actual del sistema
        hoy = datetime.today().date()

        # Comparar y eliminar si corresponde
        if hoy > fecha_modificacion:
            os.remove(archivo)
            print(f"Archivo '{archivo}' eliminado (fecha de modificación: {fecha_modificacion}, hoy: {hoy}).")
        else:
            print(f"El archivo NO fue eliminado. Fecha de modificación: {fecha_modificacion}, hoy: {hoy}.")
    else:
        print("El archivo no existe.")

def traerNuevasFichadas():
    try:
        borrarResultado()
        generarFichadasDesdeCro()
        procesar_fichadas_desde_csv()
    except Exception as e:
        print(f"Error al registrar fichada: {e}")
        return False



def actualizar_personas_desde_excel():
    conn = DataBaseInitializer.get_db_connection("personas")
    # Leer el Excel
    df = pd.read_excel('Relacion.xlsx')

    # Validar columnas necesarias
    if not {'Legajo', 'Categoria', 'Relacion'}.issubset(df.columns):
        raise ValueError("El archivo debe tener las columnas: Legajo, Categoria y Relacion")

    # Conexión y cursor
    cursor = conn.cursor()

    # Iterar sobre las filas del DataFrame
    for _, fila in df.iterrows():
        legajo = fila['Legajo']
        categoria = fila['Categoria']
        relacion = fila['Relacion']

        # Actualizar si el legajo existe
        cursor.execute("""
            UPDATE personas
            SET categoria = ?, relacion = ?
            WHERE legajo = ?
        """, (categoria, relacion, legajo))

    # Guardar cambios
    conn.commit()
    print("Actualización completa.")

def actualizarCategorias():
    conn = DataBaseInitializer.get_db_connection("personas")
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE personas
        SET 
            categoria = REPLACE(categoria, 'Liq ', '')
        WHERE 
            categoria LIKE '%Liq %'
    """)

    conn.commit()
    print("Caracteres 'Liq ' eliminados del campo categoria.")