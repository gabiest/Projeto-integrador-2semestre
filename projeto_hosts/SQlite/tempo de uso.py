import sqlite3
import datetime

conexao = None
cursor = None

try:
    # 1. Conectar ao banco de dados
    conexao = sqlite3.connect('meu_banco.db')
    cursor = conexao.cursor()

    # 2. Garantir que a tabela exista (apenas por segurança)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ativos_online (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL, ip_address TEXT, mac_address TEXT,
        status TEXT, condicao TEXT, data_inicio TEXT
    )
    ''')
    
    # --- ETAPA DE CONSULTA E CÁLCULO ---
    print("\n--- MONITOR DE ATIVOS ONLINE ---")
    
    cursor.execute("SELECT * FROM ativos_online")
    todos_os_ativos = cursor.fetchall()

    if not todos_os_ativos:
        print("Nenhum ativo encontrado.")
    else:
        # 3. Pegar a hora exata de AGORA
        #    (No seu caso, 22/10/2025 às 00:22 da manhã)
        tempo_agora = datetime.datetime.now()
        
        print(f"Relatório gerado em: {tempo_agora.isoformat()}\n")
        
        # 4. Loop para calcular e mostrar o tempo de cada ativo
        for ativo in todos_os_ativos:
            id_ativo = ativo[0]
            nome_ativo = ativo[1]
            
            # Pega a string da data (coluna 6) do banco
            data_inicio_str = ativo[6] 
            
            if data_inicio_str is None:
                print(f"ID: {id_ativo}, Nome: {nome_ativo}, Tempo de Uso: (Data não registrada)")
                continue

            try:
                # 5. Converte a string (ex: "2025-10-22T00:10:59...")
                data_inicio_obj = datetime.datetime.fromisoformat(data_inicio_str)
                
                # 6. CALCULA A DIFERENÇA
                #    (ex: 00:22:00 - 00:10:59)
                duracao = tempo_agora - data_inicio_obj
                
                # Formata para (ex: "0:11:01")
                duracao_formatada = str(duracao).split('.')[0]
                
                # 7. Imprime o resultado calculado no TERMINAL
                print(f"ID: {id_ativo}, Nome: {nome_ativo}, Tempo de Uso: {duracao_formatada}")
            
            except (TypeError, ValueError):
                print(f"ID: {id_ativo}, Nome: {nome_ativo}, Tempo de Uso: (Erro ao calcular data)")

except sqlite3.Error as e:
    print(f"Ocorreu um erro ao interagir com o banco de dados: {e}")

finally:
    # 8. Fechar a conexão
    if cursor:
        cursor.close()
    if conexao:
        conexao.close()
        print("\nConexão com o banco de dados fechada.")
        