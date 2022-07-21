import asyncio
import json
import logging
import pyotp
import pyppeteer

from .coned import Coned, Config, CONED_LOGIN_URL, CONED_USAGE_URL
from .reading import Reading


class Pyppeteer(Coned):
    def __init__(self, config: Config):
        super().__init__(config)

    async def __ainit__(self):
        browser_launch_config = {
            "defaultViewport": {"width": 1920, "height": 1080},
            "dumpio": False,
            "args": ["--no-sandbox"],
        }
        browser = await pyppeteer.launch(browser_launch_config)
        self.page = await browser.newPage()

    async def save_screenshot(self, filename: str):
        await self.page.screenshot(path=filename)

    async def login(self):
        await self.page.goto(CONED_LOGIN_URL, {"waitUntil": "domcontentloaded"})
        await self.page.querySelector("#form-login-email")
        logging.info("Authenticating...")

        await self.page.type("#form-login-email", self.cfg.user)
        await self.page.type("#form-login-password", self.cfg.password)
        await self.page.click(".submit-button"),

        mfa_form = await fetch_element(
            self.page, ".js-login-new-device-form-selector:not(.hidden)"
        )
        if mfa_form is None:
            logging.error("Never got MFA prompt. Aborting!")
            return

        logging.info("Entering MFA code...")
        mfa = await fetch_element(self.page, "#form-login-mfa-code")
        mfa_code = pyotp.TOTP(self.cfg.totp).now()
        await mfa.type(mfa_code)
        await asyncio.gather(
            self.page.waitForNavigation(),
            self.page.click(".js-login-new-device-form .button"),
        )

        logging.info("Pausing for auth...")
        await self.page.waitFor(5000)

    async def get_usage(self) -> list[Reading]:
        logging.info("Accessing usage page to trigger opower auth...")
        await self.page.goto(CONED_USAGE_URL)
        await self.page.waitFor(5000)

        logging.info("Dismissing What's new? popup...")
        try:
            close_button = await fetch_element(self.page, ".popup__button-cta")
            await close_button.click()
        except ElementNotFound:
            pass

        logging.info("Fetching readings JSON...")
        url = self.opower_usage_url
        await self.page.goto(url)
        await self.save_screenshot("screenshots/loggedin.png")

        data_elem = await self.page.querySelector("pre")
        raw_data = await self.page.evaluate("(el) => el.textContent", data_elem)
        data = json.loads(raw_data)

        # await self.browser.close()
        logging.info("Done!")

        return data


class ElementNotFound(Exception):
    pass


async def fetch_element(page, selector, max_tries=10):
    tries = 0
    el = None
    while el is None and tries < max_tries:
        el = await page.querySelector(selector)
        await page.waitFor(1000)

    if el is None:
        raise ElementNotFound

    return el
