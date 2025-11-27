# --- Importações Essenciais ---
import sqlite3
import datetime
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# --- Caminhos Importantes ---
# PASTA_RAIZ_PROJETO é a pasta '.../PROJETO HOSTS' (a pasta "pai" da pasta 'SQLite')
PASTA_RAIZ_PROJETO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# PASTA_SQLITE é onde este script (api.py) está
PASTA_SQLITE = os.path.dirname(__file__)

# O caminho correto para o banco de dados (que está DENTRO da pasta SQLite)
DB_FILE = os.path.join(PASTA_SQLITE, 'meu_banco.db') 

# --- Configuração do Aplicativo Flask ---
# Configura o Flask para servir arquivos estáticos (css, js) da PASTA_RAIZ_PROJETO
app = Flask(__name__, static_folder=PASTA_RAIZ_PROJETO)

# Habilita CORS para todas as rotas da API (prefixo /api/)
CORS(app, resources={r"/api/*": {"origins": "*"}})


# --- Rotas do Servidor Web (Front-end) ---

@app.route('/') # Rota para a raiz (ex: http://127.0.0.1:5000/)
def serve_index():
    """ Envia o usuário para a página de login por padrão. """
    try:
        # Tenta servir 'login.html' da pasta 'login'
        return send_from_directory(os.path.join(PASTA_RAIZ_PROJETO, 'login'), 'login.html')
    except FileNotFoundError:
        return "Erro: Arquivo 'login/login.html' não encontrado.", 404

@app.route('/<path:filename>')
def serve_static_files(filename):
    """
    Esta rota serve todos os seus arquivos de front-end (CSS, JS, HTML, imagens).
    Ela é inteligente e procura nas pastas certas.
    """
    
    # 1. Tenta servir o arquivo da raiz (pega css/style.css, js/script.js, imagens/logo.png, etc.)
    full_path = os.path.join(PASTA_RAIZ_PROJETO, filename)
    if os.path.isfile(full_path):
        return send_from_directory(PASTA_RAIZ_PROJETO, filename)

    # 2. Tenta servir da pasta 'templates' (dashboard.html, home.html, etc.)
    template_path = os.path.join(PASTA_RAIZ_PROJETO, 'templates', filename)
    if os.path.isfile(template_path):
        return send_from_directory(os.path.join(PASTA_RAIZ_PROJETO, 'templates'), filename)

    # 3. Tenta servir da pasta 'login' (caso seja chamado diretamente)
    login_path = os.path.join(PASTA_RAIZ_PROJETO, 'login', filename)
    if os.path.isfile(login_path):
        return send_from_directory(os.path.join(PASTA_RAIZ_PROJETO, 'login'), filename)

    # 4. Fallback: Se não achar, retorna um erro 404
    return "Arquivo não encontrado.", 404


# --- Funções de Banco de Dados (Helpers) ---

def conectar():
    """
    Cria e retorna uma conexão com o banco.
    Usamos 'row_factory' para que o banco retorne dicionários.
    """
    conexao = sqlite3.connect(DB_FILE)
    conexao.row_factory = sqlite3.Row 
    return conexao

def registrar_alerta(tipo, mensagem):
    """ Insere um novo registro na tabela 'alertas'. """
    try:
        data_agora = datetime.datetime.now().isoformat()
        conexao = conectar()
        conexao.execute(
            "INSERT INTO alertas (data_hora, tipo_alerta, mensagem) VALUES (?, ?, ?)",
            (data_agora, tipo, mensagem)
        )
        conexao.commit()
    except Exception as e:
        print(f"ERRO AO REGISTRAR ALERTA: {e}")
    finally:
        if 'conexao' in locals() and conexao:
            conexao.close()

