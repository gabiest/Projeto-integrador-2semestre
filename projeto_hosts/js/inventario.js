/**
 * ARQUIVO: js/inventario.js
 * Gerencia a tabela, o scan de rede, os modais e o CRUD.
 */

let listaGlobalAtivos = [];
const API_BASE_URL = 'http://127.0.0.1:5000/api'; 

document.addEventListener('DOMContentLoaded', () => {
    console.log("🚀 Inventário Iniciado");
    
    carregarDadosInventario(); 
    configurarBusca();
    
    // AUTO-REFRESH (30s): APENAS LÊ O BANCO (GET)
    // Não faz scan na rede aqui para não pesar e não duplicar lógica.
    setInterval(carregarDadosInventario, 30000);
});

// --- 1. LEITURA (GET) ---
async function carregarDadosInventario() {
    const tbody = document.getElementById('inventory-table-body');
    if(!tbody) return;

    try {
        const response = await fetch(`${API_BASE_URL}/ativos`);
        const data = await response.json();
        listaGlobalAtivos = data;
        preencherTabela(data);
    } catch (error) {
        console.error("Erro leitura:", error);
    }
}

// --- 2. SCAN REAL (POST) - APENAS NO BOTÃO ---
// Adiciona novos ativos e atualiza existentes. NÃO deleta o banco.
window.atualizarComScan = async function() {
    const btn = document.getElementById('refresh-btn');
    
    if(btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Buscando Novos Ativos...';
    }
    
    if(window.showToast) window.showToast('Varrendo a rede por novos dispositivos...', 'info');

    try {
        // Chama o scan completo do Python
        const responseScan = await fetch(`${API_BASE_URL}/scan-rede`, { method: 'POST' });

        if (!responseScan.ok) throw new Error('Erro no scan');

        // Recarrega a tabela com as novidades
        await carregarDadosInventario(); 
        
        if(window.showToast) window.showToast('Inventário atualizado com sucesso!', 'success');

    } catch (error) {
        console.error(error);
        if(window.showToast) window.showToast('Erro ao escanear.', 'error');
    } finally {
        if(btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Atualizar';
        }
    }
}

// --- 3. TABELA ---
function preencherTabela(dados) {
    const tbody = document.getElementById('inventory-table-body');
    if(!tbody) return;
    tbody.innerHTML = ''; 

    if (!dados.length) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:20px;">Nenhum ativo encontrado.</td></tr>';
        return;
    }

    dados.forEach(ativo => {
        const tr = document.createElement('tr');
        const statusBadge = ativo.status === 'Online' 
            ? `<span class="badge badge-online">Online</span>` 
            : `<span class="badge badge-offline">Offline</span>`;

        const acoesHTML = `
            <div class="action-icons">
                <i class="bi bi-pencil-square" onclick="prepararEdicao(${ativo.id})" title="Editar"></i>
                <i class="bi bi-trash" onclick="prepararExclusao(${ativo.id}, '${ativo.nome}')" title="Excluir"></i>
            </div>
        `;

        tr.innerHTML = `
            <td><strong>${ativo.nome || 'Sem Nome'}</strong></td>
            <td>${ativo.mac_address || '-'}</td>
            <td>${ativo.ip_address || '-'}</td>
            <td>${statusBadge}</td>
            <td>${ativo.condicao || '-'}</td>
            <td>${acoesHTML}</td>
        `;
        tbody.appendChild(tr);
    });
}

// --- 4. MODAIS E CRUD (GLOBAL) ---

function configurarBusca() {
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const termo = e.target.value.toLowerCase();
            const filtrados = listaGlobalAtivos.filter(a => 
                (a.nome && a.nome.toLowerCase().includes(termo)) ||
                (a.ip_address && a.ip_address.includes(termo)) ||
                (a.mac_address && a.mac_address.toLowerCase().includes(termo))
            );
            preencherTabela(filtrados);
        });
    }
}

