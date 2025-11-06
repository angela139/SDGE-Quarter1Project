"""
Tech Utilization Analysis for SDGE
This module provides functions to analyze technician utilization patterns
from SDGE job order data.
"""

import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import requests


def load_data():
    """
    Load and merge all required datasets for technician analysis.
    
    Returns:
        pd.DataFrame: Merged dataframe containing all relevant job and technician data
    """
    OO = pd.read_parquet('sort/REP_ORD_ORDER.parquet', engine='pyarrow', 
                         columns=['ORDER_ID', 'ORDER_NUM', 'JOB_CODE', 'ELIGIBLE', 
                                'DISPATCH_AREA', 'SLR_ZIP', 'SLR_CITY'])
    
    JC = pd.read_parquet('sort/REP_ORD_JOB_CODE.parquet', engine='pyarrow',
                         columns=['JOB_CODE_ID', 'NAME', 'CORE_DESCRIPTION'])
    
    OOS = pd.read_parquet('sort/REP_ORD_ORDER_STATE.parquet', engine='pyarrow',
                          columns=['ORDER_STATE_ID', 'FOR_ORDER', 'ORDER_NUM', 'LATEST_ASSIGNMENT',
                                 'TOTAL_TIME_EN_ROUTE', 'TOTAL_TIME_ON_SITE', 'DISPATCH_AT', 
                                 'RECEIVED_AT', 'ACKNOWLEDGED_AT', 'ENROUTE_AT', 'ONSITE_AT', 
                                 'COMPLETED', 'CLOSED'])
    
    AA = pd.read_parquet('sort/REP_ASN_ASSIGNMENT.parquet', engine='pyarrow',
                         columns=['ASSIGNMENT_ID', 'FOR_RESOURCE'])
    
    LR = pd.read_parquet('sort/REP_LAB_RESOURCE.parquet', engine='pyarrow',
                         columns=['RESOURCE_ID', 'FOR_USER'])
    
    LU = pd.read_parquet('sort/REP_LAB_USER.parquet', engine='pyarrow',
                         columns=['USER_ID', 'LOGON_ID'])
    
    DF = OO.merge(JC, left_on='JOB_CODE', right_on='JOB_CODE_ID')
    DF = DF.merge(OOS, left_on='ORDER_ID', right_on='FOR_ORDER')
    DF = DF.merge(AA, left_on='LATEST_ASSIGNMENT', right_on='ASSIGNMENT_ID')
    DF = DF.merge(LR, left_on='FOR_RESOURCE', right_on='RESOURCE_ID')
    DF = DF.merge(LU, left_on='FOR_USER', right_on='USER_ID')
    
    print(f"Merged dataset shape: {DF.shape}")
    return DF


def load_california_geojson():
    """
    Load California zip code GeoJSON data for mapping.
    
    Returns:
        dict: GeoJSON data for California zip codes
    """
    url = "https://raw.githubusercontent.com/OpenDataDE/State-zip-code-GeoJSON/master/ca_california_zip_codes_geo.min.json"
    response = requests.get(url)
    return response.json()


def get_work_dates(start_time, end_time):
    """
    Get list of work dates between start and end times.
    
    Args:
        start_time (pd.Timestamp): Start datetime
        end_time (pd.Timestamp): End datetime
    
    Returns:
        list: List of dates between start and end times
    """
    if pd.isna(start_time) or pd.isna(end_time):
        return []

    start_date = start_time.date()
    end_date = end_time.date()
    dates = []
    current_date = start_date

    while current_date <= end_date:
        dates.append(current_date)
        current_date += pd.Timedelta(days=1)
    return dates


