from flask import Flask, render_template, request, jsonify, make_response
import mysql.connector
from flask_cors import CORS
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

# --- Funciones de Pusher ---
def pusherAsistencias():
    pusher_client.trigger("canalAsistencias", "eventoAsistencias", {"message": "Cambio en asistencias."})

def pusherEmpleados():
    pusher_client.trigger("canalEmpleados", "eventoEmpleados", {"message": "La lista de empleados ha cambiado."})

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
        return make_response(jsonify([]), 400)

    con = mysql.connector.connect(**db_config)
    cursor = con.cursor(dictionary=True)
    
    sql = "SELECT idUsuario, password FROM usuarios WHERE username = %s"
    cursor.execute(sql, (usuario_ingresado,))
    registro_usuario = cursor.fetchone()
    con.close()

    usuario_encontrado = None
    if registro_usuario:
        hash_guardado = registro_usuario['password'].encode('utf-8')
        contrasena_ingresada_bytes = contrasena_ingresada.encode('utf-8')

        if bcrypt.checkpw(contrasena_ingresada_bytes, hash_guardado):
            usuario_encontrado = [{"Id_Usuario": registro_usuario['idUsuario']}]

    return make_response(jsonify(usuario_encontrado or []))

# =========================================================================
# MÓDULO EMPLEADOS
# =========================================================================

@app.route("/empleados")
def empleados():
    con = mysql.connector.connect(**db_config)
    cursor = con.cursor(dictionary=True)
    cursor.execute("SELECT idDepartamento, NombreDepartamento FROM departamento ORDER BY NombreDepartamento ASC")
    departamentos = cursor.fetchall()
    cursor.close()
    con.close()
    return render_template("empleados.html", departamentos=departamentos)

@app.route("/tbodyEmpleados")
def tbodyEmpleados():
    con = mysql.connector.connect(**db_config)
    cursor = con.cursor(dictionary=True)
    sql = """
    SELECT 
        E.idEmpleado, E.nombreEmpleado, E.numero, E.fechaIngreso, 
        E.idDepartamento, D.NombreDepartamento 
    FROM empleados AS E
    INNER JOIN departamento AS D ON E.idDepartamento = D.idDepartamento
    ORDER BY E.idEmpleado DESC
    """
    cursor.execute(sql)
    registros = cursor.fetchall()
    cursor.close()
    con.close()
    return render_template("tbodyEmpleados.html", empleados=registros)

@app.route("/empleado", methods=["POST"])
def guardarEmpleado():
    idEmpleado = request.form.get("idEmpleado")
    nombreEmpleado = request.form.get("nombreEmpleado")
    numero = request.form.get("numero")
    fechaIngreso = request.form.get("fechaIngreso")
    idDepartamento = request.form.get("idDepartamento")

    if not all([nombreEmpleado, numero, fechaIngreso, idDepartamento]):
        return make_response(jsonify({"error": "Faltan datos requeridos."}), 400)

    con = None
    try:
        con = mysql.connector.connect(**db_config)
        cursor = con.cursor()
        
        if idEmpleado:
            sql = "UPDATE empleados SET nombreEmpleado = %s, numero = %s, fechaIngreso = %s, idDepartamento = %s WHERE idEmpleado = %s"
            val = (nombreEmpleado, numero, fechaIngreso, idDepartamento, idEmpleado)
        else:
            sql = "INSERT INTO empleados (nombreEmpleado, numero, fechaIngreso, idDepartamento) VALUES (%s, %s, %s, %s)"
            val = (nombreEmpleado, numero, fechaIngreso, idDepartamento)
        
        cursor.execute(sql, val)
        con.commit()
        
        pusherEmpleados() # Notificar a los clientes del cambio
        
        return make_response(jsonify({"message": "Operación exitosa"}), 200)

    except mysql.connector.Error as err:
        if con: con.rollback()
        return make_response(jsonify({"error": f"Error de base de datos: {err}"}), 500)

    finally:
        if con and con.is_connected():
            cursor.close()
            con.close()

# =========================================================================
# MÓDULO DEPARTAMENTOS
# =========================================================================

@app.route("/departamentos")
def departamentos():
    return render_template("departamentos.html")

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

# =========================================================================
# ... (Aquí irían tus otras rutas de Asistencias, Pases, etc.) ...
# =========================================================================
