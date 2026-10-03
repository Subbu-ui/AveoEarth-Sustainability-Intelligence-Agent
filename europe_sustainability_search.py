import os
import csv
from datetime import date

from dotenv import load_dotenv
from tavily import TavilyClient


# ============================================================
# SETTINGS
# ============================================================

OUTPUT_FILE = "europe_sustainability_candidates.csv"

MAX_RESULTS_PER_TOPIC = 5

TODAY = str(date.today())


# ============================================================
# TAVILY SETUP
# ============================================================

load_dotenv()

api_key = os.getenv("TAVILY_API_KEY")

if not api_key:
    raise ValueError(
        "TAVILY_API_KEY not found in .env file."
    )

client = TavilyClient(
    api_key=api_key
)


# ============================================================
# AVEOEARTH-RELEVANT EUROPEAN TOPICS
# ============================================================

TOPICS = {

    "Sustainable Products":
        """
        Europe sustainable products consumer market trends
        responsible consumption sustainable retail 2026
        """,

    "Circular Economy":
        """
        Europe circular economy business opportunities
        SMEs sustainable products circular business models 2026
        """,

    "Ethical Sourcing":
        """
        Europe ethical sourcing responsible supply chain
        sustainable sourcing SMEs consumer products 2026
        """,

    "Sustainable Packaging":
        """
        Europe sustainable packaging reusable recyclable packaging
        SMEs retail products regulations opportunities 2026
        """,

    "Social Enterprise":
        """
        Europe social enterprise market opportunities
        sustainable business social impact SMEs 2026
        """,

    "Traceability":
        """
        Europe product traceability sustainable supply chains
        digital product passport SMEs 2026
        """,

    "Artisan Farmer Products":
        """
        Europe market opportunities artisan products farmer products
        ethical sustainable marketplace rural producers 2026
        """,

    "Sustainable Retail":
        """
        Europe sustainable retail ecommerce marketplace trends
        ethical products responsible consumers 2026
        """
}


# ============================================================
# RELEVANCE KEYWORDS
# ============================================================

AVEOEARTH_KEYWORDS = [

    "sustainable",
    "sustainability",

    "circular economy",
    "circular",

    "ethical sourcing",
    "responsible sourcing",

    "artisan",
    "artisans",

    "farmer",
    "farmers",

    "rural",

    "social enterprise",
    "social impact",

    "traceability",

    "sustainable packaging",

    "responsible consumption",

    "marketplace",

    "retail",

    "small business",
    "sme",

    "digital product passport",

    "supply chain"
]


# ============================================================
# HIGH-VALUE SOURCE SIGNALS
# ============================================================

HIGH_VALUE_DOMAINS = [

    "europa.eu",
    "ec.europa.eu",

    "europarl.europa.eu",

    "eea.europa.eu",

    "eib.org",

    "eit.europa.eu",

    "oecd.org",

    "eurostat.ec.europa.eu"
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def keyword_matches(text):

    text = str(text).lower()

    matches = []

    for keyword in AVEOEARTH_KEYWORDS:

        if keyword.lower() in text:

            matches.append(
                keyword
            )

    return matches


def source_quality(url):

    url = str(url).lower()

    for domain in HIGH_VALUE_DOMAINS:

        if domain in url:

            return "High"

    return "Standard"


def calculate_score(
    title,
    content,
    url
):

    combined = (
        str(title)
        + " "
        + str(content)
    )

    matches = keyword_matches(
        combined
    )

    score = len(matches) * 5


    if source_quality(url) == "High":

        score += 15


    return score, matches


# ============================================================
# SEARCH
# ============================================================

all_results = []

seen_urls = set()


print(
    "\nStarting Europe Sustainability Intelligence Search..."
)


for topic, query in TOPICS.items():

    print(
        "\n======================================================"
    )

    print(
        f"Searching topic: {topic}"
    )


    try:

        response = client.search(

            query=query,

            search_depth="basic",

            max_results=MAX_RESULTS_PER_TOPIC
        )


        results = response.get(
            "results",
            []
        )


        kept = 0


        for result in results:

            title = result.get(
                "title",
                ""
            )

            url = result.get(
                "url",
                ""
            )

            content = result.get(
                "content",
                ""
            )


            if not url:

                continue


            if url in seen_urls:

                continue


            score, matches = calculate_score(
                title,
                content,
                url
            )


            # Keep only results that have some relevance
            if len(matches) == 0:

                continue


            seen_urls.add(
                url
            )

            kept += 1


            all_results.append({

                "Topic":
                    topic,

                "Title":
                    title,

                "URL":
                    url,

                "Content":
                    content,

                "AveoEarth Keyword Matches":
                    ", ".join(
                        matches
                    ),

                "Relevance Score":
                    score,

                "Source Quality":
                    source_quality(
                        url
                    ),

                "Date Checked":
                    TODAY,

                "Status":
                    "Requires intelligence verification"
            })


        print(
            f"Relevant results kept: {kept}"
        )


    except Exception as error:

        print(
            f"Search error: {error}"
        )


# ============================================================
# SORT RESULTS
# ============================================================

all_results = sorted(

    all_results,

    key=lambda x:
        x[
            "Relevance Score"
        ],

    reverse=True
)


# ============================================================
# SAVE CSV
# ============================================================

fieldnames = [

    "Topic",

    "Title",

    "URL",

    "Content",

    "AveoEarth Keyword Matches",

    "Relevance Score",

    "Source Quality",

    "Date Checked",

    "Status"
]


with open(

    OUTPUT_FILE,

    "w",

    newline="",

    encoding="utf-8-sig"

) as file:

    writer = csv.DictWriter(

        file,

        fieldnames=fieldnames
    )


    writer.writeheader()

    writer.writerows(
        all_results
    )


# ============================================================
# SUMMARY
# ============================================================

print(
    "\n======================================================"
)

print(
    "EUROPE SUSTAINABILITY SEARCH COMPLETED"
)

print(
    "======================================================"
)

print(
    f"Topics searched: {len(TOPICS)}"
)

print(
    f"Relevant intelligence pages found: {len(all_results)}"
)

print(
    f"Results saved to: {OUTPUT_FILE}"
)


# ============================================================
# TOP RESULTS
# ============================================================

if len(all_results) > 0:

    print(
        "\nTop intelligence results:"
    )


    for result in all_results[:10]:

        print(
            "\n----------------------------------------"
        )

        print(
            "Topic:",
            result[
                "Topic"
            ]
        )

        print(
            "Title:",
            result[
                "Title"
            ]
        )

        print(
            "Relevance score:",
            result[
                "Relevance Score"
            ]
        )

        print(
            "Source quality:",
            result[
                "Source Quality"
            ]
        )

        print(
            "URL:",
            result[
                "URL"
            ]
        )