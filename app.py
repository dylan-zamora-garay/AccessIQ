import base64
import csv
import io
import os
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone

import face_recognition
from flask import Flask, Response, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

try:
    from PIL import Image
except ImportError:
    Image = None

# Forzar la ruta absoluta actual para que Flask busque los HTML sueltos en mysite/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__,
            template_folder=BASE_DIR,
            static_folder=os.path.join(BASE_DIR, "static"))
app.secret_key = "accessiq-clave-secreta-cambiala"

DB = os.path.join(BASE_DIR, "accessiq.db")
CARPETA_FOTOS = os.path.join(BASE_DIR, "static", "fotos")
os.makedirs(CARPETA_FOTOS, exist_ok=True)
CARPETA_CAPTURAS = os.path.join(BASE_DIR, "static", "capturas")
os.makedirs(CARPETA_CAPTURAS, exist_ok=True)

UMBRAL = 0.5          # más bajo = más estricto (0.6 es el valor por defecto de la librería)
ENCODINGS = {}        # memoria: nombre de foto -> codificación del rostro
POR_PAGINA = 20       # filas por página en el historial

# Hora de Colombia (UTC-5, sin horario de verano), sin depender del reloj del PC
ZONA = timezone(timedelta(hours=-5))


def hora_actual():
    return datetime.now(ZONA)


