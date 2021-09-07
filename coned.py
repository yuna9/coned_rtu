import functools
import json

from dateutil.parser import isoparse
import pyotp
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from reading import Reading

CONED_LOGIN_URL = "https://www.coned.com/en/login"
CONED_USAGE_URL = (
    "https://www.coned.com/en/accounts-billing/dashboard?tab1=billingandusage-1"
)

DEFAULT_TIMEOUT_SEC = 10


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


def json_to_readings(usage_json):
    readings = []
    usage = json.loads(usage_json)
    for read in usage["reads"]:
        # Opower gives readings with null value for intervals that don't have data
        # yet, so skip them.
        if read["value"] is None:
            continue

        reading = Reading(
            isoparse(read["startTime"]),
            isoparse(read["endTime"]),
            usage["unit"],
            read["value"],
        )
        readings.append(reading)
    return readings


class Coned:
    def __init__(self, user, password, totp, account_id, meter, maid=""):
        self.user = user
        self.password = password
        self.totp = totp
        self.account_id = account_id
        self.meter = meter
        self.maid = maid

        options = webdriver.ChromeOptions()
        options.add_argument("--headless")

        # this option can sometimes be necessary when running in docker, but
        # can have a negative impact on performance
        # https://stackoverflow.com/a/53970825
        options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(chrome_options=options)

    def opower_usage_url(self):
        return f"https://cned.opower.com/ei/edge/apis/cws-real-time-ami-v1/cws/cned/accounts/{self.account_id}/meters/{self.meter}/usage"  # noqa

    def save_screenshot(self, filename):
        """
        Saves a 1080p screenshot of the page with the given filename in
        the screenshots folder. Doesn't reset the window size.
        """
        path = f"screenshots/{filename}.png"
        self.driver.set_window_size(1920, 1080)
        self.driver.save_screenshot(path)

    @_screenshot_failure
    def login(self):
        # Try to load the Billing and Usage page. If we find ourselves at the
        # login page, then we need to login. If not, we have nothing to do.
        self.driver.get(CONED_USAGE_URL)
        if not self.at_login_page():
            return

        # Submit the login form
        self.driver.find_element_by_id("form-login-email").send_keys(self.user)
        self.driver.find_element_by_id("form-login-password").send_keys(self.password)
        self.driver.find_element_by_id("form-login-password").submit()

        # Wait for login form to get to 2FA step.
        try:
            tfa_field = WebDriverWait(self.driver, DEFAULT_TIMEOUT_SEC).until(
                EC.element_to_be_clickable((By.ID, "form-login-mfa-code"))
            )
        except TimeoutException as e:
            # If it times out, it's probably due to bad credentials.
            if self.is_bad_login():
                raise LoginFailedException
            else:
                raise e

        # Submit 2FA form
        totp = pyotp.TOTP(self.totp)
        tfa_field.send_keys(totp.now())
        tfa_field.submit()

        # Wait for dashboard to appear
        WebDriverWait(self.driver, DEFAULT_TIMEOUT_SEC).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@data-value='overview']"))
        )

        # If prompted to select service address, use maid id to resolve
        try:
            must_select = WebDriverWait(self.driver, 2).until(  # noqa: F841
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//div[contains(@class, 'account-focus__accounts-container')]",
                    )
                )
            )
            account_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(
                    (By.XPATH, f"//button[@data-maid='{self.maid}']")
                )
            )
            account_button.click()
        except TimeoutException:
            pass

    @_screenshot_failure
    def get_usage(self):
        self.driver.get(CONED_USAGE_URL)

        # Go to "real time usage"
        rtu_button = WebDriverWait(self.driver, DEFAULT_TIMEOUT_SEC).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[@data-value='sectionRealTimeData']")
            )
        )
        rtu_button.click()

        # Wait for "Download your real-time usage" in the iframe to appear so
        # that it triggers authentication on the opower side
        iframe = WebDriverWait(self.driver, DEFAULT_TIMEOUT_SEC).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[@id='sectionRealTimeData']/iframe")
            )
        )
        self.driver.switch_to.frame(iframe)
        WebDriverWait(self.driver, DEFAULT_TIMEOUT_SEC).until(
            EC.element_to_be_clickable((By.ID, "download-link"))
        )

        # Get the usage from opower
        self.driver.get(self.opower_usage_url())
        return self.driver.find_element_by_tag_name("body").text

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
        bad_login = self.driver.find_element_by_class_name(
            "login-form__container-error"
        )
        return "you entered does not match our records" in bad_login.text
