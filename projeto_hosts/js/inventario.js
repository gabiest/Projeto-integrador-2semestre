/**
 * Script para gerenciar o inventário de ativos
 * Puxa dados DIRETO DO BANCO DE DADOS via API
 */

// ==================== VARIÁVEIS GLOBAIS ====================

let ativos = []; // Array que armazena todos os ativos do banco

// ==================== CARREGAR ATIVOS DO BANCO ====================

async function carregarAtivosDoBank() {
    try {
        const response = await fetch('/api/ativos');
        const dados = await response.json();
        
        ativos = dados;
        console.log('✅ Ativos carregados do banco:', ativos);
        
        // Renderizar a tabela
        renderizarTabela(ativos);
        
    } catch (error) {
        console.error('❌ Erro ao carregar ativos:', error);
        mostrarToast('Erro ao carregar ativos do banco!', 'error');
    }
}

// ==================== RENDERIZAR TABELA ====================

function renderizarTabela(ativosParaMostrar) {
    const tbody = document.getElementById('inventory-table-body');
    
    if (!tbody) {
        console.warn('⚠️ Elemento tbody não encontrado');
        return;
    }
    
    // Limpar tabela
    tbody.innerHTML = '';
    
    // Se não tem ativos
    if (!ativosParaMostrar || ativosParaMostrar.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px;">Nenhum ativo encontrado</td></tr>';
        return;
    }
    
    // Renderizar cada ativo
    ativosParaMostrar.forEach((ativo, index) => {
        const row = document.createElement('tr');
        
        // Badge de status com cor
        const statusBadge = ativo.status === 'Online' 
            ? `<span class="badge badge-online">${ativo.status}</span>`
            : `<span class="badge badge-offline">${ativo.status}</span>`;
        
        // Badge de condição
        let condiacaoBadge = '';
        switch(ativo.condicao) {
            case 'Disponível':
                condiacaoBadge = '<span class="badge badge-disponivel">Disponível</span>';
                break;
            case 'Manutenção':
                condiacaoBadge = '<span class="badge badge-manutencao">Manutenção</span>';
                break;
            case 'Alocado':
                condiacaoBadge = '<span class="badge badge-alocado">Alocado</span>';
                break;
            default:
                condiacaoBadge = `<span class="badge">${ativo.condicao}</span>`;
        }
        
        row.innerHTML = `
            <td class="asset-name">
                <strong>${ativo.nome || 'N/A'}</strong>
            </td>
            <td class="asset-mac">${ativo.mac_address || 'N/A'}</td>
            <td class="asset-id">
                ${ativo.ip_address || 'N/A'}
            </td>
            <td class="asset-status">
                ${statusBadge}
            </td>
            <td class="asset-condition">
                ${condiacaoBadge}
            </td>
            <td class="asset-actions">
                <button class="btn-edit" onclick="editarAtivo(${index})" title="Editar">
                    <i class="bi bi-pencil"></i>
                </button>
                <button class="btn-delete" onclick="abrirDeleteModal(${index})" title="Deletar">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        `;
        
        tbody.appendChild(row);
    });
    
    console.log(`✅ Tabela renderizada com ${ativosParaMostrar.length} ativos`);
}

// ==================== BUSCA E FILTRO ====================

function configurarBusca() {
    const searchInput = document.getElementById('search-input');
    
    if (!searchInput) {
        console.warn('⚠️ Input de busca não encontrado');
        return;
    }
    
    searchInput.addEventListener('input', (e) => {
        const termo = e.target.value.toLowerCase();
        
        // Filtrar ativos baseado no termo
        const ativosFiltrados = ativos.filter(ativo => {
            return (
                (ativo.nome && ativo.nome.toLowerCase().includes(termo)) ||
                (ativo.ip_address && ativo.ip_address.includes(termo)) ||
                (ativo.mac_address && ativo.mac_address.toLowerCase().includes(termo)) ||
                (ativo.status && ativo.status.toLowerCase().includes(termo))
            );
        });
        
        renderizarTabela(ativosFiltrados);
    });
}

// ==================== MODAL PARA ADICIONAR/EDITAR ====================

