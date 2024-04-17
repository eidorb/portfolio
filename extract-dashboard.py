"""Extracts subset of HTML elements from dashboard page read from stdin.

Use the Datasette CLI to generate HTML and pipe it into this script:

    datasette serve \
    --get https://portfolio.brodie.id.au/-/dashboards/portfolio \
    --metadata cdk/function/metadata.yaml \
    cdk/function/portfolio.db | \
    python extract-dashboard.py | \
    pbcopy

Change the URL host to generate HTML for the demo application.
"""

from itertools import chain
from sys import stdin

from bs4 import BeautifulSoup


soup = BeautifulSoup(stdin, "lxml")
print(
    "".join(
        tag.prettify(formatter="html5")
        for tag in chain(
            # Styling.
            soup.head()[4:],
            # Grid of dashboard charts.
            soup.find_all("div", class_="dashboard-grid"),
            # Scripts.
            soup.section.find_all("script"),
        )
    ).strip()
)
