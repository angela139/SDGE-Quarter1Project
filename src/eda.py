import plotly.express as px

from preprocessing import (
    load_data,
    load_california_geojson,
    calculate_zip_utilization,
    calculate_technician_utilization,
    calculate_dispatch_area_utilization,
    prepare_job_lifecycle_analysis
)

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


def utilization_distribution_plot(daily_utilization):
    """
    Create utilization distribution analysis
    """
    
    # Calculate key statistics
    mean_util = daily_utilization['UTILIZATION_RATE'].mean()
    
    # Create the histogram
    fig = go.Figure()

    # Add optimization area (shaded region from 0 to 100%)
    fig.add_vrect(
        x0=0, x1=1.0,
        fillcolor="rgba(255, 193, 7, 0.15)",
        layer="below",
        line_width=0,
        annotation_text="OPTIMIZATION ZONE",
        annotation_position="top",
        annotation=dict(
            font=dict(size=12, color="#f39c12", family="Arial Bold"),
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="#f39c12",
            borderwidth=1
        )
    )
    
    # Add histogram
    fig.add_trace(go.Histogram(
        x=daily_utilization['UTILIZATION_RATE'],
        nbinsx=100,
        name='Daily Utilization',
        marker=dict(
            color='rgba(52, 152, 219, 0.7)',
            line=dict(color='rgba(52, 152, 219, 1.0)', width=1)
        ),
        opacity=0.8
    ))

    # Add 100% target line
    fig.add_vline(
        x=1.0, 
        line_dash="solid", 
        line_color="#27ae60",
        line_width=4,
        annotation_text="100% Utilization",
        annotation_position="top right",
        annotation=dict(
            font=dict(size=12, color="#27ae60", family="Arial Bold"),
            bgcolor="rgba(255, 255, 255, 0.9)",
            bordercolor="#27ae60",
            borderwidth=2
        )
    )
    
    # Add mean line
    fig.add_vline(
        x=mean_util, 
        line_dash="dash", 
        line_color="red",
        line_width=3,
        annotation_text=f"Current Average: {mean_util:.1%}",
        annotation_position="top"
    )

    # Update layout for clean storytelling
    fig.update_layout(
        title=dict(
            text=f'<b>Distribution of Daily Utilization Rate for Field Technician</b><br>' +
                 f'<span style="font-size:14px; color:#7f8c8d;">',
            font=dict(size=20, color='#2c3e50'),
            x=0.5,
            pad=dict(b=20)
        ),
        xaxis=dict(
            title="<b>Daily Utilization Rate</b>",
            tickformat='.0%',
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)'
        ),
        yaxis=dict(
            title="<b>Frequency</b>",
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)'
        ),
        width=1000,
        height=600,
        plot_bgcolor='white',
        showlegend=False,
        font=dict(family="Arial, sans-serif")
    )
    
    return fig


