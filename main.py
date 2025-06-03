import sqlite3
from flask import render_template, request, redirect, flash, Flask, jsonify, url_for
import DataBaseManager
import FichadaService
import HoraBaseService
import InformesService
import NovedadService
import PersonaService
import Utility
import qr
import Audio
from datetime import datetime,timedelta
import DataBaseInitializer
from flask import Flask, render_template, request, redirect, flash, url_for
import os






UPLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__))
ALLOWED_EXTENSIONS = {'cro'}
app = Flask(__name__)
audioManager = Audio.AudioManager()

@app.route('/tablaPersonas')
def inicio():
    try:
        personas = DataBaseManager.obtenerPersonas()
        cantidad = len(personas)
        return render_template('registroPersonal.html', personas=personas, cantidad=cantidad)
    except Exception as e:
        print(f"Error: {e}")
        return "Error al conectar con la base de datos"
    finally:
        print("inicio")



@app.route('/editar', methods=['GET', 'POST'])
def editar_persona():
    legajo = request.args.get('legajo', type=int)

    if request.method == 'POST':
        datos = {
            'legajo': request.form['legajo'],
            'nombre': request.form['nombre'],
            'apellido': request.form['apellido'],
            'dni': request.form['dni'],
            'fecha_ingreso': request.form['fecha_ingreso'],
            'fecha_egreso': request.form['fecha_egreso'],
            'sector': request.form['sector'],
            'centro': request.form['centro'],
            'categoria': request.form['categoria'],
            'estado': request.form['estado'],
            'relacion': request.form['relacion'],
        }

        if legajo:
            PersonaService.actualizar_persona(legajo, datos)
        else:
            PersonaService.crear_persona(datos)

        return render_template('editarPersona.html')

    persona = None
    if legajo:
        persona = PersonaService.get_persona_by_legajo(legajo)

    return render_template('editarPersona.html', persona=persona)

@app.route("/api/personas", methods=["GET", "PUT"])
@app.route("/api/personas/<int:persona_id>", methods=["GET", "POST"])
def api_personas(persona_id=None):
    personas = DataBaseManager.obtenerPersonas()

    if request.method == "GET":
        if persona_id is not None:
            persona = next((p for p in personas if p['id'] == persona_id), None)
            if persona:
                return jsonify(dict(persona))  # Convertir a dict si es sqlite3.Row
            return jsonify({"error": "Persona no encontrada"}), 404

        query = request.args.get("q", "").lower()
        if query:
            resultado = [
                dict(p) for p in personas
                if (
                    query in str(p['legajo']).lower()
                    or query in (p['nombre'] or '').lower()
                    or query in (p['apellido'] or '').lower()
                )
            ]
            return jsonify(resultado)

        return jsonify([dict(p) for p in personas])  # Convertir toda la lista

    elif request.method == "POST":
        datos = request.get_json()
        if persona_id:
            PersonaService.actualizar_persona(persona_id, datos)
            return jsonify({"mensaje": "Persona actualizada"}), 200
        else:
            return jsonify({"error": "Falta ID de persona"}), 400

    elif request.method == "PUT":
        datos = request.get_json()
        PersonaService.crear_persona(datos)
        return jsonify({"mensaje": "Persona creada"}), 201




@app.route('/editarHorarioBase')
def ehb():
    try:
        pass
        return render_template('editarHorariosBase.html')
    except Exception as e:
        print(f"Error: {e}")
        return "Error "
    finally:
        print("editarHorarioBase")


@app.route('/tablaFichadas', methods=['GET'])
def ver_fichadas():
    hoy = datetime.now().date() + timedelta(days=1)
    anterior = hoy - timedelta(days=1)
  
    registros = DataBaseManager.obtenerFichadasPorFecha(anterior, hoy)
    
    
    
    return render_template("registroFichadas.html", registros=registros, actual = hoy, anterior = anterior)

@app.route('/buscarFichadas', methods=['POST'])
def buscar_fichadas():
    data = request.get_json()
    try:
        fecha1 = datetime.strptime(data.get("fecha1"), "%Y-%m-%d")
        fecha2 = datetime.strptime(data.get("fecha2"), "%Y-%m-%d") + timedelta(days=1)
        
        registros = DataBaseManager.obtenerFichadasPorFecha(fecha1, fecha2)
        
        lista_dict = [
            {
                "legajo": r["legajo"],
                "nombre": r["nombre"],
                "fechaHora": str(r["fechaHora"])
            } for r in registros
        ]
        
        return jsonify(lista_dict)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Error al conectar con la base de datos"}), 500

@app.route('/tablaNovedades')
def novedades():
    try:
        novedades = DataBaseManager.obtenerNovedades()
        cantidad = len(novedades)
        return render_template('registroNovedades.html', novedades=novedades, cantidad=cantidad)
    except Exception as e:
        print(f"Error: {e}")
        return "Error al conectar con la base de datos"
    finally:
        print("novedades")

@app.route('/add_persona', methods=['GET', 'POST'])
def add_persona():
    if request.method == 'POST':
        legajo = request.form['legajo']
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        dni = request.form['dni']
        fecha_ingreso = request.form['fecha_ingreso']
        fecha_egreso = request.form['fecha_egreso']
        sector = request.form['sector']
        centro = request.form['centro']
        categoria = request.form['categoria']
        if not fecha_egreso:  
            fecha_egreso = None
        else:
            fecha_egreso = datetime.strptime(fecha_egreso, "%Y-%m-%d").date()

        estado = 'Activo' if fecha_egreso is None or fecha_egreso > datetime.today().date() else 'Inactivo'

        try:
            if PersonaService.agregarPersona(legajo, nombre, apellido, dni, fecha_ingreso, fecha_egreso, sector, centro, categoria, estado):
                flash('Persona añadida exitosamente!')
            else:
                flash('Hubo un error!')
            return redirect('/tablaPersonas')
        except Exception as e:
            print(f"Error: {e}")
            flash('Error al añadir persona.')
            return redirect('/add_persona')
        finally:
            print("add_persona")
    return render_template('add_persona.html')

