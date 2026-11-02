from html.parser import HTMLParser


class DescriptionParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

        self.ignored_tag = None

    def handle_data(self, data):
        if self.ignored_tag is None:
            self.parts.append(data)

    def handle_starttag(self, tag, attrs):
        if self.ignored_tag is not None:
            return
        if tag in ("script", "style"):
            self.ignored_tag = tag
            return
        if tag == "br":
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if self.ignored_tag is not None:
            if tag == self.ignored_tag:
                self.ignored_tag = None
            return
        if tag in ("p", "li"):
            self.parts.append("\n")


def description_to_text(html):
    parser = DescriptionParser()
    parser.feed(html)
    parser.close()
    return "".join(parser.parts).strip()
