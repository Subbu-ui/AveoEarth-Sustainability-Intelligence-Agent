import os
import csv
from datetime import date

from dotenv import load_dotenv
from tavily import TavilyClient


# ============================================================
# SETTINGS
# ============================================================

UNIVERSITY_FILE = "universities.txt"
OUTPUT_FILE = "open_funding_candidates.csv"

MAX_RESULTS_PER_UNIVERSITY = 8


# ============================================================
# LOAD TAVILY
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
# LOAD UNIVERSITIES
# ============================================================

def load_universities():

    universities = []

    with open(
        UNIVERSITY_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        for line in file:

            line = line.strip()

            if not line:
                continue

            name, domain = line.split("|")

            universities.append({
                "name": name.strip(),
                "domain": domain.strip()
            })

    return universities


# ============================================================
# KEYWORDS
# ============================================================

FUNDING_SIGNALS = [
    "grant",
    "funding",
    "financial support",
    "stipend",
    "subsidy",
    "non-dilutive",
    "non-repayable",
    "startup grant",
    "start-up grant",
    "innovation grant",
    "exist startup grant",
    "exist start-up grant",
    "research transfer",
    "seed funding"
]


APPLICATION_SIGNALS = [
    "apply",
    "application",
    "applications",
    "open call",
    "call for applications",
    "call for proposals",
    "deadline",
    "eligible applicants",
    "eligibility",
    "who can apply",
    "application period",
    "submit"
]


STARTUP_SIGNALS = [
    "startup",
    "start-up",
    "founder",
    "entrepreneur",
    "entrepreneurship",
    "venture",
    "spin-off",
    "spin off",
    "company",
    "business",
    "incubator"
]


BAD_PAGE_SIGNALS = [
    "postdoctoral",
    "postdoc",
    "phd scholarship",
    "doctoral scholarship",
    "research fellowship",
    "student scholarship",
    "series a",
    "series b",
    "series c",
    "funding round",
    "financing round",
    "raised €",
    "raised $",
    "secures €",
    "secures $",
    "success story"
]


# ============================================================
# HELPER
# ============================================================

def find_matches(text, keywords):

    text = str(text).lower()

    matches = []

    for keyword in keywords:

        if keyword.lower() in text:

            matches.append(keyword)

    return matches


# ============================================================
# SCORE RESULT
# ============================================================

def evaluate_result(title, content):

    combined = (
        str(title)
        + " "
        + str(content)
    )

    funding_matches = find_matches(
        combined,
        FUNDING_SIGNALS
    )

    application_matches = find_matches(
        combined,
        APPLICATION_SIGNALS
    )

    startup_matches = find_matches(
        combined,
        STARTUP_SIGNALS
    )

    bad_matches = find_matches(
        combined,
        BAD_PAGE_SIGNALS
    )


    score = 0

    score += len(funding_matches) * 3
    score += len(application_matches) * 4
    score += len(startup_matches) * 2
    score -= len(bad_matches) * 5


    return {
        "score": score,
        "funding_matches": funding_matches,
        "application_matches": application_matches,
        "startup_matches": startup_matches,
        "bad_matches": bad_matches
    }


# ============================================================
# SEARCH ONE UNIVERSITY
# ============================================================

def search_university(university):

    query = f"""
    {university['name']}

    currently open startup grant funding

    open call application deadline

    startup company founder entrepreneurship funding

    innovation sustainability circular economy

    non-dilutive grant EXIST funding

    apply 2026
    """


    print(
        f"\nSearching: {university['name']}"
    )


    response = client.search(
        query=query,
        search_depth="basic",
        max_results=MAX_RESULTS_PER_UNIVERSITY,
        include_domains=[
            university["domain"]
        ]
    )


    return response.get(
        "results",
        []
    )


# ============================================================
# MAIN
# ============================================================

universities = load_universities()

all_candidates = []

seen_urls = set()


for university in universities:

    results = search_university(
        university
    )


    kept_for_university = 0


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


        evaluation = evaluate_result(
            title,
            content
        )


        funding_matches = evaluation[
            "funding_matches"
        ]

        application_matches = evaluation[
            "application_matches"
        ]

        startup_matches = evaluation[
            "startup_matches"
        ]

        bad_matches = evaluation[
            "bad_matches"
        ]


        # ====================================================
        # STRICT SEARCH GATE
        # ====================================================

        # Funding must be mentioned
        if len(funding_matches) == 0:
            continue


        # Must contain startup/business relevance
        if len(startup_matches) == 0:
            continue


        # Prefer actual application language
        if len(application_matches) == 0:
            continue


        # Reject obvious irrelevant page categories
        if len(bad_matches) >= 2:
            continue


        seen_urls.add(url)

        kept_for_university += 1


        all_candidates.append({

            "University":
                university["name"],

            "Official Domain":
                university["domain"],

            "Page Title":
                title,

            "URL":
                url,

            "Content":
                content,

            "Search Score":
                evaluation["score"],

            "Funding Signals":
                ", ".join(
                    funding_matches
                ),

            "Application Signals":
                ", ".join(
                    application_matches
                ),

            "Startup Signals":
                ", ".join(
                    startup_matches
                ),

            "Negative Signals":
                ", ".join(
                    bad_matches
                ),

            "Date Checked":
                str(date.today()),

            "Search Status":
                "Potential current funding opportunity"
        })


    print(
        f"Potential opportunities kept: {kept_for_university}"
    )


# ============================================================
# SORT BEST RESULTS FIRST
# ============================================================

all_candidates = sorted(
    all_candidates,
    key=lambda x: x["Search Score"],
    reverse=True
)


# ============================================================
# SAVE CSV
# ============================================================

fieldnames = [
    "University",
    "Official Domain",
    "Page Title",
    "URL",
    "Content",
    "Search Score",
    "Funding Signals",
    "Application Signals",
    "Startup Signals",
    "Negative Signals",
    "Date Checked",
    "Search Status"
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
        all_candidates
    )


# ============================================================
# SUMMARY
# ============================================================

print(
    "\n======================================================"
)

print(
    "TARGETED FUNDING SEARCH COMPLETED"
)

print(
    "======================================================"
)

print(
    f"Universities searched: {len(universities)}"
)

print(
    f"Potential current funding pages found: {len(all_candidates)}"
)

print(
    f"Results saved to: {OUTPUT_FILE}"
)


if len(all_candidates) > 0:

    print(
        "\nTop results:"
    )

    for result in all_candidates[:10]:

        print(
            "\n----------------------------------------"
        )

        print(
            result["University"]
        )

        print(
            result["Page Title"]
        )

        print(
            f"Search score: {result['Search Score']}"
        )

        print(
            result["URL"]
        )