@app.route('/process_input', methods=['POST'])
def process_input():
    try:
        # Obtener y decodificar el QR
        encoded_data = request.form['encoded_data']
        decoded_data = qr.QRProcessor.decodificar(encoded_data)
        dato = qr.QRProcessor.decodificar(decoded_data)
        
        print("QR Decodificado:", dato)

        empresa, legajo, nombre_apellido = dato.split('@')
        encontrado = PersonaService.check_legajo(legajo)
    
        if not encontrado:
            
            return jsonify({'message': 'Error: No registrado', 'legajo': 'Error', 'nombre': 'Error'})

        # Registrar a la persona en la base de datos
        registro_exitoso = FichadaService.registrar_fichada(legajo, nombre_apellido)
        audioManager.reproducir_mensaje(nombre_apellido)
        if not registro_exitoso:
            return jsonify({'message': 'Error en el registro', 'legajo': legajo, 'nombre': nombre_apellido})

        # Responder con la información del usuario
        response = {
            'message': 'Registrado',
            'legajo': legajo,
            'nombre': nombre_apellido
        }

        return jsonify(response)

    except Exception as e:
        print(f"Error: {e}")
        audioManager.reproducir_mensaje("ERROR, No registrado!")
        return jsonify({'message': 'Error al procesar la entrada'}), 500

#informeDiario
from datetime import datetime, timedelta



