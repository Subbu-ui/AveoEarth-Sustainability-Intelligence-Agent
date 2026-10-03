import re
from datetime import date

import pandas as pd
from dateutil import parser


# ============================================================
# SETTINGS
# ============================================================

INPUT_FILE = "final_funding_opportunities.csv"
OUTPUT_FILE = "clean_funding_opportunities.csv"

TODAY = date.today()


# ============================================================
# HELPERS
# ============================================================

def clean_value(value):
    if pd.isna(value):
        return ""

    return str(value).strip()


def normalise_yes_no(value):
    value = clean_value(value).lower()

    if value == "yes":
        return "Yes"

    if value == "no":
        return "No"

    return "Unclear"


# ============================================================
# DEADLINE PARSER
# ============================================================

def parse_deadline(value):

    value = clean_value(value)

    if not value:
        return None

    if value.lower() in [
        "not stated",
        "unclear",
        "rolling",
        "none"
    ]:
        return None

    try:

        parsed = parser.parse(
            value,
            dayfirst=True,
            fuzzy=True
        )

        return parsed.date()

    except Exception:

        return None


# ============================================================
# CHECK IF STATUS LOOKS OPEN
# ============================================================

def status_is_open(value):

    value = clean_value(value).lower()

    return value in [
        "open",
        "upcoming",
        "rolling",
        "open - deadline today",
        "open – deadline today"
    ]


# ============================================================
# PROCESS ONE ROW
# ============================================================

def apply_rules(row):

    qa_flags = []

    # --------------------------------------------------------
    # Original AI values
    # --------------------------------------------------------

    real_funding = normalise_yes_no(
        row.get(
            "Is Real Funding",
            ""
        )
    )

    current_ai = normalise_yes_no(
        row.get(
            "Is Current Opportunity",
            ""
        )
    )

    status_ai = clean_value(
        row.get(
            "Current Status",
            ""
        )
    )

    deadline_text = clean_value(
        row.get(
            "Deadline",
            ""
        )
    )

    company_can_apply = normalise_yes_no(
        row.get(
            "Company Can Apply",
            ""
        )
    )

    existing_company_can_apply = normalise_yes_no(
        row.get(
            "Existing Company Can Apply",
            ""
        )
    )

    affiliation_required = normalise_yes_no(
        row.get(
            "University Affiliation Required",
            ""
        )
    )

    application_found = normalise_yes_no(
        row.get(
            "Application Process Found",
            ""
        )
    )

    opportunity_name = clean_value(
        row.get(
            "Opportunity Name",
            ""
        )
    )

    funding_provider = clean_value(
        row.get(
            "Funding Provider",
            ""
        )
    )


    # --------------------------------------------------------
    # Start from AI output
    # --------------------------------------------------------

    checked_status = status_ai

    checked_current = current_ai

    checked_fit = clean_value(
        row.get(
            "AveoEarth Funding Fit",
            "Unclear"
        )
    )

    try:
        checked_score = int(
            float(
                row.get(
                    "AveoEarth Fit Score",
                    0
                )
            )
        )

    except Exception:
        checked_score = 0


    checked_verification = clean_value(
        row.get(
            "Verification Status",
            "PARTIALLY VERIFIED"
        )
    )


    # ========================================================
    # RULE 1 — DEADLINE CHECK
    # ========================================================

    deadline = parse_deadline(
        deadline_text
    )

    if deadline is not None:

        if deadline < TODAY:

            checked_status = "Closed"
            checked_current = "No"

            if real_funding == "Yes":
                checked_verification = "VERIFIED CLOSED"

            qa_flags.append(
                "AI status corrected: deadline already passed"
            )


        elif deadline == TODAY:

            checked_status = "Open - deadline today"

            qa_flags.append(
                "Deadline is today"
            )


    # ========================================================
    # RULE 2 — NOT REAL FUNDING
    # ========================================================

    if real_funding == "No":

        checked_current = "No"

        checked_fit = "Not eligible"

        checked_score = 0

        checked_verification = "NOT FUNDING"

        qa_flags.append(
            "Rejected because page is not verified funding"
        )


    # ========================================================
    # RULE 3 — COMPANY CANNOT APPLY
    # ========================================================

    if company_can_apply == "No":

        checked_fit = "Not eligible"

        checked_score = 0

        qa_flags.append(
            "Companies are not eligible"
        )


    # ========================================================
    # RULE 4 — EXISTING COMPANY CANNOT APPLY
    # ========================================================

    if existing_company_can_apply == "No":

        checked_fit = "Not eligible"

        checked_score = 0

        qa_flags.append(
            "Existing companies cannot apply"
        )


    # ========================================================
    # RULE 5 — AFFILIATION CONTRADICTION
    # ========================================================

    if (
        affiliation_required == "Yes"
        and existing_company_can_apply == "Yes"
    ):

        qa_flags.append(
            "Manual review: existing company allowed but university affiliation also required"
        )

        if checked_fit == "High":

            checked_fit = "Conditional"

            checked_score = min(
                checked_score,
                50
            )


    # ========================================================
    # RULE 6 — AFFILIATION + COMPANY INELIGIBILITY
    # ========================================================

    if (
        affiliation_required == "Yes"
        and existing_company_can_apply == "No"
    ):

        checked_fit = "Not eligible"

        checked_score = 0


    # ========================================================
    # RULE 7 — OPEN STATUS WITHOUT APPLICATION ROUTE
    # ========================================================

    if (
        status_is_open(checked_status)
        and application_found == "No"
    ):

        checked_status = "Unclear"

        checked_current = "Unclear"

        checked_verification = "PARTIALLY VERIFIED"

        qa_flags.append(
            "Open status rejected because no application process was found"
        )


    # ========================================================
    # RULE 8 — OPEN BUT DEADLINE NOT STATED
    # ========================================================

    if (
        deadline is None
        and clean_value(status_ai).lower() == "open"
    ):

        qa_flags.append(
            "Current status requires manual confirmation because no deadline was found"
        )


    # ========================================================
    # RULE 9 — POSSIBLE FUNDING PROVIDER ISSUE
    # ========================================================

    opportunity_lower = opportunity_name.lower()

    provider_lower = funding_provider.lower()


    if "exist" in opportunity_lower:

        university_terms = [
            "university of",
            "technische universität",
            "technical university",
            "tu dresden",
            "tu berlin"
        ]

        if any(
            term in provider_lower
            for term in university_terms
        ):

            qa_flags.append(
                "Check funding provider against official EXIST source"
            )


    if "go-bio" in opportunity_lower:

        if (
            "universität" in provider_lower
            or "university" in provider_lower
        ):

            qa_flags.append(
                "Check GO-Bio funding provider against official programme source"
            )


    # ========================================================
    # FINAL DECISION
    # ========================================================

    if checked_status == "Closed":

        final_decision = "ARCHIVE - CLOSED"


    elif checked_fit == "Not eligible":

        final_decision = "REJECT - NOT ELIGIBLE"


    elif checked_status == "Open - deadline today":

        if (
            existing_company_can_apply == "Yes"
            and application_found == "Yes"
        ):

            final_decision = "URGENT MANUAL REVIEW"

        else:

            final_decision = "REVIEW"


    elif (
        checked_status in [
            "Open",
            "Upcoming",
            "Rolling"
        ]
        and checked_fit in [
            "High",
            "Medium"
        ]
        and existing_company_can_apply == "Yes"
        and application_found == "Yes"
        and affiliation_required != "Yes"
    ):

        final_decision = "ACTIONABLE LEAD"


    elif checked_fit == "Conditional":

        final_decision = "REVIEW ELIGIBILITY"


    else:

        final_decision = "MANUAL REVIEW"


    # ========================================================
    # RETURN NEW FIELDS
    # ========================================================

    return pd.Series({

        "Parsed Deadline":
            deadline.isoformat()
            if deadline
            else "Not parsed",

        "Rule-Checked Current Status":
            checked_status,

        "Rule-Checked Is Current":
            checked_current,

        "Rule-Checked AveoEarth Fit":
            checked_fit,

        "Rule-Checked Fit Score":
            checked_score,

        "Rule-Checked Verification":
            checked_verification,

        "Final Agent Decision":
            final_decision,

        "QA Flags":
            " | ".join(qa_flags)
            if qa_flags
            else "No major issue detected"
    })


