# python.exe -m venv .venv
# cd .venv/Scripts
# activate.bat
# py -m ensurepip --upgrade
# pip install -r requirements.txt

from flask import Flask, render_template, request, jsonify, make_response, session, redirect, url_for
import mysql.connector
import datetime
import pytz
from flask_cors import CORS
import pusher

app = Flask(__name__)
CORS(app)

# Configuración de la base de datos
def get_db_connection():
    return mysql.connector.connect(
        host="185.232.14.52",
        database="u760464709_23005019_bd",
        user="u760464709_23005019_usr",
        password="]0Pxl25["
    )

# Configuración de Pusher
def get_pusher_client():
    return pusher.Pusher(
        app_id="2048531",
        key="686124f7505c58418f23",
        secret="b5add38751c68986fc11",
        cluster="us2",
        ssl=True
    )

# Middleware para verificar autenticación
@app.before_request
def check_auth():
    # Rutas que no requieren autenticación
    public_routes = ['index', 'app2', 'iniciarSesion', 'logout']
    
    if request.endpoint not in public_routes and 'user_id' not in session:
        return redirect(url_for('app2'))

# Rutas de autenticación
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/app")
def app2():
    return render_template("login.html")

@app.route("/iniciarSesion", methods=["POST"])
def iniciarSesion():
    con = get_db_connection()
    usuario = request.form["txtUsuario"]
    contrasena = request.form["txtContrasena"]

    cursor = con.cursor(dictionary=True)
    sql = "SELECT idEmpleado, nombreEmpleado FROM empleados WHERE numero = %s AND nombreEmpleado = %s"
    val = (usuario, contrasena)

    cursor.execute(sql, val)
    user = cursor.fetchone()
    con.close()

    if user:
        session['user_id'] = user['idEmpleado']
        session['user_name'] = user['nombreEmpleado']
        return make_response(jsonify({"success": True}))
    else:
        return make_response(jsonify({"success": False, "message": "Credenciales inválidas"}))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('index'))

# Módulo de Empleados (Arquitectura en Capas)
@app.route("/empleados")
def empleados():
    return render_template("empleados.html")

@app.route("/tbodyEmpleados")
def tbodyEmpleados():
    con = get_db_connection()
    cursor = con.cursor(dictionary=True)
    sql = "SELECT * FROM empleados ORDER BY idEmpleado DESC"
    cursor.execute(sql)
    registros = cursor.fetchall()
    con.close()
    return render_template("tbodyEmpleados.html", empleados=registros)

@app.route("/empleado", methods=["POST"])
def guardarEmpleado():
    con = get_db_connection()
    id = request.form.get("id")
    nombre = request.form["nombre"]
    numero = request.form["numero"]
    fechaIngreso = request.form["fechaIngreso"]
    
    cursor = con.cursor()

    if id:
        sql = "UPDATE empleados SET nombreEmpleado = %s, numero = %s, fechaIngreso = %s WHERE idEmpleado = %s"
        val = (nombre, numero, fechaIngreso, id)
    else:
        sql = "INSERT INTO empleados (nombreEmpleado, numero, fechaIngreso) VALUES (%s, %s, %s)"
        val = (nombre, numero, fechaIngreso)
    
    cursor.execute(sql, val)
    con.commit()
    con.close()
    
    # Notificar a los clientes via Pusher
    pusher_client = get_pusher_client()
    pusher_client.trigger('canal-empleados', 'evento-empleados', {'message': 'actualizar'})
    
    return make_response(jsonify({"success": True}))

@app.route("/empleado/<int:id>")
def obtenerEmpleado(id):
    con = get_db_connection()
    cursor = con.cursor(dictionary=True)
    sql = "SELECT * FROM empleados WHERE idEmpleado = %s"
    cursor.execute(sql, (id,))
    empleado = cursor.fetchone()
    con.close()
    return make_response(jsonify(empleado))

