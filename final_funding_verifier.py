import json
import re
import time
from datetime import date

import pandas as pd
import requests
from bs4 import BeautifulSoup


# ============================================================
# SETTINGS
# ============================================================

INPUT_FILE = "open_funding_candidates.csv"
OUTPUT_FILE = "final_funding_opportunities.csv"

# First test only the top 8 unique results
TEST_LIMIT =  None

MODEL = "llama3.2:3b"
OLLAMA_URL = "http://localhost:11434/api/generate"

MAX_PAGE_CHARACTERS = 7000

TODAY = str(date.today())


# ============================================================
# LOAD AVEOEARTH CONTEXT
# ============================================================

def load_context():

    try:

        with open(
            "aveoearth_context.md",
            "r",
            encoding="utf-8"
        ) as file:

            return file.read()

    except FileNotFoundError:

        return """
AveoEarth is a sustainability-focused marketplace supporting
products made by artisans, farmers, rural producers and
underserved communities.

AveoEarth is interested in:

- sustainable products
- artisans
- farmers
- rural livelihoods
- circular economy
- ethical sourcing
- social enterprise
- responsible consumption
- traceability
- sustainable marketplaces
- European market expansion
- non-dilutive funding
"""


AVEOEARTH_CONTEXT = load_context()


# ============================================================
# WEBPAGE READER
# ============================================================

def fetch_webpage(url):

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

        text = " ".join(
            text.split()
        )

        return text[:MAX_PAGE_CHARACTERS]

    except Exception as error:

        print(
            f"Could not read webpage: {error}"
        )

        return ""


# ============================================================
# TITLE NORMALIZATION FOR DUPLICATES
# ============================================================

def normalize_title(title):

    title = str(title).lower()

    # Remove university suffixes after separators
    title = re.sub(
        r"\s+[—|-]\s+.*$",
        "",
        title
    )

    # Remove punctuation
    title = re.sub(
        r"[^a-z0-9 ]",
        " ",
        title
    )

    # Remove extra spaces
    title = " ".join(
        title.split()
    )

    return title


# ============================================================
# REMOVE DUPLICATES
# ============================================================

def remove_duplicates(df):

    df = df.copy()

    df["Normalized Title"] = df[
        "Page Title"
    ].apply(normalize_title)

    # Highest-scoring result first
    df = df.sort_values(
        by="Search Score",
        ascending=False
    )

    # Keep first version of repeated opportunity
    df = df.drop_duplicates(
        subset=[
            "Normalized Title"
        ],
        keep="first"
    )

    return df


# ============================================================
# LOCAL AI VERIFIER
# ============================================================

