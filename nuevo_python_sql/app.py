from flask import Flask, render_template, request
from conexion import obtener_conexion
from fpdf import FPDF
from flask import send_file
import io

app = Flask(__name__)


@app.route('/')
def index():
    conn = obtener_conexion()
    resumen = {'clientes': 0, 'productos': 0, 'facturas': 0}
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM cliente")
        resumen['clientes'] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM productos")
        resumen['productos'] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM factura")
        resumen['facturas'] = cursor.fetchone()[0]
        conn.close()
    return render_template('index.html', resumen=resumen)



from flask import Flask, render_template, request, redirect


@app.route('/clientes', methods=['GET', 'POST'])
@app.route('/clientes/editar/<int:id_edit>', methods=['GET', 'POST'])
def vista_clientes(id_edit=None):
    conn = obtener_conexion()
    mensaje = None
    cliente_a_editar = None

    # EDITAR
    if id_edit and conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cliente WHERE idCliente = ?", (id_edit,))
        row = cursor.fetchone()
        if row:
            columnas = [column[0] for column in cursor.description]
            # elimina espacios vacíos de SQL Server
            cliente_a_editar = {k: (v.strip() if isinstance(v, str) else v) for k, v in zip(columnas, row)}

    # GUARDAR O ACTUALIZAR
    if request.method == 'POST':
        id_clie = request.form.get('id_cliente')
        tipo    = request.form.get('tipo_doc')
        doc     = request.form.get('doc_cliente')
        nom     = request.form.get('nombre')
        ap1     = request.form.get('ape1')
        ap2     = request.form.get('ape2')
        tel     = request.form.get('telefono')
        direc   = request.form.get('direccion')
        fecha   = request.form.get('fecha_nac')
        mail    = request.form.get('email')

        if conn:
            try:
                cursor = conn.cursor()
                if id_edit: # ACTUALIZAR
                    sql = """UPDATE cliente SET tipo_doc_cliente=?, doc_cliente=?, nombres_cliente=?, 
                             ape1_cliente=?, ape2_cliente=?, tell_cliente=?, direccion_cliente=?, 
                             fecha_nac_cliente=?, email_cliente=? WHERE idCliente=?"""
                    cursor.execute(sql, (tipo, doc, nom, ap1, ap2, tel, direc, fecha, mail, id_edit))
                else: # INSERTAR
                    sql = """INSERT INTO cliente (idCliente, tipo_doc_cliente, doc_cliente, nombres_cliente, 
                             ape1_cliente, ape2_cliente, tell_cliente, direccion_cliente, 
                             fecha_nac_cliente, email_cliente) VALUES (?,?,?,?,?,?,?,?,?,?)"""
                    cursor.execute(sql, (id_clie, tipo, doc, nom, ap1, ap2, tel, direc, fecha, mail))
                
                conn.commit()
                return redirect('/clientes')
            except Exception as e:
                mensaje = f"❌ Error: {e}"

    # LISTAR EN LA TABLA
    clientes_lista = []
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cliente")
        columnas = [column[0] for column in cursor.description]
        for r in cursor.fetchall():
            # También limpiamos los datos que van a la tabla
            clientes_lista.append({k: (v.strip() if isinstance(v, str) else v) for k, v in zip(columnas, r)})
        conn.close()

    return render_template('clientes.html', clientes=clientes_lista, editando=cliente_a_editar, mensaje=mensaje)

 #RUTA PARA ELIMINAR 
@app.route('/eliminar_cliente/<int:id>')
def eliminar_cliente(id):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cliente WHERE idCliente = ?", (id,))
            conn.commit()
            conn.close()
            return redirect('/clientes')
        except Exception as e:
            
            print(f"Error de integridad: {e}")
            return redirect('/clientes?error=fk')
    
    return redirect('/clientes')


@app.route('/buscar_cliente', methods=['GET', 'POST'])
def buscar_cliente():
    
    pass


from flask import Flask, render_template, request, redirect, url_for



