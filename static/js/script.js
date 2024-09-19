// Função para exibir ou ocultar o campo de período personalizado
function togglePeriodoPersonalizado(value) {
    var periodoPersonalizado = document.getElementById('periodo-personalizado'); // Seleciona o elemento do período personalizado
    if (value === 'personalizado') {
        periodoPersonalizado.style.display = 'block'; // Exibe o campo se a opção 'personalizado' for selecionada
    } else {
        periodoPersonalizado.style.display = 'none'; // Oculta o campo caso contrário
    }
}

// Inicializa o estado do filtro personalizado baseado na seleção quando a página é carregada
document.addEventListener('DOMContentLoaded', function () {
    var periodoDropdown = document.getElementById('periodo'); // Seleciona o dropdown de período
    if (periodoDropdown) {
        var periodoSelecionado = periodoDropdown.value; // Obtém o valor selecionado no dropdown
        togglePeriodoPersonalizado(periodoSelecionado); // Chama a função para exibir/ocultar o período personalizado

        // Atualiza a exibição sempre que a seleção do dropdown mudar
        periodoDropdown.addEventListener('change', function () {
            togglePeriodoPersonalizado(this.value); // Chama a função ao alterar a seleção
        });
    }
});

//------------------------------------------------------------------------------------------------------------------------------------------

// Código para controlar o comportamento dos dropdowns no menu de navegação
document.addEventListener('DOMContentLoaded', function () {
    var mainMenuItems = document.querySelectorAll('.navbar ul.main-menu > li'); // Seleciona todos os itens do menu principal

    mainMenuItems.forEach(function (menuItem) {
        menuItem.addEventListener('click', function (event) {
            var dropdownContent = menuItem.querySelector('.dropdown-content'); // Seleciona o conteúdo do dropdown

            // Se o menu clicado tiver um dropdown, alterna a visibilidade dele
            if (dropdownContent) {
                event.preventDefault(); // Impede a navegação para itens que têm dropdown

                // Fecha outros dropdowns abertos
                mainMenuItems.forEach(function (item) {
                    var dropdown = item.querySelector('.dropdown-content');
                    if (dropdown && dropdown !== dropdownContent) {
                        dropdown.style.display = 'none'; // Fecha dropdowns que não foram clicados
                    }
                });

                // Alterna a exibição do dropdown clicado
                dropdownContent.style.display = (dropdownContent.style.display === 'block') ? 'none' : 'block';
            }
        });
    });

    // Fecha dropdowns ao clicar fora deles
    window.addEventListener('click', function (event) {
        if (!event.target.matches('.main-menu > li > a')) { // Verifica se o clique foi fora dos links do menu principal
            mainMenuItems.forEach(function (menuItem) {
                var dropdown = menuItem.querySelector('.dropdown-content');
                if (dropdown) dropdown.style.display = 'none'; // Fecha o dropdown se clicado fora
            });
        }
    });

    // Permite que os links dentro do dropdown sejam clicados normalmente
    var dropdownLinks = document.querySelectorAll('.dropdown-content a'); // Seleciona os links dentro dos dropdowns

    dropdownLinks.forEach(function (link) {
        link.addEventListener('click', function (event) {
            // Deixa os links do dropdown funcionar normalmente
            var targetHref = this.getAttribute('href');
            if (targetHref) {
                window.location.href = targetHref; // Redireciona para o link clicado
            }
        });
    });
});


document.addEventListener('DOMContentLoaded', function () {
    let table = document.querySelector(".estoque-table");
    let headers = table.querySelectorAll("th");
    
    headers.forEach(function(header, index) {
        header.addEventListener('click', function() {
            sortTableByColumn(table, index, header);
        });
    });

    function sortTableByColumn(table, columnIndex, headerElement) {
        let rows = Array.from(table.querySelectorAll("tbody > tr"));
        let isAscending = table.getAttribute('data-sort-direction') === 'asc';
        
        // Verifica se a coluna é numérica (neste caso, "Quantidade" é a coluna 2)
        let isNumericColumn = columnIndex === 2;
        
        // Realizar a ordenação
        rows.sort(function(rowA, rowB) {
            let cellA = rowA.querySelectorAll("td")[columnIndex].textContent.trim();
            let cellB = rowB.querySelectorAll("td")[columnIndex].textContent.trim();

            if (isNumericColumn) {
                // Ordenar numericamente
                return isAscending ? cellA - cellB : cellB - cellA;
            } else {
                // Ordenar como texto (alfabética)
                return isAscending ? cellA.localeCompare(cellB) : cellB.localeCompare(cellA);
            }
        });
        
        // Remover todas as linhas do tbody e reinserir as ordenadas
        table.querySelector("tbody").innerHTML = "";
        rows.forEach(function(row) {
            table.querySelector("tbody").appendChild(row);
        });

        // Alternar a direção de ordenação
        table.setAttribute('data-sort-direction', isAscending ? 'desc' : 'asc');
        
        // Atualizar a seta no cabeçalho
        updateSortArrow(headers, headerElement, isAscending);
    }

    function updateSortArrow(headers, headerElement, isAscending) {
        // Remove as setas de todos os cabeçalhos
        headers.forEach(function(th) {
            let arrow = th.querySelector(".sort-arrow");
            if (arrow) arrow.textContent = '';  // Limpa a seta
        });
        
        // Adiciona a seta de acordo com a direção de ordenação no cabeçalho atual
        let arrowElement = headerElement.querySelector(".sort-arrow");
        if (!arrowElement) {
            // Se o span da seta não existir, cria um
            arrowElement = document.createElement('span');
            arrowElement.classList.add('sort-arrow');
            headerElement.appendChild(arrowElement);
        }

        // Define a seta dependendo da direção de ordenação
        arrowElement.textContent = isAscending ? '↓' : '↑';  // Seta descendente ou ascendente
    }
});