def verify_with_ollama(
    university,
    title,
    url,
    search_content,
    webpage_content
):

    prompt = f"""
You are a funding research analyst for AveoEarth.

TODAY'S DATE IS:

{TODAY}

This date is extremely important.

Your task is to determine whether the supplied webpage describes
a funding opportunity that AveoEarth could realistically consider.

============================================================

AVEOEARTH CONTEXT

{AVEOEARTH_CONTEXT}

============================================================

UNIVERSITY / ORGANIZATION

{university}

PAGE TITLE

{title}

OFFICIAL SOURCE URL

{url}

SEARCH EXTRACT

{search_content}

OFFICIAL WEBPAGE TEXT

{webpage_content}

============================================================

STRICT RULES

1. Do not invent any information.

2. If information is absent, return "Not stated".

3. A webpage mentioning funding does NOT automatically mean
   AveoEarth can apply.

4. Distinguish:

   - university's own funding
   - German government funding
   - EU funding
   - foundation funding
   - investor funding
   - other external funding

5. If the university only assists applicants, say that the
   university is a support/application host, not the funder.

6. If the deadline is BEFORE {TODAY}, mark status "Closed".

7. Do not mark a historical award or previous recipient as
   an open funding opportunity.

8. Do not treat venture capital or investment rounds as grants.

9. Researcher-only or student-only funding should normally have
   LOW relevance to AveoEarth.

10. University affiliation is critical.
    Determine whether founders must be:

    - students
    - graduates
    - researchers
    - professors
    - employees
    - affiliated startup teams

11. Determine whether an existing external company like
    AveoEarth could realistically apply.

12. If only university-affiliated founders can apply,
    make this explicit.

13. Evaluate sustainability relevance separately from
    funding eligibility.

14. EXIST Women should not automatically be considered relevant
    merely because it provides financial support.
    Check who is eligible.

15. EXIST Research Transfer should not automatically be considered
    relevant. Check whether research-based technology and
    university affiliation are required.

16. When the page provides a past deadline, status must be Closed.

17. Be conservative.

============================================================

Return ONLY valid JSON using exactly this structure:

{{
    "opportunity_name": "Name or Not stated",

    "is_real_funding": "Yes / No / Unclear",

    "is_current_opportunity": "Yes / No / Unclear",

    "current_status": "Open / Upcoming / Rolling / Closed / Unclear",

    "deadline": "Deadline or Not stated",

    "funding_provider": "Actual organization providing money or Not stated",

    "university_role": "Direct funder / Application host / Support partner / Information only / Not clear",

    "funding_amount": "Amount or Not stated",

    "funding_type": "Grant / Stipend / Prize / Subsidy / Equity / Loan / Mixed / Not stated",

    "equity_or_non_equity": "Non-equity / Equity / Mixed / Not stated",

    "company_can_apply": "Yes / No / Unclear",

    "existing_company_can_apply": "Yes / No / Unclear",

    "university_affiliation_required": "Yes / No / Unclear",

    "affiliation_details": "Explain required university relationship or Not stated",

    "eligibility": "Short eligibility description",

    "application_process_found": "Yes / No / Unclear",

    "application_link_or_route": "Application route described by page or Not stated",

    "sustainability_relevance": "High / Medium / Low",

    "sustainability_reason": "Short explanation",

    "aveoearth_funding_fit": "High / Medium / Low / Not eligible / Unclear",

    "aveoearth_fit_score": 0,

    "aveoearth_reason": "Explain whether AveoEarth could realistically use this opportunity",

    "important_barrier": "Main eligibility barrier or None identified",

    "verification_status": "VERIFIED CURRENT / VERIFIED CLOSED / NOT ELIGIBLE / PARTIALLY VERIFIED / NOT FUNDING",

    "confidence_score": 0
}}

AveoEarth fit score must be between 0 and 100.

Use "VERIFIED CURRENT" only when:

- financial support genuinely exists
- opportunity is currently open, upcoming or rolling
- there is a real application route
- eligibility is sufficiently clear

Use "VERIFIED CLOSED" when the funding is real but the
application deadline has passed.

Use "NOT ELIGIBLE" when the program is real but the supplied
eligibility clearly excludes an existing company like AveoEarth.

Use "PARTIALLY VERIFIED" if important information is unclear.

Return JSON only.
"""


    payload = {

        "model": MODEL,

        "prompt": prompt,

        "stream": False,

        "format": "json",

        "options": {
            "temperature": 0
        }
    }


    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=240
    )

    response.raise_for_status()

    result = response.json()

    return json.loads(
        result["response"]
    )


# ============================================================
# LOAD SEARCH RESULTS
# ============================================================

print("\nLoading targeted funding search results...")

df = pd.read_csv(
    INPUT_FILE
)

print(
    f"Raw search results: {len(df)}"
)


# ============================================================
# REMOVE DUPLICATES
# ============================================================

df = remove_duplicates(
    df
)

print(
    f"Unique opportunities after duplicate removal: {len(df)}"
)


# ============================================================
# TEST LIMIT
# ============================================================

if TEST_LIMIT is not None:

    df = df.head(
        TEST_LIMIT
    )

    print(
        f"Test mode active: analysing top {len(df)} unique opportunities."
    )


# ============================================================
# ANALYSE
# ============================================================

final_results = []


