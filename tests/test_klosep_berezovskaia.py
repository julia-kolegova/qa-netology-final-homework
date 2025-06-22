import unittest

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver import ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class TestBerezovskaia(unittest.TestCase):
    def setUp(self) -> None:
        chrome_options = ChromeOptions()

        chrome_options.add_argument("--window-size=1920,1080")
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-infobars")
        # chrome_options.add_argument("--no-sandbox")
        # chrome_options.add_argument("--disable-dev-shm-usage")

        service = ChromeService(executable_path=ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        # self.driver.implicitly_wait(60)

    def tearDown(self) -> None:
        self.driver.quit()

    def find_element(self, path: str) -> WebElement:
        entity = WebDriverWait(self.driver, 60).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    path
                )
            )
        )
        return entity

    def enable_rubles(self):
        rubles_field = self.find_element('//*[@id="root"]/div/div/div[1]/div[1]/div')
        rubles_field.click()

    def enable_dollars(self):
        rubles_field = self.find_element('//*[@id="root"]/div/div/div[1]/div[2]/div')
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
            send_button = self.find_element( '//*[@id="root"]/div/div/div[2]/button/span')
            return send_button
        except:
            return None

    def get_exception_message(self) -> WebElement | None:
        try:
            exception_message = self.find_element('//*[@id="root"]/div/div/div[2]/span[2]')
            return exception_message
        except:
            return None

    def test_card_number_length(self):
        self.driver.get(url='http://localhost:8000/?balance=33000&reserved=2000')
        self.enable_rubles()
        value = self.card_input("12345678901234567")
        self.assertLessEqual(len(value), 16, "Card number accepts more then 16 digits")

    def test_check_negative_amount(self):
        self.driver.get(url='http://localhost:8000/?balance=33000&reserved=2000')
        self.enable_rubles()
        self.card_input("1111111111111111")
        self.amount_input("-100")
        send_button = self.get_send_button()
        exception_message = self.get_exception_message()
        self.assertIsNone(send_button, "The send button should not exist")
        self.assertIsNotNone(exception_message, "An error about an invalid transaction should be displayed")

    def test_zero_amount(self):
        self.driver.get(url='http://localhost:8000/?balance=33000&reserved=2000')
        self.enable_rubles()
        self.card_input("1111111111111111")
        self.amount_input("0")
        send_button = self.get_send_button()
        exception_message = self.get_exception_message()
        self.assertIsNone(send_button, "The send button should not exist")
        self.assertIsNotNone(exception_message, "An error about an invalid transaction should be displayed")

    def test_dollar_transaction_amount_more_than_the_amount_on_the_account(self):
        self.driver.get(url='http://localhost:8000/?balance=33000&reserved=2000')
        self.enable_dollars()
        self.card_input("1111111111111111")
        self.amount_input("9000")
        send_button = self.get_send_button()
        exception_message = self.get_exception_message()
        self.assertIsNone(send_button, "The send button should not exist")
        self.assertIsNotNone(exception_message, "An error about an invalid transaction should be displayed")

    def test_evro_transaction_amount_more_than_the_amount_on_the_account(self):
        self.driver.get(url='http://localhost:8000/?balance=33000&reserved=2000')
        self.enable_evro()
        self.card_input("1111111111111111")
        self.amount_input("5000")
        send_button = self.get_send_button()
        exception_message = self.get_exception_message()
        self.assertIsNone(send_button, "The send button should not exist")
        self.assertIsNotNone(exception_message, "An error about an invalid transaction should be displayed")
