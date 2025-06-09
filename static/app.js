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

// Функция для отображения событий
function displayEvents(events, containerId) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';

    if (events.length === 0) {
        container.innerHTML = '<p class="no-events">Мероприятий не найдено</p>';
        return;
    }

    events.forEach(event => {
        const date = new Date(event.date).toLocaleDateString('ru-RU');
        const card = document.createElement('div');
        card.className = 'event-card';
        card.innerHTML = `
            <h3>${event.title}</h3>
            <p class="event-date">${date}</p>
            <p>${event.description}</p>
            ${event.location ? `<p>📍 ${event.location}</p>` : ''}
        `;
        container.appendChild(card);
    });
}

// Обработчики кнопок
document.addEventListener('DOMContentLoaded', () => {
    const upcomingBtn = document.getElementById('upcoming-events-btn');
    const pastBtn = document.getElementById('past-events-btn');
    
    if (upcomingBtn) {
        upcomingBtn.addEventListener('click', async () => {
            const events = await fetchUpcomingEvents();
            displayEvents(events, 'events-container');
        });
    }
    
    if (pastBtn) {
        pastBtn.addEventListener('click', async () => {
            const events = await fetchPastEvents();
            displayEvents(events, 'events-container');
        });
    }

    // Загружаем предстоящие события по умолчанию
    if (document.getElementById('events-container')) {
        fetchUpcomingEvents().then(events => {
            displayEvents(events, 'events-container');
        });
    }
}); 