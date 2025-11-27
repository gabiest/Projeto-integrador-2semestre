/**
 * ARQUIVO: js/charts.js
 * Com animação de contagem nos números!
 */

// --- CONFIGURAÇÕES GLOBAIS ---
Chart.defaults.font.family = 'Arimo';
Chart.defaults.color = '#FFFFFF'; 
Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';

const colors = {
    success: '#2ecc71',  // Verde Esmeralda (Suave)
    danger: '#ff6b6b',   // Vermelho Coral (Não agride o olho)
    warning: '#feca57',  // Amarelo Pastel 
    purple: '#7236c6',   
    purpleLight: '#a788d9',
    textSecondary: 'rgba(255, 255, 255, 0.8)'
};

function createGradient(ctx, colorStart, colorEnd) {
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, colorStart);
    gradient.addColorStop(1, colorEnd);
    return gradient;
}

document.addEventListener('DOMContentLoaded', () => {
    carregarDadosDashboard();
    setInterval(carregarDadosDashboard, 30000);
});

let statusChart = null;
let typeChart = null;

async function carregarDadosDashboard() {
    try {
        const response = await fetch('http://127.0.0.1:5000/api/ativos');
        const ativos = await response.json();

        const total = ativos.length;
        const online = ativos.filter(a => a.status === 'Online').length;
        const offline = ativos.filter(a => a.status === 'Offline').length;
        const manutencao = ativos.filter(a => a.condicao === 'Manutenção').length; 
        
        // Calcula disponibilidade (ex: 16.7)
        const disponibilidadeNum = total > 0 ? ((online / total) * 100) : 0;

        // --- AQUI ENTRA A ANIMAÇÃO DOS NÚMEROS ---
        // Chama a função especial em vez de apenas exibir o texto
        
        animarNumero('online-assets-dash', online, 0);       // Inteiro
        animarNumero('offline-assets-count', offline, 0);    // Inteiro
        animarNumero('availability-value', disponibilidadeNum, 1, '%'); // Com 1 casa decimal e %

        // Atualiza Gráficos
        desenharGraficoStatus(online, offline, manutencao);
        desenharGraficoTipos(ativos);

    } catch (error) {
        console.error("Erro:", error);
    }
}

/**
 * FUNÇÃO MÁGICA DE ANIMAÇÃO DE NÚMEROS
 * @param {string} id - ID do elemento HTML
 * @param {number} valorFinal - O número onde deve parar
 * @param {number} decimais - Quantas casas decimais (0 para inteiros)
 * @param {string} sufixo - Símbolo para colocar no final (ex: "%")
 */
function animarNumero(id, valorFinal, decimais = 0, sufixo = '') {
    const elemento = document.getElementById(id);
    if (!elemento) return;

    const duracao = 1500; // Duração da animação em ms (1.5 segundos)
    const frameDuration = 1000 / 60; // 60 fps
    const totalFrames = Math.round(duracao / frameDuration);
    
    let frameAtual = 0;
    
    const contador = setInterval(() => {
        frameAtual++;
        
        // Função de "Easing" (suavização) para começar rápido e terminar devagar
        const progresso = frameAtual / totalFrames;
        const valorAtual = valorFinal * (1 - Math.pow(1 - progresso, 3)); // Cubic ease-out

        if (frameAtual === totalFrames) {
            clearInterval(contador);
            // Garante que termine exatamente no número certo
            elemento.innerText = valorFinal.toFixed(decimais) + sufixo;
        } else {
            elemento.innerText = valorAtual.toFixed(decimais) + sufixo;
        }
    }, frameDuration);
}

// --- GRÁFICOS (Mantidos iguais) ---

function desenharGraficoStatus(online, offline, manutencao) {
    const ctx = document.getElementById('statusChart');
    if (!ctx) return;

    if (statusChart) statusChart.destroy();

    statusChart = new Chart(ctx, {
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
            animation: {
                animateScale: true, // Anima o crescimento da rosca
                animateRotate: true // Anima a rotação
            },
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#fff',
                        font: { size: 13, weight: 'bold' },
                        padding: 20,
                        usePointStyle: true 
                    }
                }
            }
        }
    });
}

function desenharGraficoTipos(ativos) {
    const ctxCanvas = document.getElementById('assetTypeChart');
    if (!ctxCanvas) return;
    
    // Lógica de contagem (continua igual)
    let pc = 0, impressora = 0, servidor = 0, outros = 0;

    ativos.forEach(a => {
        const nome = (a.nome || '').toLowerCase();
        if (nome.includes('pc') || nome.includes('desk') || nome.includes('note') || nome.includes('windows')) pc++;
        else if (nome.includes('imp') || nome.includes('print') || nome.includes('epson')) impressora++;
        else if (nome.includes('serv') || nome.includes('srv')) servidor++;
        else outros++;
    });

    const ctx = ctxCanvas.getContext('2d');

    // 👇 A MUDANÇA ESTÁ AQUI: Gradiente AZUL específico para este gráfico
    // Azul Claro (#29b6f6) até Azul Escuro (#0277bd)
    const gradientBar = ctx.createLinearGradient(0, 0, 0, 400);
    gradientBar.addColorStop(0, '#29b6f6'); // Azul Ciano (Topo)
    gradientBar.addColorStop(1, '#01579b'); // Azul Profundo (Base)

    if (typeChart) typeChart.destroy();

    typeChart = new Chart(ctxCanvas, {
        type: 'bar',
        data: {
            labels: ['Computadores', 'Impressoras', 'Servidores', 'Outros'],
            datasets: [{
                label: 'Quantidade',
                data: [pc, impressora, servidor, outros],
                backgroundColor: gradientBar, // Usa o azul que criamos acima
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
                    ticks: { color: '#fff', font: { weight: 'bold' } }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#fff', font: { weight: 'bold' } }
                }
            }
        }
    });
}