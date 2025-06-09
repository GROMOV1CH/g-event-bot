// Инициализация Telegram WebApp
const tg = window.Telegram.WebApp;
tg.expand();

// Глобальные переменные
let isAdmin = false;
let currentUser = null;

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', async () => {
    // Получаем информацию о пользователе
    try {
        const response = await fetch('/api/user_info');
        const userData = await response.json();
        currentUser = userData;
        isAdmin = userData.is_admin;
        
        // Показываем админ-панель только администраторам
        const adminButton = document.getElementById('admin-panel-btn');
        if (isAdmin) {
            adminButton.style.display = 'block';
        }
        
        // Загружаем начальные данные
        loadUpcomingEvents();
        
    } catch (error) {
        console.error('Ошибка при получении информации о пользователе:', error);
    }
});

// Обработчики навигации
document.getElementById('upcoming-events-btn').addEventListener('click', () => {
    showContainer('events-container');
    loadUpcomingEvents();
});

document.getElementById('past-events-btn').addEventListener('click', () => {
    showContainer('events-container');
    loadPastEvents();
});

document.getElementById('polls-btn').addEventListener('click', () => {
    showContainer('polls-container');
    loadPolls();
});

if (document.getElementById('admin-panel-btn')) {
    document.getElementById('admin-panel-btn').addEventListener('click', () => {
        if (isAdmin) {
            showContainer('admin-panel');
            loadAdminData();
        } else {
            alert('Доступ запрещен');
        }
    });
}

// Функции загрузки данных
async function loadUpcomingEvents() {
    try {
        const response = await fetch('/api/events/upcoming');
        const events = await response.json();
        displayEvents(events, 'events-container');
    } catch (error) {
        console.error('Ошибка при загрузке предстоящих мероприятий:', error);
    }
}

async function loadPastEvents() {
    try {
        const response = await fetch('/api/events/past');
        const events = await response.json();
        displayEvents(events, 'events-container');
    } catch (error) {
        console.error('Ошибка при загрузке прошедших мероприятий:', error);
    }
}

async function loadPolls() {
    try {
        const response = await fetch('/api/polls');
        const polls = await response.json();
        displayPolls(polls);
    } catch (error) {
        console.error('Ошибка при загрузке опросов:', error);
    }
}

// Функции отображения
function displayEvents(events, containerId) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';

    events.forEach(event => {
        const eventElement = createEventElement(event);
        container.appendChild(eventElement);
    });
}

function createEventElement(event) {
    const div = document.createElement('div');
    div.className = 'event-card';
    
    const date = new Date(event.date);
    const formattedDate = date.toLocaleString('ru-RU', {
        day: 'numeric',
        month: 'long',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });

    div.innerHTML = `
        <h3>${event.title}</h3>
        <p class="event-description">${event.description}</p>
        <p class="event-details">
            <span class="event-date">📅 ${formattedDate}</span>
            <span class="event-location">📍 ${event.location}</span>
        </p>
        ${isAdmin ? `
            <div class="admin-controls">
                <button onclick="editEvent(${event.id})" class="button-secondary">✏️ Редактировать</button>
                <button onclick="deleteEvent(${event.id})" class="button-danger">🗑️ Удалить</button>
            </div>
        ` : ''}
    `;

    return div;
}

function displayPolls(polls) {
    const container = document.getElementById('polls-container');
    container.innerHTML = '';

    polls.forEach(poll => {
        const pollElement = createPollElement(poll);
        container.appendChild(pollElement);
    });
}

function createPollElement(poll) {
    const div = document.createElement('div');
    div.className = 'poll-card';
    
    const endDate = new Date(poll.end_date);
    const formattedEndDate = endDate.toLocaleString('ru-RU', {
        day: 'numeric',
        month: 'long',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });

    div.innerHTML = `
        <h3>${poll.title}</h3>
        <p class="poll-description">${poll.description}</p>
        <p class="poll-end-date">Окончание: ${formattedEndDate}</p>
        <div class="poll-options">
            ${poll.options.map(option => `
                <div class="poll-option">
                    <input type="radio" name="poll_${poll.id}" value="${option.id}" 
                        ${option.voted ? 'checked' : ''}>
                    <label>${option.text}</label>
                    <span class="vote-count">(${option.votes} голосов)</span>
                </div>
            `).join('')}
        </div>
        ${isAdmin ? `
            <div class="admin-controls">
                <button onclick="editPoll(${poll.id})" class="button-secondary">✏️ Редактировать</button>
                <button onclick="deletePoll(${poll.id})" class="button-danger">🗑️ Удалить</button>
            </div>
        ` : ''}
    `;

    return div;
}

// Админские функции
async function loadAdminData() {
    if (!isAdmin) return;
    
    try {
        // Загрузка статистики
        const statsResponse = await fetch('/api/admin/stats');
        const stats = await statsResponse.json();
        displayStats(stats);
        
        // Загрузка списка пользователей
        const usersResponse = await fetch('/api/admin/users');
        const users = await usersResponse.json();
        displayUsers(users);
    } catch (error) {
        console.error('Ошибка при загрузке админ-данных:', error);
    }
}

