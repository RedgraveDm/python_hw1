import multiprocessing
import pandas as pd
import time

df = pd.read_csv('temperature_data.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])


def calculate_moving_average(city_data):
    city_data = city_data.sort_values(by=['timestamp'])
    city_data['t_moving_average'] = city_data['temperature'].transform(
        lambda x: x.rolling(window=30, min_periods=1).mean()
    )
    return city_data


def calculate_seasonal_stats(city_data):
    seasonal_stats = city_data.groupby(['season']).agg(
        mean_temperature=('temperature', 'mean'),
        std_temperature=('temperature', 'std')
    ).reset_index()
    return seasonal_stats


def process_city_data(city):
    city_data = df[df['city'] == city]
    city_data = calculate_moving_average(city_data)
    seasonal_stats = calculate_seasonal_stats(city_data)
    city_data = city_data.merge(seasonal_stats[['season', 'mean_temperature', 'std_temperature']], on='season', how='left')
    city_data['anomaly'] = (
        (city_data['temperature'] < city_data['mean_temperature'] - 2 * city_data['std_temperature']) |
        (city_data['temperature'] > city_data['mean_temperature'] + 2 * city_data['std_temperature'])
    )
    return city_data


if __name__ == '__main__':
    t_start = time.time_ns()

    with multiprocessing.Pool() as pool:
        result = pool.map(process_city_data, df['city'].unique())

    df = pd.concat(result, ignore_index=True)

    t_end = time.time_ns()
    print('Execution time:', (t_end - t_start) / 1e6, 'ms')

    print(df)
