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
