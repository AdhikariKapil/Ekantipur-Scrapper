# Notes - ekantipur-scraper

## 1. Selectors I found

I inspected homepage and entertainment page in DevTools and found:

### Entertainment page - https://ekantipur.com/entertainment

| What | Selector | Notes |
|---|---|---|
| Article card | `.category-wrapper > .category` | 30 cards on the page, we take the first 5 |
| Title | `.category-description h2 a` | text_content() |
| Article URL | same `h2 a` -> `href` | absolute already |
| Image | `.category-image image.lazy` | **real URl is in `data-src`, not `src`** |
| Author | `.author-name p a` | present on all 5 current cards, but site sometimes emits empyt `author.name` (I saw an empty one, so must handle `None`) |
| Category | `.category-name p a` (it is a page header) | value is same for all card |

Things I noticed:
- **Lazy loading.** In View Source, `<img class="lazy" data-src="..."` has no `src` at all. In the DevTools Element tab, `src` is populated by the site's JS after the imagge loads.
- **Category is not per card** I searched the full page source but there is no sub-category inside article card. The only category signal is page header (मनोरञ्जन). So every article on this listing gets `category="मनोरञ्जन"`

### Homepage cartoon — https://ekantipur.com (section near the bottom)

| What | Selector | Notes |
|---|---|---|
| Section | `section.e-section` | contains the cartoon slider |
| Section title | `section.e-section h4 a` | text is `कार्टुन` |
| Today's cartoon | `section.e-section .swiper-slide.c-slide` (first) | first slide is the newest |
| Image | `img.lazy` inside that slide | **`data-src`**, same lazy-loading pattern as above |
| Title / author | `img.lazy[alt]` | alt is inconsistent |

Alt text examples I saw across slides:

- `अविनको कार्टुन` → cartoonist name is embedded (`अविन`).
- `गजब छ बा` → no cartoonist name, just a tagline.
- `कान्तिपुर दैनिकमा आज प्रकाशित कार्टुन` → no name.

So: `title` = alt of the first slide. `author` = parse `(.+?)को कार्टुन` from the alt; if it matches, take the captured name; otherwise `None`.  

## 2. What I asked the AI
I used Github Copilot. 

### Prompt 1
>I am wiriting a playwright script in python. write me one function, dont write the file
Function signature:
def scrape_entertainment(page) -> list[dict]:

It should navigate to https://ekantipur.com/entertainment and return the first 5 articles as a list of dicts with keys: title, image_url, category, author.

Here is the actual html of one article card from that page
<div class="category">
    <div class="category-inner-wrapper">
        <div class="category-description">
            <h2>
                <a href="https://ekantipur.com/entertainment/2026/10/06/former-american-idol-singer-sentenced-to-life-in-prison-for-wifes-murder-31-53.html">पत्नी हत्यामा अमेरिकन आइडलका पूर्व गायकलाई जन्मकैद</a>
            </h2>
            <div class="author-name">
                <p>
                    <a href="https://ekantipur.com/author/author-8839">एपी</a>
                </p>
            </div>
            <p>summary ...</p>
            <div class="time-wrapper"><span>4 MINS READ</span></div>
        </div>
        <div class="category-image">
            <a href="https://ekantipur.com/entertainment/...">
                <figure>
                    <div class="skeleton"></div>
                    <img class="lazy" data-src="https://assets-cdn-api.ekantipur.com/thumb.php?src=https://assets-cdn.ekantipur.com/uploads/source/news/kantipur/2026/third-party/caleb-flynn-06102026054502-1000x0.jpg&w=701&h=0" alt="...">
                </figure>
            </a>
        </div>
    </div>
</div>
The page header carries the category label
<div class="category-name">
    <p><a href="https://ekantipur.com/entertainment">मनोरञ्जन</a></p>
</div>

Requirements:
1. Navigate to the URL and wait for article cards to appear using page.wait_for_selector(".category-wrapper .category").Do not use a fixed time.sleep.
2.Read the category once, ourside the loop, from .category-name p a. Every article on this page belongs to that same category.
3. For each of the first cards:
title->text_content() of h2 a.
image_url->prefer the data-src attribute of img.lazy. Only fallback to src if data-src is missing. The URL may be protocol-relative so make it absolute with urljoin against https://ekantipur.com
author->text_content() of .author-name p a. If the element is missing or its text is empty, return None. Do not raise.
4. Return a list of dicts with exactly these keys, in this order: title, image_url, category, author.
5. Wrap per-card element access in try/except so one broken card doesn't crash the whole scrape.
6.Do not hardcode any article titles, authors, or URls. Everything comes from the live page.

**Copilot's response**
def scrape_entertainment(page) -> list[dict]:
    from urllib.parse import urljoin

    base_url = "https://ekantipur.com"

    page.goto(f"{base_url}/entertainment")
    page.wait_for_selector(".category-wrapper .category")

    category = page.locator(".category-name p a").text_content()
    category = category.strip() if category else ""

    articles = []
    cards = page.locator(".category-wrapper .category")

    for index in range(min(cards.count(), 5)):
        try:
            card = cards.nth(index)

            title = card.locator("h2 a").text_content()
            title = title.strip() if title else ""

            image = card.locator("img.lazy")
            image_url = image.get_attribute("data-src")

            if not image_url:
                image_url = image.get_attribute("src")

            image_url = urljoin(base_url, image_url) if image_url else None

            author_element = card.locator(".author-name p a")
            author = author_element.text_content()
            author = author.strip() if author else None

            articles.append({
                "title": title,
                "image_url": image_url,
                "category": category,
                "author": author,
            })
        except Exception:
            continue

    return articles

