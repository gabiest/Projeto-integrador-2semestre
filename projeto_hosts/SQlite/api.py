# --- Importações Essenciais ---
import sqlite3
import datetime
import os
import subprocess
import time
import threading
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# --- Importações Específicas para o Scan ---
import nmap
from getmac import get_mac_address

# --- CONFIGURAÇÃO DA REDE ALVO ---
TARGET_NETWORK = '192.168.15.0/24'

# --- Caminhos Importantes ---
PASTA_RAIZ_PROJETO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PASTA_SQLITE = os.path.dirname(__file__)
DB_FILE = os.path.join(PASTA_SQLITE, 'meu_banco.db') 

# --- Configuração do Aplicativo Flask ---
app = Flask(__name__, static_folder=PASTA_RAIZ_PROJETO)
CORS(app, resources={r"/api/*": {"origins": "*"}})


# =======================================================
#   ROTAS DO SERVIDOR WEB (FRONT-END)
# =======================================================

@app.route('/') 
def serve_index():
    try:
        return send_from_directory(os.path.join(PASTA_RAIZ_PROJETO, 'login'), 'login.html')
    except FileNotFoundError:
        return "Erro: Arquivo 'login/login.html' não encontrado.", 404

@app.route('/<path:filename>')
def serve_static_files(filename):
    full_path = os.path.join(PASTA_RAIZ_PROJETO, filename)
    if os.path.isfile(full_path):
        return send_from_directory(PASTA_RAIZ_PROJETO, filename)
    
    # Procura em subpastas comuns para evitar erros 404 em assets
    for folder in ['templates', 'login', 'css', 'js', 'imagens']:
        path = os.path.join(PASTA_RAIZ_PROJETO, folder, filename)
        if os.path.isfile(path):
            return send_from_directory(os.path.join(PASTA_RAIZ_PROJETO, folder), filename)

    return "Arquivo não encontrado.", 404


# =======================================================
#   FUNÇÕES DE BANCO DE DADOS
# =======================================================

def conectar():
    conexao = sqlite3.connect(DB_FILE)
    conexao.row_factory = sqlite3.Row 
    return conexao

def registrar_alerta(tipo, mensagem):
    try:
        data_agora = datetime.datetime.now().isoformat()
        conexao = conectar()
        conexao.execute("INSERT INTO alertas (data_hora, tipo_alerta, mensagem) VALUES (?, ?, ?)", (data_agora, tipo, mensagem))
        conexao.commit()
        conexao.close()
    except: pass

def criar_tabelas_iniciais():
    try:
        conexao = conectar()
        conexao.execute('''CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, email TEXT, senha TEXT)''')
        conexao.execute('''CREATE TABLE IF NOT EXISTS ativos_online (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, ip_address TEXT, mac_address TEXT, status TEXT, condicao TEXT, data_inicio TEXT, tipo TEXT)''')
        conexao.execute('''CREATE TABLE IF NOT EXISTS alertas (id INTEGER PRIMARY KEY AUTOINCREMENT, data_hora TEXT, tipo_alerta TEXT, mensagem TEXT)''')
        try:
            conexao.execute("ALTER TABLE ativos_online ADD COLUMN tipo TEXT")
        except sqlite3.OperationalError: pass 
        conexao.commit()
        print("Tabelas verificadas.")
    except Exception as e:
        print(f"Erro tabelas: {e}")


# =======================================================
#   MÓDULO DE SCAN DE REDE
# =======================================================

def netbios_lookup(ip_address):
    try:
        if os.name == 'nt':
            cmd = ['nbtstat', '-A', ip_address]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=1)
            for line in res.stdout.splitlines():
                if '<20>' in line and 'UNIQUE' in line: return line.split()[0].strip()
    except: pass 
    return None

def classificar_tipo_inteligente(nome, vendor):
    texto = (str(nome) + " " + str(vendor)).lower()
    if any(x in texto for x in ['iphone', 'android', 'galaxy', 'samsung', 'xiaomi', 'motorola']): return "Smartphone"
    if any(x in texto for x in ['notebook', 'laptop', 'thinkpad', 'latitude', 'inspiron']): return "Notebook"
    if any(x in texto for x in ['desktop', 'pc', 'computador', 'windows', 'linux', 'optiplex']): return "Computador"
    if any(x in texto for x in ['epson', 'hp', 'canon', 'brother']): return "Impressora"
    if any(x in texto for x in ['router', 'switch', 'cisco', 'tp-link', 'ubiquiti']): return "Rede"
    return "Outros Dispositivos"

