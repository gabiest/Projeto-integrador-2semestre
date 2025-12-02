/**
 * ARQUIVO: js/assets.js
 * Gerencia a página de "Ativos Online"
 * - Carrega automaticamente a cada 30s (apenas leitura do banco)
 * - Botão "Atualizar" faz scan real de status (Ping)
 */

const API_BASE_URL_ASSETS = 'http://127.0.0.1:5000/api'; 

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Página Ativos Online Iniciada');
    
    // 1. Carrega os dados do banco imediatamente (Rápido)
    carregarAtivosOnline();
    
    // 2. Auto-refresh: Apenas lê o banco a cada 30s (Não pesa a rede)
    setInterval(carregarAtivosOnline, 30000);
    
    // 3. Configura a barra de pesquisa
    configurarBuscaOnline();
});

// --- 1. LEITURA SIMPLES (GET) ---
// Busca os dados do banco de dados e preenche a tabela
async function carregarAtivosOnline() {
    const tableBody = document.getElementById('online-assets-tbody');
    // Se não houver tabela nesta página, para a execução para evitar erros
    if (!tableBody) return;

    try {
        const response = await fetch(`${API_BASE_URL_ASSETS}/ativos-online`);
        const ativos = await response.json();
        
        renderizarTabelaOnline(ativos);
        
    } catch (error) {
        console.error('Erro ao carregar:', error);
        // Em caso de erro silencioso no auto-refresh, não mudamos a tabela para não piscar erro
    }
}

// --- 2. SCAN REAL APENAS DE STATUS (POST) ---
// Esta função deve ser chamada pelo botão "Atualizar" no HTML ativosonline.html
// Ela faz um scan rápido na rede (Ping) para atualizar quem está online/offline
async function atualizarOnlineComScan() {
    const btn = document.getElementById('refresh-btn-online');
    
    // Trava o botão e mostra loading
    if(btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Verificando...';
    }

    // Mostra notificação (se o script global estiver carregado)
    if(window.showToast) window.showToast('Verificando conectividade dos ativos...', 'info');

    try {
        // Chama o Python para escanear APENAS STATUS (Rota segura que não cria/deleta ativos)
        const response = await fetch(`${API_BASE_URL_ASSETS}/scan-status`, { method: 'POST' });
        
        if (!response.ok) throw new Error('Erro no scan');

        // Sucesso! Recarrega a tabela com os novos status do banco
        await carregarAtivosOnline();
        
        // Mostra a notificação verde
        if(window.showToast) window.showToast('Status atualizados com sucesso!', 'success');

    } catch (error) {
        console.error(error);
        if(window.showToast) window.showToast('Erro ao verificar status. Verifique o servidor.', 'error');
    } finally {
        // Destrava o botão e volta ao texto original
        if(btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Atualizar';
        }
    }
}

// --- 3. RENDERIZAÇÃO DA TABELA ---
function renderizarTabelaOnline(ativos) {
    const tableBody = document.getElementById('online-assets-tbody');
    if (!tableBody) return;
    
    tableBody.innerHTML = '';
    
    // Se a lista estiver vazia
    if (!ativos || ativos.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px;">Nenhum ativo online encontrado no momento.</td></tr>';
        return;
    }
    
    ativos.forEach((ativo) => {
        const row = document.createElement('tr');
        
        // Badge de Status
        const statusBadge = `<span class="badge badge-online">${ativo.status}</span>`;
        
        // Badge de Condição
        let condiacaoBadge = `<span class="badge">${ativo.condicao || '-'}</span>`;
        if(ativo.condicao === 'Disponível') condiacaoBadge = '<span class="badge badge-disponivel">Disponível</span>';
        else if(ativo.condicao === 'Manutenção') condiacaoBadge = '<span class="badge badge-manutencao">Manutenção</span>';
        else if(ativo.condicao === 'Alocado') condiacaoBadge = '<span class="badge badge-alocado">Alocado</span>';

        // Ações (Desativadas nesta tela, apenas visual para manter padrão)
        const acoes = `
            <div class="action-icons" style="justify-content: flex-end; display: flex;">
                <i class="bi bi-pencil-square" style="opacity: 0.3; cursor: default;" title="Edição disponível apenas na aba Inventário"></i>
            </div>
        `;

        row.innerHTML = `
            <td class="asset-name"><strong>${ativo.nome || 'N/A'}</strong></td>
            <td class="asset-mac">${ativo.mac_address || 'N/A'}</td>
            <td class="asset-id">${ativo.ip_address || 'N/A'}</td>
            <td class="asset-status">${statusBadge}</td>
            <td class="asset-condition">${condiacaoBadge}</td>
            <td class="asset-actions" style="text-align: right;">${acoes}</td>
        `;
        
        tableBody.appendChild(row);
    });
}

// --- 4. BUSCA (FILTRO LOCAL) ---
function configurarBuscaOnline() {
    const searchInput = document.getElementById('assetSearch');
    if (searchInput) {
        searchInput.addEventListener('keyup', async () => {
            const term = searchInput.value.toLowerCase();
            // Filtra as linhas já renderizadas na tabela para ser instantâneo
            const rows = document.querySelectorAll('#online-assets-tbody tr');
            
            rows.forEach(row => {
                // Pega todo o texto da linha e verifica se contém o termo
                const text = row.innerText.toLowerCase();
                row.style.display = text.includes(term) ? '' : 'none';
            });
        });
    }
}