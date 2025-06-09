// Инициализация Telegram Web App
const webapp = window.Telegram.WebApp;
webapp.ready();

// Установка темы
document.documentElement.style.setProperty('--tg-theme-bg-color', webapp.backgroundColor);
document.documentElement.style.setProperty('--tg-theme-text-color', webapp.textColor);
document.documentElement.style.setProperty('--tg-theme-button-color', webapp.buttonColor);
document.documentElement.style.setProperty('--tg-theme-button-text-color', webapp.buttonTextColor);

// Функции для работы с API
async function fetchUpcomingEvents() {
    const response = await fetch('/api/events/upcoming');
    const data = await response.json();
    return data.events;
}

async function fetchPastEvents() {
    const response = await fetch('/api/events/past');
    const data = await response.json();
    return data.events;
}

async function createEvent(eventData) {
    const response = await fetch('/api/admin/events', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            ...eventData,
            user: webapp.initDataUnsafe.user
        })
    });
    return response.json();
}

// Функция для отображения событий
function displayEvents(events, containerId) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';

    if (events.length === 0) {
        container.innerHTML = '<div class="no-events">Мероприятий не найдено</div>';
        return;
    }

    events.forEach(event => {
        const date = new Date(event.date).toLocaleDateString('ru-RU', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        const card = document.createElement('div');
        card.className = 'event-card';
        card.innerHTML = `
            <h3>${event.title}</h3>
            <p class="event-date">${date}</p>
            <p>${event.description}</p>
            ${event.location ? `<p class="location-info">${event.location}</p>` : ''}
        `;
        container.appendChild(card);
    });
}

// Обработчики кнопок
document.addEventListener('DOMContentLoaded', async function() {
    const tg = window.Telegram.WebApp;
    tg.expand();
    tg.ready();

    // Инициализация UI
    const upcomingEventsBtn = document.getElementById('upcoming-events-btn');
    const pastEventsBtn = document.getElementById('past-events-btn');
    const pollsBtn = document.getElementById('polls-btn');
    const adminPanelBtn = document.getElementById('admin-panel-btn');
    const eventsContainer = document.getElementById('events-container');
    const pollsContainer = document.getElementById('polls-container');
    const adminPanel = document.getElementById('admin-panel');

    // Настраиваем обработчики кнопок
    document.getElementById('upcoming-events-btn').addEventListener('click', () => {
        showContent('events-container');
        loadEvents('upcoming');
        updateActiveButton('upcoming-events-btn');
    });

    document.getElementById('past-events-btn').addEventListener('click', () => {
        showContent('events-container');
        loadEvents('past');
        updateActiveButton('past-events-btn');
    });

    document.getElementById('polls-btn').addEventListener('click', () => {
        showContent('polls-container');
        loadPolls();
        updateActiveButton('polls-btn');
    });

    document.getElementById('admin-panel-btn')?.addEventListener('click', () => {
        showContent('admin-panel');
        updateActiveButton('admin-panel-btn');
    });

    document.getElementById('profileButton').addEventListener('click', () => {
        showContent('my-events-container');
        loadMyEvents();
        // Убираем активное состояние со всех кнопок навигации
        document.querySelectorAll('.nav-menu .button').forEach(button => {
            button.classList.remove('active');
        });
    });

    // Функция для отображения нужной секции
    function showSection(section) {
        eventsContainer.style.display = 'none';
        pollsContainer.style.display = 'none';
        if (adminPanel) adminPanel.style.display = 'none';

        switch(section) {
            case 'events':
                eventsContainer.style.display = 'grid';
                break;
            case 'polls':
                pollsContainer.style.display = 'grid';
                break;
            case 'admin':
                adminPanel.style.display = 'block';
                break;
        }
    }

    // Проверяем права администратора
    const initData = tg.initData || '';
    const user = tg.initDataUnsafe?.user;
    
    if (user) {
        try {
            const response = await fetch('/api/verify_admin', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    initData: initData,
                    user: user
                })
            });
            
            const data = await response.json();
            console.log('Admin check response:', data);
            
            if (data.is_admin) {
                console.log('User is admin');
                document.getElementById('admin-panel-btn').style.display = 'block';
                document.getElementById('admin-panel').style.display = 'none';
                setupAdminPanel();
            } else {
                console.log('User is not admin:', data.error);
            }
        } catch (error) {
            console.error('Error checking admin rights:', error);
        }
    }

    // Загружаем начальные данные
    loadEvents('upcoming');
    loadPolls();
});

