from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AveoEarth Intelligence Agent",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

FUNDING_FILE = BASE_DIR / "final_clean_funding_database.csv"

EUROPE_FILE = BASE_DIR / "europe_intelligence_final_validated.csv"

INDIA_FILE = BASE_DIR / "india_sustainability_intelligence_validated.csv"

CHANGE_FILE = BASE_DIR / "latest_change_summary.csv"


# ============================================================
# CUSTOM DESIGN
# ============================================================

st.markdown(
    """
    <style>

    .block-container {
        padding-top: 2rem;
        padding-bottom: 4rem;
        max-width: 1500px;
    }

    h1 {
        font-size: 3rem !important;
        font-weight: 750 !important;
        letter-spacing: -1px;
    }

    h2 {
        margin-top: 1.2rem;
    }

    div[data-testid="stMetric"] {
        border: 1px solid rgba(150,150,150,0.20);
        padding: 18px;
        border-radius: 14px;
    }

    .hero-subtitle {
        font-size: 1.05rem;
        opacity: 0.72;
        margin-bottom: 25px;
    }

    .section-note {
        opacity: 0.70;
        font-size: 0.95rem;
    }

    .status-good {
        padding: 12px 16px;
        border-radius: 10px;
        border-left: 4px solid #45c96b;
        background: rgba(69, 201, 107, 0.08);
        margin-bottom: 12px;
    }

    .status-watch {
        padding: 12px 16px;
        border-radius: 10px;
        border-left: 4px solid #ffb020;
        background: rgba(255, 176, 32, 0.08);
        margin-bottom: 12px;
    }

    .small-muted {
        font-size: 0.85rem;
        opacity: 0.65;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# DATA HELPERS
# ============================================================

@st.cache_data
def load_csv(path):

    if not path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(path)

    except Exception:
        return pd.DataFrame()


def safe_count(
    df,
    column,
    value
):

    if df.empty:
        return 0

    if column not in df.columns:
        return 0

    return int(
        (
            df[column]
            .astype(str)
            .str.strip()
            == value
        ).sum()
    )


def safe_values(
    df,
    column
):

    if df.empty:
        return []

    if column not in df.columns:
        return []

    return sorted(
        df[column]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )


def available_columns(
    df,
    requested
):

    return [
        column
        for column in requested
        if column in df.columns
    ]


def latest_date_from_dataframes(
    dataframes
):

    dates = []

    for df in dataframes:

        if (
            not df.empty
            and "Date Checked" in df.columns
        ):

            parsed = pd.to_datetime(
                df["Date Checked"],
                errors="coerce"
            )

            if parsed.notna().any():

                dates.append(
                    parsed.max()
                )


    if dates:

        return max(dates).strftime(
            "%d %B %Y"
        )


    return "Not available"


# ============================================================
# LOAD DATA
# ============================================================

funding_df = load_csv(
    FUNDING_FILE
)

europe_df = load_csv(
    EUROPE_FILE
)

india_df = load_csv(
    INDIA_FILE
)

change_df = load_csv(
    CHANGE_FILE
)


# ============================================================
# CORE METRICS
# ============================================================

funding_total = len(
    funding_df
)

europe_total = len(
    europe_df
)

india_total = len(
    india_df
)

change_total = len(
    change_df
)


funding_actionable = safe_count(
    funding_df,
    "Final Sanity Decision",
    "ACTIONABLE LEAD"
)


europe_priority = safe_count(
    europe_df,
    "Validated Priority Level",
    "PRIORITY"
)


europe_strategy = safe_count(
    europe_df,
    "Validated Business Decision",
    "KEEP FOR STRATEGY"
)


europe_verify = safe_count(
    europe_df,
    "Validated Business Decision",
    "VERIFY WITH STRONGER SOURCE"
)


india_priority = safe_count(
    india_df,
    "Validated Priority",
    "PRIORITY"
)


india_strategy = safe_count(
    india_df,
    "Validated Business Decision",
    "KEEP FOR STRATEGY"
)


india_verify = safe_count(
    india_df,
    "Validated Business Decision",
    "VERIFY WITH STRONGER SOURCE"
)


last_checked = latest_date_from_dataframes(
    [
        funding_df,
        europe_df,
        india_df
    ]
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title(
        "AveoEarth Agent"
    )

    st.caption(
        "Sustainability & Funding Intelligence"
    )

    st.divider()

    st.markdown(
        "### System"
    )

    st.write(
        "🔎 Tavily Web Search"
    )

    st.write(
        "🧠 Ollama / Llama 3.2"
    )

    st.write(
        "🐍 Python"
    )

    st.write(
        "✅ Rule-based verification"
    )

    st.write(
        "🗂 Historical memory"
    )

    st.write(
        "🔄 Change detection"
    )

    st.divider()

    st.markdown(
        "### Data status"
    )

    st.write(
        f"**Last checked:** {last_checked}"
    )

    st.write(
        f"**Funding records:** {funding_total}"
    )

    st.write(
        f"**Europe records:** {europe_total}"
    )

    st.write(
        f"**India records:** {india_total}"
    )

    st.divider()

    st.caption(
        "Built as an automated business-intelligence workflow for AveoEarth."
    )


# ============================================================
# HERO
# ============================================================

st.title(
    "🌍 AveoEarth Sustainability & Funding Intelligence Agent"
)

st.markdown(
    """
    <div class="hero-subtitle">
    Automated discovery, verification and monitoring of European
    funding opportunities and sustainability intelligence across
    Europe and India.
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# EXECUTIVE SUMMARY METRICS
# ============================================================

st.header(
    "Executive Overview"
)


col1, col2, col3, col4 = st.columns(
    4
)


with col1:

    st.metric(
        "Funding Opportunities Analysed",
        funding_total,
        help="European university-linked funding pages processed through the verification workflow."
    )

    st.caption(
        f"{funding_actionable} currently actionable"
    )


with col2:

    st.metric(
        "Europe Intelligence Items",
        europe_total
    )

    st.caption(
        f"{europe_priority} immediate priority"
    )


with col3:

    st.metric(
        "India Intelligence Items",
        india_total
    )

    st.caption(
        f"{india_priority} validated priority items"
    )


with col4:

    st.metric(
        "Latest Changes Detected",
        change_total
    )

    st.caption(
        "Compared with stored agent memory"
    )


st.divider()


# ============================================================
# EXECUTIVE INTERPRETATION
# ============================================================

st.subheader(
    "Management Snapshot"
)


col1, col2 = st.columns(
    2
)


with col1:

    st.markdown(
        f"""
        <div class="status-good">
        <b>India intelligence</b><br>
        {india_priority} item(s) currently meet the strict priority
        threshold, while {india_strategy} item(s) remain useful for
        strategic monitoring.
        </div>
        """,
        unsafe_allow_html=True
    )


with col2:

    st.markdown(
        f"""
        <div class="status-watch">
        <b>Europe intelligence</b><br>
        {europe_strategy} item(s) are retained for strategic monitoring
        and {europe_verify} item(s) require confirmation from a stronger
        source before management action.
        </div>
        """,
        unsafe_allow_html=True
    )


if funding_actionable == 0:

    st.info(
        "The latest European university-funding cycle produced no fully verified actionable funding lead. "
        "Expired, ineligible and information-only results were removed by the verification workflow."
    )


# ============================================================
# TABS
# ============================================================

tab_overview, tab_funding, tab_europe, tab_india, tab_changes = st.tabs(
    [
        "🏠 Overview",
        "💶 European Funding",
        "🇪🇺 Europe Sustainability",
        "🇮🇳 India Sustainability",
        "🔄 Change Monitor"
    ]
)


# ============================================================
# OVERVIEW TAB
# ============================================================

with tab_overview:

    st.header(
        "How the Agent Works"
    )


    st.code(
        """
Web Search
      ↓
Source Discovery
      ↓
Official / Relevant Page Collection
      ↓
Local AI Interpretation
      ↓
Rule-Based Verification
      ↓
Source Authority Check
      ↓
Eligibility & Business Relevance
      ↓
Priority / Watchlist / Reject
      ↓
Historical Snapshot Comparison
      ↓
Management Dashboard
        """,
        language=None
    )


    st.subheader(
        "Current Intelligence Base"
    )


    overview_df = pd.DataFrame(
        {
            "Module": [
                "European University Funding",
                "Europe Sustainability Intelligence",
                "India Sustainability Intelligence",
                "Change Detection"
            ],

            "Records": [
                funding_total,
                europe_total,
                india_total,
                change_total
            ],

            "Purpose": [
                "Identify potentially accessible funding opportunities",
                "Track European sustainability developments",
                "Track Indian schemes, market developments and opportunities",
                "Identify changes between research cycles"
            ]
        }
    )


    st.dataframe(
        overview_df,
        width="stretch",
        hide_index=True
    )


    st.subheader(
        "Current Management Signals"
    )


    signal_df = pd.DataFrame(
        {
            "Signal": [
                "Funding — Actionable",
                "Europe — Priority",
                "Europe — Verify Stronger Source",
                "India — Priority",
                "India — Keep for Strategy",
                "India — Verify Stronger Source"
            ],

            "Count": [
                funding_actionable,
                europe_priority,
                europe_verify,
                india_priority,
                india_strategy,
                india_verify
            ]
        }
    )


    st.bar_chart(
        signal_df.set_index(
            "Signal"
        ),
        width="stretch"
    )


# ============================================================
# FUNDING TAB
# ============================================================

with tab_funding:

    st.header(
        "European University Funding"
    )

    st.caption(
        "Discovery and verification of university-linked grants, "
        "startup programmes and non-dilutive funding."
    )


    if funding_df.empty:

        st.warning(
            "Funding database is unavailable."
        )

    else:

        closed_count = safe_count(
            funding_df,
            "Rule-Checked Current Status",
            "Closed"
        )


        ineligible_count = safe_count(
            funding_df,
            "Rule-Checked AveoEarth Fit",
            "Not eligible"
        )


        conditional_count = safe_count(
            funding_df,
            "Rule-Checked AveoEarth Fit",
            "Conditional"
        )


        c1, c2, c3, c4 = st.columns(
            4
        )


        c1.metric(
            "Analysed",
            funding_total
        )

        c2.metric(
            "Actionable",
            funding_actionable
        )

        c3.metric(
            "Closed",
            closed_count
        )

        c4.metric(
            "Not Eligible",
            ineligible_count
        )


        st.subheader(
            "Decision Breakdown"
        )


        decision_column = None


        for candidate in [
            "Final Sanity Decision",
            "Final Agent Decision"
        ]:

            if candidate in funding_df.columns:

                decision_column = candidate

                break


        if decision_column:

            counts = (
                funding_df[
                    decision_column
                ]
                .fillna("Unknown")
                .value_counts()
                .rename_axis(
                    "Decision"
                )
                .reset_index(
                    name="Count"
                )
            )


            st.bar_chart(
                counts.set_index(
                    "Decision"
                ),
                width="stretch"
            )


        st.subheader(
            "Funding Records"
        )


        funding_columns = available_columns(
            funding_df,
            [
                "University / Organization",
                "Opportunity Name",
                "Funding Provider",
                "Funding Amount",
                "Funding Type",
                "Deadline",
                "Rule-Checked Current Status",
                "Rule-Checked AveoEarth Fit",
                "Final Agent Decision",
                "Final Sanity Decision",
                "Official Source URL"
            ]
        )


        st.dataframe(
            funding_df[
                funding_columns
            ],
            width="stretch",
            hide_index=True
        )


        st.download_button(
            "Download funding database",
            funding_df.to_csv(
                index=False
            ).encode(
                "utf-8"
            ),
            file_name="aveoearth_funding_intelligence.csv",
            mime="text/csv"
        )


# ============================================================
# EUROPE TAB
# ============================================================

with tab_europe:

    st.header(
        "Europe Sustainability Intelligence"
    )


    if europe_df.empty:

        st.warning(
            "Europe sustainability database is unavailable."
        )

    else:

        c1, c2, c3 = st.columns(
            3
        )


        c1.metric(
            "Intelligence Items",
            europe_total
        )

        c2.metric(
            "Keep for Strategy",
            europe_strategy
        )

        c3.metric(
            "Verify Stronger Source",
            europe_verify
        )


        st.subheader(
            "Decision Breakdown"
        )


        if (
            "Validated Business Decision"
            in europe_df.columns
        ):

            counts = (
                europe_df[
                    "Validated Business Decision"
                ]
                .fillna("Unknown")
                .value_counts()
                .rename_axis(
                    "Decision"
                )
                .reset_index(
                    name="Count"
                )
            )


            st.bar_chart(
                counts.set_index(
                    "Decision"
                ),
                width="stretch"
            )


        st.subheader(
            "Explore Intelligence"
        )


        europe_topics = [
            "All"
        ] + safe_values(
            europe_df,
            "Search Topic"
        )


        selected_europe_topic = st.selectbox(
            "Filter by topic",
            europe_topics,
            key="europe_filter"
        )


        europe_filtered = (
            europe_df.copy()
        )


        if (
            selected_europe_topic != "All"
            and "Search Topic"
            in europe_filtered.columns
        ):

            europe_filtered = (
                europe_filtered[
                    europe_filtered[
                        "Search Topic"
                    ]
                    == selected_europe_topic
                ]
            )


        europe_columns = available_columns(
            europe_filtered,
            [
                "Search Topic",
                "Development",
                "Intelligence Type",
                "What Happened",
                "Rule-Checked Relevance",
                "Rule-Checked Impact",
                "Validated Priority Level",
                "Validated Business Decision",
                "Recommended Action",
                "Source Domain",
                "Source URL"
            ]
        )


        st.dataframe(
            europe_filtered[
                europe_columns
            ],
            width="stretch",
            hide_index=True
        )


        st.download_button(
            "Download Europe intelligence",
            europe_df.to_csv(
                index=False
            ).encode(
                "utf-8"
            ),
            file_name="aveoearth_europe_intelligence.csv",
            mime="text/csv"
        )


# ============================================================
# INDIA TAB
# ============================================================

with tab_india:

    st.header(
        "India Sustainability Intelligence"
    )


    if india_df.empty:

        st.warning(
            "India sustainability database is unavailable."
        )

    else:

        low_priority = safe_count(
            india_df,
            "Validated Business Decision",
            "LOW PRIORITY"
        )


        c1, c2, c3, c4 = st.columns(
            4
        )


        c1.metric(
            "Intelligence Items",
            india_total
        )

        c2.metric(
            "Act / Review Now",
            india_priority
        )

        c3.metric(
            "Keep for Strategy",
            india_strategy
        )

        c4.metric(
            "Verify Source",
            india_verify
        )


        st.subheader(
            "Business Decision Breakdown"
        )


        if (
            "Validated Business Decision"
            in india_df.columns
        ):

            counts = (
                india_df[
                    "Validated Business Decision"
                ]
                .fillna("Unknown")
                .value_counts()
                .rename_axis(
                    "Decision"
                )
                .reset_index(
                    name="Count"
                )
            )


            st.bar_chart(
                counts.set_index(
                    "Decision"
                ),
                width="stretch"
            )


        # ----------------------------------------------------
        # ACTIONABLE INDIA ITEMS
        # ----------------------------------------------------

        st.subheader(
            "Top Action / Review Items"
        )


        if (
            "Validated Business Decision"
            in india_df.columns
        ):

            india_actions = (
                india_df[
                    india_df[
                        "Validated Business Decision"
                    ]
                    == "ACT / REVIEW NOW"
                ]
            )


            if india_actions.empty:

                st.info(
                    "No India item currently meets the immediate action threshold."
                )

            else:

                for _, row in india_actions.iterrows():

                    development = row.get(
                        "Development",
                        "Untitled development"
                    )

                    authority = row.get(
                        "Validated Implementing Authority",
                        row.get(
                            "Government Body / Organization",
                            "Not stated"
                        )
                    )

                    action = row.get(
                        "Validated Recommended Action",
                        row.get(
                            "Recommended Action",
                            "Not stated"
                        )
                    )

                    source = row.get(
                        "Source URL",
                        ""
                    )


                    with st.container(
                        border=True
                    ):

                        st.markdown(
                            f"### {development}"
                        )

                        st.write(
                            f"**Implementing authority:** {authority}"
                        )

                        st.write(
                            f"**Recommended action:** {action}"
                        )

                        if pd.notna(
                            source
                        ):

                            st.write(
                                f"**Source:** {source}"
                            )


        st.subheader(
            "Explore India Intelligence"
        )


        india_topics = [
            "All"
        ] + safe_values(
            india_df,
            "Search Topic"
        )


        selected_india_topic = st.selectbox(
            "Filter by topic",
            india_topics,
            key="india_filter"
        )


        india_filtered = (
            india_df.copy()
        )


        if (
            selected_india_topic != "All"
            and "Search Topic"
            in india_filtered.columns
        ):

            india_filtered = (
                india_filtered[
                    india_filtered[
                        "Search Topic"
                    ]
                    == selected_india_topic
                ]
            )


        india_columns = available_columns(
            india_filtered,
            [
                "Search Topic",
                "Development",
                "Intelligence Type",
                "Scheme / Program",
                "Government Body / Organization",
                "Validated Implementing Authority",
                "Validated Priority",
                "Validated Business Decision",
                "Validated Recommended Action",
                "Source URL"
            ]
        )


        st.dataframe(
            india_filtered[
                india_columns
            ],
            width="stretch",
            hide_index=True
        )


        st.download_button(
            "Download India intelligence",
            india_df.to_csv(
                index=False
            ).encode(
                "utf-8"
            ),
            file_name="aveoearth_india_intelligence.csv",
            mime="text/csv"
        )


# ============================================================
# CHANGE MONITOR
# ============================================================

with tab_changes:

    st.header(
        "Change Detection & Historical Monitoring"
    )

    st.write(
        """
        The agent stores previous research snapshots and compares
        them with future runs. This allows the workflow to distinguish
        newly discovered items from previously known information.
        """
    )


    st.subheader(
        "Change Types"
    )


    st.code(
        """
NEW
UPDATED
DEADLINE CHANGED
STATUS CHANGED
PRIORITY CHANGED
DECISION CHANGED
FRESHNESS CHANGED
REMOVED / NOT FOUND
        """,
        language=None
    )


    if change_df.empty:

        st.success(
            "No changes are currently recorded against the restored baseline."
        )

    else:

        st.metric(
            "Changes Detected",
            len(change_df)
        )


        if "Change Type" in change_df.columns:

            change_counts = (
                change_df[
                    "Change Type"
                ]
                .fillna("Unknown")
                .value_counts()
                .rename_axis(
                    "Change Type"
                )
                .reset_index(
                    name="Count"
                )
            )


            st.bar_chart(
                change_counts.set_index(
                    "Change Type"
                ),
                width="stretch"
            )


        st.dataframe(
            change_df,
            width="stretch",
            hide_index=True
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.markdown(
    f"""
    <div class="small-muted">
    AveoEarth Intelligence Agent • Local AI + Web Research •
    Dashboard generated from the latest validated datasets •
    Last research date: {last_checked}
    </div>
    """,
    unsafe_allow_html=True
)