function abrirModalAdicionar() {
    const modal = document.getElementById('asset-modal');
    const modalTitle = document.getElementById('modal-title');
    
    if (!modal) {
        console.warn('⚠️ Modal não encontrado');
        return;
    }
    
    modalTitle.textContent = 'Adicionar Novo Ativo';
    document.getElementById('asset-form').reset();
    document.getElementById('assetIndex').value = '';
    
    modal.classList.add('show');
}

function fecharModal() {
    const modal = document.getElementById('asset-modal');
    if (modal) {
        modal.classList.remove('show');
    }
}

function editarAtivo(index) {
    const ativo = ativos[index];
    const modal = document.getElementById('asset-modal');
    const modalTitle = document.getElementById('modal-title');
    
    if (!modal || !ativo) {
        return;
    }
    
    modalTitle.textContent = 'Editar Ativo';
    
    // Preencher formulário
    document.getElementById('assetName').value = ativo.nome || '';
    document.getElementById('macAddress').value = ativo.mac_address || '';
    document.getElementById('assetId').value = ativo.ip_address || '';
    document.getElementById('assetStatus').value = ativo.status || 'Online';
    document.getElementById('assetCondition').value = ativo.condicao || 'Disponível';
    document.getElementById('assetIndex').value = index;
    
    modal.classList.add('show');
}

function abrirDeleteModal(index) {
    const ativo = ativos[index];
    const deleteModal = document.getElementById('delete-confirm-modal');
    
    if (!deleteModal || !ativo) {
        return;
    }
    
    document.getElementById('asset-name-to-delete').textContent = ativo.nome;
    document.getElementById('confirm-delete-btn').dataset.index = index;
    
    deleteModal.classList.add('show');
}

// ==================== SALVAR ATIVO ====================

