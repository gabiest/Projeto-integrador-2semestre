import sqlite3
import datetime

conexao = None
cursor = None

try:
    # 1. Conectar ao banco
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

    # --- ETAPA DE PESQUISA ---
    print("\n--- PESQUISAR ATIVOS ONLINE ---")
    
    # 3. Pedir o termo de pesquisa ao usuário
    termo_pesquisa = input("Digite o nome (ou parte do nome) do ativo que deseja buscar: ")

    # 4. Preparar o termo para a consulta LIKE
    #    O '%' é o coringa. %termo% busca qualquer coisa que contenha o termo.
    termo_formatado_like = f"%{termo_pesquisa}%"

    print(f"\nBuscando por ativos com nome parecido com '{termo_pesquisa}'...")

    # 5. Executar a consulta SQL com WHERE e LIKE
    cursor.execute(
        "SELECT * FROM ativos_online WHERE nome LIKE ?", 
        (termo_formatado_like,)
    )
    
    resultados = cursor.fetchall()

    # 6. Exibir os resultados
    if not resultados:
        print("Nenhum ativo encontrado com esse nome.")
    else:
        print(f"Encontrados {len(resultados)} ativo(s):")
        
        tempo_agora = datetime.datetime.now()
        
        for ativo in resultados:
            # --- Reutilizar a lógica de cálculo de tempo ---
            id_ativo = ativo[0]
            nome_ativo = ativo[1]
            ip_ativo = ativo[2]
            status_ativo = ativo[4] # Coluna 'status'
            condicao_ativo = ativo[5] # Coluna 'condicao'
            data_inicio_str = ativo[6] # Coluna 'data_inicio'
            
            if data_inicio_str is None:
                duracao_formatada = "(Data não registrada)"
            else:
                try:
                    data_inicio_obj = datetime.datetime.fromisoformat(data_inicio_str)
                    duracao = tempo_agora - data_inicio_obj
                    duracao_formatada = str(duracao).split('.')[0]
                except (TypeError, ValueError):
                    duracao_formatada = "(Erro na data)"
            
            # Imprimir o resultado completo
            print("---------------------------------")
            print(f"  ID: {id_ativo}")
            print(f"  Nome: {nome_ativo}")
            print(f"  IP: {ip_ativo}")
            print(f"  Status: {status_ativo}")
            print(f"  Condição: {condicao_ativo}")
            print(f"  Tempo de Uso: {duracao_formatada}")

except sqlite3.Error as e:
    print(f"Ocorreu um erro ao interagir com o banco de dados: {e}")
finally:
    # 7. Fechar a conexão
    if cursor:
        cursor.close()
    if conexao:
        conexao.close()
        print("\nConexão com o banco de dados fechada.")