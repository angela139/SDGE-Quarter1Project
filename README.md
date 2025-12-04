# SDGE Technician Utilization Analysis

by Angela Hu, Subika Haider, Weijie (Jack) Zhang, Nathan Dang

_Note: we cannot publish the SDG&E dataset or the graphs that are produced in this repo to protect the privacy of their data._

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

### `optimization_schedule.py`

Job scheduling optimization module using OR-Tools CP-SAT solver:

- **Constraint-based scheduling**: Uses Google OR-Tools CP-SAT solver to create optimal technician crew schedules
- **Schedule generation**: Assigns jobs to crews and workdays while respecting:
  - Job earliest start dates and due dates
  - Crew capacity constraints (configurable crew hours per shift)
  - Holiday and weekend exclusions
  - Multiple crew availability
- **Optimization objective**: Minimizes the number of late jobs (jobs scheduled after their due date)
- **Key functions**:
  - `workdays_in_month()`: Generates list of valid workdays excluding weekends and holidays
  - `create_schedule()`: Core optimization function that creates crew schedules using constraint programming
  - `merge_actuals()`: Compares planned schedules with actual job completion data
  - `plot_job_counts()`: Visualizes planned vs actual job distribution over time
- **Preprocessing integration**: Imports `load_schedule_data()` and `filter_jobs()` from preprocessing module for data loading and filtering
- **Configurable parameters**:
  - Number of crews (default: 3)
  - Net shift hours (default: 8)
  - Solver timeout (default: 60 seconds)
  - Number of search workers (default: 8 for parallel search)

The module supports analyzing schedule feasibility and identifying potential bottlenecks in crew capacity planning.

## Required Packages

Before running the analysis, ensure you have the following Python packages installed:

### Core Dependencies

```bash
pip install -r requirements.txt
```

## How to Run the Code

### Prerequisites

1. Ensure all required packages are installed (see above)
2. **For utilization analysis**, place the following parquet files in a `sort/` directory:
   - `REP_ORD_ORDER.parquet`
   - `REP_ORD_JOB_CODE.parquet`
   - `REP_ORD_ORDER_STATE.parquet`
   - `REP_ASN_ASSIGNMENT.parquet`
   - `REP_LAB_RESOURCE.parquet`
   - `REP_LAB_USER.parquet`
3. **For schedule optimization**, place the following CSV files in the project root directory:
   - `Assignment2_Planning.csv`
   - `Assignment2_Actuals.csv`

### Option A: Using Docker (Recommended)

Build and run using Docker for a consistent environment:

```bash
# Build the Docker image
docker build -t sdge-tech-analysis .

# Run utilization analysis
docker run -v "$(pwd)":/home/jovyan/work -w /home/jovyan/work sdge-tech-analysis python src/eda.py

# Run schedule optimization
docker run -v "$(pwd)":/home/jovyan/work -w /home/jovyan/work sdge-tech-analysis python src/optimization_schedule.py
```

### Option B: Local Python Environment

#### Option 1: Run Full Analysis Pipeline

**Utilization Analysis:**

```bash
python src/eda.py
```

This will execute the complete utilization analysis and generate all visualizations.

**Schedule Optimization:**

```bash
python src/optimization_schedule.py
```

This will run the optimization scheduler to create crew schedules and compare them with actual job completion data.

#### Option 2: Run Individual Components

**Utilization Analysis:**

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

**Schedule Optimization:**

```python
from preprocessing import load_schedule_data, filter_jobs
from optimization_schedule import create_schedule, merge_actuals, plot_job_counts
import pandas as pd
from datetime import date

# Load planning and actual data
planning_df, actuals_df = load_schedule_data("Assignment2_Planning.csv", "Assignment2_Actuals.csv")

# Filter jobs by due date and district
chosen_due = pd.Timestamp("2023-04-30 23:59:00")
chosen_district = "METRO-ELECTRIC"
district_df = filter_jobs(planning_df, chosen_due, chosen_district)

# Create optimized schedule
year, month = 2023, 1
holidays = [date(2023, 1, 2), date(2023, 1, 16)]  # New Year's Day observed, MLK Day
sched_df = create_schedule(district_df, year, month, holidays=holidays, num_crews=3)

# Compare with actual schedules
if not sched_df.empty:
    merged_df = merge_actuals(sched_df, actuals_df)
    print(merged_df)

    # Visualize planned vs actual
    planned_counts = sched_df['SCHEDULEDDATE'].value_counts().sort_index()
    actual_counts = merged_df['SCHEDULEDSTART'].value_counts().sort_index()
    plot_job_counts(planned_counts, actual_counts)
```
