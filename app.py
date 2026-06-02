import sqlite3
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

DB = 'evento.db'

AREAS_VALIDAS = {'Tecnología', 'Marketing', 'Negocios', 'Emprendimiento'}


def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS asistentes (
                id             INTEGER  PRIMARY KEY AUTOINCREMENT,
                num_registro   TEXT     UNIQUE NOT NULL,
                nombre         TEXT     NOT NULL,
                email          TEXT     UNIQUE NOT NULL,
                empresa        TEXT     NOT NULL,
                area_interes   TEXT     NOT NULL,
                fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/registrar', methods=['POST'])
def registrar():
    nombre       = request.form.get('nombre', '').strip()
    email        = request.form.get('email', '').strip()
    empresa      = request.form.get('empresa', '').strip()
    area_interes = request.form.get('area_interes', '').strip()

    # Validación en servidor
    if not nombre:
        return render_template('index.html', error='Por favor, ingresa tu nombre completo.',
                               email_previo=email, empresa_previa=empresa, area_previa=area_interes)
    if not email:
        return render_template('index.html', error='Por favor, ingresa tu correo electrónico.',
                               nombre_previo=nombre, empresa_previa=empresa, area_previa=area_interes)
    if not empresa:
        return render_template('index.html', error='Por favor, ingresa el nombre de tu empresa u organización.',
                               nombre_previo=nombre, email_previo=email, area_previa=area_interes)
    if area_interes not in AREAS_VALIDAS:
        return render_template('index.html', error='Por favor, selecciona un área de interés válida.',
                               nombre_previo=nombre, email_previo=email, empresa_previa=empresa)

    try:
        with get_db() as conn:
            cursor = conn.execute(
                'INSERT INTO asistentes (num_registro, nombre, email, empresa, area_interes) '
                'VALUES (?, ?, ?, ?, ?)',
                ('TMP', nombre, email, empresa, area_interes)
            )
            nuevo_id = cursor.lastrowid
            num_registro = f'REG-{nuevo_id:04d}'
            conn.execute(
                'UPDATE asistentes SET num_registro = ? WHERE id = ?',
                (num_registro, nuevo_id)
            )
    except sqlite3.IntegrityError:
        return render_template('index.html',
                               error='Este correo electrónico ya está registrado.',
                               nombre_previo=nombre, empresa_previa=empresa, area_previa=area_interes)

    return redirect(url_for('confirmacion', num_registro=num_registro))


@app.route('/confirmacion/<num_registro>')
def confirmacion(num_registro):
    with get_db() as conn:
        asistente = conn.execute(
            'SELECT * FROM asistentes WHERE num_registro = ?', (num_registro,)
        ).fetchone()

    if asistente is None:
        return redirect(url_for('index'))

    return render_template('confirmacion.html', asistente=asistente)


@app.route('/admin')
def admin():
    with get_db() as conn:
        asistentes = conn.execute(
            'SELECT * FROM asistentes ORDER BY id DESC'
        ).fetchall()

    return render_template('admin.html', asistentes=asistentes)


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
