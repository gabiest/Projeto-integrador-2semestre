import sqlite3
# Não precisamos do 'datetime' aqui, pois a tabela 'usuarios' não tem o tempo.

conexao = None
cursor = None

def mostrar_todos_os_usuarios(cursor):
    """Função auxiliar para mostrar os usuários cadastrados."""
    print("\n--- USUÁRIOS ATUALMENTE CADASTRADOS ---")
    
    cursor.execute("SELECT * FROM usuarios")
    todos_os_usuarios = cursor.fetchall()

    if not todos_os_usuarios:
        print("Nenhum usuário encontrado.")
        return False # Retorna False se a lista estiver vazia
    
    for usuario in todos_os_usuarios:
        id_usuario = usuario[0]
        nome_usuario = usuario[1]
        email_usuario = usuario[2]
        
        # Apenas imprimimos os dados, sem cálculo de tempo
        print(f"ID: {id_usuario}, Nome: {nome_usuario}, Email: {email_usuario}")
        
    return True # Retorna True se houver usuários

try:
    # 1. Conectar ao banco de dados
    conexao = sqlite3.connect('meu_banco.db')
    cursor = conexao.cursor()

    # Garante que a tabela 'usuarios' exista (não custa verificar)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT
    )
    ''')
    
    # NOTA: Removi os INSERTs de 'Ana Silva' e 'Bruno Costa'
    # para este script focar APENAS em excluir.

    # 2. Mostrar a lista de usuários ANTES de deletar
    #    (Se não houver usuários, a função nos avisa)
    if not mostrar_todos_os_usuarios(cursor):
        print("Não há usuários para excluir.")
    
    else:
        # --- ETAPA DE EXCLUSÃO (DELETE) ---
        print("\n--- EXCLUIR UM USUÁRIO ---")
        
        try:
            # Pergunta qual ID deletar (interativo)
            id_para_deletar = int(input("Digite o ID do usuário que deseja EXCLUIR: "))
            
            # Confirmação de segurança
            confirmacao = input(f"Tem certeza que deseja excluir o usuário com ID {id_para_deletar}? (s/n): ").lower()
            
            if confirmacao == 's' or confirmacao == 'sim':
                # 3. Executar o comando DELETE
                cursor.execute(
                    "DELETE FROM usuarios WHERE id = ?",
                    (id_para_deletar,)  # Passamos o ID como uma tupla
                )
                
                # 4. Verificar se algo foi realmente deletado
                if cursor.rowcount == 0:
                    print(f"\nERRO: Nenhum usuário encontrado com o ID {id_para_deletar}.")
                else:
                    # 5. Salvar (comitar) a exclusão
                    conexao.commit()
                    print(f"\nUsuário com ID {id_para_deletar} foi excluído com sucesso.")
            else:
                print("\nOperação de exclusão cancelada.")

        except ValueError:
            print("\nERRO: O ID deve ser um número.")

        # 6. Mostrar a lista de usuários DEPOIS de tentar deletar
        print("\n--- LISTA ATUALIZADA DE USUÁRIOS ---")
        mostrar_todos_os_usuarios(cursor)

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