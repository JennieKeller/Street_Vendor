from flask import Flask, jsonify, request, render_template
import pymysql

app = Flask(__name__)

# Configure local MySQL connection
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',       # Updated username
    'password': '',       # Updated password
    'database': 'street_vendor_db',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    return pymysql.connect(**DB_CONFIG)

# HOME ROUTE

@app.route('/')
def home():
    return render_template('index.html')

# GET ENDPOINTS (Read Operations)

# 1. Calculate Production Cost for a specific Product
@app.route('/produtos/<int:produto_id>/custo', methods=['GET'])
def calcular_custo(produto_id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            query = """
                SELECT 
                    p.id AS produto_id,
                    p.nome AS produto,
                    SUM(ft.quantidade_usada * i.custo_unitario) AS custo_total_producao
                FROM produtos p
                JOIN ficha_tecnica ft ON p.id = ft.produto_id
                JOIN ingredientes i ON ft.ingrediente_id = i.id
                WHERE p.id = %s
                GROUP BY p.id, p.nome;
            """
            cursor.execute(query, (produto_id,))
            result = cursor.fetchone()
            
            if not result or result['custo_total_producao'] is None:
                return jsonify({"error": "Product not found or has no ingredients registered."}), 404
                
            return jsonify(result)
    finally:
        connection.close()

# 2. List all Pending Payments
@app.route('/vendas/pendentes', methods=['GET'])
def listar_fiados():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            query = """
                SELECT 
                    v.id AS venda_id,
                    c.nome AS cliente,
                    c.telefone,
                    v.data_venda,
                    v.valor_total
                FROM vendas v
                JOIN clientes c ON v.cliente_id = c.id
                WHERE v.status_pagamento = 'Pendente'
                ORDER BY v.data_venda ASC;
            """
            cursor.execute(query)
            result = cursor.fetchall()
            return jsonify(result)
    finally:
        connection.close()

# POST ENDPOINTS

# 3. Register a New Sale
@app.route('/vendas', methods=['POST'])
def registrar_venda():
    data = request.get_json()
    cliente_id = data.get('cliente_id') # Can be None for walk-ins
    valor_total = data.get('valor_total')
    status_pagamento = data.get('status_pagamento', 'Pendente') # Default to 'Pendente'
    forma_pagamento = data.get('forma_pagamento', 'Dinheiro')
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            query = """
                INSERT INTO vendas (cliente_id, valor_total, status_pagamento, forma_pagamento)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (cliente_id, valor_total, status_pagamento, forma_pagamento))
            connection.commit()
            venda_id = cursor.lastrowid
            
        return jsonify({"message": "Venda registrada com sucesso!", "venda_id": venda_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()

# 4. Register a Business Expense
@app.route('/despesas', methods=['POST'])
def registrar_despesa():
    data = request.get_json()
    descricao = data.get('descricao')
    valor = data.get('valor')
    data_despesa = data.get('data') # Format expected: 'YYYY-MM-DD'
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            query = """
                INSERT INTO despesas (descricao, valor, data)
                VALUES (%s, %s, %s)
            """
            cursor.execute(query, (descricao, valor, data_despesa))
            connection.commit()
            
        return jsonify({"message": "Despesa registrada com sucesso!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()



# RUN SERVER

if __name__ == '__main__':
    app.run(debug=True, port=3000)