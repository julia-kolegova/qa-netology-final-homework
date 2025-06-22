import unittest

from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class TestKolegova(unittest.TestCase):
    def setUp(self) -> None:
        chrome_options = ChromeOptions()

        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        service = ChromeService(executable_path=ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.implicitly_wait(60)

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
        dollars_field = self.find_element('//*[@id="root"]/div/div/div[1]/div[2]/div')
        dollars_field.click()

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

    def get_fee(self) -> str:
        fee_el = self.find_element('//*[@id="comission"]')
        value = fee_el.text
        return value.replace(" ", "")

    def get_toast(self) -> str:
        driver = self.driver
        alert = driver.switch_to.alert
        alert_text = alert.text
        alert.accept()
        return alert_text

    def test_tc_001_commission_recalculation(self):
        card = "5559000000000000"
        money_1 = "5000"
        money_2 = "1000"
        self.driver.get("http://localhost:8000/?balance=33000&reserved=1000")
        self.enable_rubles()

        self.card_input(card)
        self.amount_input(money_1)
        self.assertTrue(self.get_fee().startswith("500"))

        button = self.get_send_button()
        self.send_money(button)
        self.assertIn("принят", self.get_toast().lower())

        self.amount_input(money_2)
        self.assertTrue(self.get_fee().startswith("100"))

    def test_tc_002_success_message_amount_and_fee(self):
        card = "4111111111111111"
        money = "1000"

        self.driver.get("http://localhost:8000/?balance=33000&reserved=1000")
        self.enable_rubles()

        self.card_input(card)
        self.amount_input(money)
        send_button = self.get_send_button()
        self.send_money(send_button)

        toast = self.get_toast()
        self.assertEqual(f"Перевод {money} ₽ на карту {card} принят банком!", toast)

    def test_tc_003_usd_overdraft_validation(self):
        card = "4000123456789000"
        money = "3111"

        self.driver.get("http://localhost:8000/?balance=33000&reserved=1000")
        self.enable_dollars()
        self.card_input(card)
        self.amount_input(money)

        send_button = self.get_send_button()
        exception_message = self.get_exception_message()
        self.assertIsNone(send_button, "The send button should not exist")
        self.assertIsNotNone(exception_message, "An error about an invalid transaction should be displayed")

    def test_tc_004_commission_floor_small_amount(self):
        card = "1234567890901122"
        money = "99"

        self.driver.get("http://localhost:8000/?balance=33000&reserved=1000")

        self.enable_rubles()
        self.card_input(card)
        self.amount_input(money)
        self.assertTrue(self.get_fee().startswith("9"))

    def test_tc_005_card_number_length_validation(self):
        self.driver.get("http://localhost:8000/?balance=33000&reserved=1000")
        self.enable_rubles()

        for card, should_pass in [
            ("123456789012", False),
            ("123456789012345678", False),
            ("5559000000000000", True)
        ]:
            self.card_input(card)
            button = self.get_send_button()
            if should_pass:
                self.assertIsNotNone(button, msg=f"Card {card} should be accepted")
            else:
                self.assertIsNone(button, msg=f"Card {card} should be rejected")
