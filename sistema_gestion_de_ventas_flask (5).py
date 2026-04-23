# =============================
# ESTRUCTURA DEL PROYECTO
# =============================
# ventas_app/
# │
# ├── app.py
# ├── config.py
# ├── db.py
# ├── requirements.txt
# │
# ├── models/
# │   ├── persona.py
# │   ├── producto.py
# │   └── usuario.py
# │
# ├── routes/
# │   ├── auth_routes.py
# │   ├── producto_routes.py
# │   ├── persona_routes.py
# │   └── ventas_routes.py
# │
# ├── templates/
# │   ├── base.html
# │   ├── login.html
# │   ├── productos.html
# │   ├── personas.html
# │   └── ventas.html
# │
# └── static/
#     ├── css/
#     └── js/

# =============================
# requirements.txt
# =============================
flask
pyodbc

# =============================
# config.py
# =============================
DB_PATH = r"C:\ruta\a\tu\datos.accdb"
CONN_STR = (
    r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
    rf"DBQ={DB_PATH};"
)

# =============================
# db.py
# =============================
import pyodbc
from config import CONN_STR

def get_connection():
    return pyodbc.connect(CONN_STR)

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
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Usuarios WHERE idUsuario=? AND password=?", (user,password))
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
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Productos")
    productos = cursor.fetchall()
    return render_template('productos.html', productos=productos)

@producto_bp.route('/nuevo', methods=['POST'])
def nuevo():
    data = request.form
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Productos (DSCPRODUCTO, PRECIO1, STOCK) VALUES (?,?,?)",
                   (data['descripcion'], data['precio'], data['stock']))
    conn.commit()
    return redirect('/productos')

# =============================
# routes/ventas_routes.py
# =============================
from flask import Blueprint, render_template, request, redirect
from db import get_connection
from datetime import datetime

ventas_bp = Blueprint('ventas', __name__, url_prefix='/ventas')

@ventas_bp.route('/')
def ventas():
    return render_template('ventas.html')

@ventas_bp.route('/guardar', methods=['POST'])
def guardar_venta():
    conn = get_connection()
    cursor = conn.cursor()

    idPersona = request.form['idPersona']
    total = request.form['total']

    cursor.execute("INSERT INTO Movimientos (FecMovimiento, IdPersona, Total, TpoMovimiento) VALUES (?,?,?,?)",
                   (datetime.now(), idPersona, total, 'VENT'))

    conn.commit()
    return redirect('/ventas')

# =============================
# templates/base.html
# =============================
"""
<!DOCTYPE html>
<html>
<head>
    <title>Ventas</title>
</head>
<body>
    <h1>Sistema de Ventas</h1>
    {% block content %}{% endblock %}
</body>
</html>
"""

# =============================
# templates/login.html
# =============================
"""
<form method="POST">
    Usuario: <input name="user"><br>
    Password: <input type="password" name="password"><br>
    <button>Login</button>
</form>
"""

# =============================
# templates/productos.html
# =============================
"""
{% extends 'base.html' %}
{% block content %}
<h2>Productos</h2>
<form method="POST" action="/productos/nuevo">
    Descripción: <input name="descripcion">
    Precio: <input name="precio">
    Stock: <input name="stock">
    <button>Guardar</button>
</form>

<ul>
{% for p in productos %}
    <li>{{p.DSCPRODUCTO}} - {{p.PRECIO1}}</li>
{% endfor %}
</ul>
{% endblock %}
"""

# =============================
# routes/ventas_routes.py (ACTUALIZADO POS)
# =============================
from flask import Blueprint, render_template, request, redirect, jsonify
from db import get_connection
from datetime import datetime

ventas_bp = Blueprint('ventas', __name__, url_prefix='/ventas')

@ventas_bp.route('/')
def ventas():
    return render_template('ventas.html')

