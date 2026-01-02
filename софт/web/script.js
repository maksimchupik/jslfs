// Конфигурация
const API_BASE_URL = localStorage.getItem('api_url') || 'http://localhost:8000';

// Утилиты
function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type} show`;
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

async function apiRequest(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
        });
        
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: response.statusText }));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        showNotification(`Ошибка: ${error.message}`, 'error');
        throw error;
    }
}

// Управление вкладками
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tabName = btn.dataset.tab;
        
        // Убрать активный класс со всех вкладок и кнопок
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        
        // Добавить активный класс к выбранной вкладке
        btn.classList.add('active');
        document.getElementById(`${tabName}-tab`).classList.add('active');
    });
});

// Загрузка списка аккаунтов
async function loadAccounts() {
    const accountsList = document.getElementById('accounts-list');
    accountsList.innerHTML = '<div class="loading">Загрузка аккаунтов</div>';
    
    try {
        const accounts = await apiRequest('/accounts');
        
        if (accounts.length === 0) {
            accountsList.innerHTML = '<div class="loading">Нет зарегистрированных аккаунтов</div>';
            return;
        }
        
        accountsList.innerHTML = accounts.map(account => `
            <div class="account-card ${account.is_active ? 'active' : 'inactive'}" data-account-id="${account.id}">
                <div class="account-header">
                    <span class="account-id">ID: ${account.id}</span>
                    <span class="status-badge ${account.is_active ? 'active' : 'inactive'}">
                        ${account.is_active ? 'Активен' : 'Неактивен'}
                    </span>
                </div>
                <div class="account-phone">${account.phone_number}</div>
                <div class="account-actions">
                    <button class="btn btn-primary btn-small" onclick="viewAccountDetails(${account.id})">
                        📊 Детали
                    </button>
                    ${account.is_active 
                        ? `<button class="btn btn-danger btn-small" onclick="stopAccount(${account.id})">⏹ Остановить</button>`
                        : `<button class="btn btn-success btn-small" onclick="startAccount(${account.id})">▶ Запустить</button>`
                    }
                    <button class="btn btn-secondary btn-small" onclick="viewProfile(${account.id})">
                        👤 Профиль
                    </button>
                    <button class="btn btn-secondary btn-small" onclick="viewMemory(${account.id})">
                        💾 Память
                    </button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        accountsList.innerHTML = `<div class="loading">Ошибка загрузки: ${error.message}</div>`;
    }
}

// Просмотр деталей аккаунта
async function viewAccountDetails(accountId) {
    const modal = document.getElementById('account-modal');
    const modalBody = document.getElementById('modal-body');
    
    modalBody.innerHTML = '<div class="loading">Загрузка данных</div>';
    modal.style.display = 'block';
    
    try {
        const stats = await apiRequest(`/accounts/${accountId}/stats`);
        
        modalBody.innerHTML = `
            <h2>Детали аккаунта #${accountId}</h2>
            
            <div class="modal-section">
                <h3>Основная информация</h3>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">Номер телефона</div>
                        <div class="info-value">${stats.phone_number || 'N/A'}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Статус</div>
                        <div class="info-value">${stats.is_active ? 'Активен' : 'Неактивен'}</div>
                    </div>
                </div>
            </div>
            
            ${stats.stats ? `
            <div class="modal-section">
                <h3>Статистика</h3>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">${stats.stats.messages_processed || 0}</div>
                        <div class="stat-label">Сообщений обработано</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${stats.stats.responses_sent || 0}</div>
                        <div class="stat-label">Ответов отправлено</div>
                    </div>
                </div>
            </div>
            ` : ''}
            
            <div class="modal-section">
                <h3>Полные данные</h3>
                <div class="profile-section">
                    <pre>${JSON.stringify(stats, null, 2)}</pre>
                </div>
            </div>
        `;
    } catch (error) {
        modalBody.innerHTML = `<div class="loading">Ошибка: ${error.message}</div>`;
    }
}

