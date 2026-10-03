import argparse
import os
import py_compile
import subprocess
import sys

from datetime import datetime
from pathlib import Path


# ============================================================
# COMMAND-LINE OPTIONS
# ============================================================

parser = argparse.ArgumentParser(
    description="AveoEarth Sustainability & Funding Intelligence Agent"
)

parser.add_argument(
    "--test",
    action="store_true",
    help="Check scripts and databases without running live research."
)

parser.add_argument(
    "--only",
    choices=[
        "europe-analyser",
        "india-analyser",
        "change-detector"
    ],
    help="Run only one selected stage."
)

args = parser.parse_args()


# ============================================================
# GLOBAL UTF-8 SETTINGS
# ============================================================

os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUNBUFFERED"] = "1"


# ============================================================
# PATHS AND LOGGING
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

LOG_DIR = BASE_DIR / "agent_logs"
LOG_DIR.mkdir(exist_ok=True)

RUN_TIME = datetime.now()

TIMESTAMP = RUN_TIME.strftime(
    "%Y%m%d_%H%M%S"
)

LOG_FILE = (
    LOG_DIR
    / f"agent_run_{TIMESTAMP}.txt"
)


# ============================================================
# COMPLETE PIPELINE
# ============================================================

STAGES = [

    # ========================================================
    # MODULE 1 — EUROPEAN UNIVERSITY FUNDING
    # ========================================================

    {
        "module": "European Funding",
        "name": "Search funding opportunities",
        "script": "open_funding_search.py",
        "id": "funding-search"
    },

    {
        "module": "European Funding",
        "name": "AI funding verification",
        "script": "final_funding_verifier.py",
        "id": "funding-analyser"
    },

    {
        "module": "European Funding",
        "name": "Funding rule validation",
        "script": "post_process_funding.py",
        "id": "funding-rules"
    },

    {
        "module": "European Funding",
        "name": "Final funding sanity check",
        "script": "final_sanity_check.py",
        "id": "funding-sanity"
    },


    # ========================================================
    # MODULE 2 — EUROPE SUSTAINABILITY
    # ========================================================

    {
        "module": "Europe Sustainability",
        "name": "Search Europe sustainability intelligence",
        "script": "europe_sustainability_search.py",
        "id": "europe-search"
    },

    {
        "module": "Europe Sustainability",
        "name": "Analyse Europe sustainability intelligence",
        "script": "europe_intelligence_analyser.py",
        "id": "europe-analyser"
    },

    {
        "module": "Europe Sustainability",
        "name": "Europe intelligence quality control",
        "script": "post_process_europe_intelligence.py",
        "id": "europe-rules"
    },

    {
        "module": "Europe Sustainability",
        "name": "Europe business prioritisation",
        "script": "finalize_europe_intelligence.py",
        "id": "europe-priority"
    },

    {
        "module": "Europe Sustainability",
        "name": "Europe source authority validation",
        "script": "source_quality_gate.py",
        "id": "europe-source"
    },


    # ========================================================
    # MODULE 3 — INDIA SUSTAINABILITY
    # ========================================================

    {
        "module": "India Sustainability",
        "name": "Search India sustainability intelligence",
        "script": "india_sustainability_search.py",
        "id": "india-search"
    },

    {
        "module": "India Sustainability",
        "name": "Analyse India sustainability intelligence",
        "script": "india_intelligence_analyser.py",
        "id": "india-analyser"
    },

    {
        "module": "India Sustainability",
        "name": "India action and authority validation",
        "script": "india_action_sanity_check.py",
        "id": "india-rules"
    },


    # ========================================================
    # MODULE 4 — CHANGE DETECTION
    # ========================================================

    {
        "module": "Change Detection",
        "name": "Compare against previous run",
        "script": "change_detector.py",
        "id": "change-detector"
    }
]


# ============================================================
# EXPECTED FINAL OUTPUT FILES
# ============================================================

EXPECTED_OUTPUTS = [

    "final_clean_funding_database.csv",

    "europe_intelligence_final_validated.csv",

    "india_sustainability_intelligence_validated.csv",

    "latest_change_summary.csv"
]


# ============================================================
# LOG FUNCTION
# ============================================================

def write_log(message=""):

    print(
        message,
        flush=True
    )

    with open(
        LOG_FILE,
        "a",
        encoding="utf-8"
    ) as file:

        file.write(
            message + "\n"
        )


