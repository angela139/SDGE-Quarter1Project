import pandas as pd
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


def expand_records_and_calculate_utilization(DF_work, additional_cols=None, group_by_cols=None):
    """
    Expands multi-day job records and calculate daily utilization rate.
    
    Args:
        DF_work (pd.DataFrame): Preprocessed work dataset
        additional_cols (list): Additional columns to include in expanded records
        group_by_cols (list): Additional columns to group by
    
    Returns:
        pd.DataFrame: Daily aggregation with utilization metrics
    """
    if additional_cols is None:
        additional_cols = []
    
    if group_by_cols is None:
        group_by_cols = ['LOGON_ID', 'DATE']
    else:
        group_by_cols = ['LOGON_ID', 'DATE'] + group_by_cols
    
    expanded_records = []
    
    for idx, row in DF_work.iterrows():
        if pd.notna(row['WORK_START']) and pd.notna(row['WORK_END']):
            work_dates = get_work_dates(row['WORK_START'], row['WORK_END'])
            
            if len(work_dates) == 1:
                record = {
                    'LOGON_ID': row['LOGON_ID'],
                    'DATE': work_dates[0],
                    'TOTAL_TIME_EN_ROUTE': row['TOTAL_TIME_EN_ROUTE'],
                    'TOTAL_TIME_ON_SITE': row['TOTAL_TIME_ON_SITE']
                }
                for col in additional_cols:
                    record[col] = row[col]
                expanded_records.append(record)
            else:
                n_days = len(work_dates)
                
                for d in work_dates:
                    record = {
                        'LOGON_ID': row['LOGON_ID'],
                        'DATE': d,
                        'TOTAL_TIME_EN_ROUTE': row['TOTAL_TIME_EN_ROUTE'] / n_days,
                        'TOTAL_TIME_ON_SITE': row['TOTAL_TIME_ON_SITE'] / n_days
                    }
                    for col in additional_cols:
                        record[col] = row[col]
                    expanded_records.append(record)
    
    expanded_df = pd.DataFrame(expanded_records)

    daily = expanded_df.groupby(group_by_cols, as_index=False).agg({
        'TOTAL_TIME_EN_ROUTE': 'sum',
        'TOTAL_TIME_ON_SITE': 'sum'
    })
    
    daily['TOTAL_WORKED'] = daily['TOTAL_TIME_EN_ROUTE'] + daily['TOTAL_TIME_ON_SITE']
    daily['DAILY_UTILIZATION_RATIO'] = daily['TOTAL_WORKED'] / (7 * 60 * 60)
    daily['DAILY_UTILIZATION_%'] = daily['DAILY_UTILIZATION_RATIO'] * 100

    return daily

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
    
    daily = expand_records_and_calculate_utilization(
        DF_clean, 
        additional_cols=['ZIP5'],
        group_by_cols=['ZIP5']
    )
    
    zip_util = daily.groupby('ZIP5', as_index=False).agg({
        'DAILY_UTILIZATION_%': 'mean',
        'TOTAL_WORKED': 'sum',
        'LOGON_ID': 'count'
    })
    
    zip_util = zip_util.rename(columns={'LOGON_ID': 'TOTAL_JOBS', 'DAILY_UTILIZATION_%': 'DAILY_UTIL_%'})
    zip_util['DAILY_UTIL_%'] = zip_util['DAILY_UTIL_%'].round(2)
    
    return zip_util

