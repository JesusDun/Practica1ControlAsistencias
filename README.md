# Practica1ControlAsistencias

Pagina: https://practica1controlasistencias-q5m0.onrender.com

Pagina de la DB: https://awos2024.free.nf/dbm

Credenciales ...

Servidor: 185.232.14.52

Base de Datos: u760464709_23005019_bd

Usuario: u760464709_23005019_usr

Contraseña: ]0Pxl25[

















# =========================================================================
# LOGIN
# =========================================================================

@app.route("/")
def login():
    if "idUsuario" in session:
        return redirect(url_for("index"))
    return render_template("login.html")

@app.route("/iniciarSesion", methods=["POST"])
def iniciarSesion():
    usuario_ingresado = request.form["txtUsuario"]
    contrasena_ingresada = request.form["txtContrasena"]

    if not usuario_ingresado or not contrasena_ingresada:
        return "Datos incompletos", 400

    con = mysql.connector.connect(**db_config)
    cursor = con.cursor(dictionary=True)
    cursor.execute("SELECT idUsuario, username, password FROM usuarios WHERE username = %s", (usuario_ingresado,))
    registro_usuario = cursor.fetchone()
    con.close()

    if registro_usuario:
        hash_guardado = registro_usuario['password'].encode('utf-8')
        contrasena_ingresada_bytes = contrasena_ingresada.encode('utf-8')
        if bcrypt.checkpw(contrasena_ingresada_bytes, hash_guardado):
            session["idUsuario"] = registro_usuario["idUsuario"]
            session["username"] = registro_usuario["username"]
            return redirect(url_for("index"))
    return "Usuario o contraseña incorrectos", 401

@app.route("/index")
def index():
    if "idUsuario" not in session:
        return redirect(url_for("login"))
    return render_template("index.html")

@app.route("/cerrarSesion")
def cerrarSesion():
    session.clear()
    return redirect(url_for("login"))
