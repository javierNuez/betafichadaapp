import sqlite3
import os
from collections import defaultdict, Counter
from statistics import mean
from datetime import datetime, timedelta

def redondear_a_15_minutos(hora):
    minutos = hora.minute
    minutos_redondeados = round(minutos / 15) * 15
    if minutos_redondeados == 60:
        hora_redondeada = hora.replace(hour=(hora.hour + 1) % 24, minute=0)
    else:
        hora_redondeada = hora.replace(minute=minutos_redondeados)
    return f"{hora_redondeada.hour:02d}:{hora_redondeada.minute:02d}"

def obtener_horarios_estimados():
    conn = get_db_connection("fichadas")
    cursor = conn.cursor()
    cursor.execute("SELECT legajo, fechaHora FROM fichadas ORDER BY legajo, fechaHora")
    registros = cursor.fetchall()
    conn.close()

    fichadas_por_legajo = defaultdict(lambda: defaultdict(list))

    for legajo, fechaHora in registros:
        dt = datetime.strptime(fechaHora, "%Y-%m-%d %H:%M:%S.%f")
        dia_semana = dt.weekday() + 1  # lunes = 1, ..., domingo = 7
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

                if duracion >= 6 * 3600:  # mínimo 6 horas
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

        # Verificar si se puede asumir el mismo horario de lunes a viernes
        dias_habiles = [d for d in range(1, 6) if d in horarios_dias]
        if len(dias_habiles) >= 3:
            # Tomar el horario más común entre los días hábiles
            horarios_habiles = [horarios_dias[d] for d in dias_habiles]
            hora_ini_mas_comun = Counter(h[0] for h in horarios_habiles).most_common(1)[0][0]
            hora_fin_mas_comun = Counter(h[1] for h in horarios_habiles).most_common(1)[0][0]

            # Asignar ese horario para lunes a viernes
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
            # Si no hay suficientes datos, usar los horarios reales por día
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

def get_db_connection(tabla):
    ruta = os.path.join("BaseDatos",f"{tabla}.db")
    #ruta = fr"BaseDatos\{tabla}.db"
    db_exists = os.path.exists(ruta)
    conn = sqlite3.connect(ruta)
    if not db_exists:
        print(f"Creando tabla {tabla}...")
        if tabla == "personas":
            create_tables_personas(conn)
        elif tabla == "fichadas":
            create_tables_fichadas(conn)
        elif tabla == "horariosBase":
            create_tables_horariosBase(conn)
        elif tabla == "novedades":
            create_tables_novedades(conn)
        elif tabla == "horasExtras":
            create_tables_horasExtras(conn)
    """        
    else:
        print(f"Base de datos {tabla} encontrada.")
        #check_tables(conn, tabla)
    """    
    conn.row_factory = sqlite3.Row
    return conn

def check_tables(conn, tabla):
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{tabla}';")
        table_exists = cursor.fetchone()
        if table_exists:
            print(f"La tabla '{tabla}' existe.")
        else:
            print(f"La tabla '{tabla}' no se ha creado.")
    except Exception as e:
        print(f"Error verificando tablas: {e}")

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
        print("Tabla 'novedades' verificada o creada exitosamente.")
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

def create_tables_horariosBase(conn):
    try:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS horariosBase (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                legajo INTEGER NOT NULL,
                dia_inicio INTEGER CHECK (dia_inicio BETWEEN 1 AND 7),  -- Día de inicio (1=Lunes, 7=Domingo)
                hora_inicio TEXT NOT NULL CHECK (hora_inicio LIKE '__:__'),  -- Formato 'HH:MM'
                dia_fin INTEGER CHECK (dia_fin BETWEEN 1 AND 7),  -- Día de fin (puede ser el mismo u otro)
                hora_fin TEXT CHECK (hora_fin LIKE '__:__' OR hora_fin IS NULL),  -- Hora fin (puede ser NULL si pasa de medianoche)
                "tipo" TEXT CHECK (LENGTH(tipo) <= 10),  -- Nueva columna de texto (máx. 10 caracteres)
                FOREIGN KEY (legajo) REFERENCES personas(legajo) ON DELETE CASCADE
            )
        ''')
        print("Tabla 'horariosBase' verificada o creada exitosamente.")
        conn.commit()
    except Exception as e:
        print(f"Error creating tables: {e}")

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