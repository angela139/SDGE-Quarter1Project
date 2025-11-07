import pandas as pd
import os
import plotly.express as px
from scipy import datasets
import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd
from datetime import date

def start_app_dashboard(df_clean, daily_counts, weekly_counts, monthly_counts):
    # Initialize the Dash app
    app = dash.Dash(__name__)

    app.layout = html.Div([
        html.Div([
            html.H1("Order Volume Analysis Dashboard", 
                    style={'textAlign': 'center', 'marginBottom': 30, 'color': '#2c3e50'}),
            
            html.Div([
                html.Div([
                    html.Label("Time Aggregation:", style={'fontWeight': 'bold', 'marginBottom': 10}),
                    html.Div([
                        html.Button('Daily', id='daily-btn', n_clicks=1, 
                                className='btn-selected', style={'margin': '0 5px'}),
                        html.Button('Weekly', id='weekly-btn', n_clicks=0, 
                                className='btn-unselected', style={'margin': '0 5px'}),
                        html.Button('Monthly', id='monthly-btn', n_clicks=0, 
                                className='btn-unselected', style={'margin': '0 5px'})
                    ], style={'display': 'flex', 'gap': '10px'})
                ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top'}),
                
                html.Div([
                    html.Label("Top N Job Types:", style={'fontWeight': 'bold', 'marginBottom': 10}),
                    dcc.Input(
                        id='top-n-input',
                        type='number',
                        value=5,
                        min=1,
                        max=20,
                        step=1,
                        style={'width': '80px', 'padding': '8px', 'textAlign': 'center', 'fontSize': '14px'}
                    )
                ], style={'width': '20%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': 30}),
                
                html.Div([
                    html.Label("Date Range:", style={'fontWeight': 'bold', 'marginBottom': 10}),
                    html.Div([
                        html.Div([
                            html.Label("Start Date:", style={'fontSize': '12px', 'marginBottom': 5, 'fontWeight': 'normal'}),
                            dcc.DatePickerSingle(
                                id='start-date-picker',
                                date=date(2024, 1, 1),  # Will be updated dynamically
                                display_format='YYYY-MM-DD',
                                style={'width': '140px'}
                            )
                        ], style={'display': 'inline-block', 'marginRight': 20}),
                        html.Div([
                            html.Label("End Date:", style={'fontSize': '12px', 'marginBottom': 5, 'fontWeight': 'normal'}),
                            dcc.DatePickerSingle(
                                id='end-date-picker',
                                date=date(2024, 12, 31),  # Will be updated dynamically
                                display_format='YYYY-MM-DD',
                                style={'width': '140px'}
                            )
                        ], style={'display': 'inline-block'})
                    ])
                ], style={'width': '45%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': 30})
                
            ], style={'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '10px', 'margin': '20px'}),
            
            dcc.Graph(id='main-plot', style={'height': '700px'})
            
        ], style={'maxWidth': '1600px', 'margin': '0 auto', 'padding': '20px'})
    ], style={'backgroundColor': '#ffffff', 'minHeight': '100vh'})

    app.index_string = '''
    <!DOCTYPE html>
    <html>
        <head>
            {%metas%}
            <title>Order Volume Dashboard</title>
            {%favicon%}
            {%css%}
            <style>
                .btn-selected {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    cursor: pointer;
                    font-weight: bold;
                    transition: background-color 0.3s;
                }
                .btn-unselected {
                    background-color: #ecf0f1;
                    color: #2c3e50;
                    border: 1px solid #bdc3c7;
                    padding: 10px 20px;
                    border-radius: 5px;
                    cursor: pointer;
                    transition: background-color 0.3s;
                }
                .btn-unselected:hover {
                    background-color: #d5dbdb;
                }
                .DateInput_input {
                    font-size: 14px !important;
                    padding: 8px !important;
                    border: 1px solid #bdc3c7 !important;
                    border-radius: 4px !important;
                }
                .DateInput {
                    width: 140px !important;
                }
            </style>
        </head>
        <body>
            {%app_entry%}
            <footer>
                {%config%}
                {%scripts%}
                {%renderer%}
            </footer>
        </body>
    </html>
    '''

    def create_time_plot(data, time_range, top_n, plot_type):
        """
        Plotting function for daily, weekly, and monthly data
        
        Parameters:
        - data: DataFrame with order counts (daily_counts, weekly_counts, or monthly_counts)
        - time_range: Tuple of (start_date, end_date) to filter data
        - top_n: Number of top job types to display
        - plot_type: 'daily', 'weekly', or 'monthly'
        """
        
        df = data.copy()
        
        time_col = {'daily': 'date', 'weekly': 'week', 'monthly': 'month'}[plot_type]
        
        # Apply time range filter
        start_date, end_date = time_range
        
        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date)
        if isinstance(end_date, str):
            end_date = pd.to_datetime(end_date)
            
        # Filter data within the time range
        df = df[(df[time_col] >= start_date) & (df[time_col] <= end_date)]
        
        if len(df) == 0:
            # Return empty plot with message
            fig = px.line(title="No data found in the specified time range")
            fig.update_layout(
                width=1400, height=700,
                title=dict(font=dict(size=18, color='#2c3e50'), x=0.5),
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            return fig
        
        # Get top N job types by total volume using CORE_DESCRIPTION for display
        top_jobs = df.groupby('CORE_DESCRIPTION')['order_count'].sum().nlargest(top_n).index
        
        # Filter data for top jobs
        df_top = df[df['CORE_DESCRIPTION'].isin(top_jobs)]
        
        # Aggregate by time and CORE_DESCRIPTION for visualization
        df_viz = df_top.groupby([time_col, 'CORE_DESCRIPTION'])['order_count'].sum().reset_index()
        
        # Create title based on plot type
        time_labels = {'daily': 'Daily', 'weekly': 'Weekly', 'monthly': 'Monthly'}
        title = f'{time_labels[plot_type]} Order Volume Trends - Top {top_n} Job Types<br><span style="font-size:14px; color:gray">{start_date.strftime("%B %d, %Y")} to {end_date.strftime("%B %d, %Y")}</span>'
        
        colors = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]
        
        fig = px.line(df_viz, 
                    x=time_col, 
                    y='order_count', 
                    color='CORE_DESCRIPTION',
                    title=title,
                    color_discrete_sequence=colors,
                    labels={
                        time_col: time_labels[plot_type],
                        'order_count': f'{time_labels[plot_type]} Order Count',
                        'CORE_DESCRIPTION': 'Job Type'
                    })
        
        marker_size = {'daily': 0, 'weekly': 6, 'monthly': 8}[plot_type]
        mode = 'lines' if plot_type == 'daily' else 'lines+markers'
        
        fig.update_traces(
            line=dict(width=3),
            marker=dict(size=marker_size),
            mode=mode,
            hovertemplate='<b>%{fullData.name}</b><br>' +
                        f'{time_labels[plot_type]}: %{{x|%Y-%m-%d}}<br>' +
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
                title=dict(text=time_labels[plot_type], font=dict(size=14, color='#2c3e50')),
                showgrid=True,
                gridcolor='rgba(128,128,128,0.2)',
                showline=True,
                linecolor='#2c3e50',
                tickfont=dict(size=11)
            ),
            yaxis=dict(
                title=dict(text=f'{time_labels[plot_type]} Order Count', font=dict(size=14, color='#2c3e50')),
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
        
        if plot_type == 'daily':
            total_period = (end_date - start_date).days + 1
            period_label = "days"
        elif plot_type == 'weekly':
            total_period = len(df_viz[time_col].unique())
            period_label = "weeks"
        else:  # monthly
            total_period = len(df_viz[time_col].unique())
            period_label = "months"
        
        total_orders = df_viz['order_count'].sum()
        avg_orders = total_orders / total_period if total_period > 0 else 0
        
        fig.add_annotation(
            text=f'<b>Summary Statistics</b><br>' +
                f'Time Period: {total_period} {period_label}<br>' +
                f'Total Orders: {total_orders:,}<br>' +
                f'Avg {time_labels[plot_type]} Orders: {avg_orders:.0f}',
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

    # Callback to update button styles
    @app.callback(
        [Output('daily-btn', 'className'),
        Output('weekly-btn', 'className'),
        Output('monthly-btn', 'className')],
        [Input('daily-btn', 'n_clicks'),
        Input('weekly-btn', 'n_clicks'),
        Input('monthly-btn', 'n_clicks')]
    )
    def update_button_styles(daily_clicks, weekly_clicks, monthly_clicks):
        ctx = dash.callback_context
        
        if not ctx.triggered:
            return 'btn-selected', 'btn-unselected', 'btn-unselected'
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        daily_class = 'btn-selected' if button_id == 'daily-btn' else 'btn-unselected'
        weekly_class = 'btn-selected' if button_id == 'weekly-btn' else 'btn-unselected'
        monthly_class = 'btn-selected' if button_id == 'monthly-btn' else 'btn-unselected'
        
        return daily_class, weekly_class, monthly_class

    # Callback to initialize date pickers based on data
    @app.callback(
        [Output('start-date-picker', 'date'),
        Output('end-date-picker', 'date'),
        Output('start-date-picker', 'min_date_allowed'),
        Output('start-date-picker', 'max_date_allowed'),
        Output('end-date-picker', 'min_date_allowed'),
        Output('end-date-picker', 'max_date_allowed')],
        [Input('daily-btn', 'n_clicks')]
    )
    def initialize_date_pickers(_):
        # Get date range from your data
        min_date = df_clean['ELIGIBLE'].min()
        max_date = df_clean['ELIGIBLE'].max()
        
        return (min_date.date(), max_date.date(),
                min_date.date(), max_date.date(),
                min_date.date(), max_date.date())

    # Main callback to update the plot
    @app.callback(
        Output('main-plot', 'figure'),
        [Input('daily-btn', 'n_clicks'),
        Input('weekly-btn', 'n_clicks'),
        Input('monthly-btn', 'n_clicks'),
        Input('top-n-input', 'value'),
        Input('start-date-picker', 'date'),
        Input('end-date-picker', 'date')]
    )
    def update_plot(daily_clicks, weekly_clicks, monthly_clicks, top_n, start_date, end_date):
        ctx = dash.callback_context
        
        # Determine which plot type to show
        if not ctx.triggered:
            plot_type = 'daily'
        else:
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
            if button_id == 'weekly-btn':
                plot_type = 'weekly'
            elif button_id == 'monthly-btn':
                plot_type = 'monthly'
            else:
                plot_type = 'daily'
        
        if top_n is None or top_n < 1:
            top_n = 5
        if start_date is None or end_date is None:
            return dash.no_update
        
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        
        if start_date > end_date:
            fig = px.line(title="Error: Start date must be before end date")
            fig.update_layout(
                width=1400, height=700,
                title=dict(font=dict(size=18, color='#e74c3c'), x=0.5),
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            return fig
        
        data_map = {
            'daily': daily_counts,
            'weekly': weekly_counts, 
            'monthly': monthly_counts
        }
        
        # Create and return the plot
        return create_time_plot(
            data_map[plot_type], 
            (start_date, end_date), 
            int(top_n), 
            plot_type
        )

    # Run the app
    app.run(debug=True, host='0.0.0.0', port=8050)


if __name__ == "__main__":

    sort_folder = './sort'
    parquet_files = [f for f in os.listdir(sort_folder) if f.endswith('.parquet')]

    # Load all datasets 
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

    start_app_dashboard(df_clean, daily_counts, weekly_counts, monthly_counts)
