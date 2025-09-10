from flask import Flask, render_template, request, jsonify, make_response, session, redirect, url_for
import mysql.connector
import datetime
import pytz
from flask_cors import CORS
import pusher

app = Flask(__name__)
CORS(app)

# Configuración de la base de datos
db_config = {
    "host": "185.232.14.52",
    "database": "u760464709_23005019_bd",
    "user": "u760464709_23005019_usr",
    "password": "]0Pxl25["
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

# Configuración de Pusher
def get_pusher_client():
    return pusher.Pusher(
        app_id='2048531',
        key='686124f7505c58418f23',
        secret='b5add38751c68986fc11',
        cluster='us2',
        ssl=True
    )

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/app")
def app_route():
    return render_template("login.html")

@app.route("/iniciarSesion", methods=["POST"])
def iniciarSesion():
    usuario = request.form["txtUsuario"]
    contrasena = request.form["txtContrasena"]
    
    # En un caso real, verificarías contra la base de datos
    # Aquí un ejemplo simplificado
    if usuario == "admin" and contrasena == "admin":
        session['usuario'] = usuario
        return make_response(jsonify([{'Id_Usuario': 1}]))
    else:
        return make_response(jsonify([]))

@app.route("/cerrarSesion")
def cerrarSesion():
    session.pop('usuario', None)
    return redirect(url_for('app_route'))

# Módulo de Empleados (Arquitectura en Capas)
@app.route("/empleados")
def empleados():
    if 'usuario' not in session:
        return redirect(url_for('app_route'))
    return render_template("empleados.html")

@app.route("/tbodyEmpleados")
def tbodyEmpleados():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    sql = """
    SELECT idEmpleado, nombreEmpleado, numero, fechaIngreso
    FROM empleados
    ORDER BY idEmpleado DESC
    """
    
    cursor.execute(sql)
    registros = cursor.fetchall()
    
    # Formatear fechas
    for registro in registros:
        if registro['fechaIngreso']:
            registro['fechaIngreso'] = registro['fechaIngreso'].strftime("%d/%m/%Y")
    
    conn.close()
    return render_template("tbodyEmpleados.html", empleados=registros)

@app.route("/empleado", methods=["POST"])
def guardarEmpleado():
    id = request.form.get("id", "")
    nombre = request.form["nombre"]
    numero = request.form["numero"]
    fecha_ingreso = request.form["fechaIngreso"]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if id:
        sql = """
        UPDATE empleados
        SET nombreEmpleado = %s, numero = %s, fechaIngreso = %s
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
    conn.commit()
    conn.close()
    
    # Notificar a los clientes via Pusher
    pusher_client = get_pusher_client()
    pusher_client.trigger("canalEmpleados", "eventoEmpleados", {"message": "Actualizar"})
    
    return make_response(jsonify({"status": "success"}))

@app.route("/empleado/<int:id>")
def obtenerEmpleado(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    sql = "SELECT * FROM empleados WHERE idEmpleado = %s"
    cursor.execute(sql, (id,))
    empleado = cursor.fetchone()
    
    if empleado and empleado['fechaIngreso']:
        empleado['fechaIngreso'] = empleado['fechaIngreso'].strftime("%Y-%m-%d")
    
    conn.close()
    return make_response(jsonify(empleado))

@app.route("/empleado/eliminar", methods=["POST"])
def eliminarEmpleado():
    id = request.form["id"]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    sql = "DELETE FROM empleados WHERE idEmpleado = %s"
    cursor.execute(sql, (id,))
    conn.commit()
    conn.close()
    
    pusher_client = get_pusher_client()
    pusher_client.trigger("canalEmpleados", "eventoEmpleados", {"message": "Actualizar"})
    
    return make_response(jsonify({"status": "success"}))

# Módulo de Asistencias (Arquitectura Orientada a Servicios)
@app.route("/asistencias")
def asistencias():
    if 'usuario' not in session:
        return redirect(url_for('app_route'))
    return render_template("asistencias.html")

@app.route("/tbodyAsistencias")
def tbodyAsistencias():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    sql = """
    SELECT a.idAsistencia, a.fecha, a.comentarios,
           COUNT(ap.idAsistenciaPase) as total_empleados,
           SUM(CASE WHEN ap.estado = 'A' THEN 1 ELSE 0 END) as asistencias,
           SUM(CASE WHEN ap.estado = 'R' THEN 1 ELSE 0 END) as retardos,
           SUM(CASE WHEN ap.estado = 'F' THEN 1 ELSE 0 END) as faltas
    FROM asistencias a
    LEFT JOIN asistenciaspases ap ON a.idAsistencia = ap.idAsistencia
    GROUP BY a.idAsistencia
    ORDER BY a.fecha DESC
    """
    
    cursor.execute(sql)
    registros = cursor.fetchall()
    
    for registro in registros:
        if registro['fecha']:
            registro['fecha'] = registro['fecha'].strftime("%d/%m/%Y")
    
    conn.close()
    return render_template("tbodyAsistencias.html", asistencias=registros)

@app.route("/asistencia", methods=["POST"])
def guardarAsistencia():
    fecha = request.form["fecha"]
    comentarios = request.form.get("comentarios", "")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    sql = "INSERT INTO asistencias (fecha, comentarios) VALUES (%s, %s)"
    val = (fecha, comentarios)
    
    cursor.execute(sql, val)
    conn.commit()
    asistencia_id = cursor.lastrowid
    conn.close()
    
    # Obtener todos los empleados para crear registros en asistenciaspases
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT idEmpleado FROM empleados")
    empleados = cursor.fetchall()
    
    for empleado in empleados:
        cursor.execute(
            "INSERT INTO asistenciaspases (idEmpleado, idAsistencia, estado) VALUES (%s, %s, %s)",
            (empleado['idEmpleado'], asistencia_id, 'A')  # Por defecto 'A' (Asistencia)
        )
    
    conn.commit()
    conn.close()
    
    pusher_client = get_pusher_client()
    pusher_client.trigger("canalAsistencias", "eventoAsistencias", {"message": "Actualizar"})
    
    return make_response(jsonify({"status": "success", "id": asistencia_id}))

@app.route("/asistencia/<int:id>")
def obtenerAsistencia(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    sql = "SELECT * FROM asistencias WHERE idAsistencia = %s"
    cursor.execute(sql, (id,))
    asistencia = cursor.fetchone()
    
    if asistencia and asistencia['fecha']:
        asistencia['fecha'] = asistencia['fecha'].strftime("%Y-%m-%d")
    
    conn.close()
    return make_response(jsonify(asistencia))

@app.route("/asistencia/eliminar", methods=["POST"])
def eliminarAsistencia():
    id = request.form["id"]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Primero eliminar los registros relacionados en asistenciaspases
    sql = "DELETE FROM asistenciaspases WHERE idAsistencia = %s"
    cursor.execute(sql, (id,))
    
    # Luego eliminar la asistencia
    sql = "DELETE FROM asistencias WHERE idAsistencia = %s"
    cursor.execute(sql, (id,))
    
    conn.commit()
    conn.close()
    
    pusher_client = get_pusher_client()
    pusher_client.trigger("canalAsistencias", "eventoAsistencias", {"message": "Actualizar"})
    
    return make_response(jsonify({"status": "success"}))

# Módulo de AsistenciasPases (Arquitectura Dirigida por Eventos)
@app.route("/asistenciaspases/<int:id_asistencia>")
def asistenciaspases(id_asistencia):
    if 'usuario' not in session:
        return redirect(url_for('app_route'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Obtener información de la asistencia
    sql = "SELECT * FROM asistencias WHERE idAsistencia = %s"
    cursor.execute(sql, (id_asistencia,))
    asistencia = cursor.fetchone()
    
    if asistencia and asistencia['fecha']:
        asistencia['fecha'] = asistencia['fecha'].strftime("%d/%m/%Y")
    
    # Obtener los pases de asistencia
    sql = """
    SELECT ap.*, e.nombreEmpleado, e.numero
    FROM asistenciaspases ap
    INNER JOIN empleados e ON ap.idEmpleado = e.idEmpleado
    WHERE ap.idAsistencia = %s
    ORDER BY e.nombreEmpleado
    """
    cursor.execute(sql, (id_asistencia,))
    pases = cursor.fetchall()
    
    conn.close()
    
    return render_template("asistenciaspases.html", asistencia=asistencia, pases=pases)

@app.route("/asistenciaspase", methods=["POST"])
def actualizarAsistenciaPase():
    id_pase = request.form["idPase"]
    estado = request.form["estado"]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    sql = "UPDATE asistenciaspases SET estado = %s WHERE idAsistenciaPase = %s"
    cursor.execute(sql, (estado, id_pase))
    conn.commit()
    conn.close()
    
    pusher_client = get_pusher_client()
    pusher_client.trigger("canalAsistenciasPases", "eventoAsistenciasPases", {"message": "Actualizar"})
    
    return make_response(jsonify({"status": "success"}))

if __name__ == "__main__":
    app.run(debug=True)
