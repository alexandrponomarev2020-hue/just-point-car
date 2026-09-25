# Just Point Car — демоверсия первого экрана

Самостоятельный адаптивный HTML/CSS/JS-прототип. Откройте `index.html` или запустите из этой папки `python3 -m http.server 4178 --bind 127.0.0.1` и перейдите на http://127.0.0.1:4178.

Реализованы главный экран, компактная строка услуг, выбор услуги с подготовкой сообщения в Telegram, контакты и мобильное меню. Данные не отправляются автоматически. Прототип не подключён к CRM и не опубликован.

25 сентября 2026 года экран развёрнут к оклейке: владелец студии написал, что сезон полировок заканчивается и до марта они теряют актуальность, а упор нужен на оклейку, при этом химчистки идут круглый год. Поэтому заголовок, описание и порядок услуг построены вокруг бронеплёнки, химчистка стоит третьей, полировка и керамика остались в списке последними.

## Данные и источники

Проверено 25 сентября 2026 года:

- [Яндекс Карты](https://yandex.ru/maps/org/just_point_car/222922385914/): рейтинг 5,0, 56 оценок, 52 отзыва, «Хорошее место 2026», Москва, Талалихина, 41с41, ежедневно 10:00–22:00, +7 985 274-45-10.
- [Канал студии](https://t.me/JPCDetailing): полировка, керамика, химчистка, оклейка полиуретаном; запись через @Justpointcar. В описании канала адрес отличается: 41с40. В демо используется адрес из карточки, расхождение указано в контактах.
- Прайс в Яндекс Картах помечен «Давно не обновлялось», поэтому цены в демо не показаны.
- [Референс 1](https://ru.pinterest.com/pin/50595195809977065/): тёмный BMW и зеркальный кузов.
- [Референс 2](https://ru.pinterest.com/pin/7388786885448908/): тёмная автомобильная композиция и акцент на видах ухода.
- [Референс 3](https://ru.pinterest.com/pin/8655424282361700/): сдержанная фотография процесса полировки.
- [Референс 4](https://ru.pinterest.com/pin/17170042326060570/): отражения на чёрном кузове и студийный свет.

Главный экран собран из настоящей фотографии студии: пост от 5 декабря 2025 года в [канале](https://t.me/JPCDetailing/390) — «Полная оклейка кузова в бронеплёнку», Mercedes-Benz GLC 300, на номере табличка студии. Исходный кадр вертикальный (600 × 800), поэтому для широкого экрана он пересобран в 1536 × 1024: машина стоит справа, слева бокс продолжен растянутой стеной из того же кадра и уведён в темноту под заголовок. Скрипт сборки — `assets/unused/hero-jpc-build.py`.

Прежняя картинка первого экрана (BMW M8, созданная встроенным imagegen) и её промпт убраны в `assets/unused/`: на демо для владельца студии чужая машина читается сразу. В шапке используется оригинальная аватарка Telegram-канала @JPCDetailing, сохранённая локально в `assets/jpc-telegram-logo.jpg`. Шрифты Manrope и Oswald сохранены локально из Google Fonts.

Толщина плёнки в текстах взята из постов студии: 210 микрон Spectroll premium на кузов ([395](https://t.me/JPCDetailing/395), [420](https://t.me/JPCDetailing/420)) и 190 микрон на фары ([89](https://t.me/JPCDetailing/89)). Цены на оклейку в карточке Яндекса нет, поэтому в демо стоимость не показана.

## Промпт прежнего изображения (не используется)

Create one cinematic ultra-premium automotive detailing website hero photograph. Landscape aspect ratio 3:2 at highest quality. Photorealistic black metallic BMW M8 coupe, full vehicle in front three-quarter view, nose angled toward camera and slightly toward the left, positioned in the RIGHT TWO THIRDS of the frame. Low camera angle close to floor, visually powerful wide front, beautiful precise headlights and glossy black kidney grille, silver polished wheel. Car is realistically proportioned and luxuriously finished. It occupies x=33% to 96% and y=32% to 84% of frame. Left third remains very dark and empty for web headline overlay; upper quarter also dark and uncluttered. Professional detailing bay black charcoal walls, overhead architectural long narrow white strip lighting creates crisp flowing white reflections across the hood and fenders. One very subtle warm backlight from far right. Dry satin black concrete floor with subtle soft reflection. Rich charcoal and graphite gray, black, silver whites, no colored neon. Extremely clean, restrained high-end automotive advertising photography, tangible immaculate lacquer, grounded realism. No people, no text, no watermarks, no typography, no license plate text, no UI. This is a website photo asset, not a finished website screenshot.
