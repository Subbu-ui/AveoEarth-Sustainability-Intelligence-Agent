from pathlib import Path
from datetime import datetime
import shutil

import pandas as pd


# ============================================================
# SETTINGS
# ============================================================

SNAPSHOT_DIR = Path("snapshots")
HISTORY_DIR = Path("history")

SNAPSHOT_DIR.mkdir(exist_ok=True)
HISTORY_DIR.mkdir(exist_ok=True)

RUN_TIME = datetime.now()

TIMESTAMP = RUN_TIME.strftime("%Y%m%d_%H%M%S")


# ============================================================
# MODULE CONFIGURATION
# ============================================================

MODULES = {

    "Funding": {

        "current_file":
            "final_clean_funding_database.csv",

        "key_column":
            "Official Source URL",

        "tracked_fields": [
            "Opportunity Name",
            "Rule-Checked Current Status",
            "Deadline",
            "Rule-Checked AveoEarth Fit",
            "Final Sanity Decision"
        ]
    },


    "Europe Intelligence": {

        "current_file":
            "europe_intelligence_final_validated.csv",

        "key_column":
            "Source URL",

        "tracked_fields": [
            "Development",
            "Intelligence Type",
            "Freshness",
            "Validated Priority Level",
            "Validated Business Decision"
        ]
    },


    "India Intelligence": {

        "current_file":
            "india_sustainability_intelligence_validated.csv",

        "key_column":
            "Source URL",

        "tracked_fields": [
            "Development",
            "Intelligence Type",
            "Freshness",
            "Validated Priority",
            "Validated Business Decision"
        ]
    }
}


# ============================================================
# HELPERS
# ============================================================

def clean_value(value):

    if pd.isna(value):
        return ""

    return str(value).strip()


def safe_value(row, column):

    if column not in row.index:
        return ""

    return clean_value(
        row[column]
    )


# ============================================================
# DETERMINE CHANGE TYPE
# ============================================================

def determine_change_type(
    module_name,
    changed_fields
):

    changed_lower = [
        field.lower()
        for field in changed_fields
    ]


    # --------------------------------------------------------
    # FUNDING
    # --------------------------------------------------------

    if module_name == "Funding":

        if any(
            "deadline" in field
            for field in changed_lower
        ):
            return "DEADLINE CHANGED"

        if any(
            "status" in field
            for field in changed_lower
        ):
            return "STATUS CHANGED"

        if any(
            "decision" in field
            for field in changed_lower
        ):
            return "DECISION CHANGED"

        return "UPDATED"


    # --------------------------------------------------------
    # EUROPE / INDIA INTELLIGENCE
    # --------------------------------------------------------

    if any(
        "priority" in field
        for field in changed_lower
    ):
        return "PRIORITY CHANGED"

    if any(
        "decision" in field
        for field in changed_lower
    ):
        return "DECISION CHANGED"

    if any(
        "freshness" in field
        for field in changed_lower
    ):
        return "FRESHNESS CHANGED"

    return "UPDATED"


# ============================================================
# COMPARE MODULE
# ============================================================