# --- SCAN COMPLETO (Botão Atualizar Inventário) ---
def executar_scan_completo():
    print(f"\n📡 [MANUAL] SCAN NA REDE: {TARGET_NETWORK}")
    nm = nmap.PortScanner()
    try:
        nm.scan(hosts=TARGET_NETWORK, arguments='-sn -PR -T5 --min-hostgroup 100')
    except Exception as e:
        print(f"Erro Nmap: {e}")
        return False

    live_hosts = nm.all_hosts()
    if not live_hosts: return True 

    print(f"✅ {len(live_hosts)} dispositivos encontrados.")
    
    conexao = conectar()
    data_hoje = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    ids_encontrados_ip = []

    for ip in live_hosts:
        ids_encontrados_ip.append(ip)
        
        mac = 'N/A'
        if 'mac' in nm[ip]['addresses']: mac = nm[ip]['addresses']['mac'].upper()
        else:
            try:
                m = get_mac_address(ip=ip)
                if m: mac = m.upper()
            except: pass

        vendor = ""
        try:
            if 'vendor' in nm[ip] and nm[ip]['vendor']:
                vendor = list(nm[ip]['vendor'].values())[0].split(' ')[0]
        except: pass

        nome_final = ""
        if 'hostnames' in nm[ip] and nm[ip]['hostnames']: nome_final = nm[ip]['hostnames'][0]['name']
        if not nome_final: nome_final = netbios_lookup(ip)
        if not nome_final:
            nome_base = f"Dispositivo-{ip.split('.')[-1]}"
            nome_final = f"{nome_base} ({vendor})" if vendor else nome_base

        tipo_final = classificar_tipo_inteligente(nome_final, vendor)

        cursor = conexao.execute("SELECT id FROM ativos_online WHERE ip_address = ? OR (mac_address = ? AND mac_address != 'N/A')", (ip, mac))
        existe = cursor.fetchone()

        if existe:
            conexao.execute("UPDATE ativos_online SET status='Online', nome=?, tipo=?, data_inicio=? WHERE id=?", (nome_final, tipo_final, data_hoje, existe['id']))
        else:
            conexao.execute("INSERT INTO ativos_online (nome, ip_address, mac_address, status, condicao, tipo, data_inicio) VALUES (?, ?, ?, 'Online', 'Monitorado', ?, ?)", (nome_final, ip, mac, tipo_final, data_hoje))

    if ids_encontrados_ip:
        placeholders = ','.join('?' for _ in ids_encontrados_ip)
        conexao.execute(f"UPDATE ativos_online SET status='Offline' WHERE ip_address NOT IN ({placeholders}) AND status='Online'", ids_encontrados_ip)
    
    conexao.commit()
    conexao.close()
    return True

# --- SCAN STATUS (Automático) ---
def executar_scan_status_apenas():
    nm = nmap.PortScanner()
    try:
        nm.scan(hosts=TARGET_NETWORK, arguments='-sn -PR -T5')
    except: return False

    ips_online = nm.all_hosts()
    conexao = conectar()
    
    if ips_online:
        placeholders = ','.join('?' for _ in ips_online)
        conexao.execute(f"UPDATE ativos_online SET status='Online' WHERE ip_address IN ({placeholders})", ips_online)
        conexao.execute(f"UPDATE ativos_online SET status='Offline' WHERE ip_address NOT IN ({placeholders})", ips_online)
    
    conexao.commit()
    conexao.close()
    return True

def monitor_background():
    while True:
        try:
            time.sleep(30)
            executar_scan_status_apenas()
        except: pass

monitor = threading.Thread(target=monitor_background, daemon=True)
monitor.start()


# =======================================================
#   ROTAS DA API (ENDPOINTS) - AQUI ESTAVAM FALTANDO
# =======================================================

# 1. ROTA DE ATIVOS ONLINE (Correção do seu Erro 404)
@app.route('/api/ativos-online', methods=['GET'])
def get_ativos_online():
    con = conectar()
    # Retorna apenas quem está online para a página de monitoramento
    res = con.execute("SELECT * FROM ativos_online WHERE status='Online'").fetchall()
    con.close()
    return jsonify([dict(x) for x in res])

# 2. ROTA DE TIPOS PARA O GRÁFICO (Correção do outro Erro 404)
@app.route('/api/estatisticas/tipos', methods=['GET'])
def stats_types():
    con = conectar()
    res = con.execute("SELECT COALESCE(tipo, 'Outros') as tipo, COUNT(*) as contagem FROM ativos_online GROUP BY tipo").fetchall()
    con.close()
    return jsonify([{'tipo': r['tipo'], 'contagem': r['contagem']} for r in res])

# 3. ROTA DE SCAN STATUS (Para o botão da página Online)
@app.route('/api/scan-status', methods=['POST'])
def rota_scan_status():
    if executar_scan_status_apenas(): return jsonify({"msg": "OK"}), 200
    return jsonify({"erro": "Falha"}), 500

# 4. ROTA DE SCAN COMPLETO (Para o Inventário)
@app.route('/api/scan-rede', methods=['POST'])
def rota_scan_rede():
    if executar_scan_completo(): return jsonify({"msg": "OK"}), 200
    return jsonify({"erro": "Falha"}), 500

