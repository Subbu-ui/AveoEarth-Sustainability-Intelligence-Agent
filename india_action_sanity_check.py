import pandas as pd
from urllib.parse import urlparse


# ============================================================
# SETTINGS
# ============================================================

INPUT_FILE = "india_sustainability_intelligence.csv"
OUTPUT_FILE = "india_sustainability_intelligence_validated.csv"


# ============================================================
# HELPERS
# ============================================================

def clean(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def get_domain(url):
    try:
        domain = urlparse(str(url)).netloc.lower()

        if domain.startswith("www."):
            domain = domain[4:]

        return domain

    except Exception:
        return ""


# ============================================================
# VALIDATION
# ============================================================

def validate_row(row):

    title = clean(
        row.get("Source Title", "")
    )

    development = clean(
        row.get("Development", "")
    )

    intelligence_type = clean(
        row.get("Intelligence Type", "")
    )

    scheme = clean(
        row.get("Scheme / Program", "")
    )

    organisation = clean(
        row.get("Government Body / Organization", "")
    )

    existing_company = clean(
        row.get("Existing Company Can Benefit", "")
    )

    original_action = clean(
        row.get("Recommended Action", "")
    )

    priority = clean(
        row.get("Final Priority", "")
    )

    business_decision = clean(
        row.get("Final Business Decision", "")
    )

    url = clean(
        row.get("Source URL", "")
    )

    domain = get_domain(url)


    combined_text = (
        title
        + " "
        + development
        + " "
        + scheme
        + " "
        + organisation
    ).lower()


    validated_authority = organisation

    corrected_action = original_action

    validated_priority = priority

    validated_decision = business_decision

    qa_notes = []


    # ========================================================
    # RULE 1 — PIB IS INFORMATION SOURCE, NOT IMPLEMENTER
    # ========================================================

    if "pib.gov.in" in domain:

        qa_notes.append(
            "PIB is treated as the information source, not automatically as the implementing body."
        )

        if (
            "press information bureau" in organisation.lower()
            or organisation == ""
            or organisation.lower() == "not stated"
        ):

            validated_authority = (
                "Implementing ministry/department must be identified from the scheme"
            )


    # ========================================================
    # RULE 2 — HANDICRAFT / NHDP
    # ========================================================

    if (
        "handicraft" in combined_text
        or "nhdp" in combined_text
        or "national handicraft development programme" in combined_text
    ):

        validated_authority = (
            "Office of Development Commissioner (Handicrafts), Ministry of Textiles"
        )

        corrected_action = (
            "Review the relevant NHDP component and eligibility through the "
            "official Development Commissioner (Handicrafts) portal. Assess "
            "whether AveoEarth can participate directly as an exporter/"
            "entrepreneur or through an eligible artisan or producer partner."
        )

        qa_notes.append(
            "Handicrafts programme routed to the Office of Development Commissioner (Handicrafts)."
        )


    # ========================================================
    # RULE 3 — MSME PROGRAMMES
    # ========================================================

    elif (
        "msme" in combined_text
        and intelligence_type in [
            "Government Scheme",
            "Government Policy",
            "MSME Support"
        ]
    ):

        if (
            validated_authority == ""
            or validated_authority.lower() == "not stated"
            or "press information bureau" in validated_authority.lower()
        ):

            validated_authority = (
                "Ministry of Micro, Small and Medium Enterprises / relevant implementing agency"
            )

        corrected_action = (
            "Verify the exact MSME scheme eligibility and application route "
            "through the responsible Ministry of MSME or official implementing "
            "agency before taking action."
        )

        qa_notes.append(
            "MSME scheme should be actioned through the implementing ministry or agency."
        )


    # ========================================================
    # RULE 4 — DO NOT CONTACT NEWS / INFORMATION PUBLISHER
    # ========================================================

    publisher_terms = [
        "press information bureau",
        "pib",
        "journal",
        "yahoo",
        "news website"
    ]

    if any(
        term in original_action.lower()
        for term in publisher_terms
    ):

        qa_notes.append(
            "Original action incorrectly targeted the information publisher."
        )

        if corrected_action == original_action:

            corrected_action = (
                "Identify the responsible implementing organization and verify "
                "the official eligibility and application process before taking action."
            )


    # ========================================================
    # RULE 5 — EXISTING COMPANY ELIGIBILITY
    # ========================================================

    if existing_company.lower() == "no":

        validated_priority = "WATCHLIST"

        validated_decision = "NOT DIRECTLY ELIGIBLE"

        qa_notes.append(
            "Existing company eligibility is explicitly negative."
        )


    elif existing_company.lower() in [
        "unclear",
        "",
        "not stated"
    ]:

        if priority == "PRIORITY":

            validated_priority = "WATCHLIST"

            validated_decision = "REVIEW ELIGIBILITY"

            qa_notes.append(
                "Priority downgraded because eligibility for an existing company is not confirmed."
            )


    # ========================================================
    # RULE 6 — GOVERNMENT SCHEME MUST HAVE NAMED PROGRAMME
    # ========================================================

    if (
        intelligence_type == "Government Scheme"
        and scheme.lower() in [
            "",
            "not stated",
            "not applicable"
        ]
    ):

        if validated_priority == "PRIORITY":

            validated_priority = "WATCHLIST"

            validated_decision = "VERIFY SCHEME DETAILS"

        qa_notes.append(
            "Government scheme classification lacks a clearly identified scheme/program name."
        )


    # ========================================================
    # OUTPUT
    # ========================================================

    return pd.Series({

        "Validated Implementing Authority":
            validated_authority,

        "Validated Recommended Action":
            corrected_action,

        "Validated Priority":
            validated_priority,

        "Validated Business Decision":
            validated_decision,

        "Action QA Notes":
            " | ".join(qa_notes)
            if qa_notes
            else "No major action issue detected"
    })


# ============================================================
# LOAD DATA
# ============================================================

print(
    "\nLoading India intelligence pilot..."
)

df = pd.read_csv(
    INPUT_FILE
)

print(
    f"Rows loaded: {len(df)}"
)


# ============================================================
# APPLY VALIDATION
# ============================================================

print(
    "\nChecking implementing authorities, eligibility and actions..."
)

validation = df.apply(
    validate_row,
    axis=1
)


final_df = pd.concat(
    [
        df,
        validation
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
    "INDIA ACTION SANITY CHECK COMPLETED"
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
    "\nValidated priorities:"
)

counts = final_df[
    "Validated Priority"
].value_counts()

for value, count in counts.items():

    print(
        f"{value}: {count}"
    )


print(
    "\nValidated business decisions:"
)

counts = final_df[
    "Validated Business Decision"
].value_counts()

for value, count in counts.items():

    print(
        f"{value}: {count}"
    )


# ============================================================
# SHOW ACTION ITEMS
# ============================================================

action_items = final_df[
    final_df[
        "Validated Priority"
    ] == "PRIORITY"
]


print(
    "\n======================================================"
)

print(
    f"VALIDATED INDIA PRIORITY ITEMS: {len(action_items)}"
)

print(
    "======================================================"
)


if len(action_items) > 0:

    for _, row in action_items.iterrows():

        print(
            "\nDevelopment:",
            row.get(
                "Development",
                ""
            )
        )

        print(
            "Authority:",
            row.get(
                "Validated Implementing Authority",
                ""
            )
        )

        print(
            "Action:",
            row.get(
                "Validated Recommended Action",
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
        "No pilot item passed the final India priority checks."
    )