def calculate_zip_utilization(DF):
    """
    Calculate average technician utilization by zip code.
    
    Args:
        DF (pd.DataFrame): Merged dataset
    
    Returns:
        pd.DataFrame: Utilization statistics by zip code
    """
    DF_clean = DF[DF['SLR_ZIP'].notna()].copy()
    DF_clean['ZIP5'] = DF_clean['SLR_ZIP'].astype(str).str[:5]
    
    DF_clean['TOTAL_TIME_EN_ROUTE'] = pd.to_numeric(DF_clean['TOTAL_TIME_EN_ROUTE'], errors='coerce')
    DF_clean['TOTAL_TIME_ON_SITE'] = pd.to_numeric(DF_clean['TOTAL_TIME_ON_SITE'], errors='coerce')
    
    DF_clean['WORK_START'] = DF_clean['ENROUTE_AT']
    DF_clean['WORK_END'] = DF_clean['COMPLETED']
    
    expanded_records = []
    
    for idx, row in DF_clean.iterrows():
        if pd.notna(row['WORK_START']) and pd.notna(row['WORK_END']):
            work_dates = get_work_dates(row['WORK_START'], row['WORK_END'])
            
            if len(work_dates) == 1:
                expanded_records.append({
                    'LOGON_ID': row['LOGON_ID'],
                    'DATE': work_dates[0],
                    'ZIP5': row['ZIP5'],
                    'TOTAL_TIME_EN_ROUTE': row['TOTAL_TIME_EN_ROUTE'],
                    'TOTAL_TIME_ON_SITE': row['TOTAL_TIME_ON_SITE']
                })
            else:
                n_days = len(work_dates)
                en_route_per_day = row['TOTAL_TIME_EN_ROUTE'] / n_days
                onsite_per_day = row['TOTAL_TIME_ON_SITE'] / n_days
                
                for d in work_dates:
                    expanded_records.append({
                        'LOGON_ID': row['LOGON_ID'],
                        'DATE': d,
                        'ZIP5': row['ZIP5'],
                        'TOTAL_TIME_EN_ROUTE': en_route_per_day,
                        'TOTAL_TIME_ON_SITE': onsite_per_day
                    })
    
    expanded_df = pd.DataFrame(expanded_records)
    expanded_df['TOTAL_WORKED'] = expanded_df['TOTAL_TIME_EN_ROUTE'] + expanded_df['TOTAL_TIME_ON_SITE']
    
    daily = expanded_df.groupby(['LOGON_ID', 'DATE', 'ZIP5'], as_index=False).agg({'TOTAL_WORKED': 'sum'})
    daily['DAILY_UTIL_%'] = (daily['TOTAL_WORKED'] / (7 * 60 * 60)) * 100
    
    zip_util = daily.groupby('ZIP5', as_index=False).agg({
        'DAILY_UTIL_%': 'mean',
        'TOTAL_WORKED': 'sum',
        'LOGON_ID': 'count'
    })
    
    zip_util = zip_util.rename(columns={'LOGON_ID': 'TOTAL_JOBS'})
    zip_util['DAILY_UTIL_%'] = zip_util['DAILY_UTIL_%'].round(2)
    
    return zip_util


def plot_zip_utilization_map(zip_util, geojson_data):
    """
    Create choropleth map showing technician utilization by zip code.
    
    Args:
        zip_util (pd.DataFrame): Utilization data by zip code
        geojson_data (dict): GeoJSON data for mapping
    
    Returns:
        plotly.graph_objects.Figure: Interactive map figure
    """
    fig = px.choropleth(
        zip_util,
        geojson=geojson_data,
        locations='ZIP5',
        featureidkey='properties.ZCTA5CE10',
        color='DAILY_UTIL_%',
        hover_data=['TOTAL_WORKED', 'TOTAL_JOBS'],
        color_continuous_scale='Plasma',
        range_color=[0, 60],
        title='Average Technician Utilization by Zip Code'
    )
    
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r": 0, "t": 50, "l": 0, "b": 0})
    
    return fig


