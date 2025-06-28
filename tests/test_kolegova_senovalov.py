import pytest

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver import ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


BASE_URL = "http://localhost:8000"


@pytest.fixture
def driver(request):
    chrome_options = ChromeOptions()

    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    service = ChromeService(executable_path=ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    request.cls.driver = driver
    yield
    driver.quit()


@pytest.mark.usefixtures("driver")
class TestSenovalov:
    def find_element(self, path: str) -> WebElement:
        entity = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    path
                )
            )
        )
        return entity

    def open_app(self, balance: int | float, reserved: int | float):
        url = f"{BASE_URL}/?balance={balance}&reserved={reserved}"
        self.driver.get(url)

    def enable_rubles(self):
        rubles_field = self.find_element('//*[@id="root"]/div/div/div[1]/div[1]/div')
        rubles_field.click()

    def card_input(self, card_number: str) -> str:
        field = self.find_element('//*[@id="root"]/div/div/div[2]/input')
        field.clear()
        field.send_keys(card_number)
        return field.get_attribute("value").replace(" ", "")

    def amount_input(self, amount: str) -> str:
        field = self.find_element('//*[@id="root"]/div/div/div[2]/input[2]')
        field.clear()
        field.send_keys(amount)
        return field.get_attribute("value").replace(" ", "")

    def get_fee_value(self) -> str:
        fee_el = self.find_element('//*[@id="comission"]')
        value = fee_el.text
        return value.replace(" ", "")

    def get_send_button(self) -> WebElement | None:
        try:
            send_button = self.find_element('//*[@id="root"]/div/div/div[2]/button/span')
            return send_button
        except:
            return None

    def send_money(self, button: WebElement):
        button.click()

    def get_exception_message(self) -> WebElement | None:
        try:
            exception_message = self.find_element('//*[@id="root"]/div/div/div[2]/span[2]')
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
        ruble_balance = self.find_element('//*[@id="rub-sum"]')
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
        self.enable_rubles()
        self.card_input("5559000000000000")
        self.amount_input("1000")
        initial_fee = self.get_fee_value()
        assert int(initial_fee) == 100
        exception_message = self.get_exception_message()
        assert exception_message is None
        send_button = self.get_send_button()
        assert send_button is not None
        self.send_money(send_button)

        toast = self.get_toast()
        assert toast is not None
        assert "принят" in toast.lower()
        balance_el = self.get_ruble_balance()
        assert balance_el == 0

    # ---------- TC-012 ---------- #
    def test_amount_with_comma(self):
        self.open_app(balance=10000, reserved=0)
        self.enable_rubles()

        self.card_input("5559000000000000")
        self.amount_input("1234,56")
        fee = self.get_fee_value()
        assert int(fee) == 123

        send_button = self.get_send_button()
        assert send_button is not None
        self.send_money(send_button)
        toast = self.get_toast()
        assert "принят" in toast.lower()

    # ---------- TC-013 ---------- #
    def test_amount_with_thousand_separator(self):
        self.open_app(balance=10000, reserved=0)
        self.enable_rubles()

        self.card_input("5559000000000000")
        self.amount_input("1 000")            # ввод с пробелом
        amount_val = self.amount_input("1 000")
        assert amount_val == "1000"

        send_button = self.get_send_button()
        assert send_button is not None
        self.send_money(send_button)
        assert "принят" in self.get_toast().lower()

    # ---------- TC-014 ---------- #
    def test_amount_more_than_two_decimals(self):
        self.open_app(balance=10000, reserved=0)
        self.enable_rubles()

        self.card_input("5559000000000000")
        amount = self.amount_input("1234,567")         # 3 знака после запятой
        assert amount == "1234,567"

        # должно появиться сообщение об ошибке и кнопка стать неактивной
        exception_message = self.get_exception_message()
        assert exception_message is not None

        send_button = self.get_send_button()
        assert send_button is None

    # ---------- TC-015 ---------- #
    def test_float_balance_coma(self):
        """
        Параллельный перевод из двух вкладок:
        1) 2 000 ₽ проходит.
        2) 3 000 ₽ во второй вкладке должен быть отклонён.
        """
        # первая вкладка
        self.driver.get(url=f'{BASE_URL}/?balance=1000,50&reserved=2000')

        ruble_balance = self.get_ruble_balance()
        assert self.is_decimal_string(ruble_balance) is True
        assert float(ruble_balance) == 1000.50

    def test_float_balance_dot(self):
        """
        Параллельный перевод из двух вкладок:
        1) 2 000 ₽ проходит.
        2) 3 000 ₽ во второй вкладке должен быть отклонён.
        """
        self.driver.get(url=f'{BASE_URL}/?balance=1000.50&reserved=2000')

        ruble_balance = self.get_ruble_balance()
        assert self.is_decimal_string(ruble_balance) is True
        assert float(ruble_balance) == 1000.50
