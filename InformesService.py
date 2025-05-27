from datetime import datetime

import DataBaseManager


def obtener_datos_para_informe(legajo, fecha_inicio, fecha_fin):
    # Asegurar que fecha_inicio y fecha_fin sean de tipo date
    if isinstance(fecha_inicio, datetime):
        fecha_inicio_dt = fecha_inicio.date()
    else:
        fecha_inicio_dt = fecha_inicio

    if isinstance(fecha_fin, datetime):
        fecha_fin_dt = fecha_fin.date()
    else:
        fecha_fin_dt = fecha_fin

    # Personas
    personas = DataBaseManager.obtenerPersonas()

    # Fichadas
    fichadas = DataBaseManager.obtenerFichadas()

    # Horarios
    horarios = DataBaseManager.obtenerHorarios()

    # Novedades
    novedades = DataBaseManager.obtenerNovedades()

    # Filtrar persona (legajo)
    persona = next((p for p in personas if p["legajo"] == legajo), None)

    if not persona:
        raise ValueError(f"No se encontró la persona con legajo {legajo}")

    # Filtrar fichadas dentro del rango
    fichadas_filtradas = []
    for f in fichadas:
        if f["legajo"] == legajo:
            try:
                fecha_fichada = datetime.strptime(f["fechaHora"], "%Y-%m-%d %H:%M:%S.%f").date()
                
            except ValueError:
                fecha_fichada = datetime.strptime(f["fechaHora"], "%Y-%m-%d %H:%M:%S").date()
            
            if fecha_inicio_dt <= fecha_fichada <= fecha_fin_dt:
                fichadas_filtradas.append(f)
                
    # Filtrar horarios del legajo
    
    horarios_legajo = [h for h in horarios if h["legajo"] == legajo]

    if not horarios_legajo:
        raise ValueError(f"No se encontraron Horarios para el legajo: {legajo}")
    # Filtrar novedades dentro del rango
    novedades_legajo = []
    for n in novedades:
        if n["legajo"] == legajo:
            fecha_inicio_n = datetime.strptime(n["fecha_inicio"], "%Y-%m-%d").date()
            fecha_fin_n = datetime.strptime(n["fecha_fin"], "%Y-%m-%d").date()
            if not (fecha_fin_n < fecha_inicio_dt or fecha_inicio_n > fecha_fin_dt):
                novedades_legajo.append({
                    **n,
                    "fecha_inicio": fecha_inicio_n,
                    "fecha_fin": fecha_fin_n
                })

    return {
        "persona": persona,
        "fichadas": fichadas_filtradas,
        "horarios": horarios_legajo,
        "novedades": novedades_legajo
    }