@app.route('/productos', methods=['GET', 'POST'])
@app.route('/productos/editar/<int:id_edit>', methods=['GET', 'POST'])
def vista_productos(id_edit=None):
    conn = obtener_conexion()
    mensaje = None
    prod_a_editar = None

    def procesar_fila(cursor, row):
        # Convertimos nombres de columnas a minúsculas para evitar errores en el HTML
        columnas = [column[0].lower() for column in cursor.description]
        return {k: (v.strip() if isinstance(v, str) else v) for k, v in zip(columnas, row)}

    # CARGAR DATOS 
    if id_edit and conn:
        cursor = conn.cursor()
        sql_edit = """
            SELECT p.*, s.cantidad 
            FROM productos p 
            JOIN stock s ON p.stock_idstock = s.idstock 
            WHERE p.idProductos = ?
        """
        cursor.execute(sql_edit, (id_edit,))
        row = cursor.fetchone()
        if row:
            prod_a_editar = procesar_fila(cursor, row)

    # CREAR O EDITAR
    if request.method == 'POST':
        nom = request.form.get('nombre')
        des = request.form.get('descripcion')
        pre = request.form.get('precio')
        cantidad_ingresada = request.form.get('stock')

        if conn:
            try:
                cursor = conn.cursor()
                if id_edit:
                    # ACTUALIZAR
                    cursor.execute("""
                        UPDATE stock SET cantidad = ? 
                        WHERE idstock = (SELECT stock_idstock FROM productos WHERE idProductos = ?)
                    """, (cantidad_ingresada, id_edit))
                    
                    cursor.execute("""
                        UPDATE productos SET nombre_productos=?, drescripcion=?, precio=? 
                        WHERE idProductos=?
                    """, (nom, des, pre, id_edit))
                else:
                   
                    # Insertar en tabla 
                    cursor.execute("SELECT ISNULL(MAX(idstock), 0) + 1 FROM stock")
                    nuevo_id_stock = cursor.fetchone()[0]
                    
                    # columna fecha
                    cursor.execute("""
                        INSERT INTO stock (idstock, cantidad, fecha) 
                        VALUES (?, ?, GETDATE())
                    """, (nuevo_id_stock, cantidad_ingresada))
                    
                    # Insertar en tabla PRODUCTOS
                    cursor.execute("SELECT ISNULL(MAX(idProductos), 0) + 1 FROM productos")
                    nuevo_id_prod = cursor.fetchone()[0]
                    
                    
                    sql_ins = """INSERT INTO productos (idProductos, nombre_productos, drescripcion, precio, 
                                 factura_idfactura, factura_Cliente_idCliente, factura_Vendedor_idvendedor, 
                                 factura_Metodo_pago_idMetodo_pago, stock_idstock) 
                                 VALUES (?, ?, ?, ?, 1, 1, 1, 1, ?)"""
                    cursor.execute(sql_ins, (nuevo_id_prod, nom, des, pre, nuevo_id_stock))
                
                conn.commit()
                return redirect('/productos')
            except Exception as e:
                mensaje = f"Error en la operación: {e}"
                print(f"Log de error: {e}")

    #LISTAR PRODUCTOS
    productos_lista = []
    if conn:
        cursor = conn.cursor()
        # cantidad total
        sql_list = """
            SELECT p.idproductos, p.nombre_productos, p.drescripcion, p.precio, s.cantidad 
            FROM productos p 
            JOIN stock s ON p.stock_idstock = s.idstock
        """
        cursor.execute(sql_list)
        for r in cursor.fetchall():
            productos_lista.append(procesar_fila(cursor, r))
        conn.close()

    return render_template('productos.html', productos=productos_lista, editando=prod_a_editar, mensaje=mensaje)

#RUTA PARA ELIMINAR
@app.route('/eliminar_producto/<int:id>')
def eliminar_producto(id):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            
            
            cursor.execute("SELECT stock_idstock FROM productos WHERE idProductos = ?", (id,))
            resultado = cursor.fetchone()
            
            if resultado:
                id_stock_a_borrar = resultado[0]
                
                
                cursor.execute("DELETE FROM productos WHERE idProductos = ?", (id,))
                
               
                cursor.execute("DELETE FROM stock WHERE idstock = ?", (id_stock_a_borrar,))
                
                conn.commit()
                print(f"Éxito: Producto {id} y Stock {id_stock_a_borrar} eliminados.")
            
            conn.close()
        except Exception as e:
            print(f"Error al eliminar: {e}")
    return redirect('/productos')

