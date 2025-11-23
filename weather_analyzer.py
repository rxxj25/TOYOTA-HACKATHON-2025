"""
Weather Impact Analysis Module
Analyzes how weather conditions affect race performance
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional

class WeatherAnalyzer:
    """Analyzes weather impact on race performance"""
    
    def __init__(self, weather_data: pd.DataFrame, lap_data: pd.DataFrame):
        self.weather_data = weather_data
        self.lap_data = lap_data
    
    def analyze_weather_impact(self) -> Dict:
        """Analyze overall weather impact on performance"""
        if self.weather_data.empty or self.lap_data.empty:
            return {}
        
        # Merge weather with lap data by time
        # For simplicity, we'll analyze correlation between weather and lap times
        
        weather_summary = {
            'avg_temp': self.weather_data['AIR_TEMP'].mean() if 'AIR_TEMP' in self.weather_data.columns else np.nan,
            'max_temp': self.weather_data['AIR_TEMP'].max() if 'AIR_TEMP' in self.weather_data.columns else np.nan,
            'min_temp': self.weather_data['AIR_TEMP'].min() if 'AIR_TEMP' in self.weather_data.columns else np.nan,
            'avg_humidity': self.weather_data['HUMIDITY'].mean() if 'HUMIDITY' in self.weather_data.columns else np.nan,
            'avg_wind_speed': self.weather_data['WIND_SPEED'].mean() if 'WIND_SPEED' in self.weather_data.columns else np.nan,
            'rain_occurred': (self.weather_data['RAIN'].sum() > 0) if 'RAIN' in self.weather_data.columns else False
        }
        
        # Analyze lap time correlation with temperature
        if 'LAP_TIME_SEC' in self.lap_data.columns and 'LAP_NUMBER' in self.lap_data.columns:
            # Group by lap number and get average lap time
            lap_avg = self.lap_data.groupby('LAP_NUMBER')['LAP_TIME_SEC'].mean().reset_index()
            
            # Simple correlation: later laps might have different weather
            if len(lap_avg) > 1:
                # Assume weather changes linearly over race
                temp_trend = 'increasing' if weather_summary['max_temp'] > weather_summary['min_temp'] else 'decreasing'
                
                weather_summary['temperature_trend'] = temp_trend
                weather_summary['temperature_range'] = weather_summary['max_temp'] - weather_summary['min_temp']
        
        return weather_summary
    
    def get_weather_forecast_impact(self, forecast_temp: float, forecast_humidity: float) -> Dict:
        """Predict impact of forecasted weather on performance"""
        if self.weather_data.empty:
            return {}
        
        current_avg_temp = self.weather_data['AIR_TEMP'].mean() if 'AIR_TEMP' in self.weather_data.columns else np.nan
        current_avg_humidity = self.weather_data['HUMIDITY'].mean() if 'HUMIDITY' in self.weather_data.columns else np.nan
        
        if pd.isna(current_avg_temp) or pd.isna(current_avg_humidity):
            return {}
        
        temp_change = forecast_temp - current_avg_temp
        humidity_change = forecast_humidity - current_avg_humidity
        
        # Simple model: higher temp = slower times (air density), higher humidity = slower times
        # Rough estimate: 0.1s per degree C, 0.05s per 10% humidity
        estimated_lap_time_impact = (temp_change * 0.1) + (humidity_change / 10 * 0.05)
        
        return {
            'forecasted_temp': forecast_temp,
            'forecasted_humidity': forecast_humidity,
            'current_temp': current_avg_temp,
            'current_humidity': current_avg_humidity,
            'temp_change': temp_change,
            'humidity_change': humidity_change,
            'estimated_lap_time_impact': estimated_lap_time_impact,
            'impact_description': f"{'+' if estimated_lap_time_impact > 0 else ''}{estimated_lap_time_impact:.3f}s per lap"
        }
    
    def get_current_weather(self) -> Dict:
        """Get current weather conditions"""
        if self.weather_data.empty:
            return {}
        
        latest = self.weather_data.iloc[-1]
        
        return {
            'temperature': float(latest['AIR_TEMP']) if 'AIR_TEMP' in latest else np.nan,
            'track_temp': float(latest['TRACK_TEMP']) if 'TRACK_TEMP' in latest else np.nan,
            'humidity': float(latest['HUMIDITY']) if 'HUMIDITY' in latest else np.nan,
            'pressure': float(latest['PRESSURE']) if 'PRESSURE' in latest else np.nan,
            'wind_speed': float(latest['WIND_SPEED']) if 'WIND_SPEED' in latest else np.nan,
            'wind_direction': float(latest['WIND_DIRECTION']) if 'WIND_DIRECTION' in latest else np.nan,
            'rain': bool(latest['RAIN']) if 'RAIN' in latest else False,
            'timestamp': latest.get('TIME_UTC_STR', 'N/A')
        }

