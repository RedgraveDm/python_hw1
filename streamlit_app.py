import streamlit as st
import pandas as pd
import plotly.express as px
import requests


def get_geolocation(city, api_key):
    url = f'http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={api_key}'
    response = requests.get(url)
    if response.status_code == 401:
        return {"error": "Invalid API key"}
    response.raise_for_status()
    response_data = response.json()
    if response_data:
        return {"lat": response_data[0]["lat"], "lon": response_data[0]["lon"]}
    return {"error": "City not found"}


def get_current_temp(lat, lon, api_key):
    url = f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric'
    response = requests.get(url)
    if response.status_code == 401:
        return {"error": "Invalid API key"}
    response.raise_for_status()
    data = response.json()
    return data["main"]["temp"]


st.title("Анализ температуры и аномалий")
uploaded_file = st.file_uploader("Загрузите CSV файл с историческими данными:", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    st.write("Данные успешно загружены!")
    st.dataframe(df.head())

    selected_city = st.selectbox("Выберите город", df['city'].unique())
    city_data = df[df['city'] == selected_city]

    st.subheader(f"Описательные статистики для исторических данных по городу {selected_city}")
    st.write(city_data.describe())

    st.subheader("Временной ряд температур с аномалиями")
    seasonal_stats = city_data.groupby(['season']).agg(
        mean_temperature=('temperature', 'mean'),
        std_temperature=('temperature', 'std')
    ).reset_index()
    city_data = city_data.merge(seasonal_stats[['season', 'mean_temperature', 'std_temperature']],
                                on=['season'],
                                how='left')
    city_data['anomaly'] = (
            (city_data['temperature'] < city_data['mean_temperature'] - 2 * city_data['std_temperature']) |
            (city_data['temperature'] > city_data['mean_temperature'] + 2 * city_data['std_temperature'])
    )
    fig = px.scatter(city_data,
                     x='timestamp',
                     y='temperature',
                     color='anomaly',
                     title="Температуры с выделением аномалий")
    st.plotly_chart(fig)

    st.subheader("Сезонные профили")
    st.write(seasonal_stats)

    st.subheader("Текущая температура")
    api_key = st.text_input("Введите API-ключ OpenWeatherMap:")
    if api_key:
        coords = get_geolocation(selected_city, api_key)
        if "error" in coords:
            st.error(coords["error"])
        else:
            lat, lon = coords["lat"], coords["lon"]
            try:
                curr_temp = get_current_temp(lat, lon, api_key)
                st.write(f"Текущая температура: {curr_temp}°C")

                cur_season_data = city_data[city_data['season'] == 'winter']
                mean_temp = cur_season_data['mean_temperature'].iloc[0]
                std_temp = cur_season_data['std_temperature'].iloc[0]

                lower_bound = mean_temp - 2 * std_temp
                upper_bound = mean_temp + 2 * std_temp

                if lower_bound <= curr_temp <= upper_bound:
                    st.success("Текущая температура нормальна для зимы")
                else:
                    st.warning("Текущая температура аномальна для зимы")
            except requests.exceptions.RequestException:
                st.error("Ошибка при запросе текущей температуры")