// Просмотр профиля
async function viewProfile(accountId) {
    const modal = document.getElementById('account-modal');
    const modalBody = document.getElementById('modal-body');

    modalBody.innerHTML = '<div class="loading">Загрузка профиля</div>';
    modal.style.display = 'block';

    try {
        const profile = await apiRequest(`/accounts/${accountId}/profile`);

        modalBody.innerHTML = `
            <h2>Профиль личности аккаунта #${accountId}</h2>

            <div class="modal-section">
                <h3>Базовые настройки</h3>
                <div class="info-grid">
                    ${profile.base ? Object.entries(profile.base).filter(([key]) => key !== 'custom_prompt').map(([key, value]) => `
                        <div class="info-item">
                            <div class="info-label">${key}</div>
                            <div class="info-value">${typeof value === 'object' ? JSON.stringify(value) : value}</div>
                        </div>
                    `).join('') : '<div class="info-item">Нет данных</div>'}
                </div>
            </div>

            ${profile.base && profile.base.custom_prompt ? `
            <div class="modal-section">
                <h3>Пользовательский промпт</h3>
                <div class="profile-section">
                    <pre>${profile.base.custom_prompt}</pre>
                </div>
            </div>
            ` : ''}

            ${profile.constraints ? `
            <div class="modal-section">
                <h3>Ограничения</h3>
                <div class="info-grid">
                    ${Object.entries(profile.constraints).map(([key, value]) => `
                        <div class="info-item">
                            <div class="info-label">${key}</div>
                            <div class="info-value">${typeof value === 'object' ? JSON.stringify(value) : value}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
            ` : ''}

            <div class="modal-section">
                <h3>Разрешенные чаты</h3>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">allowed_chats</div>
                        <div class="info-value">${profile.constraints && profile.constraints.allowed_chats ? profile.constraints.allowed_chats.join(', ') : 'Все чаты разрешены'}</div>
                    </div>
                </div>
                <div class="account-actions">
                    <button class="btn btn-primary" onclick="updateAllowedChats(${accountId})">
                        Изменить разрешенные чаты
                    </button>
                </div>
            </div>

            <div class="modal-section">
                <h3>Действия</h3>
                <div class="account-actions">
                    <button class="btn btn-primary" onclick="editProfile(${accountId})">
                        ✏️ Редактировать профиль
                    </button>
                    <button class="btn btn-primary" onclick="lockPersonality(${accountId})">
                        🔒 Заблокировать личность
                    </button>
                    <button class="btn btn-secondary" onclick="unlockPersonality(${accountId})">
                        🔓 Разблокировать личность
                    </button>
                </div>
            </div>

            <div class="modal-section">
                <h3>Полные данные профиля</h3>
                <div class="profile-section">
                    <pre>${JSON.stringify(profile, null, 2)}</pre>
                </div>
            </div>
        `;
    } catch (error) {
        modalBody.innerHTML = `<div class="loading">Ошибка: ${error.message}</div>`;
    }
}

// Просмотр памяти
async function viewMemory(accountId) {
    const chatId = prompt('Введите Chat ID (или оставьте пустым для общей информации):');
    const modal = document.getElementById('account-modal');
    const modalBody = document.getElementById('modal-body');
    
    modalBody.innerHTML = '<div class="loading">Загрузка памяти</div>';
    modal.style.display = 'block';
    
    try {
        const endpoint = chatId 
            ? `/accounts/${accountId}/memory?chat_id=${encodeURIComponent(chatId)}`
            : `/accounts/${accountId}/memory`;
        const memory = await apiRequest(endpoint);
        
        if (memory.chat_history && memory.chat_history.length > 0) {
            modalBody.innerHTML = `
                <h2>История чата #${chatId}</h2>
                <div class="modal-section">
                    <div class="profile-section">
                        ${memory.chat_history.map(msg => `
                            <div style="margin-bottom: 16px; padding: 12px; background: var(--dark-bg); border-radius: 8px;">
                                <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 4px;">
                                    ${new Date(msg.timestamp * 1000).toLocaleString('ru-RU')}
                                </div>
                                <div style="color: var(--text-primary);">
                                    ${msg.content || JSON.stringify(msg)}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        } else {
            modalBody.innerHTML = `
                <h2>Память аккаунта #${accountId}</h2>
                <div class="modal-section">
                    <div class="profile-section">
                        <pre>${JSON.stringify(memory, null, 2)}</pre>
                    </div>
                </div>
            `;
        }
    } catch (error) {
        modalBody.innerHTML = `<div class="loading">Ошибка: ${error.message}</div>`;
    }
}

// Управление аккаунтами
async function startAccount(accountId) {
    try {
        await apiRequest(`/accounts/${accountId}/start`, { method: 'POST' });
        showNotification(`Аккаунт #${accountId} запущен`, 'success');
        await loadAccounts();
    } catch (error) {
        // Ошибка уже обработана в apiRequest
    }
}

async function stopAccount(accountId) {
    try {
        await apiRequest(`/accounts/${accountId}/stop`, { method: 'POST' });
        showNotification(`Аккаунт #${accountId} остановлен`, 'success');
        await loadAccounts();
    } catch (error) {
        // Ошибка уже обработана в apiRequest
    }
}

// Управление личностью
async function lockPersonality(accountId) {
    try {
        await apiRequest(`/accounts/${accountId}/profile/lock`, { method: 'POST' });
        showNotification('Личность заблокирована', 'success');
        await viewProfile(accountId);
    } catch (error) {
        // Ошибка уже обработана в apiRequest
    }
}

async function unlockPersonality(accountId) {
    try {
        await apiRequest(`/accounts/${accountId}/profile/unlock`, { method: 'POST' });
        showNotification('Личность разблокирована', 'success');
        await viewProfile(accountId);
    } catch (error) {
        // Ошибка уже обработана в apiRequest
    }
}

// Обновление разрешенных чатов
async function updateAllowedChats(accountId) {
    const chatIds = prompt('Введите ID разрешенных чатов через запятую (например: -1001234567890,-1009876543210):');
    if (chatIds === null) return; // Пользователь отменил

    try {
        const chats = chatIds.split(',').map(id => id.trim()).filter(id => id);
        await apiRequest(`/accounts/${accountId}/allowed_chats`, {
            method: 'PUT',
            body: JSON.stringify(chats),
        });
        showNotification('Разрешенные чаты обновлены', 'success');
        await viewProfile(accountId);
    } catch (error) {
        // Ошибка уже обработана в apiRequest
    }
}

// Редактирование профиля личности
async function editProfile(accountId) {
    const modal = document.getElementById('account-modal');
    const modalBody = document.getElementById('modal-body');

    modalBody.innerHTML = '<div class="loading">Загрузка профиля для редактирования</div>';
    modal.style.display = 'block';

    try {
        const profile = await apiRequest(`/accounts/${accountId}/profile`);

        modalBody.innerHTML = `
            <h2>Редактирование профиля личности #${accountId}</h2>

            <div class="modal-section">
                <h3>Базовые настройки</h3>
                <form id="profile-form">
                    <div class="form-group">
                        <label for="speech_style">Стиль общения:</label>
                        <select id="speech_style" class="form-control">
                            <option value="дружелюбный" ${profile.base && profile.base.speech_style === 'дружелюбный' ? 'selected' : ''}>Дружелюбный</option>
                            <option value="ироничный" ${profile.base && profile.base.speech_style === 'ироничный' ? 'selected' : ''}>Ироничный</option>
                            <option value="формальный" ${profile.base && profile.base.speech_style === 'формальный' ? 'selected' : ''}>Формальный</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label for="message_length">Длина сообщений:</label>
                        <select id="message_length" class="form-control">
                            <option value="короткий" ${profile.base && profile.base.message_length === 'короткий' ? 'selected' : ''}>Короткий</option>
                            <option value="средний" ${profile.base && profile.base.message_length === 'средний' ? 'selected' : ''}>Средний</option>
                            <option value="развернутый" ${profile.base && profile.base.message_length === 'развернутый' ? 'selected' : ''}>Развернутый</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label for="emoji_usage">Использование эмодзи:</label>
                        <select id="emoji_usage" class="form-control">
                            <option value="никогда" ${profile.base && profile.base.emoji_usage === 'никогда' ? 'selected' : ''}>Никогда</option>
                            <option value="редко" ${profile.base && profile.base.emoji_usage === 'редко' ? 'selected' : ''}>Редко</option>
                            <option value="часто" ${profile.base && profile.base.emoji_usage === 'часто' ? 'selected' : ''}>Часто</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label for="interests">Интересы (через запятую):</label>
                        <input type="text" id="interests" class="form-control" value="${profile.base && profile.base.interests ? profile.base.interests.join(', ') : ''}">
                    </div>

                    <div class="form-group">
                        <label for="activity_probability">Вероятность активности (0.0 - 1.0):</label>
                        <input type="number" id="activity_probability" class="form-control" step="0.01" min="0" max="1" value="${profile.base && profile.base.activity_probability ? profile.base.activity_probability : 0.35}">
                    </div>

                    <div class="form-group">
                        <label for="custom_prompt">Пользовательский промпт:</label>
                        <textarea id="custom_prompt" class="form-control" rows="6">${profile.base && profile.base.custom_prompt ? profile.base.custom_prompt : ''}</textarea>
                        <small class="form-text">Если заполнено, будет использоваться вместо стандартных настроек личности</small>
                    </div>

                    <div class="form-group">
                        <label for="autonomy_level">Уровень автономности (0.0 - 1.0):</label>
                        <input type="number" id="autonomy_level" class="form-control" step="0.01" min="0" max="1" value="${profile.constraints && profile.constraints.autonomy_level ? profile.constraints.autonomy_level : 0.8}">
                    </div>

                    <div class="form-group">
                        <label for="banned_topics">Запрещенные темы (через запятую):</label>
                        <input type="text" id="banned_topics" class="form-control" value="${profile.constraints && profile.constraints.banned_topics ? profile.constraints.banned_topics.join(', ') : ''}">
                    </div>

                    <div class="form-group">
                        <label for="banned_users">Запрещенные пользователи (через запятую):</label>
                        <input type="text" id="banned_users" class="form-control" value="${profile.constraints && profile.constraints.banned_users ? profile.constraints.banned_users.join(', ') : ''}">
                    </div>

                    <div class="form-group">
                        <label for="allowed_chats">Разрешенные чаты (через запятую):</label>
                        <input type="text" id="allowed_chats" class="form-control" value="${profile.constraints && profile.constraints.allowed_chats ? profile.constraints.allowed_chats.join(', ') : ''}">
                    </div>

                    <div class="account-actions">
                        <button type="submit" class="btn btn-primary">Сохранить изменения</button>
                        <button type="button" class="btn btn-secondary" onclick="viewProfile(${accountId})">Отмена</button>
                    </div>
                </form>
            </div>
        `;

        // Обработчик формы
        document.getElementById('profile-form').addEventListener('submit', async (e) => {
            e.preventDefault();

            try {
                const updatedProfile = {
                    base_config: {
                        speech_style: document.getElementById('speech_style').value,
                        message_length: document.getElementById('message_length').value,
                        emoji_usage: document.getElementById('emoji_usage').value,
                        interests: document.getElementById('interests').value.split(',').map(i => i.trim()).filter(i => i),
                        activity_probability: parseFloat(document.getElementById('activity_probability').value),
                        custom_prompt: document.getElementById('custom_prompt').value
                    },
                    constraints: {
                        autonomy_level: parseFloat(document.getElementById('autonomy_level').value),
                        banned_topics: document.getElementById('banned_topics').value.split(',').map(t => t.trim()).filter(t => t),
                        banned_users: document.getElementById('banned_users').value.split(',').map(u => u.trim()).filter(u => u),
                        allowed_chats: document.getElementById('allowed_chats').value.split(',').map(c => c.trim()).filter(c => c)
                    }
                };

                await apiRequest(`/accounts/${accountId}/profile`, {
                    method: 'PUT',
                    body: JSON.stringify(updatedProfile),
                });

                showNotification('Профиль обновлен', 'success');
                await viewProfile(accountId);
            } catch (error) {
                // Ошибка уже обработана в apiRequest
            }
        });
    } catch (error) {
        modalBody.innerHTML = `<div class="loading">Ошибка: ${error.message}</div>`;
    }
}

// Создание аккаунта
document.getElementById('create-account-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = {
        phone_number: document.getElementById('phone_number').value,
        session_string: document.getElementById('session_string').value,
        api_id: parseInt(document.getElementById('api_id').value),
        api_hash: document.getElementById('api_hash').value,
    };
    
    try {
        const result = await apiRequest('/accounts', {
            method: 'POST',
            body: JSON.stringify(formData),
        });
        
        showNotification(`Аккаунт создан с ID: ${result.account_id}`, 'success');
        document.getElementById('create-account-form').reset();
        
        // Переключиться на вкладку аккаунтов и обновить список
        document.querySelector('[data-tab="accounts"]').click();
        await loadAccounts();
    } catch (error) {
        // Ошибка уже обработана в apiRequest
    }
});

// Настройки
document.getElementById('save-api-url').addEventListener('click', () => {
    const apiUrl = document.getElementById('api-url').value;
    localStorage.setItem('api_url', apiUrl);
    showNotification('URL API сохранен. Перезагрузите страницу.', 'success');
});

// Закрытие модального окна
document.querySelector('.close').addEventListener('click', () => {
    document.getElementById('account-modal').style.display = 'none';
});

window.addEventListener('click', (e) => {
    const modal = document.getElementById('account-modal');
    if (e.target === modal) {
        modal.style.display = 'none';
    }
});

// Обновление списка
document.getElementById('refreshBtn').addEventListener('click', async () => {
    await loadAccounts();
    // Также проверить сессии аккаунтов
    try {
        await apiRequest('/accounts/check_sessions', { method: 'POST' });
        showNotification('Проверка сессий завершена', 'success');
    } catch (error) {
        // Ошибка проверки сессий не критична, просто покажем уведомление
        console.log('Ошибка проверки сессий:', error.message);
    }
});

// Загрузка при старте
loadAccounts();

// Автообновление каждые 30 секунд
setInterval(loadAccounts, 30000);


