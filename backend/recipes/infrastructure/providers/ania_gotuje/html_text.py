from bs4 import BeautifulSoup


def read_plain_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    return " ".join(soup.get_text(separator=" ", strip=True).split())


def read_paragraphs(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    paragraphs: list[str] = []
    for element in soup.select("p:not(.recipe-info)"):
        text = " ".join(element.get_text(separator=" ", strip=True).split())
        if text:
            paragraphs.append(text)
    return paragraphs
