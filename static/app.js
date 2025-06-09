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
document.addEventListener('DOMContentLoaded', function() {
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

    // Обработчики кнопок навигации
    upcomingEventsBtn.addEventListener('click', () => {
        showSection('events');
        loadEvents('upcoming');
    });

    pastEventsBtn.addEventListener('click', () => {
        showSection('events');
        loadEvents('past');
    });

    pollsBtn.addEventListener('click', () => {
        showSection('polls');
        loadPolls();
    });

    if (adminPanelBtn) {
        adminPanelBtn.addEventListener('click', () => {
            showSection('admin');
            loadAdminData();
        });
    }

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

    // Загрузка событий
    async function loadEvents(type) {
        try {
            const response = await fetch(`/api/events?type=${type}`);
            const events = await response.json();
            
            eventsContainer.innerHTML = events.length ? '' : '<div class="no-events">Нет мероприятий</div>';
            
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
                eventsContainer.appendChild(card);
            });
        } catch (error) {
            console.error('Error loading events:', error);
            eventsContainer.innerHTML = '<div class="no-events">Ошибка загрузки мероприятий</div>';
        }
    }

    // Загрузка опросов
    async function loadPolls() {
        try {
            const response = await fetch('/api/polls');
            const polls = await response.json();
            
            pollsContainer.innerHTML = polls.length ? '' : '<div class="no-polls">Нет активных опросов</div>';
            
            polls.forEach(poll => {
                const endDate = new Date(poll.endDate);
                const isActive = endDate > new Date();
                const card = document.createElement('div');
                card.className = 'poll-card';
                
                let optionsHtml = '';
                if (isActive) {
                    poll.options.forEach((option, index) => {
                        optionsHtml += `
                            <div class="poll-option">
                                <input type="radio" name="poll_${poll.id}" value="${index}" id="option_${poll.id}_${index}">
                                <label for="option_${poll.id}_${index}">${option.text}</label>
                            </div>
                        `;
                    });
                } else {
                    // Показываем результаты
                    const totalVotes = poll.options.reduce((sum, opt) => sum + opt.votes, 0);
                    poll.options.forEach(option => {
                        const percentage = totalVotes > 0 ? (option.votes / totalVotes * 100).toFixed(1) : 0;
                        optionsHtml += `
                            <div class="poll-results">
                                <div>${option.text} (${option.votes} голосов, ${percentage}%)</div>
                                <div class="poll-bar">
                                    <div class="poll-bar-fill" style="width: ${percentage}%"></div>
                                </div>
                            </div>
                        `;
                    });
                }

                card.innerHTML = `
                    <h3>${poll.title}</h3>
                    <p>${poll.description}</p>
                    <div class="event-date">До: ${endDate.toLocaleString('ru-RU')}</div>
                    <div class="poll-options">
                        ${optionsHtml}
                    </div>
                    ${isActive ? '<button class="button" onclick="submitVote(' + poll.id + ')">Проголосовать</button>' : ''}
                `;
                pollsContainer.appendChild(card);
            });
        } catch (error) {
            console.error('Error loading polls:', error);
            pollsContainer.innerHTML = '<div class="no-polls">Ошибка загрузки опросов</div>';
        }
    }

    // Админ-панель
    if (adminPanel) {
        const createEventBtn = document.getElementById('create-event-btn');
        const createPollBtn = document.getElementById('create-poll-btn');
        const eventForm = document.getElementById('create-event-form');
        const pollForm = document.getElementById('create-poll-form');
        const tabButtons = document.querySelectorAll('.tab-button');
        const tabContents = document.querySelectorAll('.tab-content');

        // Обработка табов
        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const tab = button.dataset.tab;
                
                tabButtons.forEach(btn => btn.classList.remove('active'));
                tabContents.forEach(content => content.style.display = 'none');
                
                button.classList.add('active');
                document.getElementById(`${tab}-tab`).style.display = 'block';
            });
        });

        // Создание мероприятия
        createEventBtn.addEventListener('click', () => {
            eventForm.style.display = 'block';
            createEventBtn.style.display = 'none';
        });

        document.getElementById('cancel-create').addEventListener('click', () => {
            eventForm.style.display = 'none';
            createEventBtn.style.display = 'block';
        });

        document.getElementById('event-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            try {
                const response = await fetch('/api/events', {
                    method: 'POST',
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
                    eventForm.style.display = 'none';
                    createEventBtn.style.display = 'block';
                    e.target.reset();
                    loadAdminData();
                    tg.showAlert('Мероприятие успешно создано!');
                } else {
                    throw new Error('Failed to create event');
                }
            } catch (error) {
                console.error('Error creating event:', error);
                tg.showAlert('Ошибка при создании мероприятия');
            }
        });

        // Создание опроса
        createPollBtn.addEventListener('click', () => {
            pollForm.style.display = 'block';
            createPollBtn.style.display = 'none';
        });

        document.getElementById('cancel-poll').addEventListener('click', () => {
            pollForm.style.display = 'none';
            createPollBtn.style.display = 'block';
        });

        // Добавление опций для опроса
        document.getElementById('add-option').addEventListener('click', () => {
            const pollOptions = document.getElementById('poll-options');
            const newOption = document.createElement('div');
            newOption.className = 'poll-option';
            newOption.innerHTML = `
                <input type="text" name="options[]" required>
                <button type="button" class="remove-option">✕</button>
            `;
            pollOptions.appendChild(newOption);
        });

        // Удаление опций опроса
        document.getElementById('poll-options').addEventListener('click', (e) => {
            if (e.target.classList.contains('remove-option')) {
                const options = document.querySelectorAll('.poll-option');
                if (options.length > 1) {
                    e.target.closest('.poll-option').remove();
                }
            }
        });

        document.getElementById('poll-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const options = Array.from(formData.getAll('options[]')).map(text => ({ text, votes: 0 }));
            
            try {
                const response = await fetch('/api/polls', {
                    method: 'POST',
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
                    pollForm.style.display = 'none';
                    createPollBtn.style.display = 'block';
                    e.target.reset();
                    document.getElementById('poll-options').innerHTML = `
                        <div class="poll-option">
                            <input type="text" name="options[]" required>
                            <button type="button" class="remove-option">✕</button>
                        </div>
                    `;
                    loadAdminData();
                    tg.showAlert('Опрос успешно создан!');
                } else {
                    throw new Error('Failed to create poll');
                }
            } catch (error) {
                console.error('Error creating poll:', error);
                tg.showAlert('Ошибка при создании опроса');
            }
        });
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

    // Загружаем предстоящие мероприятия при старте
    loadEvents('upcoming');
}); 