@ventas_bp.route('/buscar_producto', methods=['GET'])
def buscar_producto():
    codigo = request.args.get('codigo')
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT CODPRODUCTO, DSCPRODUCTO, PRECIO1, STOCK
        FROM Productos
        WHERE CODIGOBARRA=? OR DSCPRODUCTO LIKE ?
    """, (codigo, f"%{codigo}%"))

    prod = cursor.fetchone()
    if prod:
        return jsonify({
            'id': prod.CODPRODUCTO,
            'desc': prod.DSCPRODUCTO,
            'precio': float(prod.PRECIO1),
            'stock': prod.STOCK
        })
    return jsonify(None)

@ventas_bp.route('/guardar', methods=['POST'])
def guardar_venta():
    data = request.json

    conn = get_connection()
    cursor = conn.cursor()

    # Cabecera
    cursor.execute("""
        INSERT INTO Movimientos (FecMovimiento, IdPersona, Total, TpoMovimiento)
        VALUES (?,?,?,?)
    """, (datetime.now(), data['cliente'], data['total'], 'VENT'))

    cursor.execute("SELECT @@IDENTITY")
    idMovimiento = cursor.fetchone()[0]

    # Detalle + stock
    for i, item in enumerate(data['items']):
        cursor.execute("""
            INSERT INTO Movimientos_Detalle
            (idMovimiento, orden, CodProducto, Cantidad, PrecioUnitario, Total, estado)
            VALUES (?,?,?,?,?,?,?)
        """, (idMovimiento, i+1, item['id'], item['cantidad'], item['precio'], item['total'], 1))

        # Actualizar stock
        cursor.execute("""
            UPDATE Productos SET STOCK = STOCK - ? WHERE CODPRODUCTO=?
        """, (item['cantidad'], item['id']))

    conn.commit()
    return jsonify({'ok': True})

# =============================
# routes/ventas_routes.py (ACTUALIZADO POS + CLIENTE)
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
    cursor = conn.cursor()

    cursor.execute("""
        SELECT CODPRODUCTO, DSCPRODUCTO, PRECIO1, STOCK
        FROM Productos
        WHERE CODIGOBARRA=? OR DSCPRODUCTO LIKE ?
    """, (codigo, f"%{codigo}%"))

    p = cursor.fetchone()
    if p:
        return jsonify({'id': p.CODPRODUCTO, 'desc': p.DSCPRODUCTO, 'precio': float(p.PRECIO1), 'stock': p.STOCK})
    return jsonify(None)

@ventas_bp.route('/buscar_cliente')
def buscar_cliente():
    q = request.args.get('q')
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT TOP 10 idPersona, RAZONSOCIAL
        FROM Personas
        WHERE TpoPersona='CLIE' AND (RAZONSOCIAL LIKE ? OR CUIT LIKE ?)
    """, (f"%{q}%", f"%{q}%"))

    clientes = cursor.fetchall()
    return jsonify([{'id': c.idPersona, 'nombre': c.RAZONSOCIAL} for c in clientes])

@ventas_bp.route('/guardar', methods=['POST'])
def guardar_venta():
    data = request.json

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO Movimientos (FecMovimiento, IdPersona, Total, TpoMovimiento)
        VALUES (?,?,?,?)
    """, (datetime.now(), data['cliente'], data['total'], 'VENT'))

    cursor.execute("SELECT @@IDENTITY")
    idMovimiento = cursor.fetchone()[0]

    for i, item in enumerate(data['items']):
        cursor.execute("""
            INSERT INTO Movimientos_Detalle
            (idMovimiento, orden, CodProducto, Cantidad, PrecioUnitario, Total, estado)
            VALUES (?,?,?,?,?,?,?)
        """, (idMovimiento, i+1, item['id'], item['cantidad'], item['precio'], item['total'], 1))

        cursor.execute("UPDATE Productos SET STOCK = STOCK - ? WHERE CODPRODUCTO=?",
                       (item['cantidad'], item['id']))

    conn.commit()
    return jsonify({'ok': True})

# =============================
# routes/ventas_routes.py (POS + MOTOR TpoMovimientos)
# =============================
from flask import Blueprint, render_template, request, jsonify
from db import get_connection
from datetime import datetime

ventas_bp = Blueprint('ventas', __name__, url_prefix='/ventas')

@ventas_bp.route('/')
def ventas():
    return render_template('ventas.html')

# =============================
# BUSCAR PRODUCTO
# =============================
@ventas_bp.route('/buscar_producto')
def buscar_producto():
    codigo = request.args.get('codigo')
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT CODPRODUCTO, DSCPRODUCTO, PRECIO1, STOCK
        FROM Productos
        WHERE CODIGOBARRA=? OR DSCPRODUCTO LIKE ?
    """, (codigo, f"%{codigo}%"))

    p = cursor.fetchone()
    if p:
        return jsonify({'id': p.CODPRODUCTO, 'desc': p.DSCPRODUCTO, 'precio': float(p.PRECIO1), 'stock': p.STOCK})
    return jsonify(None)

