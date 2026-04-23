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
