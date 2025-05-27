
from datetime import datetime, timedelta

import DataBaseInitializer


def cargar_novedad(legajo, fecha_inicio, fecha_fin, hora_inicio, hora_fin, motivo, db_path='mi_base.db'):
    try:
        # Convertir las fechas en objetos datetime.date
        fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()

        # Validación: fecha fin no puede ser menor que fecha inicio
        if fecha_fin < fecha_inicio:
            raise ValueError("La fecha de fin no puede ser anterior a la fecha de inicio.")

        # Conexión a la base de datos
        conn = DataBaseInitializer.get_db_connection("novedades")
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