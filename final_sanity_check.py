import re
from datetime import date

import pandas as pd
import requests
from bs4 import BeautifulSoup


# ============================================================
# SETTINGS
# ============================================================

INPUT_FILE = "clean_funding_opportunities.csv"
OUTPUT_FILE = "final_clean_funding_database.csv"

TODAY = str(date.today())


# ============================================================
# FETCH PAGE
# ============================================================

def fetch_page(url):

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/130.0 Safari/537.36"
        )
    }

    try:

        response = requests.get(
            url,
            headers=headers,
            timeout=20
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        for tag in soup(
            [
                "script",
                "style",
                "noscript",
                "svg",
                "nav",
                "footer"
            ]
        ):
            tag.decompose()

        text = soup.get_text(
            separator=" ",
            strip=True
        )

        return " ".join(
            text.split()
        ).lower()

    except Exception:

        return ""


# ============================================================
# HELPER
# ============================================================

def contains_any(text, phrases):

    return any(
        phrase.lower() in text
        for phrase in phrases
    )


# ============================================================
# FINAL SANITY RULES
# ============================================================

def sanity_check(row):

    url = str(
        row.get(
            "Official Source URL",
            ""
        )
    )

    title = str(
        row.get(
            "Opportunity Name",
            ""
        )
    )

    existing_decision = str(
        row.get(
            "Final Agent Decision",
            ""
        )
    )

    application_found = str(
        row.get(
            "Application Process Found",
            ""
        )
    ).strip().lower()

    existing_company = str(
        row.get(
            "Existing Company Can Apply",
            ""
        )
    ).strip().lower()


    print(
        f"\nChecking: {title}"
    )

    page_text = fetch_page(
        url
    )


    # --------------------------------------------------------
    # SIGNALS OF ALREADY-FUNDED PROJECT
    # --------------------------------------------------------

    funded_project_signals = [
        "project runs from",
        "project is funded by",
        "funded by the",
        "approved funding volume",
        "total approved funding",
        "project duration",
        "the project focuses on",
        "project goals",
        "project team"
    ]


    # --------------------------------------------------------
    # SIGNALS OF NEWS / ANNIVERSARY PAGE
    # --------------------------------------------------------

    historical_news_signals = [
        "celebrates its",
        "anniversary",
        "years of startup support",
        "successful funding applications",
        "has supported more than",
        "look back",
        "track record",
        "former start-up teams",
        "success story"
    ]


    # --------------------------------------------------------
    # STRONG APPLICATION SIGNALS
    # --------------------------------------------------------

    application_signals = [
        "apply now",
        "apply here",
        "applications are open",
        "application is open",
        "call for applications",
        "call for proposals",
        "application deadline",
        "submit your application",
        "application form",
        "who can apply",
        "eligible applicants"
    ]


    project_hits = sum(
        phrase in page_text
        for phrase in funded_project_signals
    )

    news_hits = sum(
        phrase in page_text
        for phrase in historical_news_signals
    )

    application_hits = sum(
        phrase in page_text
        for phrase in application_signals
    )


    # ========================================================
    # DEFAULT
    # ========================================================

    final_decision = existing_decision

    sanity_status = (
        "No additional issue detected"
    )


    # ========================================================
    # RULE 1 — ALREADY FUNDED PROJECT
    # ========================================================

    if (
        project_hits >= 2
        and application_hits == 0
    ):

        final_decision = (
            "REJECT - ALREADY FUNDED PROJECT"
        )

        sanity_status = (
            "Page describes an existing funded project, "
            "not a funding call."
        )


    # ========================================================
    # RULE 2 — HISTORICAL / NEWS PAGE
    # ========================================================

    elif (
        news_hits >= 2
        and application_hits == 0
    ):

        final_decision = (
            "REJECT - INFORMATION / NEWS PAGE"
        )

        sanity_status = (
            "Page describes historical activity or startup "
            "support but no current funding call."
        )


    # ========================================================
    # RULE 3 — ACTIONABLE MUST HAVE APPLICATION ROUTE
    # ========================================================

    elif (
        existing_decision == "ACTIONABLE LEAD"
        and application_hits == 0
    ):

        final_decision = (
            "MANUAL REVIEW - NO CURRENT CALL FOUND"
        )

        sanity_status = (
            "Previous pipeline marked this actionable, but "
            "no strong current application signal was found."
        )


    # ========================================================
    # RULE 4 — EXISTING COMPANY MUST BE ELIGIBLE
    # ========================================================

    elif (
        existing_decision == "ACTIONABLE LEAD"
        and existing_company != "yes"
    ):

        final_decision = (
            "REJECT - EXISTING COMPANY ELIGIBILITY UNCLEAR"
        )

        sanity_status = (
            "AveoEarth is an existing company but eligibility "
            "for an existing company is not confirmed."
        )


    # ========================================================
    # RULE 5 — APPLICATION FIELD CONTRADICTION
    # ========================================================

    elif (
        application_found == "yes"
        and application_hits == 0
    ):

        sanity_status = (
            "AI reported an application process, but the "
            "source page did not show strong application language."
        )


    return pd.Series({

        "Final Sanity Decision":
            final_decision,

        "Application Signals Found":
            application_hits,

        "Funded Project Signals":
            project_hits,

        "Historical / News Signals":
            news_hits,

        "Sanity Check Note":
            sanity_status,

        "Sanity Check Date":
            TODAY
    })


# ============================================================
# LOAD
# ============================================================

print(
    "\nLoading cleaned funding opportunities..."
)

df = pd.read_csv(
    INPUT_FILE
)

print(
    f"Rows loaded: {len(df)}"
)


# ============================================================
# RUN SANITY CHECK
# ============================================================

print(
    "\nRunning final source sanity check..."
)

sanity_results = df.apply(
    sanity_check,
    axis=1
)

final_df = pd.concat(
    [
        df,
        sanity_results
    ],
    axis=1
)


# ============================================================
# SAVE
# ============================================================

final_df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# SUMMARY
# ============================================================

print(
    "\n======================================================"
)

print(
    "FINAL SOURCE SANITY CHECK COMPLETED"
)

print(
    "======================================================"
)

print(
    f"Rows checked: {len(final_df)}"
)

print(
    f"Output: {OUTPUT_FILE}"
)


print(
    "\nFinal sanity decisions:"
)

counts = final_df[
    "Final Sanity Decision"
].value_counts()

for decision, count in counts.items():

    print(
        f"{decision}: {count}"
    )


# ============================================================
# ONLY CURRENT ACTIONABLE LEADS
# ============================================================

actionable = final_df[
    final_df[
        "Final Sanity Decision"
    ] == "ACTIONABLE LEAD"
]


print(
    "\n======================================================"
)

print(
    f"FINAL ACTIONABLE LEADS: {len(actionable)}"
)

print(
    "======================================================"
)


if len(actionable) > 0:

    for _, row in actionable.iterrows():

        print(
            "\nOpportunity:",
            row.get(
                "Opportunity Name",
                ""
            )
        )

        print(
            "Organization:",
            row.get(
                "University / Organization",
                ""
            )
        )

        print(
            "URL:",
            row.get(
                "Official Source URL",
                ""
            )
        )

else:

    print(
        "No currently verified actionable funding "
        "opportunity was found in this search cycle."
    )