def criar_tabelas_iniciais():
    """ Garante que TODAS as tabelas existam e a coluna 'tipo' em ativos_online. """
    try:
        conexao = conectar()
        
        # 1. Tabela de Usuários
        conexao.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT,
            senha TEXT NOT NULL
        )''')
        
        # 2. Tabela de Ativos
        conexao.execute('''
        CREATE TABLE IF NOT EXISTS ativos_online (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            ip_address TEXT,
            mac_address TEXT,
            status TEXT,
            condicao TEXT,
            data_inicio TEXT,
            tipo TEXT 
        )''')
        
        # 3. Tabela de Alertas
        conexao.execute('''
        CREATE TABLE IF NOT EXISTS alertas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora TEXT NOT NULL,
            tipo_alerta TEXT,
            mensagem TEXT
        )''')

        # --- NOVIDADE: Adicionar coluna 'tipo' em ativos_online, se não existir ---
        try:
            conexao.execute("ALTER TABLE ativos_online ADD COLUMN tipo TEXT")
            print("INFO: Coluna 'tipo' adicionada à tabela 'ativos_online'.")
        except sqlite3.OperationalError as e:
            # Ignora o erro se a coluna já existe
            if "duplicate column name: tipo" not in str(e):
                raise e 

        conexao.commit()
        print("Todas as tabelas (Usuários, Ativos, Alertas) foram verificadas/criadas/atualizadas.")
        
    except Exception as e:
        print(f"Erro ao criar tabelas: {e}")
    finally:
        if 'conexao' in locals() and conexao:
            conexao.close()


# =======================================================
#  ROTAS DA API (ENDPOINTS)
# =======================================================

# --- ROTA DE LOGIN ---
@app.route('/api/login', methods=['POST'])
def login():
    dados = request.json
    email = dados.get('email').strip() if dados.get('email') else None
    senha = dados.get('senha').strip() if dados.get('senha') else None

    # DEBUG EXPLÍCITO NO TERMINAL
    print(f"\n--- TENTATIVA DE LOGIN ---")
    print(f"Email recebido: '{email}'")

    if not email or not senha:
        print("RESULTADO: Falha (Credenciais ausentes)")
        return jsonify({"erro": "Email e senha são obrigatórios"}), 400

    try:
        conexao = conectar()
        cursor = conexao.cursor()
        
        # Tenta buscar o usuário pelo e-mail
        cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
        usuario = cursor.fetchone()
        
        if not usuario:
            print("RESULTADO: Falha (Usuário não encontrado no DB)")
            conexao.close()
            return jsonify({"erro": "Email ou senha incorretos"}), 401 
            
        # Limpa espaços em branco na senha armazenada (se houver)
        senha_db = usuario['senha'].strip()
        
        # DEBUG: Exibir senha do banco
        print(f"Senha do banco (DEBUG): '{senha_db}' | Senha digitada: '{senha}'")
        
        # Compara a senha do banco com a senha recebida
        if senha_db != senha: 
            print("RESULTADO: Falha (Senha incorreta)")
            conexao.close()
            return jsonify({"erro": "Email ou senha incorretos"}), 401

        # Sucesso
        print(f"RESULTADO: SUCESSO! Usuário: {usuario['nome']}")
        conexao.close()
        user_data = {
            "id": usuario['id'],
            "nome": usuario['nome'],
            "email": usuario['email']
        }
        return jsonify({"mensagem": "Login bem-sucedido!", "usuario": user_data}), 200

    except Exception as e:
        print(f"ERRO DE SERVIDOR NO LOGIN: {e}")
        return jsonify({"erro": str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    return jsonify({"mensagem": "Logout bem-sucedido!"}), 200


# --- ROTA DE TROCA DE SENHA (NOVA) ---
@app.route('/api/trocar-senha', methods=['POST'])
def trocar_senha():
    dados = request.json
    id_usuario = dados.get('id')
    senha_atual = dados.get('senha_atual')
    nova_senha = dados.get('nova_senha')

    if not id_usuario or not senha_atual or not nova_senha:
        return jsonify({"erro": "Todos os campos são obrigatórios."}), 400

    try:
        conexao = conectar()
        cursor = conexao.cursor()

        # 1. Verifica se a senha atual está correta para este usuário
        cursor.execute("SELECT senha FROM usuarios WHERE id = ?", (id_usuario,))
        resultado = cursor.fetchone()

        if not resultado:
            conexao.close()
            return jsonify({"erro": "Usuário não encontrado."}), 404
        
        senha_no_banco = resultado['senha'].strip()

        # Verifica se a senha antiga digitada bate com a do banco
        if senha_no_banco != senha_atual.strip():
            conexao.close()
            return jsonify({"erro": "A senha atual está incorreta."}), 401

        # 2. Se a senha antiga bateu, atualiza para a nova
        cursor.execute("UPDATE usuarios SET senha = ? WHERE id = ?", (nova_senha.strip(), id_usuario))
        conexao.commit()
        conexao.close()

        print(f"Sucesso: Senha alterada para o usuário ID {id_usuario}")
        return jsonify({"mensagem": "Senha alterada com sucesso!"}), 200

    except Exception as e:
        print(f"Erro ao trocar senha: {e}")
        return jsonify({"erro": str(e)}), 500


# --- CRUD: USUÁRIOS ---

@app.route('/api/usuarios', methods=['GET'])
def get_usuarios():
    """ (R)ead: Lista todos os usuários. """
    conexao = conectar()
    usuarios_db = conexao.execute("SELECT * FROM usuarios").fetchall()
    conexao.close()
    return jsonify([dict(usuario) for usuario in usuarios_db])

@app.route('/api/usuarios', methods=['POST'])
def add_usuario():
    """ (C)reate: Adiciona um novo usuário (com senha). """
    dados = request.json
    nome = dados.get('nome')
    email = dados.get('email')
    senha = dados.get('senha')

    if not nome or not email or not senha:
        return jsonify({"erro": "Nome, email e senha são obrigatórios"}), 400

    try:
        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute(
            "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
            (nome, email, senha)
        )
        conexao.commit()
        novo_id = cursor.lastrowid
        conexao.close()
        return jsonify({"mensagem": "Usuário adicionado com sucesso!", "id": novo_id}), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/api/usuarios/<int:id_usuario>', methods=['PUT'])
def update_usuario(id_usuario):
    """ (U)pdate: Atualiza um usuário. """
    dados = request.json
    nome = dados.get('nome')
    email = dados.get('email')
    senha = dados.get('senha')

    if not nome or not email or not senha:
        return jsonify({"erro": "Nome, email e senha são obrigatórios"}), 400

    try:
        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute(
            "UPDATE usuarios SET nome = ?, email = ?, senha = ? WHERE id = ?",
            (nome, email, senha, id_usuario)
        )
        conexao.commit()
        
        if cursor.rowcount == 0:
            conexao.close()
            return jsonify({"erro": "Usuário não encontrado"}), 404
        
        conexao.close()
        return jsonify({"mensagem": "Usuário atualizado com sucesso!"})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/api/usuarios/<int:id_usuario>', methods=['DELETE'])
def delete_usuario(id_usuario):
    """ (D)elete: Deleta um usuário. """
    try:
        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM usuarios WHERE id = ?", (id_usuario,))
        conexao.commit()

        if cursor.rowcount == 0:
            conexao.close()
            return jsonify({"erro": "Usuário não encontrado"}), 404
        
        conexao.close()
        return jsonify({"mensagem": "Usuário deletado com sucesso!"})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


# --- CRUD: ATIVOS ---

@app.route('/api/ativos', methods=['GET'])
def get_ativos():
    """ (R)ead: Lista todos os ativos. """
    conexao = conectar()
    ativos_db = conexao.execute("SELECT * FROM ativos_online").fetchall()
    conexao.close()
    return jsonify([dict(ativo) for ativo in ativos_db])

@app.route('/api/ativos', methods=['POST'])
def add_ativo():
    """ (C)reate: Adiciona um novo ativo E REGISTRA O ALERTA. """
    dados = request.json
    nome = dados.get('nome')
    ip = dados.get('ip_address')
    
    # Recebe o tipo do ativo
    tipo = dados.get('tipo', 'Outros') # Define 'Outros' como padrão se não for enviado
    
    if not nome:
        return jsonify({"erro": "O campo 'nome' é obrigatório"}), 400
    
    data_inicio = datetime.datetime.now().isoformat()
    mac = dados.get('mac_address')
    status = dados.get('status', 'Pendente') 
    condicao = dados.get('condicao', 'Desconhecida') 

    try:
        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute(
            "INSERT INTO ativos_online (nome, ip_address, mac_address, status, condicao, data_inicio, tipo) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (nome, ip, mac, status, condicao, data_inicio, tipo)
        )
        conexao.commit()
        novo_id = cursor.lastrowid
        conexao.close()
        
        registrar_alerta("Adição", f"Novo ativo entrou na rede: {nome} ({tipo}) (IP: {ip}, ID: {novo_id})")
        
        return jsonify({"mensagem": "Ativo adicionado e alerta registrado!", "id": novo_id}), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/api/ativos/<int:id_ativo>', methods=['PUT'])
def update_ativo(id_ativo):
    """ (U)pdate: Atualiza um ativo. """
    dados = request.json
    nome = dados.get('nome')
    ip = dados.get('ip_address')
    mac = dados.get('mac_address')
    status = dados.get('status')
    condicao = dados.get('condicao')
    tipo = dados.get('tipo') 

    if not nome or not status or not condicao:
        return jsonify({"erro": "Nome, status e condição são campos obrigatórios"}), 400
    
    # Constrói o comando de UPDATE dinamicamente
    sql_update = "UPDATE ativos_online SET nome = ?, ip_address = ?, mac_address = ?, status = ?, condicao = ?"
    params = [nome, ip, mac, status, condicao]
    
    if tipo:
        sql_update += ", tipo = ?"
        params.append(tipo)

    sql_update += " WHERE id = ?"
    params.append(id_ativo)

    try:
        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute(sql_update, tuple(params))
        conexao.commit()
        
        if cursor.rowcount == 0:
            conexao.close()
            return jsonify({"erro": "Ativo não encontrado"}), 404
        
        conexao.close()
        return jsonify({"mensagem": "Ativo atualizado com sucesso!"})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/api/ativos/<int:id_ativo>', methods=['DELETE'])
def delete_ativo(id_ativo):
    """ (D)elete: Remove um ativo E REGISTRA O ALERTA. """
    try:
        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("SELECT nome, ip_address, tipo FROM ativos_online WHERE id = ?", (id_ativo,))
        ativo = cursor.fetchone()
        
        if not ativo:
            conexao.close()
            return jsonify({"erro": "Ativo não encontrado"}), 404

        nome_ativo = ativo['nome']
        ip_ativo = ativo['ip_address']
        tipo_ativo = ativo['tipo'] 
        
        cursor.execute("DELETE FROM ativos_online WHERE id = ?", (id_ativo,))
        conexao.commit()
        conexao.close()
        
        registrar_alerta("Remoção", f"Ativo saiu da rede: {nome_ativo} ({tipo_ativo}) (IP: {ip_ativo}, ID: {id_ativo})")
        
        return jsonify({"mensagem": "Ativo deletado e alerta registrado!"})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# --- ROTAS DE LEITURA (Alertas e Estatísticas) ---

@app.route('/api/alertas', methods=['GET'])
def get_alertas():
    """ (R)ead: Lista todos os alertas (os mais novos primeiro). """
    conexao = conectar()
    alertas_db = conexao.execute("SELECT * FROM alertas ORDER BY id DESC").fetchall()
    conexao.close()
    return jsonify([dict(alerta) for alerta in alertas_db])


@app.route('/api/ativos-online', methods=['GET'])
def get_ativos_online():
    """ Retorna apenas os ativos com status 'Online'. """
    conexao = conectar()
    ativos_db = conexao.execute("SELECT * FROM ativos_online WHERE status = 'Online'").fetchall()
    conexao.close()
    return jsonify([dict(ativo) for ativo in ativos_db])


@app.route('/api/estatisticas', methods=['GET'])
def obter_estatisticas():
    """ Retorna estatísticas rápidas para o dashboard. """
    try:
        conexao = conectar()
        total_ativos = conexao.execute("SELECT COUNT(*) as c FROM ativos_online").fetchone()[0]
        ativos_online = conexao.execute("SELECT COUNT(*) as c FROM ativos_online WHERE status = 'Online'").fetchone()[0]
        ativos_offline = conexao.execute("SELECT COUNT(*) as c FROM ativos_online WHERE status = 'Offline'").fetchone()[0]
        total_usuarios = conexao.execute("SELECT COUNT(*) as c FROM usuarios").fetchone()[0]
        conexao.close()

        return jsonify({
            'total_ativos': total_ativos or 0,
            'ativos_online': ativos_online or 0,
            'ativos_offline': ativos_offline or 0,
            'total_usuarios': total_usuarios or 0
        })
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
        
# --- ROTA PARA GRÁFICO DE TIPOS DE ATIVOS ---
@app.route('/api/estatisticas/tipos', methods=['GET'])
def obter_tipos_ativos():
    """Retorna a contagem de ativos, agrupados pelo campo 'tipo'."""
    try:
        conexao = conectar()
        # Usa COALESCE para tratar tipos NULL como 'Não Classificado'
        query = "SELECT COALESCE(tipo, 'Não Classificado') as tipo, COUNT(*) as contagem FROM ativos_online GROUP BY tipo ORDER BY contagem DESC"
        tipos_ativos_db = conexao.execute(query).fetchall()
        conexao.close()
        
        resultado = [
            {'tipo': item['tipo'], 'contagem': item['contagem']} 
            for item in tipos_ativos_db
        ]
        
        return jsonify(resultado)
    except Exception as e:
        print(f"Erro ao obter tipos de ativos: {e}")
        return jsonify({'erro': str(e)}), 500


# --- Ponto de Partida: Roda o Servidor ---
if __name__ == '__main__':
    # 1. Garante que todas as tabelas existam
    criar_tabelas_iniciais() 
    
    # 2. Inicia o servidor da API
    print("=========================================================")
    print(" Servidor da API Mestre (Usuários, Ativos, Alertas)")
    print(" Rodando em: http://127.0.0.1:5000")
    print(" Use (Ctrl+C) para parar o servidor.")
    print("=========================================================")
    app.run(host='127.0.0.1', port=5000, debug=True)