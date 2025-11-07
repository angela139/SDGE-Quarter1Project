import pandas as pd
import os
from scipy import datasets
import pandas as pd


def plot_daily_orders_plotly(daily_counts, time_range, top_n=10):
    """
    Create interactive daily order count plot using Plotly optimized for presentation
    
    Parameters:
    - daily_counts: DataFrame with daily order counts
    - time_range: Tuple of (start_date, end_date) to filter data
                 Can be strings like '2023-01-01' or datetime objects
    - top_n: Number of top job types to display

    Example usage:
        daily_fig_2023 = plot_daily_orders_plotly(daily_counts, top_n=3, 
                                                time_range=('2023-01-01', '2024-12-31'))
        daily_fig_2023.show()
    """
    data = daily_counts.copy()
    
    # Apply time range filter
    start_date, end_date = time_range
    
    if isinstance(start_date, str):
        start_date = pd.to_datetime(start_date)
    if isinstance(end_date, str):
        end_date = pd.to_datetime(end_date)
        
    # Filter data within the time range
    data = data[(data['date'] >= start_date) & (data['date'] <= end_date)]
    
    if len(data) == 0:
        print(f"No data found in the specified time range: {start_date.date()} to {end_date.date()}")
        return None
    
    # Get top N job types by total volume using CORE_DESCRIPTION for display
    top_jobs = data.groupby('CORE_DESCRIPTION')['order_count'].sum().nlargest(top_n).index
    
    # Filter data for top jobs
    daily_top = data[data['CORE_DESCRIPTION'].isin(top_jobs)]
    daily_viz = daily_top.groupby(['date', 'CORE_DESCRIPTION'])['order_count'].sum().reset_index()
    
    title = f'Daily Order Volume Trends - Top {top_n} Job Types<br><span style="font-size:14px; color:gray">{start_date.strftime("%B %d, %Y")} to {end_date.strftime("%B %d, %Y")}</span>'
    
    colors = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
    ]
    
    fig = px.line(daily_viz, 
                  x='date', 
                  y='order_count', 
                  color='CORE_DESCRIPTION',
                  title=title,
                  color_discrete_sequence=colors,
                  labels={
                      'date': 'Date',
                      'order_count': 'Daily Order Count',
                      'CORE_DESCRIPTION': 'Job Type'
                  })
    
    fig.update_traces(
        line=dict(width=3),
        hovertemplate='<b>%{fullData.name}</b><br>' +
                      'Date: %{x|%Y-%m-%d}<br>' +
                      'Orders: %{y:,}<br>' +
                      '<extra></extra>'
    )
    
    fig.update_layout(
        width=1400,
        height=700,
        font=dict(family="Arial, sans-serif", size=12),
        title=dict(
            font=dict(size=18, color='#2c3e50'),
            x=0.5,
            xanchor='center',
            pad=dict(t=20)
        ),
        xaxis=dict(
            title=dict(text='Date', font=dict(size=14, color='#2c3e50')),
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)',
            showline=True,
            linecolor='#2c3e50',
            tickfont=dict(size=11)
        ),
        yaxis=dict(
            title=dict(text='Daily Order Count', font=dict(size=14, color='#2c3e50')),
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)',
            showline=True,
            linecolor='#2c3e50',
            tickfont=dict(size=11)
        ),
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.98,
            xanchor="left",
            x=1.02,
            font=dict(size=11),
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='rgba(128,128,128,0.5)',
            borderwidth=1
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode='x unified',
        margin=dict(l=80, r=150, t=100, b=80)
    )
    
    total_days = (end_date - start_date).days + 1
    total_orders = daily_viz['order_count'].sum()
    avg_daily_orders = total_orders / total_days
    
    fig.add_annotation(
        text=f'<b>Summary Statistics</b><br>' +
             f'Time Period: {total_days} days<br>' +
             f'Total Orders: {total_orders:,}<br>' +
             f'Avg Daily Orders: {avg_daily_orders:.0f}',
        xref="paper", yref="paper",
        x=0.02, y=0.98,
        showarrow=False,
        font=dict(size=10, color="#34495e"),
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor="#bdc3c7",
        borderwidth=1,
        borderpad=8,
        align="left"
    )
    
    return fig