async function salvarAtivo(event) {
    event.preventDefault();
    
    const assetIndex = document.getElementById('assetIndex').value;
    const nome = document.getElementById('assetName').value;
    const macAddress = document.getElementById('macAddress').value;
    const ip = document.getElementById('assetId').value;
    const status = document.getElementById('assetStatus').value;
    const condicao = document.getElementById('assetCondition').value;
    
    // Validação
    if (!nome || !macAddress || !ip) {
        mostrarToast('Preencha todos os campos obrigatórios!', 'warning');
        return;
    }
    
    try {
        // Se é edição
        if (assetIndex !== '') {
            const ativoAtual = ativos[assetIndex];
            const ativoId = ativoAtual.id;
            
            // Enviar PUT para atualizar no banco
            const response = await fetch(`/api/ativos/${ativoId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    nome,
                    mac_address: macAddress,
                    ip_address: ip,
                    status,
                    condicao
                })
            });
            
            if (!response.ok) {
                const erro = await response.json();
                throw new Error(erro.erro || 'Erro ao atualizar ativo');
            }
            
            const resultado = await response.json();
            console.log('✅ Ativo atualizado no banco:', resultado.ativo);
            mostrarToast('Ativo atualizado com sucesso!', 'success');
            
        } else {
            // Se é novo ativo
            const response = await fetch('/api/ativos', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    nome,
                    mac_address: macAddress,
                    ip_address: ip,
                    status,
                    condicao
                })
            });
            
            if (!response.ok) {
                const erro = await response.json();
                throw new Error(erro.erro || 'Erro ao criar ativo');
            }
            
            const resultado = await response.json();
            console.log('✅ Novo ativo criado no banco:', resultado.ativo);
            mostrarToast('Ativo adicionado com sucesso!', 'success');
        }
        
        // Fechar modal
        fecharModal();
        
        // Recarregar ativos do banco
        await carregarAtivosDoBank();
        
        // Sincronizar dashboard
        sincronizarDashboard();
        
    } catch (error) {
        console.error('❌ Erro ao salvar ativo:', error);
        mostrarToast('Erro ao salvar ativo: ' + error.message, 'error');
    }
}

// ==================== DELETAR ATIVO ====================

async function deletarAtivo(index) {
    if (index < 0 || index >= ativos.length) {
        return;
    }
    
    const ativo = ativos[index];
    const ativoId = ativo.id;
    
    try {
        // Enviar DELETE para o banco
        const response = await fetch(`/api/ativos/${ativoId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            const erro = await response.json();
            throw new Error(erro.erro || 'Erro ao deletar ativo');
        }
        
        const resultado = await response.json();
        console.log('✅ Ativo deletado do banco:', resultado);
        mostrarToast('Ativo deletado com sucesso!', 'success');
        
        // Fechar modal de confirmação
        const deleteModal = document.getElementById('delete-confirm-modal');
        if (deleteModal) {
            deleteModal.classList.remove('show');
        }
        
        // Recarregar ativos do banco
        await carregarAtivosDoBank();
        
        // Sincronizar dashboard
        sincronizarDashboard();
        
    } catch (error) {
        console.error('❌ Erro ao deletar ativo:', error);
        mostrarToast('Erro ao deletar ativo: ' + error.message, 'error');
    }
}

// ==================== TOAST (NOTIFICAÇÕES) ====================

function mostrarToast(mensagem, tipo = 'info') {
    const container = document.getElementById('toast-container');
    
    if (!container) {
        console.warn('⚠️ Toast container não encontrado');
        return;
    }
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${tipo}`;
    toast.textContent = mensagem;
    
    container.appendChild(toast);
    
    // Remover após 3 segundos
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// ==================== INICIALIZAÇÃO ====================

/**
 * Sincronizar com o dashboard em tempo real
 * Dispara eventos para atualizar gráficos e estatísticas
 */
function sincronizarDashboard() {
    // Disparar evento customizado para o dashboard escutar
    const evento = new CustomEvent('ativosAtualizados', {
        detail: { ativos: ativos }
    });
    window.dispatchEvent(evento);
    
    console.log('📡 Dashboard sincronizado');
    console.log('📊 Total de ativos:', ativos.length);
    console.log('🟢 Ativos Online:', ativos.filter(a => a.status === 'Online').length);
    console.log('🔴 Ativos Offline:', ativos.filter(a => a.status === 'Offline').length);
}

document.addEventListener('DOMContentLoaded', () => {
    console.log('📋 Inicializando página de inventário...');
    
    // Carregar ativos do banco
    carregarAtivosDoBank();
    
    // Configurar busca
    configurarBusca();
    
    // Botão para adicionar novo ativo
    const addBtn = document.getElementById('add-asset-btn');
    if (addBtn) {
        addBtn.addEventListener('click', abrirModalAdicionar);
    }
    
    // Formulário de ativo
    const assetForm = document.getElementById('asset-form');
    if (assetForm) {
        assetForm.addEventListener('submit', salvarAtivo);
    }
    
    // Botão para cancelar modal
    const cancelBtn = document.getElementById('cancel-btn');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', fecharModal);
    }
    
    // Modal de deletar
    const cancelDeleteBtn = document.getElementById('cancel-delete-btn');
    if (cancelDeleteBtn) {
        cancelDeleteBtn.addEventListener('click', () => {
            const deleteModal = document.getElementById('delete-confirm-modal');
            if (deleteModal) {
                deleteModal.classList.remove('show');
            }
        });
    }
    
    const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', () => {
            const index = confirmDeleteBtn.dataset.index;
            deletarAtivo(parseInt(index));
        });
    }
    
    // Fechar modal ao clicar fora
    const modal = document.getElementById('asset-modal');
    const deleteModal = document.getElementById('delete-confirm-modal');
    
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                fecharModal();
            }
        });
    }
    
    if (deleteModal) {
        deleteModal.addEventListener('click', (e) => {
            if (e.target === deleteModal) {
                deleteModal.classList.remove('show');
            }
        });
    }
    
    // Escutar eventos de atualização do dashboard
    window.addEventListener('ativosAtualizados', (e) => {
        console.log('📡 Evento de sincronização recebido');
    });
    
    console.log('✅ Página de inventário iniciada');
});

// Recarregar ativos a cada 30 segundos
setInterval(() => {
    carregarAtivosDoBank();
    sincronizarDashboard();
}, 30000);
