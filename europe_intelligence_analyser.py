import json
import time
from datetime import date

import pandas as pd
import requests
from bs4 import BeautifulSoup


# ============================================================
# SETTINGS
# ============================================================

INPUT_FILE = "europe_sustainability_candidates.csv"
OUTPUT_FILE = "europe_sustainability_intelligence.csv"

# First analyse only 8 results
TEST_LIMIT = None

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
AveoEarth is a sustainability-focused marketplace promoting
products connected with artisans, farmers, rural producers,
ethical sourcing and sustainable consumption.

The company is interested in European market opportunities,
sustainable products, circular economy, responsible sourcing,
sustainable packaging, traceability, social enterprise,
artisan/farmer-linked products and sustainable retail.
"""


AVEOEARTH_CONTEXT = load_context()


# ============================================================
# READ WEBPAGE
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
# OLLAMA INTELLIGENCE ANALYSIS
# ============================================================

def analyse_with_ollama(
    topic,
    title,
    url,
    search_content,
    webpage_content
):

    prompt = f"""
You are a sustainability business intelligence analyst
working for AveoEarth.

TODAY'S DATE:
{TODAY}

============================================================

AVEOEARTH BUSINESS CONTEXT

{AVEOEARTH_CONTEXT}

============================================================

SEARCH TOPIC

{topic}

ARTICLE / PAGE TITLE

{title}

SOURCE URL

{url}

SEARCH EXTRACT

{search_content}

FULL WEBPAGE TEXT

{webpage_content}

============================================================

YOUR JOB

Determine whether this source contains useful European
sustainability business intelligence for AveoEarth.

Possible intelligence types include:

- Regulation
- Policy
- Market Trend
- Consumer Trend
- Business Opportunity
- Technology
- Circular Economy Development
- Sustainable Packaging Development
- Supply Chain Development
- Traceability Development
- Social Enterprise Development
- Funding / Support Development
- General Information
- Other


STRICT RULES

1. Do not invent facts.

2. Use only information supported by the supplied source.

3. If information is not stated, use "Not stated".

4. Do not assume something is a European-wide trend from
   a single company example.

5. Clearly distinguish regulation from market trend.

6. Clearly distinguish an announced proposal from a law
   already in force.

7. If the page is mainly promotional content with little
   useful intelligence, mark it Low relevance.

8. Sustainability relevance alone is not enough.
   Explain whether AveoEarth could practically use the insight.

9. Recommended actions must be simple and realistic.

10. Consider AveoEarth's connection with:
    - sustainable products
    - artisans
    - farmers
    - rural livelihoods
    - ethical sourcing
    - circular economy
    - sustainable packaging
    - responsible consumption
    - social enterprise
    - traceability
    - European market expansion
    - sustainable marketplaces

11. Do not fabricate statistics.

12. If a number is important, include it only when clearly
    stated in the source.

13. If the source appears old or historical, say so.

14. Be conservative when assigning High relevance.


Return ONLY valid JSON:

{{
    "useful_intelligence": "Yes / No / Unclear",

    "intelligence_type": "Regulation / Policy / Market Trend / Consumer Trend / Business Opportunity / Technology / Circular Economy Development / Sustainable Packaging Development / Supply Chain Development / Traceability Development / Social Enterprise Development / Funding / Support Development / General Information / Other",

    "geographic_scope": "Europe-wide / EU / Country-specific / Global / Unclear",

    "country_or_region": "Country, EU, Europe or Not stated",

    "publication_date": "Date if stated or Not stated",

    "freshness": "Current / Recent / Historical / Unclear",

    "development_title": "Short human-readable description",

    "what_happened": "2-3 sentence factual explanation",

    "key_fact_or_number": "Important factual number or Not stated",

    "why_it_matters_to_aveoearth": "Short explanation",

    "opportunity_or_risk": "Opportunity / Risk / Both / Neutral",

    "business_impact": "High / Medium / Low",

    "time_horizon": "Immediate / Short-term / Medium-term / Long-term / Unclear",

    "recommended_action": "One practical action AveoEarth could consider",

    "affected_business_area": "Products / Sourcing / Packaging / Marketplace / Marketing / Supply Chain / Compliance / Traceability / Partnerships / Other",

    "aveoearth_relevance": "High / Medium / Low",

    "aveoearth_relevance_score": 0,

    "evidence_summary": "Short factual evidence from the source",

    "verification_status": "VERIFIED SOURCE INSIGHT / PARTIAL INSIGHT / LOW VALUE SOURCE",

    "confidence_score": 0
}}

aveoearth_relevance_score must be between 0 and 100.

confidence_score must be between 0 and 100.

Use VERIFIED SOURCE INSIGHT only when the source clearly
supports the stated business intelligence.

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

print(
    "\nLoading Europe sustainability candidates..."
)

df = pd.read_csv(
    INPUT_FILE
)

print(
    f"Candidate pages available: {len(df)}"
)


# ============================================================
# SORT BEST RESULTS FIRST
# ============================================================

df = df.sort_values(
    by="Relevance Score",
    ascending=False
)


# ============================================================
# TEST LIMIT
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
# PROCESS RESULTS
# ============================================================

intelligence_results = []


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

    search_score = row.get(
        "Relevance Score",
        0
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
        f"Search relevance score: {search_score}"
    )


    # --------------------------------------------------------
    # Read source page
    # --------------------------------------------------------

    print(
        "Reading source webpage..."
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
    # Run local AI
    # --------------------------------------------------------

    print(
        "Running local sustainability intelligence analysis..."
    )


    try:

        result = analyse_with_ollama(

            topic=topic,

            title=title,

            url=url,

            search_content=search_content,

            webpage_content=webpage_content
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

            "Country / Region":
                result.get(
                    "country_or_region",
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

            "Key Fact / Number":
                result.get(
                    "key_fact_or_number",
                    "Not stated"
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

            "Verification Status":
                result.get(
                    "verification_status",
                    "PARTIAL INSIGHT"
                ),

            "Confidence Score":
                result.get(
                    "confidence_score",
                    0
                ),

            "Search Relevance Score":
                search_score,

            "Source Quality":
                source_quality,

            "Source Title":
                title,

            "Source URL":
                url,

            "Date Checked":
                TODAY
        }


        intelligence_results.append(
            output_row
        )


        print(
            "Type:",
            output_row[
                "Intelligence Type"
            ]
        )

        print(
            "Useful:",
            output_row[
                "Useful Intelligence"
            ]
        )

        print(
            "AveoEarth relevance:",
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


        # Save progress after every page
        pd.DataFrame(
            intelligence_results
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
# FINAL SAVE
# ============================================================

final_df = pd.DataFrame(
    intelligence_results
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
    "EUROPE SUSTAINABILITY INTELLIGENCE COMPLETED"
)

print(
    "======================================================"
)

print(
    f"Pages analysed: {len(final_df)}"
)

print(
    f"Results saved to: {OUTPUT_FILE}"
)


if len(final_df) > 0:

    print(
        "\nIntelligence types:"
    )

    type_counts = final_df[
        "Intelligence Type"
    ].value_counts()

    for name, count in type_counts.items():

        print(
            f"{name}: {count}"
        )


    print(
        "\nAveoEarth relevance:"
    )

    relevance_counts = final_df[
        "AveoEarth Relevance"
    ].value_counts()

    for name, count in relevance_counts.items():

        print(
            f"{name}: {count}"
        )


    print(
        "\nBusiness impact:"
    )

    impact_counts = final_df[
        "Business Impact"
    ].value_counts()

    for name, count in impact_counts.items():

        print(
            f"{name}: {count}"
        )