window.abrirModalAdicionar = function() {
    const m = document.getElementById('asset-modal');
    if(m) {
        document.getElementById('modal-title').innerText = "Adicionar Novo Ativo";
        document.getElementById('assetIdDatabase').value = ""; // ID Vazio = Novo
        document.getElementById('asset-form').reset();
        m.style.display = 'flex';
    }
}

window.prepararEdicao = function(id) {
    const ativo = listaGlobalAtivos.find(a => a.id === id);
    if (!ativo) return;
    
    const m = document.getElementById('asset-modal');
    document.getElementById('modal-title').innerText = "Editar Ativo";
    
    // Preenche o ID para que o salvamento saiba que é edição
    document.getElementById('assetIdDatabase').value = ativo.id;
    
    document.getElementById('assetName').value = ativo.nome;
    document.getElementById('macAddress').value = ativo.mac_address;
    document.getElementById('assetId').value = ativo.ip_address;
    document.getElementById('assetStatus').value = ativo.status;
    
    if(document.getElementById('assetCondition')) document.getElementById('assetCondition').value = ativo.condicao;
    if(document.getElementById('assetType')) document.getElementById('assetType').value = ativo.tipo || 'Outros';
    
    m.style.display = 'flex';
}

window.prepararExclusao = function(id, nome) {
    const m = document.getElementById('delete-confirm-modal');
    document.getElementById('asset-name-to-delete').innerText = nome;
    document.getElementById('delete-id-target').value = id;
    m.style.display = 'flex';
}

window.fecharModais = function() {
    document.querySelectorAll('.modal-overlay').forEach(m => m.style.display = 'none');
}

// SALVAR (Novo ou Edição)
window.salvarAtivo = async function(event) {
    event.preventDefault(); 
    
    // Pega o ID do campo oculto correto
    const id = document.getElementById('assetIdDatabase').value;
    
    const dados = {
        nome: document.getElementById('assetName').value,
        mac_address: document.getElementById('macAddress').value,
        ip_address: document.getElementById('assetId').value,
        status: document.getElementById('assetStatus').value,
        condicao: document.getElementById('assetCondition') ? document.getElementById('assetCondition').value : 'Disponível'
    };
    if(document.getElementById('assetType')) dados.tipo = document.getElementById('assetType').value;

    // Se tem ID, é PUT (Atualizar). Se não, é POST (Criar).
    const metodo = id ? 'PUT' : 'POST';
    const url = id ? `${API_BASE_URL}/ativos/${id}` : `${API_BASE_URL}/ativos`;

    try {
        const response = await fetch(url, {
            method: metodo,
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(dados)
        });

        if (!response.ok) throw new Error('Falha ao salvar');

        fecharModais();
        carregarDadosInventario();
        if(window.showToast) window.showToast(id ? 'Ativo atualizado!' : 'Ativo criado!', 'success');
    } catch (e) { 
        console.error(e);
        if(window.showToast) window.showToast('Erro ao salvar.', 'error');
    }
}

// EXCLUIR
window.confirmarExclusao = async function() {
    const id = document.getElementById('delete-id-target').value;
    try {
        await fetch(`${API_BASE_URL}/ativos/${id}`, { method: 'DELETE' });
        fecharModais();
        carregarDadosInventario();
        if(window.showToast) window.showToast('Excluído!', 'success');
    } catch (e) { console.error(e); }
}

// ZERAR BANCO
window.abrirModalReset = function() {
    const m = document.getElementById('reset-confirm-modal');
    if(m) m.style.display = 'flex';
}

window.confirmarResetBanco = async function() {
    const btn = document.querySelector('#reset-confirm-modal .btn-confirm-delete');
    if(btn) { btn.innerText = "Apagando..."; btn.disabled = true; }
    try {
        await fetch(`${API_BASE_URL}/ativos/reset`, { method: 'DELETE' });
        if(window.showToast) window.showToast('Banco zerado!', 'success');
        fecharModais();
        carregarDadosInventario(); 
    } catch (e) { console.error(e); }
    finally {
        if(btn) { btn.innerText = "APAGAR TUDO"; btn.disabled = false; }
    }
}