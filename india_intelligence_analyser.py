import json
import time
from datetime import date
from urllib.parse import urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup


# ============================================================
# SETTINGS
# ============================================================

INPUT_FILE = "india_sustainability_candidates.csv"
OUTPUT_FILE = "india_sustainability_intelligence.csv"

# Test first before processing all 49
TEST_LIMIT = None

MODEL = "llama3.2:3b"
OLLAMA_URL = "http://localhost:11434/api/generate"

MAX_PAGE_CHARACTERS = 7000

TODAY = str(date.today())


# ============================================================
# TRUSTED INDIA SOURCES
# ============================================================

TRUSTED_DOMAINS = [
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
    "nabard.org",
    "ncdc.in",
    "worldbank.org",
    "undp.org",
    "un.org"
]


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
AveoEarth is a sustainability-focused marketplace promoting
products made by artisans, farmers, rural producers and
underserved communities.

Important business areas include sustainable products,
artisan livelihoods, farmer-linked products, rural enterprise,
ethical sourcing, circular economy, sustainable packaging,
traceability, social enterprise, sustainable retail and
responsible consumption.
"""


AVEOEARTH_CONTEXT = load_context()


# ============================================================
# DOMAIN CHECK
# ============================================================

def get_domain(url):

    try:

        domain = urlparse(
            str(url)
        ).netloc.lower()

        if domain.startswith("www."):
            domain = domain[4:]

        return domain

    except Exception:

        return ""


def trusted_source(url):

    domain = get_domain(url)

    for trusted in TRUSTED_DOMAINS:

        if (
            domain == trusted
            or domain.endswith("." + trusted)
        ):
            return True

    return False


# ============================================================
# FETCH WEBPAGE
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
            f"Could not fully read webpage: {error}"
        )

        return ""


# ============================================================
# LOCAL AI ANALYSIS
# ============================================================

def analyse_with_ollama(
    topic,
    title,
    url,
    search_content,
    webpage_content
):

    prompt = f"""
You are a sustainability and market intelligence analyst
working for AveoEarth.

TODAY'S DATE:
{TODAY}

============================================================

AVEOEARTH BUSINESS CONTEXT

{AVEOEARTH_CONTEXT}

============================================================

INDIA INTELLIGENCE TOPIC

{topic}

SOURCE TITLE

{title}

SOURCE URL

{url}

SEARCH EXTRACT

{search_content}

FULL WEBPAGE TEXT

{webpage_content}

============================================================

YOUR JOB

Determine whether this source provides useful business
intelligence for AveoEarth in India.

Possible intelligence types:

- Government Scheme
- Government Policy
- Regulation
- Market Trend
- Consumer Trend
- Business Opportunity
- MSME Support
- Artisan Support
- Farmer / Rural Enterprise Support
- Social Enterprise Development
- Circular Economy Development
- Sustainable Packaging Development
- Traceability Development
- Supply Chain Development
- Technology
- General Information
- Other


STRICT RULES

1. Do not invent facts.

2. Use only information supported by the supplied source.

3. If information is not stated, use "Not stated".

4. Clearly distinguish a government scheme from a general
   article discussing government policy.

5. Clearly distinguish an existing scheme from an old,
   expired or historical scheme.

6. If a scheme is mentioned, determine whether an existing
   business like AveoEarth could potentially use it.

7. Do not assume that a scheme for individual artisans,
   students, farmers or researchers automatically applies
   to AveoEarth as a company.

8. Clearly identify important eligibility restrictions.

9. For market trends, do not claim an India-wide trend from
   one company example.

10. A general sustainability article should not automatically
    receive High business impact.

11. Recommended actions must be specific and practical.

12. Evaluate relevance to:
    - sustainable products
    - artisans
    - farmers
    - rural livelihoods
    - MSMEs
    - ethical sourcing
    - circular economy
    - sustainable packaging
    - responsible consumption
    - traceability
    - marketplace growth
    - social enterprise

13. Be conservative with High relevance and High impact.

14. If this is an official scheme or regulation, identify the
    responsible government body when stated.

15. Do not fabricate statistics.


Return ONLY valid JSON:

{{
    "useful_intelligence": "Yes / No / Unclear",

    "intelligence_type": "Government Scheme / Government Policy / Regulation / Market Trend / Consumer Trend / Business Opportunity / MSME Support / Artisan Support / Farmer / Rural Enterprise Support / Social Enterprise Development / Circular Economy Development / Sustainable Packaging Development / Traceability Development / Supply Chain Development / Technology / General Information / Other",

    "geographic_scope": "India-wide / State-specific / Regional / Global / Unclear",

    "state_or_region": "State, region, India or Not stated",

    "publication_date": "Date or Not stated",

    "freshness": "Current / Recent / Historical / Unclear",

    "development_title": "Short human-readable title",

    "what_happened": "2-3 sentence factual explanation",

    "government_body_or_organization": "Responsible body or Not stated",

    "key_fact_or_number": "Important verified number or Not stated",

    "scheme_or_program_name": "Name or Not applicable",

    "eligibility": "Eligibility or Not stated",

    "existing_company_can_benefit": "Yes / No / Unclear",

    "why_it_matters_to_aveoearth": "Short explanation",

    "opportunity_or_risk": "Opportunity / Risk / Both / Neutral",

    "business_impact": "High / Medium / Low",

    "time_horizon": "Immediate / Short-term / Medium-term / Long-term / Unclear",

    "recommended_action": "One specific practical action",

    "affected_business_area": "Products / Artisans / Farmers / MSME / Sourcing / Packaging / Marketplace / Marketing / Supply Chain / Compliance / Traceability / Partnerships / Other",

    "aveoearth_relevance": "High / Medium / Low",

    "aveoearth_relevance_score": 0,

    "evidence_summary": "Short factual evidence from source",

    "confidence_score": 0
}}

aveoearth_relevance_score must be 0 to 100.

confidence_score must be 0 to 100.

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
# FINAL BUSINESS PRIORITY RULES
# ============================================================

def determine_priority(
    result,
    url
):

    relevance = result.get(
        "aveoearth_relevance",
        "Low"
    )

    impact = result.get(
        "business_impact",
        "Low"
    )

    freshness = result.get(
        "freshness",
        "Unclear"
    )

    intelligence_type = result.get(
        "intelligence_type",
        "General Information"
    )

    useful = result.get(
        "useful_intelligence",
        "Unclear"
    )

    existing_company = result.get(
        "existing_company_can_benefit",
        "Unclear"
    )

    action = str(
        result.get(
            "recommended_action",
            ""
        )
    ).lower()

    trusted = trusted_source(
        url
    )


    generic_actions = [
        "could consider",
        "monitor",
        "stay updated",
        "explore opportunities",
        "consider exploring",
        "learn more"
    ]


    generic_action = any(
        phrase in action
        for phrase in generic_actions
    )


    # --------------------------------------------------------
    # LOW VALUE
    # --------------------------------------------------------

    if useful == "No":

        return (
            "BACKGROUND",
            "LOW PRIORITY",
            "Source does not provide sufficiently useful business intelligence."
        )


    if relevance == "Low" and impact == "Low":

        return (
            "BACKGROUND",
            "LOW PRIORITY",
            "Low direct relevance and business impact for AveoEarth."
        )


    # --------------------------------------------------------
    # HIGH-PRIORITY GOVERNMENT / REGULATORY SIGNAL
    # --------------------------------------------------------

    if (
        trusted
        and intelligence_type in [
            "Government Scheme",
            "Government Policy",
            "Regulation",
            "MSME Support",
            "Artisan Support",
            "Farmer / Rural Enterprise Support"
        ]
        and freshness in [
            "Current",
            "Recent"
        ]
        and relevance == "High"
        and impact == "High"
        and existing_company != "No"
        and not generic_action
    ):

        return (
            "PRIORITY",
            "ACT / REVIEW NOW",
            "Current high-impact official development with direct AveoEarth relevance."
        )


    # --------------------------------------------------------
    # HIGH-PRIORITY MARKET OPPORTUNITY
    # --------------------------------------------------------

    if (
        trusted
        and intelligence_type in [
            "Business Opportunity",
            "Market Trend",
            "Consumer Trend",
            "Circular Economy Development",
            "Sustainable Packaging Development",
            "Traceability Development",
            "Supply Chain Development"
        ]
        and relevance == "High"
        and impact == "High"
        and freshness in [
            "Current",
            "Recent"
        ]
        and not generic_action
    ):

        return (
            "PRIORITY",
            "ACT / REVIEW NOW",
            "Strong current business development supported by a high-authority source."
        )


    # --------------------------------------------------------
    # STRONG SIGNAL BUT WEAKER SOURCE
    # --------------------------------------------------------

    if (
        not trusted
        and relevance == "High"
        and impact == "High"
    ):

        return (
            "WATCHLIST",
            "VERIFY WITH STRONGER SOURCE",
            "Potentially important signal but requires stronger source confirmation."
        )


    # --------------------------------------------------------
    # STRATEGIC WATCHLIST
    # --------------------------------------------------------

    if (
        relevance in [
            "High",
            "Medium"
        ]
        and impact in [
            "High",
            "Medium"
        ]
    ):

        return (
            "WATCHLIST",
            "KEEP FOR STRATEGY",
            "Relevant intelligence but not sufficiently strong for immediate action."
        )


    return (
        "BACKGROUND",
        "LOW PRIORITY",
        "Limited immediate relevance for AveoEarth."
    )


