import pandas as pd


# ============================================================
# SETTINGS
# ============================================================

INPUT_FILE = "europe_sustainability_intelligence.csv"
OUTPUT_FILE = "clean_europe_sustainability_intelligence.csv"


# ============================================================
# HELPERS
# ============================================================

def clean_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalise_label(value, allowed=None, default="Unclear"):
    value = clean_text(value)

    if not value:
        return default

    if allowed is None:
        return value

    for item in allowed:
        if value.lower() == item.lower():
            return item

    return default


# ============================================================
# RULE ENGINE
# ============================================================

def apply_rules(row):

    qa_flags = []

    search_topic = clean_text(row.get("Search Topic", ""))
    development = clean_text(row.get("Development", ""))
    source_title = clean_text(row.get("Source Title", ""))
    intelligence_type = clean_text(row.get("Intelligence Type", ""))
    usefulness = clean_text(row.get("Useful Intelligence", ""))
    freshness = clean_text(row.get("Freshness", ""))
    impact = clean_text(row.get("Business Impact", ""))
    relevance = clean_text(row.get("AveoEarth Relevance", ""))
    recommended_action = clean_text(row.get("Recommended Action", ""))
    source_quality = clean_text(row.get("Source Quality", ""))
    what_happened = clean_text(row.get("What Happened", ""))
    evidence_summary = clean_text(row.get("Evidence Summary", ""))
    opportunity_or_risk = clean_text(row.get("Opportunity / Risk", ""))

    try:
        relevance_score = int(float(row.get("AveoEarth Relevance Score", 0)))
    except Exception:
        relevance_score = 0

    title_blob = (
        f"{development} {source_title} {what_happened} {evidence_summary}"
    ).lower()


    # --------------------------------------------------------
    # keyword signals
    # --------------------------------------------------------

    academic_signals = [
        "study",
        "research",
        "publication",
        "journal",
        "perspective",
        "review",
        "paper",
        "report",
        "small firm growth perspective",
        "global food system"
    ]

    generic_signals = [
        "general overview",
        "broad discussion",
        "background information",
        "general information"
    ]

    strong_regulation_signals = [
        "regulation",
        "directive",
        "compliance",
        "mandatory",
        "requirement",
        "law",
        "legislation",
        "digital product passport"
    ]

    strong_market_signals = [
        "market growth",
        "consumer demand",
        "market opportunity",
        "expanding market",
        "new opportunity",
        "industry shift",
        "supply chain change"
    ]

    weak_action_signals = [
        "consider partnerships",
        "monitor the trend",
        "stay updated",
        "explore opportunities",
        "could consider"
    ]

    academic_hits = sum(
        term in title_blob for term in academic_signals
    )

    generic_hits = sum(
        term in title_blob for term in generic_signals
    )

    regulation_hits = sum(
        term in title_blob for term in strong_regulation_signals
    )

    market_hits = sum(
        term in title_blob for term in strong_market_signals
    )

    weak_action = any(
        term in recommended_action.lower()
        for term in weak_action_signals
    )


    # --------------------------------------------------------
    # start with AI output
    # --------------------------------------------------------

    checked_relevance = relevance if relevance else "Low"
    checked_impact = impact if impact else "Low"
    checked_score = relevance_score

    final_tier = "USEFUL BACKGROUND"


    # ========================================================
    # RULE 1 — usefulness not confirmed
    # ========================================================

    if usefulness.lower() == "no":
        final_tier = "LOW VALUE"
        checked_relevance = "Low"
        checked_impact = "Low"
        checked_score = min(checked_score, 20)
        qa_flags.append("AI itself marked this as not useful intelligence")


    # ========================================================
    # RULE 2 — academic / research-heavy pages
    # ========================================================

    if academic_hits >= 2:
        qa_flags.append("Academic/research-style source detected")

        if intelligence_type not in [
            "Regulation",
            "Policy",
            "Business Opportunity"
        ]:
            final_tier = "USEFUL BACKGROUND"

            if checked_relevance == "High":
                checked_relevance = "Medium"

            if checked_impact == "High":
                checked_impact = "Medium"

            checked_score = min(checked_score, 60)


    # ========================================================
    # RULE 3 — historical content
    # ========================================================

    if freshness.lower() == "historical":
        qa_flags.append("Historical content detected")

        if final_tier == "STRONG BUSINESS INTELLIGENCE":
            final_tier = "USEFUL BACKGROUND"

        if checked_impact == "High":
            checked_impact = "Medium"

        checked_score = min(checked_score, 55)


    # ========================================================
    # RULE 4 — generic content downgrade
    # ========================================================

    if (
        intelligence_type in ["General Information", "Other"]
        or generic_hits >= 1
    ):
        qa_flags.append("Generic or broad information source")

        if checked_relevance == "High":
            checked_relevance = "Medium"

        if checked_impact == "High":
            checked_impact = "Medium"

        checked_score = min(checked_score, 55)

        if final_tier != "LOW VALUE":
            final_tier = "USEFUL BACKGROUND"


    # ========================================================
    # RULE 5 — weak recommended action
    # ========================================================

    if weak_action:
        qa_flags.append("Recommended action is generic, not strongly actionable")

        if checked_impact == "High":
            checked_impact = "Medium"

        checked_score = min(checked_score, 65)


    # ========================================================
    # RULE 6 — strong regulation / policy source
    # ========================================================

    if (
        intelligence_type in ["Regulation", "Policy"]
        and source_quality == "High"
        and regulation_hits >= 1
        and checked_relevance in ["High", "Medium"]
    ):
        final_tier = "STRONG BUSINESS INTELLIGENCE"
        qa_flags.append("Strong regulation/policy signal")


    # ========================================================
    # RULE 7 — strong market / opportunity source
    # ========================================================

    elif (
        intelligence_type in [
            "Market Trend",
            "Consumer Trend",
            "Business Opportunity",
            "Technology",
            "Circular Economy Development",
            "Sustainable Packaging Development",
            "Traceability Development",
            "Supply Chain Development"
        ]
        and checked_relevance in ["High", "Medium"]
        and checked_impact in ["High", "Medium"]
        and source_quality in ["High", "Standard"]
        and (
            market_hits >= 1
            or source_quality == "High"
            or opportunity_or_risk in ["Opportunity", "Both"]
        )
    ):
        if academic_hits == 0 and generic_hits == 0:
            final_tier = "STRONG BUSINESS INTELLIGENCE"
            qa_flags.append("Strong business-use signal")
        else:
            final_tier = "USEFUL BACKGROUND"


    # ========================================================
    # RULE 8 — low source quality + exaggerated rating
    # ========================================================

    if (
        source_quality == "Standard"
        and checked_relevance == "High"
        and checked_impact == "High"
        and intelligence_type in ["General Information", "Other"]
    ):
        checked_relevance = "Medium"
        checked_impact = "Medium"
        checked_score = min(checked_score, 50)
        final_tier = "USEFUL BACKGROUND"
        qa_flags.append("Downgraded exaggerated rating on standard-quality generic source")


    # ========================================================
    # RULE 9 — if score is very low, final tier low value
    # ========================================================

    if checked_score <= 25:
        final_tier = "LOW VALUE"

    # if relevance low and impact low, low value
    if checked_relevance == "Low" and checked_impact == "Low":
        final_tier = "LOW VALUE"


    # ========================================================
    # final rule-checked recommendation
    # ========================================================

    if final_tier == "STRONG BUSINESS INTELLIGENCE":
        final_decision = "KEEP - PRIORITY REVIEW"

    elif final_tier == "USEFUL BACKGROUND":
        final_decision = "KEEP - BACKGROUND"

    else:
        final_decision = "LOW PRIORITY / IGNORE"


    return pd.Series({
        "Rule-Checked Relevance": checked_relevance,
        "Rule-Checked Impact": checked_impact,
        "Rule-Checked Relevance Score": checked_score,
        "Final Intelligence Tier": final_tier,
        "Final Intelligence Decision": final_decision,
        "QC Flags": " | ".join(qa_flags) if qa_flags else "No major issue detected"
    })