def compare_module(
    module_name,
    config
):

    current_file = Path(
        config["current_file"]
    )

    key_column = config[
        "key_column"
    ]

    tracked_fields = config[
        "tracked_fields"
    ]


    print(
        "\n======================================================"
    )

    print(
        f"MODULE: {module_name}"
    )

    print(
        "======================================================"
    )


    # --------------------------------------------------------
    # CHECK CURRENT FILE
    # --------------------------------------------------------

    if not current_file.exists():

        print(
            f"Current file missing: {current_file}"
        )

        return []


    current_df = pd.read_csv(
        current_file
    )


    if key_column not in current_df.columns:

        print(
            f"Key column missing: {key_column}"
        )

        return []


    current_df[key_column] = (
        current_df[key_column]
        .astype(str)
        .str.strip()
    )


    current_df = current_df[
        current_df[key_column] != ""
    ]


    # --------------------------------------------------------
    # SNAPSHOT FILE
    # --------------------------------------------------------

    snapshot_file = (
        SNAPSHOT_DIR
        / f"{module_name.lower().replace(' ', '_')}_latest.csv"
    )


    # --------------------------------------------------------
    # FIRST RUN
    # --------------------------------------------------------

    if not snapshot_file.exists():

        current_df.to_csv(
            snapshot_file,
            index=False,
            encoding="utf-8-sig"
        )


        history_copy = (
            HISTORY_DIR
            / f"{module_name.lower().replace(' ', '_')}_{TIMESTAMP}.csv"
        )


        current_df.to_csv(
            history_copy,
            index=False,
            encoding="utf-8-sig"
        )


        print(
            f"Baseline created with {len(current_df)} records."
        )

        print(
            "No previous run exists, so there are no changes to compare yet."
        )

        return []


    # --------------------------------------------------------
    # LOAD PREVIOUS SNAPSHOT
    # --------------------------------------------------------

    previous_df = pd.read_csv(
        snapshot_file
    )


    previous_df[key_column] = (
        previous_df[key_column]
        .astype(str)
        .str.strip()
    )


    previous_df = previous_df[
        previous_df[key_column] != ""
    ]


    # --------------------------------------------------------
    # REMOVE DUPLICATE KEYS
    # --------------------------------------------------------

    current_df = current_df.drop_duplicates(
        subset=[key_column],
        keep="first"
    )


    previous_df = previous_df.drop_duplicates(
        subset=[key_column],
        keep="first"
    )


    current_indexed = current_df.set_index(
        key_column,
        drop=False
    )

    previous_indexed = previous_df.set_index(
        key_column,
        drop=False
    )


    current_keys = set(
        current_indexed.index
    )

    previous_keys = set(
        previous_indexed.index
    )


    changes = []


    # ========================================================
    # NEW ITEMS
    # ========================================================

    new_keys = (
        current_keys
        - previous_keys
    )


    for key in new_keys:

        row = current_indexed.loc[key]


        changes.append({

            "Module":
                module_name,

            "Change Type":
                "NEW",

            "URL / Key":
                key,

            "Item":
                (
                    safe_value(
                        row,
                        "Opportunity Name"
                    )
                    or safe_value(
                        row,
                        "Development"
                    )
                    or safe_value(
                        row,
                        "Source Title"
                    )
                ),

            "Changed Fields":
                "New record",

            "Previous Value":
                "",

            "Current Value":
                "",

            "Detected At":
                RUN_TIME.isoformat(
                    timespec="seconds"
                )
        })


    # ========================================================
    # REMOVED ITEMS
    # ========================================================

    removed_keys = (
        previous_keys
        - current_keys
    )


    for key in removed_keys:

        row = previous_indexed.loc[key]


        changes.append({

            "Module":
                module_name,

            "Change Type":
                "REMOVED / NOT FOUND",

            "URL / Key":
                key,

            "Item":
                (
                    safe_value(
                        row,
                        "Opportunity Name"
                    )
                    or safe_value(
                        row,
                        "Development"
                    )
                    or safe_value(
                        row,
                        "Source Title"
                    )
                ),

            "Changed Fields":
                "Record not present in current run",

            "Previous Value":
                "",

            "Current Value":
                "",

            "Detected At":
                RUN_TIME.isoformat(
                    timespec="seconds"
                )
        })


    # ========================================================
    # EXISTING ITEMS
    # ========================================================

    common_keys = (
        current_keys
        & previous_keys
    )


    for key in common_keys:

        current_row = current_indexed.loc[
            key
        ]

        previous_row = previous_indexed.loc[
            key
        ]


        changed_fields = []

        previous_values = []

        current_values = []


        for field in tracked_fields:

            previous_value = safe_value(
                previous_row,
                field
            )

            current_value = safe_value(
                current_row,
                field
            )


            if (
                previous_value
                != current_value
            ):

                changed_fields.append(
                    field
                )

                previous_values.append(
                    f"{field}: {previous_value}"
                )

                current_values.append(
                    f"{field}: {current_value}"
                )


        if changed_fields:

            change_type = (
                determine_change_type(
                    module_name,
                    changed_fields
                )
            )


            changes.append({

                "Module":
                    module_name,

                "Change Type":
                    change_type,

                "URL / Key":
                    key,

                "Item":
                    (
                        safe_value(
                            current_row,
                            "Opportunity Name"
                        )
                        or safe_value(
                            current_row,
                            "Development"
                        )
                        or safe_value(
                            current_row,
                            "Source Title"
                        )
                    ),

                "Changed Fields":
                    " | ".join(
                        changed_fields
                    ),

                "Previous Value":
                    " | ".join(
                        previous_values
                    ),

                "Current Value":
                    " | ".join(
                        current_values
                    ),

                "Detected At":
                    RUN_TIME.isoformat(
                        timespec="seconds"
                    )
            })


    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print(
        f"Previous records: {len(previous_df)}"
    )

    print(
        f"Current records: {len(current_df)}"
    )

    print(
        f"New: {len(new_keys)}"
    )

    print(
        f"Removed / not found: {len(removed_keys)}"
    )

    print(
        f"Updated: {len(changes) - len(new_keys) - len(removed_keys)}"
    )


    # --------------------------------------------------------
    # SAVE NEW SNAPSHOT
    # --------------------------------------------------------

    current_df.to_csv(
        snapshot_file,
        index=False,
        encoding="utf-8-sig"
    )


    history_copy = (
        HISTORY_DIR
        / f"{module_name.lower().replace(' ', '_')}_{TIMESTAMP}.csv"
    )


    current_df.to_csv(
        history_copy,
        index=False,
        encoding="utf-8-sig"
    )


    return changes


# ============================================================
# RUN ALL MODULES
# ============================================================

print(
    "\n======================================================"
)

print(
    "AVEOEARTH CHANGE DETECTOR"
)

print(
    "======================================================"
)


all_changes = []


for module_name, config in MODULES.items():

    module_changes = compare_module(
        module_name,
        config
    )

    all_changes.extend(
        module_changes
    )


# ============================================================
# SAVE CHANGE LOG
# ============================================================

change_columns = [

    "Module",

    "Change Type",

    "URL / Key",

    "Item",

    "Changed Fields",

    "Previous Value",

    "Current Value",

    "Detected At"
]


changes_df = pd.DataFrame(
    all_changes,
    columns=change_columns
)


run_change_file = (
    HISTORY_DIR
    / f"change_log_{TIMESTAMP}.csv"
)


changes_df.to_csv(
    run_change_file,
    index=False,
    encoding="utf-8-sig"
)


changes_df.to_csv(
    "latest_change_summary.csv",
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
    "CHANGE DETECTION COMPLETED"
)

print(
    "======================================================"
)

print(
    f"Total changes detected: {len(changes_df)}"
)

print(
    "Latest summary: latest_change_summary.csv"
)

print(
    f"Historical log: {run_change_file}"
)


if len(changes_df) > 0:

    print(
        "\nChanges by type:"
    )

    counts = changes_df[
        "Change Type"
    ].value_counts()

    for change_type, count in counts.items():

        print(
            f"{change_type}: {count}"
        )


    print(
        "\nChanges by module:"
    )

    counts = changes_df[
        "Module"
    ].value_counts()

    for module, count in counts.items():

        print(
            f"{module}: {count}"
        )

else:

    print(
        "\nNo changes detected."
    )

    print(
        "If this is the first run, baselines were created."
    )