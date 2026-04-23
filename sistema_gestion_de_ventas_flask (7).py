# =============================
# PROYECTO COMPLETO FLASK + MYSQL
# =============================

# =============================
# requirements.txt
# =============================
flask
mysql-connector-python

# =============================
# config.py
# =============================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root123",
    "database": "ventas"
}

# =============================
# db.py
# =============================
import mysql.connector
from config import DB_CONFIG

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

# =============================
# app.py
# =============================
from flask import Flask
from routes.auth_routes import auth_bp
from routes.producto_routes import producto_bp
from routes.persona_routes import persona_bp
from routes.ventas_routes import ventas_bp

app = Flask(__name__)
app.secret_key = "secret_key"

app.register_blueprint(auth_bp)
app.register_blueprint(producto_bp)
app.register_blueprint(persona_bp)
app.register_blueprint(ventas_bp)

if __name__ == "__main__":
    app.run(debug=True)

# =============================
# routes/auth_routes.py
# =============================
from flask import Blueprint, render_template, request, redirect, session
from db import get_connection

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = request.form['user']
        password = request.form['password']

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Usuarios WHERE idUsuario=%s AND password=%s", (user,password))
        row = cursor.fetchone()

        if row:
            session['user'] = user
            return redirect('/productos')

    return render_template('login.html')

# =============================
# routes/producto_routes.py
# =============================
from flask import Blueprint, render_template, request, redirect
from db import get_connection

producto_bp = Blueprint('productos', __name__, url_prefix='/productos')

@producto_bp.route('/')
def listar():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Productos")
    productos = cursor.fetchall()
    return render_template('productos.html', productos=productos)

@producto_bp.route('/nuevo', methods=['POST'])
def nuevo():
    data = request.form
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO Productos (DSCPRODUCTO, PRECIO1, STOCK) VALUES (%s,%s,%s)",
                   (data['descripcion'], data['precio'], data['stock']))

    conn.commit()
    return redirect('/productos')

# =============================
# routes/persona_routes.py
# =============================
from flask import Blueprint, render_template, request, redirect
from db import get_connection

persona_bp = Blueprint('personas', __name__, url_prefix='/personas')

@persona_bp.route('/')
def listar():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Personas WHERE ESTADO=1")
    personas = cursor.fetchall()
    return render_template('personas.html', personas=personas)

@persona_bp.route('/nuevo', methods=['POST'])
def nuevo():
    data = request.form
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO Personas
        (TpoPersona, CUIT, CONDIVA, RAZONSOCIAL, DOMICILIO, LOCALIDAD, TELEFONO, EMAIL, ESTADO)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,1)
    """, (
        data['tpo'], data['cuit'], data['condiva'], data['razon'],
        data['domicilio'], data['localidad'], data['telefono'], data['email']
    ))

    conn.commit()
    return redirect('/personas')

@persona_bp.route('/eliminar/<int:id>')
def eliminar(id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE Personas SET ESTADO=0 WHERE idPersona=%s", (id,))

    conn.commit()
    return redirect('/personas')

# =============================
# routes/ventas_routes.py (MYSQL)
# =============================
from flask import Blueprint, render_template, request, jsonify
from db import get_connection
from datetime import datetime

ventas_bp = Blueprint('ventas', __name__, url_prefix='/ventas')

@ventas_bp.route('/')
def ventas():
    return render_template('ventas.html')

@ventas_bp.route('/buscar_producto')
def buscar_producto():
    codigo = request.args.get('codigo')
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT CODPRODUCTO, DSCPRODUCTO, PRECIO1, STOCK
        FROM Productos
        WHERE CODIGOBARRA=%s OR DSCPRODUCTO LIKE %s
        LIMIT 1
    """, (codigo, f"%{codigo}%"))

    p = cursor.fetchone()
    return jsonify(p if p else None)

@ventas_bp.route('/buscar_cliente')
def buscar_cliente():
    q = request.args.get('q')
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT idPersona, RAZONSOCIAL
        FROM Personas
        WHERE TpoPersona='CLIE' AND (RAZONSOCIAL LIKE %s OR CUIT LIKE %s)
        LIMIT 10
    """, (f"%{q}%", f"%{q}%"))

    return jsonify(cursor.fetchall())

@ventas_bp.route('/guardar', methods=['POST'])
def guardar_venta():
    data = request.json

    conn = get_connection()
    cursor = conn.cursor()

    total = float(data['total'])
    efectivo = float(data['efectivo'])
    tarjeta = float(data['tarjeta'])
    transferencia = float(data['transferencia'])

    total_pagado = efectivo + tarjeta + transferencia
    saldo = total - total_pagado

    cursor.execute("SELECT FactorStock, FactorCtaCte FROM TpoMovimientos WHERE tpoMovimiento=%s", ('VENT',))
    tpo = cursor.fetchone()

    factor_stock = tpo[0] if tpo else -1
    factor_ctacte = tpo[1] if tpo else 1

    cursor.execute("""
        INSERT INTO Movimientos (FecMovimiento, IdPersona, Total, TpoMovimiento,
        TotalEfectivo, TotalTarjeta, TotalTransferencia, TotalCtaCte)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        datetime.now(), data['cliente'], total, 'VENT',
        efectivo, tarjeta, transferencia, saldo if saldo > 0 else 0
    ))

    idMovimiento = cursor.lastrowid

    for i, item in enumerate(data['items']):
        cursor.execute("""
            INSERT INTO Movimientos_Detalle
            (idMovimiento, orden, CodProducto, Cantidad, PrecioUnitario, Total, estado)
            VALUES (%s,%s,%s,%s,%s,%s,1)
        """, (idMovimiento, i+1, item['id'], item['cantidad'], item['precio'], item['total']))

        cursor.execute("UPDATE Productos SET STOCK = STOCK + (%s * %s) WHERE CODPRODUCTO=%s",
                       (item['cantidad'], factor_stock, item['id']))

    if saldo > 0 and factor_ctacte != 0:
        tipo = 'DEUD' if factor_ctacte == 1 else 'PAGO'

        cursor.execute("""
            INSERT INTO CuentasCorrientes
            (idMovimiento, Tipo, MontoTotal, Pago, idPersona, FecCtaCte, Concepto)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (
            idMovimiento, tipo, total, total_pagado,
            data['cliente'], datetime.now(), 'Movimiento'
        ))

    conn.commit()
    return jsonify({'ok': True})
