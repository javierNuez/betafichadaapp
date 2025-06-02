import sqlite3
from flask import jsonify
import DataBaseInitializer
import requests
import DataBaseManager


def get_persona_by_legajo(legajo):
        conn = DataBaseInitializer.get_db_connection("personas")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM personas WHERE legajo = ?", (legajo,))
        row = cursor.fetchone()
        conn.close()

        if row:
            keys = ['legajo', 'nombre', 'apellido', 'dni', 'fecha_ingreso', 'fecha_egreso', 'sector', 'centro', 'categoria', 'estado', 'relacion']
            return dict(zip(keys, row))
        return None

def importar_personas_desde_api():
    url = 'http://89.0.0.213:8000/api/personas'  # Cambiar a la URL real de tu API

    try:
        response = requests.get(url)
        response.raise_for_status()
        personas = response.json()

        for p in personas:
            agregarPersona(
                legajo=p.get("legajo"),
                nombre=p.get("nombre"),
                apellido=p.get("apellido"),
                dni="",  # No está en los datos, se deja vacío o se puede generar
                fecha_ingreso=p.get("f_ingreso") or None,
                fecha_egreso=None,  # No está en los datos
                sector=p.get("sector"),
                centro="",  # Mapeado desde 'sucursal'
                categoria="",  # No está disponible
                estado="Activo" if p.get("habilitado") == "si" else "Inactivo"
            )
        print("Importación completada correctamente.")
    except Exception as e:
        print(f"Error al importar personas: {e}")
    

def delete_personas_by_legajos(legajos):
    if not legajos:
        return  # No hay nada que eliminar

    conn = DataBaseInitializer.get_db_connection()
    try:
        cursor = conn.cursor()
        # Crear una cláusula IN segura usando marcadores de posición
        placeholders = ','.join(['?'] * len(legajos))
        query = f"DELETE FROM personas WHERE legajo IN ({placeholders})"
        cursor.execute(query, legajos)
        conn.commit()
    finally:
        conn.close()

def agregarPersona(legajo, nombre, apellido, dni, fecha_ingreso, fecha_egreso, sector, centro, categoria, estado):
    conn = DataBaseInitializer.get_db_connection("personas")
    cursor = conn.cursor()
    cursor.execute('''
            INSERT INTO personas (legajo, nombre, apellido, dni, fecha_ingreso, fecha_egreso, sector, centro, categoria, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (legajo, nombre, apellido, dni, fecha_ingreso, fecha_egreso, sector, centro, categoria, estado))
    conn.commit()

def check_legajo(legajo):
    try:
        conn = DataBaseInitializer.get_db_connection("personas")
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM personas WHERE legajo = ?', (legajo,))
        result = cursor.fetchone()
        return result[0] > 0
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Error al verificar el legajo'}), 500
    finally:
        conn.close()

def obtener_todos_los_legajos():
    try:
        # Conexiones y datos
        conn = DataBaseInitializer.get_db_connection("personas")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Consultamos todos los legajos con nombre y apellido
        cur.execute("""
                SELECT legajo, nombre, apellido
                FROM personas
                WHERE fecha_egreso IS NULL OR estado = 'activo'
                ORDER BY apellido, nombre
            """)
        
        personas = [
                {
                    "legajo": row["legajo"],
                "nombre": row["nombre"],
                "apellido": row["apellido"]
                }
                for row in cur.fetchall()
            ]
        print(personas)
        return personas

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        conn.close()

def obtener_nombre_por_legajo(legajo):
    try:
        conn = DataBaseInitializer.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT nombre, apellido
            FROM personas
            WHERE legajo = ?
        """, (legajo,))
        
        resultado = cursor.fetchone()
        if resultado:
            nombre, apellido = resultado
            return f"{nombre} {apellido}"
        else:
            return None  # O podrías lanzar una excepción o devolver un mensaje

    except Exception as e:
        print("Error al buscar el nombre:", e)
        return None

    finally:
        conn.close()



def actualizar_persona(id_persona, datos):
    conn = DataBaseInitializer.get_db_connection("personas")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE personas
        SET nombre = ?, apellido = ?, dni = ?, fecha_ingreso = ?, fecha_egreso = ?, 
            sector = ?, centro = ?, categoria = ?, estado = ?, relacion = ?
        WHERE id = ?
    """, (
        datos['nombre'],
        datos['apellido'],
        datos['dni'],
        datos['fecha_ingreso'],
        datos['fecha_egreso'],
        datos['sector'],
        datos['centro'],
        datos['categoria'],
        datos['estado'],
        datos['relacion'],
        id_persona  # cambiás legajo por id
    ))
    conn.commit()
    conn.close()




def crear_persona(datos):
        conn = DataBaseInitializer.get_db_connection("personas")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO personas (legajo, nombre, apellido, dni, fecha_ingreso, fecha_egreso, sector, centro, categoria, estado, relacion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datos['legajo'],
            datos['nombre'],
            datos['apellido'],
            datos['dni'],
            datos['fecha_ingreso'],
            datos['fecha_egreso'],
            datos['sector'],
            datos['centro'],
            datos['categoria'],
            datos['estado'],
            datos['relacion']
        ))
        conn.commit()
        conn.close()

def get_persona_by_nombre(nombre):
        conn = DataBaseInitializer.get_db_connection("personas")
        cursor = conn.cursor()
        cursor.execute("SELECT legajo, nombre, apellido, dni, fecha_ingreso, fecha_egreso, sector, centro, categoria, estado, relacion FROM personas WHERE nombre = ?", (nombre,))
        row = cursor.fetchone()
        conn.close()
        if row:
            print(f"""
                'legajo': {row[0]},
                'nombre': {row[1]},
                'apellido': {row[2]},
                'dni': {row[3]},
                'fecha_ingreso': {row[4]},
                'fecha_egreso': {row[5]},
                'sector': {row[6]},
                'centro': {row[7]},
                'categoria': {row[8]},
                'estado': {row[9]},
                'relacion': {row[10]}

                    """)
            return {
                'legajo': row[0],
                'nombre': row[1],
                'apellido': row[2],
                'dni': row[3],
                'fecha_ingreso': row[4],
                'fecha_egreso': row[5],
                'sector': row[6],
                'centro': row[7],
                'categoria': row[8],
                'estado': row[9],
                'relacion': row[10]
            }
        return None

def obtenerLegajoRelacion():
    registros = []
    personas = DataBaseManager.obtenerPersonas()
    for p in personas:
        l = [p[1], p[11]]
        
        registros.append(l)
    #print(type(registros))
    return registros