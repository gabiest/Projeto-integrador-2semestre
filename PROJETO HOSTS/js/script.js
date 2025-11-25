/* eslint-disable no-undef */
/* eslint-disable no-unused-vars */

/**
 * ARQUIVO: js/script.js
 * OBJETIVO: Gestor GLOBAL do Site
 * FUNCIONALIDADES: Menu Lateral, Toasts (Avisos), Modais, Configurações de Usuário.
 * * IMPORTANTE: Este arquivo NÃO deve conter lógica de Tabelas ou Gráficos.
 * - Para Tabelas: use 'js/inventario.js'
 * - Para Gráficos: use 'js/charts.js'
 */

document.addEventListener('DOMContentLoaded', () => {
    
    // ============================================================
    // 1. MENU LATERAL E NAVEGAÇÃO
    // ============================================================
    const botaoMenu = document.querySelector('.botao-menu');
    const menuLateral = document.querySelector('.menu-lateral');
    const conteudo = document.querySelector('.conteudo');
    const background = document.querySelector('.background');
    
    const toggleMenu = () => {
        if (menuLateral) menuLateral.classList.toggle('ativo');
        if (botaoMenu) botaoMenu.classList.toggle('ativo');
        if (conteudo) conteudo.classList.toggle('ativo');
        if (background) background.classList.toggle('ativo');
        
        // Específico para a Home (Tela de Boas-Vindas)
        const welcomeScreen = document.querySelector('main.welcome-screen');
        if (welcomeScreen) welcomeScreen.classList.toggle('ativo');
    };

    if (botaoMenu) botaoMenu.addEventListener('click', toggleMenu);
    
    if (background) {
        background.addEventListener('click', () => {
            if (menuLateral && menuLateral.classList.contains('ativo')) {
                toggleMenu();
            }
        });
    }

    // ============================================================
    // 2. SISTEMA DE TOAST (NOTIFICAÇÕES GLOBAIS)
    // ============================================================
    const toastContainer = document.getElementById('toast-container');
    
    // Função Global acessível por outros scripts (inventario.js, charts.js)
    window.showToast = (message, type = 'info', duration = 3000) => {
        if (!toastContainer) return; 

        const toast = document.createElement('div');
        toast.classList.add('toast', type);
        
        let iconClass = 'bi-info-circle-fill';
        if (type === 'success') iconClass = 'bi-check-circle-fill';
        if (type === 'error') iconClass = 'bi-x-octagon-fill';
        
        toast.innerHTML = `<i class="bi ${iconClass}"></i> <span>${message}</span>`;
        toastContainer.prepend(toast); 

        // Animação de entrada e saída
        const removeTimer = setTimeout(() => {
            toast.style.animation = 'fadeOutToast 0.5s ease forwards';
            toast.addEventListener('animationend', () => toast.remove());
        }, duration);

        toast.addEventListener('click', () => {
            clearTimeout(removeTimer);
            toast.remove();
        });
    };

    // Adiciona estilos de animação do toast dinamicamente se não existir
    if (toastContainer && !document.getElementById('toastAnimationStyle')) {
        const style = document.createElement('style');
        style.id = 'toastAnimationStyle';
        style.innerHTML = `@keyframes fadeOutToast { from { opacity: 1; transform: translateX(0); } to { opacity: 0; transform: translateX(100%); } }`;
        document.head.appendChild(style);
    }

    // ============================================================
    // 3. GERENCIAMENTO DE USUÁRIO (LOCALSTORAGE)
    // ============================================================
    const loadUserToUI = () => {
        try {
            const raw = localStorage.getItem('app_user');
            if (!raw) return;
            const user = JSON.parse(raw);
            
            // Atualiza nome no menu
            const profileSpan = document.getElementById('profile-username');
            if (profileSpan && user.name) profileSpan.textContent = user.name;
            
            // Atualiza campos na página de configurações
            const currentUsername = document.getElementById('current-username');
            if (currentUsername && user.name) currentUsername.value = user.name;
            
            const currentEmail = document.getElementById('current-email');
            if (currentEmail && user.email) currentEmail.value = user.email;
        } catch (e) {
            console.warn('Erro carregando usuário', e);
        }
    };
    
    loadUserToUI(); // Carrega ao iniciar

    // Listener para salvar perfil (Apenas na página de Configurações)
    const formPerfil = document.getElementById('form-nome-email');
    if (formPerfil) {
        formPerfil.addEventListener('submit', (e) => {
            e.preventDefault();
            const newName = document.getElementById('new-username')?.value.trim();
            const newEmail = document.getElementById('new-email')?.value.trim();
            
            try {
                const raw = localStorage.getItem('app_user');
                const prev = raw ? JSON.parse(raw) : {};
                const updated = { ...prev, name: newName || prev.name, email: newEmail || prev.email };
                
                localStorage.setItem('app_user', JSON.stringify(updated));
                loadUserToUI();
                
                if(window.closeModal) window.closeModal('modal-nome-email');
                window.showToast('Perfil atualizado!', 'success');
            } catch (err) {
                console.error(err);
                window.showToast('Erro ao salvar perfil.', 'error');
            }
        });
    }

    // ============================================================
    // 4. LÓGICA DE CONFIGURAÇÕES (LINKS E MODAIS)
    // ============================================================

    // Abrir modal de perfil
    const perfilCard = document.querySelector('.cartao-perfil');
    if (perfilCard) {
        perfilCard.onclick = () => window.openModal('modal-nome-email');
    }

    // Trocar Senha
    const linkSenha = document.querySelector('.bi-key')?.closest('a');
    if (linkSenha) {
        linkSenha.onclick = (e) => { e.preventDefault(); window.openModal('modal-trocar-senha'); };
    }
    const formSenha = document.getElementById('form-trocar-senha');
    if (formSenha) {
        formSenha.onsubmit = (e) => {
            e.preventDefault();
            window.closeModal('modal-trocar-senha');
            window.showToast('Senha alterada com sucesso!', 'success');
        };
    }

    // Termos e Atualização
    const linkTermos = document.querySelector('.bi-file-earmark-text')?.closest('a');
    if (linkTermos) {
        linkTermos.onclick = (e) => { e.preventDefault(); window.openModal('modal-termos-condicoes'); };
    }
    const linkUpdate = document.querySelector('.bi-cloud-download')?.closest('a');
    if (linkUpdate) {
        linkUpdate.onclick = (e) => { e.preventDefault(); window.openModal('modal-atualizacao-software'); };
    }

    // Ícone de "Olho" da senha
    document.querySelectorAll('.password-toggle-icon').forEach(icon => {
        icon.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            const input = document.getElementById(targetId);
            if (input) {
                if (input.type === 'password') {
                    input.type = 'text';
                    this.classList.replace('bi-eye-slash-fill', 'bi-eye-fill');
                } else {
                    input.type = 'password';
                    this.classList.replace('bi-eye-fill', 'bi-eye-slash-fill');
                }
            }
        });
    });

}); // FIM DO DOM CONTENT LOADED

// ============================================================
// 5. FUNÇÕES GLOBAIS (FORA DO ESCOPO)
// ============================================================

window.openModal = (modalId) => {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
        setTimeout(() => modal.style.opacity = '1', 10);
    }
    // Fecha o menu lateral se estiver aberto (melhor UX no mobile)
    const menu = document.querySelector('.menu-lateral');
    if (menu && menu.classList.contains('ativo')) {
        menu.classList.remove('ativo');
        document.querySelector('.conteudo')?.classList.remove('ativo');
        document.querySelector('.background')?.classList.remove('ativo');
        document.querySelector('.botao-menu')?.classList.remove('ativo');
    }
};

window.closeModal = (modalId) => {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.opacity = '0';
        setTimeout(() => modal.style.display = 'none', 300);
    }
};

// Fechar modal ao clicar fora (Overlay)
document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', function(e) {
        if (e.target === this) window.closeModal(this.id);
    });
});