def utilization_hourly_plot(hourly_df):
    """
    Create a utilization/idle time hourly analysis
    """

    # hourly summary from hourly_df
    hourly_summary = hourly_df.groupby('HOUR').agg({
        'WORK_MINUTES': 'sum',
        'TECH_ID': 'nunique',
        'ORDER_COUNT': 'sum',
        'UTILIZATION_RATE': 'mean',
        'IDLE_MINUTES': 'sum',
        'IDLE_TIME_PCT': 'mean'
    }).reset_index()

    hourly_summary.rename(columns={
        'WORK_MINUTES': 'TOTAL_WORK_MINUTES',
        'TECH_ID': 'UNIQUE_TECHS',
        'ORDER_COUNT': 'TOTAL_ORDERS',
        'UTILIZATION_RATE': 'AVG_UTILIZATION_RATE',
        'IDLE_MINUTES': 'TOTAL_IDLE_MINUTES',
        'IDLE_TIME_PCT': 'AVG_IDLE_TIME_PCT'
    }, inplace=True)
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=(
            'Idle Time Pattern and Order Volume by Hour', 
            'Utilization Rate Throughout the Day'
        ),
        specs=[[{"secondary_y": True}], [{"secondary_y": False}]],
        vertical_spacing=0.15
    )
    
    # TOP PLOT: Idle Time and Order Count
    fig.add_trace(
        go.Scatter(
            x=hourly_summary['HOUR'], 
            y=hourly_summary['AVG_IDLE_TIME_PCT'],
            mode='lines+markers',
            name='Idle Time %',
            line=dict(color='#e74c3c', width=4),
            marker=dict(size=10, color='#e74c3c'),
            hovertemplate='<b>Hour %{x}:00</b><br>' +
                         'Idle Time: %{y:.1f}%<br>' +
                         '<extra></extra>'
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=[None], y=[None],
            mode='markers',
            name='Business Hours (8-17)',
            marker=dict(size=10, color='rgba(39,174,96,0.3)'),
            showlegend=True
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(
            x=hourly_summary['HOUR'],
            y=hourly_summary['TOTAL_ORDERS'],
            name='Order Count',
            marker=dict(color='rgba(52, 152, 219, 0.3)', line=dict(color='#3498db', width=1)),
            hovertemplate='<b>Hour %{x}:00</b><br>' +
                         'Orders: %{y:.1f}<br>' +
                         '<extra></extra>',
            yaxis='y2'
        ),
        row=1, col=1, secondary_y=True
    )
    
    # BOTTOM PLOT: Utilization Rate 
    fig.add_trace(
        go.Scatter(
            x=hourly_summary['HOUR'],
            y=hourly_summary['AVG_UTILIZATION_RATE'] * 100,  # Convert to percentage
            mode='lines+markers',
            name='Utilization Rate %',
            line=dict(color='#27ae60', width=4),
            marker=dict(size=10, color='#27ae60'),
            hovertemplate='<b>Hour %{x}:00</b><br>' +
                         'Utilization: %{y:.1f}%<br>' +
                         '<extra></extra>'
        ),
        row=2, col=1
    )
    
    highest_idle_hour = int(hourly_summary.loc[hourly_summary['AVG_IDLE_TIME_PCT'].idxmax(), 'HOUR'])
    lowest_idle_hour = int(hourly_summary.loc[hourly_summary['AVG_IDLE_TIME_PCT'].idxmin(), 'HOUR'])
    peak_utilization_hour = int(hourly_summary.loc[hourly_summary['AVG_UTILIZATION_RATE'].idxmax(), 'HOUR'])
    
    highest_idle_value = hourly_summary['AVG_IDLE_TIME_PCT'].max()
    lowest_idle_value = hourly_summary['AVG_IDLE_TIME_PCT'].min()
    peak_utilization_value = hourly_summary['AVG_UTILIZATION_RATE'].max() * 100
    
    # Highest idle time annotation
    fig.add_annotation(
        x=highest_idle_hour, y=highest_idle_value,
        text=f"{highest_idle_hour:02d}:00<br>{highest_idle_value:.1f}% idle",
        showarrow=True,
        arrowcolor="#e74c3c",
        bgcolor="rgba(231,76,60,0.9)",
        bordercolor="#e74c3c",
        font=dict(color="white", size=11, family="Arial Black"),
        ax=0, ay=-50,
        row=1, col=1
    )
    
    # Lowest idle time annotation
    fig.add_annotation(
        x=lowest_idle_hour, y=lowest_idle_value,
        text=f"{lowest_idle_hour:02d}:00<br>{lowest_idle_value:.1f}% idle",
        showarrow=True,
        arrowcolor="#27ae60",
        bgcolor="rgba(39,174,96,0.9)",
        bordercolor="#27ae60",
        font=dict(color="white", size=11, family="Arial Black"),
        ax=0, ay=50,
        row=1, col=1
    )
    
    # Peak utilization annotation
    fig.add_annotation(
        x=peak_utilization_hour, y=peak_utilization_value,
        text=f"{peak_utilization_hour:02d}:00<br>{peak_utilization_value:.1f}% utilized",
        showarrow=True,
        arrowcolor="#27ae60",
        bgcolor="rgba(39,174,96,0.9)",
        bordercolor="#27ae60",
        font=dict(color="white", size=11, family="Arial Black"),
        ax=0, ay=-50,
        row=2, col=1
    )
    
    fig.update_layout(
        title=dict(
            text=f'<b>Field Technician Hourly Analysis: Idle Time vs Utilization Efficiency</b><br>' +
                 f'<span style="font-size:14px; color:#e67e22;">',
            font=dict(size=18, color='#2c3e50'),
            x=0.5
        ),
        height=800,
        width=1200,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="center", x=0.5
        )
    )
    
    fig.update_xaxes(title_text="<b>Hour of Day</b>", row=2, col=1)
    fig.update_yaxes(title_text="<b>Idle Time %</b>", row=1, col=1)
    fig.update_yaxes(title_text="<b>Order Count</b>", row=1, col=1, secondary_y=True)
    fig.update_yaxes(title_text="<b>Utilization Rate %</b>", row=2, col=1)
    
    fig.add_hline(y=100, line_dash="dash", line_color="red", 
                  annotation_text="100% Utilization Target", row=2, col=1)
    
    fig.add_vrect(x0=8, x1=17, fillcolor="rgba(39,174,96,0.1)", layer="below", line_width=0, row=1, col=1)
    fig.add_vrect(x0=8, x1=17, fillcolor="rgba(39,174,96,0.1)", layer="below", line_width=0, row=2, col=1)
    
    return fig


