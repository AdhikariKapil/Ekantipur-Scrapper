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