# =============================
# BUSCAR CLIENTE
# =============================
@ventas_bp.route('/buscar_cliente')
def buscar_cliente():
    q = request.args.get('q')
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT TOP 10 idPersona, RAZONSOCIAL
        FROM Personas
        WHERE TpoPersona='CLIE' AND (RAZONSOCIAL LIKE ? OR CUIT LIKE ?)
    """, (f"%{q}%", f"%{q}%"))

    clientes = cursor.fetchall()
    return jsonify([{'id': c.idPersona, 'nombre': c.RAZONSOCIAL} for c in clientes])

# =============================
# GUARDAR VENTA CON MOTOR
# =============================
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

    # 🔥 Leer configuración del tipo de movimiento
    cursor.execute("SELECT FactorStock, FactorCtaCte FROM TpoMovimientos WHERE tpoMovimiento=?", ('VENT',))
    tpo = cursor.fetchone()

    factor_stock = tpo.FactorStock if tpo else -1
    factor_ctacte = tpo.FactorCtaCte if tpo else 1

    # Cabecera
    cursor.execute("""
        INSERT INTO Movimientos (FecMovimiento, IdPersona, Total, TpoMovimiento,
        TotalEfectivo, TotalTarjeta, TotalTransferencia, TotalCtaCte)
        VALUES (?,?,?,?,?,?,?,?)
    """, (
        datetime.now(), data['cliente'], total, 'VENT',
        efectivo, tarjeta, transferencia, saldo if saldo > 0 else 0
    ))

    cursor.execute("SELECT @@IDENTITY")
    idMovimiento = cursor.fetchone()[0]

    # Detalle + stock dinámico
    for i, item in enumerate(data['items']):
        cursor.execute("""
            INSERT INTO Movimientos_Detalle
            (idMovimiento, orden, CodProducto, Cantidad, PrecioUnitario, Total, estado)
            VALUES (?,?,?,?,?,?,?)
        """, (idMovimiento, i+1, item['id'], item['cantidad'], item['precio'], item['total'], 1))

        # 🔥 Aplicar factor de stock
        cursor.execute("""
            UPDATE Productos SET STOCK = STOCK + (? * ?) WHERE CODPRODUCTO=?
        """, (item['cantidad'], factor_stock, item['id']))

    # Cuenta corriente dinámica
    if saldo > 0 and factor_ctacte != 0:
        tipo = 'DEUD' if factor_ctacte == 1 else 'PAGO'

        cursor.execute("""
            INSERT INTO CuentasCorrientes
            (idMovimiento, Tipo, MontoTotal, Pago, idPersona, FecCtaCte, Concepto)
            VALUES (?,?,?,?,?,?,?)
        """, (
            idMovimiento, tipo, total, total_pagado,
            data['cliente'], datetime.now(), 'Movimiento'
        ))

    conn.commit()
    return jsonify({'ok': True})

# =============================
# templates/ventas.html (POS + PAGOS)
# =============================
# =============================
"""
{% extends 'base.html' %}
{% block content %}
<h2>Venta POS</h2>

