# SDGE Technician Utilization Analysis

by Angela Hu, Subika Haider, Weijie (Jack) Zhang, Nathan Dang

*Note: we cannot publish the SDG&E dataset or the graphs that are produced in this repo to protect the privacy of their data.*

## Project Description

San Diego Gas & Electric (SDG&E) is committed to optimizing technician workforce efficiency to enhance service delivery and reduce operational costs. One way to calculate efficiency is through the utilization rate for technicians. This can be approximated as the amount of time that technicians spend enroute to a job site and working on a job site out of their 7 hour work shift. This project analyzes technician utilization patterns to identify opportunities for improvement in reducing the idle time that technicians are spending outside of their work.

## Project Structure

The analysis code is organized into modular Python files within the `src/` directory:

### `preprocessing.py`

Core data processing and calculation module containing:

- **`load_data()`**: Loads and merges all required parquet datasets for technician and job data (orders, job codes, assignments, technician resources)
- **`load_california_geojson()`**: Fetches California zip code boundary data for mapping visualizations
- **Utilization calculation functions**:
  - `calculate_zip_utilization()`: Computes technician utilization metrics aggregated by zip code
  - `calculate_technician_utilization()`: Analyzes individual technician performance and utilization rates
  - `calculate_dispatch_area_utilization()`: Calculates utilization patterns by dispatch area
- **`prepare_job_lifecycle_analysis()`**: Processes job lifecycle data for timing analysis
- **Helper functions**: Including `expand_records_and_calculate_utilization()` for handling multi-day job records

### `eda.py`

Exploratory Data Analysis and visualization module featuring:

- **Geographic visualizations**: Choropleth maps showing utilization by zip code using Plotly
- **Statistical plots**: Histograms, scatter plots, and distribution analysis of utilization metrics
- **Performance analysis**: Visualizations for technician performance, job counts, and dispatch area comparisons
- **Job lifecycle analysis**: Timeline and duration analysis for different job types
- **`run_full_analysis()`**: Main function that executes the complete analysis pipeline and generates all visualizations

### `aggregate_analysis.py`

Advanced analytical functions for temporal and aggregate patterns:

- **Daily order volume analysis**: Time series analysis of job orders with interactive Plotly visualizations
- **Trend identification**: Functions to identify patterns in order volumes over time
- **Job type analysis**: Breakdown of order patterns by job type and time periods
- **Presentation-optimized plots**: Interactive visualizations designed for stakeholder presentations

### `dashboard.py`

Interactive dashboard module using Dash framework:

- **Real-time dashboard**: Web-based interactive dashboard for exploring utilization data
- **Multi-temporal views**: Dashboard components for daily, weekly, and monthly analysis
- **Interactive filtering**: User controls for date ranges, job types, and geographic regions
- **`start_app_dashboard()`**: Main function to launch the interactive web application

## Required Packages

Before running the analysis, ensure you have the following Python packages installed:

### Core Dependencies

```bash
pip install -r requirements.txt
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

### Option A: Using Docker (Recommended)

Build and run using Docker for a consistent environment:

```bash
# Build the Docker image
docker build -t sdge-tech-analysis .

# Run analysis script directly
docker run -v "$(pwd)":/home/jovyan/work -w /home/jovyan/work sdge-tech-analysis python src/eda.py
```

### Option B: Local Python Environment

#### Option 1: Run Full Analysis Pipeline

```bash
python src/eda.py
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
