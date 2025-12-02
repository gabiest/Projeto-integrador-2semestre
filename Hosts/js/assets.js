const botaoMenu = document.querySelector('.botao-menu');
const menuLateral = document.querySelector('.menu-lateral');
const conteudo = document.querySelector('.conteudo');
const background = document.querySelector('.background');

// Adiciona um evento de clique para o botão do menu
botaoMenu.addEventListener('click', () => {
    // Alterna a classe 'ativo' em todos os elementos
    menuLateral.classList.toggle('ativo');
    botaoMenu.classList.toggle('ativo');
    conteudo.classList.toggle('ativo');
    background.classList.toggle('ativo');
});

// Adiciona um evento de clique para o fundo de sobreposição
background.addEventListener('click', () => {
    // Remove a classe 'ativo' de todos os elementos para fechar o menu
    menuLateral.classList.remove('ativo');
    botaoMenu.classList.remove('ativo');
    conteudo.classList.remove('ativo');
    background.classList.remove('ativo');
});

// Preenche a tabela com os dados dos ativos
Assets.forEach(asset => {
    const tr = document.createElement('tr');
    const trContent = `
        <td>${asset.assetName}</td>
        <td>${asset.assetNumber}</td>
        <td>${asset.status}</td>
        <td class="${asset.condition === 'Crítico' ? 'danger' : asset.condition === 'Alerta' ? 'warning' : 'success'}">${asset.condition}</td>
        <td class="primary">Detalhes</td>
    `;
    tr.innerHTML = trContent;
    document.querySelector('table tbody').appendChild(tr);
});