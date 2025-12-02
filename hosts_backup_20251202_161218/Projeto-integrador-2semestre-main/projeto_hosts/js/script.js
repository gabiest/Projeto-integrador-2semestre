/* eslint-disable no-undef */
/* eslint-disable no-unused-vars */

/**
 * Gestor do Menu Lateral, Navegação, Dashboard, Inventário e Configurações
 * Este script unificado controla as funcionalidades principais da aplicação.
 * VERSÃO CORRIGIDA E UNIFICADA COM API E TROCA DE SENHA REAL
 */
document.addEventListener('DOMContentLoaded', () => {
    
    // --- SELEÇÃO DE ELEMENTOS GERAIS ---
    const botaoMenu = document.querySelector('.botao-menu');
    const menuLateral = document.querySelector('.menu-lateral');
    const conteudo = document.querySelector('.conteudo');
    const background = document.querySelector('.background');
    
    // --- LÓGICA DO TOAST (Notificação Global) ---
    const toastContainer = document.getElementById('toast-container');
    const showToast = (message, type = 'info', duration = 3000) => {
        if (!toastContainer) {
            console.warn('Container de Toast não encontrado nesta página.');
            return; 
        }
        const toast = document.createElement('div');
        toast.classList.add('toast', type);
        let iconClass = 'bi-info-circle-fill';
        if (type === 'success') iconClass = 'bi-check-circle-fill';
        if (type === 'error') iconClass = 'bi-x-octagon-fill';
        toast.innerHTML = `<i class="bi ${iconClass}"></i> <span>${message}</span>`;
        toastContainer.prepend(toast);
        const removeTimer = setTimeout(() => {
            toast.style.animation = 'fadeOutToast 0.5s ease forwards';
            toast.addEventListener('animationend', () => toast.remove());
        }, duration);
        toast.addEventListener('click', () => {
            clearTimeout(removeTimer);
            toast.style.animation = 'fadeOutToast 0.3s ease forwards';
            toast.addEventListener('animationend', () => toast.remove());
        });
    };
    
    if (toastContainer && !document.getElementById('toastAnimationStyle')) {
        const style = document.createElement('style');
        style.id = 'toastAnimationStyle';
        style.innerHTML = `@keyframes fadeOutToast { from { opacity: 1; transform: translateX(0); } to { opacity: 0; transform: translateX(100%); } }`;
        document.head.appendChild(style);
    }
    window.showToast = showToast;


    // --- FUNÇÕES GLOBAIS DE MODAL ---
    window.openModal = (modalId) => {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'flex';
            setTimeout(() => { 
                modal.style.opacity = '1';
            }, 10);
        }
        if (menuLateral && menuLateral.classList.contains('ativo')) {
            toggleMenu();
        }
    };

    window.closeModal = (modalId) => {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.opacity = '0';
            setTimeout(() => { 
                modal.style.display = 'none';
            }, 300); 
        }
    };

    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', function(e) {
            if (e.target === this) {
                window.closeModal(this.id);
            }
        });
    });


    // --- LÓGICA DE USUÁRIO (localStorage) ---
    const loadUserToUI = () => {
        try {
            // Tenta pegar de 'usuario_logado' (padrão do login) ou 'app_user' (fallback)
            const raw = localStorage.getItem('usuario_logado') || localStorage.getItem('app_user');
            if (!raw) return;
            const user = JSON.parse(raw);
            
            const profileSpan = document.getElementById('profile-username');
            if (profileSpan && user.nome) profileSpan.textContent = user.nome; // user.nome vindo da API
            
            const currentUsername = document.getElementById('current-username');
            if (currentUsername && user.nome) currentUsername.value = user.nome;
            
            const currentEmail = document.getElementById('current-email');
            if (currentEmail && user.email) currentEmail.value = user.email;
        } catch (e) {
            console.warn('Erro carregando usuário do localStorage', e);
        }
    };

    const bindProfileForm = () => {
        const form = document.getElementById('form-nome-email');
        if (!form) return; 
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const newName = document.getElementById('new-username')?.value.trim() || '';
            const newEmail = document.getElementById('new-email')?.value.trim() || '';
            try {
                const raw = localStorage.getItem('usuario_logado') || localStorage.getItem('app_user');
                const prev = raw ? JSON.parse(raw) : {};
                
                // Atualiza localmente (Visual apenas, ideal seria ter rota na API para isso tbm)
                const updated = { ...prev, nome: newName || prev.nome, email: newEmail || prev.email };
                
                localStorage.setItem('usuario_logado', JSON.stringify(updated));
                localStorage.setItem('app_user', JSON.stringify(updated)); // Mantém compatibilidade
                
                loadUserToUI(); 
                window.closeModal('modal-nome-email');
                showToast('Informações salvas localmente (Visual)!', 'success');
                
            } catch (err) {
                console.warn('Erro ao salvar novo nome/email', err);
                showToast('Erro ao salvar informações.', 'error');
            }
        });
    };

    loadUserToUI();
    bindProfileForm();

    // --- LÓGICA DO MENU LATERAL ---
    const toggleMenu = () => {
        if (menuLateral) menuLateral.classList.toggle('ativo');
        if (botaoMenu) botaoMenu.classList.toggle('ativo');
        if (conteudo) conteudo.classList.toggle('ativo');
        if (background) background.classList.toggle('ativo');
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

    // =======================================================
    // === LÓGICA DA PÁGINA DE DASHBOARD (Gráficos e KPIs) ===
    // =======================================================
    
    const dashboardGrid = document.querySelector('.dashboard-grid');
    if (dashboardGrid) { 
    
        // --- CHARTS.JS ---
        const blue = '#00BFFF';
        const success = '#41f1b6';
        const warning = '#ffbb55';
        const danger = '#ff7782';
        const textColor = '#ffffffff';
        const gridColor = 'rgba(255, 255, 255, 0.14)';
        Chart.defaults.color = textColor;
        Chart.defaults.font.family = 'Arimo';
        Chart.defaults.plugins.legend.display = false;
        
        let statusChartInstance = null;
        let assetTypeChartInstance = null;

        function createGradient(ctx, color1, color2) {
            if (!ctx?.canvas) return color1;
            const gradient = ctx.createLinearGradient(0, 0, 0, ctx.canvas.height);
            gradient.addColorStop(0, color1);
            gradient.addColorStop(1, color2);
            return gradient;
        }

        const cards = document.querySelectorAll('.kpi-card, .chart-card, .table-card');
        cards.forEach((card, index) => {
            card.style.opacity = '0'; 
            card.style.animationDelay = `${index * 0.08}s`;
            card.classList.add('animate-entrada');
        });

        const animateCountUp = (elementId, finalValue, duration = 1500, decimalPlaces = 0, suffix = '') => {
            const element = document.getElementById(elementId);
            if (!element) return;
            let startTimestamp = null;
            const step = (timestamp) => {
                if (!startTimestamp) startTimestamp = timestamp;
                const progress = Math.min((timestamp - startTimestamp) / duration, 1);
                const currentValue = progress * finalValue;
                element.textContent = currentValue.toFixed(decimalPlaces) + suffix;
                if (progress < 1) {
                    window.requestAnimationFrame(step);
                } else {
                    element.textContent = finalValue.toFixed(decimalPlaces) + suffix;
                }
            };
            window.requestAnimationFrame(step);
        };
        
        async function carregarEstatisticas() { 
        try {
                const response = await fetch('/api/estatisticas');
                if (!response.ok) throw new Error('Falha ao buscar estatísticas');
                const stats = await response.json();
                
                let disponibilidade = 0.0;
                if (stats.total_ativos > 0) {
                    disponibilidade = (stats.ativos_online / stats.total_ativos * 100);
                }
                const ativos_offline = stats.total_ativos - stats.ativos_online;
                
                animateCountUp('availability-value', disponibilidade, 1500, 1, '%');
                animateCountUp('online-assets-dash', stats.ativos_online, 1500, 0, '');
                animateCountUp('offline-assets-count', ativos_offline, 1500, 0, ''); 
                
            } catch (error) {
                console.error("Erro ao carregar KPIs:", error);
            }
        }
        
        async function carregarDadosDosGraficos() {
            try {
                const responseAssets = await fetch('/api/ativos');
                if (!responseAssets.ok) throw new Error('Falha ao buscar ativos');
                const assets = await responseAssets.json();
                
                const onlineAssets = assets.filter(asset => asset.status === 'Online').length;
                const offlineAssets = assets.filter(asset => asset.status !== 'Online').length;

                const statusCtx = document.getElementById('statusChart');
                if (statusCtx) {
                    if (statusChartInstance) statusChartInstance.destroy();
                    statusChartInstance = new Chart(statusCtx.getContext('2d'), {
                        type: 'doughnut',
                        data: {
                            labels: ['Online', 'Offline'],
                            datasets: [{
                                data: [onlineAssets, offlineAssets],
                                backgroundColor: [success, danger],
                                borderColor: 'transparent',
                                borderWidth: 0,
                                hoverOffset: 8
                            }]
                        },
                        options: {
                            maintainAspectRatio: false,
                            cutout: '70%',
                            plugins: { legend: { display: true, position: 'bottom', labels: { padding: 20 } } }
                        }
                    });
                }
                
                const responseTipos = await fetch('/api/estatisticas/tipos');
                if (!responseTipos.ok) throw new Error('Falha ao buscar tipos de ativos');
                const tiposData = await responseTipos.json();
                
                const labels = tiposData.map(item => item.tipo);
                const contagens = tiposData.map(item => item.contagem);
                
                const assetTypeCtx = document.getElementById('assetTypeChart');
                if (assetTypeCtx) {
                    const blue3Gradient = createGradient(assetTypeCtx.getContext('2d'), '#00BFFF', 'rgba(0, 191, 255, 0.3)');
                    if (assetTypeChartInstance) assetTypeChartInstance.destroy();
                    assetTypeChartInstance = new Chart(assetTypeCtx.getContext('2d'), {
                        type: 'bar',
                        data: {
                            labels: labels,
                            datasets: [{
                                label: 'Quantidade',
                                data: contagens,
                                backgroundColor: blue3Gradient,
                                borderRadius: 5
                            }]
                        },
                        options: { 
                            maintainAspectRatio: false,
                            scales: { 
                                y: { grid: { color: gridColor }, beginAtZero: true, ticks: { stepSize: 1 } }, 
                                x: { grid: { display: false } } 
                            } 
                        }
                    });
                }

            } catch (error) {
                console.error("Erro ao carregar dados dos gráficos:", error);
            }
        }
        
        carregarEstatisticas();
        carregarDadosDosGraficos();
    }


    // =============================================================
    // === LÓGICA DA PÁGINA DE INVENTÁRIO (Tabela CRUD) ===
    // =============================================================

    const inventoryTableBody = document.getElementById('inventory-table-body');
    
    // O código dentro deste IF só roda se estiver na página de inventário
    if (inventoryTableBody) {
        
        const searchInput = document.getElementById('search-input');
        const addAssetBtn = document.getElementById('add-asset-btn');
        const modal = document.getElementById('asset-modal');
        const cancelBtn = document.getElementById('cancel-btn');
        const assetForm = document.getElementById('asset-form');
        const modalTitle = document.getElementById('modal-title');
        const assetIdInput = document.getElementById('assetIndex'); // Campo oculto do ID
        
        const deleteModal = document.getElementById('delete-confirm-modal');
        const cancelDeleteBtn = document.getElementById('cancel-delete-btn');
        const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
        const assetNameToDeleteSpan = document.getElementById('asset-name-to-delete');

        const API_URL = '/api/ativos'; 
        let assetsData = []; 
        let assetIdToDelete = null;

        // --- FUNÇÕES PRINCIPAIS (Definidas ANTES de usar) ---

        const renderTable = (data) => {
            inventoryTableBody.innerHTML = '';
            if (data.length === 0) {
                inventoryTableBody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 2rem;">Nenhum ativo encontrado.</td></tr>`;
                return;
            }

            data.forEach((asset, index) => {
                const tr = document.createElement('tr');
                
                let conditionClass = '';
                if (asset.condicao === 'Alocado' || asset.condicao === 'Crítico') conditionClass = 'danger';
                else if (asset.condicao === 'Manutenção') conditionClass = 'warning';
                else conditionClass = 'success';
                
                const statusClass = asset.status === 'Online' ? 'success' : 'danger';

                tr.innerHTML = `
                    <td>${asset.nome || '-'}</td>
                    <td>${asset.mac_address || '-'}</td> 
                    <td>${asset.ip_address || '-'}</td>
                    <td class="${statusClass}">${asset.status || '-'}</td>
                    <td class="${conditionClass}">${asset.condicao || '-'}</td>
                    <td class="action-icons">
                        <i class="bi bi-pencil-square edit-btn" data-id="${asset.id}" title="Editar"></i>
                        <i class="bi bi-trash delete-btn" data-id="${asset.id}" title="Excluir"></i>
                    </td>
                `;
                tr.style.setProperty('--animation-delay', `${index * 0.05}s`);
                inventoryTableBody.appendChild(tr);

                // Botão Editar (Binding direto)
                tr.querySelector('.edit-btn')?.addEventListener('click', () => {
                    const assetToEdit = assetsData.find(a => a.id == asset.id);
                    if (assetToEdit) {
                        assetForm.reset();
                        if(assetIdInput) assetIdInput.value = assetToEdit.id; 
                        if(modalTitle) modalTitle.textContent = 'Editar Ativo';
                        
                        document.getElementById('assetName').value = assetToEdit.nome || '';
                        document.getElementById('macAddress').value = assetToEdit.mac_address || '';
                        document.getElementById('assetId').value = assetToEdit.ip_address || ''; 
                        
                        // Preenche o tipo, se existir no HTML
                        const typeSelect = document.getElementById('assetType');
                        if(typeSelect) typeSelect.value = assetToEdit.tipo || 'Outros';

                        document.getElementById('assetStatus').value = assetToEdit.status || 'Online';
                        document.getElementById('assetCondition').value = assetToEdit.condicao || 'Disponível';
                        
                        window.openModal('asset-modal');
                    }
                });
                
                // Botão Excluir (Binding direto)
                tr.querySelector('.delete-btn')?.addEventListener('click', () => {
                    assetIdToDelete = asset.id; 
                    if(assetNameToDeleteSpan) assetNameToDeleteSpan.textContent = asset.nome;
                    window.openModal('delete-confirm-modal');
                });
            });
        };

        async function carregarDadosDaAPI() {
            try {
                const response = await fetch('/api/ativos'); 
                if (!response.ok) throw new Error(`Erro: ${response.statusText}`);
                
                assetsData = await response.json(); 
                renderTable(assetsData); 
                
            } catch (error) {
                console.error("Falha ao carregar ativos:", error);
                showToast('Erro ao carregar ativos.', 'error');
                inventoryTableBody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 2rem; color: #ff7782;">Falha ao conectar com o servidor.</td></tr>`;
            }
        }

        // --- EVENT LISTENERS (Botões e Formulário) ---

        if (addAssetBtn) {
            addAssetBtn.addEventListener('click', () => {
                assetForm.reset();
                if(assetIdInput) assetIdInput.value = ''; 
                if(modalTitle) modalTitle.textContent = 'Adicionar Novo Ativo';
                window.openModal('asset-modal');
            });
        }
        
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                carregarDadosDaAPI();
                showToast('Lista atualizada!', 'success');
            });
        }

        if (cancelBtn) cancelBtn.addEventListener('click', () => window.closeModal('asset-modal'));
        if (cancelDeleteBtn) cancelDeleteBtn.addEventListener('click', () => window.closeModal('delete-confirm-modal'));


        if (assetForm) {
            assetForm.addEventListener('submit', async (e) => { 
                e.preventDefault();
                
                const assetData = {
                    nome: document.getElementById('assetName')?.value || 'Nome Indefinido',
                    mac_address: document.getElementById('macAddress')?.value || '',
                    ip_address: document.getElementById('assetId')?.value || '', 
                    tipo: document.getElementById('assetType')?.value || 'Outros', 
                    status: document.getElementById('assetStatus')?.value || 'Online',
                    condicao: document.getElementById('assetCondition')?.value || 'Disponível'
                };
                
                const idParaEditar = assetIdInput ? assetIdInput.value : '';
                
                let url = API_URL;
                let method = 'POST'; 
                let toastMessage = 'Ativo adicionado com sucesso!';

                if (idParaEditar) {
                    url = `${API_URL}/${idParaEditar}`;
                    method = 'PUT';
                    toastMessage = 'Ativo atualizado com sucesso!';
                }

                try {
                    const response = await fetch(url, {
                        method: method,
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(assetData)
                    });

                    if (!response.ok) {
                        const errorData = await response.json();
                        throw new Error(errorData.erro || 'Falha ao salvar ativo');
                    }
                    
                    showToast(toastMessage, 'success');
                    window.closeModal('asset-modal');
                    carregarDadosDaAPI(); 
                    
                    // Se estiver rodando o Dashboard no mesmo arquivo (SPA), atualiza gráficos
                    if (dashboardGrid && typeof carregarDadosDosGraficos === 'function') {
                        carregarDadosDosGraficos(); 
                    }

                } catch (error) {
                    console.error("Erro ao salvar:", error);
                    showToast(error.message, 'error');
                }
            });
        }

        if (confirmDeleteBtn) {
            confirmDeleteBtn.addEventListener('click', async () => { 
                if (assetIdToDelete !== null) {
                    try {
                        const response = await fetch(`${API_URL}/${assetIdToDelete}`, { method: 'DELETE' });
                        if (!response.ok) {
                            const errorData = await response.json();
                            throw new Error(errorData.erro || 'Falha ao excluir');
                        }
                        showToast(`Ativo excluído com sucesso.`, 'info');
                        carregarDadosDaAPI(); 
                        
                        if (dashboardGrid && typeof carregarDadosDosGraficos === 'function') {
                            carregarDadosDosGraficos(); 
                        }
                    } catch (error) {
                        console.error("Erro ao deletar:", error);
                        showToast(error.message, 'error');
                    }
                    window.closeModal('delete-confirm-modal');
                    assetIdToDelete = null; 
                }
            });
        }

        // CSS de Animação da Tabela
        if (!document.getElementById('tableRowAnimationStyle')) {
            const style = document.createElement('style');
            style.id = 'tableRowAnimationStyle';
            style.innerHTML = `
                .inventory-table tbody td { 
                    opacity: 0; 
                    transform: translateY(10px); 
                    animation: fadeInRow 0.4s ease forwards; 
                    animation-delay: var(--animation-delay, 0s);
                }
                @keyframes fadeInRow { 
                    to { opacity: 1; transform: translateY(0); } 
                }`;
            document.head.appendChild(style);
        }

        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                const searchTerm = e.target.value.toLowerCase().trim();
                const filteredAssets = assetsData.filter(asset =>
                    (asset.nome && asset.nome.toLowerCase().includes(searchTerm)) ||
                    (asset.mac_address && asset.mac_address.toLowerCase().includes(searchTerm)) || 
                    (asset.ip_address && asset.ip_address.toLowerCase().includes(searchTerm)) ||
                    (asset.status && asset.status.toLowerCase().includes(searchTerm)) ||
                    (asset.condicao && asset.condicao.toLowerCase().includes(searchTerm))
                );
                renderTable(filteredAssets);
            });
        }

        // --- INICIALIZAÇÃO FINAL ---
        carregarDadosDaAPI();
    } 


    // =======================================================
    // == LÓGICA DA PÁGINA DE CONFIGURAÇÕES
    // =======================================================
    
    // --- BINDING DOS LINKS PARA ABRIR MODAIS ---
    const perfilCard = document.querySelector('.cartao-perfil');
    if (perfilCard) {
        perfilCard.onclick = () => {
            const newUsername = document.getElementById('new-username');
            const newEmail = document.getElementById('new-email');
            if (newUsername) newUsername.value = '';
            if (newEmail) newEmail.value = '';
            window.openModal('modal-nome-email');
        };
    }
    
    // 2. Link "Trocar Senha"
    const senhaLink = document.querySelector('a[href="#"] .bi-key')?.closest('.configuracao-item');
    if (senhaLink) {
        senhaLink.onclick = (e) => {
            e.preventDefault();
            
            // Limpa os campos antes de abrir
            const fields = ['current-password', 'new-password', 'confirm-new-password'];
            fields.forEach(id => {
                const el = document.getElementById(id);
                if(el) el.value = '';
            });

            window.openModal('modal-trocar-senha');
        };
    }

    // =========================================================================
    // === ATUALIZAÇÃO IMPORTANTE: TROCA DE SENHA CONECTADA AO BANCO DE DADOS ==
    // =========================================================================
    const formTrocarSenha = document.getElementById('form-trocar-senha');
    if (formTrocarSenha) {
        formTrocarSenha.onsubmit = async function(e) {
            e.preventDefault();
            
            // Pega os valores dos inputs
            // NOTA: Certifique-se que no seu HTML o ID do input da senha atual é 'current-password'
            const senhaAtual = document.getElementById('current-password')?.value || '';
            const novaSenha = document.getElementById('new-password')?.value || '';
            const confirmSenha = document.getElementById('confirm-new-password')?.value || '';

            // Validações Básicas
            if (!senhaAtual) {
                showToast('Digite sua senha atual.', 'error');
                return;
            }
            if (novaSenha.length < 4) {
                showToast('A nova senha deve ter pelo menos 4 caracteres.', 'error'); 
                return;
            }
            if (novaSenha !== confirmSenha) {
                showToast('A nova senha e a confirmação não coincidem.', 'error');
                return;
            }
            
            // Recupera o ID do usuário Logado
            // Tenta 'usuario_logado' (padrão) ou 'app_user' (fallback)
            const rawUser = localStorage.getItem('usuario_logado') || localStorage.getItem('app_user');
            const usuario = rawUser ? JSON.parse(rawUser) : null;
            
            if (!usuario || !usuario.id) {
                showToast('Erro: Sessão inválida. Faça login novamente.', 'error');
                return;
            }

            // Envia para a API Python
            try {
                showToast('Processando...', 'info', 1000);
                
                const response = await fetch('/api/trocar-senha', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        id: usuario.id,
                        senha_atual: senhaAtual,
                        nova_senha: novaSenha
                    })
                });

                const data = await response.json();

                if (response.ok) {
                    // Sucesso
                    window.closeModal('modal-trocar-senha');
                    showToast('Sucesso! ' + data.mensagem, 'success');
                    
                    // Limpa formulário
                    formTrocarSenha.reset();
                } else {
                    // Erro (ex: Senha atual incorreta)
                    showToast('Erro: ' + data.erro, 'error');
                }

            } catch (error) {
                console.error("Erro na troca de senha:", error);
                showToast('Erro de conexão com o servidor.', 'error');
            }
        };
    }
    
    // 3. Link "Atualização de Software"
    const updateLink = document.querySelector('a[href="#"] .bi-cloud-download')?.closest('.configuracao-item');
    if (updateLink) {
        updateLink.onclick = (e) => {
            e.preventDefault();
            window.openModal('modal-atualizacao-software');
        };
    }

    // 4. Link "Termos e Condições"
    const termosLink = document.querySelector('a[href="#"] .bi-file-earmark-text')?.closest('.configuracao-item');
    if (termosLink) {
        termosLink.onclick = (e) => {
            e.preventDefault();
            window.openModal('modal-termos-condicoes');
        };
    }

    // 5. Formulário de Linguagem
    const formLinguagem = document.getElementById('form-linguagem');
    if (formLinguagem) {
        formLinguagem.onsubmit = function(e) {
            e.preventDefault();
            const selectedLang = document.getElementById('language-select').value;
            const langText = document.getElementById('language-select').options[document.getElementById('language-select').selectedIndex].text;
            
            const langItem = document.querySelector('a[href="#"] .bi-globe')?.closest('.configuracao-item');
            if (langItem) {
                langItem.querySelector('.detalhe').textContent = langText;
            }
            
            window.closeModal('modal-linguagem');
            showToast(`Idioma alterado para: ${langText}`, 'info');
        };
    }

    // 6. Lógica do "Olho da Senha"
    document.querySelectorAll('.password-toggle-icon').forEach(icon => {
        icon.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            const inputField = document.getElementById(targetId);
            if (inputField) {
                if (inputField.type === 'password') {
                    inputField.type = 'text';
                    this.classList.remove('bi-eye-slash-fill');
                    this.classList.add('bi-eye-fill');
                } else {
                    inputField.type = 'password';
                    this.classList.remove('bi-eye-fill');
                    this.classList.add('bi-eye-slash-fill');
                }
            }
        });
    });
    
    // --- ATUALIZAÇÃO DE SOFTWARE (Auto-close) ---
    const btnVerificarUpdate = document.getElementById('btn-verificar-update');
    
    if (btnVerificarUpdate) {
        btnVerificarUpdate.addEventListener('click', () => {
            showToast('Nenhuma atualização disponível.', 'success');
            
            const versaoAtualInput = document.getElementById('current-version-input');
            const agora = new Date();
            const dia = String(agora.getDate()).padStart(2, '0');
            const mes = String(agora.getMonth() + 1).padStart(2, '0');
            const ano = agora.getFullYear();
            const dataFormatada = `${dia}/${mes}/${ano}`;
            
            if (versaoAtualInput) {
                const prefixo = versaoAtualInput.value.split(' - ')[0]; 
                versaoAtualInput.value = `${prefixo} - Última verificação: ${dataFormatada}`;
            }

            setTimeout(() => {
                window.closeModal('modal-atualizacao-software');
            }, 1); 

            btnVerificarUpdate.disabled = true;
            setTimeout(() => {
                btnVerificarUpdate.disabled = false;
            }, 3000); 
        });
    }
    
    const btnFecharUpdate = document.getElementById('btn-fechar-update');
    if(btnFecharUpdate) {
        btnFecharUpdate.addEventListener('click', () => {
            window.closeModal('modal-atualizacao-software');
        });
    }

}); // --- FIM ---