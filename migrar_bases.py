import sqlite3
import os
from collections import defaultdict, Counter
from statistics import mean
from datetime import datetime, timedelta

import DataBaseInitializer

def redondear_a_15_minutos(hora):
    minutos = hora.minute
    minutos_redondeados = round(minutos / 15) * 15
    if minutos_redondeados == 60:
        hora_redondeada = hora.replace(hour=(hora.hour + 1) % 24, minute=0)
    else:
        hora_redondeada = hora.replace(minute=minutos_redondeados)
    return f"{hora_redondeada.hour:02d}:{hora_redondeada.minute:02d}"

def obtener_horarios_estimados():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT legajo, fechaHora FROM fichadas ORDER BY legajo, fechaHora")
    registros = cursor.fetchall()
    conn.close()

    fichadas_por_legajo = defaultdict(lambda: defaultdict(list))

    for legajo, fechaHora in registros:
        dt = datetime.strptime(fechaHora, "%Y-%m-%d %H:%M:%S.%f")
        dia_semana = dt.weekday() + 1
        fichadas_por_legajo[legajo][dia_semana].append(dt)

    resultados = []

    for legajo, dias_semana in fichadas_por_legajo.items():
        horarios_dias = {}
        dias_validos = []

        for dia, fichadas_dia in dias_semana.items():
            fichadas_por_fecha = defaultdict(list)
            for dt in fichadas_dia:
                fichadas_por_fecha[dt.date()].append(dt)

            inicios = []
            fines = []

            for fecha, fichadas in fichadas_por_fecha.items():
                fichadas.sort()
                if len(fichadas) < 2:
                    continue

                inicio = fichadas[0]
                fin = fichadas[-1]
                duracion = (fin - inicio).seconds

                if duracion >= 6 * 3600:
                    inicios.append(inicio.time())
                    fines.append(fin.time())

            if not inicios or not fines:
                continue

            promedio_inicio = int(mean(h.hour * 3600 + h.minute * 60 for h in inicios))
            promedio_fin = int(mean(h.hour * 3600 + h.minute * 60 for h in fines))

            hora_ini = (datetime(2000, 1, 1) + timedelta(seconds=promedio_inicio)).time()
            hora_fin = (datetime(2000, 1, 1) + timedelta(seconds=promedio_fin)).time()

            duracion_total = (promedio_fin - promedio_inicio) % (24 * 3600)
            if 30600 <= duracion_total <= 34200:
                hora_ini = (datetime.combine(datetime.today(), hora_fin) - timedelta(hours=9)).time()

            hora_ini = redondear_a_15_minutos(hora_ini)
            hora_fin = redondear_a_15_minutos(hora_fin)

            horarios_dias[dia] = (hora_ini, hora_fin)
            dias_validos.append(dia)

        dias_habiles = [d for d in range(1, 6) if d in horarios_dias]
        if len(dias_habiles) >= 3:
            horarios_habiles = [horarios_dias[d] for d in dias_habiles]
            hora_ini_mas_comun = Counter(h[0] for h in horarios_habiles).most_common(1)[0][0]
            hora_fin_mas_comun = Counter(h[1] for h in horarios_habiles).most_common(1)[0][0]

            for d in range(1, 6):
                resultados.append({
                    "legajo": legajo,
                    "dia_inicio": d,
                    "hora_inicio": hora_ini_mas_comun,
                    "dia_fin": d,
                    "hora_fin": hora_fin_mas_comun,
                    "tipo": "estimado_habil"
                })
        else:
            for d, (h_ini, h_fin) in horarios_dias.items():
                resultados.append({
                    "legajo": legajo,
                    "dia_inicio": d,
                    "hora_inicio": h_ini,
                    "dia_fin": d,
                    "hora_fin": h_fin,
                    "tipo": "estimado"
                })

    return resultados

def get_db_connection():
    ruta = "BDtablas.db"
    conn = sqlite3.connect(ruta)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    tablas_esperadas = {
        "personas": create_tables_personas,
        "fichadas": create_tables_fichadas,
        "horariosBase": create_tables_horariosBase,
        "novedades": create_tables_novedades,
        "horasExtras": create_tables_horasExtras
    }
    for nombre_tabla, funcion_creacion in tablas_esperadas.items():
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (nombre_tabla,)
        )
        if not cursor.fetchone():
            print(f"Tabla '{nombre_tabla}' no existe. Creándola...")
            funcion_creacion(conn)
        else:
            print(f"Tabla '{nombre_tabla}' ya existe.")
    return conn

def create_tables_personas(conn):
    try:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS personas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                legajo INTEGER UNIQUE,
                nombre TEXT,
                apellido TEXT,
                dni INTEGER,
                fecha_ingreso TEXT,
                fecha_egreso TEXT,
                sector TEXT,
                centro TEXT,
                categoria TEXT,
                estado TEXT,
                relacion TEXT
            )
        ''')
        print("Tabla 'personas' verificada o creada exitosamente.")
        conn.commit()
    except Exception as e:
        print(f"Error creating tables: {e}")

def create_tables_fichadas(conn):
    try:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fichadas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                legajo INTEGER,
                nombre TEXT,
                fechaHora DATETIME
            )
        ''')
        print("Tabla 'fichadas' verificada o creada exitosamente.")
        conn.commit()
    except Exception as e:
        print(f"Error creating tables: {e}")

