from flask import Flask, render_template, request, redirect, jsonify, url_for, current_app, flash, session
from libro import Libro
from usuario import Usuario
from usuario_pendiente import UsuarioPendiente
from factory_usuarios import FabricaUsuario
import os
from werkzeug.utils import secure_filename
import sqlite3

app = Flask(__name__)
app.secret_key = 'clave-super-secreta-123'

app.config['UPLOAD_FOLDER'] = 'static/img/libros'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

def obtener_ids_libros_inicio():
    with sqlite3.connect("biblio.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id_libro FROM libros_inicio")
        filas = cursor.fetchall()
        return [fila[0] for fila in filas]

def guardar_imagen_sin_sobrescribir(imagen, carpeta_relativa='img/libros'):
    carpeta_destino = os.path.join(current_app.root_path, 'static', carpeta_relativa)
    os.makedirs(carpeta_destino, exist_ok=True)

    nombre_seguro = secure_filename(imagen.filename)
    nombre_base, extension = os.path.splitext(nombre_seguro)
    nombre_final = nombre_seguro
    contador = 1

    while os.path.exists(os.path.join(carpeta_destino, nombre_final)):
        nombre_final = f"{nombre_base}_{contador}{extension}"
        contador += 1

    ruta_completa = os.path.join(carpeta_destino, nombre_final)
    imagen.save(ruta_completa)

    return f"{carpeta_relativa}/{nombre_final}"

niveles_jerarquia = {
    'creador': 5,
    'dueño': 4,
    'jefe': 3,
    'gerente': 2,
    'colaborador': 1
}

def jerarquia(cargo):
    return niveles_jerarquia.get(cargo, 0)

def reenumerar_ids(lista):
    for i, usuario in enumerate(lista, start=1):
        usuario["id"] = str(i)

@app.route('/')
def home():
    ids_inicio = obtener_ids_libros_inicio()
    libros_inicio = Libro.obtener_por_ids(ids_inicio)
    return render_template('index.html', libros=libros_inicio)

@app.route('/suscripcion')
def suscripcion():
    return render_template('suscripcion.html')

@app.route('/catalogo')
def catalogo():
    consulta = request.args.get('q', '').lower()
    if consulta:
        libros_filtrados = Libro.buscar_por_titulo_o_autor(consulta)
    else:
        libros_filtrados = Libro.obtener_todos()
    return render_template('catalogo.html', libros=libros_filtrados)