// Настройка админ-панели
function setupAdminPanel() {
    const adminPanel = document.getElementById('admin-panel');
    
    // Настраиваем табы
    const tabButtons = adminPanel.querySelectorAll('.tab-button');
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabId = button.getAttribute('data-tab');
            showAdminTab(tabId);
            if (tabId === 'stats') {
                loadStats();
            }
        });
    });

    // Настраиваем формы создания
    setupEventForm();
    setupPollForm();
}

// Функция для отображения табов админ-панели
function showAdminTab(tabId) {
    const tabs = document.querySelectorAll('.tab-content');
    const buttons = document.querySelectorAll('.tab-button');

    tabs.forEach(tab => {
        tab.style.display = tab.id === `${tabId}-tab` ? 'block' : 'none';
    });

    buttons.forEach(button => {
        button.classList.toggle('active', button.getAttribute('data-tab') === tabId);
    });
}

// Функция настройки формы создания мероприятия
function setupEventForm() {
    const form = document.getElementById('event-form');
    const createBtn = document.getElementById('create-event-btn');
    const cancelBtn = document.getElementById('cancel-create');
    
    createBtn.addEventListener('click', () => {
        document.getElementById('create-event-form').style.display = 'block';
        document.getElementById('events-management').style.display = 'none';
    });
    
    cancelBtn.addEventListener('click', () => {
        document.getElementById('create-event-form').style.display = 'none';
        document.getElementById('events-management').style.display = 'block';
        form.reset();
    });
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = {
            title: form.title.value,
            description: form.description.value,
            date: new Date(form.date.value).toISOString(),
            location: form.location.value,
            category: form.category.value
        };
        
        try {
            const response = await fetch('/api/events', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            if (response.ok) {
                // Очищаем форму и скрываем её
                form.reset();
                document.getElementById('create-event-form').style.display = 'none';
                document.getElementById('events-management').style.display = 'block';
                
                // Обновляем список мероприятий
                loadEvents('upcoming');
                
                // Показываем уведомление об успехе
                tg.showAlert('Мероприятие успешно создано!');
            } else {
                const error = await response.json();
                tg.showAlert(`Ошибка: ${error.detail}`);
            }
        } catch (error) {
            console.error('Error creating event:', error);
            tg.showAlert('Произошла ошибка при создании мероприятия');
        }
    });
}

// Функция настройки формы создания опроса
function setupPollForm() {
    const form = document.getElementById('poll-form');
    const createBtn = document.getElementById('create-poll-btn');
    const cancelBtn = document.getElementById('cancel-poll');
    const addOptionBtn = document.getElementById('add-option');
    
    createBtn.addEventListener('click', () => {
        document.getElementById('create-poll-form').style.display = 'block';
        document.getElementById('polls-management').style.display = 'none';
    });
    
    cancelBtn.addEventListener('click', () => {
        document.getElementById('create-poll-form').style.display = 'none';
        document.getElementById('polls-management').style.display = 'block';
        form.reset();
        resetPollOptions();
    });
    
    addOptionBtn.addEventListener('click', addPollOption);
    
    // Добавляем обработчики удаления для существующих опций
    document.querySelectorAll('.remove-option').forEach(btn => {
        btn.addEventListener('click', () => btn.parentElement.remove());
    });
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const options = Array.from(form.querySelectorAll('input[name="options[]"]'))
            .map(input => input.value)
            .filter(value => value.trim() !== '');
        
        if (options.length < 2) {
            tg.showAlert('Добавьте как минимум 2 варианта ответа');
            return;
        }
        
        const formData = {
            title: form.title.value,
            description: form.description.value,
            endDate: new Date(form.endDate.value).toISOString(),
            options: options.map(text => ({ text }))
        };
        
        try {
            const response = await fetch('/api/polls', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            if (response.ok) {
                // Очищаем форму и скрываем её
                form.reset();
                resetPollOptions();
                document.getElementById('create-poll-form').style.display = 'none';
                document.getElementById('polls-management').style.display = 'block';
                
                // Обновляем список опросов
                loadPolls();
                
                // Показываем уведомление об успехе
                tg.showAlert('Опрос успешно создан!');
            } else {
                const error = await response.json();
                tg.showAlert(`Ошибка: ${error.detail}`);
            }
        } catch (error) {
            console.error('Error creating poll:', error);
            tg.showAlert('Произошла ошибка при создании опроса');
        }
    });
}

// Вспомогательная функция для добавления поля опции в форму опроса
function addPollOption() {
    const optionsContainer = document.getElementById('poll-options');
    const optionDiv = document.createElement('div');
    optionDiv.className = 'poll-option';
    optionDiv.innerHTML = `
        <input type="text" name="options[]" required>
        <button type="button" class="remove-option">✕</button>
    `;
    
    const removeBtn = optionDiv.querySelector('.remove-option');
    removeBtn.addEventListener('click', () => optionDiv.remove());
    
    optionsContainer.appendChild(optionDiv);
}

