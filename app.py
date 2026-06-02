import os
import psycopg
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for

load_dotenv()
DATABASE_URL = os.environ['DATABASE_URL']

app = Flask(__name__)

AREAS_VALIDAS = {'Tecnología', 'Marketing', 'Negocios', 'Emprendimiento'}


def get_db():
    return psycopg.connect(DATABASE_URL, row_factory=psycopg.rows.dict_row)


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
                'INSERT INTO asistentes (numero_registro, nombre, email, empresa, area_interes) '
                'VALUES (%s, %s, %s, %s, %s) RETURNING id',
                ('TMP', nombre, email, empresa, area_interes)
            )
            nuevo_id = cursor.fetchone()['id']
            numero_registro = f'REG-{nuevo_id:04d}'
            conn.execute(
                'UPDATE asistentes SET numero_registro = %s WHERE id = %s',
                (numero_registro, nuevo_id)
            )
    except psycopg.errors.UniqueViolation:
        return render_template('index.html',
                               error='Este correo electrónico ya está registrado.',
                               nombre_previo=nombre, empresa_previa=empresa, area_previa=area_interes)

    return redirect(url_for('confirmacion', numero_registro=numero_registro))


@app.route('/confirmacion/<numero_registro>')
def confirmacion(numero_registro):
    with get_db() as conn:
        asistente = conn.execute(
            'SELECT * FROM asistentes WHERE numero_registro = %s', (numero_registro,)
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
    app.run(debug=True)
