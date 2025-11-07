# SDGE Technician Utilization Analysis
by Angela Hu, Subika Haider, Weijie (Jack) Zhang, Nathan Dang

*Note: we cannot publish the SDG&E dataset or the graphs that are produced in this repo to protect the privacy of their data.*

## Project Description

San Diego Gas & Electric (SDG&E) is committed to optimizing technician workforce efficiency to enhance service delivery and reduce operational costs. One way to calculate efficiency is through the utilization rate for technicians. This can be approximated as the amount of time that technicians spend enroute to a job site and working on a job site out of their 7 hour work shift. This project analyzes technician utilization patterns to identify opportunities for improvement in reducing the idle time that technicians are spending outside of their work.

## Required Packages

Before running the analysis, ensure you have the following Python packages installed:

### Core Dependencies
```bash
pip install pandas
pip install plotly
pip install requests
pip install pyarrow
```

## How to Run the Code

### Prerequisites
1. Ensure all required packages are installed (see above)
2. Place the following parquet files in a `sort/` directory:
   - `REP_ORD_ORDER.parquet`
   - `REP_ORD_JOB_CODE.parquet`
   - `REP_ORD_ORDER_STATE.parquet`
   - `REP_ASN_ASSIGNMENT.parquet`
   - `REP_LAB_RESOURCE.parquet`
   - `REP_LAB_USER.parquet`

### Running the Complete Analysis

#### Option 1: Run Full Analysis Pipeline
```bash
python eda.py
```
This will execute the complete analysis and generate all visualizations.

#### Option 2: Run Individual Components
```python
from preprocessing import load_data, calculate_technician_utilization
from eda import plot_utilization_histogram

# Load data
DF = load_data()

# Calculate technician utilization
tech_util = calculate_technician_utilization(DF)

# Create visualization
fig = plot_utilization_histogram(tech_util)
fig.show()
```