# ============================================================
# CHILD PROCESS ENVIRONMENT
# ============================================================

def build_child_environment():

    child_env = os.environ.copy()

    child_env["PYTHONUTF8"] = "1"
    child_env["PYTHONIOENCODING"] = "utf-8"
    child_env["PYTHONUNBUFFERED"] = "1"

    return child_env


# ============================================================
# RUN ONE STAGE
# ============================================================

def run_stage(
    stage,
    number=1,
    total=1
):

    module = stage[
        "module"
    ]

    name = stage[
        "name"
    ]

    script_name = stage[
        "script"
    ]

    script_path = (
        BASE_DIR
        / script_name
    )


    write_log()

    write_log(
        "=" * 70
    )

    write_log(
        f"STAGE {number}/{total}"
    )

    write_log(
        f"Module: {module}"
    )

    write_log(
        f"Task: {name}"
    )

    write_log(
        f"Script: {script_name}"
    )

    write_log(
        "=" * 70
    )


    # --------------------------------------------------------
    # CHECK SCRIPT EXISTS
    # --------------------------------------------------------

    if not script_path.exists():

        write_log(
            f"ERROR: Script not found: {script_path}"
        )

        return False


    child_env = build_child_environment()

    start_time = datetime.now()


    try:

        process = subprocess.Popen(

            [
                sys.executable,
                "-u",
                str(script_path)
            ],

            cwd=str(
                BASE_DIR
            ),

            stdout=subprocess.PIPE,

            stderr=subprocess.STDOUT,

            text=True,

            encoding="utf-8",

            errors="replace",

            env=child_env,

            bufsize=1
        )


        if process.stdout is not None:

            for line in process.stdout:

                cleaned_line = (
                    line.rstrip()
                )

                print(
                    cleaned_line,
                    flush=True
                )

                with open(
                    LOG_FILE,
                    "a",
                    encoding="utf-8"
                ) as file:

                    file.write(
                        cleaned_line
                        + "\n"
                    )


        return_code = (
            process.wait()
        )


        finish_time = datetime.now()

        duration = (
            finish_time
            - start_time
        )


        if return_code == 0:

            write_log(
                f"SUCCESS: {name}"
            )

            write_log(
                f"Duration: {duration}"
            )

            return True


        write_log(
            f"FAILED: {name}"
        )

        write_log(
            f"Exit code: {return_code}"
        )

        write_log(
            "Pipeline stopped to avoid using stale downstream data."
        )

        return False


    except Exception as error:

        write_log(
            f"ERROR running {script_name}"
        )

        write_log(
            str(error)
        )

        return False


# ============================================================
# SAFE TEST MODE
# ============================================================

def run_test_mode():

    print()

    print(
        "=" * 70
    )

    print(
        "AVEOEARTH AGENT — SAFE TEST MODE"
    )

    print(
        "=" * 70
    )

    print()

    print(
        "No Tavily searches, Ollama analyses, "
        "database updates or snapshot changes will occur."
    )

    print()


    passed = 0

    failed = 0


    for number, stage in enumerate(
        STAGES,
        start=1
    ):

        script_path = (
            BASE_DIR
            / stage["script"]
        )

        print(
            f"[{number}/{len(STAGES)}] "
            f"{stage['name']}"
        )


        if not script_path.exists():

            print(
                f"    MISSING: {stage['script']}"
            )

            failed += 1

            continue


        try:

            py_compile.compile(
                str(script_path),
                doraise=True
            )

            print(
                f"    OK: {stage['script']}"
            )

            passed += 1


        except Exception as error:

            print(
                f"    FAILED: {stage['script']}"
            )

            print(
                f"    {error}"
            )

            failed += 1


    # ========================================================
    # DATABASE CHECK
    # ========================================================

    print()

    print(
        "=" * 70
    )

    print(
        "CURRENT OUTPUT DATABASES"
    )

    print(
        "=" * 70
    )


    database_count = 0


    for filename in EXPECTED_OUTPUTS:

        path = (
            BASE_DIR
            / filename
        )


        if path.exists():

            size = (
                path.stat().st_size
            )

            print(
                f"OK: {filename} "
                f"({size:,} bytes)"
            )

            database_count += 1

        else:

            print(
                f"MISSING: {filename}"
            )


    # ========================================================
    # MEMORY CHECK
    # ========================================================

    print()

    print(
        "=" * 70
    )

    print(
        "AGENT MEMORY"
    )

    print(
        "=" * 70
    )


    for folder_name in [
        "snapshots",
        "history"
    ]:

        folder = (
            BASE_DIR
            / folder_name
        )


        if folder.exists():

            count = len(
                list(
                    folder.glob("*")
                )
            )

            print(
                f"OK: {folder_name}/ "
                f"({count} files)"
            )

        else:

            print(
                f"MISSING: {folder_name}/"
            )


    # ========================================================
    # TEST SUMMARY
    # ========================================================

    print()

    print(
        "=" * 70
    )

    print(
        "SAFE TEST COMPLETED"
    )

    print(
        "=" * 70
    )

    print(
        f"Scripts passed: {passed}"
    )

    print(
        f"Scripts failed: {failed}"
    )

    print(
        f"Final databases found: "
        f"{database_count}/{len(EXPECTED_OUTPUTS)}"
    )


    if failed == 0:

        print()

        print(
            "MASTER AGENT STRUCTURE IS READY."
        )

    else:

        print()

        print(
            "Fix the failed scripts before a live run."
        )


