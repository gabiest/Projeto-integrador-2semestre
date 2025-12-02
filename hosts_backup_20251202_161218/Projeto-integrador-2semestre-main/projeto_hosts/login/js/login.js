// 1. ADICIONA O LOG DE EXECUÇÃO PARA DEBUG
console.log("LOGIN.JS EXECUTADO...");

// FUNÇÃO PARA EXIBIR A NOTIFICAÇÃO DE ERRO E ESCONDÊ-LA APÓS 3 SEGUNDOS
function showErrorNotification(message, erroDiv) {
    erroDiv.textContent = message;
    erroDiv.style.display = 'block';

    // Esconde o erro após 3000 milissegundos (3 segundos)
    setTimeout(() => {
        erroDiv.style.display = 'none';
        erroDiv.textContent = ''; // Limpa o texto
    }, 3000);
}

// 2. FUNÇÃO AUXILIAR DE TOGGLE (PARA O ÍCONE DE OLHO)
function togglePasswordVisibility(inputID, iconID) {
    const passwordInput = document.getElementById(inputID);
    const toggleIcon = document.getElementById(iconID);

    if (passwordInput && toggleIcon) {
        if (passwordInput.type === 'password') {
            passwordInput.type = 'text';
            toggleIcon.classList.remove('bx-hide');
            toggleIcon.classList.add('bx-show');
        } else {
            passwordInput.type = 'password';
            toggleIcon.classList.remove('bx-show');
            toggleIcon.classList.add('bx-hide');
        }
    }
}

// 3. LÓGICA PRINCIPAL DO FORMULÁRIO DE LOGIN
document.addEventListener('DOMContentLoaded', () => {
    // Seleciona o primeiro (e único) formulário na página
    const form = document.querySelector('form'); 
    
    // Elementos do formulário
    const emailInput = document.getElementById('login-email');
    const senhaInput = document.getElementById('login-password');
    const erroDiv = document.getElementById('login-error');
    
    // O botão de submit do formulário
    const loginButton = form ? form.querySelector('button[type="submit"]') : null;

    if (!form || !emailInput || !senhaInput || !erroDiv || !loginButton) {
        console.error("Erro: Um ou mais elementos do formulário de login não foram encontrados.");
        return; 
    }
    
    // Esconde a mensagem de erro ao iniciar
    erroDiv.style.display = 'none';

    form.addEventListener('submit', async (event) => {
        // Previne o recarregamento da página (a ação padrão do formulário)
        event.preventDefault(); 
        
        erroDiv.style.display = 'none'; // Esconde o erro antes de tentar
        
        // Desabilita o botão para evitar envio duplicado
        loginButton.disabled = true;
        loginButton.textContent = "Entrando...";

        const email = emailInput.value;
        const senha = senhaInput.value;

        console.log(`Tentando login para: ${email}`);

        try {
            // Chamada à API (Back-end)
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, senha }),
            });
            
            const data = await response.json();

            if (response.ok) {
                // SUCESSO!
                console.log("Login bem-sucedido:", data);
                
                // ============================================================
                // ATUALIZAÇÃO IMPORTANTE: SALVAR COMO OBJETO ÚNICO
                // Isso conecta com a página de Configurações e Troca de Senha
                // ============================================================
                const usuarioObjeto = {
                    id: data.usuario.id,
                    nome: data.usuario.nome,
                    email: data.usuario.email
                };
                
                // Salva o objeto inteiro como JSON
                localStorage.setItem('usuario_logado', JSON.stringify(usuarioObjeto));
                
                // Mantém compatibilidade caso algo antigo ainda use chaves separadas (opcional)
                localStorage.setItem('app_user', JSON.stringify(usuarioObjeto)); 
                
                // 2. Redirecionar para a página principal
                // O '../' volta da pasta 'login' para a raiz
                window.location.href = '../home.html'; 
                
            } else {
                // ERRO DE AUTENTICAÇÃO (401)
                const errorMessage = data.erro || data.mensagem || "Erro desconhecido ao logar.";
                console.error("Falha no login:", errorMessage);
                
                // --- EXIBE O ERRO COMO UMA NOTIFICAÇÃO TEMPORÁRIA ---
                showErrorNotification(errorMessage, erroDiv);
                
                senhaInput.value = '';
                loginButton.disabled = false;
                loginButton.textContent = "Login";
            }
        } catch (error) {
            // ERRO DE REDE/SERVIDOR
            console.error("Erro de conexão com a API:", error);
            showErrorNotification("Erro de conexão com o servidor. Verifique se o 'api.py' está rodando.", erroDiv);
            
            loginButton.disabled = false;
            loginButton.textContent = "Login";
            senhaInput.value = '';
        }
    });

    window.togglePasswordVisibility = togglePasswordVisibility;
});