@app.route('/donacion')
def donacion():
    return render_template('donacion.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    mensaje_error = None
    if request.method == 'POST':
        email = request.form['email'].lower()
        contrasena = request.form['contrasena']
        usuario = Usuario.obtener_por_email(email)

        if usuario:

            if usuario.contrasena == contrasena:
                # Guardar usuario en sesión
                session['usuario'] = {
                    'id': usuario.id,
                    'nombre': usuario.nombre,
                    'email': usuario.email,
                    'contrasena': usuario.contrasena,
                    'cargo': usuario.cargo,
                    'img': usuario.img
                }
                return redirect(url_for('inicio_admin'))
            else:
                mensaje_error = "Contraseña incorrecta."
        else:
            mensaje_error = ("Usuario no encontrado.\n"
                             "Todavía no te has creado una cuenta o tu cuenta no ha sido aceptada.\n"
                             "Para más detalles escribí a hola@biblio.com "
                             "con el título 'Problemas de Inicio de Sesión'")
    return render_template('login.html', mensaje=mensaje_error)

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email'].lower()
        contrasena = request.form['contrasena']
        confirmar = request.form['confirmar']
        imagen = request.files.get('imagen')

        if contrasena != confirmar:
            flash('Las contraseñas no coinciden.', 'error')
            return redirect(url_for('registro'))

        # Verificamos en ambas tablas
        emails_existentes = [u.email for u in Usuario.obtener_todos()] + \
                            [u.email for u in UsuarioPendiente.obtener_todos()]
        if email in emails_existentes:
            flash('Ese correo ya está registrado.', 'error')
            return redirect(url_for('registro'))

        ruta_img = 'img/usuarios/icono-usuario.jpg'
        if imagen and imagen.filename != '':
            ruta_img = guardar_imagen_sin_sobrescribir(imagen, carpeta_relativa='img/usuarios')

        nuevo_usuario = FabricaUsuario.crear_postulante(
            nombre=nombre,
            email=email,
            contrasena=contrasena,
            img=ruta_img
        )

        nuevo_usuario.guardar()

        mensaje_exito = (
            "Tus datos han sido validados. Podrás ingresar tu cuenta en login cuando un administrador "
            "te lo permita.\nSi pasan más de 72 horas y no se aceptó tu cuenta, escribinos a hola@biblio.com"
        )
        return render_template('login.html', mensaje=mensaje_exito)

    return render_template('registro.html')

@app.route('/inicio_admin')
def inicio_admin():
    usuario_actual = session.get('usuario')
    ids_inicio = obtener_ids_libros_inicio()
    libros_inicio = Libro.obtener_por_ids(ids_inicio)
    return render_template('inicio-admin.html', libros=libros_inicio, usuario=usuario_actual)

@app.route('/eliminar_libro/<id>', methods=['POST'])
def eliminar_libro(id):
    libro = Libro.obtener_por_id(id)
    if libro:
        ruta_imagen = libro.portada
        ruta_imagen_completa = os.path.join(current_app.static_folder, ruta_imagen)

        try:
            if os.path.exists(ruta_imagen_completa):
                os.remove(ruta_imagen_completa)
        except Exception as e:
            print(f"Error eliminando imagen: {e}")

        # Eliminar libro de la base de datos
        with sqlite3.connect("biblio.db") as conn:
            cursor = conn.cursor()

            # 1. Eliminar de libros
            cursor.execute("DELETE FROM libros WHERE id = ?", (id,))
            
            # 2. Eliminar de libros_inicio si está
            cursor.execute("DELETE FROM libros_inicio WHERE id_libro = ?", (id,))
            
            # 3. Reemplazar si quedan menos de 5
            cursor.execute("SELECT id_libro FROM libros_inicio")
            ids_en_inicio = [row[0] for row in cursor.fetchall()]
            
            if len(ids_en_inicio) < 5:
                # Buscar un libro no incluido aún
                cursor.execute(
                    "SELECT id FROM libros WHERE id NOT IN (SELECT id_libro FROM libros_inicio)"
                )
                fila_reemplazo = cursor.fetchone()
                if fila_reemplazo:
                    id_reemplazo = fila_reemplazo[0]
                    cursor.execute(
                        "INSERT INTO libros_inicio (id_libro) VALUES (?)", (id_reemplazo,)
                    )

            conn.commit()

    # Mismo retorno que antes
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'status': 'ok'})
    else:
        return redirect(url_for('inicio_admin'))

@app.route('/libros_inicio', methods=['GET', 'POST'])
def libros_inicio():
    mensaje_error = None
    titulos_no_encontrados = []

    if request.method == 'POST':
        # Títulos del formulario
        titulos = [
            request.form.get('libro1'),
            request.form.get('libro2'),
            request.form.get('libro3'),
            request.form.get('libro4'),
            request.form.get('libro5'),
        ]

        nuevos_ids = []
        for titulo in titulos:
            libro = Libro.obtener_por_titulo(titulo)
            if libro:
                nuevos_ids.append(libro.id)
            else:
                titulos_no_encontrados.append(titulo)

        if titulos_no_encontrados:
            mensaje_error = (
                "Los siguientes libros no se encuentran en la base de datos: "
                + ", ".join(titulos_no_encontrados)
            )
        else:
            # Borrar todos los registros anteriores en libros_inicio
            with sqlite3.connect("biblio.db") as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM libros_inicio")
                for id_libro in nuevos_ids:
                    cursor.execute(
                        "INSERT INTO libros_inicio (id_libro) VALUES (?)", (id_libro,)
                    )
                conn.commit()
            return redirect(url_for('inicio_admin'))

    # Obtener todos los libros disponibles para el datalist
    libros_disponibles = Libro.obtener_todos()
    return render_template(
        'libros-inicio.html',
        libros=libros_disponibles,
        mensaje_error=mensaje_error
    )