// Вспомогательная функция для сброса опций опроса
function resetPollOptions() {
    const optionsContainer = document.getElementById('poll-options');
    // Оставляем только первую опцию
    const options = optionsContainer.querySelectorAll('.poll-option');
    for (let i = 1; i < options.length; i++) {
        options[i].remove();
    }
    // Очищаем значение первой опции
    const firstOption = optionsContainer.querySelector('input[name="options[]"]');
    if (firstOption) {
        firstOption.value = '';
    }
}

// Функция загрузки мероприятий
async function loadEvents(type = 'upcoming') {
    const container = document.getElementById('events-container');
    container.innerHTML = '<div class="loading">Загрузка...</div>';

    try {
        const response = await fetch(`/api/events?type=${type}`);
        const events = await response.json();

        if (events.length === 0) {
            container.innerHTML = type === 'upcoming' ? 
                '<div class="no-events">Нет предстоящих мероприятий</div>' : 
                '<div class="no-events">Нет прошедших мероприятий</div>';
            return;
        }

        container.innerHTML = '';
        events.forEach(event => {
            const date = new Date(event.date);
            const card = document.createElement('div');
            card.className = 'event-card';
            card.innerHTML = `
                <h3>${event.title}</h3>
                <div class="event-date">${date.toLocaleString('ru-RU')}</div>
                <p>${event.description}</p>
                ${event.location ? `<div class="location-info">${event.location}</div>` : ''}
            `;
            container.appendChild(card);
        });
    } catch (error) {
        console.error('Error loading events:', error);
        container.innerHTML = '<div class="error">Ошибка загрузки мероприятий</div>';
    }
}

// Функция загрузки опросов
async function loadPolls() {
    const container = document.getElementById('polls-container');
    container.innerHTML = '<div class="loading">Загрузка...</div>';

    try {
        const response = await fetch('/api/polls');
        const polls = await response.json();

        if (polls.length === 0) {
            container.innerHTML = '<div class="no-polls">Нет активных опросов</div>';
            return;
        }

        container.innerHTML = '';
        polls.forEach(poll => {
            const endDate = new Date(poll.end_date);
            const card = document.createElement('div');
            card.className = 'poll-card';
            card.innerHTML = `
                <h3>${poll.title}</h3>
                <p>${poll.description}</p>
                <div class="poll-date">Окончание: ${endDate.toLocaleString('ru-RU')}</div>
                <div class="poll-options">
                    ${poll.options.map(option => `
                        <div class="poll-option">
                            <input type="radio" name="poll_${poll.id}" value="${option.id}" id="option_${poll.id}_${option.id}">
                            <label for="option_${poll.id}_${option.id}">${option.text}</label>
                            <div class="poll-bar">
                                <div class="poll-bar-fill" style="width: ${option.votes_percentage}%"></div>
                            </div>
                            <span class="votes-count">${option.votes_count} голосов</span>
                        </div>
                    `).join('')}
                </div>
            `;
            container.appendChild(card);
        });
    } catch (error) {
        console.error('Error loading polls:', error);
        container.innerHTML = '<div class="error">Ошибка загрузки опросов</div>';
    }
}

// Загрузка данных для админ-панели
async function loadAdminData() {
    if (!adminPanel) return;

    try {
        // Загрузка мероприятий для управления
        const eventsResponse = await fetch('/api/events/all');
        const events = await eventsResponse.json();
        const eventsManagement = document.getElementById('events-management');
        
        eventsManagement.innerHTML = events.length ? '' : '<div class="no-events">Нет мероприятий</div>';
        
        events.forEach(event => {
            const date = new Date(event.date);
            const card = document.createElement('div');
            card.className = 'event-card';
            card.innerHTML = `
                <h3>${event.title}</h3>
                <div class="event-date">${date.toLocaleString('ru-RU')}</div>
                <p>${event.description}</p>
                ${event.location ? `<div class="location-info">${event.location}</div>` : ''}
                <div class="form-actions">
                    <button class="button button-secondary" onclick="editEvent(${event.id})">Редактировать</button>
                    <button class="button button-secondary" onclick="deleteEvent(${event.id})">Удалить</button>
                </div>
            `;
            eventsManagement.appendChild(card);
        });

        // Загрузка опросов для управления
        const pollsResponse = await fetch('/api/polls/all');
        const polls = await pollsResponse.json();
        const pollsManagement = document.getElementById('polls-management');
        
        pollsManagement.innerHTML = polls.length ? '' : '<div class="no-polls">Нет опросов</div>';
        
        polls.forEach(poll => {
            const endDate = new Date(poll.endDate);
            const card = document.createElement('div');
            card.className = 'poll-card';
            card.innerHTML = `
                <h3>${poll.title}</h3>
                <p>${poll.description}</p>
                <div class="event-date">До: ${endDate.toLocaleString('ru-RU')}</div>
                <div class="form-actions">
                    <button class="button button-secondary" onclick="editPoll(${poll.id})">Редактировать</button>
                    <button class="button button-secondary" onclick="deletePoll(${poll.id})">Удалить</button>
                </div>
            `;
            pollsManagement.appendChild(card);
        });
    } catch (error) {
        console.error('Error loading admin data:', error);
    }
}