# ---------- Base de datos ----------
def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def iniciar_db():
    con = db()
    con.execute("""
        CREATE TABLE IF NOT EXISTS personas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            identificacion TEXT UNIQUE NOT NULL,
            hora_inicio TEXT NOT NULL,
            hora_fin TEXT NOT NULL,
            permiso TEXT NOT NULL,
            foto TEXT NOT NULL,
            creado TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS accesos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            persona_id INTEGER,
            resultado TEXT NOT NULL,
            fecha TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)
    columnas = [c["name"] for c in con.execute("PRAGMA table_info(accesos)")]
    if "motivo" not in columnas:
        con.execute("ALTER TABLE accesos ADD COLUMN motivo TEXT")
    if "captura" not in columnas:
        con.execute("ALTER TABLE accesos ADD COLUMN captura TEXT")

    # Usuarios que pueden iniciar sesión en el sistema
    con.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            rol TEXT NOT NULL DEFAULT 'usuario',
            creado TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)
    # Si no hay usuarios, se crea el administrador inicial (el que ya usabas)
    if con.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0:
        con.execute(
            "INSERT INTO usuarios (usuario, password_hash, rol) VALUES (?, ?, 'admin')",
            ("dylan", generate_password_hash("10225")),
        )

    con.commit()
    con.close()


iniciar_db()


def requiere_login():
    """True si hay que mandar al login (sin sesión o con usuario ya eliminado)."""
    if "usuario" not in session:
        return True
    con = db()
    fila = con.execute(
        "SELECT 1 FROM usuarios WHERE usuario = ?", (session["usuario"],)
    ).fetchone()
    con.close()
    if not fila:
        session.clear()
        return True
    return False


def es_admin():
    if "usuario" not in session:
        return False
    con = db()
    fila = con.execute(
        "SELECT rol FROM usuarios WHERE usuario = ?", (session["usuario"],)
    ).fetchone()
    con.close()
    return bool(fila) and fila["rol"] == "admin"


@app.context_processor
def inyectar_datos():
    # Permite usar {% if es_admin %} en todos los HTML (para mostrar el menú Usuarios)
    return {"es_admin": es_admin()}


# ---------- Reconocimiento facial ----------
def codificar(datos_jpg):
    imagen = face_recognition.load_image_file(io.BytesIO(datos_jpg))
    codigos = face_recognition.face_encodings(imagen)
    return codigos[0] if codigos else None


def encodings_registrados():
    con = db()
    filas = con.execute("SELECT * FROM personas").fetchall()
    con.close()

    resultado = []
    for fila in filas:
        nombre_foto = fila["foto"]
        if nombre_foto not in ENCODINGS:
            ruta = os.path.join(CARPETA_FOTOS, nombre_foto)
            try:
                with open(ruta, "rb") as f:
                    ENCODINGS[nombre_foto] = codificar(f.read())
            except Exception:
                ENCODINGS[nombre_foto] = None
        if ENCODINGS[nombre_foto] is not None:
            resultado.append((fila, ENCODINGS[nombre_foto]))
    return resultado


def dentro_de_horario(inicio, fin):
    ahora = hora_actual().strftime("%H:%M")
    if inicio <= fin:
        return inicio <= ahora <= fin
    return ahora >= inicio or ahora <= fin   # horario que cruza la medianoche


def guardar_captura(datos_jpg):
    """Guarda una miniatura del rostro capturado y devuelve el nombre del archivo."""
    nombre = uuid.uuid4().hex + ".jpg"
    ruta = os.path.join(CARPETA_CAPTURAS, nombre)
    try:
        if Image is None:
            raise RuntimeError("Pillow no disponible")
        img = Image.open(io.BytesIO(datos_jpg)).convert("RGB")
        img.thumbnail((320, 320))
        img.save(ruta, "JPEG", quality=80)
    except Exception:
        with open(ruta, "wb") as f:
            f.write(datos_jpg)
    return nombre


def registrar_acceso(persona_id, resultado, motivo, captura=None):
    fecha = hora_actual().strftime("%Y-%m-%d %H:%M:%S")
    con = db()
    con.execute(
        "INSERT INTO accesos (persona_id, resultado, motivo, fecha, captura) "
        "VALUES (?, ?, ?, ?, ?)",
        (persona_id, resultado, motivo, fecha, captura),
    )
    con.commit()
    con.close()


# ---------- Inicio y login ----------
@app.route("/")
def inicio():
    return render_template("inicio.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"].strip()
        contraseña = request.form["contraseña"]

        con = db()
        fila = con.execute(
            "SELECT * FROM usuarios WHERE usuario = ?", (usuario,)
        ).fetchone()
        con.close()

        if fila and check_password_hash(fila["password_hash"], contraseña):
            session.clear()
            session["usuario"] = fila["usuario"]
            session["rol"] = fila["rol"]
            return redirect(url_for("panel"))
        else:
            return render_template("login.html", error="Usuario o contraseña incorrectos")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("inicio"))


# ---------- Panel ----------
@app.route("/panel")
def panel():
    if requiere_login():
        return redirect(url_for("login"))

    hoy = hora_actual().strftime("%Y-%m-%d")

    con = db()
    total = con.execute("SELECT COUNT(*) FROM personas").fetchone()[0]
    autorizados = con.execute(
        "SELECT COUNT(*) FROM accesos WHERE resultado = 'autorizado' "
        "AND date(fecha) = ?", (hoy,)
    ).fetchone()[0]
    rechazados = con.execute(
        "SELECT COUNT(*) FROM accesos WHERE resultado = 'rechazado' "
        "AND date(fecha) = ?", (hoy,)
    ).fetchone()[0]
    ultimos = con.execute("""
        SELECT a.resultado, a.motivo, a.fecha, a.captura, p.nombre, p.foto
        FROM accesos a
        LEFT JOIN personas p ON p.id = a.persona_id
        ORDER BY a.id DESC
        LIMIT 8
    """).fetchall()
    con.close()

    return render_template(
        "panel.html",
        usuario=session["usuario"],
        total_personas=total,
        accesos_hoy=autorizados,
        rechazados_hoy=rechazados,
        ultimos=ultimos,
    )


# ---------- Personas ----------
@app.route("/personas")
def personas():
    if requiere_login():
        return redirect(url_for("login"))

    con = db()
    lista = con.execute("SELECT * FROM personas ORDER BY id DESC").fetchall()
    con.close()
    return render_template("personas.html", personas=lista)


@app.route("/personas/guardar", methods=["POST"])
def guardar_persona():
    if requiere_login():
        return redirect(url_for("login"))

    nombre = request.form.get("nombre", "").strip()
    identificacion = request.form.get("identificacion", "").strip()
    hora_inicio = request.form.get("hora_inicio", "")
    hora_fin = request.form.get("hora_fin", "")
    permiso = request.form.get("permiso", "autorizado")
    foto = request.form.get("foto", "")

    if not (nombre and identificacion and hora_inicio and hora_fin):
        flash("Completa todos los campos.", "error")
        return redirect(url_for("personas"))

    if not foto.startswith("data:image"):
        flash("Debes tomar la foto con la cámara o subir una imagen antes de guardar.", "error")
        return redirect(url_for("personas"))

    try:
        datos = base64.b64decode(foto.split(",", 1)[1])
        codigo = codificar(datos)
    except Exception:
        flash("La foto no se pudo procesar. Inténtalo de nuevo.", "error")
        return redirect(url_for("personas"))

    if codigo is None:
        flash("No se detectó ningún rostro en la foto. Usa una foto de frente y con buena luz.", "error")
        return redirect(url_for("personas"))

    nombre_foto = uuid.uuid4().hex + ".jpg"

    con = db()
    try:
        con.execute(
            "INSERT INTO personas (nombre, identificacion, hora_inicio, "
            "hora_fin, permiso, foto) VALUES (?, ?, ?, ?, ?, ?)",
            (nombre, identificacion, hora_inicio, hora_fin, permiso, nombre_foto),
        )
        con.commit()
    except sqlite3.IntegrityError:
        con.close()
        flash("Ya existe una persona con esa identificación.", "error")
        return redirect(url_for("personas"))
    con.close()

    with open(os.path.join(CARPETA_FOTOS, nombre_foto), "wb") as f:
        f.write(datos)
    ENCODINGS[nombre_foto] = codigo

    flash(f"{nombre} fue registrado correctamente.", "ok")
    return redirect(url_for("personas"))


@app.route("/personas/editar/<int:persona_id>", methods=["POST"])
def editar_persona(persona_id):
    if requiere_login():
        return redirect(url_for("login"))

    nombre = request.form.get("nombre", "").strip()
    identificacion = request.form.get("identificacion", "").strip()
    hora_inicio = request.form.get("hora_inicio", "")
    hora_fin = request.form.get("hora_fin", "")
    permiso = "autorizado" if request.form.get("permiso") == "autorizado" else "denegado"

    if not (nombre and identificacion and hora_inicio and hora_fin):
        flash("Completa todos los campos.", "error")
        return redirect(url_for("personas"))

    con = db()
    try:
        con.execute(
            "UPDATE personas SET nombre = ?, identificacion = ?, hora_inicio = ?, "
            "hora_fin = ?, permiso = ? WHERE id = ?",
            (nombre, identificacion, hora_inicio, hora_fin, permiso, persona_id),
        )
        con.commit()
    except sqlite3.IntegrityError:
        con.close()
        flash("Ya existe otra persona con esa identificación.", "error")
        return redirect(url_for("personas"))
    con.close()

    flash("Cambios guardados.", "ok")
    return redirect(url_for("personas"))


@app.route("/personas/eliminar/<int:persona_id>", methods=["POST"])
def eliminar_persona(persona_id):
    if requiere_login():
        return redirect(url_for("login"))

    con = db()
    fila = con.execute("SELECT foto FROM personas WHERE id = ?", (persona_id,)).fetchone()
    if fila:
        con.execute("DELETE FROM personas WHERE id = ?", (persona_id,))
        con.commit()
        ENCODINGS.pop(fila["foto"], None)
        ruta = os.path.join(CARPETA_FOTOS, fila["foto"])
        if os.path.exists(ruta):
            os.remove(ruta)
    con.close()

    flash("Persona eliminada.", "ok")
    return redirect(url_for("personas"))


# ---------- Entrada (reconocimiento facial) ----------
@app.route("/entrada")
def entrada():
    if requiere_login():
        return redirect(url_for("login"))
    return render_template("entrada.html")


@app.route("/entrada/verificar", methods=["POST"])
def verificar_entrada():
    if requiere_login():
        return jsonify(estado="error", mensaje="La sesión expiró. Vuelve a iniciar sesión."), 401

    foto = (request.get_json(silent=True) or {}).get("foto", "")
    if not foto.startswith("data:image"):
        return jsonify(estado="error", mensaje="Imagen no válida."), 400

    try:
        datos = base64.b64decode(foto.split(",", 1)[1])
        codigo = codificar(datos)
    except Exception:
        return jsonify(estado="error", mensaje="No se pudo procesar la imagen."), 400

    ahora = hora_actual().strftime("%H:%M:%S")

    if codigo is None:
        return jsonify(
            estado="sin_rostro",
            mensaje="No se detectó ningún rostro. Mira de frente a la cámara.",
            hora=ahora,
        )

    registrados = encodings_registrados()
    persona = None
    if registrados:
        distancias = face_recognition.face_distance([c for _, c in registrados], codigo)
        mejor = min(range(len(distancias)), key=lambda k: distancias[k])
        if distancias[mejor] <= UMBRAL:
            persona = registrados[mejor][0]

    # Rostro desconocido: se guarda una miniatura del intento
    if persona is None:
        captura = guardar_captura(datos)
        registrar_acceso(None, "rechazado", "Rostro no registrado", captura)
        return jsonify(
            estado="rechazado",
            nombre="Persona no registrada",
            mensaje="Acceso denegado: rostro no registrado.",
            hora=ahora,
        )

    foto_url = url_for("static", filename="fotos/" + persona["foto"])

    # Persona registrada, pero sin permiso
    if persona["permiso"] != "autorizado":
        registrar_acceso(persona["id"], "rechazado", "Permiso denegado")
        return jsonify(
            estado="rechazado", nombre=persona["nombre"], foto=foto_url, hora=ahora,
            mensaje="Acceso denegado: no tiene permiso de acceso.",
        )

    # Persona con permiso, pero fuera de su horario
    if not dentro_de_horario(persona["hora_inicio"], persona["hora_fin"]):
        motivo = f"Fuera de horario ({persona['hora_inicio']} - {persona['hora_fin']})"
        registrar_acceso(persona["id"], "rechazado", motivo)
        return jsonify(
            estado="rechazado", nombre=persona["nombre"], foto=foto_url, hora=ahora,
            mensaje="Acceso denegado: " + motivo.lower() + ".",
        )

    # Todo en orden
    registrar_acceso(persona["id"], "autorizado", "Acceso concedido")
    return jsonify(
        estado="autorizado", nombre=persona["nombre"], foto=foto_url, hora=ahora,
        mensaje="Acceso autorizado. ¡Bienvenido!",
    )


# ---------- Historial ----------
def filtrar_accesos(args):
    """Arma el WHERE según los filtros del formulario."""
    condiciones = []
    params = []

    resultado = args.get("resultado", "")
    if resultado in ("autorizado", "rechazado"):
        condiciones.append("a.resultado = ?")
        params.append(resultado)

    desde = args.get("desde", "")
    if desde:
        condiciones.append("date(a.fecha) >= ?")
        params.append(desde)

    hasta = args.get("hasta", "")
    if hasta:
        condiciones.append("date(a.fecha) <= ?")
        params.append(hasta)

    q = args.get("q", "").strip()
    if q:
        condiciones.append("(p.nombre LIKE ? OR p.identificacion LIKE ?)")
        params.extend([f"%{q}%", f"%{q}%"])

    donde = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""
    return donde, params


def leer_filtros(args):
    return {
        "q": args.get("q", "").strip(),
        "resultado": args.get("resultado", ""),
        "desde": args.get("desde", ""),
        "hasta": args.get("hasta", ""),
    }


@app.route("/historial")
def historial():
    if requiere_login():
        return redirect(url_for("login"))

    donde, params = filtrar_accesos(request.args)
    filtros = leer_filtros(request.args)

    con = db()

    cuentas = con.execute(
        "SELECT a.resultado, COUNT(*) AS n FROM accesos a "
        "LEFT JOIN personas p ON p.id = a.persona_id "
        f"{donde} GROUP BY a.resultado",
        params,
    ).fetchall()
    total_autorizados = 0
    total_rechazados = 0
    for c in cuentas:
        if c["resultado"] == "autorizado":
            total_autorizados = c["n"]
        elif c["resultado"] == "rechazado":
            total_rechazados = c["n"]
    total = total_autorizados + total_rechazados

    paginas = max((total + POR_PAGINA - 1) // POR_PAGINA, 1)
    pagina = request.args.get("pagina", 1, type=int) or 1
    pagina = min(max(pagina, 1), paginas)

    filas = con.execute(
        "SELECT a.id, a.resultado, a.motivo, a.fecha, a.captura, "
        "p.nombre, p.identificacion, p.foto "
        "FROM accesos a LEFT JOIN personas p ON p.id = a.persona_id "
        f"{donde} ORDER BY a.id DESC LIMIT ? OFFSET ?",
        params + [POR_PAGINA, (pagina - 1) * POR_PAGINA],
    ).fetchall()
    con.close()

    return render_template(
        "historial.html",
        filas=filas,
        f=filtros,
        total=total,
        total_autorizados=total_autorizados,
        total_rechazados=total_rechazados,
        pagina=pagina,
        paginas=paginas,
    )


@app.route("/historial/exportar")
def exportar_historial():
    if requiere_login():
        return redirect(url_for("login"))

    donde, params = filtrar_accesos(request.args)

    con = db()
    filas = con.execute(
        "SELECT a.resultado, a.motivo, a.fecha, p.nombre, p.identificacion "
        "FROM accesos a LEFT JOIN personas p ON p.id = a.persona_id "
        f"{donde} ORDER BY a.id DESC",
        params,
    ).fetchall()
    con.close()

    salida = io.StringIO()
    escritor = csv.writer(salida, delimiter=";")
    escritor.writerow(["Fecha", "Hora", "Persona", "Identificación", "Resultado", "Motivo"])
    for fila in filas:
        fecha = fila["fecha"] or ""
        escritor.writerow([
            fecha[:10],
            fecha[11:19],
            fila["nombre"] or "Persona no registrada",
            fila["identificacion"] or "-",
            (fila["resultado"] or "").capitalize(),
            fila["motivo"] or "-",
        ])

    nombre_archivo = "historial_accessiq_" + hora_actual().strftime("%Y%m%d_%H%M") + ".csv"
    # BOM para que Excel muestre bien las tildes
    contenido = "\ufeff" + salida.getvalue()
    return Response(
        contenido,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={nombre_archivo}"},
    )


# ---------- Usuarios (solo administrador) ----------
@app.route("/usuarios")
def usuarios():
    if requiere_login():
        return redirect(url_for("login"))
    if not es_admin():
        return redirect(url_for("panel"))

    con = db()
    lista = con.execute("SELECT * FROM usuarios ORDER BY id").fetchall()
    con.close()
    return render_template("usuarios.html", usuarios=lista, actual=session["usuario"])


@app.route("/usuarios/crear", methods=["POST"])
def crear_usuario():
    if requiere_login():
        return redirect(url_for("login"))
    if not es_admin():
        return redirect(url_for("panel"))

    usuario = request.form.get("usuario", "").strip()
    clave = request.form.get("clave", "")
    rol = "admin" if request.form.get("rol") == "admin" else "usuario"

    if len(usuario) < 3:
        flash("El usuario debe tener al menos 3 caracteres.", "error")
        return redirect(url_for("usuarios"))

    if len(clave) < 4:
        flash("La contraseña debe tener al menos 4 caracteres.", "error")
        return redirect(url_for("usuarios"))

    con = db()
    try:
        con.execute(
            "INSERT INTO usuarios (usuario, password_hash, rol) VALUES (?, ?, ?)",
            (usuario, generate_password_hash(clave), rol),
        )
        con.commit()
    except sqlite3.IntegrityError:
        con.close()
        flash("Ya existe un usuario con ese nombre.", "error")
        return redirect(url_for("usuarios"))
    con.close()

    flash(f"Usuario «{usuario}» creado correctamente.", "ok")
    return redirect(url_for("usuarios"))


@app.route("/usuarios/clave/<int:usuario_id>", methods=["POST"])
def cambiar_clave(usuario_id):
    if requiere_login():
        return redirect(url_for("login"))
    if not es_admin():
        return redirect(url_for("panel"))

    clave = request.form.get("clave", "")
    if len(clave) < 4:
        flash("La contraseña debe tener al menos 4 caracteres.", "error")
        return redirect(url_for("usuarios"))

    con = db()
    con.execute(
        "UPDATE usuarios SET password_hash = ? WHERE id = ?",
        (generate_password_hash(clave), usuario_id),
    )
    con.commit()
    con.close()

    flash("Contraseña actualizada.", "ok")
    return redirect(url_for("usuarios"))


@app.route("/usuarios/eliminar/<int:usuario_id>", methods=["POST"])
def eliminar_usuario(usuario_id):
    if requiere_login():
        return redirect(url_for("login"))
    if not es_admin():
        return redirect(url_for("panel"))

    con = db()
    fila = con.execute("SELECT usuario FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()

    if not fila:
        con.close()
        return redirect(url_for("usuarios"))

    if fila["usuario"].lower() == session["usuario"].lower():
        con.close()
        flash("No puedes eliminar tu propio usuario.", "error")
        return redirect(url_for("usuarios"))

    con.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
    con.commit()
    con.close()

    flash(f"Usuario «{fila['usuario']}» eliminado.", "ok")
    return redirect(url_for("usuarios"))


if __name__ == "__main__":
    app.run(debug=False, use_reloader=False, threaded=True)