def plot_weekly_orders_plotly(weekly_counts, time_range, top_n=10):
    """
    Create interactive weekly order count plot using Plotly optimized for presentation
    
    Parameters:
    - weekly_counts: DataFrame with weekly order counts
    - time_range: Tuple of (start_date, end_date) to filter data
                 Can be strings like '2023-01-01' or datetime objects
    - top_n: Number of top job types to display

    Example usage:
        weekly_fig = plot_weekly_orders_plotly(
            weekly_counts, 
            time_range=('2024-01-01', '2024-12-31'),
            top_n=6
        )
        weekly_fig.show()
    """
    
    data = weekly_counts.copy()
    
    # Apply time range filter
    start_date, end_date = time_range
    
    # Convert to datetime if strings
    if isinstance(start_date, str):
        start_date = pd.to_datetime(start_date)
    if isinstance(end_date, str):
        end_date = pd.to_datetime(end_date)
        
    # Filter data within the time range
    data = data[(data['week'] >= start_date) & (data['week'] <= end_date)]
    
    if len(data) == 0:
        print(f"No data found in the specified time range: {start_date.date()} to {end_date.date()}")
        return None
    
    # Get top N job types by total volume using CORE_DESCRIPTION for display
    top_jobs = data.groupby('CORE_DESCRIPTION')['order_count'].sum().nlargest(top_n).index
    
    # Filter data for top jobs
    weekly_top = data[data['CORE_DESCRIPTION'].isin(top_jobs)]
    weekly_viz = weekly_top.groupby(['week', 'CORE_DESCRIPTION'])['order_count'].sum().reset_index()
    
    title = f'Weekly Order Volume Trends - Top {top_n} Job Types<br><span style="font-size:14px; color:gray">{start_date.strftime("%B %d, %Y")} to {end_date.strftime("%B %d, %Y")}</span>'
    
    colors = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
    ]
    
    fig = px.line(weekly_viz, 
                  x='week', 
                  y='order_count', 
                  color='CORE_DESCRIPTION',
                  title=title,
                  color_discrete_sequence=colors,
                  labels={
                      'week': 'Week',
                      'order_count': 'Weekly Order Count',
                      'CORE_DESCRIPTION': 'Job Type'
                  })
    
    fig.update_traces(
        line=dict(width=3),
        marker=dict(size=6),
        mode='lines+markers',
        hovertemplate='<b>%{fullData.name}</b><br>' +
                      'Week: %{x|%Y-%m-%d}<br>' +
                      'Orders: %{y:,}<br>' +
                      '<extra></extra>'
    )
    
    fig.update_layout(
        width=1400,
        height=700,
        font=dict(family="Arial, sans-serif", size=12),
        title=dict(
            font=dict(size=18, color='#2c3e50'),
            x=0.5,
            xanchor='center',
            pad=dict(t=20)
        ),
        xaxis=dict(
            title=dict(text='Week', font=dict(size=14, color='#2c3e50')),
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)',
            showline=True,
            linecolor='#2c3e50',
            tickfont=dict(size=11)
        ),
        yaxis=dict(
            title=dict(text='Weekly Order Count', font=dict(size=14, color='#2c3e50')),
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)',
            showline=True,
            linecolor='#2c3e50',
            tickfont=dict(size=11)
        ),
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.98,
            xanchor="left",
            x=1.02,
            font=dict(size=11),
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='rgba(128,128,128,0.5)',
            borderwidth=1
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode='x unified',
        margin=dict(l=80, r=150, t=100, b=80)
    )
    
    total_weeks = len(weekly_viz['week'].unique())
    total_orders = weekly_viz['order_count'].sum()
    avg_weekly_orders = total_orders / total_weeks if total_weeks > 0 else 0
    
    fig.add_annotation(
        text=f'<b>Summary Statistics</b><br>' +
             f'Time Period: {total_weeks} weeks<br>' +
             f'Total Orders: {total_orders:,}<br>' +
             f'Avg Weekly Orders: {avg_weekly_orders:.0f}',
        xref="paper", yref="paper",
        x=0.02, y=0.98,
        showarrow=False,
        font=dict(size=10, color="#34495e"),
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor="#bdc3c7",
        borderwidth=1,
        borderpad=8,
        align="left"
    )
    
    return fig


