
from datetime import datetime, timedelta

import DataBaseInitializer


def cargar_novedad(legajo, fecha_inicio, fecha_fin, hora_inicio, hora_fin, motivo):
    try:
        # Convertir las fechas en objetos datetime.date
        fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()

        # Validación: fecha fin no puede ser menor que fecha inicio
        if fecha_fin < fecha_inicio:
            raise ValueError("La fecha de fin no puede ser anterior a la fecha de inicio.")

        # Conexión a la base de datos
        conn = DataBaseInitializer.get_db_connection()
        cursor = conn.cursor()

        # Cargar una novedad por cada día del rango
        fecha_actual = fecha_inicio
        while fecha_actual <= fecha_fin:
            cursor.execute("""
                INSERT INTO novedades (legajo, fecha_inicio, fecha_fin, hora_inicio, hora_fin, motivo)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                legajo,
                fecha_actual.isoformat(),
                fecha_actual.isoformat(),  # mismo valor para inicio y fin si es un solo día
                hora_inicio,
                hora_fin,
                motivo
            ))
            fecha_actual += timedelta(days=1)

        conn.commit()
        print("Novedades cargadas correctamente.")
    except Exception as e:
        print(f"Error al cargar la novedad: {e}")
    finally:
        conn.close()




def eliminar_novedad_por_id(novedad_id):
    try:
        # Conexión a la base de datos
        conn = DataBaseInitializer.get_db_connection()
        cursor = conn.cursor()

        print(f"Intentando eliminar novedad con ID: {novedad_id}")

        # Verificamos si existe la novedad
        cursor.execute("SELECT * FROM novedades WHERE id = ?", (novedad_id,))
        row = cursor.fetchone()

        if not row:
            print(f"No se encontró ninguna novedad con ID {novedad_id}.")
            return {"success": False, "message": f"No existe la novedad con ID {novedad_id}"}

        print("Registro encontrado:", row)

        # Ejecutar la eliminación
        cursor.execute("DELETE FROM novedades WHERE id = ?", (novedad_id,))
        conn.commit()

        if cursor.rowcount > 0:
            print(f"Novedad con ID {novedad_id} eliminada correctamente.")
            return {"success": True, "message": f"Novedad con ID {novedad_id} eliminada correctamente."}
        else:
            print("No se eliminó ninguna fila.")
            return {"success": False, "message": "No se eliminó ninguna fila."}

    except Error as e:
        print(f"Error al eliminar la novedad: {e}")
        return {"success": False, "message": f"Error al eliminar: {e}"}
    finally:
        if conn:
            conn.close()