@app.route('/catalogo_admin')
def catalogo_admin():
    consulta = request.args.get('q', '').lower()

    if consulta:
        libros_filtrados = Libro.buscar_por_titulo_o_autor(consulta)
    else:
        libros_filtrados = Libro.obtener_todos()

    return render_template('catalogo-admin.html', libros=libros_filtrados)

@app.route('/agregar_libro', methods=['GET', 'POST'])
def agregar_libro():
    if request.method == 'POST':
        titulo = request.form['titulo']
        autor = request.form['autor']
        descarga = request.form['descarga']
        imagen = request.files.get('imagen')

        portada = ''
        if imagen and imagen.filename != '':
            portada = guardar_imagen_sin_sobrescribir(imagen)

        # Crear y guardar el libro en la base de datos
        nuevo_libro = Libro(
            id=None,  # Se asigna automáticamente con AUTOINCREMENT
            titulo=titulo,
            autor=autor,
            descarga=descarga,
            portada=portada
        )
        nuevo_libro.guardar()

        return redirect(url_for('inicio_admin'))

    return render_template('agregar-libro.html')

@app.route('/modificar_libro', methods=['GET', 'POST'])
def modificar_libro():
    if request.method == 'POST':
        libro_id = int(request.form['id'])
        nuevo_titulo = request.form['titulo']
        nuevo_autor = request.form['autor']
        nueva_descarga = request.form['descarga']
        nueva_portada = None

        imagen = request.files.get('imagen')

        # Obtener libro original desde la base
        libro = Libro.obtener_por_id(libro_id)
        if not libro:
            return "Libro no encontrado", 404

        portada_anterior = libro.portada

        # Si se sube una imagen nueva, guardarla y eliminar la anterior
        if imagen and imagen.filename != '':
            nueva_portada = guardar_imagen_sin_sobrescribir(imagen)

            if portada_anterior:
                ruta_anterior = os.path.join(current_app.root_path, 'static', *portada_anterior.split('/'))
                if os.path.exists(ruta_anterior):
                    os.remove(ruta_anterior)

        # Actualizar los campos
        libro.titulo = nuevo_titulo
        libro.autor = nuevo_autor
        libro.descarga = nueva_descarga
        if nueva_portada:
            libro.portada = nueva_portada

        # Guardar cambios en la base
        libro.actualizar()

        return redirect(url_for('inicio_admin'))

    else:
        libro_id = request.args.get('id')
        try:
            libro_id = int(libro_id)
        except (ValueError, TypeError):
            return "ID inválido", 400

        libro = Libro.obtener_por_id(libro_id)
        if not libro:
            return "Libro no encontrado", 404

        return render_template('modificar-libro.html', libro=libro)

@app.route("/perfil")
def perfil():
    usuario_actual = session.get('usuario')

    empleados = [
        u for u in Usuario.obtener_todos() if jerarquia(u.cargo) < jerarquia(usuario_actual['cargo'])
    ]

    postulantes = UsuarioPendiente.obtener_todos()

    return render_template("perfil.html",
                           usuario=usuario_actual,
                           empleados=empleados,
                           postulantes=postulantes,
                           niveles=niveles_jerarquia,
                           jerarquia=jerarquia)

@app.route('/aceptar_postulante/<email>')
def aceptar_postulante(email):
    usuario_actual = session.get('usuario')

    # Buscar postulante por email
    postulantes = UsuarioPendiente.obtener_todos()
    postulante = next((p for p in postulantes if p.email == email), None)

    if postulante and jerarquia(postulante.cargo) < jerarquia(usuario_actual['cargo']):
        # Insertar en usuarios
        nuevo_usuario = FabricaUsuario.promover_desde_postulante(postulante)
        nuevo_usuario.guardar()

        # Eliminar de usuarios_pendientes
        UsuarioPendiente.eliminar_por_id(postulante.id)

    return redirect(url_for("perfil"))