def utilization_job_counts_plot(daily_utilization):
    """
    Create Bar Chart Analyzing Utilization Rate By Ranges of Job Counts Assignment
    
    Args:
        daily_uitlization (pd.DataFrame): Utilization data by field techs
    
    Returns:
        plotly express bar chart displaying utilization rate in percentages by ranges of job counts
    """
    util_job_counts = daily_utilization.copy()

    bins = [0, 3, 6, 9, 12, 15, 18, float('inf')]
    labels = ['1–3', '4–6', '7–9', '10–12', '13–15', '16–18', '19+']

    util_job_counts['JOB_COUNT_RANGE'] = pd.cut(util_job_counts['JOBS_COUNT'], bins=bins, labels=labels, right=True)

    job_range_avg = (
        util_job_counts
        .groupby('JOB_COUNT_RANGE', observed=False)['UTILIZATION_RATE_%']
        .mean()
        .reset_index()
    )

    fig1 = px.bar(
        job_range_avg,
        x='JOB_COUNT_RANGE',
        y='UTILIZATION_RATE_%',
        text=job_range_avg['UTILIZATION_RATE_%'].round(1).astype(str) + '%',
        title='Average Utilization Rate by Job Counts',
        labels={'UTILIZATION_RATE_%': 'Average Utilization Rate (%)', 'JOB_COUNT_RANGE': 'Job Count Range'}
    )

    fig1.update_layout(template='simple_white')
    fig1.show()


def utilization_days_week_plot(daily_utilization):  
    """
    Create Bar Chart Analyzing Utilization Rate By Days of the Week
    
    Args:
        daily_uitlization (pd.DataFrame): Utilization data by field techs
    
    Returns:
        plotly express bar chart displaying utilization rate in percentages by days of the week
    """
    util_day_ofweek = daily_utilization.copy()

    util_day_ofweek['DAY_OF_WEEK'] = util_day_ofweek['DATE'].dt.day_of_week
    map_day = {
        0: 'Monday',
        1: 'Tuesday',
        2: 'Wednesday',
        3: 'Thursday',
        4: 'Friday',
        5: 'Saturday',
        6: 'Sunday'
    }

    util_day_ofweek['DAY_OF_WEEK'] = util_day_ofweek['DAY_OF_WEEK'].map(map_day) 

    day_week_avg = (
        util_day_ofweek
        .groupby('DAY_OF_WEEK', observed=False)['UTILIZATION_RATE_%']
        .mean()
        .reset_index()
    )

    weekday_in_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_week_avg['DAY_OF_WEEK'] = pd.Categorical(day_week_avg['DAY_OF_WEEK'], categories=weekday_in_order, ordered=True)
    day_week_avg = day_week_avg.sort_values('DAY_OF_WEEK')

    fig2 = px.bar(
        day_week_avg,
        x='DAY_OF_WEEK',
        y='UTILIZATION_RATE_%',
        text=day_week_avg['UTILIZATION_RATE_%'].round(1).astype(str) + '%',
        title='Average Utilization Rate by Days of the Week',
        labels={'UTILIZATION_RATE_%': 'Average Utilization Rate (%)', 'DAY_OF_WEEK': 'Days of the Week'}
    )

    fig2.update_layout(template='simple_white')
    fig2.show()


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
    
    tech_util = calculate_technician_utilization(DF)
    
    util_hist = plot_utilization_histogram(tech_util)
    util_hist.show()
    
    dispatch_util = calculate_dispatch_area_utilization(DF)
    
    dispatch_chart = plot_dispatch_area_utilization(dispatch_util)
    dispatch_chart.show()
    
    DF_lifecycle = prepare_job_lifecycle_analysis(DF)
    
    lifecycle_chart = plot_job_lifecycle_analysis(DF_lifecycle)
    lifecycle_chart.show()

if __name__ == "__main__":
    run_full_analysis()
