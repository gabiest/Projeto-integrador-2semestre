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
TARGET_NETWORK = '192.168.56.0/24'  # Rede alvo para o scan
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
            return nm_detail_data['osmatch'][0]['name']
    except Exception:
        pass
    return "OS Bloqueado" # Nome profissional para falha de OS

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
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] OTIMIZAÇÃO (1/3): Buscando hosts ativos (Ping Scan) em {TARGET_NETWORK}...")
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
    # ETAPA 3: PROCESSAR E SALVAR NO BANCO (LÓGICA CORRIGIDA)
    # -----------------------------------------------------------------
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] OTIMIZAÇÃO (3/3): Processando e salvando TODOS os {len(live_hosts_ips)} hosts no banco...")
    
    conexao = conectar()
    cursor = conexao.cursor()
    data_hora_atual = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')

    # *** A LÓGICA CORRIGIDA: Iteramos pela lista da ETAPA 1 (os 21 hosts) ***
    for ip_address in live_hosts_ips: 
        
        # Pega os dados básicos da Etapa 1 (nm_fast)
        mac_address = nm_fast[ip_address]['addresses'].get('mac', 'N/A') 
        
        # Tenta pegar os dados detalhados da Etapa 2 (nm_detail)
        # Se o host foi bloqueado (AP Isolation), nm_host_data será None
        nm_host_data = nm_detail[ip_address] if ip_address in nm_detail.all_hosts() else None

        # --- CORREÇÃO PARA O MAC LOCAL ---
        if mac_address == 'N/A':
            mac_local = get_mac_address(ip=ip_address)
            if mac_local:
                mac_address = mac_local.upper()
        
        # 1. Resolve o nome (usa dados da Etapa 2 se disponíveis)
        nome_base = get_best_name(ip_address, nm_host_data)
        
        # 2. Resolve o OS (usa dados da Etapa 2 se disponíveis)
        sistema_op = get_os_guess(nm_host_data)
        
        # 3. COMBINA OS DOIS NA COLUNA NOME
        nome_ativo_final = f"{nome_base} ({sistema_op})"
        
        # ... (Restante do código para inserir ou atualizar no banco) ...
        cursor.execute(
            "SELECT id FROM ativos_online WHERE ip_address = ? OR (mac_address = ? AND mac_address != 'N/A')",
            (ip_address, mac_address)
        )
        ativo_existente = cursor.fetchone()

        if not ativo_existente:
            cursor.execute(
                """INSERT INTO ativos_online (nome, ip_address, mac_address, status, condicao, data_inicio) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (nome_ativo_final, ip_address, mac_address, 'Online', '', data_hora_atual)
            )
        else:
            cursor.execute(
                "UPDATE ativos_online SET status = 'Online', nome = ?, data_inicio = ? WHERE id = ?",
                (nome_ativo_final, data_hora_atual, ativo_existente['id'])
            )
            
    conexao.commit()
    conexao.close()
    print(f"\nDiscovery Otimizado finalizado. {len(live_hosts_ips)} hosts processados e salvos.")

if __name__ == "__main__":
    discover_and_add_assets()