from selectolax.parser import HTMLParser


class Parser:

    def parse(self, html: str) -> HTMLParser:
        """
        Convierte HTML en un árbol navegable.
        """

        return HTMLParser(html)