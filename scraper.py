import json
import re
from urllib.parse import urljoin

from playwright.sync_api import Page, sync_playwright

BASE_URL = "https://ekantipur.com"


def scrape_entertainment(page: Page) -> list[dict]:

    page.goto(f"{BASE_URL}/entertainment")
    page.wait_for_selector(".category-wrapper .category")

    # the category label is only on the page header, not inside each card.
    # every article on this listing belong to that single category
    category_element = page.query_selector(".category-name p a")
    category_text = category_element.text_content() if category_element else None
    category = (
        category_text.strip() if category_text and category_text.strip() else None
    )

    articles = []
    cards = page.query_selector_all(".category-wrapper .category")[:5]

    for card in cards:
        try:
            title_element = card.query_selector("h2 a")
            title_text = title_element.text_content() if title_element else None
            title = title_text.strip() if title_text and title_text.strip() else None

            image_element = card.query_selector("img")
            image_url = None

            if image_element:
                image_url = image_element.get_attribute("data-src")

                if not image_url:
                    image_url = image_element.get_attribute("src")

                    image_url = urljoin(BASE_URL, image_url)

            author_element = card.query_selector(".author-name p a")
            author_text = author_element.text_content() if author_element else None
            author = (
                author_text.strip() if author_text and author_text.strip() else None
            )

            articles.append(
                {
                    "title": title,
                    "image_url": image_url,
                    "category": category,
                    "author": author,
                }
            )
        except Exception:
            continue

    return articles


def scrape_cartoon(page: Page) -> dict:
    import re
    from urllib.parse import urljoin

    base_url = "https://ekantipur.com"
    empty_result = {
        "title": None,
        "image_url": None,
        "author": None,
    }

    page.goto(base_url, wait_until="domcontentloaded")
    page.wait_for_selector(
        "section.e-section .swiper-slide.c-slide",
        state="attached",
    )

    slide = page.query_selector("section.e-section .swiper-slide.c-slide")

    if not slide:
        return empty_result

    image = slide.query_selector("img")

    if not image:
        return empty_result

    image_url = image.get_attribute("data-src")

    if not image_url:
        image_url = image.get_attribute("src")

    image_url = urljoin(base_url, image_url)

    alt_text = image.get_attribute("alt")
    title = alt_text.strip() if alt_text and alt_text.strip() else None

    author = None
    if title:
        match = re.fullmatch(r"(.+?को\s*कार्टुन)", title)
        if match:
            author = match.group(1).strip()
            author = re.sub(r"को\s*कार्टुन$", "", author).strip()

    return {
        "title": title,
        "image_url": image_url,
        "author": author,
    }


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        entertainment_news = scrape_entertainment(page)
        cartoon_of_the_day = scrape_cartoon(page)

        output = {
            "entertainment_news": entertainment_news,
            "cartoon_of_the_day": cartoon_of_the_day,
        }

        # ensure_ascii=False so Devanagari is written as readable characters
        with open("output.json", "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        browser.close()

        print(f"Wrote {len(entertainment_news)} entertainment articles.")


if __name__ == "__main__":
    main()
