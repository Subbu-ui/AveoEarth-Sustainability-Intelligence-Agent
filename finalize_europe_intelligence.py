import pandas as pd


# ============================================================
# SETTINGS
# ============================================================

INPUT_FILE = "clean_europe_sustainability_intelligence.csv"
OUTPUT_FILE = "final_europe_sustainability_intelligence.csv"


# ============================================================
# HELPER
# ============================================================

def clean(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


# ============================================================
# FINAL PRIORITY LOGIC
# ============================================================

def final_priority(row):

    intelligence_type = clean(
        row.get("Intelligence Type", "")
    )

    relevance = clean(
        row.get("Rule-Checked Relevance", "")
    )

    impact = clean(
        row.get("Rule-Checked Impact", "")
    )

    freshness = clean(
        row.get("Freshness", "")
    )

    source_quality = clean(
        row.get("Source Quality", "")
    )

    action = clean(
        row.get("Recommended Action", "")
    ).lower()

    source_title = clean(
        row.get("Source Title", "")
    ).lower()

    source_url = clean(
        row.get("Source URL", "")
    ).lower()

    opportunity_risk = clean(
        row.get("Opportunity / Risk", "")
    )

    time_horizon = clean(
        row.get("Time Horizon", "")
    )


    # --------------------------------------------------------
    # Generic action signals
    # --------------------------------------------------------

    generic_actions = [
        "could consider",
        "consider partnering",
        "monitor",
        "stay updated",
        "explore opportunities",
        "learn from",
        "consider exploring"
    ]

    generic_action = any(
        phrase in action
        for phrase in generic_actions
    )


    # --------------------------------------------------------
    # Report / publication signals
    # --------------------------------------------------------

    publication_source = (
        "/publication" in source_url
        or "/publications" in source_url
        or "report" in source_title
        or "study" in source_title
        or "publication" in source_title
    )


    # ========================================================
    # PRIORITY CASE 1:
    # Regulation / policy with high impact
    # ========================================================

    if (
        intelligence_type in [
            "Regulation",
            "Policy"
        ]
        and relevance == "High"
        and impact == "High"
        and freshness in [
            "Current",
            "Recent"
        ]
        and source_quality == "High"
    ):

        return pd.Series({
            "Final Priority Level":
                "PRIORITY",

            "Final Business Decision":
                "ACT / REVIEW NOW",

            "Priority Reason":
                "Current high-impact regulation or policy from a strong source."
        })


    # ========================================================
    # PRIORITY CASE 2:
    # Strong commercial opportunity
    # ========================================================

    if (
        intelligence_type in [
            "Business Opportunity",
            "Market Trend",
            "Consumer Trend",
            "Sustainable Packaging Development",
            "Traceability Development",
            "Supply Chain Development",
            "Circular Economy Development"
        ]
        and relevance == "High"
        and impact == "High"
        and opportunity_risk in [
            "Opportunity",
            "Both"
        ]
        and not generic_action
        and not publication_source
    ):

        return pd.Series({
            "Final Priority Level":
                "PRIORITY",

            "Final Business Decision":
                "ACT / REVIEW NOW",

            "Priority Reason":
                "High-impact business development with a specific AveoEarth implication."
        })


    # ========================================================
    # WATCHLIST:
    # relevant but not yet immediately actionable
    # ========================================================

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

        reason = (
            "Relevant intelligence, but not sufficiently "
            "specific or urgent for immediate action."
        )

        if publication_source:
            reason = (
                "High-quality report/publication useful for strategy, "
                "but not a direct current business trigger."
            )

        if generic_action:
            reason = (
                "Relevant insight, but the resulting business action "
                "is still general rather than immediately executable."
            )

        return pd.Series({
            "Final Priority Level":
                "WATCHLIST",

            "Final Business Decision":
                "KEEP FOR STRATEGY",

            "Priority Reason":
                reason
        })


    # ========================================================
    # BACKGROUND
    # ========================================================

    return pd.Series({
        "Final Priority Level":
            "BACKGROUND",

        "Final Business Decision":
            "LOW PRIORITY",

        "Priority Reason":
            "Limited immediate business relevance for AveoEarth."
    })


# ============================================================
# LOAD DATA
# ============================================================

print("\nLoading cleaned Europe intelligence...")

df = pd.read_csv(
    INPUT_FILE
)

print(
    f"Rows loaded: {len(df)}"
)


# ============================================================
# APPLY FINAL PRIORITISATION
# ============================================================

print(
    "\nApplying final business-priority rules..."
)

priority_results = df.apply(
    final_priority,
    axis=1
)

final_df = pd.concat(
    [
        df,
        priority_results
    ],
    axis=1
)


# ============================================================
# SORT
# ============================================================

priority_order = {
    "PRIORITY": 1,
    "WATCHLIST": 2,
    "BACKGROUND": 3
}


final_df["_Priority Order"] = final_df[
    "Final Priority Level"
].map(
    priority_order
).fillna(99)


final_df = final_df.sort_values(
    by=[
        "_Priority Order",
        "Rule-Checked Relevance Score"
    ],
    ascending=[
        True,
        False
    ]
)


final_df = final_df.drop(
    columns=[
        "_Priority Order"
    ]
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
    "FINAL EUROPE INTELLIGENCE PRIORITISATION COMPLETED"
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
    "\nFinal priority levels:"
)

priority_counts = final_df[
    "Final Priority Level"
].value_counts()

for level, count in priority_counts.items():

    print(
        f"{level}: {count}"
    )


print(
    "\nFinal business decisions:"
)

decision_counts = final_df[
    "Final Business Decision"
].value_counts()

for decision, count in decision_counts.items():

    print(
        f"{decision}: {count}"
    )


# ============================================================
# SHOW PRIORITY ITEMS
# ============================================================

priority_df = final_df[
    final_df[
        "Final Priority Level"
    ] == "PRIORITY"
]


print(
    "\n======================================================"
)

print(
    f"FINAL PRIORITY INTELLIGENCE ITEMS: {len(priority_df)}"
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
        "No item met the strict threshold for immediate priority action."
    )