<h3>Cliente</h3>
<input id="cliente_buscar" placeholder="Buscar cliente..." onkeyup="buscarCliente()">
<ul id="clientes"></ul>
<p>Seleccionado: <span id="cliente_nombre"></span></p>

<hr>

<input id="codigo" placeholder="Código de barra" autofocus>
<button onclick="agregar()">Agregar</button>

<table border="1" id="tabla">
    <thead>
        <tr>
            <th>Producto</th>
            <th>Cant</th>
            <th>Precio</th>
            <th>Total</th>
        </tr>
    </thead>
    <tbody></tbody>
</table>

<h3>Total: $<span id="total">0</span></h3>

<hr>
<h3>Pagos</h3>
Efectivo: <input id="efectivo" value="0"><br>
Tarjeta: <input id="tarjeta" value="0"><br>
Transferencia: <input id="transferencia" value="0"><br>

<h3>Saldo: $<span id="saldo">0</span></h3>

<button onclick="guardar()">Finalizar Venta</button>

<script>
let items = [];
let clienteSeleccionado = null;

function buscarCliente(){
    let q = document.getElementById('cliente_buscar').value;

    fetch(`/ventas/buscar_cliente?q=${q}`)
    .then(r => r.json())
    .then(data => {
        let ul = document.getElementById('clientes');
        ul.innerHTML = '';

        data.forEach(c => {
            ul.innerHTML += `<li onclick="seleccionarCliente(${c.id}, '${c.nombre}')">${c.nombre}</li>`;
        });
    });
}

function seleccionarCliente(id, nombre){
    clienteSeleccionado = id;
    document.getElementById('cliente_nombre').innerText = nombre;
    document.getElementById('clientes').innerHTML = '';
}

function agregar() {
    let cod = document.getElementById('codigo').value;

    fetch(`/ventas/buscar_producto?codigo=${cod}`)
    .then(r => r.json())
    .then(p => {
        if(!p) return alert('No encontrado');

        let existente = items.find(i => i.id == p.id);

        if(existente){
            existente.cantidad++;
            existente.total = existente.cantidad * existente.precio;
        } else {
            items.push({id: p.id, desc: p.desc, precio: p.precio, cantidad: 1, total: p.precio});
        }

        render();
        document.getElementById('codigo').value = '';
    });
}

function render(){
    let tbody = document.querySelector('#tabla tbody');
    tbody.innerHTML = '';

    let total = 0;

    items.forEach(i => {
        total += i.total;

        tbody.innerHTML += `
        <tr>
            <td>${i.desc}</td>
            <td>${i.cantidad}</td>
            <td>${i.precio}</td>
            <td>${i.total}</td>
        </tr>`;
    });

    document.getElementById('total').innerText = total;
    calcularSaldo();
}

function calcularSaldo(){
    let total = parseFloat(document.getElementById('total').innerText) || 0;
    let ef = parseFloat(document.getElementById('efectivo').value) || 0;
    let ta = parseFloat(document.getElementById('tarjeta').value) || 0;
    let tr = parseFloat(document.getElementById('transferencia').value) || 0;

    let saldo = total - (ef + ta + tr);
    document.getElementById('saldo').innerText = saldo;
}

['efectivo','tarjeta','transferencia'].forEach(id => {
    document.getElementById(id).addEventListener('input', calcularSaldo);
});

function guardar(){
    if(!clienteSeleccionado) return alert('Seleccionar cliente');

    fetch('/ventas/guardar', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({
            cliente: clienteSeleccionado,
            total: document.getElementById('total').innerText,
            efectivo: document.getElementById('efectivo').value,
            tarjeta: document.getElementById('tarjeta').value,
            transferencia: document.getElementById('transferencia').value,
            items: items
        })
    }).then(r => r.json())
    .then(r => {
        alert('Venta guardada');
        items = [];
        clienteSeleccionado = null;
        document.getElementById('cliente_nombre').innerText = '';
        render();
    });
}
</script>

{% endblock %}
"""
