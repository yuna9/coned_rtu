import time
import datetime
import functools

import pyotp
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .coned import Coned, Config, CONED_USAGE_URL

DEFAULT_TIMEOUT = 120


class LoginFailedException(Exception):
    pass


def _screenshot_failure(f):
    """Saves a screenshot if an error occurs. Only decorate Coned instance
    functions, because we assume presence of self."""

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            self = args[0]
            self.save_screenshot("error.png")
            raise e

    return wrapper


class Selenium(Coned):
    def __init__(self, config: Config):
        super().__init__(config)

        options = webdriver.ChromeOptions()
        options.add_argument("--headless")

        # this one also solves some crashes sometimes
        # https://stackoverflow.com/a/50725918
        options.add_argument("--no-sandbox")

        # this option can sometimes be necessary when running in docker, but
        # can have a negative impact on performance
        # https://stackoverflow.com/a/53970825
        options.add_argument("--disable-dev-shm-usage")

        self.driver = webdriver.Chrome(chrome_options=options)

    async def save_screenshot(self, filename):
        time = datetime.datetime.now().isoformat()
        path = f"screenshots/{filename}-{time}.png"
        self.driver.set_window_size(1920, 1080)
        self.driver.save_screenshot(path)

    @_screenshot_failure
    async def login(self):
        # Try to load the Billing and Usage page. If we find ourselves at the
        # login page, then we need to login. If not, we have nothing to do.
        self.driver.get(CONED_USAGE_URL)
        if not self.at_login_page():
            return

        # Submit the login form
        self.driver.find_element_by_id("form-login-email").send_keys(self.cfg.user)
        self.driver.find_element_by_id("form-login-password").send_keys(
            self.cfg.password
        )
        self.driver.find_element_by_id("form-login-password").submit()

        # Wait for login form to get to 2FA step.
        try:
            tfa_field = WebDriverWait(self.driver, DEFAULT_TIMEOUT).until(
                EC.element_to_be_clickable((By.ID, "form-login-mfa-code"))
            )
        except TimeoutException as e:
            # If it times out, it's probably due to bad credentials.
            if self.is_bad_login():
                raise LoginFailedException
            else:
                raise e

        # Submit 2FA form
        totp = pyotp.TOTP(self.cfg.totp)
        tfa_field.send_keys(totp.now())
        tfa_field.submit()

        # Wait for dashboard to appear
        WebDriverWait(self.driver, DEFAULT_TIMEOUT).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@data-value='overview']"))
        )

        # If prompted to select service address, use maid id to resolve
        try:
            _ = WebDriverWait(self.driver, 2).until(  # noqa: F841
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//div[contains(@class, 'account-focus__accounts-container')]",
                    )
                )
            )
            account_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(
                    (By.XPATH, f"//button[@data-maid='{self.cfg.maid}']")
                )
            )
            account_button.click()
        except TimeoutException:
            pass

        # If the "What's new?" popup appears, close it
        try:
            close_popup_button = WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//a[contains(@class, 'popup__button-cta')]",
                    )
                )
            )
            close_popup_button.click()
        except TimeoutException:
            pass

    @_screenshot_failure
    async def get_usage(self):
        self.driver.get(CONED_USAGE_URL)

        # Go to "real time usage"
        rtu_button = WebDriverWait(self.driver, DEFAULT_TIMEOUT).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[@data-value='sectionRealTimeData']")
            )
        )
        rtu_button.click()

        # This never takes less than at least 5 seconds.
        time.sleep(5.0)

        # Select custom element that contains the shadow DOM.
        # sdom = WebDriverWait(self.driver, DEFAULT_TIMEOUT).until(
        #     EC.element_to_be_clickable((By.TAG_NAME, "opower-widget-real-time-ami"))
        # )

        # sroot = self.driver.execute_script("return arguments[0].shadowRoot", sdom)
        sroot = self.driver.execute_script(
            'return document.querySelector("opower-widget-real-time-ami").shadowRoot.querySelector("div.usage-export-content").shadowRoot'  # noqa
        )
        print(sroot)

        for _ in range(3):
            # This never takes less than 5 seconds.
            time.sleep(5.0)

            try:
                linkdiv = sroot.find_element_by_class_name("usage-export-content'")
                break
            except NoSuchElementException:
                pass

        print(linkdiv)

        return

        # Wait for "Download your real-time usage" in the iframe to appear so
        # that it triggers authentication on the opower side
        # iframe = WebDriverWait(self.driver, DEFAULT_TIMEOUT).until(
        #     EC.presence_of_element_located(
        #         (By.XPATH, "//*[@id='sectionRealTimeData']")
        #     )
        # )

        self.save_screenshot("wait iframe")

        # link = WebDriverWait(self.driver, DEFAULT_TIMEOUT).until(
        #     EC.element_to_be_clickable(
        #         (iframe.find_element_by_id("download-link"))
        #     )
        # )

        # cookies = self.driver.get_cookies()

        # url = link.get_attribute("href")
        # resp = requests.get(url)

        # Get the usage from opower
        self.driver.get(self.opower_usage_url())
        self.save_screenshot("aaa")
        # return shadow_root.find_element_by_tag_name("body").text
        return

    @_screenshot_failure
    def at_login_page(self):
        """
        at_login_page returns whether the driver is at the ConEd login
        page by looking for the login form.
        """
        try:
            self.driver.find_element_by_id("form-login-email")
            return True
        except NoSuchElementException:
            return False

    @_screenshot_failure
    def is_bad_login(self):
        """
        is_bad_login returns whether there is a failed login indicator
        on the page.
        """
        try:
            bad_login = self.driver.find_element_by_class_name(
                "login-form__container-error"
            )
            return "you entered does not match our records" in bad_login.text
        except NoSuchElementException:
            return False
