import requests
import pandas as pd
from datetime import datetime, timedelta
from io import StringIO

# Ottawa coordinates
OTTAWA_LAT = 45.4215
OTTAWA_LON = -75.6972

# ============================================================
# AQHI DATA (Environment Canada)
# ============================================================

def fetch_aqhi_data(latitude: float = OTTAWA_LAT, longitude: float = OTTAWA_LON) -> dict:
    """
    Fetches current AQHI data from Environment Canada using bbox query.
    """
    # Use bbox query - more reliable than lat/lon
    buffer = 0.1
    min_lon = longitude - buffer
    max_lon = longitude + buffer
    min_lat = latitude - buffer
    max_lat = latitude + buffer
    bbox = f"{min_lon},{min_lat},{max_lon},{max_lat}"
    
    url = (
        f"https://api.weather.gc.ca/collections/aqhi-observations-realtime/items"
        f"?f=json&lang=en&bbox={bbox}&limit=1"
    )
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data.get("features"):
            return {"status": "error", "message": "No AQHI data available"}
        
        properties = data["features"][0].get("properties", {})
        aqhi_value = properties.get("aqhi")
        
        if aqhi_value is None:
            return {"status": "error", "message": "AQHI value not available"}
        
        if aqhi_value >= 10:
            risk = "Very High"
        elif aqhi_value >= 7:
            risk = "High"
        elif aqhi_value >= 4:
            risk = "Moderate"
        else:
            risk = "Low"
        
        return {
            "status": "success",
            "source": "Environment Canada",
            "station_name": properties.get("station_name", "Ottawa"),
            "aqhi_value": aqhi_value,
            "risk_level": risk,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M EDT")
        }
    
    except Exception as e:
        return {"status": "error", "message": f"AQHI API error: {str(e)}"}


# ============================================================
# INDIVIDUAL POLLUTANTS (Air Quality Ontario)
# ============================================================

def fetch_individual_pollutants() -> dict:
    """
    Fetches real-time individual pollutant concentrations from Air Quality Ontario.
    Returns PM2.5, O3, NO2, SO2, CO for Ottawa Downtown.
    """
    url = "https://www.airqualityontario.com/history/summary.php"
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        tables = pd.read_html(StringIO(response.text), header=0)
        
        pollutant_table = None
        for table in tables:
            if 'Station' in table.columns and 'O3 (ppb)' in table.columns:
                pollutant_table = table
                break
        
        if pollutant_table is None:
            return {"status": "error", "message": "Could not find pollutant table"}
        
        ottawa_data = pollutant_table[
            pollutant_table['Station'].str.contains("Ottawa", na=False)
        ].dropna(how='all')
        
        if ottawa_data.empty:
            return {"status": "error", "message": "No Ottawa station data found"}
        
        ottawa_data_indexed = ottawa_data.set_index('Station')
        
        # Find the station (try different names)
        station_name = None
        for name in ['Ottawa Downtown', 'Ottawa Central', 'Ottawa']:
            if name in ottawa_data_indexed.index:
                station_name = name
                break
        
        if not station_name:
            return {"status": "error", "message": "No matching Ottawa station found"}
        
        station_row = ottawa_data_indexed.loc[station_name]
        
        return {
            "status": "success",
            "source": "Air Quality Ontario",
            "station": station_name,
            "pm25": float(station_row['PM2.5 (µg/m3)']) if 'PM2.5 (µg/m3)' in station_row else None,
            "o3": float(station_row['O3 (ppb)']) if 'O3 (ppb)' in station_row else None,
            "no2": float(station_row['NO2 (ppb)']) if 'NO2 (ppb)' in station_row else None,
            "so2": station_row.get('SO2 (ppb)'),
            "co": station_row.get('CO (ppm)'),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M EDT")
        }
    
    except Exception as e:
        return {"status": "error", "message": f"Pollutant API error: {str(e)}"}


# ============================================================
# HISTORICAL AQHI TREND (3-Day Time Series)
# ============================================================

