#Python 3.10.2

# Task:
# Find out when credit discounts were/are active.

# Notes:
# The WoT website news page displays a grid list of preview images.
# Each preview image links to an event page which describes
#   the details of the event which may include: Which tanks are on discount; The discount amount;
#   Start/End Date;

# Todo:
# Figure out a better way of scraping/displaying the event page table information
# Scrape other kinds of info

import re
import sys
import requests
import asyncio
import aiohttp
import tabulate
from typing import List
from bs4 import BeautifulSoup
from bs4 import Tag

_WOT_URL = "https://worldoftanks.eu"  # Site path
_NUMBER_OF_PAGES_TO_SCRAPE:int = 1500  # How many pages to scrape before stopping
# Set this to the amount of links displayed on the WoT news page. 72 as of 28/2/22
_EVENTS_PER_NEWS_PAGE:int = 72
# How many page requests should be sent per second? Recommended: 10
_REQUEST_SEND_RATE:float = 10


def get_wot_event_urls_from_page(page_index):
    """Get all the event page URLs from the specified WoT news page.
    0 index is the first page."""

    # Build URL string to get correct page
    url = _WOT_URL + "/en/news/"
    if page_index > 0:
        url += f"p{page_index+1}/"

    # Convert html to "soup" and get the tags that have desired href attributes
    news_page = requests.get(url)
    news_page_soup = BeautifulSoup(news_page.content, features="html.parser")
    preview_titles = news_page_soup.find_all("h2", class_="preview_title")

    event_links = []

    # Gather event page URLs
    for title in preview_titles:
        parent = title.findParent("a", class_="preview_link", href=True)
        if parent is not None:
            event_links.append(_WOT_URL + parent["href"])

    return event_links


def is_easily_printable_table(tbody: Tag) -> bool:
    """Is the table consistent to a grid shape and printable to a terminal window?"""

    # Make sure every row has same amount of columns
    rows = tbody("tr")
    if len(rows) == 0:
        return False

    last_div_count = -1
    for row in rows:
        div_count = len(row("td"))

        if last_div_count == -1:
            last_div_count = div_count

        if div_count != last_div_count:
            return False

    return True


def print_table(tbody: Tag):
    """Attempt to extract data from an html tbody tag and print it in a nice format."""
    rows = tbody("tr")

    # Take first row as headers
    head = []
    data = []
    for i, row in enumerate(rows):
        divs = row(string=re.compile("\w"))
        row_data = []
        # if i == 0:
        #     for div in divs:
        #         head.append(div.text)
        # else:
        for div in divs:
            row_data.append(div.text)
        data.append(row_data)

    print(tabulate.tabulate(data, headers=head))


async def scrape_event_page(page: aiohttp.ClientResponse):
    """Scrapes a WoT event webpage to find desired discount information and prints it."""
    soup = BeautifulSoup(await page.text(), features="html.parser")

    # Find all "tbody" tags (table body)
    tables = soup("tbody")
    for table in tables:
        # Check that table has "discount" and not "rental" text in any of its children
        if table(string=re.compile("discount")) and not table(string=re.compile("rental")) and is_easily_printable_table(table):
            print(f"\n{page.url}")
            # Find time span by identifying something that looks like a time: "00:00". This tag is always positioned before the table.
            time_span_tag = table.find_previous(string=re.compile("\d\d:\d\d"))
            time_span_text = ""
            if time_span_tag:
                time_span_text = time_span_tag.text

            print(f"{time_span_text}:")
            print_table(table)


# Not used
async def async_get_request(session, *urls):
    """ Asynchronously peforms multiple get requests and returns results in corresponding order to the passed in URL list."""
    coros = []
    for url in urls:
        coros.append(session.get(url))
    return await asyncio.gather(*coros)


async def async_get_page_content(session: aiohttp.ClientSession, url: str, out_queue: asyncio.Queue[aiohttp.ClientResponse]):
    """Performs a get request and adds ClientResponse object to queue when completed."""
    try:
        response: aiohttp.ClientResponse = await session.get(url)
    except aiohttp.ServerDisconnectedError as e:
        print("Server disconnected. Try a lower request rate.")
        sys.exit()
    # Here, await has the effect of waiting until the queue has space for another element.
    await out_queue.put(response)


async def async_get_WOT_events_continuously(session: aiohttp.ClientSession, out_queue: asyncio.Queue[aiohttp.ClientResponse], rate: float):
    """Sends GET requests for WoT event pages continuously, at the specified rate, and adds response to page_contents until _NUMBER_OF_NEWS_PAGES_TO_SCRAPE has been reached."""
    events_requested = 0
    event_urls: List[str] = []  # Contains the URLs we need to request

    while events_requested < _NUMBER_OF_PAGES_TO_SCRAPE:
        if events_requested % _EVENTS_PER_NEWS_PAGE == 0:  # If we are starting on a new news page
            # Get all events links from page. 72 links per news page
            event_urls = get_wot_event_urls_from_page(
                events_requested // _EVENTS_PER_NEWS_PAGE)
            print(
                f"Getting event pages {events_requested} to {events_requested + _EVENTS_PER_NEWS_PAGE}...")

        asyncio.create_task(async_get_page_content(
            session, event_urls[events_requested % _EVENTS_PER_NEWS_PAGE], out_queue))
        events_requested += 1

        await asyncio.sleep(1 / rate)


async def main():
    async with aiohttp.ClientSession() as session:
        events_scraped = 0
        page_contents: asyncio.Queue[aiohttp.ClientResponse] = asyncio.Queue()

        # Start requesting pages continuously
        task = asyncio.create_task(
            async_get_WOT_events_continuously(session, page_contents, _REQUEST_SEND_RATE))

        # async_get_WOT_events_continuously() adds responses to our queue.
        # As they come into the queue, scrape them.
        try:
            while events_scraped < _NUMBER_OF_PAGES_TO_SCRAPE:
                page_content = await page_contents.get()
                await scrape_event_page(page_content)
                events_scraped += 1
        except Exception as e:
            print(e)

        print(f"Finished! {events_scraped} pages were scraped.")


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

asyncio.run(main())