def plot_monthly_orders_plotly(monthly_counts, time_range, top_n=10):
    """
    Create interactive monthly order count plot using Plotly optimized for presentation
    
    Parameters:
    - monthly_counts: DataFrame with monthly order counts
    - time_range: Tuple of (start_date, end_date) to filter data
                 Can be strings like '2023-01-01' or datetime objects
    - top_n: Number of top job types to display

    Example usage:
        monthly_fig = plot_monthly_orders_plotly(
            monthly_counts, 
            time_range=('2024-01-01', '2024-12-31'),
            top_n=5
        )
        monthly_fig.show()
    """
    
    data = monthly_counts.copy()
    
    # Apply time range filter
    start_date, end_date = time_range
    
    # Convert to datetime if strings
    if isinstance(start_date, str):
        start_date = pd.to_datetime(start_date)
    if isinstance(end_date, str):
        end_date = pd.to_datetime(end_date)
        
    # Filter data within the time range
    data = data[(data['month'] >= start_date) & (data['month'] <= end_date)]
    
    if len(data) == 0:
        print(f"No data found in the specified time range: {start_date.date()} to {end_date.date()}")
        return None
    
    # Get top N job types by total volume using CORE_DESCRIPTION for display
    top_jobs = data.groupby('CORE_DESCRIPTION')['order_count'].sum().nlargest(top_n).index
    
    # Filter data for top jobs
    monthly_top = data[data['CORE_DESCRIPTION'].isin(top_jobs)]
    monthly_viz = monthly_top.groupby(['month', 'CORE_DESCRIPTION'])['order_count'].sum().reset_index()
    
    title = f'Monthly Order Volume Trends - Top {top_n} Job Types<br><span style="font-size:14px; color:gray">{start_date.strftime("%B %d, %Y")} to {end_date.strftime("%B %d, %Y")}</span>'
    
    colors = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
    ]
    
    fig = px.line(monthly_viz, 
                  x='month', 
                  y='order_count', 
                  color='CORE_DESCRIPTION',
                  title=title,
                  color_discrete_sequence=colors,
                  labels={
                      'month': 'Month',
                      'order_count': 'Monthly Order Count',
                      'CORE_DESCRIPTION': 'Job Type'
                  })
    
    fig.update_traces(
        line=dict(width=3),
        marker=dict(size=8),
        mode='lines+markers',
        hovertemplate='<b>%{fullData.name}</b><br>' +
                      'Month: %{x|%Y-%m}<br>' +
                      'Orders: %{y:,}<br>' +
                      '<extra></extra>'
    )
    
    fig.update_layout(
        width=1400,
        height=700,
        font=dict(family="Arial, sans-serif", size=12),
        title=dict(
            font=dict(size=18, color='#2c3e50'),
            x=0.5,
            xanchor='center',
            pad=dict(t=20)
        ),
        xaxis=dict(
            title=dict(text='Month', font=dict(size=14, color='#2c3e50')),
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)',
            showline=True,
            linecolor='#2c3e50',
            tickfont=dict(size=11)
        ),
        yaxis=dict(
            title=dict(text='Monthly Order Count', font=dict(size=14, color='#2c3e50')),
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)',
            showline=True,
            linecolor='#2c3e50',
            tickfont=dict(size=11)
        ),
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.98,
            xanchor="left",
            x=1.02,
            font=dict(size=11),
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='rgba(128,128,128,0.5)',
            borderwidth=1
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode='x unified',
        margin=dict(l=80, r=150, t=100, b=80)
    )
    
    total_months = len(monthly_viz['month'].unique())
    total_orders = monthly_viz['order_count'].sum()
    avg_monthly_orders = total_orders / total_months if total_months > 0 else 0
    
    fig.add_annotation(
        text=f'<b>Summary Statistics</b><br>' +
             f'Time Period: {total_months} months<br>' +
             f'Total Orders: {total_orders:,}<br>' +
             f'Avg Monthly Orders: {avg_monthly_orders:.0f}',
        xref="paper", yref="paper",
        x=0.02, y=0.98,
        showarrow=False,
        font=dict(size=10, color="#34495e"),
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor="#bdc3c7",
        borderwidth=1,
        borderpad=8,
        align="left"
    )
    
    return fig


