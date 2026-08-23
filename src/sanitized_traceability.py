import pandas as pd
from pathlib import Path


# =================================================
# PATHS
# =================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PRIVATE_INPUT = (
    PROJECT_ROOT
    / "output"
    / "private"
    / "Master_Traceability_Report.xlsx"
)

PUBLIC_OUTPUT = (
    PROJECT_ROOT
    / "output"
    / "public"
    / "sample_traceability_report.xlsx"
)

SOURCE_SHEET = "Filtered Traceability"


# =================================================
# GENERIC PORTFOLIO VALUES
# =================================================

GENERIC_DEPARTMENTS = [
    "Assembly",
    "Final Test",
    "Electronics",
    "Machine Shop",
    "Quality Lab",
    "Production"
]


def clean_text(value):
    if pd.isna(value):
        return pd.NA

    cleaned = str(value).strip()

    if not cleaned:
        return pd.NA

    return cleaned


def create_alias_map(values, prefix):
    unique_values = sorted(
        {
            str(value).strip()
            for value in values
            if pd.notna(value)
            and str(value).strip()
        }
    )

    return {
        value: f"{prefix}-{index:04d}"
        for index, value in enumerate(
            unique_values,
            start=1
        )
    }


def anonymize_description(value):
    if pd.isna(value):
        return "Production Tool"

    text = str(value).casefold()

    if "driver" in text:
        return "Torque Driver"

    if "wrench" in text:
        return "Torque Wrench"

    if "tester" in text:
        return "Calibration Tester"

    if "analyzer" in text:
        return "Calibration Analyzer"

    if "torque" in text:
        return "Torque Tool"

    return "Production Tool"


def sanitize_traceability(
    input_file=PRIVATE_INPUT,
    output_file=PUBLIC_OUTPUT
):
    if not input_file.exists():
        raise FileNotFoundError(
            "Private traceability report was not found:\n"
            f"{input_file}"
        )

    report = pd.read_excel(
        input_file,
        sheet_name=SOURCE_SHEET,
        engine="openpyxl"
    )

    report.columns = (
        report.columns
        .astype(str)
        .str.strip()
    )

    required_columns = {
        "Calibration Date",
        "Item Number",
        "Description",
        "Department",
        "Item Settings",
        "Master Item"
    }

    missing_columns = (
        required_columns
        - set(report.columns)
    )

    if missing_columns:
        raise ValueError(
            "Required columns missing from the "
            "Filtered Traceability worksheet:\n"
            + "\n".join(sorted(missing_columns))
        )

    sanitized = report.copy()

    # ---------------------------------------------
    # Tool aliases
    # ---------------------------------------------

    tool_map = create_alias_map(
        sanitized["Item Number"],
        "TOOL"
    )

    sanitized["Item Number"] = (
        sanitized["Item Number"]
        .astype("string")
        .str.strip()
        .map(tool_map)
    )

    # ---------------------------------------------
    # Master aliases
    # ---------------------------------------------

    master_map = create_alias_map(
        sanitized["Master Item"],
        "MSTR"
    )

    sanitized["Master Item"] = (
        sanitized["Master Item"]
        .astype("string")
        .str.strip()
        .map(master_map)
    )

    # ---------------------------------------------
    # Technician aliases
    # ---------------------------------------------

    if "Entered By" in sanitized.columns:
        operator_map = create_alias_map(
            sanitized["Entered By"],
            "TECH"
        )

        sanitized["Entered By"] = (
            sanitized["Entered By"]
            .astype("string")
            .str.strip()
            .map(operator_map)
            .str.replace(
                "TECH-",
                "Technician ",
                regex=False
            )
        )

    # ---------------------------------------------
    # Generic departments
    # ---------------------------------------------

    real_departments = sorted(
        sanitized["Department"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
    )

    department_map = {
        department: GENERIC_DEPARTMENTS[
            index % len(GENERIC_DEPARTMENTS)
        ]
        for index, department in enumerate(
            real_departments
        )
    }

    sanitized["Department"] = (
        sanitized["Department"]
        .astype("string")
        .str.strip()
        .map(department_map)
    )

    # ---------------------------------------------
    # Generic descriptions
    # ---------------------------------------------

    sanitized["Description"] = (
        sanitized["Description"]
        .apply(anonymize_description)
    )

    # ---------------------------------------------
    # Synthetic dates preserving row order
    # ---------------------------------------------

    sanitized["Calibration Date"] = pd.to_datetime(
        sanitized["Calibration Date"],
        errors="coerce"
    )

    sanitized = sanitized.sort_values(
        by=["Calibration Date", "Item Number"],
        na_position="last"
    ).reset_index(drop=True)

    synthetic_start = pd.Timestamp("2026-01-15")

    sanitized["Calibration Date"] = [
        synthetic_start
        + pd.Timedelta(days=index * 7)
        for index in range(len(sanitized))
    ]

    # ---------------------------------------------
    # Replace company references in text fields
    # ---------------------------------------------

    for column in sanitized.select_dtypes(
        include=["object", "string"]
    ).columns:

        sanitized[column] = (
            sanitized[column]
            .astype("string")
            .str.replace(
                "AMETEK",
                "Company",
                case=False,
                regex=False
            )
        )

    # ---------------------------------------------
    # Keep only public portfolio columns
    # ---------------------------------------------

    public_columns = [
        "Calibration Date",
        "Item Number",
        "Description",
        "Department",
        "Item Settings",
        "Master Item",
        "Entered By",
        "Match Status",
        "Inventory Match Status"
    ]

    public_columns = [
        column
        for column in public_columns
        if column in sanitized.columns
    ]

    sanitized = sanitized[
        public_columns
    ].copy()

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with pd.ExcelWriter(
        output_file,
        engine="openpyxl",
        date_format="mm/dd/yyyy",
        datetime_format="mm/dd/yyyy"
    ) as writer:

        sanitized.to_excel(
            writer,
            sheet_name="Filtered Traceability",
            index=False
        )

    return sanitized


if __name__ == "__main__":
    result = sanitize_traceability()

    print(
        "Sanitized portfolio report created:"
    )

    print(PUBLIC_OUTPUT.resolve())

    print(
        f"Rows exported: {len(result):,}"
    )