@app.route("/empleado/eliminar", methods=["POST"])
def eliminarEmpleado():
    con = get_db_connection()
    id = request.form["id"]
    cursor = con.cursor()
    sql = "DELETE FROM empleados WHERE idEmpleado = %s"
    cursor.execute(sql, (id,))
    con.commit()
    con.close()
    
    # Notificar a los clientes via Pusher
    pusher_client = get_pusher_client()
    pusher_client.trigger('canal-empleados', 'evento-empleados', {'message': 'actualizar'})
    
    return make_response(jsonify({"success": True}))

# Módulo de Asistencias (Arquitectura Orientada a Servicios)
@app.route("/asistencias")
def asistencias():
    return render_template("asistencias.html")

@app.route("/tbodyAsistencias")
def tbodyAsistencias():
    con = get_db_connection()
    cursor = con.cursor(dictionary=True)
    sql = """
    SELECT a.idAsistencia, a.fecha, a.comentarios, 
           GROUP_CONCAT(CONCAT(e.nombreEmpleado, ' (', ap.estado, ')') SEPARATOR ', ') as detalles
    FROM asistencias a
    LEFT JOIN asistenciaspases ap ON a.idAsistencia = ap.idAsistencia
    LEFT JOIN empleados e ON ap.idEmpleado = e.idEmpleado
    GROUP BY a.idAsistencia
    ORDER BY a.fecha DESC
    """
    cursor.execute(sql)
    registros = cursor.fetchall()
    con.close()
    return render_template("tbodyAsistencias.html", asistencias=registros)

@app.route("/asistencia", methods=["POST"])
def guardarAsistencia():
    con = get_db_connection()
    fecha = request.form["fecha"]
    comentarios = request.form["comentarios"]
    empleados = request.form.getlist("empleados[]")
    estados = request.form.getlist("estados[]")
    
    cursor = con.cursor()
    
    # Insertar asistencia
    sql = "INSERT INTO asistencias (fecha, comentarios) VALUES (%s, %s)"
    val = (fecha, comentarios)
    cursor.execute(sql, val)
    id_asistencia = cursor.lastrowid
    
    # Insertar detalles de asistencia
    for i in range(len(empleados)):
        if empleados[i] and estados[i]:
            sql = "INSERT INTO asistenciaspases (idEmpleado, idAsistencia, estado) VALUES (%s, %s, %s)"
            val = (empleados[i], id_asistencia, estados[i])
            cursor.execute(sql, val)
    
    con.commit()
    con.close()
    
    return make_response(jsonify({"success": True}))

# Módulo de Reportes (Arquitectura Serverless - Simulada)
@app.route("/reportes")
def reportes():
    return render_template("reportes.html")

@app.route("/generarReporte", methods=["POST"])
def generarReporte():
    con = get_db_connection()
    tipo_reporte = request.form["tipo_reporte"]
    fecha_inicio = request.form["fecha_inicio"]
    fecha_fin = request.form["fecha_fin"]
    
    cursor = con.cursor(dictionary=True)
    
    if tipo_reporte == "asistencias":
        sql = """
        SELECT e.nombreEmpleado, 
               COUNT(CASE WHEN ap.estado = 'A' THEN 1 END) as asistencias,
               COUNT(CASE WHEN ap.estado = 'R' THEN 1 END) as retardos,
               COUNT(CASE WHEN ap.estado = 'F' THEN 1 END) as faltas
        FROM empleados e
        LEFT JOIN asistenciaspases ap ON e.idEmpleado = ap.idEmpleado
        LEFT JOIN asistencias a ON ap.idAsistencia = a.idAsistencia
        WHERE a.fecha BETWEEN %s AND %s
        GROUP BY e.idEmpleado
        """
        val = (fecha_inicio, fecha_fin)
    else:
        return make_response(jsonify({"error": "Tipo de reporte no válido"}))
    
    cursor.execute(sql, val)
    resultados = cursor.fetchall()
    con.close()
    
    return make_response(jsonify(resultados))

if __name__ == "__main__":
    app.run(debug=True)
