import sqlite3
import datetime # Vamos usar só para exibir o tempo de uso na consulta

conexao = None
cursor = None

def mostrar_todos_os_ativos(cursor):
    """Função auxiliar para mostrar os ativos e seu tempo de uso."""
    print("\n--- ATIVOS ATUALMENTE CADASTRADOS ---")
    
    cursor.execute("SELECT * FROM ativos_online")
    todos_os_ativos = cursor.fetchall()

    if not todos_os_ativos:
        print("Nenhum ativo encontrado.")
        return False # Retorna False se a lista estiver vazia
    
    tempo_agora = datetime.datetime.now()
    
    for ativo in todos_os_ativos:
        id_ativo = ativo[0]
        nome_ativo = ativo[1]
        data_inicio_str = ativo[6] # Coluna da data de início
        
        try:
            # Calcula o tempo de uso para exibição
            data_inicio_obj = datetime.datetime.fromisoformat(data_inicio_str)
            duracao = tempo_agora - data_inicio_obj
            duracao_formatada = str(duracao).split('.')[0]
        except (TypeError, ValueError):
            duracao_formatada = "Erro na data"
            
        print(f"ID: {id_ativo}, Nome: {nome_ativo}, Tempo de Uso: {duracao_formatada}")
        
    return True # Retorna True se houver ativos

try:
    # 1. Conectar ao banco de dados
    conexao = sqlite3.connect('meu_banco.db')
    cursor = conexao.cursor()

    # Garante que a tabela exista (não custa verificar)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ativos_online (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL, ip_address TEXT, mac_address TEXT,
        status TEXT, condicao TEXT, data_inicio TEXT
    )
    ''')

    # 2. Mostrar a lista de ativos ANTES de deletar
    #    (Se não houver ativos, a função nos avisa)
    if not mostrar_todos_os_ativos(cursor):
        print("Não há ativos para excluir.")
    
    else:
        # --- ETAPA DE EXCLUSÃO (DELETE) ---
        print("\n--- EXCLUIR UM ATIVO ---")
        
        try:
            id_para_deletar = int(input("Digite o ID do ativo que deseja EXCLUIR: "))
            
            # Confirmação de segurança
            confirmacao = input(f"Tem certeza que deseja excluir o ativo com ID {id_para_deletar}? (s/n): ").lower()
            
            if confirmacao == 's' or confirmacao == 'sim':
                # 3. Executar o comando DELETE
                cursor.execute(
                    "DELETE FROM ativos_online WHERE id = ?",
                    (id_para_deletar,)  # Passamos o ID como uma tupla (é o jeito seguro)
                )
                
                # 4. Verificar se algo foi realmente deletado
                #    cursor.rowcount diz quantas linhas foram afetadas
                if cursor.rowcount == 0:
                    print(f"\nERRO: Nenhum ativo encontrado com o ID {id_para_deletar}.")
                else:
                    # 5. Salvar (comitar) a exclusão
                    conexao.commit()
                    print(f"\nAtivo com ID {id_para_deletar} foi excluído com sucesso.")
            else:
                print("\nOperação de exclusão cancelada.")

        except ValueError:
            print("\nERRO: O ID deve ser um número.")

        # 6. Mostrar a lista de ativos DEPOIS de tentar deletar
        print("\n--- LISTA ATUALIZADA DE ATIVOS ---")
        mostrar_todos_os_ativos(cursor)

except sqlite3.Error as e:
    print(f"Ocorreu um erro ao interagir com o banco de dados: {e}")
    if conexao:
        conexao.rollback() # Desfaz qualquer mudança pendente se der erro

finally:
    # 7. Fechar a conexão
    if cursor:
        cursor.close()
    if conexao:
        conexao.close()
        print("\nConexão com o banco de dados fechada.")