# ============================================================
# LOAD CANDIDATES
# ============================================================

print(
    "\nLoading India sustainability candidates..."
)

df = pd.read_csv(
    INPUT_FILE
)

print(
    f"Candidate pages available: {len(df)}"
)


# ============================================================
# SORT STRONG SOURCES FIRST
# ============================================================

df["_Source Priority"] = df[
    "Source Quality"
].apply(
    lambda x: 0
    if str(x).lower() == "high"
    else 1
)


df = df.sort_values(
    by=[
        "_Source Priority",
        "Relevance Score"
    ],
    ascending=[
        True,
        False
    ]
)


df = df.drop(
    columns=[
        "_Source Priority"
    ]
)


# ============================================================
# TEST MODE
# ============================================================

if TEST_LIMIT is not None:

    df_to_process = df.head(
        TEST_LIMIT
    )

    print(
        f"Test mode active: analysing top {TEST_LIMIT} pages."
    )

else:

    df_to_process = df


# ============================================================
# ANALYSE
# ============================================================

final_results = []


for counter, (_, row) in enumerate(
    df_to_process.iterrows(),
    start=1
):

    topic = str(
        row.get(
            "Topic",
            ""
        )
    )

    title = str(
        row.get(
            "Title",
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

    source_quality = str(
        row.get(
            "Source Quality",
            ""
        )
    )


    print(
        "\n======================================================"
    )

    print(
        f"Analysing {counter}/{len(df_to_process)}"
    )

    print(
        f"Topic: {topic}"
    )

    print(
        f"Title: {title}"
    )

    print(
        f"Source quality: {source_quality}"
    )


    # --------------------------------------------------------
    # FETCH SOURCE
    # --------------------------------------------------------

    print(
        "Reading source..."
    )

    webpage_content = fetch_webpage(
        url
    )


    if webpage_content:

        print(
            f"Collected {len(webpage_content)} characters."
        )

    else:

        print(
            "Using Tavily search extract as fallback."
        )


    # --------------------------------------------------------
    # OLLAMA
    # --------------------------------------------------------

    print(
        "Running India intelligence analysis..."
    )


    try:

        result = analyse_with_ollama(
            topic=topic,
            title=title,
            url=url,
            search_content=search_content,
            webpage_content=webpage_content
        )


        priority, decision, priority_reason = determine_priority(
            result,
            url
        )


        output_row = {

            "Search Topic":
                topic,

            "Development":
                result.get(
                    "development_title",
                    "Not stated"
                ),

            "Useful Intelligence":
                result.get(
                    "useful_intelligence",
                    "Unclear"
                ),

            "Intelligence Type":
                result.get(
                    "intelligence_type",
                    "General Information"
                ),

            "Geographic Scope":
                result.get(
                    "geographic_scope",
                    "Unclear"
                ),

            "State / Region":
                result.get(
                    "state_or_region",
                    "Not stated"
                ),

            "Publication Date":
                result.get(
                    "publication_date",
                    "Not stated"
                ),

            "Freshness":
                result.get(
                    "freshness",
                    "Unclear"
                ),

            "What Happened":
                result.get(
                    "what_happened",
                    "Not stated"
                ),

            "Government Body / Organization":
                result.get(
                    "government_body_or_organization",
                    "Not stated"
                ),

            "Key Fact / Number":
                result.get(
                    "key_fact_or_number",
                    "Not stated"
                ),

            "Scheme / Program":
                result.get(
                    "scheme_or_program_name",
                    "Not applicable"
                ),

            "Eligibility":
                result.get(
                    "eligibility",
                    "Not stated"
                ),

            "Existing Company Can Benefit":
                result.get(
                    "existing_company_can_benefit",
                    "Unclear"
                ),

            "Why It Matters to AveoEarth":
                result.get(
                    "why_it_matters_to_aveoearth",
                    "Not stated"
                ),

            "Opportunity / Risk":
                result.get(
                    "opportunity_or_risk",
                    "Neutral"
                ),

            "Business Impact":
                result.get(
                    "business_impact",
                    "Low"
                ),

            "Time Horizon":
                result.get(
                    "time_horizon",
                    "Unclear"
                ),

            "Recommended Action":
                result.get(
                    "recommended_action",
                    "Not stated"
                ),

            "Affected Business Area":
                result.get(
                    "affected_business_area",
                    "Other"
                ),

            "AveoEarth Relevance":
                result.get(
                    "aveoearth_relevance",
                    "Low"
                ),

            "AveoEarth Relevance Score":
                result.get(
                    "aveoearth_relevance_score",
                    0
                ),

            "Evidence Summary":
                result.get(
                    "evidence_summary",
                    "Not stated"
                ),

            "Confidence Score":
                result.get(
                    "confidence_score",
                    0
                ),

            "Source Quality":
                source_quality,

            "Trusted Source":
                "Yes"
                if trusted_source(url)
                else "No",

            "Final Priority":
                priority,

            "Final Business Decision":
                decision,

            "Priority Reason":
                priority_reason,

            "Source Title":
                title,

            "Source URL":
                url,

            "Date Checked":
                TODAY
        }


        final_results.append(
            output_row
        )


        print(
            "Type:",
            output_row[
                "Intelligence Type"
            ]
        )

        print(
            "Relevance:",
            output_row[
                "AveoEarth Relevance"
            ],
            output_row[
                "AveoEarth Relevance Score"
            ]
        )

        print(
            "Impact:",
            output_row[
                "Business Impact"
            ]
        )

        print(
            "Final decision:",
            output_row[
                "Final Business Decision"
            ]
        )


        # Save after each result
        pd.DataFrame(
            final_results
        ).to_csv(
            OUTPUT_FILE,
            index=False,
            encoding="utf-8-sig"
        )


    except Exception as error:

        print(
            f"Analysis error: {error}"
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
# SUMMARY
# ============================================================

print(
    "\n======================================================"
)

print(
    "INDIA SUSTAINABILITY INTELLIGENCE COMPLETED"
)

print(
    "======================================================"
)

print(
    f"Pages analysed: {len(final_df)}"
)

print(
    f"Output: {OUTPUT_FILE}"
)


if len(final_df) > 0:

    print(
        "\nFinal priority:"
    )

    counts = final_df[
        "Final Priority"
    ].value_counts()

    for value, count in counts.items():

        print(
            f"{value}: {count}"
        )


    print(
        "\nFinal business decisions:"
    )

    counts = final_df[
        "Final Business Decision"
    ].value_counts()

    for value, count in counts.items():

        print(
            f"{value}: {count}"
        )


    print(
        "\nSource authority:"
    )

    counts = final_df[
        "Trusted Source"
    ].value_counts()

    for value, count in counts.items():

        print(
            f"{value}: {count}"
        )


# ============================================================
# PRIORITY ITEMS
# ============================================================

priority_df = final_df[
    final_df[
        "Final Priority"
    ] == "PRIORITY"
]


print(
    "\n======================================================"
)

print(
    f"INDIA PRIORITY ITEMS: {len(priority_df)}"
)

print(
    "======================================================"
)


if len(priority_df) > 0:

    for _, row in priority_df.iterrows():

        print(
            "\nTopic:",
            row.get(
                "Search Topic",
                ""
            )
        )

        print(
            "Development:",
            row.get(
                "Development",
                ""
            )
        )

        print(
            "Action:",
            row.get(
                "Recommended Action",
                ""
            )
        )

        print(
            "Source:",
            row.get(
                "Source URL",
                ""
            )
        )

else:

    print(
        "No item met the strict priority threshold."
    )