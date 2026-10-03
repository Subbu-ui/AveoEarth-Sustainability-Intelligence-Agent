import pandas as pd
from urllib.parse import urlparse


INPUT_FILE = "final_europe_sustainability_intelligence.csv"
OUTPUT_FILE = "europe_intelligence_final_validated.csv"


# ============================================================
# TRUSTED / HIGH-AUTHORITY SOURCES
# ============================================================

TRUSTED_DOMAINS = [
    "europa.eu",
    "ec.europa.eu",
    "eea.europa.eu",
    "europarl.europa.eu",
    "eurostat.ec.europa.eu",
    "oecd.org",
    "eib.org",
    "eit.europa.eu",
    "un.org",
    "worldbank.org"
]


# ============================================================
# HELPER
# ============================================================

def get_domain(url):

    try:
        domain = urlparse(str(url)).netloc.lower()

        if domain.startswith("www."):
            domain = domain[4:]

        return domain

    except Exception:
        return ""


def is_trusted_domain(domain):

    for trusted in TRUSTED_DOMAINS:

        if (
            domain == trusted
            or domain.endswith("." + trusted)
        ):
            return True

    return False


# ============================================================
# VALIDATION
# ============================================================

def validate_priority(row):

    url = row.get(
        "Source URL",
        ""
    )

    domain = get_domain(url)

    original_priority = str(
        row.get(
            "Final Priority Level",
            ""
        )
    )

    original_decision = str(
        row.get(
            "Final Business Decision",
            ""
        )
    )

    intelligence_type = str(
        row.get(
            "Intelligence Type",
            ""
        )
    )

    source_quality = str(
        row.get(
            "Source Quality",
            ""
        )
    )


    trusted = is_trusted_domain(
        domain
    )


    final_priority = original_priority
    final_decision = original_decision

    source_validation = "Accepted"


    # ========================================================
    # PRIORITY ITEM FROM TRUSTED SOURCE
    # ========================================================

    if (
        original_priority == "PRIORITY"
        and trusted
    ):

        source_validation = (
            "Priority supported by high-authority source"
        )


    # ========================================================
    # PRIORITY ITEM FROM NON-TRUSTED SOURCE
    # ========================================================

    elif (
        original_priority == "PRIORITY"
        and not trusted
    ):

        final_priority = "WATCHLIST"

        final_decision = (
            "VERIFY WITH STRONGER SOURCE"
        )

        source_validation = (
            "Priority downgraded because source authority "
            "is insufficient for immediate business action"
        )


    # ========================================================
    # WATCHLIST CAN REMAIN
    # ========================================================

    elif original_priority == "WATCHLIST":

        if trusted:

            source_validation = (
                "Strong source; suitable for strategic monitoring"
            )

        else:

            source_validation = (
                "Useful as background but should be cross-checked "
                "before business action"
            )


    return pd.Series({

        "Source Domain":
            domain,

        "Trusted Source":
            "Yes" if trusted else "No",

        "Validated Priority Level":
            final_priority,

        "Validated Business Decision":
            final_decision,

        "Source Validation Note":
            source_validation
    })


# ============================================================
# LOAD
# ============================================================

print(
    "\nLoading Europe intelligence..."
)

df = pd.read_csv(
    INPUT_FILE
)

print(
    f"Rows loaded: {len(df)}"
)


# ============================================================
# APPLY SOURCE QUALITY GATE
# ============================================================

print(
    "\nApplying source-authority validation..."
)

validation = df.apply(
    validate_priority,
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
    "EUROPE SOURCE VALIDATION COMPLETED"
)

print(
    "======================================================"
)

print(
    f"Rows processed: {len(final_df)}"
)

print(
    f"Output: {OUTPUT_FILE}"
)


print(
    "\nValidated priority levels:"
)

counts = final_df[
    "Validated Priority Level"
].value_counts()

for level, count in counts.items():

    print(
        f"{level}: {count}"
    )


print(
    "\nValidated business decisions:"
)

counts = final_df[
    "Validated Business Decision"
].value_counts()

for decision, count in counts.items():

    print(
        f"{decision}: {count}"
    )


# ============================================================
# FINAL PRIORITY ITEMS
# ============================================================

priority = final_df[
    final_df[
        "Validated Priority Level"
    ] == "PRIORITY"
]


print(
    "\n======================================================"
)

print(
    f"FINAL VALIDATED PRIORITY ITEMS: {len(priority)}"
)

print(
    "======================================================"
)


if len(priority) > 0:

    for _, row in priority.iterrows():

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
            "Source:",
            row.get(
                "Source URL",
                ""
            )
        )

else:

    print(
        "No intelligence item met both the business "
        "priority and source-authority thresholds."
    )