"""
@app.route('/informeDiario', methods=["GET", "POST"])
def reporteDia():
    if request.method == "POST":
        # 1. Obtener la fecha desde el formulario
        fecha_str = request.form.get("fecha")
        if fecha_str:
            fecha_base = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        else:
            fecha_base = datetime.now().date()

        # 2. Obtener datos desde la base
        personas = DataBaseManager.obtenerPersonasBSAS()
        horariosBase = DataBaseManager.obtenerHorarios()
        fichadas = DataBaseManager.obtenerFichadas()
        novedades = DataBaseManager.obtenerNovedades()

        listaDelDia = []

        for p in personas:
            area = p[7]
            legajo = p[1]
            apellidoNombre = f"{p[3]} {p[2]}"
            fecha_actual_dt = datetime.combine(fecha_base, datetime.min.time())

            horaInicioBase = HoraBaseService.traerHoraInicioBaseDelDia(legajo, fecha_actual_dt, horariosBase)
            horaInicioFichada = FichadaService.traerPrimeraHoraFichadaDelDia(legajo, fecha_actual_dt, fichadas)
            horaFinBase = HoraBaseService.traerHoraFinBaseDelDia(legajo, fecha_actual_dt, horariosBase)
            horaFinFichada = FichadaService.traerUltimaHoraFichadaDelDia(legajo, fecha_actual_dt, fichadas)

            observaciones = ""
            llegadasTarde = Utility.calcularDiferenciaParaLlegadasTarde(horaInicioBase, horaInicioFichada)
            retiroDespuesHora = Utility.calcularDiferenciaParasalidasDespuesHora(horaFinBase, horaFinFichada)
            horasTrabajadas = Utility.calcularHorasTrabajadas(horaInicioFichada, horaFinFichada)

            if horaInicioBase:
                hIB = datetime.strptime(horaInicioBase, "%H:%M").time()

                if horaFinBase:
                    hFB = datetime.strptime(horaFinBase, "%H:%M").time()
                    if hIB > hFB:
                        fecha_siguiente_dt = datetime.combine(fecha_base + timedelta(days=1), datetime.min.time())
                        horaFinBase = HoraBaseService.traerHoraFinBaseDelDia(legajo, fecha_siguiente_dt, horariosBase)
                        horaFinFichada = FichadaService.traerUltimaHoraFichadaDelDia(legajo, fecha_siguiente_dt, fichadas)
                else:
                    fecha_siguiente_dt = datetime.combine(fecha_base + timedelta(days=1), datetime.min.time())
                    horaFinBase = HoraBaseService.traerHoraFinBaseDelDia(legajo, fecha_siguiente_dt, horariosBase)
                    horaFinFichada = FichadaService.traerUltimaHoraFichadaDelDia(legajo, fecha_siguiente_dt, fichadas)

            if horaInicioBase or horaFinBase:
                registro = [
                    area, legajo, apellidoNombre,
                    fecha_base, horaInicioBase, horaInicioFichada,
                    horaFinBase, horaFinFichada, observaciones, llegadasTarde,
                    retiroDespuesHora, horasTrabajadas
                ]
                listaDelDia.append(registro)

    else:
        # Método GET: no se busca información
        fecha_base = datetime.now().date()
        listaDelDia = []

    try:
        return render_template(
            'informeDia.html',
            listaDelDia=listaDelDia,
            fecha=fecha_base.isoformat()
        )
    except Exception as e:
        print(f"Error al renderizar la plantilla: {e}")
        return "Error al conectar con la base de datos"
    finally:
        print("Informe diario ejecutado")

def obtener_fichadas_por_fecha(fecha_str): #para grafico
    if fecha_str:
        fecha_base = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    else:
        fecha_base = datetime.now().date()

    personas = DataBaseManager.obtenerPersonasBSAS()
    horariosBase = DataBaseManager.obtenerHorarios()
    fichadas = DataBaseManager.obtenerFichadas()
    novedades = DataBaseManager.obtenerNovedades()

    listaDelDia = []

    for p in personas:
        area = p[7]
        legajo = p[1]
        apellidoNombre = f"{p[3]} {p[2]}"
        fecha_actual_dt = datetime.combine(fecha_base, datetime.min.time())

        horaInicioBase = HoraBaseService.traerHoraInicioBaseDelDia(legajo, fecha_actual_dt, horariosBase)
        horaInicioFichada = FichadaService.traerPrimeraHoraFichadaDelDia(legajo, fecha_actual_dt, fichadas)
        horaFinBase = HoraBaseService.traerHoraFinBaseDelDia(legajo, fecha_actual_dt, horariosBase)
        horaFinFichada = FichadaService.traerUltimaHoraFichadaDelDia(legajo, fecha_actual_dt, fichadas)

        observaciones = ""
        llegadasTarde = Utility.calcularDiferenciaParaLlegadasTarde(horaInicioBase, horaInicioFichada)
        retiroDespuesHora = Utility.calcularDiferenciaParasalidasDespuesHora(horaFinBase, horaFinFichada)
        horasTrabajadas = Utility.calcularHorasTrabajadas(horaInicioFichada, horaFinFichada)

        if horaInicioBase:
            hIB = datetime.strptime(horaInicioBase, "%H:%M").time()
            if horaFinBase:
                hFB = datetime.strptime(horaFinBase, "%H:%M").time()
                if hIB > hFB:
                    fecha_siguiente_dt = datetime.combine(fecha_base + timedelta(days=1), datetime.min.time())
                    horaFinBase = HoraBaseService.traerHoraFinBaseDelDia(legajo, fecha_siguiente_dt, horariosBase)
                    horaFinFichada = FichadaService.traerUltimaHoraFichadaDelDia(legajo, fecha_siguiente_dt, fichadas)
            else:
                fecha_siguiente_dt = datetime.combine(fecha_base + timedelta(days=1), datetime.min.time())
                horaFinBase = HoraBaseService.traerHoraFinBaseDelDia(legajo, fecha_siguiente_dt, horariosBase)
                horaFinFichada = FichadaService.traerUltimaHoraFichadaDelDia(legajo, fecha_siguiente_dt, fichadas)

        if horaInicioBase or horaFinBase:
            registro = {
                "sector": area,
                "legajo": legajo,
                "nombre": apellidoNombre,
                "fecha": fecha_base.isoformat(),
                "hora_inicio_base": horaInicioBase,
                "hora_inicio_fichada": horaInicioFichada,
                "hora_fin_base": horaFinBase,
                "hora_fin_fichada": horaFinFichada,
                "observacion": observaciones,
                "llegadas_tarde": llegadasTarde,
                "retiro_despues": retiroDespuesHora,
                "horas_trabajadas": horasTrabajadas
            }
            listaDelDia.append(registro)

    return listaDelDia, fecha_base
"""
@app.route('/informeDiario', methods=["GET", "POST"])
def informe_diario():
    fecha = datetime.now().date()
    listaDelDia = []

    if request.method == 'POST':
        fecha = request.form.get('fecha')
        if fecha:
            conn = DataBaseInitializer.get_db_connection()
            cursor = conn.cursor()

            query = '''WITH fichadas_filtradas AS (
    SELECT 
        p.legajo,
        DATE(f.fechaHora) AS fecha,
        time(f.fechaHora) AS hora,
        f.fechaHora,
        hb.hora_inicio,
        hb.hora_fin,
        ABS(strftime('%s', time(f.fechaHora)) - strftime('%s', '1970-01-01 ' || hb.hora_inicio)) AS diff_inicio,
        ABS(strftime('%s', time(f.fechaHora)) - strftime('%s', '1970-01-01 ' || hb.hora_fin)) AS diff_fin
    FROM fichadas f
    JOIN personas p ON p.legajo = f.legajo
    LEFT JOIN horariosBase hb 
        ON p.legajo = hb.legajo
        AND datetime(f.fechaHora) >= datetime(hb.fecha_hora_desde)
        AND datetime(f.fechaHora) <= datetime(IFNULL(hb.fecha_hora_hasta, f.fechaHora))
    WHERE p.sector != 'Fuerza de ventas' 
      AND p.legajo < 4000
      AND DATE(f.fechaHora) = ?
),
clasificadas AS (
    SELECT 
        legajo,
        fecha,
        hora_inicio,
        hora_fin,
        CASE 
            WHEN COUNT(*) = 1 THEN 
                CASE 
                    WHEN MIN(diff_inicio) <= MIN(diff_fin) THEN MIN(hora)
                    ELSE NULL
                END
            ELSE MIN(hora)
        END AS entrada,
        CASE 
            WHEN COUNT(*) = 1 THEN 
                CASE 
                    WHEN MIN(diff_fin) < MIN(diff_inicio) THEN MAX(hora)
                    ELSE NULL
                END
            ELSE MAX(hora)
        END AS salida
    FROM fichadas_filtradas
    GROUP BY legajo, fecha
)
SELECT 
    p.sector AS area,
    p.legajo,
    p.apellido || ', ' || p.nombre AS nombre_completo,
    c.fecha,
    c.hora_inicio,
    c.entrada,
    c.hora_fin,
    c.salida,

    -- Observaciones con motivo si hay novedad
    CASE 
        WHEN c.entrada IS NOT NULL AND c.salida IS NOT NULL AND c.entrada = c.salida THEN 'Aún en la empresa'
        WHEN c.salida < c.hora_fin THEN 'Con ret. anticipado'
        WHEN c.entrada IS NOT NULL AND c.salida IS NULL THEN 'Dentro de la empresa'
        WHEN c.entrada IS NULL AND c.salida IS NOT NULL THEN 'Revisar'
        WHEN c.entrada > c.hora_inicio THEN 'Tarde'
        ELSE '-'
    END 
    || 
    CASE 
        WHEN n.motivo IS NOT NULL THEN ' ' || n.motivo
        ELSE ''
    END AS observaciones,

    CASE 
        WHEN c.entrada > c.hora_inicio THEN 
            printf('%02d:%02d', 
                (strftime('%s', c.entrada) - strftime('%s', c.hora_inicio)) / 3600,
                ((strftime('%s', c.entrada) - strftime('%s', c.hora_inicio)) % 3600) / 60
            )
        ELSE '-' 
    END AS llegada_tarde,

    CASE 
        WHEN c.salida > c.hora_fin THEN 
            printf('%02d:%02d', 
                (strftime('%s', c.salida) - strftime('%s', c.hora_fin)) / 3600,
                ((strftime('%s', c.salida) - strftime('%s', c.hora_fin)) % 3600) / 60
            )
        ELSE '-' 
    END AS retiro_despues_hora,

    CASE 
        WHEN c.entrada IS NOT NULL AND c.salida IS NOT NULL THEN 
            ROUND((strftime('%s', c.salida) - strftime('%s', c.entrada)) / 3600.0, 2)
        ELSE 0
    END AS horas_trabajadas,

    p.relacion

FROM clasificadas c
JOIN personas p ON p.legajo = c.legajo
LEFT JOIN novedades n 
    ON n.legajo = c.legajo 
    AND DATE(c.fecha) BETWEEN DATE(n.fecha_inicio) AND DATE(n.fecha_fin)
WHERE p.sector != 'Fuerza de ventas' 
  AND p.legajo < 4000
  AND p.legajo != 1231
ORDER BY c.fecha, p.legajo;

'''

            params = (fecha,)
            cursor.execute(query, params)
            listaDelDia = cursor.fetchall()
            
            conn.close()

    return render_template('informeDia.html', fecha=fecha, listaDelDia=listaDelDia)