def calculate_technician_utilization(DF):
    """
    Calculate technician utilization using actual timestamps.
    
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
    
    DF_work['TOTAL_TIME_EN_ROUTE'] = (DF_work['ONSITE_START'] - DF_work['WORK_START']).dt.total_seconds()
    DF_work['TOTAL_TIME_ON_SITE'] = (DF_work['WORK_END'] - DF_work['ONSITE_START']).dt.total_seconds()
    
    daily = expand_records_and_calculate_utilization(DF_work)
    
    tech_util = daily.groupby('LOGON_ID', as_index=False).agg({
        'DAILY_UTILIZATION_RATIO': 'mean'
    })
    tech_util['UTILIZATION_%'] = tech_util['DAILY_UTILIZATION_RATIO'] * 100
    
    return tech_util

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

def prepare_job_lifecycle_analysis(DF):
    """
    Prepare data for job lifecycle timing analysis.
    
    Args:
        DF (pd.DataFrame): Merged dataset
    
    Returns:
        pd.DataFrame: Dataset with calculated timing columns
    """
    DF_lifecycle = DF.copy()
    
    timestamp_cols = ['COMPLETED', 'CLOSED', 'DISPATCH_AT', 'RECEIVED_AT', 
                     'ACKNOWLEDGED_AT', 'ENROUTE_AT', 'ONSITE_AT']
    for col in timestamp_cols:
        DF_lifecycle[col] = pd.to_datetime(DF_lifecycle[col], errors='coerce')
    
    DF_lifecycle = DF_lifecycle.dropna(subset=['ACKNOWLEDGED_AT'])
    
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


def prepare_hourly_data(DF):
    '''
    Prepare hourly technician activity data from order timestamps.
    
    Args:
        DF (pd.DataFrame): Hourly dataset
    
    Returns:
        pd.DataFrame: Hourly technician activity with utilization metrics
    '''

    # Calculate actual work duration using timestamps
    DF['WORK_START'] = DF['ENROUTE_AT']  # When work actually started
    DF['WORK_END'] = DF['COMPLETED']     # When work actually ended

    # Calculate actual work duration in minutes
    DF['ACTUAL_WORK_DURATION'] = (DF['WORK_END'] - DF['WORK_START']).dt.total_seconds() / 60

    # Create date ranges for orders spanning multiple days
    def get_work_dates(start_time, end_time):
        """Get all dates between start and end of work"""
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

    # Calculate daily work time for each order
    expanded_records = []

    for idx, row in DF.iterrows():
        if pd.notna(row['WORK_START']) and pd.notna(row['WORK_END']):
            work_dates = get_work_dates(row['WORK_START'], row['WORK_END'])
            
            if len(work_dates) == 1:
                # Single day work
                expanded_records.append({
                    'TECH_ID': row['LOGON_ID'],
                    'DATE': work_dates[0],
                    'DAILY_WORK_TIME': row['ACTUAL_WORK_DURATION'],
                })
            else:
                # Multi-day work - distribute time across days
                total_duration = row['ACTUAL_WORK_DURATION']
                daily_duration = total_duration / len(work_dates)
                
                for work_date in work_dates:
                    expanded_records.append({
                        'TECH_ID': row['LOGON_ID'],
                        'DATE': work_date,
                        'DAILY_WORK_TIME': daily_duration,
                    })

    expanded_df = pd.DataFrame(expanded_records)

    # Extract hourly data
    expanded_df['WORK_START_HOUR'] = pd.to_datetime(expanded_df['WORK_START']).dt.hour
    expanded_df['WORK_END_HOUR'] = pd.to_datetime(expanded_df['WORK_END']).dt.hour

    # Hourly analysis with utilization and idle time calculations
    def create_hourly_activity_data():
        hourly_records = []
        
        for idx, row in expanded_df.iterrows():
            if pd.notna(row['WORK_START_HOUR']) and pd.notna(row['WORK_END_HOUR']):
                start_hour = int(row['WORK_START_HOUR'])
                end_hour = int(row['WORK_END_HOUR'])
                duration = row['DAILY_WORK_TIME']
                
                # If work spans multiple hours, distribute time across hours
                if start_hour == end_hour:
                    # Work completed within same hour
                    hourly_records.append({
                        'TECH_ID': row['TECH_ID'],
                        'DATE': row['DATE'],
                        'HOUR': start_hour,
                        'WORK_MINUTES': duration,
                        'ORDER_COUNT': 1
                    })
                else:
                    # Work spans multiple hours - distribute evenly
                    if end_hour < start_hour:  # Work crosses midnight
                        hours_worked = (24 - start_hour) + end_hour
                    else:
                        hours_worked = end_hour - start_hour + 1
                    
                    minutes_per_hour = duration / hours_worked
                    
                    current_hour = start_hour
                    while True:
                        hourly_records.append({
                            'TECH_ID': row['TECH_ID'],
                            'DATE': row['DATE'],
                            'HOUR': current_hour,
                            'WORK_MINUTES': minutes_per_hour,
                            'ORDER_COUNT': 1/hours_worked  # Fraction of order per hour
                        })
                        
                        current_hour = (current_hour + 1) % 24
                        if current_hour == (end_hour % 24):
                            break
        
        return pd.DataFrame(hourly_records)

    hourly_df = create_hourly_activity_data()

    # Calculate utilization and idle time for each tech-hour combination
    HOUR_MINUTES = 60  # 60 minutes per hour

    # Calculate utilization rate and idle time for each record
    hourly_df['UTILIZATION_RATE'] = (hourly_df['WORK_MINUTES'] / HOUR_MINUTES).clip(upper=1.0)  # Cap at 100%
    hourly_df['IDLE_MINUTES'] = HOUR_MINUTES - hourly_df['WORK_MINUTES']
    hourly_df['IDLE_MINUTES'] = hourly_df['IDLE_MINUTES'].clip(lower=0)  # No negative idle time
    hourly_df['IDLE_TIME_PCT'] = (hourly_df['IDLE_MINUTES'] / HOUR_MINUTES) * 100

    # Add additional time dimensions for analysis
    hourly_df['DAY_OF_WEEK'] = pd.to_datetime(hourly_df['DATE']).dt.day_name()
    hourly_df['MONTH'] = pd.to_datetime(hourly_df['DATE']).dt.month_name()
    hourly_df['IS_WEEKEND'] = pd.to_datetime(hourly_df['DATE']).dt.dayofweek.isin([5, 6])
    hourly_df['IS_BUSINESS_HOUR'] = hourly_df['HOUR'].between(8, 17)

    return hourly_df

