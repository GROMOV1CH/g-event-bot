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
document.addEventListener('DOMContentLoaded', () => {
    const upcomingBtn = document.getElementById('upcoming-events-btn');
    const pastBtn = document.getElementById('past-events-btn');
    const createBtn = document.getElementById('create-event-btn');
    const createForm = document.getElementById('create-event-form');
    const eventForm = document.getElementById('event-form');
    const cancelBtn = document.getElementById('cancel-create');
    
    if (upcomingBtn) {
        upcomingBtn.addEventListener('click', async () => {
            const events = await fetchUpcomingEvents();
            displayEvents(events, 'events-container');
            if (createForm) createForm.style.display = 'none';
        });
    }
    
    if (pastBtn) {
        pastBtn.addEventListener('click', async () => {
            const events = await fetchPastEvents();
            displayEvents(events, 'events-container');
            if (createForm) createForm.style.display = 'none';
        });
    }

    if (createBtn) {
        createBtn.addEventListener('click', () => {
            createForm.style.display = 'block';
            document.getElementById('events-container').innerHTML = '';
        });
    }

    if (cancelBtn) {
        cancelBtn.addEventListener('click', () => {
            createForm.style.display = 'none';
            eventForm.reset();
            fetchUpcomingEvents().then(events => {
                displayEvents(events, 'events-container');
            });
        });
    }

    if (eventForm) {
        eventForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const eventData = {
                title: formData.get('title'),
                description: formData.get('description'),
                date: formData.get('date'),
                location: formData.get('location')
            };

            try {
                const response = await createEvent(eventData);
                if (response.status === 'success') {
                    webapp.showPopup({
                        title: 'Успех',
                        message: 'Мероприятие успешно создано!',
                        buttons: [{
                            type: 'ok',
                        }]
                    });
                    e.target.reset();
                    createForm.style.display = 'none';
                    const events = await fetchUpcomingEvents();
                    displayEvents(events, 'events-container');
                }
            } catch (error) {
                webapp.showPopup({
                    title: 'Ошибка',
                    message: 'Не удалось создать мероприятие',
                    buttons: [{
                        type: 'ok',
                    }]
                });
            }
        });
    }

    // Загружаем предстоящие события по умолчанию
    fetchUpcomingEvents().then(events => {
        displayEvents(events, 'events-container');
    });
}); 