@app.route('/nueva_factura')
def nueva_factura():
    conn = obtener_conexion()
    cursor = conn.cursor()

    try:
        
        cursor.execute("SELECT idCliente, nombres_Cliente FROM cliente")
        clientes = cursor.fetchall()
        
        cursor.execute("SELECT idvendedor, nombres_Vendedor FROM vendedor")
        vendedores = cursor.fetchall()

        cursor.execute("""
            SELECT p.idProductos, p.nombre_productos, p.precio, s.cantidad 
            FROM productos p 
            JOIN stock s ON p.stock_idstock = s.idstock
        """)
        productos = [dict(zip([col[0].lower() for col in cursor.description], row)) for row in cursor.fetchall()]

        #Métodos de Pago
        cursor.execute("SELECT idMetodo_pago, efectivo, tarjeta, transferencia, llave FROM metodo_pago")
        metodos_raw = cursor.fetchall()
        metodos_procesados = []
        for m in metodos_raw:
            if m[1] and m[1] != 'No': nombre = "Efectivo"
            elif m[2] and m[2] != 'No': nombre = "Tarjeta"
            elif m[3] and m[3] != 'No': nombre = "Transferencia"
            elif m[4] and m[4] != 'No': nombre = "Llave"
            else: continue
            metodos_procesados.append({'id': m[0], 'nombre': nombre})

        # HISTORIAL
        cursor.execute("""
            SELECT 
                f.idfactura, 
                c.nombres_Cliente, 
                v.nombres_Vendedor, 
                CASE 
                    WHEN m.efectivo != 'No' THEN 'Efectivo'
                    WHEN m.tarjeta != 'No' THEN 'Tarjeta'
                    WHEN m.transferencia != 'No' THEN 'Transferencia'
                    ELSE 'Llave'
                END as Pago,
                -- Aquí traemos el nombre, la cantidad y el precio
                ISNULL((SELECT STRING_AGG(
                            p.nombre_productos + ' (Cant: ' + CAST(php.productos_stock_idstock AS VARCHAR) + ') - $' + CAST(p.precio AS VARCHAR), 
                            ' | '
                        ) 
                        FROM proveedor_has_productos php
                        JOIN productos p ON php.productos_idProductos = p.idProductos
                        WHERE php.productos_factura_idfactura = f.idfactura), 'Sin detalle') as Articulos
            FROM factura f
            JOIN cliente c ON f.Cliente_idCliente = c.idCliente
            JOIN vendedor v ON f.Vendedor_idvendedor = v.idvendedor
            JOIN metodo_pago m ON f.Metodo_pago_idMetodo_pago = m.idMetodo_pago
        """)
        historial = cursor.fetchall()
        

        conn.close() # Cerramos conexión al final para evitar errores
        return render_template('nueva_factura.html', clientes=clientes, vendedores=vendedores, 
                               productos=productos, metodos=metodos_procesados, facturas_viejas=historial)
    except Exception as e:
        if conn: conn.close()
        return f"Error: {str(e)}"
    