def fetch_aqhi_historical_trend() -> dict:
    """
    Fetches historical AQHI observations for the past 3 days.
    Uses Environment Canada's real-time observations API with bounding box.
    """
    buffer = 0.25
    min_lon = OTTAWA_LON - buffer
    min_lat = OTTAWA_LAT - buffer
    max_lon = OTTAWA_LON + buffer
    max_lat = OTTAWA_LAT + buffer
    bbox_string = f"{min_lon},{min_lat},{max_lon},{max_lat}"
    
    url = (
        "https://api.weather.gc.ca/collections/aqhi-observations-realtime/items"
        f"?lang=en&f=json&bbox={bbox_string}&limit=100"
    )
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data.get('features'):
            return {"status": "error", "message": "No historical AQHI data available"}
        
        plot_data = []
        for feature in data['features']:
            props = feature.get('properties', {})
            timestamp = props.get('observation_datetime')
            aqhi_value = props.get('aqhi')
            
            if timestamp and aqhi_value is not None:
                plot_data.append({
                    'timestamp': timestamp,
                    'aqhi': float(aqhi_value)
                })
        
        if not plot_data:
            return {"status": "error", "message": "No valid AQHI observations found"}
        
        df = pd.DataFrame(plot_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values(by='timestamp')
        
        # Calculate trend metrics
        current_aqhi = df['aqhi'].iloc[-1]
        previous_aqhi = df['aqhi'].iloc[0]
        avg_aqhi = df['aqhi'].mean()
        max_aqhi = df['aqhi'].max()
        min_aqhi = df['aqhi'].min()
        
        change_percent = ((current_aqhi - previous_aqhi) / previous_aqhi * 100) if previous_aqhi > 0 else 0
        
        # CRITICAL: Only flag as "worsening" if crossing into MODERATE or HIGH zones
        # If max_aqhi never leaves LOW zone (1-3), it's STABLE not worsening
        if max_aqhi <= 3:
            # All values are in LOW risk zone - this is stable/safe
            trend = "stable_low"
        elif current_aqhi > previous_aqhi and max_aqhi > 3:
            # Moving upward AND into moderate/high zone
            trend = "increasing"
        elif current_aqhi < previous_aqhi:
            trend = "decreasing"
        else:
            trend = "stable"
        
        return {
            "status": "success",
            "source": "Environment Canada Historical",
            "data_points": len(df),
            "current_aqhi": current_aqhi,
            "previous_aqhi": previous_aqhi,
            "average_aqhi": avg_aqhi,
            "max_aqhi": max_aqhi,
            "min_aqhi": min_aqhi,
            "trend": trend,
            "change_percent": round(change_percent, 1),
            "time_range": f"{df['timestamp'].min().strftime('%Y-%m-%d %H:%M')} to {df['timestamp'].max().strftime('%Y-%m-%d %H:%M')}",
            "timestamps": df['timestamp'].astype(str).tolist(),
            "aqhi_values": df['aqhi'].tolist()
        }
    
    except Exception as e:
        return {"status": "error", "message": f"Historical AQHI error: {str(e)}"}


# ============================================================
# WEATHER DATA
# ============================================================

def fetch_weather_data(latitude: float = OTTAWA_LAT, longitude: float = OTTAWA_LON) -> dict:
    """
    Fetches real-time weather data from Open-Meteo API.
    """
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={latitude}&longitude={longitude}"
        f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code,is_day"
        f"&timezone=America/Toronto"
    )
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        current = data.get("current", {})
        
        weather_code = current.get("weather_code", 0)
        weather_descriptions = {
            0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
            45: "Foggy", 51: "Light drizzle", 61: "Slight rain", 63: "Moderate rain",
            65: "Heavy rain", 71: "Slight snow", 95: "Thunderstorm",
        }
        
        weather_desc = weather_descriptions.get(weather_code, "Unknown")
        
        return {
            "status": "success",
            "source": "Open-Meteo",
            "temperature_celsius": current.get("temperature_2m"),
            "relative_humidity": current.get("relative_humidity_2m"),
            "wind_speed_kmh": current.get("wind_speed_10m"),
            "weather_condition": weather_desc,
            "is_daytime": current.get("is_day") == 1,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M EDT")
        }
    
    except Exception as e:
        return {"status": "error", "message": f"Weather API error: {str(e)}"}


# ============================================================
# POLLEN DATA
# ============================================================

def fetch_pollen_data(latitude: float = OTTAWA_LAT, longitude: float = OTTAWA_LON) -> dict:
    """
    Fetches pollen concentration data for Ottawa (seasonal).
    """
    month = datetime.now().month
    
    pollen_seasons = {
        1: {"tree": "Low", "grass": "None", "weed": "None"},
        2: {"tree": "Low", "grass": "None", "weed": "None"},
        3: {"tree": "Moderate", "grass": "Low", "weed": "None"},
        4: {"tree": "High", "grass": "Moderate", "weed": "Low"},
        5: {"tree": "Moderate", "grass": "High", "weed": "Moderate"},
        6: {"tree": "Low", "grass": "High", "weed": "High"},
        7: {"tree": "None", "grass": "Moderate", "weed": "High"},
        8: {"tree": "None", "grass": "Low", "weed": "High"},
        9: {"tree": "Low", "grass": "Moderate", "weed": "High"},
        10: {"tree": "Moderate", "grass": "Low", "weed": "Moderate"},
        11: {"tree": "Low", "grass": "None", "weed": "None"},
        12: {"tree": "Low", "grass": "None", "weed": "None"},
    }
    
    current_pollen = pollen_seasons.get(month, {"tree": "Unknown", "grass": "Unknown", "weed": "Unknown"})
    
    return {
        "status": "success",
        "source": "Seasonal Data (Ottawa)",
        "tree_pollen": current_pollen["tree"],
        "grass_pollen": current_pollen["grass"],
        "weed_pollen": current_pollen["weed"],
        "month": datetime.now().strftime("%B"),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M EDT")
    }