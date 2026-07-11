from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from app.config.settings import HEADLESS, TIMEOUT, USER_AGENT
from app.utils.logger import logger


class BrowserManager:
    """
    Encapsula toda la lógica de Playwright.
    Solo esta clase puede abrir o cerrar el navegador.
    """

    def __init__(self):
        self.playwright = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None

    async def start(self):
        logger.info("Iniciando navegador...")

        self.playwright = await async_playwright().start()

        self.browser = await self.playwright.chromium.launch(
            headless=HEADLESS
        )

        self.context = await self.browser.new_context(
            user_agent=USER_AGENT
        )

        logger.info("Navegador iniciado correctamente.")

    async def new_page(self) -> Page:
        """
        Devuelve una nueva pestaña lista para navegar.
        """

        page = await self.context.new_page()

        page.set_default_timeout(TIMEOUT)

        return page

    async def close(self):
        logger.info("Cerrando navegador...")

        if self.browser:
            await self.browser.close()

        if self.playwright:
            await self.playwright.stop()

        logger.info("Navegador cerrado.")