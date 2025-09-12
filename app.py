# python.exe -m venv .venv
# cd .venv/Scripts
# activate.bat
# py -m ensurepip --upgrade
# pip install -r requirements.txt
# pip install bcrypt

from flask import Flask, render_template, request, jsonify, make_response
import mysql.connector
from flask_cors import CORS, cross_origin
import pusher
import bcrypt

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

app.secret_key = "pruebaLLaveSecreta_123"

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
    usuario_ingresado = request.form.get("txtUsuario")
    contrasena_ingresada = request.form.get("txtContrasena")

    if not usuario_ingresado or not contrasena_ingresada:
        return make_response(jsonify([]), 400)  # Datos incompletos

    con = mysql.connector.connect(**db_config)
    cursor = con.cursor(dictionary=True)

    sql = "SELECT idUsuario, username, password FROM usuarios WHERE username = %s"
    cursor.execute(sql, (usuario_ingresado,))
    registro_usuario = cursor.fetchone()
    con.close()

    usuario_encontrado = None
    if registro_usuario:
        hash_guardado = registro_usuario['password'].encode('utf-8')
        contrasena_ingresada_bytes = contrasena_ingresada.encode('utf-8')

        if bcrypt.checkpw(contrasena_ingresada_bytes, hash_guardado):
            # ✅ Guardamos la sesión
            session["idUsuario"] = registro_usuario["idUsuario"]
            session["username"] = registro_usuario["username"]
            usuario_encontrado = [{"Id_Usuario": registro_usuario['idUsuario']}]

    return make_response(jsonify(usuario_encontrado or []))

@app.route("/cerrarSesion")
def cerrarSesion():
    session.clear()
    return redirect(url_for("login"))

# =========================================================================
# MÓDULO EMPLEADOS
# =========================================================================

@app.route("/empleados")
def empleados():
    # para poderla pasar al formulario.
    con = mysql.connector.connect(**db_config)
    cursor = con.cursor(dictionary=True)
    
    # Consulta para obtener todos los departamentos
    cursor.execute("SELECT idDepartamento, NombreDepartamento FROM departamento ORDER BY NombreDepartamento ASC")
    departamentos = cursor.fetchall()
    
    cursor.close()
    con.close()
    
    # Pasamos la lista de departamentos a la plantilla
    return render_template("empleados.html", departamentos=departamentos)
    
@app.route("/tbodyEmpleados")
def tbodyEmpleados():
    con = mysql.connector.connect(**db_config)
    cursor = con.cursor(dictionary=True)

    # MODIFICACIÓN: Se usa INNER JOIN para obtener el nombre del departamento.
    # Se selecciona E.* (todos los campos de empleados) y D.NombreDepartamento.
    sql = """
    SELECT 
        E.idEmpleado, 
        E.nombreEmpleado, 
        E.numero, 
        E.fechaIngreso, 
        E.idDepartamento,
        D.NombreDepartamento 
    FROM 
        empleados AS E
    INNER JOIN 
        departamento AS D ON E.idDepartamento = D.idDepartamento
    ORDER BY 
        E.idEmpleado DESC
    """
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


@app.route("/departamento", methods=["POST"])
def guardarDepartamento():
    con = mysql.connector.connect(**db_config)
    cursor = con.cursor()

    idDepartamento     = request.form.get("idDepartamento", "")
    nombreDepartamento = request.form["txtNombreDepartamento"]
    edificio           = request.form["txtEdificio"]
    descripcion        = request.form["txtDescripcion"]

    if idDepartamento:  
        sql = """
            UPDATE departamento
            SET NombreDepartamento = %s, Edificio = %s, Descripcion = %s
            WHERE idDepartamento = %s
        """
        val = (nombreDepartamento, edificio, descripcion, idDepartamento)
    else:
        sql = """
            INSERT INTO departamento (NombreDepartamento, Edificio, Descripcion)
            VALUES (%s, %s, %s)
        """
        val = (nombreDepartamento, edificio, descripcion)

    cursor.execute(sql, val)
    con.commit()

    cursor.close()
    con.close()

    return jsonify({"status": "success"})

@app.route("/tbodyDepartamentos")
def tbodyDepartamentos():
    con = mysql.connector.connect(**db_config)
    cursor = con.cursor(dictionary=True)

    sql = "SELECT idDepartamento, NombreDepartamento, Edificio, Descripcion FROM departamento ORDER BY idDepartamento DESC"
    cursor.execute(sql)
    registros = cursor.fetchall()

    cursor.close()
    con.close()
    
    return render_template("tbodyDepartamentos.html", departamentos=registros)