// Голосование в опросе
window.submitVote = async (pollId) => {
    const selectedOption = document.querySelector(`input[name="poll_${pollId}"]:checked`);
    if (!selectedOption) {
        tg.showAlert('Пожалуйста, выберите вариант ответа');
        return;
    }

    try {
        const response = await fetch(`/api/polls/${pollId}/vote`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                optionIndex: parseInt(selectedOption.value)
            })
        });

        if (response.ok) {
            tg.showAlert('Ваш голос учтен!');
            loadPolls();
        } else {
            throw new Error('Failed to submit vote');
        }
    } catch (error) {
        console.error('Error submitting vote:', error);
        tg.showAlert('Ошибка при голосовании');
    }
};

// Редактирование мероприятия
window.editEvent = async (eventId) => {
    try {
        const response = await fetch(`/api/events/${eventId}`);
        const event = await response.json();
        
        const form = document.getElementById('event-form');
        form.elements.title.value = event.title;
        form.elements.description.value = event.description;
        form.elements.date.value = event.date.slice(0, 16); // Формат YYYY-MM-DDTHH:mm
        form.elements.location.value = event.location || '';
        
        document.getElementById('create-event-form').style.display = 'block';
        document.getElementById('create-event-btn').style.display = 'none';
        
        // Изменяем обработчик формы для обновления
        const originalSubmit = form.onsubmit;
        form.onsubmit = async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            try {
                const response = await fetch(`/api/events/${eventId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        title: formData.get('title'),
                        description: formData.get('description'),
                        date: formData.get('date'),
                        location: formData.get('location')
                    })
                });

                if (response.ok) {
                    document.getElementById('create-event-form').style.display = 'none';
                    document.getElementById('create-event-btn').style.display = 'block';
                    form.reset();
                    form.onsubmit = originalSubmit;
                    loadAdminData();
                    tg.showAlert('Мероприятие успешно обновлено!');
                } else {
                    throw new Error('Failed to update event');
                }
            } catch (error) {
                console.error('Error updating event:', error);
                tg.showAlert('Ошибка при обновлении мероприятия');
            }
        };
    } catch (error) {
        console.error('Error loading event for edit:', error);
        tg.showAlert('Ошибка при загрузке мероприятия');
    }
};

// Редактирование опроса
window.editPoll = async (pollId) => {
    try {
        const response = await fetch(`/api/polls/${pollId}`);
        const poll = await response.json();
        
        const form = document.getElementById('poll-form');
        form.elements.title.value = poll.title;
        form.elements.description.value = poll.description;
        form.elements['endDate'].value = poll.endDate.slice(0, 16); // Формат YYYY-MM-DDTHH:mm
        
        const pollOptions = document.getElementById('poll-options');
        pollOptions.innerHTML = '';
        poll.options.forEach(option => {
            const optionDiv = document.createElement('div');
            optionDiv.className = 'poll-option';
            optionDiv.innerHTML = `
                <input type="text" name="options[]" value="${option.text}" required>
                <button type="button" class="remove-option">✕</button>
            `;
            pollOptions.appendChild(optionDiv);
        });
        
        document.getElementById('create-poll-form').style.display = 'block';
        document.getElementById('create-poll-btn').style.display = 'none';
        
        // Изменяем обработчик формы для обновления
        const originalSubmit = form.onsubmit;
        form.onsubmit = async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const options = Array.from(formData.getAll('options[]')).map((text, index) => ({
                text,
                votes: poll.options[index]?.votes || 0
            }));
            
            try {
                const response = await fetch(`/api/polls/${pollId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        title: formData.get('title'),
                        description: formData.get('description'),
                        endDate: formData.get('endDate'),
                        options
                    })
                });

                if (response.ok) {
                    document.getElementById('create-poll-form').style.display = 'none';
                    document.getElementById('create-poll-btn').style.display = 'block';
                    form.reset();
                    form.onsubmit = originalSubmit;
                    pollOptions.innerHTML = `
                        <div class="poll-option">
                            <input type="text" name="options[]" required>
                            <button type="button" class="remove-option">✕</button>
                        </div>
                    `;
                    loadAdminData();
                    tg.showAlert('Опрос успешно обновлен!');
                } else {
                    throw new Error('Failed to update poll');
                }
            } catch (error) {
                console.error('Error updating poll:', error);
                tg.showAlert('Ошибка при обновлении опроса');
            }
        };
    } catch (error) {
        console.error('Error loading poll for edit:', error);
        tg.showAlert('Ошибка при загрузке опроса');
    }
};

