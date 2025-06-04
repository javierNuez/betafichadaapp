from datetime import date, datetime, timedelta
import random
import DataBaseInitializer
import DataBaseManager
import HoraBaseService
import PersonaService

rangoHoras = 3 #rango de horas para tomar una fichada válida.

def registrar_fichada(legajo, nombre):
    try:
        conn = DataBaseInitializer.get_db_connection()
        cursor = conn.cursor()
        fechaHora = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        cursor.execute('''
            INSERT INTO fichadas (legajo, nombre, fechaHora) 
            VALUES (?, ?, ?)
        ''', (legajo, nombre, fechaHora))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al registrar fichada: {e}")
        return False
    finally:
        conn.close()

def registrar_fichada_manual(legajo, nombre, fechaHora):
    try:
        conn = DataBaseInitializer.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO fichadas (legajo, nombre, fechaHora) 
            VALUES (?, ?, ?)
        ''', (legajo, nombre, fechaHora))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al registrar fichada: {e}")
        return False
    finally:
        conn.close()


def registrar_fichada_manual_sin_repetir(legajo, nombre, fechaHora):
    try:
        conn = DataBaseInitializer.get_db_connection()
        cursor = conn.cursor()

        # Verificar si ya existe una fichada con el mismo legajo y fechaHora
        cursor.execute('''
            SELECT 1 FROM fichadas WHERE legajo = ? AND fechaHora = ?
        ''', (legajo, fechaHora))
        existe = cursor.fetchone()

        if existe:
            #print("Fichada ya registrada.")
            return False

        # Si no existe, insertar la nueva fichada
        cursor.execute('''
            INSERT INTO fichadas (legajo, nombre, fechaHora) 
            VALUES (?, ?, ?)
        ''', (legajo, nombre, fechaHora))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al registrar fichada: {e}")
        return False
    finally:
        conn.close()


#Trae la primera fichada del día.
def traerPrimeraHoraFichadaDelDia(legajo, diaActual, fichadas):
    horaFichada = None
    i = 0
    encontrado = False
    
    while i < len(fichadas) and encontrado != True:
        f = fichadas[i]
        
        horaBaseFichadas = datetime.strptime(f[3], "%Y-%m-%d %H:%M:%S.%f")
        
        if f[1] == legajo and diaActual.date() == horaBaseFichadas.date() and esFichadaValidaI(legajo,diaActual, horaBaseFichadas, rangoHoras):
        #if f[1] == legajo and diaActual.date() == horaBaseFichadas.date():    
            horaFichada = horaBaseFichadas.time().strftime("%H:%M")
            #print ("fichada primera",horaFichada)
            encontrado = True
            
        i += 1
    return horaFichada

def esFichadaValidaF(legajo, diaActual, horaFichada, rangoHoras):
    esValida = False
    horasReales = DataBaseManager.obtenerHorarios()
    horaBaseFin = HoraBaseService.traerHoraFinBaseDelDia(legajo, diaActual, horasReales)
    if horaBaseFin != None:
        hora_obj = datetime.strptime(horaBaseFin, '%H:%M').time()
        horaFichada_obj = horaFichada.time()
        esValida = esta_en_rango(hora_obj, horaFichada_obj, rangoHoras)
        #print(f"Esta en rango {legajo} salida?: ", esValida)
    return esValida

def esFichadaValidaI(legajo, diaActual, horaFichada, rangoHoras):
    esValida = False
    horasReales = DataBaseManager.obtenerHorarios()
    horaBaseInicio = HoraBaseService.traerHoraInicioBaseDelDia(legajo, diaActual, horasReales)
    if horaBaseInicio != None:
        hora_obj = datetime.strptime(horaBaseInicio, '%H:%M').time()
        horaFichada_obj = horaFichada.time()
        esValida = esta_en_rango(hora_obj, horaFichada_obj, rangoHoras)#hora registrada en la base, hora fichada, rango.
        #print(f"Esta en rango {legajo} salida?: ", esValida)
    return esValida

def traerUltimaHoraFichadaDelDia(legajo, diaActual, fichadas):
    ultimaHora = None
    
    for f in fichadas:
        horaBaseFichadas = datetime.strptime(f[3], "%Y-%m-%d %H:%M:%S.%f")
        diaSolo = comvierteDateTiemeADate(diaActual)
        if f[1] == legajo and horaBaseFichadas.date() == diaSolo  and esFichadaValidaF(legajo,diaActual, horaBaseFichadas, rangoHoras):
        #if f[1] == legajo and fA.date() == diaActual.date():    
            ultimaHora = str(horaBaseFichadas.time())[:5]
            
    return ultimaHora

def comvierteDateTiemeADate(fecha):
    if isinstance(fecha, datetime):
        return fecha.date()
    elif isinstance(fecha, date):
        return fecha
    else:
        raise ValueError("El valor no es un objeto date o datetime")

def esta_en_rango(hora_referencia, hora_real, rango_hora):
    """
    Verifica si hora_real está dentro del rango (en minutos) antes o después de hora_referencia.
    
    Parámetros:
        hora_referencia (datetime.time): Hora base.
        hora_real (datetime.time): Hora a verificar fichada.
        rango_hora (int): Rango en minutos permitido antes o después.
    
    Retorna:
        bool: True si está en rango, False si no.
    """
    # Convertimos todo a datetime con una fecha fija para poder restar
    fecha_ficticia = datetime(2000, 1, 1)  # cualquier fecha
    dt_referencia = datetime.combine(fecha_ficticia, hora_referencia)
    dt_real = datetime.combine(fecha_ficticia, hora_real)
    
    diferencia = abs((dt_real - dt_referencia).total_seconds() / 60)  # diferencia en minutos
    
    return diferencia <= rango_hora*60 #se multiplica por 60 pq el calculo es en minutos.

def generar_fichadas(legajo, horaInicio, horaFin, puntualidad):
    # Obtener la fecha actual
    fecha_actual = datetime.now()
    
    # Lista para almacenar las fichadas
    fichadas = []
    
    # Definir los rangos de ajuste según la puntualidad
    if puntualidad == 'puntual':
        ajuste_inicio = (0, 5)  # Ajuste de 0 a 5 minutos
        ajuste_fin = (0, 5)
    elif puntualidad == 'regular':
        ajuste_inicio = (5, 15)  # Ajuste de 5 a 15 minutos
        ajuste_fin = (5, 15)
    elif puntualidad == 'impuntual':
        ajuste_inicio = (15, 30)  # Ajuste de 15 a 30 minutos
        ajuste_fin = (15, 30)
    else:
        raise ValueError("Puntualidad debe ser 'puntual', 'regular' o 'impuntual'")
    
    # Iterar desde la fecha actual hasta 30 días atrás
    for i in range(30):
        # Calcular la fecha
        fecha = fecha_actual - timedelta(days=i)
        
        # Verificar si la fecha es sábado o domingo
        if fecha.weekday() >= 5:
            continue
        
        # Crear las fichadas para la fecha con ajustes según la puntualidad
        fichada_inicio = fecha.replace(hour=horaInicio.hour, minute=horaInicio.minute) + timedelta(minutes=random.randint(*ajuste_inicio))
        fichada_fin = fecha.replace(hour=horaFin.hour, minute=horaFin.minute) + timedelta(minutes=random.randint(*ajuste_fin))
        
        # Agregar las fichadas a la lista
        fichadas.append((legajo, fichada_inicio))
        fichadas.append((legajo, fichada_fin))
    
    return fichadas

def agregar_fichadas_a_bd(fichadas):
    conn = DataBaseInitializer.get_db_connection()
    cursor = conn.cursor()
    
    # Crear la tabla si no existe
    cursor.execute('''CREATE TABLE IF NOT EXISTS fichadas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        legajo INTEGER,
                        nombre TEXT,
                        fechaHora DATETIME)''')
    
    # Insertar las fichadas en la base de datos
    for fichada in fichadas:
        nombre_completo = PersonaService.obtener_nombre_por_legajo(fichada[0])
        if not nombre_completo:
            raise ValueError(f"No se encontro persona {fichada[0]} en la base de datos.")
        cursor.execute("INSERT INTO fichadas (legajo, nombre, fechaHora) VALUES (?, ?, ?)", (fichada[0], nombre_completo, fichada[1]))
    
    conn.commit()
    conn.close()
    