@app.route('/guardar_factura', methods=['POST'])
def guardar_factura():
    cliente_id = request.form.get('cliente_id')
    vendedor_id = request.form.get('vendedor_id')
    metodo_id = request.form.get('metodo_id')
    prod_ids = request.form.getlist('prod_ids[]') 

    conn = obtener_conexion()
    cursor = conn.cursor()

    try:
        # Generar nuevo ID 
        cursor.execute("SELECT ISNULL(MAX(idfactura), 0) + 1 FROM factura")
        nuevo_id_f = cursor.fetchone()[0]

        # Insertar factura
        cursor.execute("""
            INSERT INTO factura (idfactura, Cliente_idCliente, Vendedor_idvendedor, Metodo_pago_idMetodo_pago)
            VALUES (?, ?, ?, ?)
        """, (nuevo_id_f, cliente_id, vendedor_id, metodo_id))


        for p_id in prod_ids:
           
            cursor.execute("SELECT stock_idstock FROM productos WHERE idProductos = ?", (p_id,))
            res_prod = cursor.fetchone()
            
            if res_prod:
                stock_id = res_prod[0]
              
                prov_id = 1 

                cursor.execute("""
                    INSERT INTO proveedor_has_productos (
                        proveedor_idproveedor, productos_idProductos, 
                        productos_factura_idfactura, productos_factura_Cliente_idCliente,
                        productos_factura_Vendedor_idvendedor, productos_factura_Metodo_pago_idMetodo_pago,
                        productos_stock_idstock
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (prov_id, p_id, nuevo_id_f, cliente_id, vendedor_id, metodo_id, stock_id))

                
                cursor.execute("UPDATE stock SET cantidad = CAST(CAST(cantidad AS INT) - 1 AS VARCHAR(45)) WHERE idstock = ?", (stock_id,))
        conn.commit()
        conn.close()
        return redirect('/nueva_factura')
    except Exception as e:
        if conn: conn.rollback(); conn.close()
        return f"Error al guardar: {str(e)}"
    
    # ELIMINAR
@app.route('/eliminar_factura/<int:id>')
def eliminar_factura(id):
    conn = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM proveedor_has_productos WHERE productos_factura_idfactura = ?", (id,))
        
        
        cursor.execute("DELETE FROM factura WHERE idfactura = ?", (id,))
        
        conn.commit()
        conn.close()
        return redirect('/nueva_factura')
    except Exception as e:
        if conn: conn.rollback(); conn.close()
        return f"Error al eliminar: {str(e)}"


@app.route('/actualizar_factura/<int:id>', methods=['POST'])
def actualizar_factura(id):
    c_id = request.form.get('cliente_id')
    v_id = request.form.get('vendedor_id')

    conn = obtener_conexion()
    cursor = conn.cursor()
    try:
        # Actualizar
        cursor.execute("UPDATE factura SET Cliente_idCliente = ?, Vendedor_idvendedor = ? WHERE idfactura = ?", (c_id, v_id, id))
        
        
        cursor.execute("""
            UPDATE proveedor_has_productos 
            SET productos_factura_Cliente_idCliente = ?, productos_factura_Vendedor_idvendedor = ? 
            WHERE productos_factura_idfactura = ?
        """, (c_id, v_id, id))
        
        conn.commit()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
    return redirect('/nueva_factura')


@app.route('/pedido_proveedor', methods=['GET', 'POST'])
def pedido_proveedor():
    conn = obtener_conexion()
    cursor = conn.cursor()

    if request.method == 'POST':
        prov_id = request.form.get('proveedor_id')
        prod_id = request.form.get('producto_id')
        cantidad_ingresada = int(request.form.get('cantidad'))

        try:
            # Obtener el stock del producto
            cursor.execute("SELECT stock_idstock FROM productos WHERE idProductos = ?", (prod_id,))
            stock_id = cursor.fetchone()[0]

            # Sumar al stock real
            cursor.execute("""
                UPDATE stock 
                SET cantidad = CAST(CAST(cantidad AS INT) + ? AS VARCHAR(45)) 
                WHERE idstock = ?
            """, (cantidad_ingresada, stock_id))


            cursor.execute("""
                INSERT INTO proveedor_has_productos (
                    proveedor_idproveedor, productos_idProductos, 
                    productos_stock_idstock, productos_factura_idfactura,
                    productos_factura_Cliente_idCliente, productos_factura_Vendedor_idvendedor,
                    productos_factura_Metodo_pago_idMetodo_pago
                ) VALUES (?, ?, ?, 1, 1, 1, 1)
            """, (prov_id, prod_id, stock_id))

            conn.commit()
            return redirect('/pedido_proveedor')
        except Exception as e:
            conn.rollback()
            return f"Error: {e}"

    # Carga de datos para los selectores
    cursor.execute("SELECT idproveedor, nombre_proveedor FROM proveedor")
    proveedores = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]

    cursor.execute("SELECT idProductos, nombre_productos FROM productos")
    productos = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]

    # HISTORIAL
    cursor.execute("""
        SELECT 
            p.nombre_productos, 
            prov.nombre_proveedor, 
            s.cantidad as cantidad_stock
        FROM proveedor_has_productos php
        JOIN productos p ON php.productos_idProductos = p.idProductos
        JOIN proveedor prov ON php.proveedor_idproveedor = prov.idproveedor
        JOIN stock s ON php.productos_stock_idstock = s.idstock
        WHERE php.productos_factura_idfactura = 1 -- Filtramos solo entradas de proveedor
    """)
    historial_raw = cursor.fetchall()
    historial = [{'nombre_producto': r[0], 'nombre_proveedor': r[1], 'cantidad': r[2]} for r in historial_raw]

    conn.close()
    return render_template('pedido_proveedor.html', 
                           proveedores=proveedores, 
                           productos=productos, 
                           historial=historial)

@app.route('/estadisticas')
def estadisticas():
    conn = obtener_conexion()
    cursor = conn.cursor()
    
    try:
        # CONSULTA: El Cliente Estrella 
        cursor.execute("""
            SELECT TOP 1 
                c.nombres_Cliente, 
                COUNT(f.idfactura) AS total_compras,
                -- Subconsulta para el método de pago
                (SELECT TOP 1 CASE 
                    WHEN mp.efectivo != 'No' THEN 'Efectivo' 
                    WHEN mp.tarjeta != 'No' THEN 'Tarjeta' ELSE 'Otros' END 
                FROM factura f2 
                JOIN metodo_pago mp ON f2.Metodo_pago_idMetodo_pago = mp.idMetodo_pago 
                WHERE f2.Cliente_idCliente = f.Cliente_idCliente),
                -- Subconsulta para el producto que más compra
                (SELECT TOP 1 p2.nombre_productos 
                FROM proveedor_has_productos php2 
                JOIN productos p2 ON php2.productos_idProductos = p2.idProductos
                WHERE php2.productos_factura_Cliente_idCliente = f.Cliente_idCliente
                GROUP BY p2.nombre_productos 
                ORDER BY COUNT(*) DESC) AS producto_favorito
            FROM factura f
            JOIN cliente c ON f.Cliente_idCliente = c.idCliente
            GROUP BY c.nombres_Cliente, f.Cliente_idCliente
            ORDER BY total_compras DESC
        """)
        cliente_estrella = cursor.fetchone()
        

        # CONSULTA: Proveedor con mayor ingreso de productos
        cursor.execute("""
            SELECT TOP 1 
                prov.nombre_proveedor, 
                SUM(CAST(php.productos_stock_idstock AS INT)) AS total_unidades,
                SUM(CAST(p.precio AS FLOAT) * CAST(php.productos_stock_idstock AS INT)) AS inversion_total,
                (SELECT TOP 1 p2.nombre_productos 
                FROM proveedor_has_productos php2 
                JOIN productos p2 ON php2.productos_idProductos = p2.idProductos
                WHERE php2.proveedor_idproveedor = prov.idproveedor
                GROUP BY p2.nombre_productos 
                ORDER BY SUM(CAST(php2.productos_stock_idstock AS INT)) DESC) AS producto_principal
            FROM proveedor prov
            JOIN proveedor_has_productos php ON prov.idproveedor = php.proveedor_idproveedor
            JOIN productos p ON php.productos_idProductos = p.idProductos
            WHERE php.productos_factura_idfactura = 1 
            GROUP BY prov.nombre_proveedor, prov.idproveedor
            ORDER BY total_unidades DESC
        """)
        mejor_proveedor = cursor.fetchone()

        # CONSULTA: El mejor vendedor
        cursor.execute("""
            SELECT TOP 1 
                v.nombres_Vendedor, 
                SUM(CAST(php.productos_stock_idstock AS INT)) AS total_productos_vendidos,
                (SELECT TOP 1 p2.nombre_productos 
                 FROM proveedor_has_productos php2 
                 JOIN productos p2 ON php2.productos_idProductos = p2.idProductos
                 WHERE php2.productos_factura_Vendedor_idvendedor = v.idvendedor
                   AND php2.productos_factura_idfactura > 1 -- Solo ventas, no pedidos
                 GROUP BY p2.nombre_productos 
                 ORDER BY COUNT(*) DESC) AS producto_mas_vendido
            FROM vendedor v
            JOIN proveedor_has_productos php ON v.idvendedor = php.productos_factura_Vendedor_idvendedor
            WHERE php.productos_factura_idfactura > 1 -- Filtramos para que sean solo ventas
            GROUP BY v.nombres_Vendedor, v.idvendedor
            ORDER BY total_productos_vendidos DESC
        """)
        mejor_vendedor = cursor.fetchone()

  # CONSULTA: Producto más vendido
        cursor.execute("""
            SELECT TOP 1 
                p.nombre_productos, 
                p.precio, 
                COUNT(DISTINCT php.productos_factura_idfactura) AS total_facturas,
                SUM(CAST(php.productos_stock_idstock AS INT)) AS unidades_totales
            FROM productos p
            JOIN proveedor_has_productos php ON p.idProductos = php.productos_idProductos
            WHERE php.productos_factura_idfactura > 1 -- Solo ventas reales
            GROUP BY p.nombre_productos, p.precio, p.idProductos
            ORDER BY unidades_totales DESC
        """)
        producto_top = cursor.fetchone()

        # CONSULTA: Producto con más existencias
        cursor.execute("""
            SELECT TOP 1 
                p.nombre_productos, 
                s.cantidad AS existencias, 
                p.precio, 
                prov.nombre_proveedor
            FROM productos p
            JOIN stock s ON p.stock_idstock = s.idstock
            CROSS APPLY (
                SELECT TOP 1 ph.proveedor_idproveedor 
                FROM proveedor_has_productos ph 
                WHERE ph.productos_idProductos = p.idProductos 
                  AND ph.productos_factura_idfactura = 1 -- Filtramos por entrada de proveedor
                ORDER BY ph.productos_factura_idfactura ASC 
            ) last_prov
            JOIN proveedor prov ON last_prov.proveedor_idproveedor = prov.idproveedor
            ORDER BY CAST(s.cantidad AS INT) DESC
        """)
        producto_stock_max = cursor.fetchone()


    except Exception as e:
        return f"Error en consultas: {str(e)}"
    finally:
        conn.close()

    return render_template('estadisticas.html', 
                           cliente=cliente_estrella, 
                           mejor_proveedor=mejor_proveedor, 
                           vendedor_estrella=mejor_vendedor,
                           producto_top=producto_top,
                           stock_max=producto_stock_max)


from datetime import datetime

@app.route('/descargar_factura/<int:id_factura>')
def descargar_factura(id_factura):
    conn = obtener_conexion()
    cursor = conn.cursor()

    try:
        # 1. Obtener datos básicos (Sin la columna 'fecha' que no existe)
        cursor.execute("""
            SELECT f.idfactura, c.nombres_Cliente, v.nombres_Vendedor
            FROM factura f
            JOIN cliente c ON f.Cliente_idCliente = c.idCliente
            JOIN vendedor v ON f.Vendedor_idvendedor = v.idvendedor
            WHERE f.idfactura = ?
        """, (id_factura,))
        datos_f = cursor.fetchone()

        if not datos_f:
            return "Factura no encontrada", 404

        # 2. Obtener los productos de esa factura
        cursor.execute("""
            SELECT p.nombre_productos, p.precio, php.productos_stock_idstock as cantidad
            FROM proveedor_has_productos php
            JOIN productos p ON php.productos_idProductos = p.idProductos
            WHERE php.productos_factura_idfactura = ?
        """, (id_factura,))
        items = cursor.fetchall()

        # 3. Crear el PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        
        pdf.cell(190, 10, "TIENDA DE CALZADO UNIMINUTO", ln=True, align='C')
        pdf.set_font("Arial", size=12)
        pdf.cell(190, 10, f"Factura Nro: {datos_f[0]}", ln=True, align='R')
        
        # Usamos la fecha actual del servidor
        fecha_hoy = datetime.now().strftime("%d/%m/%Y")
        pdf.cell(190, 10, f"Fecha: {fecha_hoy}", ln=True, align='R')
        pdf.ln(10)

        pdf.set_font("Arial", 'B', 12)
        pdf.cell(100, 10, f"Cliente: {datos_f[1]}", ln=False)
        pdf.cell(90, 10, f"Vendedor: {datos_f[2]}", ln=True)
        pdf.ln(5)

        # Encabezados de tabla
        pdf.set_fill_color(230, 230, 230)
        pdf.cell(90, 10, "Producto", 1, 0, 'C', True)
        pdf.cell(30, 10, "Cant.", 1, 0, 'C', True)
        pdf.cell(35, 10, "Precio Unit.", 1, 0, 'C', True)
        pdf.cell(35, 10, "Subtotal", 1, 1, 'C', True)

        total = 0
        pdf.set_font("Arial", size=11)
        for item in items:
            nombre, precio, cant = item[0], float(item[1]), int(item[2])
            subtotal = precio * cant
            total += subtotal
            pdf.cell(90, 10, nombre, 1)
            pdf.cell(30, 10, str(cant), 1, 0, 'C')
            pdf.cell(35, 10, f"${precio:,.2f}", 1, 0, 'R')
            pdf.cell(35, 10, f"${subtotal:,.2f}", 1, 1, 'R')

        pdf.set_font("Arial", 'B', 12)
        pdf.cell(155, 10, "TOTAL A PAGAR:", 1, 0, 'R')
        pdf.cell(35, 10, f"${total:,.2f}", 1, 1, 'R')

        output = io.BytesIO()
        # El encode latin-1 previene errores con tildes
        pdf_out = pdf.output(dest='S').encode('latin-1', 'ignore') 
        output.write(pdf_out)
        output.seek(0)

        return send_file(output, mimetype='application/pdf', 
                         as_attachment=True, 
                         download_name=f"Factura_{id_factura}.pdf")

    except Exception as e:
        return f"Error al generar PDF: {str(e)}"
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)