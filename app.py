from flask import Flask, render_template, request, jsonify, make_response
import mysql.connector
from flask_cors import CORS, cross_origin
import pusher

# CONEXIÓN A LA BASE DE DATOS (Tus Credenciales)
con = mysql.connector.connect(
    host="185.232.14.52",
    database="u760464709_23005019_bd",
    user="u760464709_23005019_usr",
    password="]0Pxl25["
)

app = Flask(__name__)
CORS(app)

# CONFIGURACIÓN DE PUSHER (Tus Credenciales)
pusher_client = pusher.Pusher(
    app_id='2048531',  # Tu APP_ID
    key='686124f7505c58418f23',    # Tu KEY
    secret='b5add38751c68986fc11',  # Tu SECRET
    cluster='us2',
    ssl=True
)

def pusherAsistencias():
    # Función para notificar cambios en Asistencias (Arquitectura Dirigida por Eventos)
    pusher_client.trigger("canalAsistencias", "eventoAsistencias", {"message": "Nueva asistencia registrada."})
    return make_response(jsonify({}))

# =========================================================================
# RUTAS BASE
# =========================================================================

@app.route("/")
def index():
    if not con.is_connected():
        con.reconnect()
    con.close()
    return render_template("index.html")

@app.route("/app")
def app2():
    if not con.is_connected():
        con.reconnect()
    con.close()
    return render_template("login.html")

@app.route("/iniciarSesion", methods=["POST"])
def iniciarSesion():
    if not con.is_connected():
        con.reconnect()

    usuario    = request.form["txtUsuario"]
    contrasena = request.form["txtContrasena"]

    cursor = con.cursor(dictionary=True)
    # Importante: Asume que tienes la tabla 'usuarios' con 'Nombre_Usuario' y 'Contrasena'
    sql    = "SELECT Id_Usuario FROM usuarios WHERE Nombre_Usuario = %s AND Contrasena = %s"
    val    = (usuario, contrasena)

    cursor.execute(sql, val)
    registros = cursor.fetchall()
    con.close()
    return make_response(jsonify(registros))

# =========================================================================
# MÓDULO EMPLEADOS (N Capas)
# =========================================================================

@app.route("/empleados")
def empleados():
    return render_template("empleados.html")

@app.route("/tbodyEmpleados")
def tbodyEmpleados():
    if not con.is_connected():
        con.reconnect()

    cursor = con.cursor(dictionary=True)
    # READ (LECTURA)
    sql    = "SELECT idEmpleado, nombreEmpleado, numero, fechaIngreso FROM empleados ORDER BY idEmpleado DESC"
    cursor.execute(sql)
    registros = cursor.fetchall()
    con.close()
    return render_template("tbodyEmpleados.html", empleados=registros)

@app.route("/empleado", methods=["POST"])
def guardarEmpleado():
    if not con.is_connected():
        con.reconnect()

    idEmpleado   = request.form.get("idEmpleado", "") # Obtiene ID o cadena vacía si es nuevo
    nombreEmpleado = request.form["nombreEmpleado"]
    numero     = request.form["numero"]
    fechaIngreso   = request.form["fechaIngreso"]
    
    cursor = con.cursor()

    if idEmpleado:
        # UPDATE (ACTUALIZAR)
        sql = "UPDATE empleados SET nombreEmpleado = %s, numero = %s, fechaIngreso = %s WHERE idEmpleado = %s"
        val = (nombreEmpleado, numero, fechaIngreso, idEmpleado)
    else:
        # CREATE (CREAR)
        sql = "INSERT INTO empleados (nombreEmpleado, numero, fechaIngreso) VALUES (%s, %s, %s)"
        val = (nombreEmpleado, numero, fechaIngreso)
    
    cursor.execute(sql, val)
    con.commit()
    con.close()
    return make_response(jsonify({}))

# =========================================================================
# MÓDULO ASISTENCIAS (Dirigida por Eventos)
# =========================================================================

@app.route("/asistencias")
def asistencias():
    return render_template("asistencias.html")

@app.route("/tbodyAsistencias")
def tbodyAsistencias():
    if not con.is_connected():
        con.reconnect()

    cursor = con.cursor(dictionary=True)
    # READ (LECTURA)
    sql    = "SELECT idAsistencia, fecha, comentarios FROM asistencias ORDER BY idAsistencia DESC"
    cursor.execute(sql)
    registros = cursor.fetchall()
    con.close()
    return render_template("tbodyAsistencias.html", asistencias=registros)

@app.route("/asistencia", methods=["POST"])
def guardarAsistencia():
    if not con.is_connected():
        con.reconnect()

    fecha      = request.form["fecha"]
    comentarios = request.form["comentarios"]
    
    cursor = con.cursor()
    # CREATE (CREAR)
    sql    = "INSERT INTO asistencias (fecha, comentarios) VALUES (%s, %s)"
    val    = (fecha, comentarios)
    
    cursor.execute(sql, val)
    con.commit()
    con.close()

    pusherAsistencias() # Emite el evento para la actualización en tiempo real.
    return make_response(jsonify({}))

# =========================================================================
# MÓDULO ASISTENCIASPASES (N Capas)
# Para el READ se muestra la información relacionada con Empleados y Asistencias.
# =========================================================================

@app.route("/asistenciaspases")
def asistenciaspases():
    return render_template("asistenciaspases.html")

@app.route("/tbodyAsistenciasPases")
def tbodyAsistenciasPases():
    if not con.is_connected():
        con.reconnect()

    cursor = con.cursor(dictionary=True)
    # READ (LECTURA) - Une las tablas para mostrar la información completa
    sql = """
    SELECT 
        AP.idAsistenciaPase, 
        E.nombreEmpleado, 
        A.fecha AS fechaAsistencia, 
        AP.estado
    FROM asistenciaspases AS AP
    INNER JOIN empleados AS E ON E.idEmpleado = AP.idEmpleado
    INNER JOIN asistencias AS A ON A.idAsistencia = AP.idAsistencia
    ORDER BY AP.idAsistenciaPase DESC
    """
    cursor.execute(sql)
    registros = cursor.fetchall()
    con.close()
    return render_template("tbodyAsistenciasPases.html", asistenciaspases=registros)

@app.route("/asistenciapase/eliminar", methods=["POST"])
def eliminarAsistenciaPase():
    if not con.is_connected():
        con.reconnect()

    id = request.form["id"]

    cursor = con.cursor(dictionary=True)
    # DELETE (ELIMINAR)
    sql    = "DELETE FROM asistenciaspases WHERE idAsistenciaPase = %s"
    val    = (id,)

    cursor.execute(sql, val)
    con.commit()
    con.close()

    return make_response(jsonify({}))
