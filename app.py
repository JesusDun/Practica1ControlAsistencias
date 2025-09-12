# python.exe -m venv .venv
# cd .venv/Scripts
# activate.bat
# py -m ensurepip --upgrade
# pip install -r requirements.txt
# pip install bcrypt

from flask import Flask, render_template, request, jsonify, make_response
import mysql.connector
from flask_cors import CORS
import pusher
import bcrypt

# --- Configuración de la base de datos ---
db_config = {
    "host": "185.232.14.52",
    "database": "u760464709_23005019_bd",
    "user": "u760464709_23005019_usr",
    "password": "]0Pxl25["
}

app = Flask(__name__)
CORS(app)
app.secret_key = "tu_llave_secreta_aqui" # Se define una sola vez

# --- CONFIGURACIÓN DE PUSHER ---
pusher_client = pusher.Pusher(
    app_id='2048531',
    key='686124f7505c58418f23',
    secret='b5add38751c68986fc11',
    cluster='us2',
    ssl=True
)

# --- Funciones de Pusher para notificar a los clientes ---
def pusherAsistencias():
    pusher_client.trigger("canalAsistencias", "eventoAsistencias", {"message": "Cambio en asistencias."})

def pusherEmpleados():
    pusher_client.trigger("canalEmpleados", "eventoEmpleados", {"message": "La lista de empleados ha cambiado."})

def pusherDepartamentos():
    pusher_client.trigger("canalDepartamentos", "eventoDepartamentos", {"message": "La lista de empleados ha cambiado."})

# =========================================================================
# RUTAS BASE Y AUTENTICACIÓN
# =========================================================================

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/app")
def app2():
    return render_template("login.html")

@app.route("/iniciarSesion", methods=["POST"])
def iniciarSesion():
    # CORRECCIÓN CRÍTICA: Se implementa el inicio de sesión seguro con bcrypt.
    usuario_ingresado = request.form.get("txtUsuario")
    contrasena_ingresada = request.form.get("txtContrasena")

    if not usuario_ingresado or not contrasena_ingresada:
        return make_response(jsonify([]), 400) # Evita errores si los campos están vacíos

    con = mysql.connector.connect(**db_config)
    cursor = con.cursor(dictionary=True)
    
    # 1. Se busca al usuario por su nombre de usuario
    sql = "SELECT idUsuario, password FROM usuarios WHERE username = %s"
    cursor.execute(sql, (usuario_ingresado,))
    registro_usuario = cursor.fetchone()
    con.close()

    usuario_encontrado = None
    if registro_usuario:
        hash_guardado = registro_usuario['password'].encode('utf-8')
        contrasena_ingresada_bytes = contrasena_ingresada.encode('utf-8')

        # 2. Se compara la contraseña ingresada con el hash de la BD
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
    con.close()
    return render_template("tbodyEmpleados.html", empleados=registros)

@app.route("/empleado", methods=["POST"])
def guardarEmpleado():
    # MEJORA: Se usa .get() para más seguridad y se añade manejo de errores.
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
        
        # NUEVO: Se notifica a los clientes del cambio a través de Pusher.
        pusherEmpleados()
        
        return make_response(jsonify({"message": "Operación exitosa"}), 200)

    except mysql.connector.Error as err:
        if con: con.rollback()
        return make_response(jsonify({"error": f"Error de base de datos: {err}"}), 500)

    finally:
        if con and con.is_connected():
            cursor.close()
            con.close()

# =========================================================================
# MÓDULO ASISTENCIAS (Sin cambios, ya estaba bien)
# =========================================================================
@app.route("/asistencias")
def asistencias():
    return render_template("asistencias.html")

@app.route("/tbodyAsistencias")
def tbodyAsistencias():
    con = mysql.connector.connect(**db_config)
    cursor = con.cursor(dictionary=True)
    sql = "SELECT idAsistencia, fecha, comentarios FROM asistencias ORDER BY idAsistencia DESC"
    cursor.execute(sql)
    registros = cursor.fetchall()
    con.close()
    return render_template("tbodyAsistencias.html", asistencias=registros)

