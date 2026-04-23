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