def calculate_technician_utilization_v1(DF):
    """
    Calculate technician utilization using actual timestamps (Version 1).
    
    Args:
        DF (pd.DataFrame): Merged dataset
    
    Returns:
        pd.DataFrame: Technician utilization statistics
    """
    DF_work = DF.copy()
    DF_work['TOTAL_TIME_EN_ROUTE'] = pd.to_numeric(DF_work['TOTAL_TIME_EN_ROUTE'], errors='coerce')
    DF_work['TOTAL_TIME_ON_SITE'] = pd.to_numeric(DF_work['TOTAL_TIME_ON_SITE'], errors='coerce')
    
    DF_work['WORK_START'] = DF_work['ENROUTE_AT']
    DF_work['WORK_END'] = DF_work['COMPLETED']
    DF_work['ONSITE_START'] = DF_work['ONSITE_AT']
    
    DF_work['ACTUAL_TIME_EN_ROUTE'] = (DF_work['ONSITE_START'] - DF_work['WORK_START']).dt.total_seconds()
    DF_work['ACTUAL_TIME_ON_SITE'] = (DF_work['WORK_END'] - DF_work['ONSITE_START']).dt.total_seconds()
    
    expanded_records = []
    
    for idx, row in DF_work.iterrows():
        if pd.notna(row['WORK_START']) and pd.notna(row['WORK_END']):
            work_dates = get_work_dates(row['WORK_START'], row['WORK_END'])
            
            if len(work_dates) == 1:
                expanded_records.append({
                    'LOGON_ID': row['LOGON_ID'],
                    'DATE': work_dates[0],
                    'TOTAL_TIME_EN_ROUTE': row['ACTUAL_TIME_EN_ROUTE'],
                    'TOTAL_TIME_ON_SITE': row['ACTUAL_TIME_ON_SITE']
                })
            else:
                n_days = len(work_dates)
                en_route_per_day = row['ACTUAL_TIME_EN_ROUTE'] / n_days
                onsite_per_day = row['ACTUAL_TIME_ON_SITE'] / n_days
                
                for d in work_dates:
                    expanded_records.append({
                        'LOGON_ID': row['LOGON_ID'],
                        'DATE': d,
                        'TOTAL_TIME_EN_ROUTE': en_route_per_day,
                        'TOTAL_TIME_ON_SITE': onsite_per_day
                    })
    
    expanded_df = pd.DataFrame(expanded_records)
    
    daily = expanded_df.groupby(['LOGON_ID', 'DATE'], as_index=False).agg({
        'TOTAL_TIME_EN_ROUTE': 'sum',
        'TOTAL_TIME_ON_SITE': 'sum'
    })
    
    daily['TOTAL_WORKED'] = daily['TOTAL_TIME_EN_ROUTE'] + daily['TOTAL_TIME_ON_SITE']
    daily['DAILY_UTILIZATION_RATIO'] = daily['TOTAL_WORKED'] / (7 * 60 * 60)
    daily['DAILY_UTILIZATION_%'] = daily['DAILY_UTILIZATION_RATIO'] * 100
    
    tech_util = daily.groupby('LOGON_ID', as_index=False).agg({
        'DAILY_UTILIZATION_RATIO': 'mean'
    })
    tech_util['UTILIZATION_%'] = tech_util['DAILY_UTILIZATION_RATIO'] * 100
    
    return tech_util


def calculate_technician_utilization_v2(DF):
    """
    Calculate technician utilization using ELIGIBLE date (Version 2).
    
    Args:
        DF (pd.DataFrame): Merged dataset
    
    Returns:
        pd.DataFrame: Technician utilization statistics
    """
    DF_work = DF.copy()
    DF_work['TOTAL_TIME_EN_ROUTE'] = pd.to_numeric(DF_work['TOTAL_TIME_EN_ROUTE'], errors='coerce')
    DF_work['TOTAL_TIME_ON_SITE'] = pd.to_numeric(DF_work['TOTAL_TIME_ON_SITE'], errors='coerce')
    
    DF_work['DATE'] = pd.to_datetime(DF_work['ELIGIBLE']).dt.date
    
    daily = (
        DF_work.groupby(['LOGON_ID', 'DATE'], as_index=False)
               .agg({'TOTAL_TIME_EN_ROUTE': 'sum', 'TOTAL_TIME_ON_SITE': 'sum'})
    )
    
    daily['TOTAL_WORKED'] = daily['TOTAL_TIME_EN_ROUTE'] + daily['TOTAL_TIME_ON_SITE']
    daily['DAILY_UTILIZATION_RATIO'] = (daily['TOTAL_WORKED'] / (7 * 60 * 60))
    daily['DAILY_UTILIZATION_%'] = daily['DAILY_UTILIZATION_RATIO'] * 100
    
    tech_util = (
        daily.groupby('LOGON_ID', as_index=False)
             .agg({'DAILY_UTILIZATION_RATIO': 'mean'})
    )
    
    tech_util['UTILIZATION_%'] = tech_util['DAILY_UTILIZATION_RATIO'] * 100
    
    return tech_util


