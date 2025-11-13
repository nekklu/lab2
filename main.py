import re
import sys
from typing import List, Optional
import requests

# Ищем последовательности цифр с пробелами/дефисами, в сумме ровно 16 цифр.
# (?<!\d) и (?!\d) гарантируют, что до/после нет других цифр (lookarounds).
CARD_PATTERN = re.compile(r'(?<!\d)(?:\d[\s-]?){15}\d(?!\d)')


def is_valid_prefix(cleaned_number: str) -> bool:
    """
    Проверка префиксов для 16-значных карт:
    - Visa: 4...
    - Mastercard: 51-55 и 2221-2720
    - MIR: 2200-2204
    """
    first2 = int(cleaned_number[:2])
    first4 = int(cleaned_number[:4])

    if cleaned_number.startswith('4'):  # Visa
        return True
    if 51 <= first2 <= 55:  # Mastercard)
        return True
    if 2221 <= first4 <= 2720:  # Mastercard (новый диапазон)
        return True
    if 2200 <= first4 <= 2204:  # Mir
        return True
    return False


def luhn_validate(card_number: str) -> bool:
    """
    Классическая Luhn-проверка для 16-значной строки цифр.
    """
    if not card_number.isdigit():
        return False
    
    total = 0
    reversed_digits = list(map(int, card_number[::-1]))
    for i, d in enumerate(reversed_digits):
        if i % 2 == 1:  # Удваиваем каждый второй элемент (индексы 1, 3, 5...)
            dbl = d * 2
            if dbl > 9:
                dbl -= 9
            total += dbl
        else:
            total += d
    return total % 10 == 0


def find_and_validate_card_numbers(text: str) -> List[str]:
    """
    Основная функция: находит кандидатов, проверяет их префикс и алгоритм Луна.
    """
    raw_matches = CARD_PATTERN.findall(text)
    valid_numbers = []
    seen = set()
    for match in raw_matches:
        cleaned = re.sub(r'\D', '', match)  # Оставляем только цифры
        if len(cleaned) != 16:
            continue
        
        # Выполняем обе проверки
        if is_valid_prefix(cleaned) and luhn_validate(cleaned):
            if cleaned not in seen:
                seen.add(cleaned)
                valid_numbers.append(cleaned)
    return valid_numbers


# --- Новые функции для работы с источниками данных ---

def get_content_from_url(url: str) -> Optional[str]:
    """
    Получает текстовое содержимое веб-страницы по URL.

    Args:
        url: URL-адрес веб-страницы.

    Returns:
        Текстовое содержимое страницы или None в случае ошибки.
    """
    try:
        # Устанавливаем заголовок, чтобы имитировать обычный браузер
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()  # Проверка на HTTP ошибки (4xx или 5xx)
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при загрузке URL {url}: {e}", file=sys.stderr)
        return None


def get_content_from_file(filepath: str) -> Optional[str]:
    """
    Считывает содержимое из файла.

    Args:
        filepath: Путь к файлу.

    Returns:
        Содержимое файла или None в случае ошибки.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except (IOError, FileNotFoundError) as e:
        print(f"Ошибка при чтении файла {filepath}: {e}", file=sys.stderr)
        return None


# --- Точка входа в программу ---

def main():
    """
    Главная функция для интерактивного взаимодействия с пользователем.
    """
    print("--- Поиск и валидация номеров банковских карт ---")
    print("Выберите источник данных:")
    print("1. Пользовательский ввод")
    print("2. Веб-страница (по URL)")
    print("3. Локальный файл")

    choice = input("Ваш выбор (1-3): ")
    content = None

    if choice == '1':
        content = input("Введите текст для поиска номеров карт:\n")
    elif choice == '2':
        url = input("Введите URL веб-страницы: ")
        content = get_content_from_url(url)
    elif choice == '3':
        filepath = input("Введите путь к файлу: ")
        content = get_content_from_file(filepath)
    else:
        print("Неверный выбор. Программа завершена.", file=sys.stderr)
        sys.exit(1)

    if content:
        print("\n--- Анализ данных... ---")
        valid_cards = find_and_validate_card_numbers(content)
        if valid_cards:
            print("\nНайдены следующие валидные номера карт:")
            for card in sorted(valid_cards):
                print(f"- {card}")
        else:
            print("\nВалидные номера карт не найдены.")
    else:
        print("\nНе удалось получить данные для анализа.", file=sys.stderr)


if __name__ == '__main__':
    main()