from flask import request, render_template
from datetime import datetime, date

@app.route('/ausentes', methods=["GET", "POST"])
def reporte_ausentes():
    # Obtener la fecha desde el formulario o usar la fecha actual
    fecha_str = request.form.get("fecha") if request.method == "POST" else None
    fecha_base = datetime.strptime(fecha_str, "%Y-%m-%d").date() if fecha_str else date.today()

    try:
        lista_del_dia = obtener_ausentes_del_dia(fecha_base)
        return render_template(
            'ausentes.html',
            listaDelDia=lista_del_dia,
            fecha=fecha_base.isoformat()
        )
    except Exception as e:
        print(f"Error al renderizar la plantilla: {e}")
        return "Error al conectar con la base de datos"
    finally:
        print("Informe diario ejecutado")


def obtener_ausentes_del_dia(fecha_base):
    conn = DataBaseInitializer.get_db_connection()
    cursor = conn.cursor()

    query = """SELECT 
    DATE(?) AS fecha,
    p.sector AS area,
    p.legajo,
    p.apellido || ' ' || p.nombre AS apellidoNombre,
    COALESCE((
        SELECT 
            n.motivo || ' (desde ' || DATE(n.fecha_inicio) || ' hasta ' || DATE(n.fecha_fin) || ')'
        FROM novedades n
        WHERE n.legajo = p.legajo
          AND DATE(?) BETWEEN DATE(n.fecha_inicio) AND DATE(n.fecha_fin)
    ), 'Ausente') AS observaciones,
    p.relacion
FROM personas p
WHERE p.legajo <= 4000
  AND p.sector != 'Fuerza de ventas'
  AND NOT EXISTS (
      SELECT 1
      FROM fichadas f
      WHERE f.legajo = p.legajo
        AND DATE(f.fechaHora) = DATE(?)
  );



    """

    cursor.execute(query, (fecha_base, fecha_base,fecha_base))
    resultados = cursor.fetchall()
    conn.close()
    return resultados




@app.route('/scanner')
def scanner():
    # Obtener la dirección IP del cliente
    ip_cliente = request.remote_addr
    # Obtener el nombre del equipo cliente usando la dirección IP
    #nombre_equipo_cliente = obtener_nombre_equipo(ip_cliente)
    nombre_equipo_cliente = Utility.obtener_nombre_equipo(ip_cliente)
    
         
    try:
        return render_template('scannerServidor.html', equipo=nombre_equipo_cliente)
    except Exception as e:
        print(f"Error al renderizar la plantilla: {e}")
        return "Error al conectar con la base de datos"
    finally:
        print("scanner ejecutado")



@app.route("/add_horarios_base_semanal", methods=["GET", "POST"])
def agregar_horarios():
    legajos = obtener_legajos() 
    tipo = "Semanal"
    if request.method == "POST":
        
        legajo = request.form["legajo"]
        dias = request.form.getlist("dias")  # Lista con los días seleccionados (1 al 7)
        hora_inicio = request.form["hora_inicio"]
        hora_fin = request.form["hora_fin"] if request.form["hora_fin"] else None  # Puede ser NULL
        fecha_hora_desde = request.form["fecha_hora_desde"].replace("T", " ")
        fecha_hora_hasta = request.form["fecha_hora_hasta"].replace("T", " ")
        

        resultado = HoraBaseService.insertarHorasSemanal(legajo,dias,hora_inicio,hora_fin,tipo,fecha_hora_desde,fecha_hora_hasta)
        if resultado["success"]:
            flash(resultado["message"], "success")
            return redirect(url_for("horarios"))  # Evita resubmisión al refrescar
        else:
            flash(resultado["message"], "danger")
        
        return redirect("/registroHorariosBase")

    return render_template("add_horarios_base_semanal.html", legajos = legajos)

from flask import flash, redirect, url_for

