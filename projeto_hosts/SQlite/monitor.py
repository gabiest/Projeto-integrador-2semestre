import sqlite3
import datetime
import time
from ping3 import ping # Importa a função 'ping' da biblioteca ping3

# --- Configurações ---
DB_FILE = 'meu_banco.db'
TEMPO_DE_ESPERA = 30 # Segundos (Verifica a cada 30 segundos)
# ---------------------

def conectar():
    """Conecta ao banco e retorna uma conexão em formato de dicionário."""
    conexao = sqlite3.connect(DB_FILE)
    conexao.row_factory = sqlite3.Row 
    return conexao

def registrar_alerta(tipo, mensagem):
    """Função central para salvar qualquer notificação no banco."""
    try:
        data_agora = datetime.datetime.now().isoformat()
        conexao = conectar()
        conexao.execute(
            "INSERT INTO alertas (data_hora, tipo_alerta, mensagem) VALUES (?, ?, ?)",
            (data_agora, tipo, mensagem)
        )
        conexao.commit()
    except Exception as e:
        print(f"Erro ao registrar alerta: {e}")
    finally:
        if conexao:
            conexao.close()

def ping_host(ip):
    """
    Verifica se um IP está respondendo (Online).
    Retorna True se Online (recebeu resposta), False se Offline (timeout).
    """
    try:
        # ping() retorna o tempo de resposta (em segundos) ou None/False se falhar.
        resposta = ping(ip, timeout=1) 
        return resposta is not None and resposta is not False
    except Exception as e:
        print(f"Erro ao pingar {ip}: {e}")
        return False # Assume offline se der erro

def verificar_ativos():
    """A função principal do monitor."""
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Verificando status dos ativos...")
    
    try:
        conexao = conectar()
        cursor = conexao.cursor()
        
        cursor.execute("SELECT id, nome, ip_address, status FROM ativos_online")
        todos_os_ativos = cursor.fetchall()

        if not todos_os_ativos:
            print("Nenhum ativo cadastrado para monitorar.")
            return

        for ativo in todos_os_ativos:
            id_ativo = ativo['id']
            nome_ativo = ativo['nome']
            ip_ativo = ativo['ip_address']
            status_antigo = ativo['status']
            
            if not ip_ativo:
                print(f"Ativo '{nome_ativo}' (ID: {id_ativo}) pulado. (Sem IP)")
                continue # Pula ativos sem IP

            # 1. PINGA O ATIVO
            esta_online = ping_host(ip_ativo)
            
            # 2. DEFINE O NOVO STATUS
            status_novo = "Online" if esta_online else "Offline"

            # 3. COMPARA COM O STATUS ANTIGO
            if status_novo != status_antigo:
                # O STATUS MUDOU!
                print(f"!!! ALERTA !!! Ativo '{nome_ativo}' mudou de '{status_antigo}' para '{status_novo}'.")
                
                # Atualiza o status no banco
                cursor.execute("UPDATE ativos_online SET status = ? WHERE id = ?", (status_novo, id_ativo))
                conexao.commit()
                
                # Registra o alerta
                if status_novo == "Offline":
                    registrar_alerta("Status: Offline", f"O ativo '{nome_ativo}' (IP: {ip_ativo}) ficou OFFLINE.")
                else:
                    registrar_alerta("Status: Online", f"O ativo '{nome_ativo}' (IP: {ip_ativo}) voltou a ficar ONLINE.")
            else:
                # Se não mudou, apenas informa no console
                print(f"Ativo '{nome_ativo}' permanece {status_novo}.")
            
    except Exception as e:
        print(f"Erro no loop de verificação: {e}")
    finally:
        if 'conexao' in locals() and conexao:
            conexao.close()

# --- Loop Principal do Monitor ---
if __name__ == "__main__":
    print("=========================================================")
    print(" Iniciando o Monitor de Ativos (Script de Alerta)")
    print(" Use (Ctrl+C) para parar o monitor.")
    print("=========================================================")
    while True:
        verificar_ativos()
        print(f"Monitoramento concluído. Próxima verificação em {TEMPO_DE_ESPERA} segundos.\n")
        time.sleep(TEMPO_DE_ESPERA)