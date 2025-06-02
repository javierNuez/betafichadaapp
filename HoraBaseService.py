#Traer el horario de ingreso base.    
import DataBaseInitializer
import Utility
import sqlite3

def traerHoraInicioBaseDelDia(legajo, diaActual, horariosBase):
    diaA = diaActual.weekday() + 1
    horaInicio = None
    i = 0
    while i < len(horariosBase):
        h = horariosBase[i]
        if h[1] == legajo and diaA == h[2]:
            horaInicio = h[3]
            
            break
        i += 1
        
    return horaInicio

def traerHoraFinBaseDelDia(legajo, diaActual, horariosBase):
    diaA = diaActual.weekday() + 1
    ultimaHora = None
    for h in horariosBase:
        if h[1] == legajo and h[4] == diaA :
            ultimaHora = h[5]
    return ultimaHora

def insertar_horario_base(legajo, dia_inicio, hora_inicio, tipo, dia_fin=None, hora_fin=None, fecha_hora_desde=None, fecha_hora_hasta=None):
    conexion = DataBaseInitializer.get_db_connection()
    cursor = conexion.cursor()

    # Validación de conflicto similar a la anterior
    cursor.execute("""
        SELECT 1 FROM horariosbase
        WHERE legajo = ?
        AND dia_inicio = ?
        AND (
            (fecha_hora_desde <= ? AND fecha_hora_hasta >= ?)
            OR
            (fecha_hora_desde <= ? AND fecha_hora_hasta >= ?)
            OR
            (fecha_hora_desde BETWEEN ? AND ?)
            OR
            (fecha_hora_hasta BETWEEN ? AND ?)
        )
        AND (
            (hora_inicio < ? AND hora_fin > ?)
        )
        LIMIT 1
    """, (
        legajo,
        dia_inicio,
        fecha_hora_hasta, fecha_hora_desde,
        fecha_hora_desde, fecha_hora_hasta,
        fecha_hora_desde, fecha_hora_hasta,
        fecha_hora_desde, fecha_hora_hasta,
        hora_fin, hora_inicio
    ))

    if cursor.fetchone() is not None:
        conexion.close()
        return {
            "success": False,
            "message": "No se pudo agregar el horario porque tiene conflicto con un registro vigente."
        }

    # Si no hay conflicto, inserto
    query = """
    INSERT INTO horariosbase (legajo, dia_inicio, hora_inicio, dia_fin, hora_fin, tipo, fecha_hora_desde, fecha_hora_hasta)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    cursor.execute(query, (legajo, dia_inicio, hora_inicio, dia_fin, hora_fin, tipo, fecha_hora_desde, fecha_hora_hasta))
    conexion.commit()
    conexion.close()

    return {
        "success": True,
        "message": "Horario agregado correctamente."
    }


def insertarHorasSemanal(legajo, dias, hora_inicio, hora_fin, tipo, fecha_hora_desde, fecha_hora_hasta):
    conexion = DataBaseInitializer.get_db_connection()
    cursor = conexion.cursor()

    # Primero, verifico si existe algún registro con validez superpuesta
    # Esto implica que:
    # - el rango [fecha_hora_desde, fecha_hora_hasta] se solapa con algún registro existente
    # - y que el día y horario también se solape.

    # Vamos a consultar si existe algún registro que coincida en el legajo, que se superponga en fecha y horario

    # Para cada día que queremos insertar, verificamos:
    for dia in dias:
        cursor.execute("""
            SELECT 1 FROM horariosBase
            WHERE legajo = ?
            AND dia_inicio = ?
            AND (
                (fecha_hora_desde <= ? AND fecha_hora_hasta >= ?)  -- nuevo rango dentro del existente
                OR
                (fecha_hora_desde <= ? AND fecha_hora_hasta >= ?)  -- existente dentro del nuevo rango
                OR
                (fecha_hora_desde BETWEEN ? AND ?)                 -- comienza dentro del nuevo rango
                OR
                (fecha_hora_hasta BETWEEN ? AND ?)                 -- termina dentro del nuevo rango
            )
            AND (
                (hora_inicio < ? AND hora_fin > ?)  -- se superpone horario
            )
            LIMIT 1
        """, (
            legajo,
            dia,
            fecha_hora_hasta, fecha_hora_desde,
            fecha_hora_desde, fecha_hora_hasta,
            fecha_hora_desde, fecha_hora_hasta,
            fecha_hora_desde, fecha_hora_hasta,
            hora_fin, hora_inicio
        ))

        if cursor.fetchone() is not None:
            conexion.close()
            return {
                "success": False,
                "message": "No se pudo agregar el grupo de horarios porque algún día tiene conflicto."
            }

    # Si no hay conflicto, inserto todos los días:
    for dia in dias:
        cursor.execute("""
            INSERT INTO horariosBase (legajo, dia_inicio, hora_inicio, dia_fin, hora_fin, tipo, fecha_hora_desde, fecha_hora_hasta)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (legajo, dia, hora_inicio, dia, hora_fin, tipo, fecha_hora_desde, fecha_hora_hasta))

    conexion.commit()
    conexion.close()
    return {
        "success": True,
        "message": "Grupo de horarios agregado exitosamente."
    }


def insertarHorasEstimadas():
    conexion = DataBaseInitializer.get_db_connection()
    cursor = conexion.cursor()
    horarios = DataBaseInitializer.obtener_horarios_estimados()
    
    for h in horarios:
        legajo = h["legajo"]
        dia = h["dia_inicio"]
        hora_inicio = h["hora_inicio"]
        hora_fin = h["hora_fin"]
        tipo = ""
        cursor.execute("""
            INSERT INTO horariosBase (legajo, dia_inicio, hora_inicio, dia_fin, hora_fin, tipo)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (legajo, dia, hora_inicio, dia, hora_fin, tipo))

        conexion.commit()
    conexion.close()

import pandas as pd

def cargar_horarios_desde_excel():
    archivo = "PersonalHorarios.xlsx"
    df = pd.read_excel(archivo)

    for _, fila in df.iterrows():
        legajo = int(fila['Legajo'])
        apellido = fila['Apellido']
        nombre = fila['Nombre']
        horario_str = str(fila['Horarios'])

        horarios = Utility.parsear_horarios(horario_str)

        # Determinar tipo de horario
        dias_con_horario = [i for i, h in enumerate(horarios) if h]
        if dias_con_horario == list(range(5)):  # lunes (0) a viernes (4)
            tipo = "Semanal"
        else:
            tipo = "Variado"

        for dia, rango in enumerate(horarios):
            if rango:
                dia_inicio = dia + 1  # ajustar: lunes = 1 ... domingo = 7
                hora_inicio = rango[0]
                hora_fin = rango[1]
                insertar_horario_base(legajo, dia_inicio, hora_inicio, tipo, dia_fin=dia_inicio, hora_fin=hora_fin)


def obtenerLegajosUnicos():
    conn = DataBaseInitializer.get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Traer solo los legajos distintos
    cursor.execute("SELECT DISTINCT legajo FROM horariosBase ORDER BY legajo")
    filas = cursor.fetchall()
    conn.close()
    
    # Convertir a una lista de legajos
    legajos = [fila["legajo"] for fila in filas]
    
    return legajos