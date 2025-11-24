from typing import List, Dict, Any, Tuple, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Маппинг ISO кодов на названия стран
COUNTRY_NAMES = {
    "US": "США",
    "GB": "Великобритания",
    "RU": "Россия",
    "FR": "Франция",
    "DE": "Германия",
    "IT": "Италия",
    "ES": "Испания",
    "CA": "Канада",
    "AU": "Австралия",
    "JP": "Япония",
    "KR": "Южная Корея",
    "CN": "Китай",
    "IN": "Индия",
    "BR": "Бразилия",
    "MX": "Мексика",
}


def format_countries(country_codes: List[str]) -> str:
    """Форматирование списка ISO кодов стран в читаемый формат"""
    if not country_codes:
        return "Неизвестно"

    # Преобразуем коды в названия
    # Показываем максимум 3 страны
    names = [COUNTRY_NAMES.get(code, code) for code in country_codes[:3]]
    result = ", ".join(names)

    if len(country_codes) > 3:
        result += f" и ещё {len(country_codes) - 3}"

    return result


def format_search_result(result: Dict[str, Any]) -> str:
    """
    Форматирование одного результата поиска для отображения в Telegram

    Args:
        result: Словарь с данными о фильме/сериале

    Returns:
        Отформатированная строка для сообщения
    """
    title = result.get("title", "Без названия")
    original_title = result.get("original_title", "")
    overview = result.get("overview", "Описание отсутствует")
    release_date = result.get("release_date", "Неизвестно")
    vote_average = result.get("vote_average", 0)
    vote_count = result.get("vote_count", 0)
    content_type = "🎥 Фильм" if result.get("type") == "movie" else "📺 Сериал"

    # Обрезаем описание до 250 символов для более компактного отображения
    if len(overview) > 250:
        overview = overview[:247] + "..."

    # Форматируем дату (оставляем только год, если есть)
    year = "Неизвестно"
    if release_date and release_date != "Неизвестно":
        try:
            year = release_date.split("-")[0]
        except:
            year = release_date

    # Форматируем рейтинг
    rating_text = ""
    if vote_average > 0 and vote_count > 0:
        rating_text = f"⭐ {vote_average:.1f}/10 ({vote_count} оценок)"

    # Формируем текст
    text_parts = [
        f"{content_type}",
        f"📌 {title}",
    ]

    if original_title and original_title != title:
        text_parts.append(f"🇬🇧 {original_title}")

    if year != "Неизвестно":
        text_parts.append(f"📅 {year}")

    if rating_text:
        text_parts.append(rating_text)

    text_parts.append(f"\n{overview}")

    return "\n".join(text_parts)


def format_results_list(results: List[Dict[str, Any]], max_results: int = 10) -> List[str]:
    """
    Форматирование списка результатов для отображения в Telegram
    Разбивает результаты на несколько сообщений, если они слишком длинные

    Args:
        results: Список результатов поиска
        max_results: Максимальное количество результатов для отображения

    Returns:
        Список отформатированных строк (каждая не превышает 4096 символов)
    """
    if not results:
        return ["😔 К сожалению, ничего не найдено. Попробуйте изменить параметры поиска."]

    # Ограничиваем количество результатов
    display_results = results[:max_results]

    formatted_results = []
    for i, result in enumerate(display_results, 1):
        formatted_result = format_search_result(result)
        formatted_results.append(f"{i}. {formatted_result}")

    header = f"🎬 Найдено результатов: {len(results)}\n\n"

    # Разбиваем на части, если сообщение слишком длинное
    # Лимит Telegram - 4096 символов, оставляем запас
    MAX_MESSAGE_LENGTH = 4000
    messages = []
    current_message = header

    for formatted_result in formatted_results:
        # Проверяем, поместится ли следующий результат
        test_message = current_message + formatted_result + "\n\n"

        if len(test_message) > MAX_MESSAGE_LENGTH and current_message != header:
            # Сохраняем текущее сообщение и начинаем новое
            messages.append(current_message.rstrip())
            current_message = formatted_result + "\n\n"
        else:
            current_message = test_message

    # Добавляем последнее сообщение
    if current_message != header:
        messages.append(current_message.rstrip())
    else:
        # Если даже header не поместился (маловероятно, но на всякий случай)
        messages.append(header.rstrip())

    return messages


