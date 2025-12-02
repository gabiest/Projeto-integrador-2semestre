// --- CONFIGURAÇÕES GLOBAIS ---
Chart.defaults.font.family = 'Arimo';
Chart.defaults.color = '#FFFFFF'; 
Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';

// --- CORES ---
const colors = {
    success: '#2ecc71', 
    danger: '#ff6b6b',   
    warning: '#feca57', 
};

// --- INICIALIZAÇÃO ---
document.addEventListener('DOMContentLoaded', () => {
    console.log("📊 CARREGANDO GRÁFICOS - FORÇANDO CATEGORIAS..."); 
    carregarDadosDashboard();
    setInterval(carregarDadosDashboard, 30000);
});

async function carregarDadosDashboard() {
    try {
        const response = await fetch('http://127.0.0.1:5000/api/ativos');
        const ativos = await response.json();

        // KPIs
        const total = ativos.length;
        const online = ativos.filter(a => a.status === 'Online').length;
        const offline = ativos.filter(a => a.status === 'Offline').length;
        const manutencao = ativos.filter(a => a.condicao === 'Manutenção').length; 
        const disponibilidade = total > 0 ? ((online / total) * 100) : 0;

        animarNumero('online-assets-dash', online, 0);       
        animarNumero('offline-assets-count', offline, 0);    
        animarNumero('availability-value', disponibilidade, 1, '%');

        desenharGraficoStatus(online, offline, manutencao);
        
        // AQUI ESTÁ O SEGREDO: Passamos a lista bruta para ser filtrada na hora
        desenharGraficoTipos(ativos);

    } catch (error) {
        console.error("Erro dashboard:", error);
    }
}

function animarNumero(id, valorFinal, decimais = 0, sufixo = '') {
    const elemento = document.getElementById(id);
    if (!elemento) return;
    elemento.innerText = valorFinal.toFixed(decimais) + sufixo;
}

// --- GRÁFICO 1: STATUS (ROSCA) ---
function desenharGraficoStatus(online, offline, manutencao) {
    const ctxCanvas = document.getElementById('statusChart');
    if (!ctxCanvas) return;

    const existingChart = Chart.getChart(ctxCanvas);
    if (existingChart) existingChart.destroy();

    new Chart(ctxCanvas, {
        type: 'doughnut',
        data: {
            labels: ['Online', 'Offline', 'Manutenção'],
            datasets: [{
                data: [online, offline, manutencao],
                backgroundColor: [colors.success, colors.danger, colors.warning],
                borderColor: 'var(--bg-card)', 
                borderWidth: 0,
                hoverOffset: 8 
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '65%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#fff', font: { size: 13 }, padding: 20, usePointStyle: true }
                }
            }
        }
    });
}

// --- GRÁFICO 2: TIPOS (CATEGORIAS FORÇADAS) ---
function desenharGraficoTipos(ativos) {
    const ctxCanvas = document.getElementById('assetTypeChart');
    if (!ctxCanvas) return;
    
    const existingChart = Chart.getChart(ctxCanvas);
    if (existingChart) existingChart.destroy();
    
    // Zera contadores
    let smartphones = 0;
    let notebooks = 0;
    let computadores = 0;
    let outros = 0;

    // CLASSIFICAÇÃO MANUAL NO JAVASCRIPT
    ativos.forEach(a => {
        // Pega tudo que temos sobre o ativo e joga para minúsculo
        const texto = (a.nome + " " + (a.tipo || "")).toLowerCase();

        // 1. SMARTPHONES
        if (texto.match(/mobile|celular|iphone|android|galaxy|samsung|xiaomi|motorola|redmi|a54|s2[0-9]|pixel/)) {
            smartphones++;
        } 
        // 2. NOTEBOOKS
        else if (texto.match(/notebook|laptop|macbook|thinkpad|latitude|inspiron|ideapad|zenbook|vivobook/)) {
            notebooks++;
        }
        // 3. COMPUTADORES (Desktops)
        else if (texto.match(/computador|pc|desktop|windows|linux|mac|optiplex|vostro|torre|all-in-one|cas/)) {
            computadores++;
        }
        // 4. OUTROS
        else {
            outros++;
        }
    });

    const ctx = ctxCanvas.getContext('2d');
    // Gradiente Azul Simples e Garantido
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, '#29B6F6'); 
    gradient.addColorStop(1, '#01579B');

    new Chart(ctxCanvas, {
        type: 'bar',
        data: {
            // Rótulos FIXOS: Isso garante que eles apareçam mesmo se for 0
            labels: ['Smartphones', 'Notebooks', 'Computadores', 'Outros'],
            datasets: [{
                label: 'Quantidade',
                data: [smartphones, notebooks, computadores, outros],
                backgroundColor: gradient,
                borderRadius: 6,
                barPercentage: 0.6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                    ticks: { color: '#fff', stepSize: 1 }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#fff', font: { size: 11 } }
                }
            }
        }
    });
}