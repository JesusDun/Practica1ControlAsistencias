con = mysql.connector.connect(
    host="185.232.14.52",
    database="u760464709_23005019_bd",
    user="u760464709_23005019_usr",
    password="]0Pxl25["
)

# ===== MÓDULO EMPLEADOS (Arquitectura N-capas) =====
@app.route("/empleados")
def empleados():
    return render_template("empleados.html")

@app.route("/tbodyEmpleados")
def tbodyEmpleados():
    if not con.is_connected():
        con.reconnect()

    cursor = con.cursor(dictionary=True)
    sql = """
    SELECT idEmpleado, nombreEmpleado, numero, fechaIngreso
    FROM empleados
    ORDER BY idEmpleado DESC
    LIMIT 10 OFFSET 0
    """

    cursor.execute(sql)
    registros = cursor.fetchall()
    
    # Formatear fechas
    for registro in registros:
        if registro["fechaIngreso"]:
            registro["fechaIngreso"] = registro["fechaIngreso"].strftime("%Y-%m-%d")
    
    return render_template("tbodyEmpleados.html", empleados=registros)

@app.route("/empleado", methods=["POST"])
def guardarEmpleado():
    if not con.is_connected():
        con.reconnect()

    id = request.form.get("id", "")
    nombre = request.form["nombre"]
    numero = request.form["numero"]
    fecha_ingreso = request.form["fecha_ingreso"]
    
    cursor = con.cursor()

    if id:
        sql = """
        UPDATE empleados
        SET nombreEmpleado = %s,
            numero = %s,
            fechaIngreso = %s
        WHERE idEmpleado = %s
        """
        val = (nombre, numero, fecha_ingreso, id)
    else:
        sql = """
        INSERT INTO empleados (nombreEmpleado, numero, fechaIngreso)
        VALUES (%s, %s, %s)
        """
        val = (nombre, numero, fecha_ingreso)
    
    cursor.execute(sql, val)
    con.commit()
    con.close()

    return make_response(jsonify({"status": "success"}))

@app.route("/empleado/<int:id>")
def obtenerEmpleado(id):
    if not con.is_connected():
        con.reconnect()

    cursor = con.cursor(dictionary=True)
    sql = """
    SELECT idEmpleado, nombreEmpleado, numero, fechaIngreso
    FROM empleados
    WHERE idEmpleado = %s
    """
    val = (id,)

    cursor.execute(sql, val)
    registro = cursor.fetchone()
    
    if registro and registro["fechaIngreso"]:
        registro["fechaIngreso"] = registro["fechaIngreso"].strftime("%Y-%m-%d")
    
    con.close()
    return make_response(jsonify(registro))

@app.route("/empleado/eliminar", methods=["POST"])
def eliminarEmpleado():
    if not con.is_connected():
        con.reconnect()

    id = request.form["id"]
    cursor = con.cursor()
    sql = "DELETE FROM empleados WHERE idEmpleado = %s"
    val = (id,)

    cursor.execute(sql, val)
    con.commit()
    con.close()

    return make_response(jsonify({"status": "success"}))

# ===== MÓDULO ASISTENCIAS (Arquitectura N-capas) =====
@app.route("/asistencias")
def asistencias():
    return render_template("asistencias.html")

@app.route("/tbodyAsistencias")
def tbodyAsistencias():
    if not con.is_connected():
        con.reconnect()

    cursor = con.cursor(dictionary=True)
    sql = """
    SELECT idAsistencia, fecha, comentarios
    FROM asistencias
    ORDER BY fecha DESC, idAsistencia DESC
    LIMIT 10 OFFSET 0
    """

    cursor.execute(sql)
    registros = cursor.fetchall()
    
    for registro in registros:
        if registro["fecha"]:
            registro["fecha"] = registro["fecha"].strftime("%Y-%m-%d")
    
    return render_template("tbodyAsistencias.html", asistencias=registros)