// Удаление мероприятия
window.deleteEvent = async (eventId) => {
    if (confirm('Вы уверены, что хотите удалить это мероприятие?')) {
        try {
            const response = await fetch(`/api/events/${eventId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                loadAdminData();
                tg.showAlert('Мероприятие успешно удалено!');
            } else {
                throw new Error('Failed to delete event');
            }
        } catch (error) {
            console.error('Error deleting event:', error);
            tg.showAlert('Ошибка при удалении мероприятия');
        }
    }
};

// Удаление опроса
window.deletePoll = async (pollId) => {
    if (confirm('Вы уверены, что хотите удалить этот опрос?')) {
        try {
            const response = await fetch(`/api/polls/${pollId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                loadAdminData();
                tg.showAlert('Опрос успешно удален!');
            } else {
                throw new Error('Failed to delete poll');
            }
        } catch (error) {
            console.error('Error deleting poll:', error);
            tg.showAlert('Ошибка при удалении опроса');
        }
    }
};

function checkAdminRights() {
    const user = webapp.initDataUnsafe.user;
    if (user && user.id) {
        fetch(`/api/users/${user.id}/is_admin`)
            .then(response => response.json())
            .then(data => {
                if (data.is_admin) {
                    document.getElementById('adminButton').style.display = 'block';
                    loadAdminData();
                }
            })
            .catch(error => console.error('Error checking admin rights:', error));
    }
}

function showSection(sectionId) {
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
    });
    document.querySelectorAll('.nav-menu button').forEach(button => {
        button.classList.remove('active');
    });
    
    document.getElementById(sectionId).classList.add('active');
    event.target.classList.add('active');
}