def plot_utilization_histogram(tech_util):
    """
    Create histogram of technician utilization distribution.
    
    Args:
        tech_util (pd.DataFrame): Technician utilization data
    
    Returns:
        plotly.graph_objects.Figure: Histogram figure
    """
    fig = px.histogram(
        tech_util,
        x='UTILIZATION_%',
        nbins=20,
        title='Distribution of Technician Utilization for SDGE Job Assignments',
    )
    
    fig.update_layout(
        xaxis_title='Utilization (%)',
        yaxis_title='Number of Technicians',
        xaxis=dict(range=[0, 100]),
        bargap=0.05,
        template='plotly_white',
    )
    
    fig.update_traces(
        hovertemplate='Utilization: %{x:.1f}%<br>Technicians: %{y}'
    )
    
    fig.update_layout(
        annotations=[
            dict(
                xref='paper',
                yref='paper',
                x=0,
                y=-0.2,
                showarrow=False,
                text='*Utilization = % of shift time spent traveling to and working on jobs*',
                font=dict(size=12, color='gray'),
                align='left'
            )
        ]
    )
    
    return fig


def calculate_dispatch_area_utilization(DF):
    """
    Calculate average utilization by dispatch area.
    
    Args:
        DF (pd.DataFrame): Merged dataset
    
    Returns:
        pd.DataFrame: Utilization statistics by dispatch area
    """
    DF_work = DF.copy()
    DF_work['TOTAL_TIME_EN_ROUTE'] = pd.to_numeric(DF_work['TOTAL_TIME_EN_ROUTE'], errors='coerce')
    DF_work['TOTAL_TIME_ON_SITE'] = pd.to_numeric(DF_work['TOTAL_TIME_ON_SITE'], errors='coerce')
    DF_work['DATE'] = pd.to_datetime(DF_work['ELIGIBLE']).dt.date
    
    daily_dispatch_area = (
        DF_work.groupby(['LOGON_ID', 'DISPATCH_AREA', 'DATE'], as_index=False)
               .agg({'TOTAL_TIME_EN_ROUTE': 'sum', 'TOTAL_TIME_ON_SITE': 'sum'})
    )
    
    daily_dispatch_area['TOTAL_WORKED'] = (daily_dispatch_area['TOTAL_TIME_EN_ROUTE'] + 
                                          daily_dispatch_area['TOTAL_TIME_ON_SITE'])
    daily_dispatch_area['DAILY_UTILIZATION_RATIO'] = daily_dispatch_area['TOTAL_WORKED'] / (7 * 60 * 60)
    daily_dispatch_area['DAILY_UTILIZATION_%'] = daily_dispatch_area['DAILY_UTILIZATION_RATIO'] * 100
    
    dispatch_util = (
        daily_dispatch_area.groupby('DISPATCH_AREA', as_index=False)
                          .agg({'DAILY_UTILIZATION_RATIO': 'mean'})
    )
    
    dispatch_util['AVG_UTILIZATION_%'] = dispatch_util['DAILY_UTILIZATION_RATIO'] * 100
    dispatch_util = dispatch_util.sort_values(by='AVG_UTILIZATION_%', ascending=False)
    
    return dispatch_util


def plot_dispatch_area_utilization(dispatch_util):
    """
    Create bar chart of utilization by dispatch area.
    
    Args:
        dispatch_util (pd.DataFrame): Dispatch area utilization data
    
    Returns:
        plotly.graph_objects.Figure: Bar chart figure
    """
    fig = px.bar(dispatch_util,
                 x='DISPATCH_AREA',
                 y='AVG_UTILIZATION_%',
                 text='AVG_UTILIZATION_%',
                 labels={'AVG_UTILIZATION_%': 'Average Utilization (%)', 
                        'DISPATCH_AREA': 'Dispatch Area'},
                 title='Average Technician Utilization by Dispatch Area',
                 color='AVG_UTILIZATION_%',
                 color_continuous_scale='Blues')
    
    fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
    fig.update_layout(yaxis=dict(range=[0, 50]), xaxis_tickangle=-45)
    
    return fig