@app.route("/asistencia", methods=["POST"])
def guardarAsistencia():
    if not con.is_connected():
        con.reconnect()

    fecha = request.form["fecha"]
    comentarios = request.form.get("comentarios", "")
    
    cursor = con.cursor()
    sql = """
    INSERT INTO asistencias (fecha, comentarios)
    VALUES (%s, %s)
    """
    val = (fecha, comentarios)
    
    cursor.execute(sql, val)
    con.commit()
    con.close()

    return make_response(jsonify({"status": "success"}))

# ===== MÓDULO ASISTENCIASPASES (Arquitectura N-capas) =====
@app.route("/asistenciaspases")
def asistenciaspases():
    return render_template("asistenciaspases.html")

@app.route("/tbodyAsistenciasPases")
def tbodyAsistenciasPases():
    if not con.is_connected():
        con.reconnect()

    cursor = con.cursor(dictionary=True)
    sql = """
    SELECT ap.idAsistenciaPase, e.nombreEmpleado, a.fecha, ap.estado
    FROM asistenciaspases ap
    INNER JOIN empleados e ON ap.idEmpleado = e.idEmpleado
    INNER JOIN asistencias a ON ap.idAsistencia = a.idAsistencia
    ORDER BY a.fecha DESC, ap.idAsistenciaPase DESC
    LIMIT 10 OFFSET 0
    """

    cursor.execute(sql)
    registros = cursor.fetchall()
    
    for registro in registros:
        if registro["fecha"]:
            registro["fecha"] = registro["fecha"].strftime("%Y-%m-%d")
    
    return render_template("tbodyAsistenciasPases.html", asistenciaspases=registros)

@app.route("/asistenciapase", methods=["POST"])
def guardarAsistenciaPase():
    if not con.is_connected():
        con.reconnect()

    id_empleado = request.form["id_empleado"]
    id_asistencia = request.form["id_asistencia"]
    estado = request.form["estado"]
    
    cursor = con.cursor()
    sql = """
    INSERT INTO asistenciaspases (idEmpleado, idAsistencia, estado)
    VALUES (%s, %s, %s)
    """
    val = (id_empleado, id_asistencia, estado)
    
    cursor.execute(sql, val)
    con.commit()
    con.close()

    return make_response(jsonify({"status": "success"}))

# ===== MÓDULO REPORTES (Arquitectura Orientada a Servicios) =====
class ReporteService:
    def __init__(self, db_connection):
        self.con = db_connection
    
    def obtener_reporte_asistencias(self, fecha_inicio, fecha_fin):
        """Servicio para obtener reporte de asistencias por rango de fechas"""
        if not self.con.is_connected():
            self.con.reconnect()

        cursor = self.con.cursor(dictionary=True)
        sql = """
        SELECT a.fecha, 
               COUNT(ap.idAsistenciaPase) as total_registros,
               SUM(CASE WHEN ap.estado = 'A' THEN 1 ELSE 0 END) as asistencias,
               SUM(CASE WHEN ap.estado = 'R' THEN 1 ELSE 0 END) as retardos,
               SUM(CASE WHEN ap.estado = 'F' THEN 1 ELSE 0 END) as faltas
        FROM asistencias a
        LEFT JOIN asistenciaspases ap ON a.idAsistencia = ap.idAsistencia
        WHERE a.fecha BETWEEN %s AND %s
        GROUP BY a.fecha
        ORDER BY a.fecha
        """
        val = (fecha_inicio, fecha_fin)

        cursor.execute(sql, val)
        registros = cursor.fetchall()
        
        for registro in registros:
            if registro["fecha"]:
                registro["fecha"] = registro["fecha"].strftime("%Y-%m-%d")
        
        return registros

# Instancia del servicio
reporte_service = ReporteService(con)

@app.route("/reportes")
def reportes():
    return render_template("reportes.html")

@app.route("/reporte/asistencias", methods=["GET"])
def generar_reporte_asistencias():
    fecha_inicio = request.args.get("fecha_inicio")
    fecha_fin = request.args.get("fecha_fin")
    
    if not fecha_inicio or not fecha_fin:
        return make_response(jsonify({"error": "Fechas requeridas"}), 400)
    
    try:
        reporte = reporte_service.obtener_reporte_asistencias(fecha_inicio, fecha_fin)
        return make_response(jsonify(reporte))
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)
