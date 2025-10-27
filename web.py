from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os

app = Flask(__name__)
app.secret_key = "clave_super_secreta_cámbiala"  # ✅ Cambia esto por una clave propia
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'docs')

# Crear carpeta si no existe
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Inicializar extensiones
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ---------- MODELO DE USUARIO ----------
class User(UserMixin, db.Model):
    __tablename__ = 'users'  # ✅ Mejor usar nombre plural para evitar conflictos
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default='estudiante')

# ---------- CARGADOR DE USUARIOS ----------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------- RUTAS ----------
@app.route('/')
def index():
    archivos = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('index.html', archivos=archivos, usuario=current_user)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    if current_user.rol != 'profesor':
        flash('Solo los profesores pueden subir documentos.')
        return redirect(url_for('index'))

    if request.method == 'POST':
        archivo = request.files.get('file')
        if archivo and archivo.filename.strip():
            ruta = os.path.join(app.config['UPLOAD_FOLDER'], archivo.filename)
            archivo.save(ruta)
            flash('Archivo subido correctamente.')
            return redirect(url_for('index'))
        else:
            flash('No se seleccionó ningún archivo.')
    return render_template('upload.html')

@app.route('/descargar/<nombre>')
def descargar(nombre):
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], nombre, as_attachment=True)
    except FileNotFoundError:
        flash('El archivo no existe.')
        return redirect(url_for('index'))

# ---------- LOGIN ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            flash('Inicio de sesión exitoso.')
            return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos.')
    return render_template('login.html')

# ---------- REGISTRO ----------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        rol = request.form.get('rol', 'estudiante')  # ✅ valor por defecto si el usuario no elige rol

        if User.query.filter_by(username=username).first():
            flash('Ese usuario ya existe.')
            return redirect(url_for('register'))

        nuevo_usuario = User(username=username, password=password, rol=rol)
        db.session.add(nuevo_usuario)
        db.session.commit()

        flash('Usuario creado correctamente. Ahora inicia sesión.')
        return redirect(url_for('login'))

    return render_template('register.html')

# ---------- CERRAR SESIÓN ----------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada correctamente.')
    return redirect(url_for('index'))

# ---------- INICIALIZAR BASE DE DATOS ----------
with app.app_context():
    db.create_all()

# ---------- INICIO DE LA APLICACIÓN ----------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