@app.route("/add_horarios_base", methods=["GET", "POST"])
def horarios():
    legajos = obtener_legajos()
    tipo = "Rotativo"
    if request.method == "POST":
        legajo = request.form["legajo"]
        dia_inicio = request.form["dia_inicio"]
        hora_inicio = request.form["hora_inicio"]
        dia_fin = request.form.get("dia_fin", None)
        hora_fin = request.form.get("hora_fin", None)
        fecha_hora_desde = request.form.get("fecha_hora_desde", None)
        fecha_hora_hasta = request.form.get("fecha_hora_hasta", None)

        if not dia_fin:
            dia_fin = None
        if not hora_fin:
            hora_fin = None

        resultado = HoraBaseService.insertar_horario_base(
            legajo, dia_inicio, hora_inicio, tipo, dia_fin, hora_fin, fecha_hora_desde, fecha_hora_hasta
        )

        if resultado["success"]:
            flash(resultado["message"], "success")
            return redirect(url_for("horarios"))  # Evita resubmisión al refrescar
        else:
            flash(resultado["message"], "danger")

    return render_template("add_horario_base.html", legajos=legajos)


def es_vigente(horario):
    # fecha_hora_desde y fecha_hora_hasta vienen como string, convertir a datetime
    formato = "%Y-%m-%d %H:%M:%S"
    ahora = datetime.now()

    try:
        desde = datetime.strptime(horario["fecha_hora_desde"], formato)
        hasta = datetime.strptime(horario["fecha_hora_hasta"], formato)
    except Exception as e:
        return False  # En caso de error, no marcar vigente

    return desde <= ahora <= hasta