def create_tables_horariosBase(conn):
    try:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS horariosBase (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                legajo INTEGER NOT NULL,
                dia_inicio INTEGER CHECK (dia_inicio BETWEEN 1 AND 7),
                hora_inicio TEXT NOT NULL CHECK (hora_inicio LIKE '__:__'),
                dia_fin INTEGER CHECK (dia_fin BETWEEN 1 AND 7),
                hora_fin TEXT CHECK (hora_fin LIKE '__:__' OR hora_fin IS NULL),
                tipo TEXT CHECK (LENGTH(tipo) <= 10),
                FOREIGN KEY (legajo) REFERENCES personas(legajo) ON DELETE CASCADE
            )
        ''')
        print("Tabla 'horariosBase' verificada o creada exitosamente.")
        conn.commit()
    except Exception as e:
        print(f"Error creating tables: {e}")

def create_tables_novedades(conn):
    try:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS novedades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                legajo INTEGER NOT NULL,
                fecha_inicio DATE NOT NULL,
                fecha_fin DATE NOT NULL,
                hora_inicio TIME NOT NULL,
                hora_fin TIME NOT NULL,
                motivo TEXT,
                FOREIGN KEY (legajo) REFERENCES personas(legajo)
            )
        ''')
        print("Tabla 'novedades' verificada o creada exitosamente.")
        conn.commit()
    except Exception as e:
        print(f"Error creating tables: {e}")

def create_tables_horasExtras(conn):
    try:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS horasExtras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                legajo INTEGER UNIQUE,
                fecha DATE,
                hora_inicio TIME,
                hora_fin TIME,
                tipo TEXT
            )
        ''')
        print("Tabla 'horasExtras' verificada o creada exitosamente.")
        conn.commit()
    except Exception as e:
        print(f"Error creating tables: {e}")

import sqlite3
import os
import shutil




def get_old_db_path(name):
    return f"{name}.db"

def get_all_data_from_old_db(db_name, table_name):
    path = get_old_db_path(db_name)
    if not os.path.exists(path):
        print(f"Base de datos {path} no encontrada.")
        return []
    
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(f"SELECT * FROM {table_name}").fetchall()
            return rows
        except Exception as e:
            print(f"Error leyendo {table_name} desde {path}: {e}")
            return []

def insert_data_into_new_db(conn, table_name, rows):
    if not rows:
        return
    cols = rows[0].keys()
    placeholders = ", ".join(["?"] * len(cols))
    column_names = ", ".join(cols)
    values = [tuple(row[col] for col in cols) for row in rows]
    
    with conn:
        conn.executemany(
            f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})",
            values
        )
    print(f"{len(rows)} registros insertados en {table_name}.")

def migrate_all_to_new_db():
    new_db_path = "BDtablas.db"

    # Conectarse a la BD nueva
    conn = sqlite3.connect(new_db_path)
    cursor = conn.cursor()

    # Nombres de las tablas que deberían existir
    tablas_necesarias = ["personas", "fichadas", "horariosBase", "novedades", "horasExtras"]
    tablas_faltantes = []

    for tabla in tablas_necesarias:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (tabla,))
        if not cursor.fetchone():
            tablas_faltantes.append(tabla)

    if not tablas_faltantes:
        print("La base de datos ya contiene todas las tablas necesarias. No se necesita migrar.")
        conn.close()
        return

    # Si hay tablas faltantes, continuar con la migración
    print(f"Faltan las tablas: {', '.join(tablas_faltantes)}. Se procederá a la migración.")

    conn.close()
    
    if os.path.exists(new_db_path):
        os.remove(new_db_path)
        print("Eliminando base de datos antigua y creando nueva base de datos unificada...")

    conn = sqlite3.connect(new_db_path)
    DataBaseInitializer.create_tables_personas(conn)
    DataBaseInitializer.create_tables_fichadas(conn)
    DataBaseInitializer.create_tables_horariosBase(conn)
    DataBaseInitializer.create_tables_novedades(conn)
    DataBaseInitializer.create_tables_horasExtras(conn)
    conn.close()

    conn = sqlite3.connect(new_db_path)
    conn.row_factory = sqlite3.Row

    tablas_info = {
        "personas": "personas",
        "fichadas": "fichadas",
        "horariosBase": "horariosBase",
        "novedades": "novedades",
        "horasExtras": "horasExtras"
    }

    for old_db, tabla in tablas_info.items():
        print(f"Migrando {tabla} desde {old_db}.db...")
        rows = get_all_data_from_old_db(old_db, tabla)
        insert_data_into_new_db(conn, tabla, rows)

    conn.close()
    print("Migración completa.")

    eliminar = input("¿Deseas eliminar los archivos antiguos? (s/n): ").lower()
    if eliminar == 's':
        for old_db in tablas_info.keys():
            path = get_old_db_path(old_db)
            if os.path.exists(path):
                os.remove(path)
                print(f"{path} eliminado.")

if __name__ == "__main__":
    migrate_all_to_new_db()