if __name__ == "__main__":

    sort_folder = './sort'
    parquet_files = [f for f in os.listdir(sort_folder) if f.endswith('.parquet')]

    datasets = {}
    file_names = ['REP_ORD_ORDER.parquet', 'REP_ORD_JOB_CODE.parquet']

    for file in file_names:
        file_path = os.path.join(sort_folder, file)
        df = pd.read_parquet(file_path)
        datasets[file] = df

    order = datasets['REP_ORD_ORDER.parquet']
    order_job_code = datasets['REP_ORD_JOB_CODE.parquet']

    order_merged = order.merge(order_job_code, left_on='JOB_CODE', right_on='JOB_CODE_ID', how='left', suffixes=('', '_job'))

    # Convert relevant columns to datetime
    time_col = ['ELIGIBLE', 'EXPIRES', 'TIMESTAMP', 'UPDATE_STAMP', 'TIMESTAMP_job']

    order_merged[time_col] = order_merged[time_col].apply(pd.to_datetime, errors='coerce')

    # Updated aggregation code to use JOB_CODE_ID for counting and CORE_DESCRIPTION for display
    df_clean = order_merged.dropna(subset=['ELIGIBLE', 'CORE_DESCRIPTION', 'JOB_CODE_ID']).copy()

    # Extract date components
    df_clean['date'] = df_clean['ELIGIBLE'].dt.date
    df_clean['week'] = df_clean['ELIGIBLE'].dt.to_period('W').dt.start_time
    df_clean['month'] = df_clean['ELIGIBLE'].dt.to_period('M').dt.start_time

    # 1. DAILY AGGREGATION
    daily_counts = df_clean.groupby(['date', 'JOB_CODE_ID', 'CORE_DESCRIPTION']).size().reset_index(name='order_count')
    daily_counts['date'] = pd.to_datetime(daily_counts['date'])

    # 2. WEEKLY AGGREGATION
    weekly_counts = df_clean.groupby(['week', 'JOB_CODE_ID', 'CORE_DESCRIPTION']).size().reset_index(name='order_count')

    # 3. MONTHLY AGGREGATION
    monthly_counts = df_clean.groupby(['month', 'JOB_CODE_ID', 'CORE_DESCRIPTION']).size().reset_index(name='order_count')


    # Example usage of aggregated visualization 
    daily_fig = plot_daily_orders_plotly(
        daily_counts, 
        top_n=3, 
        time_range=('2023-01-01', '2024-12-31')
    )
    daily_fig.show()

    weekly_fig = plot_weekly_orders_plotly(
        weekly_counts, 
        time_range=('2024-01-01', '2024-12-31'),
        top_n=6
    )
    weekly_fig.show()

    monthly_fig = plot_monthly_orders_plotly(
        monthly_counts, 
        time_range=('2024-01-01', '2024-12-31'),
        top_n=5
    )
    monthly_fig.show()

