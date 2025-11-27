import sqlite3

# O arquivo do banco de dados é o MESMO
DB_FILE = 'meu_banco.db'

def conectar():
    """Cria e retorna uma conexão com o banco de dados."""
    return sqlite3.connect(DB_FILE)

def criar_tabela():
    """Garante que a tabela 'usuarios' exista."""
    try:
        conexao = conectar()
        cursor = conexao.cursor()
        # Comando SQL para criar a tabela usuarios
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT
        )
        ''')
        conexao.commit()
    except sqlite3.Error as e:
        print(f"Erro ao criar a tabela: {e}")
    finally:
        if conexao:
            conexao.close()

# --- CREATE (Criar) ---
def adicionar_usuario():
    """Pede dados ao usuário e insere um novo usuário no banco."""
    print("\n--- (C) Adicionar Novo Usuário ---")
    nome = input("Nome do usuário: ")
    email = input("Email do usuário: ")

    try:
        conexao = conectar()
        cursor = conexao.cursor()
        # SQL adaptado para 'usuarios'
        cursor.execute(
            "INSERT INTO usuarios (nome, email) VALUES (?, ?)",
            (nome, email)
        )
        conexao.commit()
        print(f"Usuário '{nome}' adicionado com sucesso!")
    except sqlite3.Error as e:
        print(f"Erro ao adicionar usuário: {e}")
    finally:
        if conexao:
            conexao.close()

# --- READ (Ler) ---
def listar_usuarios():
    """Lista todos os usuários cadastrados na tabela."""
    print("\n--- (R) Lista de Todos os Usuários ---")
    try:
        conexao = conectar()
        cursor = conexao.cursor()
        # SQL adaptado para 'usuarios'
        cursor.execute("SELECT * FROM usuarios")
        usuarios = cursor.fetchall()
        
        if not usuarios:
            print("Nenhum usuário cadastrado.")
            return

        # Cabeçalho formatado para usuários
        print(f"{'ID':<4} | {'Nome':<25} | {'Email':<25}")
        print("-" * 55)
        # Imprime cada usuário
        for usuario in usuarios:
            # Colunas: 0=id, 1=nome, 2=email
            print(f"{usuario[0]:<4} | {usuario[1]:<25} | {usuario[2]:<25}")

    except sqlite3.Error as e:
        print(f"Erro ao listar usuários: {e}")
    finally:
        if conexao:
            conexao.close()

# --- UPDATE (Atualizar) ---
def atualizar_usuario():
    """Pede um ID e atualiza os dados de um usuário."""
    print("\n--- (U) Atualizar Usuário ---")
    listar_usuarios() # Mostra a lista para o usuário saber qual ID
    try:
        id_para_atualizar = int(input("Digite o ID do usuário que deseja atualizar: "))
    except ValueError:
        print("ID inválido.")
        return

    try:
        conexao = conectar()
        cursor = conexao.cursor()
        
        # SQL adaptado para 'usuarios'
        cursor.execute("SELECT * FROM usuarios WHERE id = ?", (id_para_atualizar,))
        usuario = cursor.fetchone()
        
        if not usuario:
            print(f"Erro: Usuário com ID {id_para_atualizar} não encontrado.")
            return

        print(f"\nAtualizando dados para: {usuario[1]} (ID: {usuario[0]})")
        print("(Deixe em branco para manter o valor atual)")

        # Pede os novos dados (nome e email)
        nome = input(f"Novo Nome ({usuario[1]}): ") or usuario[1]
        email = input(f"Novo Email ({usuario[2]}): ") or usuario[2]

        # Executa o comando UPDATE adaptado
        cursor.execute(
            '''UPDATE usuarios 
               SET nome = ?, email = ?
               WHERE id = ?''',
            (nome, email, id_para_atualizar)
        )
        conexao.commit()
        print("Usuário atualizado com sucesso!")

    except sqlite3.Error as e:
        print(f"Erro ao atualizar usuário: {e}")
    finally:
        if conexao:
            conexao.close()

# --- DELETE (Deletar) ---
def deletar_usuario():
    """Pede um ID e remove um usuário do banco."""
    print("\n--- (D) Deletar Usuário ---")
    listar_usuarios() # Mostra a lista para facilitar
    try:
        id_para_deletar = int(input("Digite o ID do usuário que deseja DELETAR: "))
    except ValueError:
        print("ID inválido.")
        return

    try:
        conexao = conectar()
        cursor = conexao.cursor()

        # SQL adaptado para 'usuarios'
        cursor.execute("SELECT nome FROM usuarios WHERE id = ?", (id_para_deletar,))
        usuario = cursor.fetchone()
        
        if not usuario:
            print(f"Erro: Usuário com ID {id_para_deletar} não encontrado.")
            return
        
        # Confirmação final
        confirmacao = input(f"Tem CERTEZA que quer deletar o usuário '{usuario[0]}' (ID: {id_para_deletar})? [s/n]: ").lower()

        if confirmacao == 's':
            # SQL adaptado para 'usuarios'
            cursor.execute("DELETE FROM usuarios WHERE id = ?", (id_para_deletar,))
            conexao.commit()
            print("Usuário deletado com sucesso.")
        else:
            print("Operação cancelada.")
            
    except sqlite3.Error as e:
        print(f"Erro ao deletar usuário: {e}")
    finally:
        if conexao:
            conexao.close()

# --- FUNÇÃO PRINCIPAL (MENU) ---
def main():
    """Função principal que mostra o menu e gerencia o loop do programa."""
    criar_tabela() # Garante que a tabela 'usuarios' exista

    while True:
        print("\n--- GERENCIADOR DE USUÁRIOS (CRUD) ---")
        print("1. Adicionar Usuário (Create)")
        print("2. Listar Usuários (Read)")
        print("3. Atualizar Usuário (Update)")
        print("4. Deletar Usuário (Delete)")
        print("5. Sair")
        
        escolha = input("Escolha uma opção (1-5): ")
        
        if escolha == '1':
            adicionar_usuario()
        elif escolha == '2':
            listar_usuarios()
        elif escolha == '3':
            atualizar_usuario()
        elif escolha == '4':
            deletar_usuario()
        elif escolha == '5':
            print("Saindo do programa...")
            break
        else:
            print("Opção inválida. Por favor, tente novamente.")

# --- INICIA O PROGRAMA ---
if __name__ == "__main__":
    main()