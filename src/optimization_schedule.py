from datetime import date, timedelta
import pandas as pd
from ortools.sat.python import cp_model
import plotly.graph_objects as go
from preprocessing import load_schedule_data, filter_jobs
import numpy as np


def workdays_in_month(year, month, holidays=None):
    """Return a list of workdays (Mon-Fri) in a given month, excluding holidays."""
    holidays = holidays or []
    d = date(year, month, 1)
    days = []
    while d.month == month:
        if d.weekday() < 5 and d not in holidays:
            days.append(d)
        d += timedelta(days=1)
    return days

def create_schedule(district_df, year, month, holidays=None, num_crews=3, net_shift_hours=8, output_file="schedule.csv"):
    """Create an optimized schedule using OR-Tools CP-SAT."""
    workdays = workdays_in_month(year, month, holidays)
    num_days = len(workdays)
    
    jobs = list(district_df.index)
    durations = district_df["DURATION"].tolist()
    est_dates = district_df["EARLYSTART"].dt.date.tolist()
    due_dates = district_df["DUEDATE"].dt.date.tolist()
    
    model = cp_model.CpModel()
    net_shift_seconds = net_shift_hours * 3600
    
    x = {}
    for j in jobs:
        for d in range(num_days):
            for c in range(num_crews):
                x[j,d,c] = model.NewBoolVar(f"x_{j}_{d}_{c}")
    
    # Each job assigned exactly once
    for j in jobs:
        model.Add(sum(x[j,d,c] for d in range(num_days) for c in range(num_crews)) == 1)
    
    # Jobs cannot start before earliest start
    for j in jobs:
        for d, day in enumerate(workdays):
            if day < est_dates[j]:
                for c in range(num_crews):
                    model.Add(x[j,d,c] == 0)
    
    # Late job indicators
    late = {}
    for j in jobs:
        late[j] = model.NewBoolVar(f"late_{j}")
        after_due_assignments = []
        for d, day in enumerate(workdays):
            if day > due_dates[j]:
                for c in range(num_crews):
                    after_due_assignments.append(x[j,d,c])
        if after_due_assignments:
            model.AddMaxEquality(late[j], after_due_assignments)
        else:
            model.Add(late[j] == 0)
    
    # Crew capacity constraint
    for d in range(num_days):
        for c in range(num_crews):
            model.Add(sum(durations[j] * x[j,d,c] for j in jobs) <= net_shift_seconds)
    
    # Objective: minimize late jobs
    model.Minimize(sum(late[j] for j in jobs))
    
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 60
    solver.parameters.num_search_workers = 8
    
    result = solver.Solve(model)
    
    if result in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        schedule = []
        for j in jobs:
            for d in range(num_days):
                for c in range(num_crews):
                    if solver.Value(x[j,d,c]) == 1:
                        schedule.append({
                            "CALLID": district_df.loc[j, "CALLID"],
                            "EARLIEST STARTDATE": est_dates[j].isoformat(),
                            "DUEDATE": due_dates[j].isoformat(),
                            "SCHEDULEDDATE": workdays[d].isoformat()
                        })
        sched_df = pd.DataFrame(schedule)
        
        sched_df.to_csv(output_file, index=False)
        print(f"Schedule saved to {output_file}")
        
        return sched_df
    else:
        print("No feasible schedule found.")
        return pd.DataFrame()

def merge_actuals(sched_df, actuals_df):
    """Merge scheduled data with actuals."""
    merged_df = pd.merge(
        sched_df,
        actuals_df[['CALLID', 'STATUS', 'SCHEDULEDSTART']],
        on='CALLID',
        how='left'
    )
    merged_df['SCHEDULEDSTART'] = pd.to_datetime(merged_df['SCHEDULEDSTART']).dt.date
    return merged_df

def plot_job_counts(planned_counts, actual_counts):
    """Plot planned vs actual jobs using Plotly."""
    planned_counts.index = pd.to_datetime(planned_counts.index)
    actual_counts.index = pd.to_datetime(actual_counts.index)
    
    all_dates = pd.date_range(
        start=min(planned_counts.index.min(), actual_counts.index.min()),
        end=max(planned_counts.index.max(), actual_counts.index.max())
    )
    
    planned_counts = planned_counts.reindex(all_dates, fill_value=0)
    actual_counts = actual_counts.reindex(all_dates, fill_value=0)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=all_dates,
        y=planned_counts.values,
        name='Planned',
        marker_color='skyblue'
    ))
    fig.add_trace(go.Bar(
        x=all_dates,
        y=actual_counts.values,
        name='Actual',
        marker_color='salmon'
    ))
    fig.update_layout(
        title='Planned vs Actual Jobs Scheduled Per Day for METRO-ELECTRIC (Jan 2023)',
        xaxis_title='Date',
        yaxis_title='Number of Jobs',
        barmode='group',
        xaxis_tickangle=-45,
        template='plotly_white',
        width=1000,
        height=500
    )
    fig.show()

def plot_job_diff(planned_counts, actual_counts):
    """ Plot differences in actual jobs completed against scheduled plan with Plotly """
    planned_counts.index = pd.to_datetime(planned_counts.index)
    actual_counts.index  = pd.to_datetime(actual_counts.index)

    all_dates = pd.date_range(
        start=min(planned_counts.index.min(), actual_counts.index.min()),
        end=max(planned_counts.index.max(), actual_counts.index.max())
    )

    planned_counts = planned_counts.reindex(all_dates, fill_value=0)
    actual_counts = actual_counts.reindex(all_dates, fill_value=0)

    diff = actual_counts - planned_counts
    values = diff.values
    labels = [v if v != 0 else "" for v in values]
    colors = np.where(values > 0, "green", "red")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=all_dates,
        y=values,
        marker_color=colors,
        text=labels,
        textposition="outside",
        showlegend=False
    ))

    fig.update_layout(
        title= 'Differences in Jobs Count Between Planned Schedule and Actual Activity',
        xaxis_title="Date",
        yaxis_title="Jobs (Actual - Planned)",
        template="plotly_white"
    )

    fig.add_trace(go.Bar(
        x=[None], y=[None],
        marker_color="green",
        name="Ahead"
    ))
    fig.add_trace(go.Bar(
        x=[None], y=[None],
        marker_color="red",
        name="Extra (Planning Leftover)"
    ))
    
    fig.show()
 
if __name__ == "__main__":
    planning_file = "Assignment2_Planning.csv"
    actuals_file = "Assignment2_Actuals.csv"
    df, actuals = load_schedule_data(planning_file, actuals_file)
    
    chosen_due = pd.Timestamp("2023-04-30 23:59:00")
    chosen_district = "METRO-ELECTRIC"
    year = 2023
    month = 1
    
    district_df = filter_jobs(df, chosen_due, chosen_district)
    holidays = [date(2023,1,2), date(2023,1,16)]
    sched_df = create_schedule(district_df, year, month, holidays=holidays)
    
    if not sched_df.empty:
        merged_df = merge_actuals(sched_df, actuals)
        print(merged_df)
