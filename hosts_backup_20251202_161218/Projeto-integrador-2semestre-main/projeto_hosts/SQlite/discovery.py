import sqlite3
import datetime
import os
import nmap
import ipaddress
import time 
import subprocess 
from getmac import get_mac_address

# --- Configurações CRÍTICAS ---
DB_FILE = 'meu_banco.db' 
# ATUALIZADO PARA A REDE DO SENAC:
TARGET_NETWORK = '192.168.15.0/24'
# ------------------------------

def conectar():
    """Conecta ao banco de dados."""
    try:
        conexao = sqlite3.connect(DB_FILE)
        conexao.row_factory = sqlite3.Row 
        return conexao
    except sqlite3.OperationalError as e:
        print(f"ERRO DE CONEXÃO: {e}")
        raise

def netbios_lookup(ip_address):
    """Tenta obter o Nome NetBIOS (Hostname) usando o 'nbtstat' do Windows."""
    try:
        comando = ['nbtstat', '-A', ip_address]
        resultado = subprocess.run(
            comando, capture_output=True, text=True, timeout=1, check=False)
        
        for line in resultado.stdout.splitlines():
            if '<20>' in line and 'UNIQUE' in line:
                nome_netbios = line.split()[0].strip()
                if nome_netbios:
                    return nome_netbios
    except Exception:
        pass 
    return None

def get_best_name(ip, nm_detail_data):
    """Tenta obter o Nome (NetBIOS ou Nmap) ou usa um genérico."""
    netbios_name = netbios_lookup(ip)
    if netbios_name:
        return netbios_name
    
    # Tenta o nome do Nmap (Plano B)
    try:
        if nm_detail_data and 'hostnames' in nm_detail_data:
            for h in nm_detail_data['hostnames']:
                name = h.get('name')
                if name and name != 'localhost':
                    return name
    except Exception: pass

    return f"Dispositivo-{ip.split('.')[-1]}" 

def get_os_guess(nm_detail_data):
    """Extrai a melhor estimativa de OS do resultado do Nmap."""
    try:
        if nm_detail_data and 'osmatch' in nm_detail_data and nm_detail_data['osmatch']:
            # Pega a primeira e melhor estimativa
            return nm_detail_data['osmatch'][0]['name']
    except Exception:
        pass
    return "OS Bloqueado"

# -----------------------------------------------------------
# >>> NOVA FUNÇÃO PARA CLASSIFICAR O TIPO DE ATIVO PARA O GRÁFICO <<<
# -----------------------------------------------------------
def get_asset_type(os_guess):
    """Mapeia a estimativa de OS para um Tipo de Ativo para o Dashboard."""
    os_guess = os_guess.lower()
    
    if 'windows' in os_guess or 'linux' in os_guess or 'unix' in os_guess:
        return 'Computador'
    if 'router' in os_guess or 'openwrt' in os_guess or 'cisco' in os_guess:
        return 'Roteador/Firewall'
    if 'printer' in os_guess or 'hp' in os_guess or 'canon' in os_guess or 'epson' in os_guess:
        return 'Impressora'
    if 'server' in os_guess or 'esxi' in os_guess or 'hyper-v' in os_guess:
        return 'Servidor'
    if 'switch' in os_guess or 'network' in os_guess:
        return 'Switch'
    
    return 'Outros' # Tipo padrão se não houver correspondência

# --- FUNÇÃO PRINCIPAL ATUALIZADA ---

