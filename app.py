# python.exe -m venv .venv
# cd .venv/Scripts
# activate.bat
# py -m ensurepip --upgrade
# pip install -r requirements.txt

from flask import Flask, render_template, request, jsonify, make_response
import mysql.connector
from flask_cors import CORS, cross_origin
import pusher

# Configuración de la base de datos
db_config = {
    "host": "185.232.14.52",
    "database": "u760464709_23005019_bd",
    "user": "u760464709_23005019_usr",
    "password": "]0Pxl25["
}

app = Flask(__name__)
CORS(app)

# CONFIGURACIÓN DE PUSHER
pusher_client = pusher.Pusher(
    app_id='2048531',
    key='686124f7505c58418f23',
    secret='b5add38751c68986fc11',
    cluster='us2',
    ssl=True
)

def pusherAsistencias():
    pusher_client.trigger("canalAsistencias", "eventoAsistencias", {"message": "Nueva asistencia registrada."})
    return make_response(jsonify({}))

# =========================================================================
# RUTAS BASE
# =========================================================================

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/app")
def app2():
    return render_template("login.html")

@app.route("/iniciarSesion", methods=["POST"])
def iniciarSesion():
    con = mysql.connector.connect(**db_config)
    cursor = con.cursor(dictionary=True)
    
    usuario    = request.form["txtUsuario"]
    contrasena = request.form["txtContrasena"]
    
    sql    = "SELECT Id_Usuario FROM usuarios WHERE Nombre_Usuario = %s AND Contrasena = %s"
    val    = (usuario, contrasena)

    cursor.execute(sql, val)
    registros = cursor.fetchall()
    
    cursor.close()
    con.close()
    
    return make_response(jsonify(registros))

# =========================================================================
# MÓDULO EMPLEADOS
# =========================================================================

@app.route("/empleados")
def empleados():
    return render_template("empleados.html")

@app.route("/tbodyEmpleados")
def tbodyEmpleados():
    con = mysql.connector.connect(**db_config)
    cursor = con.cursor(dictionary=True)

    sql    = "SELECT idEmpleado, nombreEmpleado, numero, fechaIngreso, idDepartamento FROM empleados ORDER BY idEmpleado DESC"
    cursor.execute(sql)
    registros = cursor.fetchall()
    
    cursor.close()
    con.close()
    
    return render_template("tbodyEmpleados.html", empleados=registros)

@app.route("/empleado", methods=["POST"])
def guardarEmpleado():
    con = mysql.connector.connect(**db_config)
    cursor = con.cursor()
    
    idEmpleado     = request.form.get("idEmpleado", "")
    nombreEmpleado = request.form["nombreEmpleado"]
    numero         = request.form["numero"]
    fechaIngreso   = request.form["fechaIngreso"]
    idDepartamento = request.form["idDepartamento"]

    if idEmpleado:
        sql = "UPDATE empleados SET nombreEmpleado = %s, numero = %s, fechaIngreso = %s, idDepartamento = %s WHERE idEmpleado = %s"
        val = (nombreEmpleado, numero, fechaIngreso, idDepartamento, idEmpleado)
    else:
        sql = "INSERT INTO empleados (nombreEmpleado, numero, fechaIngreso, idDepartamento) VALUES (%s, %s, %s, %s)"
        val = (nombreEmpleado, numero, fechaIngreso, idDepartamento)
    
    cursor.execute(sql, val)
    con.commit()

    cursor.close()
    con.close()
    
    return make_response(jsonify({}))

# =========================================================================
# MÓDULO ASISTENCIAS
# =========================================================================

@app.route("/asistencias")
def asistencias():
    return render_template("asistencias.html")

@app.route("/tbodyAsistencias")
def tbodyAsistencias():
    con = mysql.connector.connect(**db_config)
    cursor = con.cursor(dictionary=True)

    sql    = "SELECT idAsistencia, fecha, comentarios FROM asistencias ORDER BY idAsistencia DESC"
    cursor.execute(sql)
    registros = cursor.fetchall()

    cursor.close()
    con.close()
    
    return render_template("tbodyAsistencias.html", asistencias=registros)

@app.route("/asistencia", methods=["POST"])
def guardarAsistencia():
    con = mysql.connector.connect(**db_config)
    cursor = con.cursor()
    
    fecha      = request.form["fecha"]
    comentarios = request.form["comentarios"]
    
    sql    = "INSERT INTO asistencias (fecha, comentarios) VALUES (%s, %s)"
    val    = (fecha, comentarios)
    
    cursor.execute(sql, val)
    con.commit()

    cursor.close()
    con.close()

    pusherAsistencias()
    return make_response(jsonify({}))

# =========================================================================
# MÓDULO ASISTENCIASPASES
# =========================================================================

@app.route("/asistenciaspases")
def asistenciaspases():
    return render_template("asistenciaspases.html")

@app.route("/tbodyAsistenciasPases")
def tbodyAsistenciasPases():
    con = mysql.connector.connect(**db_config)
    cursor = con.cursor(dictionary=True)

    sql = """
    SELECT 
        AP.idAsistenciaPase, E.nombreEmpleado, A.fecha AS fechaAsistencia, AP.estado
    FROM asistenciaspases AS AP
    INNER JOIN empleados AS E ON E.idEmpleado = AP.idEmpleado
    INNER JOIN asistencias AS A ON A.idAsistencia = AP.idAsistencia
    ORDER BY AP.idAsistenciaPase DESC
    """
    cursor.execute(sql)
    registros = cursor.fetchall()
    
    cursor.close()
    con.close()
    
    return render_template("tbodyAsistenciasPases.html", asistenciaspases=registros)

@app.route("/asistenciapase/eliminar", methods=["POST"])
def eliminarAsistenciaPase():
    con = mysql.connector.connect(**db_config)
    cursor = con.cursor()

    id_pase = request.form["id"]
    sql     = "DELETE FROM asistenciaspases WHERE idAsistenciaPase = %s"
    val     = (id_pase,)

    cursor.execute(sql, val)
    con.commit()
    
    cursor.close()
    con.close()

    return make_response(jsonify({}))

# =========================================================================
# MÓDULO DEPARTAMENTOS
# =========================================================================

@app.route("/departamentos")
def departamentos():
    return render_template("departamentos.html")

@app.route("/tbodyDepartamentos")
def tbodyDepartamentos():
    try:
        con = mysql.connector.connect(**db_config)
        if not con.is_connected():
            con.reconnect()

        cursor = con.cursor(dictionary=True)
        sql    = "SELECT idDepartamento, NombreDepartamento, Edificio, Descripcion FROM departamento ORDER BY idDepartamento DESC"
        cursor.execute(sql)
        registros = cursor.fetchall()
        con.close()
        return render_template("tbodyDepartamentos.html", departamentos=registros)
    except Exception as e:
        return f"Error en /tbodyDepartamentos: {str(e)}", 500