function loadEvents(type) {
    document.querySelectorAll('.tab-menu button').forEach(button => {
        button.classList.remove('active');
    });
    event.target.classList.add('active');

    const eventsList = document.getElementById('eventsList');
    eventsList.innerHTML = '<div class="loading">Загрузка...</div>';

    fetch(`/api/events?type=${type}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.length === 0) {
                eventsList.innerHTML = '<div class="no-data">Мероприятий не найдено</div>';
                return;
            }

            eventsList.innerHTML = data.map(event => `
                <div class="event-card">
                    <h3>${event.title}</h3>
                    <p>${event.description}</p>
                    <div class="event-details">
                        <span>📅 ${formatDate(event.date)}</span>
                        <span>📍 ${event.location}</span>
                    </div>
                </div>
            `).join('');
        })
        .catch(error => {
            console.error('Error loading events:', error);
            eventsList.innerHTML = '<div class="error">Ошибка при загрузке мероприятий. Пожалуйста, попробуйте позже.</div>';
        });
}

function loadPolls() {
    const pollsList = document.getElementById('pollsList');
    pollsList.innerHTML = '<div class="loading">Загрузка...</div>';

    fetch('/api/polls')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.length === 0) {
                pollsList.innerHTML = '<div class="no-data">Опросов не найдено</div>';
                return;
            }

            pollsList.innerHTML = data.map(poll => `
                <div class="poll-card">
                    <h3>${poll.question}</h3>
                    <div class="poll-options">
                        ${poll.options.map(option => `
                            <button onclick="vote(${poll.id}, '${option}')">${option}</button>
                        `).join('')}
                    </div>
                    ${poll.results ? `
                        <div class="poll-results">
                            ${Object.entries(poll.results).map(([option, votes]) => `
                                <div class="result-bar">
                                    <span>${option}: ${votes} голосов</span>
                                    <div class="bar" style="width: ${(votes / poll.total_votes * 100)}%"></div>
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                </div>
            `).join('');
        })
        .catch(error => {
            console.error('Error loading polls:', error);
            pollsList.innerHTML = '<div class="error">Ошибка при загрузке опросов. Пожалуйста, попробуйте позже.</div>';
        });
}

function loadAdminData() {
    loadAdminEvents();
    loadAdminPolls();
}

function loadAdminEvents() {
    fetch('/api/events/all')
        .then(response => response.json())
        .then(data => {
            const adminEventsList = document.getElementById('adminEventsList');
            adminEventsList.innerHTML = data.map(event => `
                <div class="admin-item">
                    <h4>${event.title}</h4>
                    <div class="admin-controls">
                        <button onclick="editEvent(${event.id})">Редактировать</button>
                        <button onclick="deleteEvent(${event.id})">Удалить</button>
                    </div>
                </div>
            `).join('');
        })
        .catch(error => console.error('Error loading admin events:', error));
}

function loadAdminPolls() {
    fetch('/api/polls/all')
        .then(response => response.json())
        .then(data => {
            const adminPollsList = document.getElementById('adminPollsList');
            adminPollsList.innerHTML = data.map(poll => `
                <div class="admin-item">
                    <h4>${poll.title}</h4>
                    <div class="admin-controls">
                        <button onclick="editPoll(${poll.id})">Редактировать</button>
                        <button onclick="deletePoll(${poll.id})">Удалить</button>
                    </div>
                </div>
            `).join('');
        })
        .catch(error => console.error('Error loading admin polls:', error));
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('ru-RU', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Функции для работы с модальными окнами
function showCreateEventForm() {
    document.getElementById('createEventModal').style.display = 'block';
}

function showCreatePollForm() {
    document.getElementById('createPollModal').style.display = 'block';
}

// Закрытие модальных окон
document.querySelectorAll('.close').forEach(closeBtn => {
    closeBtn.onclick = function() {
        this.closest('.modal').style.display = 'none';
    }
});

window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
}

// Обработка форм
document.getElementById('createEventForm').onsubmit = function(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const eventData = {
        title: formData.get('title'),
        description: formData.get('description'),
        date: new Date(formData.get('date')).toISOString(),
        location: formData.get('location')
    };

    fetch('/api/events', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(eventData)
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('createEventModal').style.display = 'none';
        loadAdminEvents();
        loadEvents('upcoming');
    })
    .catch(error => console.error('Error creating event:', error));
};

document.getElementById('createPollForm').onsubmit = function(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const pollData = {
        question: formData.get('question'),
        options: Array.from(formData.getAll('options[]')).filter(option => option.trim() !== '')
    };

    fetch('/api/polls', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(pollData)
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('createPollModal').style.display = 'none';
        loadAdminPolls();
        loadPolls();
    })
    .catch(error => console.error('Error creating poll:', error));
};

function addOption() {
    const container = document.getElementById('optionsContainer');
    const input = document.createElement('input');
    input.type = 'text';
    input.name = 'options[]';
    input.placeholder = `Вариант ${container.children.length + 1}`;
    input.required = true;
    container.appendChild(input);
}

// Функции для голосования
function vote(pollId, option) {
    fetch(`/api/polls/${pollId}/vote`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ option })
    })
    .then(response => response.json())
    .then(data => {
        loadPolls();
    })
    .catch(error => console.error('Error voting:', error));
}

// Функции для редактирования и удаления
function editEvent(eventId) {
    // TODO: Реализовать редактирование мероприятия
}

function deleteEvent(eventId) {
    if (confirm('Вы уверены, что хотите удалить это мероприятие?')) {
        fetch(`/api/events/${eventId}`, {
            method: 'DELETE'
        })
        .then(response => {
            if (response.ok) {
                loadAdminEvents();
                loadEvents('upcoming');
            }
        })
        .catch(error => console.error('Error deleting event:', error));
    }
}

function editPoll(pollId) {
    // TODO: Реализовать редактирование опроса
}

function deletePoll(pollId) {
    if (confirm('Вы уверены, что хотите удалить этот опрос?')) {
        fetch(`/api/polls/${pollId}`, {
            method: 'DELETE'
        })
        .then(response => {
            if (response.ok) {
                loadAdminPolls();
                loadPolls();
            }
        })
        .catch(error => console.error('Error deleting poll:', error));
    }
}

let tg = window.Telegram.WebApp;
tg.expand();

let currentEvents = [];
let myEvents = new Set();
let searchTimeout;

document.addEventListener('DOMContentLoaded', async function() {
    // Проверяем права администратора
    const initData = tg.initData || '';
    const user = tg.initDataUnsafe?.user;
    
    if (user) {
        try {
            const response = await fetch('/api/verify_admin', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    initData: initData,
                    user: user
                })
            });
            
            const data = await response.json();
            console.log('Admin check response:', data);
            
            if (data.is_admin) {
                console.log('User is admin');
                document.getElementById('admin-panel-btn').style.display = 'block';
                document.getElementById('admin-panel').style.display = 'none';
                setupAdminPanel();
            } else {
                console.log('User is not admin:', data.error);
            }
        } catch (error) {
            console.error('Error checking admin rights:', error);
        }
    }

    // Загружаем сохраненные мероприятия
    loadSavedEvents();

    // Настраиваем обработчики кнопок
    document.getElementById('upcoming-events-btn').addEventListener('click', () => {
        showContent('events-container');
        loadEvents('upcoming');
        updateActiveButton('upcoming-events-btn');
    });

    document.getElementById('past-events-btn').addEventListener('click', () => {
        showContent('events-container');
        loadEvents('past');
        updateActiveButton('past-events-btn');
    });

    document.getElementById('polls-btn').addEventListener('click', () => {
        showContent('polls-container');
        loadPolls();
        updateActiveButton('polls-btn');
    });

    document.getElementById('admin-panel-btn')?.addEventListener('click', () => {
        showContent('admin-panel');
        updateActiveButton('admin-panel-btn');
    });

    document.getElementById('profileButton').addEventListener('click', () => {
        showContent('my-events-container');
        loadMyEvents();
        // Убираем активное состояние со всех кнопок навигации
        document.querySelectorAll('.nav-menu .button').forEach(button => {
            button.classList.remove('active');
        });
    });

    // Настраиваем поиск и фильтры
    setupSearchAndFilters();

    // Настраиваем модальное окно напоминания
    setupReminderModal();

    // Загружаем начальные данные
    loadEvents('upcoming');
});

// Функция настройки поиска и фильтров
function setupSearchAndFilters() {
    const searchInput = document.getElementById('searchInput');
    const searchButton = document.getElementById('searchButton');
    const monthFilter = document.getElementById('monthFilter');
    const categoryFilter = document.getElementById('categoryFilter');

    searchInput.addEventListener('input', () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            filterEvents();
        }, 300);
    });

    searchButton.addEventListener('click', filterEvents);
    monthFilter.addEventListener('change', filterEvents);
    categoryFilter.addEventListener('change', filterEvents);
}

// Функция фильтрации мероприятий
function filterEvents() {
    const searchQuery = document.getElementById('searchInput').value.toLowerCase();
    const monthValue = document.getElementById('monthFilter').value;
    const categoryValue = document.getElementById('categoryFilter').value;

    const filteredEvents = currentEvents.filter(event => {
        const matchesSearch = event.title.toLowerCase().includes(searchQuery) ||
                            event.description.toLowerCase().includes(searchQuery) ||
                            event.location?.toLowerCase().includes(searchQuery);

        const eventDate = new Date(event.date);
        const matchesMonth = !monthValue || eventDate.getMonth() === parseInt(monthValue);
        const matchesCategory = !categoryValue || event.category === categoryValue;

        return matchesSearch && matchesMonth && matchesCategory;
    });

    displayEvents(filteredEvents);
}

// Функция отображения мероприятий
function displayEvents(events) {
    const container = document.getElementById('events-container');
    container.innerHTML = '';

    if (events.length === 0) {
        container.innerHTML = '<div class="no-events">Мероприятия не найдены</div>';
        return;
    }

    events.forEach(event => {
        const date = new Date(event.date);
        const card = document.createElement('div');
        card.className = 'event-card';
        card.innerHTML = `
            <h3>${event.title}</h3>
            <div class="event-date">${date.toLocaleString('ru-RU')}</div>
            <p>${event.description}</p>
            ${event.location ? `<div class="location-info">${event.location}</div>` : ''}
            <div class="event-actions">
                <button class="action-button share-button" title="Поделиться">📤</button>
                <button class="action-button reminder-button" title="Установить напоминание">⏰</button>
                <button class="action-button save-button ${myEvents.has(event.id) ? 'active' : ''}" title="Сохранить">🌟</button>
            </div>
        `;

        // Настраиваем обработчики кнопок
        const shareButton = card.querySelector('.share-button');
        const reminderButton = card.querySelector('.reminder-button');
        const saveButton = card.querySelector('.save-button');

        shareButton.addEventListener('click', () => shareEvent(event));
        reminderButton.addEventListener('click', () => showReminderModal(event));
        saveButton.addEventListener('click', () => toggleSaveEvent(event, saveButton));

        container.appendChild(card);
    });
}

// Функция для поделиться мероприятием
function shareEvent(event) {
    const date = new Date(event.date);
    const message = `
🎉 ${event.title}

📅 ${date.toLocaleString('ru-RU')}
📝 ${event.description}
${event.location ? `📍 ${event.location}` : ''}
`;
    
    tg.sendData(JSON.stringify({
        action: 'share_event',
        event_id: event.id,
        message: message
    }));
}

// Функция настройки модального окна напоминания
function setupReminderModal() {
    const modal = document.getElementById('reminder-modal');
    const closeBtn = modal.querySelector('.close');
    const form = document.getElementById('reminder-form');
    const cancelBtn = document.getElementById('cancel-reminder');

    closeBtn.addEventListener('click', () => modal.style.display = 'none');
    cancelBtn.addEventListener('click', () => modal.style.display = 'none');

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        const reminderTime = document.getElementById('reminder-time').value;
        setReminder(form.dataset.eventId, reminderTime);
        modal.style.display = 'none';
    });

    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
}

// Функция показа модального окна напоминания
function showReminderModal(event) {
    const modal = document.getElementById('reminder-modal');
    const form = document.getElementById('reminder-form');
    form.dataset.eventId = event.id;
    modal.style.display = 'block';
}

// Функция установки напоминания
function setReminder(eventId, reminderTime) {
    const event = currentEvents.find(e => e.id === eventId);
    if (!event) return;

    const eventDate = new Date(event.date);
    const reminderDate = new Date(eventDate.getTime() - reminderTime * 60000);

    tg.sendData(JSON.stringify({
        action: 'set_reminder',
        event_id: eventId,
        reminder_time: reminderTime,
        event_title: event.title,
        event_date: eventDate.toISOString(),
        reminder_date: reminderDate.toISOString()
    }));
}

// Функция сохранения/удаления мероприятия
function toggleSaveEvent(event, button) {
    if (myEvents.has(event.id)) {
        myEvents.delete(event.id);
        button.classList.remove('active');
    } else {
        myEvents.add(event.id);
        button.classList.add('active');
    }

    localStorage.setItem('myEvents', JSON.stringify(Array.from(myEvents)));
    
    // Если мы находимся в разделе "Мои события", обновляем список
    if (document.getElementById('my-events-container').style.display === 'block') {
        loadMyEvents();
    }
}

// Функция загрузки сохраненных мероприятий
function loadSavedEvents() {
    const saved = localStorage.getItem('myEvents');
    if (saved) {
        myEvents = new Set(JSON.parse(saved));
    }
}

// Функция загрузки моих мероприятий
function loadMyEvents() {
    const container = document.getElementById('my-events-container');
    const myEventsList = currentEvents.filter(event => myEvents.has(event.id));
    
    if (myEventsList.length === 0) {
        container.innerHTML = '<div class="no-events">У вас нет сохраненных мероприятий</div>';
        return;
    }

    displayEvents(myEventsList);
}

// Функция обновления активной кнопки
function updateActiveButton(buttonId) {
    document.querySelectorAll('.nav-menu .button').forEach(button => {
        button.classList.remove('active');
    });
    document.getElementById(buttonId).classList.add('active');
}

// Функция отображения контента
function showContent(contentId) {
    const containers = ['events-container', 'my-events-container', 'polls-container', 'admin-panel'];
    containers.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.style.display = id === contentId ? 'block' : 'none';
        }
    });
}

// Функция загрузки статистики
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();

        // Статистика мероприятий
        const eventsStats = document.getElementById('events-stats');
        eventsStats.innerHTML = `
            <div class="stat-item">
                <span class="stat-label">Всего мероприятий</span>
                <span class="stat-value">${stats.events.total}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Предстоящие</span>
                <span class="stat-value">${stats.events.upcoming}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Прошедшие</span>
                <span class="stat-value">${stats.events.past}</span>
            </div>
            <div class="chart-container" id="events-chart"></div>
        `;

        // Статистика опросов
        const pollsStats = document.getElementById('polls-stats');
        pollsStats.innerHTML = `
            <div class="stat-item">
                <span class="stat-label">Всего опросов</span>
                <span class="stat-value">${stats.polls.total}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Активные</span>
                <span class="stat-value">${stats.polls.active}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Завершенные</span>
                <span class="stat-value">${stats.polls.completed}</span>
            </div>
            <div class="chart-container" id="polls-chart"></div>
        `;

        // Статистика пользователей
        const usersStats = document.getElementById('users-stats');
        usersStats.innerHTML = `
            <div class="stat-item">
                <span class="stat-label">Всего пользователей</span>
                <span class="stat-value">${stats.users.total}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Активные сегодня</span>
                <span class="stat-value">${stats.users.active_today}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Новые за неделю</span>
                <span class="stat-value">${stats.users.new_this_week}</span>
            </div>
            <div class="chart-container" id="users-chart"></div>
        `;

    } catch (error) {
        console.error('Error loading stats:', error);
    }
} 