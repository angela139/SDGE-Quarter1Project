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
