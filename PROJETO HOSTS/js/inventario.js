/**
 * ARQUIVO: js/inventario.js
 */

let listaGlobalAtivos = [];
const API_BASE = 'http://127.0.0.1:5000/api/ativos'; 

document.addEventListener('DOMContentLoaded', () => {
    console.log("🚀 Inventário Iniciado");
    carregarDadosInventario();
    configurarBusca();
    
    // Auto-refresh
    setInterval(carregarDadosInventario, 30000);
});

// --- READ (Carregar) ---
function carregarDadosInventario() {
    const tbody = document.getElementById('inventory-table-body');
    const btn = document.getElementById('refresh-btn');
    if(!tbody) return;

    if(btn) btn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> ...';

    fetch(API_BASE)
        .then(r => r.json())
        .then(data => {
            listaGlobalAtivos = data;
            preencherTabela(data);
        })
        .catch(console.error)
        .finally(() => {
            if(btn) btn.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Atualizar';
        });
}

// --- TABELA ---
function preencherTabela(dados) {
    const tbody = document.getElementById('inventory-table-body');
    if(!tbody) return;
    tbody.innerHTML = ''; 

    if (!dados.length) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:20px;">Nenhum ativo.</td></tr>';
        return;
    }

    dados.forEach(ativo => {
        const tr = document.createElement('tr');
        const statusBadge = ativo.status === 'Online' 
            ? `<span class="badge badge-online">Online</span>` 
            : `<span class="badge badge-offline">Offline</span>`;

        // HTML dos ícones
        const acoesHTML = `
            <div class="action-icons">
                <i class="bi bi-pencil-square" onclick="prepararEdicao(${ativo.id})" title="Editar"></i>
                <i class="bi bi-trash" onclick="prepararExclusao(${ativo.id}, '${ativo.nome}')" title="Excluir"></i>
            </div>
        `;

        tr.innerHTML = `
            <td><strong>${ativo.nome || 'N/A'}</strong></td>
            <td>${ativo.mac_address || '-'}</td>
            <td>${ativo.ip_address || '-'}</td>
            <td>${statusBadge}</td>
            <td>${ativo.condicao || '-'}</td>
            <td>${acoesHTML}</td>
        `;
        tbody.appendChild(tr);
    });
}

// --- BUSCA ---
function configurarBusca() {
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const termo = e.target.value.toLowerCase();
            const filtrados = listaGlobalAtivos.filter(a => 
                (a.nome && a.nome.toLowerCase().includes(termo)) ||
                (a.ip_address && a.ip_address.includes(termo))
            );
            preencherTabela(filtrados);
        });
    }
}

// --- FUNÇÕES GLOBAIS (Para o HTML acessar) ---

window.abrirModalAdicionar = function() {
    const modal = document.getElementById('asset-modal');
    document.getElementById('modal-title').innerText = "Adicionar Novo Ativo";
    document.getElementById('assetIdDatabase').value = ""; 
    document.getElementById('asset-form').reset();
    modal.style.display = 'flex';
    setTimeout(() => modal.style.opacity = '1', 10);
}

window.prepararEdicao = function(id) {
    const ativo = listaGlobalAtivos.find(a => a.id === id);
    if (!ativo) return;

    const modal = document.getElementById('asset-modal');
    document.getElementById('modal-title').innerText = "Editar Ativo";
    document.getElementById('assetIdDatabase').value = ativo.id;
    
    document.getElementById('assetName').value = ativo.nome;
    document.getElementById('macAddress').value = ativo.mac_address;
    document.getElementById('assetId').value = ativo.ip_address;
    document.getElementById('assetStatus').value = ativo.status;

    modal.style.display = 'flex';
    setTimeout(() => modal.style.opacity = '1', 10);
}

window.prepararExclusao = function(id, nome) {
    const modal = document.getElementById('delete-confirm-modal');
    document.getElementById('asset-name-to-delete').innerText = nome;
    document.getElementById('delete-id-target').value = id;
    modal.style.display = 'flex';
    setTimeout(() => modal.style.opacity = '1', 10);
}

window.fecharModais = function() {
    document.querySelectorAll('.modal-overlay').forEach(m => {
        m.style.opacity = '0';
        setTimeout(() => m.style.display = 'none', 300);
    });
}

window.salvarAtivo = function(event) {
    event.preventDefault(); 
    const id = document.getElementById('assetIdDatabase').value;
    const dados = {
        nome: document.getElementById('assetName').value,
        mac_address: document.getElementById('macAddress').value,
        ip_address: document.getElementById('assetId').value,
        status: document.getElementById('assetStatus').value,
        condicao: 'Disponível'
    };

    const metodo = id ? 'PUT' : 'POST';
    const url = id ? `${API_BASE}/${id}` : API_BASE;

    fetch(url, {
        method: metodo,
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(dados)
    }).then(() => {
        fecharModais();
        carregarDadosInventario();
        if(window.showToast) window.showToast('Salvo com sucesso!', 'success');
    });
}

window.confirmarExclusao = function() {
    const id = document.getElementById('delete-id-target').value;
    fetch(`${API_BASE}/${id}`, { method: 'DELETE' })
    .then(() => {
        fecharModais();
        carregarDadosInventario();
        if(window.showToast) window.showToast('Excluído!', 'success');
    });
}