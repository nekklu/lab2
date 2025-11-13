
import unittest
import requests
# unittest.mock позволяет "подменять" функции, которые зависят от внешних систем (сеть, файлы).
from unittest.mock import patch, mock_open

import main


# Создаем класс, который будет содержать все наши тесты.
# Он должен наследоваться от unittest.TestCase.
class TestCardValidator(unittest.TestCase):

    def test_luhn_validate(self):
        # Этот тест проверяет функцию luhn_validate.
        print("\n[TEST] Running test_luhn_validate...")

        # --- Проверка на валидных номерах ---
        # self.assertTrue ожидает, что выражение вернет True.
        # Эти номера математически корректны по алгоритму Луна.
        self.assertTrue(main.luhn_validate('4242424242424242'), '#1 Visa valid')
        self.assertTrue(main.luhn_validate('5555555555554444'), '#2 Mastercard valid')
        self.assertTrue(main.luhn_validate('2200601177358396'), '#3 Mir valid')

        # --- Проверка на невалидных номерах ---
        # self.assertFalse ожидает, что выражение вернет False.
        self.assertFalse(main.luhn_validate('4242424242424243'), '#4 Invalid checksum') # Неверная контрольная сумма
        self.assertFalse(main.luhn_validate('12345'), '#5 Invalid length (too short)') # Неверная длина
        self.assertFalse(main.luhn_validate('not a number'), '#6 Not a number') # Не является числом

    def test_is_valid_prefix(self):
        # Этот тест проверяет функцию is_valid_prefix.
        print("\n[TEST] Running test_is_valid_prefix...")

        # --- Проверка на валидных префиксах ---
        self.assertTrue(main.is_valid_prefix('4111111111111111'), '#1 Visa prefix')
        self.assertTrue(main.is_valid_prefix('5111111111111111'), '#2 Mastercard prefix (51)')
        self.assertTrue(main.is_valid_prefix('2200111111111111'), '#3 Mir prefix (2200)')
        self.assertTrue(main.is_valid_prefix('2221111111111111'), '#4 Mastercard new range prefix')

        # --- Проверка на невалидных префиксах ---
        self.assertFalse(main.is_valid_prefix('1111111111111111'), '#5 Invalid prefix (starts with 1)')
        self.assertFalse(main.is_valid_prefix('6111111111111111'), '#6 Invalid prefix (starts with 6)')
        self.assertFalse(main.is_valid_prefix('2205111111111111'), '#7 Invalid Mir prefix (2205)')

    def test_find_and_validate_card_numbers_integration(self):
        # Это интеграционный тест. Он проверяет, как все функции ядра работают вместе.
        print("\n[TEST] Running test_find_and_validate_card_numbers_integration...")
        
        sample_text = """
        Это комплексный текст для проверки.
        Валидная Visa с дефисами: 4242-4242-4242-4242.
        Валидная карта Мир без разделителей: 2200601177358396.
        Невалидный номер (ошибка в сумме): 5555 5555 5555 4443.
        Номер с неверным префиксом: 6011-0000-0000-0000.
        Слишком длинный номер: 4242-4242-4242-42421.
        Текст с дубликатом: 4242-4242-4242-4242.
        """
        
        # Ожидаемый результат: только два уникальных валидных номера.
        expected_cards = ['4242424242424242', '2200601177358396']
        
        # Получаем реальный результат от нашей функции.
        actual_cards = main.find_and_validate_card_numbers(sample_text)
        
        # self.assertCountEqual сравнивает два списка, игнорируя порядок элементов.
        # Это идеально, так как наша функция возвращает уникальные номера в неопределенном порядке.
        self.assertCountEqual(actual_cards, expected_cards, '#1 Complex text processing')

    def test_no_cards_found(self):
        # Проверяем сценарий, когда в тексте нет номеров карт.
        print("\n[TEST] Running test_no_cards_found...")
        text_without_cards = "В этом тексте нет никаких номеров, которые могли бы подойти."
        
        # Ожидаем получить пустой список.
        self.assertEqual(main.find_and_validate_card_numbers(text_without_cards), [], '#1 Text without cards')


    # --- Тесты для функций ввода-вывода (с использованием mock) ---

    # @patch - это "декоратор", который подменяет указанный объект на "мок" (имитацию).
    # Здесь мы подменяем функцию requests.get в нашем модуле main.
    @patch('main.requests.get')
    def test_get_content_from_url_success(self, mock_get):
        # Тестируем успешную загрузку данных с URL.
        # mock_get - это объект-имитация, который передан в наш тест.
        print("\n[TEST] Running test_get_content_from_url_success...")

        # Настраиваем имитацию: когда requests.get будет вызвана, она должна
        # вернуть объект, у которого есть атрибут .text с нужным нам содержимым.
        mock_response = unittest.mock.Mock()
        mock_response.text = "<html><body>Карта: 2200-6011-7735-8396</body></html>"
        mock_get.return_value = mock_response

        # Вызываем нашу реальную функцию. Она вызовет не настоящую requests.get, а нашу имитацию.
        content = main.get_content_from_url("http://example.com")

        # Проверяем, что функция вернула то, что мы "заложили" в имитацию.
        self.assertEqual(content, "<html><body>Карта: 2200-6011-7735-8396</body></html>", '#1 URL success case')

    @patch('main.requests.get')
    def test_get_content_from_url_failure(self, mock_get):
        # Тестируем обработку ошибки при загрузке URL.
        print("\n[TEST] Running test_get_content_from_url_failure...")

        # Настраиваем имитацию так, чтобы она "выбрасывала" исключение, как
        # это сделала бы реальная библиотека requests при ошибке сети.
        mock_get.side_effect = requests.exceptions.RequestException

        # Вызываем нашу функцию. Внутри нее сработает блок try...except.
        content = main.get_content_from_url("http://invalid-url.com")

        # Проверяем, что в случае ошибки функция корректно вернула None.
        self.assertIsNone(content, '#1 URL failure case')

    def test_get_content_from_file_success(self):
        # Тестируем успешное чтение из файла, используя mock_open.
        print("\n[TEST] Running test_get_content_from_file_success...")
        mock_content = "Данные из файла. Карта: 4242-4242-4242-4242"
        
        # patch подменяет встроенную функцию open на имитацию, которая
        # при чтении "возвращает" заранее заданный нами текст mock_content.
        with patch("builtins.open", mock_open(read_data=mock_content)) as mock_file:
            # Вызываем нашу функцию.
            content = main.get_content_from_file("dummy/path.txt")
            
            # Проверяем, что она вернула правильное содержимое.
            self.assertEqual(content, mock_content, '#1 File read success')
            
            # Дополнительно проверяем, что файл был "открыт" с правильными параметрами.
            mock_file.assert_called_with("dummy/path.txt", 'r', encoding='utf-8')

    def test_get_content_from_file_not_found(self):
        # Тестируем обработку ошибки, когда файл не найден.
        print("\n[TEST] Running test_get_content_from_file_not_found...")
        
        # Настраиваем имитацию open так, чтобы она выбрасывала ошибку FileNotFoundError.
        with patch("builtins.open", side_effect=FileNotFoundError):
            content = main.get_content_from_file("non_existent_file.txt")
            
            # Проверяем, что функция вернула None, как и ожидалось.
            self.assertIsNone(content, '#1 File not found case')


# --- Точка входа для запуска тестов ---

# Этот блок позволяет запускать тесты напрямую из командной строки: python test_main.py
if __name__ == '__main__':
    unittest.main()