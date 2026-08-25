# Calibration Master Traceability Pipeline

A Python-based data pipeline that transforms semi-structured calibration
records into a validated Excel traceability report.

The workflow combines calibration event history, master-equipment
assignments, inventory information, and tool settings to identify tools
associated with a selected calibration master during a defined period.

## Project Overview

Calibration information may be distributed across multiple Excel reports
with different structures:

1. A calibration-event history containing repeating item sections
2. An item-to-master assignment report
3. An inventory report containing descriptions, departments, and tool settings
4. Audit traceability to easily identify which tools were calibrated with which master, cleaner format.

This project normalizes those reports since I cannot publicly publish the company's items due to legal reasons, connects them by item number,
validates the relationships and creates a filtered traceability report.

## Business Question

> Which tools were associated with a selected calibration master during
> a specified date range, and what torque setting was assigned to each tool?

## Data Pipeline

```text
Calibration Event History
        |
        | Extract item-number headings
        | Fill item numbers into event records
        | Keep calibration events
        v
Normalized Calibration History
        |
        +--------------------------+
                                   |
Master Assignments ---------------+----> Traceability Merge
                                   |
Item Inventory and Settings ------+
                                   |
                                   v
                     Validation and Exception Checks
                                   |
                                   v
                     Filtered Traceability Report