@app.route("/registroHorariosBase")
def ver_horarios():
    conn = DataBaseInitializer.get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
    SELECT 
      hb.id,
      p.nombre || ' ' || p.apellido AS nombreApellido,
      hb.legajo,
      hb.dia_inicio,
      hb.hora_inicio,
      hb.dia_fin,
      hb.hora_fin,
      hb.tipo,
      hb.fecha_hora_desde,
      hb.fecha_hora_hasta,
      CASE 
        WHEN datetime('now','localtime') BETWEEN hb.fecha_hora_desde AND hb.fecha_hora_hasta THEN 1
        ELSE 0
      END AS vigente
    FROM horariosBase hb
    JOIN personas p ON hb.legajo = p.legajo
    WHERE hb.legajo <= 4000
      AND p.sector != 'Fuerza de ventas'
    ORDER BY hb.legajo, hb.fecha_hora_hasta DESC;
    """)

    rows = cursor.fetchall()
    horarios = []

    for row in rows:
        horario = dict(row)
        # Convertimos vigente a booleano para más claridad en el template
        horario["vigente"] = bool(horario["vigente"])
        horarios.append(horario)
    conn.close()
    return render_template("registroHorariosBase.html", horarios=horarios)


@app.route("/editarHorario/<int:id>", methods=["GET", "POST"])
def editar_horario(id):
    conexion = DataBaseInitializer.get_db_connection()
    cursor = conexion.cursor()

    if request.method == "POST":
        legajo = request.form["legajo"]
        dia_inicio = request.form["dia_inicio"]
        hora_inicio = request.form["hora_inicio"]
        dia_fin = request.form["dia_fin"]
        hora_fin = request.form["hora_fin"]
        tipo = request.form["tipo"]

        cursor.execute("""
            UPDATE horariosBase 
            SET legajo=?, dia_inicio=?, hora_inicio=?, dia_fin=?, hora_fin=?, tipo=? 
            WHERE id=?
        """, (legajo, dia_inicio, hora_inicio, dia_fin, hora_fin, tipo, id))
        conexion.commit()
        conexion.close()
        return redirect("/registroHorariosBase")
    
    cursor.execute("SELECT * FROM horariosBase WHERE id = ?", (id,))
    horario = cursor.fetchone()
    conexion.close()
    return render_template("editarHorario.html", horario=horario)


@app.route("/api/horarios/<int:legajo>", methods=["GET"])
def get_horarios_de_legajo(legajo):
    conexion = DataBaseInitializer.get_db_connection()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM horariosBase WHERE legajo = ?", (legajo,))
    rows = cursor.fetchall()
    conexion.close()

    horarios = []
    for row in rows:
        horarios.append({
            "id": row[0],
            "legajo": row[1],
            "dia_inicio": row[2],
            "hora_inicio": row[3],
            "dia_fin": row[4],
            "hora_fin": row[5],
            "tipo": row[6],
            "fecha_hora_desde": row[7],
            "fecha_hora_hasta": row[8]
        })

    if not horarios:
        return jsonify({"error": "No se encontraron horarios para este legajo"}), 404

    return jsonify(horarios)


@app.route("/api/horario/<int:id>", methods=["POST"])
def actualizar_horario(id):
    data = request.json
    conexion = DataBaseInitializer.get_db_connection()
    cursor = conexion.cursor()

    # Convertir T a espacio
    fecha_desde = data["fecha_hora_desde"].replace("T", " ") if data["fecha_hora_desde"] else None
    fecha_hasta = data["fecha_hora_hasta"].replace("T", " ") if data["fecha_hora_hasta"] else None

    cursor.execute("""
        UPDATE horariosBase 
        SET hora_inicio=?, hora_fin=?, tipo=?, fecha_hora_desde=?, fecha_hora_hasta=?
        WHERE id=?
    """, (
        data["hora_inicio"],
        data["hora_fin"],
        data["tipo"],
        fecha_desde,
        fecha_hasta,
        id
    ))

    conexion.commit()
    conexion.close()
    print(data["hora_inicio"], data["hora_fin"], data["tipo"], fecha_desde, fecha_hasta, id)
    return jsonify({"success": True})



def obtener_legajos():
    personas = DataBaseManager.obtenerPersonas()
    legajos = []
    for l in personas:
        legajos.append(l[1])
    return legajos








@app.route('/generar_fichadas', methods=["GET", "POST"])
def generador_fichadas():
    msj = ""
    if request.method == "POST":
        try:
            # Validación de datos
            legajo = int(request.form["legajo"])
            inicio = request.form["inicio"]
            fin = request.form["fin"]
            horaInicio = datetime.strptime(inicio, "%H:%M")
            horaFin = datetime.strptime(fin, "%H:%M")
            puntualidad = request.form["tipo"]
            
            if puntualidad not in ['puntual', 'regular', 'impuntual']:
                raise ValueError("Tipo de puntualidad inválido")
            
            # Generar y agregar fichadas a la base de datos
            fichadas = FichadaService.generar_fichadas(legajo, horaInicio, horaFin, puntualidad)
            FichadaService.agregar_fichadas_a_bd(fichadas)
            
            msj = f"Las fichadas han sido agregadas a la base de datos. Total de fichadas: {len(fichadas)}"
        except Exception as e:
            msj = f"Error: {str(e)}"
    
    return render_template("generador.html", mensaje=msj)

@app.route('/generar_fichada_manual', methods=["GET", "POST"])
def generador_fichada_manual():
    msj = ""
    if request.method == "POST":
        try:
            # Validación de datos
            fechaHora = request.form["fechaHora"]+":00.1"
            
            legajo = int(request.form["legajo"])
            nombre = request.form["nombre"]
            fh = datetime.strptime(fechaHora, "%Y-%m-%dT%H:%M:%S.%f")
            FichadaService.registrar_fichada_manual(legajo, nombre, fh)
            msj = f"La fichada han sido agregada en la base de datos."
        except Exception as e:
            msj = f"Error: {str(e)}"
    
    return render_template("fichada_manual.html", mensaje=msj)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=["GET",'POST'])
def upload_file():
    if request.method == "GET":
        return render_template('upload.html')
    if request.method == "POST":
        if 'file' not in request.files:
            flash('No se envió ningún archivo')
            return redirect(request.url)
    
        file = request.files['file']

        if file.filename == '':
            flash('No se seleccionó ningún archivo')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = 'Fichadas.cro'  # Nombre fijo o usa file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            flash('Archivo subido exitosamente')
            if Utility.traerNuevasFichadas():
                flash('Se actualizaron las fichadas exitosamente')
            return render_template('upload.html')
        else:
            flash('Tipo de archivo no permitido. Solo se aceptan archivos .cro')
            return render_template('upload.html')

@app.route('/')
def menu():
    #Utility.generarFichadas() #genera archivo resultado paso 1
    #Utility.procesar_fichadas_desde_csv() #genera fichadas desde resultado a bd fichadas paso 2
    #PersonaService.importar_personas_desde_api() #Se utiliza para traer los datos de Internos
    #HoraBaseService.insertarHorasEstimadas()
    #HoraBaseService.cargar_horarios_desde_excel()
    #PersonaService.delete_personas_by_legajos([2428,2183,2184,2330,2410,2570,2589,2590,2592,2845,2869])#para eliminar legajos de Personal BD
    #Utility.actualizar_personas_desde_excel()
    #Utility.actualizarCategorias()
    #Utility.agregar_campos_caducidad()
    return render_template("index.html")

@app.route('/informe_llegadas')
def informe_llegadas():
    return render_template('llegadas_tarde.html')


# Función auxiliar para parsear fechas con o sin microsegundos
def parse_fecha_hora(fecha_str):
    try:
        return datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        return datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")

from datetime import datetime
from flask import render_template

@app.route('/llegadas_tarde_hoy', methods=['GET', 'POST'])
def llegadas_tardes_hoy():
    
    if request.method == 'POST':
        fecha = request.form['fecha']
    else:
        fecha_actual = datetime.now().date()  # Esto da un objeto date
        fecha = fecha_actual.isoformat()  # 'YYYY-MM-DD'
    registros = []
    # Convertimos la lista de listas en un diccionario
    legajosConRelacion = {legajo: relacion for legajo, relacion in PersonaService.obtenerLegajoRelacion()}
    horarios = DataBaseManager.obtenerHorarios(fecha)
    fichadasDia = DataBaseManager.obtenerFichadasPorFechaDia(fecha)
    primeras_fichadas = {}

    for f in fichadasDia:
        legajo = f["legajo"]

        if legajo in legajosConRelacion:
            fila_dict = dict(f)

            # Parsear la fechaHora
            if isinstance(fila_dict["fechaHora"], str):
                try:
                    fila_dict["fechaHora"] = datetime.strptime(fila_dict["fechaHora"], "%Y-%m-%d %H:%M:%S.%f")
                except ValueError:
                    fila_dict["fechaHora"] = datetime.strptime(fila_dict["fechaHora"], "%Y-%m-%d %H:%M:%S")

            fila_dict["fechaHora"] = fila_dict["fechaHora"].replace(second=0, microsecond=0)

            if legajo not in primeras_fichadas or fila_dict["fechaHora"] < primeras_fichadas[legajo]["fechaHora"]:
                primeras_fichadas[legajo] = fila_dict

    for legajo, fichada in primeras_fichadas.items():
        fecha_fichada = fichada["fechaHora"].date()
        fichada["horarioEsperado"] = HoraBaseService.traerHoraInicioBaseDelDia(legajo, fecha_fichada, horarios)
        fichada["relacion"] = legajosConRelacion[legajo]  # ← aquí se agrega la relación

    registros = list(primeras_fichadas.values())
    
    return render_template('llegadas_tarde_hoy.html', registros=registros,fecha = fecha )


def parse_fecha_hora(fechaHora_str):
    try:
        return datetime.strptime(fechaHora_str, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        return datetime.strptime(fechaHora_str, "%Y-%m-%d %H:%M:%S")


def formatear_minutos(minutos):
    horas = minutos // 60
    mins = minutos % 60
    if horas > 0:
        return f"{horas}h {mins}min"
    return f"{mins}min"

@app.route('/llegadas_tarde', methods=['GET'])
def llegadas_tarde():
    try:
        # Obtener parámetros desde query string
        legajo = int(request.args.get('legajo', 0))
        tolerancia = int(request.args.get('tolerancia', 0)) + 1
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')

        if not fecha_inicio or not fecha_fin:
            return jsonify({"error": "Faltan fechas inicio o fin"}), 400

        fi = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        ff = datetime.strptime(fecha_fin, "%Y-%m-%d")

        conn = DataBaseInitializer.get_db_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 1) Obtener datos de persona
        cursor.execute("SELECT nombre, apellido FROM personas WHERE legajo = ?", (legajo,))
        persona = cursor.fetchone()
        if persona is None:
            return jsonify({"error": "Legajo no encontrado"}), 404

        # 2) Obtener novedades para el legajo
        cursor.execute("""
            SELECT fecha_inicio, fecha_fin
            FROM novedades
            WHERE legajo = ?
        """, (legajo,))
        novedades = cursor.fetchall()

        # 3) Obtener horarios vigentes dentro del rango y para cada día de la semana
        cursor.execute("""
            SELECT dia_inicio, hora_inicio, fecha_hora_desde, fecha_hora_hasta
            FROM horariosBase
            WHERE legajo = ?
            AND fecha_hora_desde <= ?
            AND fecha_hora_hasta >= ?
        """, (legajo, fecha_fin, fecha_inicio))
        horarios = cursor.fetchall()

        # 4) Obtener fichadas en rango para el legajo
        cursor.execute("""
            SELECT fechaHora
            FROM fichadas
            WHERE legajo = ?
            AND fechaHora BETWEEN ? AND ?
        """, (legajo, fecha_inicio + " 00:00:00", fecha_fin + " 23:59:59"))
        fichadas = cursor.fetchall()

        conn.close()

        # Convertir novedades y horarios a listas de dict para fácil manejo
        novedades_list = [dict(n) for n in novedades]
        horarios_list = [dict(h) for h in horarios]
        fichadas_list = [dict(f) for f in fichadas]

        llegadas_tarde = []
        total_minutos_demorados = 0

        dias_rango = [fi + timedelta(days=i) for i in range((ff - fi).days + 1)]

        for dia in dias_rango:
            fecha_str = dia.strftime("%Y-%m-%d")
            dia_semana = dia.isoweekday()

            # Saltear si hay novedad activa para ese día
            if any(n["fecha_inicio"] <= fecha_str <= n["fecha_fin"] for n in novedades_list):
                continue

            # Filtrar horarios para el día de la semana
            horarios_del_dia = [h for h in horarios_list if h["dia_inicio"] == dia_semana]
            if not horarios_del_dia:
                continue

            hora_esperada_str = horarios_del_dia[0]["hora_inicio"]
            hora_esperada_dt = datetime.strptime(f"{fecha_str} {hora_esperada_str}", "%Y-%m-%d %H:%M")
            hora_tolerada_dt = hora_esperada_dt + timedelta(minutes=tolerancia)

            # Filtrar fichadas de ese día
            fichadas_del_dia = [f for f in fichadas_list if f["fechaHora"].startswith(fecha_str)]
            if not fichadas_del_dia:
                continue

            fichada_entrada = min([parse_fecha_hora(f["fechaHora"]) for f in fichadas_del_dia])

            if fichada_entrada > hora_tolerada_dt:
                minutos_demorado = int((fichada_entrada - hora_esperada_dt).total_seconds() // 60)
                total_minutos_demorados += minutos_demorado
                llegadas_tarde.append({
                    "fecha": fecha_str,
                    "hora_prevista": hora_esperada_dt.strftime("%H:%M"),
                    "hora_fichada": fichada_entrada.strftime("%H:%M"),
                    "minutos_demorado": minutos_demorado
                })

        return jsonify({
            "legajo": legajo,
            "nombre": f'{persona["nombre"]} {persona["apellido"]}',
            "cantidad_llegadas_tarde": len(llegadas_tarde),
            "total_minutos_demorados": total_minutos_demorados,
            "total_demorado_formateado": formatear_minutos(total_minutos_demorados),
            "detalle": llegadas_tarde
        })

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 400


@app.route('/novedad', methods=['GET', 'POST'])
def novedad():
    if request.method == 'POST':
        legajo = request.form['legajo']
        fecha_inicio = request.form['fecha_inicio']
        fecha_fin = request.form['fecha_fin']
        hora_inicio = request.form['hora_inicio']
        hora_fin = request.form['hora_fin']
        motivo = request.form['motivo']
        print("Novedad:", legajo, motivo)
        try:
            NovedadService.cargar_novedad(int(legajo), fecha_inicio, fecha_fin, hora_inicio, hora_fin, motivo)
            return redirect(url_for('add_novedad'))  # o a una página de confirmación
        except Exception as e:
            return f"Error al cargar la novedad: {e}", 400

    return render_template('add_novedad.html')

@app.route('/add_novedad', methods=['POST'])
def agregar_novedad():
    if request.method == 'POST':
        legajo = request.form['legajo']
        fecha_inicio = request.form['fecha_inicio']
        fecha_fin = request.form['fecha_fin']
        hora_inicio = request.form['hora_inicio']
        hora_fin = request.form['hora_fin']
        motivo = request.form['motivo']
        print("Novedad:", legajo, motivo)
        if motivo == "Otro":
            motivo = request.form.get('otro_motivo', '')

        try:
            NovedadService.cargar_novedad(int(legajo), fecha_inicio, fecha_fin, hora_inicio, hora_fin, motivo)
            
        except Exception as e:
            return f"Error al cargar la novedad: {e}", 400

    return redirect("/tablaNovedades")

@app.route('/comprobarBase/<base>')
def comprobarBases(base):
    conn = DataBaseInitializer.get_db_connection(base)
    cursor = conn.cursor()
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{base}';")
    table_exists = cursor.fetchone()
    conn.close()
    if table_exists:
        return f"La tabla '{base}' existe."
    else:
        return f"La tabla '{base}' no se ha creado."


@app.route('/api/persona')
def obtener_persona_api():
    legajo = request.args.get('legajo', type=int)
    nombre = request.args.get('nombre', type=str)

    persona = None
    if legajo:
        persona = PersonaService.get_persona_by_legajo(legajo)
    elif nombre:
        persona = PersonaService.get_persona_by_nombre(nombre)

    if persona:
        return jsonify(persona)
    else:
        return jsonify({'error': 'Persona no encontrada'}), 404

@app.route('/borrarHoras/<int:legajo>')
def borrar_horarios_por_legajo(legajo):
    conexion = DataBaseInitializer.get_db_connection()
    cursor = conexion.cursor()

    cursor.execute("DELETE FROM horariosBase WHERE legajo = ?", (legajo,))
    conexion.commit()
    conexion.close()

    return jsonify({"success": True, "mensaje": f"Se eliminaron todos los horarios del legajo {legajo}."})

@app.route('/grafico')
def grafico():
    print("Inicio Proceso:", datetime.today())
    fecha_desde_str = request.args.get('fecha_desde')
    fecha_hasta_str = request.args.get('fecha_hasta')
    tipo = request.args.get('tipo')    # Lo seguimos recibiendo para mantener la URL
    sector = request.args.get('sector')  # Igual

    # Si no vienen fechas, por defecto uso el día anterior
    if not fecha_desde_str or not fecha_hasta_str:
        ayer = datetime.today().date() - timedelta(days=1)
        fecha_desde = ayer
        #fecha_hasta = ayer + timedelta(days=1)
        fecha_hasta = ayer
        return redirect(url_for('grafico', 
                                fecha_desde=fecha_desde.isoformat(),
                                fecha_hasta=fecha_hasta.isoformat(),
                                tipo=tipo or '',
                                sector=sector or ''))

    try:
        fecha_desde = datetime.strptime(fecha_desde_str, "%Y-%m-%d").date()
        fecha_hasta = datetime.strptime(fecha_hasta_str, "%Y-%m-%d").date()
    except ValueError:
        ayer = datetime.today().date() - timedelta(days=1)
        fecha_desde = ayer
        fecha_hasta = ayer + timedelta(days=1)
        return redirect(url_for('grafico', 
                                fecha_desde=fecha_desde.isoformat(),
                                fecha_hasta=fecha_hasta.isoformat(),
                                tipo=tipo or '',
                                sector=sector or ''))

    # Llamamos sin filtros tipo y sector, solo fechas
    fichadas = obtener_datos_fichadas(fecha_desde, fecha_hasta, tipo, sector)

    print("Fin Proceso:", datetime.today())
    return render_template(
        "grafico.html", 
        fichadas=fichadas, 
        fecha_desde=fecha_desde.isoformat(), 
        fecha_hasta=fecha_hasta.isoformat(),
        tipo=tipo,
        sector=sector
    )

def obtener_datos_fichadas(fecha_desde_str, fecha_hasta_str, tipo=None, sector=None):
    conn = DataBaseInitializer.get_db_connection()
    cursor = conn.cursor()

    query = '''
        SELECT 
            p.legajo,
            p.apellido || ', ' || p.nombre AS nombre,
            p.sector,
            p.relacion AS tipo_personal,
            ROUND(SUM(sub.horas_trabajadas), 2) AS horas_trabajadas
        FROM personas p
        JOIN (
            SELECT 
                f.legajo,
                DATE(f.fechaHora) AS fecha,
                CASE 
                    WHEN COUNT(*) > 1 THEN 
                        (JULIANDAY(MAX(f.fechaHora)) - JULIANDAY(MIN(f.fechaHora))) * 24
                    ELSE 0
                END AS horas_trabajadas
            FROM fichadas f
            WHERE DATE(f.fechaHora) BETWEEN ? AND ?
            GROUP BY f.legajo, DATE(f.fechaHora)
        ) sub ON p.legajo = sub.legajo
        WHERE p.sector != 'Fuerza de ventas'
          AND p.legajo < 4000
    '''

    params = [fecha_desde_str, fecha_hasta_str]

    if tipo:
        query += " AND p.relacion = ?"
        params.append(tipo)

    if sector:
        query += " AND p.sector = ?"
        params.append(sector)

    query += '''
        GROUP BY p.legajo
        HAVING horas_trabajadas > 0
        ORDER BY horas_trabajadas DESC;
    '''

    cursor.execute(query, params)
    resultados = cursor.fetchall()
    conn.close()

    datos = []
    for fila in resultados:
        datos.append({
            'legajo': fila[0],
            'nombre': fila[1],
            'sector': fila[2],
            'tipo_personal': fila[3],
            'horas_trabajadas': fila[4]
        })

    return datos




@app.route("/eliminar_novedad/<int:id>", methods=["DELETE"])
def eliminar_novedad(id):
    resultado = NovedadService.eliminar_novedad_por_id(id)
    return jsonify({"message": resultado["message"]}), 200 if resultado["success"] else 404




if __name__ == '__main__':
    app.config['SECRET_KEY'] = 'vigoray'
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.run(host="0.0.0.0", port=5000, debug=True)
    
