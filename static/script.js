function atualizarDados() {
    fetch('/api/atualizar-dados')
        .then(response => response.json())
        .then(data => {
            console.log(data);  // Imprime os dados para verificação
            const corpoTabela = document.querySelector('#tabela-distribuicao tbody');
            let html = '';
            // Verifica se dados_tabela existe e é um array antes de chamar forEach
            if (Array.isArray(data.dados_tabela)) {
                data.dados_tabela.forEach(ativo => {
                    const rowClass = ativo['Var (%)'] >= 0 ? 'positive' : 'negative';
                    html += `<tr class="${rowClass}">
                                <th>${ativo['Ativo']}</th>
                                <td>${ativo['Qtde efet'] ? ativo['Qtde efet'].toFixed(5) : 'N/A'}</td>
                                <td>$${ativo['Preço Médio ($)'] ? ativo['Preço Médio ($)'].toFixed(2) : 'N/A'}</td>
                                <td>$${ativo['Preço Atual ($)'] ? ativo['Preço Atual ($)'].toFixed(2) : 'N/A'}</td>
                                <td>R$${ativo['Valor Investido'] ? ativo['Valor Investido'].toFixed(2) : 'N/A'}</td>
                                <td>R$${ativo['Investido Atual (R$)'] ? ativo['Investido Atual (R$)'].toFixed(2) : 'N/A'}</td>
                                <td>R$${ativo['Var (R$)'] ? ativo['Var (R$)'].toFixed(2) : 'N/A'}</td>
                                <td>${ativo['Var (%)'] ? ativo['Var (%)'].toFixed(2) : 'N/A'}%</td>
                                <td>${ativo['% Carteira'] ? ativo['% Carteira'].toFixed(2) : 'N/A'}%</td>
                            </tr>`;
                });
            } else {
                console.error('dados_tabela não está definido ou não é um array');
            }

            corpoTabela.innerHTML = html;

            // Atualizar dados do resumo da carteira
            const valorTotalCarteiraElem = document.getElementById('total-carteira-valor');
            const valorizacaoTotalCarteiraElem = document.getElementById('var-real-valor');
            if (valorTotalCarteiraElem && valorizacaoTotalCarteiraElem) {
                valorTotalCarteiraElem.innerText = `R$ ${data.valor_total_carteira.toFixed(2)}`;
                valorizacaoTotalCarteiraElem.innerText = `R$ ${data.valorizacao_total_carteira.toFixed(2)}`;
            }
        })
        .catch(error => console.error('Erro ao atualizar dados:', error));
}

setInterval(atualizarDados, 5000);  // Atualiza os preços a cada minuto
window.onload = atualizarDados; 