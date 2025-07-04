import pytest

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver import ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


BASE_URL = "http://localhost:8000/"


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
class TestKlosep:
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

    def get_url(self, url: str):
        self.driver.get(url=url)

    def enable_rubles(self):
        rubles_field = self.find_element('//*[@id="root"]/div/div/div[1]/div[1]/div')
        rubles_field.click()

    def enable_evro(self):
        rubles_field = self.find_element('//*[@id="root"]/div/div/div[1]/div[3]/div')
        rubles_field.click()

    def card_input(self, card_number: str) -> str:
        input_field = self.find_element('//*[@id="root"]/div/div/div[2]/input')
        input_field.send_keys(card_number)
        value = input_field.get_attribute("value")
        return value.replace(" ", "")

    def amount_input(self, amount: str) -> str:
        input_field = self.find_element('//*[@id="root"]/div/div/div[2]/input[2]')
        input_field.clear()
        input_field.send_keys(amount)
        value = input_field.get_attribute("value")
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

    def get_ruble_balance(self) -> str:
        ruble_balance = self.find_element('//*[@id="rub-sum"]')
        value = ruble_balance.text
        value = value.replace("'", "")
        return value

    def get_ruble_reserve(self) -> str:
        ruble_reserve = self.find_element('//*[@id="rub-reserved"]')
        value = ruble_reserve.text
        value = value.replace("'", "")
        return value

    def get_alert(self) -> str:
        driver = self.driver
        alert = driver.switch_to.alert
        alert_text = alert.text
        alert.accept()
        return alert_text

    def test_incorrect_balance_and_reserve(self):
        self.get_url(f"{BASE_URL}?balance=330%1.4&reserved=!")
        ruble_balance = self.get_ruble_balance()
        ruble_reserve = self.get_ruble_reserve()
        assert ruble_balance == "NaN"
        assert ruble_reserve == "NaN"

    def test_reserve_more_then_balance(self):
        self.get_url(url=f'{BASE_URL}?balance=33001&reserved=330014')
        ruble_balance = self.get_ruble_balance()
        ruble_reserve = self.get_ruble_reserve()
        assert int(ruble_reserve) <= int(ruble_balance)

    def test_negative_balance_and_reserve(self):
        self.get_url(url=f'{BASE_URL}?balance=-33001&reserved=-330014')
        ruble_balance = self.get_ruble_balance()
        ruble_reserve = self.get_ruble_reserve()
        assert int(ruble_balance) > 0
        assert int(ruble_reserve) > 0

    def test_evro_transaction_amount_more_than_the_amount_on_the_account(self):
        self.driver.get(url=f'{BASE_URL}?balance=33000&reserved=2000')
        self.enable_evro()
        self.card_input("1111111111111111")
        self.amount_input("1500")
        send_button = self.get_send_button()
        exception_message = self.get_exception_message()
        assert send_button is None
        assert exception_message is not None

    def test_balance_update_after_transaction(self):
        self.driver.get(url=f'{BASE_URL}?balance=33000&reserved=2000')
        ruble_balance_before_transaction = self.get_ruble_balance()
        self.enable_rubles()
        self.card_input("1111111111111111")
        self.amount_input("1000")
        send_button = self.get_send_button()
        self.send_money(button=send_button)
        self.get_alert()
        ruble_balance_after_transaction = self.get_ruble_balance()
        assert ruble_balance_before_transaction > ruble_balance_after_transaction

    def test_amount_start_with_zero(self):
        self.driver.get(url=f'{BASE_URL}?balance=33000&reserved=2000')
        self.enable_rubles()
        self.card_input("1111111111111111")
        self.amount_input("000123")
        send_button = self.get_send_button()
        exception_message = self.get_exception_message()
        assert send_button is None
        assert exception_message is not None