function displayStats(stats) {
    document.getElementById('events-stats').innerHTML = `
        <p>Всего мероприятий: ${stats.total_events}</p>
        <p>Предстоящих: ${stats.upcoming_events}</p>
        <p>Прошедших: ${stats.past_events}</p>
    `;
    
    document.getElementById('polls-stats').innerHTML = `
        <p>Всего опросов: ${stats.total_polls}</p>
        <p>Активных: ${stats.active_polls}</p>
        <p>Завершенных: ${stats.completed_polls}</p>
    `;
    
    document.getElementById('users-stats').innerHTML = `
        <p>Всего пользователей: ${stats.total_users}</p>
        <p>Активных сегодня: ${stats.active_today}</p>
    `;
}

function displayUsers(users) {
    const tbody = document.getElementById('users-table-body');
    tbody.innerHTML = '';
    
    users.forEach(user => {
        const row = document.createElement('tr');
        const lastSeen = new Date(user.last_seen).toLocaleString('ru-RU');
        
        row.innerHTML = `
            <td>${user.id}</td>
            <td>${user.username || 'Нет username'}</td>
            <td>${lastSeen}</td>
        `;
        
        tbody.appendChild(row);
    });
}

// Обработчики форм создания
if (document.getElementById('create-event-btn')) {
    document.getElementById('create-event-btn').addEventListener('click', () => {
        if (isAdmin) {
            document.getElementById('create-event-form').style.display = 'block';
        } else {
            alert('Только администраторы могут создавать мероприятия');
        }
    });
}

if (document.getElementById('create-poll-btn')) {
    document.getElementById('create-poll-btn').addEventListener('click', () => {
        if (isAdmin) {
            document.getElementById('create-poll-form').style.display = 'block';
        } else {
            alert('Только администраторы могут создавать опросы');
        }
    });
}

// Вспомогательные функции
function showContainer(containerId) {
    // Скрываем все контейнеры
    document.querySelectorAll('.content > div').forEach(container => {
        container.style.display = 'none';
    });
    
    // Показываем нужный контейнер
    document.getElementById(containerId).style.display = 'block';
    
    // Обновляем активную кнопку в навигации
    document.querySelectorAll('.nav-menu button').forEach(button => {
        button.classList.remove('active');
        if (button.getAttribute('data-container') === containerId) {
            button.classList.add('active');
        }
    });
}

// Функции для работы с формами
document.getElementById('event-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!isAdmin) {
        alert('Только администраторы могут создавать мероприятия');
        return;
    }
    
    const formData = new FormData(e.target);
    const eventData = {
        title: formData.get('title'),
        description: formData.get('description'),
        date: formData.get('date'),
        location: formData.get('location'),
        category: formData.get('category')
    };
    
    try {
        const response = await fetch('/api/events', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(eventData)
        });
        
        if (response.ok) {
            alert('Мероприятие успешно создано');
            document.getElementById('create-event-form').style.display = 'none';
            e.target.reset();
            loadUpcomingEvents();
        } else {
            throw new Error('Ошибка при создании мероприятия');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Произошла ошибка при создании мероприятия');
    }
});

document.getElementById('poll-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!isAdmin) {
        alert('Только администраторы могут создавать опросы');
        return;
    }
    
    const formData = new FormData(e.target);
    const options = Array.from(formData.getAll('options[]')).filter(option => option.trim() !== '');
    
    const pollData = {
        title: formData.get('title'),
        description: formData.get('description'),
        end_date: formData.get('endDate'),
        options: options
    };
    
    try {
        const response = await fetch('/api/polls', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(pollData)
        });
        
        if (response.ok) {
            alert('Опрос успешно создан');
            document.getElementById('create-poll-form').style.display = 'none';
            e.target.reset();
            loadPolls();
        } else {
            throw new Error('Ошибка при создании опроса');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Произошла ошибка при создании опроса');
    }
});

// Обработчики отмены форм
document.getElementById('cancel-create').addEventListener('click', () => {
    document.getElementById('create-event-form').style.display = 'none';
    document.getElementById('event-form').reset();
});

document.getElementById('cancel-poll').addEventListener('click', () => {
    document.getElementById('create-poll-form').style.display = 'none';
    document.getElementById('poll-form').reset();
});

// Функции для работы с опциями опроса
document.getElementById('add-option').addEventListener('click', () => {
    const optionsContainer = document.getElementById('poll-options');
    const newOption = document.createElement('div');
    newOption.className = 'poll-option';
    newOption.innerHTML = `
        <input type="text" name="options[]" required>
        <button type="button" class="remove-option">✕</button>
    `;
    optionsContainer.appendChild(newOption);
});

document.addEventListener('click', (e) => {
    if (e.target.classList.contains('remove-option')) {
        const optionsContainer = document.getElementById('poll-options');
        if (optionsContainer.children.length > 1) {
            e.target.parentElement.remove();
        } else {
            alert('Должен быть хотя бы один вариант ответа');
        }
    }
}); 