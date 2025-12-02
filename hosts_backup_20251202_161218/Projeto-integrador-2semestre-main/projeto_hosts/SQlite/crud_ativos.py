import sqlite3

# Nome do arquivo do nosso banco de dados
DB_FILE = 'meu_banco.db'

def conectar():
    """Cria e retorna uma conexão com o banco de dados."""
    return sqlite3.connect(DB_FILE)

def criar_tabela():
    """Garante que a tabela 'ativos_online' exista."""
    try:
        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ativos_online (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            ip_address TEXT,
            mac_address TEXT,
            status TEXT,
            condicao TEXT,
            tempo_de_uso INTEGER
        )
        ''')
        conexao.commit()
    except sqlite3.Error as e:
        print(f"Erro ao criar a tabela: {e}")
    finally:
        if conexao:
            conexao.close()

# --- CREATE (Criar) ---
def adicionar_ativo():
    """Pede dados ao usuário e insere um novo ativo no banco."""
    print("\n--- (C) Adicionar Novo Ativo ---")
    nome = input("Nome do ativo: ")
    ip = input("IP do ativo: ")
    mac = input("MAC Address: ")
    status = input("Status (ex: Online, Offline): ")
    condicao = input("Condição (ex: Bom, Manutenção): ")
    try:
        tempo = int(input("Tempo de uso (em minutos): "))
    except ValueError:
        print("Tempo inválido, será salvo como 0.")
        tempo = 0

    try:
        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute(
            "INSERT INTO ativos_online (nome, ip_address, mac_address, status, condicao, tempo_de_uso) VALUES (?, ?, ?, ?, ?, ?)",
            (nome, ip, mac, status, condicao, tempo)
        )
        conexao.commit()
        print(f"Ativo '{nome}' adicionado com sucesso!")
    except sqlite3.Error as e:
        print(f"Erro ao adicionar ativo: {e}")
    finally:
        if conexao:
            conexao.close()

# --- READ (Ler) ---
def listar_ativos():
    """Lista todos os ativos cadastrados na tabela."""
    print("\n--- (R) Lista de Todos os Ativos ---")
    try:
        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("SELECT * FROM ativos_online")
        ativos = cursor.fetchall()
        
        if not ativos:
            print("Nenhum ativo cadastrado.")
            return

        # Imprime um cabeçalho formatado
        print(f"{'ID':<4} | {'Nome':<20} | {'IP':<15} | {'Status':<10}")
        print("-" * 55)
        # Imprime cada ativo
        for ativo in ativos:
            # Colunas: 0=id, 1=nome, 2=ip, 4=status
            print(f"{ativo[0]:<4} | {ativo[1]:<20} | {ativo[2]:<15} | {ativo[4]:<10}")

    except sqlite3.Error as e:
        print(f"Erro ao listar ativos: {e}")
    finally:
        if conexao:
            conexao.close()

# --- UPDATE (Atualizar) ---
def atualizar_ativo():
    """Pede um ID e atualiza os dados de um ativo."""
    print("\n--- (U) Atualizar Ativo ---")
    listar_ativos() # Mostra a lista para o usuário saber qual ID
    try:
        id_para_atualizar = int(input("Digite o ID do ativo que deseja atualizar: "))
    except ValueError:
        print("ID inválido.")
        return

    try:
        conexao = conectar()
        cursor = conexao.cursor()
        
        # Primeiro, verifica se o ativo existe
        cursor.execute("SELECT * FROM ativos_online WHERE id = ?", (id_para_atualizar,))
        ativo = cursor.fetchone()
        
        if not ativo:
            print(f"Erro: Ativo com ID {id_para_atualizar} não encontrado.")
            return

        print(f"\nAtualizando dados para: {ativo[1]} (ID: {ativo[0]})")
        print("(Deixe em branco para manter o valor atual)")

        # Pede os novos dados, usando o valor antigo (ativo[x]) se o usuário não digitar nada
        nome = input(f"Novo Nome ({ativo[1]}): ") or ativo[1]
        ip = input(f"Novo IP ({ativo[2]}): ") or ativo[2]
        mac = input(f"Novo MAC ({ativo[3]}): ") or ativo[3]
        status = input(f"Novo Status ({ativo[4]}): ") or ativo[4]
        condicao = input(f"Nova Condição ({ativo[5]}): ") or ativo[5]
        
        try:
            tempo_str = input(f"Novo Tempo de Uso ({ativo[6]}): ")
            tempo = int(tempo_str) if tempo_str else ativo[6]
        except ValueError:
            print("Valor inválido, mantendo tempo original.")
            tempo = ativo[6]

        # Executa o comando UPDATE
        cursor.execute(
            '''UPDATE ativos_online 
               SET nome = ?, ip_address = ?, mac_address = ?, status = ?, condicao = ?, tempo_de_uso = ?
               WHERE id = ?''',
            (nome, ip, mac, status, condicao, tempo, id_para_atualizar)
        )
        conexao.commit()
        print("Ativo atualizado com sucesso!")

    except sqlite3.Error as e:
        print(f"Erro ao atualizar ativo: {e}")
    finally:
        if conexao:
            conexao.close()

# --- DELETE (Deletar) ---
def deletar_ativo():
    """Pede um ID e remove um ativo do banco."""
    print("\n--- (D) Deletar Ativo ---")
    listar_ativos() # Mostra a lista para facilitar
    try:
        id_para_deletar = int(input("Digite o ID do ativo que deseja DELETAR: "))
    except ValueError:
        print("ID inválido.")
        return

    try:
        conexao = conectar()
        cursor = conexao.cursor()

        # Verifica se existe antes de tentar deletar
        cursor.execute("SELECT nome FROM ativos_online WHERE id = ?", (id_para_deletar,))
        ativo = cursor.fetchone()
        
        if not ativo:
            print(f"Erro: Ativo com ID {id_para_deletar} não encontrado.")
            return
        
        # Confirmação final
        confirmacao = input(f"Tem CERTEZA que quer deletar o ativo '{ativo[0]}' (ID: {id_para_deletar})? [s/n]: ").lower()

        if confirmacao == 's':
            cursor.execute("DELETE FROM ativos_online WHERE id = ?", (id_para_deletar,))
            conexao.commit()
            print("Ativo deletado com sucesso.")
        else:
            print("Operação cancelada.")
            
    except sqlite3.Error as e:
        print(f"Erro ao deletar ativo: {e}")
    finally:
        if conexao:
            conexao.close()

# --- FUNÇÃO PRINCIPAL (MENU) ---
def main():
    """Função principal que mostra o menu e gerencia o loop do programa."""
    criar_tabela() # Garante que a tabela exista antes de tudo

    while True:
        print("\n--- GERENCIADOR DE ATIVOS (CRUD) ---")
        print("1. Adicionar Ativo (Create)")
        print("2. Listar Ativos (Read)")
        print("3. Atualizar Ativo (Update)")
        print("4. Deletar Ativo (Delete)")
        print("5. Sair")
        
        escolha = input("Escolha uma opção (1-5): ")
        
        if escolha == '1':
            adicionar_ativo()
        elif escolha == '2':
            listar_ativos()
        elif escolha == '3':
            atualizar_ativo()
        elif escolha == '4':
            deletar_ativo()
        elif escolha == '5':
            print("Saindo do programa...")
            break
        else:
            print("Opção inválida. Por favor, tente novamente.")

# --- INICIA O PROGRAMA ---
if __name__ == "__main__":
    main()