for counter, (_, row) in enumerate(
    df.iterrows(),
    start=1
):

    university = str(
        row.get(
            "University",
            ""
        )
    )

    title = str(
        row.get(
            "Page Title",
            ""
        )
    )

    url = str(
        row.get(
            "URL",
            ""
        )
    )

    search_content = str(
        row.get(
            "Content",
            ""
        )
    )

    search_score = row.get(
        "Search Score",
        0
    )


    print(
        "\n======================================================"
    )

    print(
        f"Analysing {counter}/{len(df)}"
    )

    print(
        f"University: {university}"
    )

    print(
        f"Page: {title}"
    )

    print(
        f"Search score: {search_score}"
    )


    # --------------------------------------------------------
    # Read official webpage
    # --------------------------------------------------------

    print(
        "Reading official webpage..."
    )

    webpage_content = fetch_webpage(
        url
    )


    if webpage_content:

        print(
            f"Collected {len(webpage_content)} webpage characters."
        )

    else:

        print(
            "Using search extract as fallback."
        )


    # --------------------------------------------------------
    # AI verification
    # --------------------------------------------------------

    print(
        "Running strict local AI verification..."
    )


    try:

        result = verify_with_ollama(
            university=university,
            title=title,
            url=url,
            search_content=search_content,
            webpage_content=webpage_content
        )


        row_output = {

            "University / Organization":
                university,

            "Opportunity Name":
                result.get(
                    "opportunity_name",
                    "Not stated"
                ),

            "Is Real Funding":
                result.get(
                    "is_real_funding",
                    "Unclear"
                ),

            "Is Current Opportunity":
                result.get(
                    "is_current_opportunity",
                    "Unclear"
                ),

            "Current Status":
                result.get(
                    "current_status",
                    "Unclear"
                ),

            "Deadline":
                result.get(
                    "deadline",
                    "Not stated"
                ),

            "Funding Provider":
                result.get(
                    "funding_provider",
                    "Not stated"
                ),

            "University Role":
                result.get(
                    "university_role",
                    "Not clear"
                ),

            "Funding Amount":
                result.get(
                    "funding_amount",
                    "Not stated"
                ),

            "Funding Type":
                result.get(
                    "funding_type",
                    "Not stated"
                ),

            "Equity / Non-Equity":
                result.get(
                    "equity_or_non_equity",
                    "Not stated"
                ),

            "Company Can Apply":
                result.get(
                    "company_can_apply",
                    "Unclear"
                ),

            "Existing Company Can Apply":
                result.get(
                    "existing_company_can_apply",
                    "Unclear"
                ),

            "University Affiliation Required":
                result.get(
                    "university_affiliation_required",
                    "Unclear"
                ),

            "Affiliation Details":
                result.get(
                    "affiliation_details",
                    "Not stated"
                ),

            "Eligibility":
                result.get(
                    "eligibility",
                    "Not stated"
                ),

            "Application Process Found":
                result.get(
                    "application_process_found",
                    "Unclear"
                ),

            "Application Route":
                result.get(
                    "application_link_or_route",
                    "Not stated"
                ),

            "Sustainability Relevance":
                result.get(
                    "sustainability_relevance",
                    "Low"
                ),

            "Sustainability Reason":
                result.get(
                    "sustainability_reason",
                    "Not stated"
                ),

            "AveoEarth Funding Fit":
                result.get(
                    "aveoearth_funding_fit",
                    "Unclear"
                ),

            "AveoEarth Fit Score":
                result.get(
                    "aveoearth_fit_score",
                    0
                ),

            "AveoEarth Reason":
                result.get(
                    "aveoearth_reason",
                    "Not stated"
                ),

            "Important Barrier":
                result.get(
                    "important_barrier",
                    "Not stated"
                ),

            "Verification Status":
                result.get(
                    "verification_status",
                    "PARTIALLY VERIFIED"
                ),

            "Confidence Score":
                result.get(
                    "confidence_score",
                    0
                ),

            "Search Score":
                search_score,

            "Official Source URL":
                url,

            "Date Checked":
                TODAY
        }


        final_results.append(
            row_output
        )


        print(
            "Verification:",
            row_output[
                "Verification Status"
            ]
        )

        print(
            "Current status:",
            row_output[
                "Current Status"
            ]
        )

        print(
            "Existing company can apply:",
            row_output[
                "Existing Company Can Apply"
            ]
        )

        print(
            "University affiliation:",
            row_output[
                "University Affiliation Required"
            ]
        )

        print(
            "AveoEarth fit:",
            row_output[
                "AveoEarth Funding Fit"
            ],
            row_output[
                "AveoEarth Fit Score"
            ]
        )


        # Save after every result
        pd.DataFrame(
            final_results
        ).to_csv(
            OUTPUT_FILE,
            index=False,
            encoding="utf-8-sig"
        )


    except Exception as error:

        print(
            f"Verification error: {error}"
        )


    time.sleep(1)


# ============================================================
# SAVE
# ============================================================

final_df = pd.DataFrame(
    final_results
)

final_df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# FINAL SUMMARY
# ============================================================

print(
    "\n======================================================"
)

print(
    "FINAL FUNDING VERIFICATION COMPLETED"
)

print(
    "======================================================"
)

print(
    f"Opportunities analysed: {len(final_df)}"
)

print(
    f"Results saved to: {OUTPUT_FILE}"
)


if len(final_df) > 0:

    print(
        "\nVerification status:"
    )

    status_counts = final_df[
        "Verification Status"
    ].value_counts()

    for status, count in status_counts.items():

        print(
            f"{status}: {count}"
        )


    print(
        "\nCurrent status:"
    )

    current_counts = final_df[
        "Current Status"
    ].value_counts()

    for status, count in current_counts.items():

        print(
            f"{status}: {count}"
        )


    print(
        "\nAveoEarth funding fit:"
    )

    fit_counts = final_df[
        "AveoEarth Funding Fit"
    ].value_counts()

    for fit, count in fit_counts.items():

        print(
            f"{fit}: {count}"
        )