def format_single_result(result: Dict[str, Any], current_index: int, total_count: int) -> Tuple[str, str, InlineKeyboardMarkup]:
    """
    Форматирование одного результата для отображения с постером и навигацией

    Args:
        result: Словарь с данными о фильме/сериале
        current_index: Текущий индекс (0-based)
        total_count: Общее количество результатов

    Returns:
        Кортеж: (текст сообщения, URL постера, клавиатура навигации)
    """
    title = result.get("title", "Без названия")
    original_title = result.get("original_title", "")
    overview = result.get("overview", "Описание отсутствует")
    release_date = result.get("release_date", "Неизвестно")
    vote_average = result.get("vote_average", 0)
    vote_count = result.get("vote_count", 0)
    content_type = "🎥 Фильм" if result.get("type") == "movie" else "📺 Сериал"
    poster_url = result.get("poster_url", "")

    # Форматируем дату (оставляем только год, если есть)
    year = "Неизвестно"
    if release_date and release_date != "Неизвестно":
        try:
            year = release_date.split("-")[0]
        except:
            year = release_date

    # Форматируем рейтинг
    rating_text = ""
    if vote_average > 0 and vote_count > 0:
        rating_text = f"⭐ {vote_average:.1f}/10 ({vote_count} оценок)"

    # Формируем базовую часть текста (без описания)
    base_parts = [
        f"🎬 Найдено результатов: {total_count}",
        f"📄 Результат {current_index + 1} из {total_count}",
        "",
        f"{content_type}",
        f"📌 {title}",
    ]

    if original_title and original_title != title:
        base_parts.append(f"🇬🇧 {original_title}")

    if year != "Неизвестно":
        base_parts.append(f"📅 {year}")

    if rating_text:
        base_parts.append(rating_text)

    # Формируем полный текст и проверяем длину
    # Лимит для caption в Telegram - 1024 символа, оставляем запас
    MAX_CAPTION_LENGTH = 1000

    # Сначала формируем текст с полным описанием
    full_text = "\n".join(base_parts) + f"\n{overview}"

    # Если текст слишком длинный, обрезаем описание
    if len(full_text) > MAX_CAPTION_LENGTH:
        base_text = "\n".join(base_parts)
        base_length = len(base_text)
        available_length = MAX_CAPTION_LENGTH - base_length - 1  # -1 для "\n"

        if available_length > 20:  # Минимум 20 символов для описания
            overview = overview[:available_length - 3] + "..."
            text_parts = base_parts + [f"\n{overview}"]
        else:
            # Если места очень мало, оставляем только базовую часть
            text_parts = base_parts
    else:
        text_parts = base_parts + [f"\n{overview}"]

    # Создаём клавиатуру навигации
    keyboard_rows = []

    # Первая строка: кнопки навигации
    nav_buttons = []

    # Кнопка "Назад" (влево)
    if current_index > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="result_prev"
        ))

    # Кнопка "Вперёд" (вправо)
    if current_index < total_count - 1:
        nav_buttons.append(InlineKeyboardButton(
            text="Вперёд ▶️",
            callback_data="result_next"
        ))

    if nav_buttons:
        keyboard_rows.append(nav_buttons)

    # Вторая строка: кнопка "Завершить поиск"
    keyboard_rows.append([
        InlineKeyboardButton(
            text="✅ Завершить поиск",
            callback_data="finish_search"
        )
    ])

    # Третья строка: кнопка "Отмена"
    keyboard_rows.append([
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel_search"
        )
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

    return "\n".join(text_parts), poster_url, keyboard


def format_result_for_callback(result: Dict[str, Any]) -> str:
    """
    Форматирование результата для callback (более компактный формат)

    Args:
        result: Словарь с данными о фильме/сериале

    Returns:
        Компактная строка для callback
    """
    title = result.get("title", "Без названия")
    content_type = "🎥" if result.get("type") == "movie" else "📺"
    release_date = result.get("release_date", "")
    year = ""
    if release_date and release_date != "Неизвестно":
        try:
            year = release_date.split("-")[0]
        except:
            year = release_date

    return f"{content_type} {title} ({year})" if year else f"{content_type} {title}"


# Маппинг названий провайдеров для русского языка
PROVIDER_NAMES = {
    "Netflix": "Netflix",
    "Okko": "Okko",
    "IVI": "IVI",
    "Kinopoisk HD": "Кинопоиск HD",
    "more.tv": "more.tv",
    "Premier": "Premier",
    "Megogo": "Megogo",
    "Apple TV": "Apple TV",
    "YouTube": "YouTube",
    "YouTube Premium": "YouTube Premium",
    "Amazon Prime Video": "Amazon Prime Video",
    "Disney Plus": "Disney+",
    "HBO Max": "HBO Max",
    "START": "START",
    "Amediateka": "Amediateka",
}


def format_watch_providers(providers_data: Optional[Dict[str, Any]], title: str) -> Tuple[str, InlineKeyboardMarkup]:
    """
    Форматирование списка стриминговых сервисов для отображения

    Args:
        providers_data: Словарь с данными о провайдерах из TMDB API
        title: Название фильма/сериала

    Returns:
        Кортеж: (текст сообщения, клавиатура с кнопками)
    """
    if not providers_data:
        text = (
            f"📺 {title}\n\n"
            "😔 К сожалению, информация о доступных стриминговых сервисах не найдена."
        )
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text="◀️ Вернуться к поиску", callback_data="back_to_search")],
                [InlineKeyboardButton(
                    text="🏠 В главное меню", callback_data="back_to_main")]
            ]
        )
        return text, keyboard

    text_parts = [f"📺 {title}", "", "🎬 Где посмотреть:"]

    # Подписки (flatrate)
    flatrate = providers_data.get("flatrate", [])
    if flatrate:
        text_parts.append("\n📱 Подписки:")
        provider_names = []
        for provider in flatrate[:10]:  # Ограничиваем до 10 сервисов
            provider_name = provider.get("provider_name", "")
            display_name = PROVIDER_NAMES.get(provider_name, provider_name)
            provider_names.append(display_name)
        text_parts.append(" • " + "\n • ".join(provider_names))

    # Аренда (rent)
    rent = providers_data.get("rent", [])
    if rent:
        text_parts.append("\n💰 Аренда:")
        provider_names = []
        for provider in rent[:10]:
            provider_name = provider.get("provider_name", "")
            display_name = PROVIDER_NAMES.get(provider_name, provider_name)
            provider_names.append(display_name)
        text_parts.append(" • " + "\n • ".join(provider_names))

    # Покупка (buy)
    buy = providers_data.get("buy", [])
    if buy:
        text_parts.append("\n💳 Покупка:")
        provider_names = []
        for provider in buy[:10]:
            provider_name = provider.get("provider_name", "")
            display_name = PROVIDER_NAMES.get(provider_name, provider_name)
            provider_names.append(display_name)
        text_parts.append(" • " + "\n • ".join(provider_names))

    # Если нет ни одного провайдера
    if not flatrate and not rent and not buy:
        text_parts.append(
            "\n😔 К сожалению, информация о доступных сервисах не найдена.")

    # Добавляем ссылку на TMDB, если есть
    link = providers_data.get("link", "")
    if link:
        text_parts.append(f"\n🔗 Подробнее: {link}")

    text = "\n".join(text_parts)

    # Создаём клавиатуру
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="◀️ Вернуться к поиску", callback_data="back_to_search")],
            [InlineKeyboardButton(text="🏠 В главное меню",
                                  callback_data="back_to_main")]
        ]
    )

    return text, keyboard
