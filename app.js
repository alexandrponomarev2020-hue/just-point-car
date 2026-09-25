const bookingDialog = document.querySelector('#booking-dialog');
const contactDialog = document.querySelector('#contact-dialog');
const serviceSelect = document.querySelector('#service-select');
const carModel = document.querySelector('#car-model');
const telegramBooking = document.querySelector('#telegram-booking');
const serviceInfo = document.querySelector('#service-info');
const menuToggle = document.querySelector('.menu-toggle');
const mobileMenu = document.querySelector('#mobile-menu');

const services = {
  consult: { name: 'Подбор защиты', description: 'Подскажем, что выгоднее защитить: весь кузов или только зоны риска.' },
  film: { name: 'Оклейка кузова бронеплёнкой', description: 'Полиуретановая плёнка 210 микрон на весь кузов. Стоимость зависит от модели и состояния лака, считаем по фотографиям.' },
  zones: { name: 'Оклейка зон риска', description: 'Защищаем капот, фары, пороги и зеркала, куда чаще всего летят камни из-под колёс.' },
  lights: { name: 'Оклейка фар', description: 'Полиуретан 190 микрон на фары: спасает от пескоструя и мелких сколов, оптика остаётся прозрачной.' },
  interior: { name: 'Химчистка салона', description: 'Глубокая очистка кожи, текстиля и пластика с вниманием к каждой поверхности.' },
  polish: { name: 'Полировка кузова', description: 'Убираем поверхностные дефекты и возвращаем кузову глубину цвета. Объём работ определим после осмотра.' },
  ceramic: { name: 'Керамическое покрытие', description: 'Защищаем подготовленный кузов, усиливаем блеск и облегчаем дальнейший уход.' }
};

function updateMessage() {
  const service = services[serviceSelect.value];
  serviceInfo.textContent = service.description;
  const car = carModel.value.trim();
  const message = `Здравствуйте! Интересует ${service.name.toLowerCase()}.${car ? ` Автомобиль: ${car}.` : ''} Подскажите, пожалуйста, стоимость и ближайшее время для записи.`;
  telegramBooking.href = `https://t.me/Justpointcar?text=${encodeURIComponent(message)}`;
}

function closeMenu() {
  mobileMenu.hidden = true;
  menuToggle.setAttribute('aria-expanded', 'false');
  menuToggle.setAttribute('aria-label', 'Открыть меню');
}

function openDialog(dialog) {
  closeMenu();
  dialog.showModal();
  document.body.classList.add('dialog-open');
}

document.querySelectorAll('[data-booking], [data-service]').forEach(button => {
  button.addEventListener('click', () => {
    serviceSelect.value = button.dataset.service || 'consult';
    updateMessage();
    openDialog(bookingDialog);
  });
});

document.querySelectorAll('[data-contact]').forEach(button => {
  button.addEventListener('click', () => openDialog(contactDialog));
});

document.querySelectorAll('dialog').forEach(dialog => {
  dialog.querySelector('[data-close]').addEventListener('click', () => dialog.close());
  dialog.addEventListener('close', () => document.body.classList.remove('dialog-open'));
  let pointerStartedOutside = false;
  const outside = event => {
    const rect = dialog.getBoundingClientRect();
    return event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom;
  };
  dialog.addEventListener('pointerdown', event => { pointerStartedOutside = outside(event); });
  dialog.addEventListener('click', event => {
    if (pointerStartedOutside && outside(event)) dialog.close();
    pointerStartedOutside = false;
  });
});

menuToggle.addEventListener('click', () => {
  const isOpen = menuToggle.getAttribute('aria-expanded') === 'true';
  mobileMenu.hidden = isOpen;
  menuToggle.setAttribute('aria-expanded', String(!isOpen));
  menuToggle.setAttribute('aria-label', isOpen ? 'Открыть меню' : 'Закрыть меню');
});
mobileMenu.querySelectorAll('a').forEach(link => link.addEventListener('click', closeMenu));
document.addEventListener('keydown', event => { if (event.key === 'Escape') closeMenu(); });
window.matchMedia('(min-width: 901px)').addEventListener('change', event => { if (event.matches) closeMenu(); });
serviceSelect.addEventListener('change', updateMessage);
carModel.addEventListener('input', updateMessage);
document.querySelector('#care-form').addEventListener('submit', event => event.preventDefault());
updateMessage();