@app.route('/borrar_postulante/<email>')
def borrar_postulante(email):
    usuario_actual = session.get('usuario')

    # Buscar postulante por email
    postulantes = UsuarioPendiente.obtener_todos()
    postulante = next((p for p in postulantes if p.email == email), None)

    if postulante and jerarquia(postulante.cargo) < jerarquia(usuario_actual['cargo']):
        UsuarioPendiente.eliminar_por_id(postulante.id)

    return redirect(url_for("perfil"))

@app.route('/borrar_empleado/<email>')
def borrar_empleado(email):
    usuario_actual = session.get('usuario')

    empleado = Usuario.obtener_por_email(email)
    if empleado and jerarquia(empleado.cargo) < jerarquia(usuario_actual['cargo']):
        Usuario.eliminar_por_id(empleado.id)

    return redirect(url_for("perfil"))

@app.route("/cambiar_cargo/<email>", methods=["POST"])
def cambiar_cargo(email):
    usuario_actual = session.get('usuario')

    nuevo_cargo = request.form.get("nuevo_cargo")
    empleado = Usuario.obtener_por_email(email)

    if empleado and jerarquia(empleado.cargo) < jerarquia(usuario_actual['cargo']):
        if jerarquia(nuevo_cargo) < jerarquia(usuario_actual['cargo']):
            empleado.cambiar_cargo(email,nuevo_cargo)

    return redirect(url_for("perfil"))

@app.route("/modificar_perfil", methods=["GET", "POST"])
def modificar_perfil():
    usuario_actual = session.get('usuario')
    if not usuario_actual:
        return redirect(url_for("login"))

    if request.method == "POST":
        id_usuario = int(request.form.get("id"))
        nombre = request.form.get("nombre")
        email = request.form.get("email")
        contraseña = request.form.get("contraseña")
        confirmar = request.form.get("confirmar_contraseña")
        imagen = request.files.get("imagen")

        if contraseña != confirmar:
            flash("Las contraseñas no coinciden.")
            return redirect(url_for("modificar_perfil"))

        # Verificar email ya registrado por otro usuario o postulante
        email_ya_registrado = any(
            u.email == email and u.id != id_usuario
            for u in Usuario.obtener_todos()
        ) or any(
            p.email == email
            for p in UsuarioPendiente.obtener_todos()
        )
        if email_ya_registrado:
            flash("Ese correo electrónico ya está registrado.")
            return redirect(url_for("modificar_perfil"))

        usuario_db = Usuario.obtener_por_id(id_usuario)
        if not usuario_db:
            flash("Usuario no encontrado.")
            return redirect(url_for("modificar_perfil"))

        imagen_anterior = usuario_db.img
        nueva_ruta = imagen_anterior

        if imagen and imagen.filename:
            nueva_ruta = guardar_imagen_sin_sobrescribir(imagen, "img/usuarios")
            print("Ruta guardada:", nueva_ruta)
            if imagen_anterior and imagen_anterior != "img/usuarios/icono-usuario.jpg":
                ruta_completa = os.path.join(current_app.root_path, 'static', *imagen_anterior.split('/'))
                if os.path.exists(ruta_completa):
                    os.remove(ruta_completa)

        # Actualizar en base de datos
        usuario_db.modificar(nombre, email, contraseña, nueva_ruta)

        # Si el usuario modificó su propio perfil, actualizar en sesión
        if usuario_actual["id"] == int(id_usuario):
            session['usuario'] = {
                "id": int(id_usuario),
                "nombre": nombre,
                "email": email,
                "contrasena": contraseña,
                "img": nueva_ruta,
                "cargo": usuario_actual["cargo"]
            }
        print("Imagen en session:", session['usuario']['img'])
        session.modified = True
        return redirect(url_for("perfil"))

    return render_template("modificar-perfil.html", usuario=usuario_actual)

@app.route('/cerrar_sesion')
def cerrar_sesion():
    session.pop('usuario', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)