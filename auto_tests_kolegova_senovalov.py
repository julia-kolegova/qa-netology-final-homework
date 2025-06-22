import unittest
import time

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver import ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement


BASE_URL = "http://localhost:8000"


class TestSenovalov(unittest.TestCase):
    def setUp(self) -> None:
        chrome_options = ChromeOptions()
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-infobars")

        service = ChromeService(executable_path=ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def tearDown(self) -> None:
        self.driver.quit()

    def open_app(self, balance: int | float, reserved: int | float):
        url = f"{BASE_URL}/?balance={balance}&reserved={reserved}"
        self.driver.get(url)

    def enable_rubles(self):
        rubles_field = self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[1]/div[1]/div')
        rubles_field.click()

    def card_input(self, card_number: str) -> str:
        field = self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/input')
        field.clear()
        field.send_keys(card_number)
        return field.get_attribute("value").replace(" ", "")

    def amount_input(self, amount: str) -> str:
        field = self.driver.find_element(
            By.XPATH, '//*[@id="root"]/div/div/div[2]/input[2]'
        )
        field.clear()
        field.send_keys(amount)
        return field.get_attribute("value").replace(" ", "")

    def get_fee_value(self) -> str:
        fee_el = self.driver.find_element(By.XPATH, '//*[@id="comission"]')
        value = fee_el.text
        return value.replace(" ", "")

    def get_send_button(self) -> WebElement | None:
        try:
            send_button = self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/button/span')
            return send_button
        except:
            return None

    def send_money(self, button: WebElement):
        button.click()

    def get_exception_message(self) -> WebElement | None:
        try:
            exception_message = self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/span[2]')
            return exception_message
        except:
            return None

    def get_toast(self) -> str:
        driver = self.driver
        alert = driver.switch_to.alert
        alert_text = alert.text
        alert.accept()
        return alert_text

    def get_ruble_balance(self) -> str:
        ruble_balance = self.driver.find_element(By.XPATH, '//*[@id="rub-sum"]')
        value = ruble_balance.text
        value = value.replace("'", "")
        return value

    def is_decimal_string(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    # ---------- TC-011 ---------- #
    def test_exact_available_balance_transfer(self):
        """
        Баланс 1 100 ₽, перевод 1 000 ₽ + комиссия 100 ₽ = 0 ₽.
        Должно пройти успешно и обнулить баланс.
        """
        self.open_app(balance=1100, reserved=0)
        time.sleep(2)
        self.enable_rubles()
        self.card_input("5559000000000000")
        self.amount_input("1000")
        initial_fee = self.get_fee_value()
        self.assertTrue(int(initial_fee) == 100, "Комиссия не равна 100 ₽")
        time.sleep(1)
        exception_message = self.get_exception_message()
        self.assertIsNone(exception_message)
        send_button = self.get_send_button()
        self.assertIsNotNone(send_button)
        self.send_money(send_button)

        time.sleep(2)
        toast = self.get_toast()
        self.assertIsNotNone(toast)
        self.assertIn("принят", toast.lower())
        balance_el = self.get_ruble_balance()
        self.assertTrue(balance_el == 0, "Баланс должен быть равен 0")

    # ---------- TC-012 ---------- #
    def test_amount_with_comma(self):
        self.open_app(balance=10000, reserved=0)
        time.sleep(2)
        self.enable_rubles()

        self.card_input("5559000000000000")
        self.amount_input("1234,56")
        fee = self.get_fee_value()
        self.assertTrue(int(fee) == 123, "Комиссия должна быть 123 ₽")

        send_button = self.get_send_button()
        self.assertIsNotNone(send_button)
        self.send_money(send_button)
        time.sleep(1)
        toast = self.get_toast()
        self.assertIn("принят", toast.lower())

    # ---------- TC-013 ---------- #
    def test_amount_with_thousand_separator(self):
        self.open_app(balance=10000, reserved=0)
        time.sleep(2)
        self.enable_rubles()

        self.card_input("5559000000000000")
        self.amount_input("1 000")            # ввод с пробелом
        amount_val = self.amount_input("1 000")
        self.assertEqual(amount_val, "1000", "Разделитель тысяч не убран")

        send_button = self.get_send_button()
        self.assertIsNotNone(send_button)
        self.send_money(send_button)
        time.sleep(1)
        self.assertIn("принят", self.get_toast().lower())

    # ---------- TC-014 ---------- #
    def test_amount_more_than_two_decimals(self):
        self.open_app(balance=10000, reserved=0)
        time.sleep(2)
        self.enable_rubles()

        self.card_input("5559000000000000")
        amount = self.amount_input("1234,567")         # 3 знака после запятой
        self.assertEqual(amount, "1234,567")

        # должно появиться сообщение об ошибке и кнопка стать неактивной
        exception_message = self.get_exception_message()
        self.assertIsNotNone(exception_message)

        send_button = self.get_send_button()
        self.assertIsNone(send_button)

    # ---------- TC-015 ---------- #
    def test_float_balance_coma(self):
        """
        Параллельный перевод из двух вкладок:
        1) 2 000 ₽ проходит.
        2) 3 000 ₽ во второй вкладке должен быть отклонён.
        """
        # первая вкладка
        self.driver.get(url='http://localhost:8000/?balance=1000,50&reserved=2000')
        time.sleep(2)

        ruble_balance = self.get_ruble_balance()
        self.assertTrue(self.is_decimal_string(ruble_balance))
        self.assertEqual(float(ruble_balance), 1000.50, "Balance should be a number")

    def test_float_balance_dot(self):
        """
        Параллельный перевод из двух вкладок:
        1) 2 000 ₽ проходит.
        2) 3 000 ₽ во второй вкладке должен быть отклонён.
        """
        # первая вкладка
        self.driver.get(url='http://localhost:8000/?balance=1000.50&reserved=2000')
        time.sleep(2)

        ruble_balance = self.get_ruble_balance()
        self.assertTrue(self.is_decimal_string(ruble_balance))
        self.assertEqual(float(ruble_balance), 1000.50, "Balance should be a number")