# 5. ROTA DE RESET (Para zerar o banco)
@app.route('/api/ativos/reset', methods=['DELETE'])
def resetar_inventario():
    try:
        con = conectar()
        con.execute("DELETE FROM ativos_online")
        con.execute("DELETE FROM sqlite_sequence WHERE name='ativos_online'")
        con.commit()
        con.close()
        return jsonify({"msg": "OK"}), 200
    except Exception as e: return jsonify({"erro": str(e)}), 500

# 6. CRUD GERAL (Listar todos, Adicionar, Editar, Excluir)
@app.route('/api/ativos', methods=['GET'])
def get_ativos():
    con = conectar()
    res = con.execute("SELECT * FROM ativos_online").fetchall()
    con.close()
    return jsonify([dict(x) for x in res])

@app.route('/api/ativos', methods=['POST'])
def add_ativo():
    d = request.json
    try:
        con = conectar()
        c = con.cursor()
        c.execute("INSERT INTO ativos_online (nome, ip_address, mac_address, status, condicao, tipo, data_inicio) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                  (d['nome'], d['ip_address'], d['mac_address'], d.get('status','Pendente'), d.get('condicao','Monitorado'), d.get('tipo','Outros'), datetime.datetime.now().isoformat()))
        con.commit()
        nid = c.lastrowid
        con.close()
        return jsonify({"msg": "Criado", "id": nid}), 201
    except Exception as e: return jsonify({"erro": str(e)}), 500

@app.route('/api/ativos/<int:id>', methods=['PUT'])
def update_ativo(id):
    d = request.json
    try:
        con = conectar()
        con.execute("UPDATE ativos_online SET nome=?, ip_address=?, mac_address=?, status=?, condicao=?, tipo=? WHERE id=?", 
                    (d['nome'], d['ip_address'], d['mac_address'], d['status'], d['condicao'], d.get('tipo'), id))
        con.commit()
        con.close()
        return jsonify({"msg": "Atualizado"}), 200
    except Exception as e: return jsonify({"erro": str(e)}), 500

@app.route('/api/ativos/<int:id>', methods=['DELETE'])
def delete_ativo(id):
    try:
        con = conectar()
        con.execute("DELETE FROM ativos_online WHERE id=?", (id,))
        con.commit()
        con.close()
        return jsonify({"msg": "Deletado"}), 200
    except Exception as e: return jsonify({"erro": str(e)}), 500

# 7. LOGIN / USUÁRIOS
@app.route('/api/login', methods=['POST'])
def login():
    d = request.json
    try:
        con = conectar()
        u = con.execute("SELECT * FROM usuarios WHERE email=?",(d.get('email'),)).fetchone()
        con.close()
        if u and u['senha']==d.get('senha'): 
            return jsonify({"msg":"OK", "usuario": {"id":u['id'], "nome":u['nome'], "email":u['email']}}), 200
        return jsonify({"erro":"Falha"}), 401
    except Exception as e: return jsonify({"erro": str(e)}), 500

@app.route('/api/usuarios', methods=['GET'])
def get_usuarios():
    con = conectar()
    res = con.execute("SELECT * FROM usuarios").fetchall()
    con.close()
    return jsonify([dict(x) for x in res])

@app.route('/api/usuarios', methods=['POST'])
def add_usuario():
    d = request.json
    try:
        con = conectar()
        c = con.cursor()
        c.execute("INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)", (d['nome'], d['email'], d['senha']))
        con.commit()
        nid = c.lastrowid
        con.close()
        return jsonify({"id": nid}), 201
    except Exception as e: return jsonify({"erro": str(e)}), 500

@app.route('/api/usuarios/<int:id>', methods=['DELETE'])
def delete_usuario(id):
    try:
        con = conectar()
        con.execute("DELETE FROM usuarios WHERE id=?", (id,))
        con.commit()
        con.close()
        return jsonify({"msg": "Deletado"}), 200
    except Exception as e: return jsonify({"erro": str(e)}), 500

# 8. ESTATÍSTICAS GERAIS
@app.route('/api/estatisticas', methods=['GET'])
def stats():
    con = conectar()
    t = con.execute("SELECT COUNT(*) FROM ativos_online").fetchone()[0]
    on = con.execute("SELECT COUNT(*) FROM ativos_online WHERE status='Online'").fetchone()[0]
    off = con.execute("SELECT COUNT(*) FROM ativos_online WHERE status='Offline'").fetchone()[0]
    con.close()
    return jsonify({'total_ativos':t, 'ativos_online':on, 'ativos_offline':off})

@app.route('/api/alertas', methods=['GET'])
def get_alertas():
    con = conectar()
    res = con.execute("SELECT * FROM alertas ORDER BY id DESC").fetchall()
    con.close()
    return jsonify([dict(x) for x in res])


if __name__ == '__main__':
    criar_tabelas_iniciais()
    print(f"\n--- SERVIDOR ONLINE: http://127.0.0.1:5000 ({TARGET_NETWORK}) ---\n")
    app.run(host='127.0.0.1', port=5000, debug=True)