def plot_lowest_utilization_technicians(tech_util, n=10):
    """
    Plot technicians with lowest utilization rates.
    
    Args:
        tech_util (pd.DataFrame): Technician utilization data
        n (int): Number of technicians to show
    """
    lowest_util = tech_util.sort_values('UTILIZATION_%', ascending=True)
    lowest_n = lowest_util.head(n)
    
    plt.figure(figsize=(8, 5))
    plt.barh(lowest_n['LOGON_ID'], lowest_n['UTILIZATION_%'], color='salmon')
    plt.xlabel('Utilization (%)')
    plt.ylabel('Technician')
    plt.title(f'Technicians with Lowest Utilization Rates (Top {n})')
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()


def plot_highest_job_count_technicians(tech_util, DF, n=10):
    """
    Plot technicians with highest job counts and their utilization.
    
    Args:
        tech_util (pd.DataFrame): Technician utilization data
        DF (pd.DataFrame): Full dataset for job counting
        n (int): Number of technicians to show
    """
    job_counts = DF.groupby('LOGON_ID').size().reset_index(name='TOTAL_JOBS')
    tech_util_full = tech_util.merge(job_counts, on='LOGON_ID')
    top_n_jobs = tech_util_full.sort_values('TOTAL_JOBS', ascending=False).head(n)
    
    plt.figure(figsize=(8, 5))
    plt.barh(top_n_jobs['LOGON_ID'], top_n_jobs['UTILIZATION_%'], color='skyblue')
    
    for i, (util, total_jobs) in enumerate(zip(top_n_jobs['UTILIZATION_%'], top_n_jobs['TOTAL_JOBS'])):
        plt.text(util + 1, i, f'{total_jobs} jobs', va='center')
    
    plt.xlabel('Average Daily Utilization (%)')
    plt.ylabel('Technician')
    plt.title(f'Technicians with Most Jobs and Their Average Daily Utilization (Top {n})')
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()


def plot_utilization_vs_job_count(tech_util, DF):
    """
    Create scatter plot of utilization vs total job count.
    
    Args:
        tech_util (pd.DataFrame): Technician utilization data
        DF (pd.DataFrame): Full dataset for job counting
    """
    job_counts = DF.groupby('LOGON_ID').size().reset_index(name='TOTAL_JOBS')
    tech_util_full = tech_util.merge(job_counts, on='LOGON_ID')
    tech_util_clean = tech_util_full[tech_util_full['UTILIZATION_%'] <= 100]
    
    plt.figure(figsize=(8, 6))
    plt.scatter(tech_util_clean['TOTAL_JOBS'], tech_util_clean['UTILIZATION_%'], 
                alpha=0.7, color='teal')
    plt.xlabel('Total Jobs')
    plt.ylabel('Average Daily Utilization (%)')
    plt.title('Technician Utilization vs. Total Jobs')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.show()


