import pyotp
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

CONED_LOGIN_URL = "https://www.coned.com/en/login"
CONED_USAGE_URL = (
    "https://www.coned.com/en/accounts-billing/dashboard?tab1=billingandusage-1"
)
OPOWER_USAGE_URL = f"https://cned.opower.com/ei/edge/apis/cws-real-time-ami-v1/cws/cned/accounts/{OPOWER_ACCOUNT_ID}/meters/{OPOWER_METER}/usage"

DEFAULT_TIMEOUT_SEC = 10


class Coned:
    def __init__(self, user, password, totp, account_id, meter):
        self.user = user
        self.password = password
        self.totp = totp
        self.account_id = account_id
        self.meter = meter

        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        self.driver = webdriver.Chrome(chrome_options=options)

    def login(self):
        # Try to load the Billing and Usage page. If we find ourselves at the
        # login page, then we need to login. If not, we have nothing to do.
        driver.get(CONED_USAGE_URL)
        if not self.at_login_page():
            return

        # Submit the login form
        driver.find_element_by_id("form-login-email").send_keys(self.user)
        driver.find_element_by_id("form-login-password").send_keys(self.password)
        driver.find_element_by_id("form-login-password").submit()

        # Wait for login form to get to 2FA step
        tfa_field = WebDriverWait(driver, DEFAULT_TIMEOUT_SEC).until(
            EC.element_to_be_clickable((By.ID, "form-login-mfa-code"))
        )

        # Submit 2FA form
        totp = pyotp.TOTP(self.totp)
        tfa_field.send_keys(totp.now())
        tfa_field.submit()

        # Wait for dashboard to appear
        WebDriverWait(driver, DEFAULT_TIMEOUT_SEC).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@data-value='overview']"))
        )

    def get_usage(self):
        driver.get(CONED_USAGE_URL)

        # Go to "real time usage"
        rtu_button = WebDriverWait(driver, DEFAULT_TIMEOUT_SEC).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[@data-value='sectionRealTimeData']")
            )
        )
        rtu_button.click()

        # Wait for "Download your real-time usage" in the iframe to appear so that it
        # triggers authentication on the opower side
        iframe = WebDriverWait(driver, DEFAULT_TIMEOUT_SEC).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[@id='sectionRealTimeData']/iframe")
            )
        )
        driver.switch_to.frame(iframe)
        download_button = WebDriverWait(driver, DEFAULT_TIMEOUT_SEC).until(
            EC.element_to_be_clickable((By.ID, "download-link"))
        )

        # Get the usage from opower
        driver.get(OPOWER_USAGE_URL)
        return driver.find_element_by_tag_name("body").text

    # at_login_page returns whether the driver is at the ConEd login page by
    # looking for the login form.
    def at_login_page(self):
        try:
            driver.find_element_by_id("form-login-email")
            return True
        except NoSuchElementException:
            return False
