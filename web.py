from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os

app = Flask(__name__)
app.secret_key = "clave_secreta"  # Cambia esto por una clave tuya
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER'] = 'static/docs'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ---------- MODELO DE USUARIO ----------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

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
    if request.method == 'POST':
        archivo = request.files['file']
        if archivo.filename != '':
            archivo.save(os.path.join(app.config['UPLOAD_FOLDER'], archivo.filename))
            flash('Archivo subido correctamente')
            return redirect(url_for('index'))
    return render_template('upload.html')

@app.route('/descargar/<nombre>')
def descargar(nombre):
    return send_from_directory(app.config['UPLOAD_FOLDER'], nombre, as_attachment=True)

# ---------- LOGIN ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.password == request.form['password']:
            login_user(user)
            flash('Inicio de sesión exitoso')
            return redirect(url_for('index'))
        flash('Usuario o contraseña incorrectos')
    return render_template('login.html')

# ---------- REGISTRO ----------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nuevo_usuario = User(
            username=request.form['username'],
            password=request.form['password']
        )
        db.session.add(nuevo_usuario)
        db.session.commit()
        flash('Usuario creado. Ahora inicia sesión.')
        return redirect(url_for('login'))
    return render_template('register.html')

# ---------- CERRAR SESIÓN ----------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada')
    return redirect(url_for('index'))

# ---------- INICIALIZAR BD ----------
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