def prepare_job_lifecycle_analysis(DF):
    """
    Prepare data for job lifecycle timing analysis.
    
    Args:
        DF (pd.DataFrame): Merged dataset
    
    Returns:
        pd.DataFrame: Dataset with calculated timing columns
    """
    DF_lifecycle = DF.copy()
    
    # Convert timestamp columns
    timestamp_cols = ['COMPLETED', 'CLOSED', 'DISPATCH_AT', 'RECEIVED_AT', 
                     'ACKNOWLEDGED_AT', 'ENROUTE_AT', 'ONSITE_AT']
    for col in timestamp_cols:
        DF_lifecycle[col] = pd.to_datetime(DF_lifecycle[col], errors='coerce')
    
    DF_lifecycle = DF_lifecycle.dropna(subset=['ACKNOWLEDGED_AT'])
    
    # Calculate timing metrics (in hours)
    DF_lifecycle['time_to_receive'] = (DF_lifecycle['RECEIVED_AT'] - 
                                      DF_lifecycle['DISPATCH_AT']).dt.total_seconds() / 3600
    DF_lifecycle['time_to_ack'] = (DF_lifecycle['ACKNOWLEDGED_AT'] - 
                                  DF_lifecycle['RECEIVED_AT']).dt.total_seconds() / 3600
    DF_lifecycle['time_to_leave'] = (DF_lifecycle['ENROUTE_AT'] - 
                                    DF_lifecycle['ACKNOWLEDGED_AT']).dt.total_seconds() / 3600
    DF_lifecycle['time_to_enroute'] = DF_lifecycle['TOTAL_TIME_EN_ROUTE'] / 3600
    DF_lifecycle['onsite_duration'] = DF_lifecycle['TOTAL_TIME_ON_SITE'] / 3600
    DF_lifecycle['post_completion_delay'] = (DF_lifecycle['CLOSED'] - 
                                           DF_lifecycle['COMPLETED']).dt.total_seconds() / 3600
    
    return DF_lifecycle


def plot_job_lifecycle_analysis(DF_lifecycle):
    """
    Create bar chart showing average duration between job lifecycle stages.
    
    Args:
        DF_lifecycle (pd.DataFrame): Dataset with timing calculations
    
    Returns:
        plotly.graph_objects.Figure: Bar chart figure
    """
    delays = DF_lifecycle[['time_to_receive', 'time_to_ack', 'time_to_leave', 
                          'time_to_enroute', 'onsite_duration', 
                          'post_completion_delay']].mean().sort_values(ascending=False)
    
    delays_df = delays.reset_index()
    delays_df.columns = ['Stage', 'Average_Hours']
    
    fig = px.bar(
        delays_df,
        x='Average_Hours',
        y='Stage',
        orientation='h',
        text='Average_Hours',
        title="Average Duration Between Job Lifecycle Stages (hrs)",
        labels={'Average_Hours': 'Hours', 'Stage': 'Job Stage'}
    )
    
    fig.update_traces(texttemplate='%{text:.2f} hrs', textposition='outside')
    fig.update_layout(yaxis={'categoryorder': 'total ascending'}, 
                     margin=dict(l=150, r=50, t=50, b=150))
    
    caption_text = (
        "time_to_receive: Time from job dispatch to technician receiving it<br>"
        "time_to_ack: Time from technician receiving job to acknowledging it <br>"
        "time_to_leave: Time from technician acknowledging job to going to job site<br>"
        "time_to_enroute: Time spent traveling to the job site<br>"
        "onsite_duration: Time spent working at the job site<br>"
        "post_completion_delay: Time from job completion to closing job"
    )
    
    fig.add_annotation(
        text=caption_text,
        xref="paper",
        yref="paper",
        x=-0.2,
        y=-0.4,
        showarrow=False,
        align="left",
        font=dict(size=12)
    )
    
    return fig


def run_full_analysis():
    """
    Run the complete technician utilization analysis pipeline.
    
    This function executes all analysis steps and generates all visualizations.
    """
    DF = load_data()
    
    geojson_data = load_california_geojson()
    
    zip_util = calculate_zip_utilization(DF)
    
    zip_map = plot_zip_utilization_map(zip_util, geojson_data)
    zip_map.show()
    
    tech_util = calculate_technician_utilization_v2(DF)
    
    util_hist = plot_utilization_histogram(tech_util)
    util_hist.show()
    
    dispatch_util = calculate_dispatch_area_utilization(DF)
    
    dispatch_chart = plot_dispatch_area_utilization(dispatch_util)
    dispatch_chart.show()
    
    plot_lowest_utilization_technicians(tech_util)
    
    plot_highest_job_count_technicians(tech_util, DF)
    
    plot_utilization_vs_job_count(tech_util, DF)
    
    DF_lifecycle = prepare_job_lifecycle_analysis(DF)
    
    lifecycle_chart = plot_job_lifecycle_analysis(DF_lifecycle)
    lifecycle_chart.show()


if __name__ == "__main__":
    run_full_analysis()