def discover_and_add_assets():
    """
    Executa um scan OTIMIZADO em 2 Etapas:
    1. Ping Scan Rápido (para achar IPs vivos)
    2. OS Scan Lento (APENAS nos IPs vivos)
    3. Salva TODOS os IPs da Etapa 1, enriquecidos com dados da Etapa 2
    """
    nm_fast = nmap.PortScanner() # Scanner para Etapa 1
    nm_detail = nmap.PortScanner() # Scanner para Etapa 2
    
    # -----------------------------------------------------------------
    # ETAPA 1: ACHAR HOSTS VIVOS (RÁPIDO)
    # -----------------------------------------------------------------
    start_time = datetime.datetime.now()
    print(f"[{start_time.strftime('%Y-%m-%d %H:%M:%S')}] OTIMIZAÇÃO (1/3): Buscando hosts ativos (Ping Scan) em {TARGET_NETWORK}...")
    try:
        nm_fast.scan(hosts=TARGET_NETWORK, arguments='-sn -T4')
        print("Scan Rápido concluído.")
    except nmap.PortScannerError as e:
        print(f"ERRO CRÍTICO DO NMAP (Etapa 1): {e}")
        return

    live_hosts_ips = nm_fast.all_hosts()
    if not live_hosts_ips:
        print("Nenhum host ativo encontrado na rede.")
        return
        
    print(f"Encontrados {len(live_hosts_ips)} hosts ativos. IPs: {live_hosts_ips}")
    live_hosts_str = ' '.join(live_hosts_ips) 

    # -----------------------------------------------------------------
    # ETAPA 2: BUSCAR DETALHES (OS/NOME) APENAS DOS HOSTS VIVOS
    # -----------------------------------------------------------------
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] OTIMIZAÇÃO (2/3): Buscando OS/Detalhes dos hosts ativos (pode demorar)...")
    try:
        nm_detail.scan(hosts=live_hosts_str, arguments='-sV -O -T4')
        print("Scan Detalhado concluído.")
    except nmap.PortScannerError as e:
        print(f"ERRO CRÍTICO DO NMAP (Etapa 2): {e}")
        # Mesmo se a Etapa 2 falhar, continuamos para salvar os dados da Etapa 1
        pass 

    # -----------------------------------------------------------------
    # ETAPA 3: PROCESSAR E SALVAR NO BANCO (LÓGICA ATUALIZADA)
    # -----------------------------------------------------------------
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] OTIMIZAÇÃO (3/3): Processando e salvando TODOS os {len(live_hosts_ips)} hosts no banco...")
    
    conexao = conectar()
    cursor = conexao.cursor()
    data_hora_atual = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')

    hosts_escaneados_neste_ciclo = [] # Para rastrear quem foi encontrado

    for ip_address in live_hosts_ips: 
        hosts_escaneados_neste_ciclo.append(ip_address) # Marca como encontrado

        # Pega os dados básicos da Etapa 1 (nm_fast)
        mac_address = nm_fast[ip_address]['addresses'].get('mac', 'N/A') 
        
        # Tenta pegar os dados detalhados da Etapa 2 (nm_detail)
        nm_host_data = nm_detail[ip_address] if ip_address in nm_detail.all_hosts() else None

        # --- CORREÇÃO PARA O MAC LOCAL ---
        if mac_address == 'N/A':
            mac_local = get_mac_address(ip=ip_address)
            if mac_local:
                mac_address = mac_local.upper()
        
        # 1. Resolve o nome 
        nome_base = get_best_name(ip_address, nm_host_data)
        
        # 2. Resolve o OS 
        sistema_op = get_os_guess(nm_host_data)
        
        # 3. NOVIDADE: Resolve o Tipo para o Gráfico
        tipo_ativo_final = get_asset_type(sistema_op) 
        
        # 4. Combina o nome e OS
        nome_ativo_final = f"{nome_base} ({sistema_op})"
        
        
        cursor.execute(
            "SELECT id FROM ativos_online WHERE ip_address = ? OR (mac_address = ? AND mac_address != 'N/A')",
            (ip_address, mac_address)
        )
        ativo_existente = cursor.fetchone()

        if not ativo_existente:
            print(f" [+] INSERINDO NOVO: {nome_ativo_final} | Tipo: {tipo_ativo_final}")
            
            # >>> SQL ATUALIZADO: INCLUI O CAMPO 'TIPO' <<<
            cursor.execute(
                """INSERT INTO ativos_online (nome, ip_address, mac_address, status, condicao, data_inicio, tipo) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (nome_ativo_final, ip_address, mac_address, 'Online', 'Monitorado', data_hora_atual, tipo_ativo_final)
            )
        else:
            print(f" [~] ATUALIZANDO: {nome_ativo_final} | Tipo: {tipo_ativo_final}")
            
            # >>> SQL ATUALIZADO: INCLUI O CAMPO 'TIPO' NO UPDATE <<<
            cursor.execute(
                """UPDATE ativos_online 
                   SET status = 'Online', nome = ?, tipo = ?, data_inicio = ? 
                   WHERE id = ?""",
                (nome_ativo_final, tipo_ativo_final, data_hora_atual, ativo_existente['id'])
            )
    
    # --- LÓGICA DE DETECÇÃO DE OFFLINE ---
    
    if hosts_escaneados_neste_ciclo:
        live_ips_tuple = tuple(hosts_escaneados_neste_ciclo)
        
        # Marcamos como 'Offline' os ativos que estavam online e NÃO foram encontrados no scan
        placeholders = ','.join('?' for _ in live_ips_tuple)
        
        cursor.execute(f"""
            UPDATE ativos_online 
            SET status = 'Offline' 
            WHERE ip_address NOT IN ({placeholders}) AND status = 'Online'
        """, live_ips_tuple)
        
        offline_count = cursor.rowcount
        if offline_count > 0:
            print(f" [!] {offline_count} ativos detectados como OFFLINE (Não apareceram no scan).")
        
            
    conexao.commit()
    conexao.close()
    print(f"\nDiscovery Otimizado finalizado. {len(live_hosts_ips)} hosts encontrados.")

if __name__ == "__main__":
    discover_and_add_assets()