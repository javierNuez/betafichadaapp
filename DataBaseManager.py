from datetime import datetime
import sqlite3
from flask import app
import DataBaseInitializer

def obtenerPersonas():
    conn = DataBaseInitializer.get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM personas")
    personas = cursor.fetchall()
    conn.close()
    return personas

def obtenerPersonasBSAS():
    conn = DataBaseInitializer.get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""SELECT * 
        FROM personas
        WHERE legajo < 4000
        AND sector <> 'Fuerza de ventas' and estado <> 'Inactivo';""")
    personas = cursor.fetchall()
    conn.close()
    return personas

def obtenerFichadas():
    conn = DataBaseInitializer.get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM fichadas")
    fichadas = cursor.fetchall()
    conn.close()
    return fichadas

def obtenerFichadasPorFecha(fecha1, fecha2):
    conn = DataBaseInitializer.get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    consulta = """
    SELECT id, legajo, nombre, substr(fechaHora, 1, length(fechaHora) - 10) as fechaHora
    FROM fichadas
    WHERE fechaHora BETWEEN ? AND ?
    ORDER BY fechaHora ASC
"""
    cursor.execute(consulta, (fecha1, fecha2))
    fichadas = cursor.fetchall()
    conn.close()
    
    return fichadas

def obtenerHorarios():
    conn = DataBaseInitializer.get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM horariosBase order by dia_inicio")
    horarios = cursor.fetchall()
    conn.close()

    return horarios






def obtenerNovedades():
    conn = DataBaseInitializer.get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM novedades")
    novedades = cursor.fetchall()
    conn.close()
    return novedades

def obtenerFichadasPorFechaDia(fecha):
    conn = DataBaseInitializer.get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    fecha_str = fecha
    

    consulta = """
    SELECT * FROM fichadas
    WHERE DATE(fechaHora) = ?
    ORDER BY fechaHora ASC
    """
    cursor.execute(consulta, (fecha_str,))
    fichadas = cursor.fetchall()
    
    conn.close()
    
    return fichadas