# ============================================================
# SINGLE-STAGE MODE
# ============================================================

def run_only_stage(stage_id):

    selected_stage = None


    for stage in STAGES:

        if stage[
            "id"
        ] == stage_id:

            selected_stage = stage

            break


    if selected_stage is None:

        print(
            f"Unknown stage: {stage_id}"
        )

        return


    print()

    print(
        "=" * 70
    )

    print(
        "SINGLE-STAGE TEST"
    )

    print(
        "=" * 70
    )

    print(
        f"Running only: "
        f"{selected_stage['name']}"
    )

    print()


    success = run_stage(
        selected_stage,
        1,
        1
    )


    print()


    if success:

        print(
            "SINGLE-STAGE TEST PASSED"
        )

    else:

        print(
            "SINGLE-STAGE TEST FAILED"
        )


# ============================================================
# FULL LIVE AGENT
# ============================================================

def run_full_agent():

    write_log()

    write_log(
        "=" * 70
    )

    write_log(
        "AVEOEARTH SUSTAINABILITY & FUNDING "
        "INTELLIGENCE AGENT"
    )

    write_log(
        "=" * 70
    )

    write_log(
        f"Started: {RUN_TIME}"
    )

    write_log(
        f"Python: {sys.executable}"
    )

    write_log(
        f"Working directory: {BASE_DIR}"
    )

    write_log(
        f"UTF-8 mode: "
        f"{os.environ.get('PYTHONUTF8')}"
    )

    write_log(
        f"Unbuffered mode: "
        f"{os.environ.get('PYTHONUNBUFFERED')}"
    )

    write_log(
        f"Log file: {LOG_FILE}"
    )


    completed = 0


    for number, stage in enumerate(
        STAGES,
        start=1
    ):

        success = run_stage(
            stage,
            number,
            len(STAGES)
        )


        if success:

            completed += 1

        else:

            write_log()

            write_log(
                "=" * 70
            )

            write_log(
                "AGENT STOPPED"
            )

            write_log(
                "=" * 70
            )

            write_log(
                f"Stages completed successfully: "
                f"{completed}/{len(STAGES)}"
            )

            write_log(
                f"Failed stage: {stage['name']}"
            )

            write_log(
                "Fix this stage before continuing."
            )

            return


    # ========================================================
    # SUCCESS
    # ========================================================

    finish_time = (
        datetime.now()
    )

    duration = (
        finish_time
        - RUN_TIME
    )


    write_log()

    write_log(
        "=" * 70
    )

    write_log(
        "AGENT RUN COMPLETED"
    )

    write_log(
        "=" * 70
    )

    write_log(
        f"Finished: {finish_time}"
    )

    write_log(
        f"Total duration: {duration}"
    )

    write_log(
        f"Stages completed successfully: "
        f"{completed}/{len(STAGES)}"
    )

    write_log()

    write_log(
        "ALL STAGES COMPLETED SUCCESSFULLY"
    )


    write_log()

    write_log(
        "Final output files:"
    )


    for filename in EXPECTED_OUTPUTS:

        write_log(
            f"- {filename}"
        )


    write_log()

    write_log(
        f"Detailed log: {LOG_FILE}"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    if args.test:

        run_test_mode()


    elif args.only:

        run_only_stage(
            args.only
        )


    else:

        run_full_agent()