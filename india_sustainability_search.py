import os
import csv
from datetime import date

from dotenv import load_dotenv
from tavily import TavilyClient


# ============================================================
# SETTINGS
# ============================================================

OUTPUT_FILE = "india_sustainability_candidates.csv"

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
# INDIA INTELLIGENCE TOPICS
# ============================================================

TOPICS = {

    "Government Sustainability Schemes":
        """
        India government sustainability schemes startups SMEs
        sustainable business green enterprise 2026
        """,

    "MSME Sustainability":
        """
        India MSME sustainability schemes green manufacturing
        sustainable business support MSME 2026
        """,

    "Artisan and Handicraft Sector":
        """
        India artisan handicraft sustainable products
        government schemes market opportunities artisans 2026
        """,

    "Farmer and Rural Enterprise":
        """
        India farmer rural entrepreneurship sustainable products
        agribusiness rural enterprise market opportunities 2026
        """,

    "Circular Economy":
        """
        India circular economy business opportunities startups SMEs
        recycling reuse sustainable products 2026
        """,

    "Sustainable Packaging":
        """
        India sustainable packaging regulations business trends
        recyclable reusable packaging consumer products 2026
        """,

    "Ethical and Sustainable Sourcing":
        """
        India ethical sourcing sustainable supply chain
        responsible sourcing artisan farmer products 2026
        """,

    "Social Enterprise":
        """
        India social enterprise sustainable business
        impact entrepreneurship rural livelihoods 2026
        """,

    "Sustainable Retail":
        """
        India sustainable retail ecommerce ethical products
        conscious consumers sustainable marketplace 2026
        """,

    "Traceability":
        """
        India product traceability sustainable supply chains
        digital traceability artisan farmer products 2026
        """
}


# ============================================================
# AVEOEARTH RELEVANCE KEYWORDS
# ============================================================

AVEOEARTH_KEYWORDS = [

    "sustainable",
    "sustainability",

    "artisan",
    "artisans",

    "handicraft",
    "handicrafts",

    "farmer",
    "farmers",

    "rural",

    "msme",
    "small business",

    "social enterprise",
    "social impact",

    "circular economy",
    "circular",

    "ethical sourcing",
    "responsible sourcing",

    "sustainable packaging",

    "traceability",

    "responsible consumption",

    "marketplace",

    "retail",

    "livelihood",
    "livelihoods",

    "supply chain",

    "startup",
    "start-up"
]


# ============================================================
# HIGH-AUTHORITY INDIA SOURCES
# ============================================================

HIGH_VALUE_DOMAINS = [

    "gov.in",
    "nic.in",

    "pib.gov.in",

    "startupindia.gov.in",

    "msme.gov.in",

    "moef.gov.in",

    "niti.gov.in",

    "investindia.gov.in",

    "rbi.org.in",

    "sidbi.in",

    "ncdc.in",

    "nabard.org",

    "worldbank.org",

    "undp.org",

    "un.org"
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def keyword_matches(text):

    text = str(text).lower()

    matches = []

    for keyword in AVEOEARTH_KEYWORDS:

        if keyword.lower() in text:

            matches.append(keyword)

    return matches


def source_quality(url):

    url = str(url).lower()

    for domain in HIGH_VALUE_DOMAINS:

        if domain in url:

            return "High"

    return "Standard"


def calculate_score(title, content, url):

    combined = (
        str(title)
        + " "
        + str(content)
    )

    matches = keyword_matches(
        combined
    )

    score = len(matches) * 5


    # Give authoritative sources extra weight
    if source_quality(url) == "High":

        score += 20


    return score, matches


# ============================================================
# SEARCH
# ============================================================

all_results = []

seen_urls = set()


print(
    "\nStarting India Sustainability Intelligence Search..."
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


            # Must have at least some AveoEarth relevance
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
                    ", ".join(matches),

                "Relevance Score":
                    score,

                "Source Quality":
                    source_quality(url),

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
        x["Relevance Score"],

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
    "INDIA SUSTAINABILITY SEARCH COMPLETED"
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
# RESULTS BY TOPIC
# ============================================================

if len(all_results) > 0:

    print(
        "\nResults by topic:"
    )

    topic_counts = {}

    for item in all_results:

        topic = item["Topic"]

        topic_counts[topic] = (
            topic_counts.get(
                topic,
                0
            )
            + 1
        )


    for topic, count in topic_counts.items():

        print(
            f"{topic}: {count}"
        )


# ============================================================
# TOP RESULTS
# ============================================================

if len(all_results) > 0:

    print(
        "\nTop India intelligence results:"
    )


    for result in all_results[:10]:

        print(
            "\n----------------------------------------"
        )

        print(
            "Topic:",
            result["Topic"]
        )

        print(
            "Title:",
            result["Title"]
        )

        print(
            "Relevance score:",
            result["Relevance Score"]
        )

        print(
            "Source quality:",
            result["Source Quality"]
        )

        print(
            "URL:",
            result["URL"]
        )