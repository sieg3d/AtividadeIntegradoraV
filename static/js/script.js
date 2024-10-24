// Função para exibir ou ocultar o campo de período personalizado
function togglePeriodoPersonalizado(value) {
    var periodoPersonalizado = document.getElementById('periodo-personalizado');
    if (value === 'personalizado') {
        periodoPersonalizado.style.display = 'block';
    } else {
        periodoPersonalizado.style.display = 'none';
    }
}

// Função para formatar o CPF no formato xxx.xxx.xxx-xx
function formatCPF(cpf) {
    cpf = cpf.replace(/\D/g, ""); // Remove tudo que não é dígito
    cpf = cpf.replace(/(\d{3})(\d)/, "$1.$2"); // Coloca o primeiro ponto
    cpf = cpf.replace(/(\d{3})(\d)/, "$1.$2"); // Coloca o segundo ponto
    cpf = cpf.replace(/(\d{3})(\d{1,2})$/, "$1-$2"); // Coloca o traço
    return cpf;
}

// Função para validar o formulário de cadastro de projetos
function validarFormulario() {
    var orcamento = document.getElementById('orcamento').value;
    if (orcamento) {
        orcamento = parseFloat(orcamento.replace(',', '.').trim());
        if (isNaN(orcamento)) {
            alert('O orçamento deve ser um número válido.');
            return false;
        } else if (orcamento < 0) {
            alert('O orçamento não pode ser negativo.');
            return false;
        }
    }
    return true;
}

