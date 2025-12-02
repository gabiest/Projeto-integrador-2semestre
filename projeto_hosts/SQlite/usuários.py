import sqlite3

conexao = None
cursor = None

try:
    # 1. Conectar (ou criar) um banco de dados
    # Como você apagou 'meu_banco.db', ele será criado do zero
    conexao = sqlite3.connect('meu_banco.db')
    cursor = conexao.cursor()

    # --- ETAPA DE CRIAÇÃO (CREATE) ---
    # Este comando AGORA VAI SER EXECUTADO
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT,
        senha TEXT NOT NULL
    )
    ''')
    print("Tabela 'usuarios' criada/verificada com a coluna 'senha'.")

    # --- DADOS DE TESTE (Corrigido) ---
    # CORREÇÃO: Agora tem 4 placeholders (?, ?, ?, ?)
    cursor.execute("INSERT OR IGNORE INTO usuarios (id, nome, email, senha) VALUES (?, ?, ?, ?)", (1, 'Ana Silva', 'ana.silva@email.com', 'admin123'))
    cursor.execute("INSERT OR IGNORE INTO usuarios (id, nome, email, senha) VALUES (?, ?, ?, ?)", (2, 'Bruno Costa', 'bruno.costa@email.com', 'admin123'))
    conexao.commit()
    # print("Dados de exemplo inseridos/verificados.")

    # --- CONSULTA (Antes de Adicionar) ---
    print("\n--- DADOS ANTES DE ADICIONAR O NOVO USUÁRIO ---")
    cursor.execute("SELECT * FROM usuarios")
    for usuario in cursor.fetchall():
        print(usuario)

    # --- ETAPA DE ADICIONAR NOVO USUÁRIO (INSERT) ---
    print("\n--- ADICIONAR NOVO USUÁRIO ---")
    nome_digitado = input("Digite o nome do novo usuário: ")
    email_digitado = input("Digite o email do novo usuário: ")
    senha_digitado = input("Digite a senha do novo usuário: ")

    print(f"\nAdicionando '{nome_digitado}' ao banco de dados...")
    
    # CORREÇÃO: Agora tem 3 placeholders (?, ?, ?)
    cursor.execute(
        "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
        (nome_digitado, email_digitado, senha_digitado) 
    )
    
    # 5. Salvar (comitar) a adição
    conexao.commit()
    print("Usuário adicionado com sucesso.")

    # --- CONSULTA (Depois de Adicionar) ---
    print("\n--- DADOS DEPOIS DE ADICIONAR (LISTA ATUALIZADA) ---")
    cursor.execute("SELECT * FROM usuarios")
    
    todos_os_usuarios = cursor.fetchall()

    if not todos_os_usuarios:
        print("Nenhum usuário encontrado.")
    else:
        for usuario in todos_os_usuarios:
            print(usuario) # Agora vai mostrar 4 colunas!

except sqlite3.Error as e:
    print(f"Ocorreu um erro ao interagir com o banco de dados: {e}")
    if conexao:
        conexao.rollback()

finally:
    # 8. Fechar a conexão
    if cursor:
        cursor.close()
    if conexao:
        conexao.close()
        print("\nConexão com o banco de dados fechada.")