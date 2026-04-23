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