# ============================================================
# LOAD DATA
# ============================================================

print("\nLoading AI verification results...")

df = pd.read_csv(
    INPUT_FILE
)

print(
    f"Rows loaded: {len(df)}"
)

print(
    f"Rule-check date: {TODAY}"
)


# ============================================================
# APPLY RULE ENGINE
# ============================================================

print(
    "\nApplying deterministic quality-control rules..."
)

rule_results = df.apply(
    apply_rules,
    axis=1
)

final_df = pd.concat(
    [
        df,
        rule_results
    ],
    axis=1
)


# ============================================================
# SORT RESULTS
# ============================================================

decision_order = {

    "ACTIONABLE LEAD": 1,

    "URGENT MANUAL REVIEW": 2,

    "REVIEW ELIGIBILITY": 3,

    "MANUAL REVIEW": 4,

    "REVIEW": 5,

    "REJECT - NOT ELIGIBLE": 6,

    "ARCHIVE - CLOSED": 7
}


final_df[
    "_Decision Order"
] = final_df[
    "Final Agent Decision"
].map(
    decision_order
).fillna(99)


final_df = final_df.sort_values(
    by=[
        "_Decision Order",
        "Rule-Checked Fit Score"
    ],
    ascending=[
        True,
        False
    ]
)


final_df = final_df.drop(
    columns=[
        "_Decision Order"
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
    "FUNDING QUALITY CONTROL COMPLETED"
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
    "\nFinal agent decisions:"
)

decision_counts = final_df[
    "Final Agent Decision"
].value_counts()

for decision, count in decision_counts.items():

    print(
        f"{decision}: {count}"
    )


print(
    "\nRule-checked status:"
)

status_counts = final_df[
    "Rule-Checked Current Status"
].value_counts()

for status, count in status_counts.items():

    print(
        f"{status}: {count}"
    )


print(
    "\nRule-checked AveoEarth fit:"
)

fit_counts = final_df[
    "Rule-Checked AveoEarth Fit"
].value_counts()

for fit, count in fit_counts.items():

    print(
        f"{fit}: {count}"
    )