// Função para deletar usuário
async function deleteUser(userId) {
    if (confirm('Tem certeza que deseja excluir este usuário?')) {
        try {
            const response = await fetch(`/api/users/${userId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const row = document.querySelector(`input[value="${userId}"]`).closest('tr');
                row.remove();
                updateDeleteButton();
            } else {
                const error = await response.json();
                alert(error.detail || 'Erro ao excluir usuário');
            }
        } catch (error) {
            console.error('Erro:', error);
            alert('Erro ao excluir usuário');
        }
    }
}

// Função para deletar múltiplos usuários
async function deleteSelected() {
    const selectedUsers = Array.from(document.querySelectorAll('.user-checkbox:checked')).map(cb => cb.value);
    
    if (selectedUsers.length === 0) {
        alert('Selecione pelo menos um usuário para excluir');
        return;
    }

    if (confirm(`Tem certeza que deseja excluir ${selectedUsers.length} usuário(s)?`)) {
        try {
            let hasError = false;
            for (const userId of selectedUsers) {
                const response = await fetch(`/api/users/${userId}`, {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                if (response.ok) {
                    const row = document.querySelector(`input[value="${userId}"]`).closest('tr');
                    row.remove();
                } else {
                    hasError = true;
                    const error = await response.json();
                    console.error(`Erro ao excluir usuário ${userId}:`, error);
                }
            }

            if (hasError) {
                alert('Alguns usuários não puderam ser excluídos. Verifique o console para mais detalhes.');
            }

            // Atualiza o estado do botão de exclusão
            updateDeleteButton();
            
            // Desmarca o checkbox "Selecionar Todos" se estiver marcado
            const selectAllCheckbox = document.getElementById('selectAll');
            if (selectAllCheckbox.checked) {
                selectAllCheckbox.checked = false;
            }
        } catch (error) {
            console.error('Erro:', error);
            alert('Erro ao excluir usuários');
        }
    }
}

// Função para editar usuário
async function editUser(userId) {
    try {
        const response = await fetch(`/api/users/${userId}`);
        const user = await response.json();

        document.getElementById('editUserId').value = user.id;
        document.getElementById('editNome').value = user.nome;
        document.getElementById('editEmail').value = user.email;
        document.getElementById('editCpf').value = user.cpf;
        
        // Converter a data para o formato YYYY-MM-DD
        const data = new Date(user.data_nascimento);
        const dataFormatada = data.toISOString().split('T')[0];
        document.getElementById('editDataNascimento').value = dataFormatada;

        const modal = new bootstrap.Modal(document.getElementById('editModal'));
        modal.show();
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao carregar dados do usuário');
    }
}

// Função para salvar edição
async function saveEdit() {
    const userId = document.getElementById('editUserId').value;
    const form = document.getElementById('editForm');
    
    if (!form.checkValidity()) {
        form.classList.add('was-validated');
        return;
    }

    const formData = new FormData();
    formData.append('nome', document.getElementById('editNome').value);
    formData.append('email', document.getElementById('editEmail').value);
    formData.append('cpf', document.getElementById('editCpf').value);
    formData.append('data_nascimento', document.getElementById('editDataNascimento').value);

    try {
        const response = await fetch(`/api/users/${userId}`, {
            method: 'PUT',
            body: formData
        });

        if (response.ok) {
            window.location.reload();
        } else {
            const error = await response.json();
            alert(error.detail || 'Erro ao atualizar usuário');
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao atualizar usuário');
    }
}

// Função para selecionar/desselecionar todos
function toggleSelectAll() {
    const selectAllCheckbox = document.getElementById('selectAll');
    const checkboxes = document.querySelectorAll('.user-checkbox');
    
    checkboxes.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
    });
    
    updateDeleteButton();
}

// Função para atualizar o estado do botão de exclusão
function updateDeleteButton() {
    const selectedCount = document.querySelectorAll('.user-checkbox:checked').length;
    const deleteButton = document.getElementById('deleteSelectedBtn');
    
    deleteButton.disabled = selectedCount === 0;
    deleteButton.innerHTML = `<i class="fas fa-trash-alt"></i> Excluir ${selectedCount} Selecionado${selectedCount !== 1 ? 's' : ''}`;
}

// Validação de formulários
(function () {
    'use strict'
    var forms = document.querySelectorAll('.needs-validation')
    Array.prototype.slice.call(forms)
        .forEach(function (form) {
            form.addEventListener('submit', function (event) {
                if (!form.checkValidity()) {
                    event.preventDefault()
                    event.stopPropagation()
                }
                form.classList.add('was-validated')
            }, false)
        })
})()

// Máscara para CPF
document.addEventListener('DOMContentLoaded', function() {
    const cpfInputs = document.querySelectorAll('#cpf, #editCpf');
    cpfInputs.forEach(input => {
        if (input) {
            input.addEventListener('input', function(e) {
                let value = e.target.value.replace(/\D/g, '');
                if (value.length > 11) value = value.slice(0, 11);
                value = value.replace(/(\d{3})(\d)/, '$1.$2');
                value = value.replace(/(\d{3})(\d)/, '$1.$2');
                value = value.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
                e.target.value = value;
            });
        }
    });
}); 