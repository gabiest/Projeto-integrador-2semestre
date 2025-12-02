import sqlite3
import datetime

conexao = None
cursor = None

def mostrar_e_calcular_ativos(cursor):
    """
    Função reutilizável para buscar todos os ativos
    e CALCULAR o tempo de uso de cada um.
    """
    print("\n--- MONITOR DE ATIVOS (COM TEMPO DE USO CALCULADO) ---")
    
    cursor.execute("SELECT * FROM ativos_online")
    todos_os_ativos = cursor.fetchall()

    if not todos_os_ativos:
        print("Nenhum ativo encontrado.")
    else:
        # Pega a hora exata de AGORA
        tempo_agora = datetime.datetime.now()
        
        for ativo in todos_os_ativos:
            id_ativo = ativo[0]
            nome_ativo = ativo[1]
            ip_ativo = ativo[2]
            
            # Pega a string da data (coluna 6) do banco
            data_inicio_str = ativo[6] 
            
            if data_inicio_str is None:
                print(f"ID: {id_ativo}, Nome: {nome_ativo}, IP: {ip_ativo}, Tempo de Uso: (Data não registrada)")
                continue

            try:
                # Converte a string de volta para um objeto 'datetime'
                data_inicio_obj = datetime.datetime.fromisoformat(data_inicio_str)
                
                # Calcula a diferença (o "cronômetro"!)
                duracao = tempo_agora - data_inicio_obj
                
                # Tira os microsegundos para ficar mais limpo (ex: 0:05:10)
                duracao_formatada = str(duracao).split('.')[0]
                
                # Imprime o resultado calculado
                print(f"ID: {id_ativo}, Nome: {nome_ativo}, IP: {ip_ativo}, Tempo de Uso: {duracao_formatada}")
            
            except (TypeError, ValueError):
                print(f"ID: {id_ativo}, Nome: {nome_ativo}, IP: {ip_ativo}, Tempo de Uso: (Erro ao calcular data)")

try:
    conexao = sqlite3.connect('meu_banco.db')
    cursor = conexao.cursor()

    # --- ETAPA DE CRIAÇÃO (CREATE) ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ativos_online (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        ip_address TEXT,
        mac_address TEXT,
        status TEXT,
        condicao TEXT,
        data_inicio TEXT
    )
    ''')

    # --- CONSULTA (Antes de Adicionar) ---
    # Agora a lista "ANTES" também calcula o tempo de uso
    mostrar_e_calcular_ativos(cursor)


    # --- ETAPA DE ADICIONAR NOVO ATIVO (INSERT) ---
    print("\n--- ADICIONAR NOVO ATIVO ---")
    nome_digitado = input("Digite o nome do ativo: ")
    ip_digitado = input("Digite o IP do ativo: ")
    mac_digitado = input("Digite o MAC Address: ")
    status_digitado = input("Digite o status (ex: Online, Offline): ")
    condicao_digitada = input("Digite a condição (ex: Bom, Manutenção): ")
    
    # Capturamos a hora atual para salvar no banco
    data_agora = datetime.datetime.now().isoformat()
    
    print(f"\nAdicionando '{nome_digitado}' ao banco de dados às {data_agora}...")
    
    cursor.execute(
        "INSERT INTO ativos_online (nome, ip_address, mac_address, status, condicao, data_inicio) VALUES (?, ?, ?, ?, ?, ?)",
        (nome_digitado, ip_digitado, mac_digitado, status_digitado, condicao_digitada, data_agora) 
    )
    
    conexao.commit()
    print("Ativo adicionado com sucesso.")


    # --- CONSULTA (Depois de Adicionar) ---
    # A lista "DEPOIS" também calcula o tempo de uso (agora com o novo item)
    mostrar_e_calcular_ativos(cursor)

except sqlite3.Error as e:
    print(f"Ocorreu um erro ao interagir com o banco de dados: {e}")
    if conexao:
        conexao.rollback()

finally:
    if cursor:
        cursor.close()
    if conexao:
        conexao.close()
        print("\nConexão com o banco de dados fechada.")