### Prompt 2
>Your function ran, but it returned only 3 articles instead of 5. No exception was raised, nothing was printed, two cards just disappeared.
I think I know why. You used card.locator() for every read inside the loop:
title = card.locator("h2 a").text_content()

Please rewrite the functioni  with these changes:
1. Replace every locator() inside the loop with query_sector. Keep the same function signature, the same selector string and the same return shape.
2. Read the category once, outside the loop from .category-name p a using page.query_selector() instead of page.locator().
3. For each of the first 5 cards:
*title - text_content() of h2 a, stripped, None if element is missing or the text is empty.
* image_url - prefer data-src over src on img.lazy. If data-src is missing, fall back to src. If the resulting URL starts with //, make it absolute with urljoin.
* author - text_content() of .author-name p a, stripped, None if the element is missing or the text is empty.
4. Keep a per-card try / except as a safety net.

**Copilot's Response**
def scrape_entertainment(page) -> list[dict]:
    from urllib.parse import urljoin

    base_url = "https://ekantipur.com"

    page.goto(f"{base_url}/entertainment")
    page.wait_for_selector(".category-wrapper .category")

    category_element = page.query_selector(".category-name p a")
    category_text = category_element.text_content() if category_element else None
    category = category_text.strip() if category_text and category_text.strip() else None

    articles = []
    cards = page.query_selector_all(".category-wrapper .category")[:5]

    for card in cards:
        try:
            title_element = card.query_selector("h2 a")
            title_text = title_element.text_content() if title_element else None
            title = title_text.strip() if title_text and title_text.strip() else None

            image_element = card.query_selector("img.lazy")
            image_url = None

            if image_element:
                image_url = image_element.get_attribute("data-src")

                if not image_url:
                    image_url = image_element.get_attribute("src")

                if image_url and image_url.startswith("//"):
                    image_url = urljoin(base_url, image_url)

            author_element = card.query_selector(".author-name p a")
            author_text = author_element.text_content() if author_element else None
            author = (
                author_text.strip()
                if author_text and author_text.strip()
                else None
            )

            articles.append({
                "title": title,
                "image_url": image_url,
                "category": category,
                "author": author,
            })
        except Exception:
            continue

    return articles


### Prompt 3
>Write me one more function matching the style of the first, no main(), no file writing.
function signature: def scrape_cartoon(page) -> dict:
It should navigate to https://ekantipur.com and return the Cartoon of the day as a single dict with keys: title, image_url, author.
Here is the actual HTML of the cartoon section
<section class="e-section">
    <div class="container">
        <div class="section-news">
            <h4><a href="https://ekantipur.com/cartoon">कार्टुन</a></h4>
            <div class="swiper cartoon-slider">
                <div class="swiper-wrapper">
                    <div class="swiper-slide c-slide">
                        <figure>
                            <a class="loading-img"
                               href="https://assets-cdn-api.ekantipur.com/thumb.php?..."
                               data-fancybox="gallery"
                               data-thumb="..."
                               data-type="image">
                                <div class="skeleton"></div>
                                <img class="lazy"
                                     data-src="https://assets-cdn-api.ekantipur.com/thumb.php?src=...&w=601&h=0"
                                     alt="अविनको कार्टुन">
                            </a>
                        </figure>
                    </div>
                    <!-- more .swiper-slide.c-slide slides follow, the first is today's -->
                </div>
            </div>
        </div>
    </div>
</section>

Requirements:
1. Navigate to https://ekantipur.com with wait_until="documentloaded"
2. Wait for section.e-section .swiper-slide.c-slide with state="attached".
3. Take the first slide as today's cartoon.
4. For that slide:
* image_url - select img, prefer data-src, fallback to src. urljoin against https://ekantipur.com for protocol-relative URLs. If neither attribute is present, None.
* title - the alt attribute of the image, stripped. There is no other title source.
* author - parse the alt only when it literally matches ^(.+?को\s*कार्टुन$), returning the captured name. Otherwise None. Do not hardcore any name. Do not assume the cartoonist is always in the alt.
5. If the slide or the image is missing, return
{"title": None, "image_url": None, "author": None} rather than raising.
6. Use query_selector, not locator, and use the same if el else None pattern as the entertainment function.

**Copilot's Response**
def scrape_cartoon(page) -> dict:
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

    slide = page.query_selector(
        "section.e-section .swiper-slide.c-slide"
    )

    if not slide:
        return empty_result

    image = slide.query_selector("img")

    if not image:
        return empty_result

    image_url = image.get_attribute("data-src")

    if not image_url:
        image_url = image.get_attribute("src")

    if image_url and image_url.startswith("//"):
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

## 3. One thing it got wrong

### Copilot's code returned 3 articles instead of 5, with no error

**How I noticed**
I ran the function on the live entertainment page with headless=False. The script ran without any error and returned 3 article only. 2 article clearly visible on the page were missing from the result entirely. There were no warning nothing in terminal.
I remebered in "Helpful Playwright methods" section in the task pdf there was the use of query_selector instead of locator.

**What I did:**
I sent copilot a correction prompt to replace locator to query_selector and it produced 5 results with the copilot's responose.