// Evento DOMContentLoaded para garantir que o DOM esteja carregado
document.addEventListener('DOMContentLoaded', function () {
    // Código para formatar o CPF no formulário
    var cpfInput = document.getElementById('cpf');
    if (cpfInput) {
        cpfInput.addEventListener('input', function() {
            this.value = formatCPF(this.value);
        });
    }

    // Código relacionado ao período personalizado
    var periodoDropdown = document.getElementById('periodo');
    if (periodoDropdown) {
        var periodoSelecionado = periodoDropdown.value;
        togglePeriodoPersonalizado(periodoSelecionado);

        periodoDropdown.addEventListener('change', function () {
            togglePeriodoPersonalizado(this.value);
        });
    }

    // Código para controlar o comportamento dos dropdowns no menu de navegação
    var mainMenuItems = document.querySelectorAll('.navbar ul.main-menu > li');
    mainMenuItems.forEach(function (menuItem) {
        menuItem.addEventListener('click', function (event) {
            var dropdownContent = menuItem.querySelector('.dropdown-content');
            if (dropdownContent) {
                event.preventDefault();

                mainMenuItems.forEach(function (item) {
                    var dropdown = item.querySelector('.dropdown-content');
                    if (dropdown && dropdown !== dropdownContent) {
                        dropdown.style.display = 'none';
                    }
                });

                dropdownContent.style.display = (dropdownContent.style.display === 'block') ? 'none' : 'block';
            }
        });
    });

    window.addEventListener('click', function (event) {
        if (!event.target.matches('.main-menu > li > a')) {
            mainMenuItems.forEach(function (menuItem) {
                var dropdown = menuItem.querySelector('.dropdown-content');
                if (dropdown) dropdown.style.display = 'none';
            });
        }
    });

    var dropdownLinks = document.querySelectorAll('.dropdown-content a');
    dropdownLinks.forEach(function (link) {
        link.addEventListener('click', function (event) {
            var targetHref = this.getAttribute('href');
            if (targetHref) {
                window.location.href = targetHref;
            }
        });
    });

    // Código para ordenação da tabela em estoque.html
    let table = document.querySelector(".estoque-table");
    if (table) {
        let headers = table.querySelectorAll("th");

        headers.forEach(function(header, index) {
            header.addEventListener('click', function() {
                sortTableByColumn(table, index, header);
            });
        });

        function sortTableByColumn(table, columnIndex, headerElement) {
            let rows = Array.from(table.querySelectorAll("tbody > tr"));
            let isAscending = headerElement.getAttribute('data-sort-direction') === 'asc';

            let numericColumns = [2, 3];
            let isNumericColumn = numericColumns.includes(columnIndex);

            rows.sort(function(rowA, rowB) {
                let cellA = rowA.querySelectorAll("td")[columnIndex].textContent.trim();
                let cellB = rowB.querySelectorAll("td")[columnIndex].textContent.trim();

                if (isNumericColumn) {
                    cellA = parseFloat(cellA.replace('R$', '').replace(',', '.').trim());
                    cellB = parseFloat(cellB.replace('R$', '').replace(',', '.').trim());

                    return isAscending ? cellA - cellB : cellB - cellA;
                } else {
                    cellA = cellA.toLowerCase();
                    cellB = cellB.toLowerCase();

                    return isAscending ? cellA.localeCompare(cellB) : cellB.localeCompare(cellA);
                }
            });

            let tbody = table.querySelector("tbody");
            tbody.innerHTML = "";
            rows.forEach(function(row) {
                tbody.appendChild(row);
            });

            isAscending = !isAscending;
            headerElement.setAttribute('data-sort-direction', isAscending ? 'asc' : 'desc');

            updateSortArrow(headers, headerElement, isAscending);
        }

        function updateSortArrow(headers, headerElement, isAscending) {
            headers.forEach(function(th) {
                let arrow = th.querySelector(".sort-arrow");
                if (arrow) arrow.textContent = '';
            });

            let arrowElement = headerElement.querySelector(".sort-arrow");
            if (!arrowElement) {
                arrowElement = document.createElement('span');
                arrowElement.classList.add('sort-arrow');
                headerElement.appendChild(arrowElement);
            }

            arrowElement.textContent = isAscending ? '↑' : '↓';
        }
    }

    // Código para o formulário de entrada de itens
    var entradaForm = document.getElementById('entradaForm');
    if (entradaForm) {
        entradaForm.addEventListener('submit', function(event) {
            event.preventDefault();

            const formData = new FormData(this);
            const url = this.getAttribute('data-url');

            fetch(url, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const mensagens = document.getElementById('mensagens');
                    const novaMensagem = document.createElement('li');
                    novaMensagem.classList.add('alert', 'alert-success', 'success');
                    novaMensagem.textContent = `Entrada de ${data.quantidade} unidade(s) de ${data.item} realizada com sucesso!`;
                    mensagens.querySelector('ul').appendChild(novaMensagem);

                    document.getElementById('quantidade').value = '';
                } else {
                    alert('Erro ao registrar entrada: ' + data.error);
                }
            })
            .catch(error => console.error('Erro:', error));
        });
    }

    // Código para o formulário de saída de itens
    var saidaForm = document.getElementById('saidaForm');
    if (saidaForm) {
        saidaForm.addEventListener('submit', function(event) {
            event.preventDefault();

            const formData = new FormData(this);
            const url = this.getAttribute('data-url');

            fetch(url, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const mensagens = document.getElementById('mensagens');
                    const novaMensagem = document.createElement('li');
                    novaMensagem.classList.add('alert', 'alert-success', 'success');
                    novaMensagem.textContent = `Saída de ${data.quantidade} unidade(s) de ${data.item} registrada com sucesso! Justificativa: ${data.justificativa}`;
                    mensagens.querySelector('ul').appendChild(novaMensagem);

                    // Limpar os campos do formulário
                    document.getElementById('quantidade').value = '';
                    document.getElementById('justificativa').value = '';
                } else {
                    alert('Erro ao registrar saída: ' + data.error);
                }
            })
            .catch(error => console.error('Erro:', error));
        });
    }

    // Código para validar o formulário de cadastro de projetos
    var cadastrarProjetoForm = document.getElementById('cadastrarProjetoForm');
    if (cadastrarProjetoForm) {
        cadastrarProjetoForm.addEventListener('submit', function(event) {
            if (!validarFormulario()) {
                event.preventDefault();
            }
        });
    }

    // Código para o "Selecionar Todos" em cestas_personalizadas.html
    var selectAllCheckbox = document.getElementById('select-all');
    if (selectAllCheckbox) {
        var itemCheckboxes = document.querySelectorAll('.item-checkbox');

        selectAllCheckbox.addEventListener('change', function () {
            var isChecked = this.checked;
            itemCheckboxes.forEach(function (checkbox) {
                checkbox.checked = isChecked;
            });
        });

        // Atualiza o estado do "Selecionar Todos" baseado nos checkboxes individuais
        itemCheckboxes.forEach(function (checkbox) {
            checkbox.addEventListener('change', function () {
                if (!this.checked) {
                    selectAllCheckbox.checked = false;
                } else {
                    var allChecked = Array.from(itemCheckboxes).every(function (cb) {
                        return cb.checked;
                    });
                    selectAllCheckbox.checked = allChecked;
                }
            });
        });
    }

    // Código para confirmar a remoção do morador
    var removeButtons = document.querySelectorAll('.btn-remover');

    removeButtons.forEach(function (button) {
        button.addEventListener('click', function () {
            var nomeMorador = this.getAttribute('data-morador-nome');
            var apelidoMorador = this.getAttribute('data-morador-apelido');
            var url = this.getAttribute('data-url');
            var apelidoTexto = apelidoMorador ? ` (${apelidoMorador})` : '';
            var confirmation = confirm(`Tem certeza que deseja remover o registro do morador: ${nomeMorador}${apelidoTexto}?`);

            if (confirmation) {
                // Enviar a requisição POST para remover o morador
                var form = document.createElement('form');
                form.method = 'POST';
                form.action = url;

                // Adiciona o form ao body e submete o formulário para a URL de remoção
                document.body.appendChild(form);
                form.submit();
            }
        });
    });
});


document.addEventListener('DOMContentLoaded', function () {
    var agendarCompromissoForm = document.getElementById('agendarCompromissoForm');
    if (agendarCompromissoForm) {
        agendarCompromissoForm.addEventListener('submit', function (event) {
            var data = document.getElementById('data').value;
            var hora = document.getElementById('hora').value;

            // Lógica simples para impedir agendamentos no passado
            var agora = new Date();
            var dataCompromisso = new Date(`${data}T${hora}`);

            if (dataCompromisso < agora) {
                alert('Não é possível agendar um compromisso no passado.');
                event.preventDefault(); // Cancela o envio do formulário
            }
        });
    }
});