@app.route("/asistencia", methods=["POST"])
def guardarAsistencia():
    # Esta ruta puede mejorarse con manejo de errores como en guardarEmpleado
    con = mysql.connector.connect(**db_config)
    cursor = con.cursor()
    fecha = request.form["fecha"]
    comentarios = request.form["comentarios"]
    sql = "INSERT INTO asistencias (fecha, comentarios) VALUES (%s, %s)"
    val = (fecha, comentarios)
    cursor.execute(sql, val)
    con.commit()
    cursor.close()
    con.close()
    pusherAsistencias()
    return make_response(jsonify({}))

# =========================================================================
# MÓDULO ASISTENCIAS/PASES
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

# --- RUTA UNIFICADA PARA CREAR Y ACTUALIZAR ---
@app.route("/asistenciapase", methods=["POST"])
def guardarAsistenciaPase():
    try:
        con = mysql.connector.connect(**db_config)
        cursor = con.cursor()
        
        idAsistenciaPase = request.form.get("idAsistenciaPase")
        idEmpleado = request.form["idEmpleado"]
        idAsistencia = request.form["idAsistencia"]
        estado = request.form["estado"]

        if idAsistenciaPase:
            # Lógica de Actualización
            sql = """
                UPDATE asistenciaspases 
                SET idEmpleado = %s, idAsistencia = %s, estado = %s 
                WHERE idAsistenciaPase = %s
            """
            val = (idEmpleado, idAsistencia, estado, idAsistenciaPase)
        else:
            # Lógica de Creación (Lanzando evento con Pusher como lo tenías)
            pusher_client.trigger("canalPases", "eventoNuevoPase", {
                "idEmpleado": idEmpleado,
                "idAsistencia": idAsistencia,
                "estado": estado
            })
            # Nota: La inserción real ocurre en manejarEventoPase
            # Para un CRUD más directo, aquí iría el INSERT
            sql = """
                INSERT INTO asistenciaspases (idEmpleado, idAsistencia, estado) 
                VALUES (%s, %s, %s)
            """
            val = (idEmpleado, idAsistencia, estado)

        cursor.execute(sql, val)
        con.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        con.close()

# --- RUTA PARA OBTENER DATOS DE UN PASE (PARA EDITAR) ---
@app.route("/asistenciapase/<int:id>", methods=["GET"])
def obtenerAsistenciaPase(id):
    try:
        con = mysql.connector.connect(**db_config)
        cursor = con.cursor(dictionary=True)
        sql = "SELECT * FROM asistenciaspases WHERE idAsistenciaPase = %s"
        cursor.execute(sql, (id,))
        pase = cursor.fetchone()
        if pase:
            return jsonify(pase)
        return jsonify({"error": "Pase no encontrado"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        con.close()

@app.route("/asistenciapase/eliminar", methods=["POST"])
def eliminarAsistenciaPase():
    con = mysql.connector.connect(**db_config)
    cursor = con.cursor()
    id_pase = request.form["id"]
    sql = "DELETE FROM asistenciaspases WHERE idAsistenciaPase = %s"
    val = (id_pase,)
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
    con = mysql.connector.connect(**db_config)
    cursor = con.cursor(dictionary=True)
    sql = "SELECT idDepartamento, NombreDepartamento, Edificio, Descripcion FROM departamento ORDER BY idDepartamento DESC"
    cursor.execute(sql)
    registros = cursor.fetchall()
    con.close()
    return render_template("tbodyDepartamentos.html", departamentos=registros)

# Faltaba la ruta para guardar/editar departamentos, aquí está:
@app.route("/departamento", methods=["POST"])
def guardarDepartamento():
    idDepartamento = request.form.get("idDepartamento")
    nombre = request.form.get("nombreDepartamento")
    edificio = request.form.get("edificio")
    descripcion = request.form.get("descripcion")

    con = mysql.connector.connect(**db_config)
    cursor = con.cursor()

    if idDepartamento:
        sql = "UPDATE departamento SET NombreDepartamento = %s, Edificio = %s, Descripcion = %s WHERE idDepartamento = %s"
        val = (nombre, edificio, descripcion, idDepartamento)
    else:
        sql = "INSERT INTO departamento (NombreDepartamento, Edificio, Descripcion) VALUES (%s, %s, %s)"
        val = (nombre, edificio, descripcion)
    
    cursor.execute(sql, val)
    con.commit()
    cursor.close()
    con.close()
    pusherDepartamentos()
    
    return make_response(jsonify({"status": "success"}))
