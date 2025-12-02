/**
 * Script spara carregar dados do banco de dados SQLite
 * Puxar ativos, estatísticas e popular tabelas/gráficos
 * ⚠️ IMPORTANTE: Tudo é sincronizado com o banco SQLite
 */

// ==================== CARREGAR ATIVOS ====================

async function carregarAtivos() {
    try {
        const response = await fetch('/api/ativos');
        const ativos = await response.json();
        
        console.log('✅ Ativos carregados do banco:', ativos);
        
        // Atualizar tabela
        atualizarTabela(ativos);
        
        // Atualizar gráficos
        atualizarGraficos(ativos);
        
        // Atualizar estatísticas também
        calcularEstatisticas(ativos);
        
    } catch (error) {
        console.error('❌ Erro ao carregar ativos:', error);
    }
}

async function carregarAtivosOnline() {
    try {
        const response = await fetch('/api/ativos-online');
        const ativos = await response.json();
        
        console.log('✅ Ativos online carregados:', ativos);
        atualizarTabela(ativos);
        calcularEstatisticas(ativos);
        
    } catch (error) {
        console.error('❌ Erro ao carregar ativos online:', error);
    }
}

async function carregarEstatisticas() {
    try {
        const response = await fetch('/api/estatisticas');
        const stats = await response.json();
        
        console.log('✅ Estatísticas carregadas:', stats);
        
        // Atualizar cards com dados EXATOS do banco
        atualizarCards(stats);
        
    } catch (error) {
        console.error('❌ Erro ao carregar estatísticas:', error);
    }
}

function atualizarCards(stats) {
    // Atualiza os cards de estatísticas com dados do banco
    const elementos = {
        'total-ativos': stats.total_ativos,
        'ativos-online': stats.ativos_online,
        'ativos-offline': stats.ativos_offline,
        'total-usuarios': stats.total_usuarios
    };
    
    for (const [id, valor] of Object.entries(elementos)) {
        const elem = document.getElementById(id);
        if (elem) {
            elem.textContent = valor || 0;
        }
    }
}

function calcularEstatisticas(ativos) {
    // Calcula estatísticas REAIS dos ativos
    if (!ativos || ativos.length === 0) {
        return;
    }
    
    let online = 0;
    let offline = 0;
    
    ativos.forEach(ativo => {
        if (ativo.status && ativo.status.toLowerCase() === 'online') {
            online++;
        } else if (ativo.status && ativo.status.toLowerCase() === 'offline') {
            offline++;
        }
    });
    
    // Atualizar cards
    const totalAtivos = document.getElementById('total-ativos');
    const ativosOnline = document.getElementById('ativos-online');
    const ativosOffline = document.getElementById('ativos-offline');
    
    if (totalAtivos) totalAtivos.textContent = ativos.length;
    if (ativosOnline) ativosOnline.textContent = online;
    if (ativosOffline) ativosOffline.textContent = offline;
}

// ==================== ATUALIZAR TABELA ====================

function atualizarTabela(ativos) {
    const tbody = document.querySelector('table tbody');
    
    if (!tbody) {
        console.warn('Tabela não encontrada');
        return;
    }
    
    // Limpar conteúdo
    tbody.innerHTML = '';
    
    if (ativos.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center">Nenhum ativo encontrado</td></tr>';
        return;
    }
    
    // Adicionar linhas
    ativos.forEach(ativo => {
        const tr = document.createElement('tr');
        
        // Definir cores baseado no status
        const statusBadge = ativo.status === 'Online' 
            ? '<span class="badge badge-success">Online</span>'
            : '<span class="badge badge-danger">Offline</span>';
        
        tr.innerHTML = `
            <td>${ativo.id || '-'}</td>
            <td>${ativo.nome || '-'}</td>
            <td>${ativo.ip_address || '-'}</td>
            <td>${ativo.mac_address || '-'}</td>
            <td>${statusBadge}</td>
            <td>${ativo.condicao || '-'}</td>
            <td>${ativo.data_inicio ? formatarData(ativo.data_inicio) : '-'}</td>
        `;
        
        tbody.appendChild(tr);
    });
}

// ==================== ATUALIZAR GRÁFICOS ====================

function atualizarGraficos(ativos) {
    // Contar status
    let online = 0;
    let offline = 0;
    
    ativos.forEach(ativo => {
        if (ativo.status === 'Online') {
            online++;
        } else {
            offline++;
        }
    });
    
    // Atualizar gráfico de pizza (se existir)
    const pieCtx = document.getElementById('statusPie');
    if (pieCtx) {
        criarGraficoPizza(online, offline);
    }
    
    // Atualizar gráfico de barras (se existir)
    const barCtx = document.getElementById('statusBar');
    if (barCtx) {
        criarGraficoBarras(ativos);
    }
}

function criarGraficoPizza(online, offline) {
    const ctx = document.getElementById('statusPie');
    
    if (!ctx) return;
    
    // Destruir gráfico anterior
    if (window.chartPizza) {
        window.chartPizza.destroy();
    }
    
    // Criar novo gráfico
    window.chartPizza = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Online', 'Offline'],
            datasets: [{
                data: [online, offline],
                backgroundColor: [
                    '#28a745',
                    '#dc3545'
                ],
                borderColor: ['#fff', '#fff'],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

function criarGraficoBarras(ativos) {
    const ctx = document.getElementById('statusBar');
    
    if (!ctx) return;
    
    // Contar por tipo/IP (exemplo simples)
    const nomes = ativos.slice(0, 5).map(a => a.nome);
    const online = ativos.slice(0, 5).map(a => a.status === 'Online' ? 1 : 0);
    
    // Destruir gráfico anterior
    if (window.chartBar) {
        window.chartBar.destroy();
    }
    
    // Criar novo gráfico
    window.chartBar = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: nomes,
            datasets: [{
                label: 'Status',
                data: online,
                backgroundColor: online.map(v => v === 1 ? '#28a745' : '#dc3545'),
                borderRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 1
                }
            }
        }
    });
}

// ==================== FUNÇÕES AUXILIARES ====================

function formatarData(dataStr) {
    if (!dataStr) return '-';
    
    try {
        const data = new Date(dataStr);
        return data.toLocaleDateString('pt-BR') + ' ' + data.toLocaleTimeString('pt-BR');
    } catch {
        return dataStr;
    }
}

// ==================== INICIALIZAÇÃO ====================

document.addEventListener('DOMContentLoaded', function() {
    console.log('Página carregada, carregando dados do banco...');
    
    // Carregar dados conforme a página
    const page = window.location.pathname;
    
    // Estatísticas sempre
    carregarEstatisticas();
    
    // Ativos conforme página
    if (page.includes('ativosnarede')) {
        carregarAtivos();
    } else if (page.includes('ativosonline')) {
        carregarAtivosOnline();
    } else if (page.includes('dashboard') || page.includes('home')) {
        carregarAtivos();
        carregarEstatisticas();
    }
    
    // Atualizar a cada 30 segundos
    setInterval(() => {
        carregarEstatisticas();
        if (page.includes('ativosnarede') || page.includes('dashboard') || page.includes('home')) {
            carregarAtivos();
        }
    }, 30000);
});

console.log('✅ Script de dados carregado e pronto!');