# ============================================================
# LOAD
# ============================================================

print("\nLoading Europe intelligence output...")

df = pd.read_csv(INPUT_FILE)

print(f"Rows loaded: {len(df)}")


# ============================================================
# APPLY RULES
# ============================================================

print("\nApplying intelligence quality-control rules...")

rule_results = df.apply(apply_rules, axis=1)

final_df = pd.concat([df, rule_results], axis=1)


# ============================================================
# SORT
# ============================================================

tier_order = {
    "STRONG BUSINESS INTELLIGENCE": 1,
    "USEFUL BACKGROUND": 2,
    "LOW VALUE": 3
}

final_df["_Tier Order"] = final_df["Final Intelligence Tier"].map(tier_order).fillna(99)

final_df = final_df.sort_values(
    by=["_Tier Order", "Rule-Checked Relevance Score"],
    ascending=[True, False]
)

final_df = final_df.drop(columns=["_Tier Order"])


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

print("\n======================================================")
print("EUROPE INTELLIGENCE QUALITY CONTROL COMPLETED")
print("======================================================")
print(f"Rows checked: {len(final_df)}")
print(f"Output: {OUTPUT_FILE}")

print("\nFinal intelligence tier:")
tier_counts = final_df["Final Intelligence Tier"].value_counts()
for tier, count in tier_counts.items():
    print(f"{tier}: {count}")

print("\nRule-checked relevance:")
rel_counts = final_df["Rule-Checked Relevance"].value_counts()
for rel, count in rel_counts.items():
    print(f"{rel}: {count}")

print("\nRule-checked impact:")
impact_counts = final_df["Rule-Checked Impact"].value_counts()
for imp, count in impact_counts.items():
    print(f"{imp}: {count}")

print("\nFinal intelligence decision:")
decision_counts = final_df["Final Intelligence Decision"].value_counts()
for dec, count in decision_counts.items():
    print(f"{dec}: {count}")