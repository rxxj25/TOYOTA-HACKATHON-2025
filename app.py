"""
GR Cup Real-Time Analytics Dashboard
Main Streamlit application for race engineers
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import time

from data_processor import RaceDataProcessor
from race_simulator import RaceSimulator
from strategy_calculator import StrategyCalculator
from weather_analyzer import WeatherAnalyzer

# Page configuration
st.set_page_config(
    page_title="GR Cup Real-Time Analytics",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #E50914;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #1e1e1e;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #333;
    }
    .stAlert {
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'simulator' not in st.session_state:
    st.session_state.simulator = None
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'simulation_running' not in st.session_state:
    st.session_state.simulation_running = False

@st.cache_data
def load_race_data(track, race):
    """Load and cache race data"""
    processor = RaceDataProcessor()
    
    results = processor.load_results(track, race)
    lap_times = processor.load_lap_times(track, race)
    weather = processor.load_weather(track, race)
    best_laps = processor.load_best_laps(track, race)
    
    # Process lap data
    if not lap_times.empty:
        lap_times = processor.process_lap_data(lap_times)
    
    return {
        'results': results,
        'lap_times': lap_times,
        'weather': weather,
        'best_laps': best_laps,
        'processor': processor
    }

def main():
    # Header
    st.markdown('<h1 class="main-header">🏎️ GR Cup Real-Time Analytics Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("### Professional Race Engineering Tool for Strategy & Performance Analysis")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        processor = RaceDataProcessor()
        tracks = processor.get_available_tracks()
        
        track = st.selectbox(
            "Select Track",
            tracks,
            format_func=lambda x: processor.get_track_display_name(x)
        )
        
        race = st.selectbox("Select Race", [1, 2])
        
        if st.button("📊 Load Race Data", type="primary"):
            with st.spinner("Loading race data..."):
                data = load_race_data(track, race)
                st.session_state.race_data = data
                st.session_state.data_loaded = True
                st.success("Data loaded successfully!")
        
        st.divider()
        
        if st.session_state.data_loaded:
            st.header("🎮 Simulation Controls")
            
            speed_multiplier = st.slider(
                "Simulation Speed (x)",
                min_value=1,
                max_value=300,
                value=60,
                help="How many times faster than real-time"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("▶️ Start Simulation"):
                    if st.session_state.race_data:
                        lap_data = st.session_state.race_data['lap_times']
                        results_data = st.session_state.race_data['results']
                        
                        if not lap_data.empty:
                            st.session_state.simulator = RaceSimulator(lap_data, results_data)
                            st.session_state.simulator.start_simulation(speed_multiplier)
                            st.session_state.simulation_running = True
                            st.rerun()
            
            with col2:
                if st.button("⏸️ Stop Simulation"):
                    st.session_state.simulation_running = False
                    st.rerun()
    
    # Main content
    if not st.session_state.data_loaded:
        st.info("👈 Please load race data from the sidebar to begin")
        st.markdown("""
        ### Welcome to GR Cup Real-Time Analytics
        
        This dashboard provides:
        - **Real-Time Race Simulation**: Watch the race unfold with live position updates
        - **Pit Stop Strategy**: Get optimal pit window recommendations
        - **Tire Degradation Analysis**: Monitor tire performance over the race
        - **Weather Impact**: Understand how conditions affect performance
        - **Driver Insights**: Detailed performance metrics for each driver
        
        Select a track and race from the sidebar to get started!
        """)
        return
    
    data = st.session_state.race_data
    lap_data = data['lap_times']
    results_data = data['results']
    weather_data = data['weather']
    
    # Debug information (collapsible)
    with st.expander("🔍 Debug: Data Status", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"**Lap Data**: {'✅ Loaded' if not lap_data.empty else '❌ Empty'}")
            if not lap_data.empty:
                st.write(f"Rows: {len(lap_data)}, Columns: {len(lap_data.columns)}")
                st.write(f"Drivers: {len(lap_data['NUMBER'].unique()) if 'NUMBER' in lap_data.columns else 'N/A'}")
        with col2:
            st.write(f"**Results Data**: {'✅ Loaded' if not results_data.empty else '❌ Empty'}")
            if not results_data.empty:
                st.write(f"Rows: {len(results_data)}, Columns: {len(results_data.columns)}")
        with col3:
            st.write(f"**Weather Data**: {'✅ Loaded' if not weather_data.empty else '❌ Empty'}")
            if not weather_data.empty:
                st.write(f"Rows: {len(weather_data)}, Columns: {len(weather_data.columns)}")
        
        if not lap_data.empty:
            st.write("**Lap Data Columns:**")
            st.write(", ".join(lap_data.columns[:15].tolist()))
            if 'LAP_TIME_SEC' in lap_data.columns:
                st.success("✅ LAP_TIME_SEC column found")
            else:
                st.warning("⚠️ LAP_TIME_SEC column missing - data may not be processed correctly")
    
    if lap_data.empty:
        st.error("No lap time data available for this race")
        st.info("💡 Try selecting a different track or race from the sidebar")
        return
    
    # Tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Real-Time Race", 
        "🎯 Strategy", 
        "🛞 Tire Analysis", 
        "🌤️ Weather", 
        "👤 Driver Insights"
    ])
    
    with tab1:
        st.header("Real-Time Race Monitor")
        
        if st.session_state.simulation_running and st.session_state.simulator:
            # Auto-refresh for real-time feel
            placeholder = st.empty()
            
            with placeholder.container():
                state = st.session_state.simulator.get_current_race_state()
                
                # Key metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Current Lap", state.get('current_lap', 0))
                with col2:
                    st.metric("Elapsed Time", state.get('elapsed_time_formatted', '0:00.000'))
                with col3:
                    st.metric("Cars on Track", len(state.get('positions', [])))
                with col4:
                    if state.get('positions'):
                        leader = state['positions'][0]
                        st.metric("Leader", f"#{leader['number']}")
                
                # Live positions table
                if state.get('positions'):
                    st.subheader("🏁 Current Positions")
                    positions_df = pd.DataFrame(state['positions'])
                    st.dataframe(
                        positions_df[['position', 'number', 'lap_time', 'kph', 's1', 's2', 's3']],
                        use_container_width=True,
                        hide_index=True
                    )
                
                # Position chart
                if len(state.get('positions', [])) > 0:
                    top_10 = positions_df.head(10).copy()
                    if 'lap_time_sec' in top_10.columns and not top_10['lap_time_sec'].isna().all():
                        fig = px.bar(
                            top_10,
                            x='number',
                            y='lap_time_sec',
                            title="Top 10 - Current Lap Times",
                            labels={'number': 'Car Number', 'lap_time_sec': 'Lap Time (seconds)'},
                            color='lap_time_sec',
                            color_continuous_scale='RdYlGn_r'
                        )
                        fig.update_layout(height=400)
                        st.plotly_chart(fig, use_container_width=True)
            
            # Auto-refresh
            time.sleep(0.5)
            st.rerun()
        else:
            st.info("Click 'Start Simulation' in the sidebar to begin real-time monitoring")
            
            # Show static data preview
            st.subheader("Race Overview")
            if not results_data.empty:
                # Clean column names for display
                display_results = results_data.head(20).copy()
                # Select key columns if available
                key_cols = ['POSITION', 'NUMBER', 'LAPS', 'TOTAL_TIME', 'GAP_FIRST', 'FL_TIME']
                available_cols = [col for col in key_cols if col in display_results.columns]
                if available_cols:
                    st.dataframe(display_results[available_cols], use_container_width=True)
                else:
                    st.dataframe(display_results, use_container_width=True)
    
    with tab2:
        st.header("🎯 Strategy & Pit Stop Calculator")
        
        # Get driver numbers - handle different column name formats
        driver_col = None
        for col in ['NUMBER', ' NUMBER', 'DRIVER_NUMBER', 'DRIVER NUMBER']:
            if col in lap_data.columns:
                driver_col = col
                break
        
        if driver_col is None or lap_data.empty:
            st.warning("⚠️ No driver data available. Please load race data first.")
            if not lap_data.empty:
                st.info(f"Available columns: {', '.join(lap_data.columns[:10])}")
        else:
            # Get unique driver numbers and convert to int, handling any data type issues
            unique_drivers = lap_data[driver_col].dropna().unique()
            driver_numbers = []
            for x in unique_drivers:
                try:
                    num = int(float(x))  # Convert to float first to handle string numbers
                    if num not in driver_numbers:
                        driver_numbers.append(num)
                except (ValueError, TypeError):
                    continue
            driver_numbers = sorted(driver_numbers)
            
            if st.session_state.simulation_running and st.session_state.simulator:
                current_lap = st.session_state.simulator.current_lap
            else:
                current_lap = st.number_input("Current Lap", min_value=1, max_value=50, value=5)
            
            driver_number = st.selectbox(
                "Select Driver",
                driver_numbers if driver_numbers else []
            )
            
            if driver_number and driver_numbers:
                try:
                    calculator = StrategyCalculator(lap_data, weather_data)
                    
                    # Pit stop recommendation
                    st.subheader("🛑 Pit Stop Recommendation")
                    recommendation = calculator.recommend_pit_window(driver_number, int(current_lap))
                    
                    urgency_colors = {
                        'high': '🔴',
                        'medium': '🟡',
                        'low': '🟢'
                    }
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(
                            "Recommended Pit Lap",
                            recommendation.get('recommended_lap', 'N/A'),
                            delta=f"Lap {recommendation.get('laps_remaining', 0)} away"
                        )
                    with col2:
                        urgency = recommendation.get('urgency', 'low')
                        st.metric("Urgency", f"{urgency_colors.get(urgency, '⚪')} {urgency.upper()}")
                    with col3:
                        st.metric(
                            "Current Degradation",
                            f"{recommendation.get('current_degradation', 0):.2f}%"
                        )
                    
                    st.info(f"💡 **Reason**: {recommendation.get('reason', 'N/A')}")
                    
                    # Undercut calculator
                    st.subheader("⚡ Undercut Overtake Calculator")
                    target_pos = st.number_input("Target Position", min_value=1, max_value=30, value=1)
                    
                    if st.button("Calculate Undercut"):
                        undercut = calculator.calculate_undercut_overtake(
                            driver_number, target_pos, int(current_lap)
                        )
                        
                        if undercut.get('feasible'):
                            st.success(f"✅ **Feasible!** {undercut.get('recommendation', '')}")
                            st.metric("Net Advantage", f"{undercut.get('net_advantage', 0):.3f}s")
                        else:
                            st.warning(f"❌ **Not Feasible**: {undercut.get('reason', '')}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Current Position", undercut.get('current_position', 'N/A'))
                            st.metric("Gap to Target", f"{undercut.get('gap_to_target', 0):.3f}s")
                        with col2:
                            st.metric("Target Position", target_pos)
                            st.metric("Potential Gain", f"{undercut.get('potential_gain', 0):.3f}s")
                except Exception as e:
                    st.error(f"Error calculating strategy: {str(e)}")
                    st.info("Please ensure lap time data is loaded correctly.")
    
    with tab3:
        st.header("🛞 Tire Degradation Analysis")
        
        # Get driver numbers - handle different column name formats
        driver_col = None
        for col in ['NUMBER', ' NUMBER', 'DRIVER_NUMBER', 'DRIVER NUMBER']:
            if col in lap_data.columns:
                driver_col = col
                break
        
        if driver_col is None or lap_data.empty:
            st.warning("⚠️ No driver data available. Please load race data first.")
        else:
            # Get unique driver numbers and convert to int, handling any data type issues
            unique_drivers = lap_data[driver_col].dropna().unique()
            driver_numbers = []
            for x in unique_drivers:
                try:
                    num = int(float(x))  # Convert to float first to handle string numbers
                    if num not in driver_numbers:
                        driver_numbers.append(num)
                except (ValueError, TypeError):
                    continue
            driver_numbers = sorted(driver_numbers)
            
            driver_number = st.selectbox(
                "Select Driver for Analysis",
                driver_numbers if driver_numbers else [],
                key="tire_driver"
            )
            
            if driver_number and driver_numbers:
                try:
                    calculator = StrategyCalculator(lap_data, weather_data)
                    degradation = calculator.calculate_tire_degradation(driver_number)
                    
                    if not degradation.empty:
                        driver_degradation = degradation[degradation['NUMBER'] == driver_number]
                        
                        if not driver_degradation.empty:
                            # Degradation chart
                            fig = px.line(
                                driver_degradation,
                                x='LAP_NUMBER',
                                y='DEGRADATION_PCT',
                                title=f"Tire Degradation - Driver #{driver_number}",
                                labels={'LAP_NUMBER': 'Lap Number', 'DEGRADATION_PCT': 'Degradation (%)'},
                                markers=True
                            )
                            fig.add_hline(y=2.0, line_dash="dash", line_color="red", 
                                        annotation_text="Critical Threshold (2%)")
                            fig.update_layout(height=400)
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Lap time progression
                            fig2 = px.line(
                                driver_degradation,
                                x='LAP_NUMBER',
                                y='LAP_TIME',
                                title=f"Lap Time Progression - Driver #{driver_number}",
                                labels={'LAP_NUMBER': 'Lap Number', 'LAP_TIME': 'Lap Time (seconds)'},
                                markers=True
                            )
                            fig2.update_layout(height=400)
                            st.plotly_chart(fig2, use_container_width=True)
                            
                            # Summary stats
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Max Degradation", f"{driver_degradation['DEGRADATION_PCT'].max():.2f}%")
                            with col2:
                                st.metric("Avg Degradation", f"{driver_degradation['DEGRADATION_PCT'].mean():.2f}%")
                            with col3:
                                st.metric("Laps Analyzed", len(driver_degradation))
                            with col4:
                                critical_laps = len(driver_degradation[driver_degradation['DEGRADATION_PCT'] > 2.0])
                                st.metric("Critical Laps", critical_laps)
                        else:
                            st.warning("No degradation data calculated for this driver")
                    else:
                        st.warning("⚠️ No degradation data available. This may be due to:")
                        st.info("• Insufficient lap data (need at least 3 laps)\n• Missing LAP_TIME_SEC column\n• Data processing issues")
                        if not lap_data.empty:
                            st.info(f"Available columns: {', '.join([c for c in lap_data.columns if 'LAP' in c.upper() or 'TIME' in c.upper()][:10])}")
                except Exception as e:
                    st.error(f"Error calculating tire degradation: {str(e)}")
                    import traceback
                    with st.expander("Error Details"):
                        st.code(traceback.format_exc())
    
    with tab4:
        st.header("🌤️ Weather Impact Analysis")
        
        if not weather_data.empty:
            try:
                analyzer = WeatherAnalyzer(weather_data, lap_data)
                
                # Current weather
                st.subheader("Current Conditions")
                current_weather = analyzer.get_current_weather()
                
                if current_weather:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        temp = current_weather.get('temperature', np.nan)
                        track_temp = current_weather.get('track_temp', np.nan)
                        st.metric("Temperature", f"{temp:.1f}°C" if pd.notna(temp) else "N/A")
                        st.metric("Track Temp", f"{track_temp:.1f}°C" if pd.notna(track_temp) else "N/A")
                    with col2:
                        humidity = current_weather.get('humidity', np.nan)
                        pressure = current_weather.get('pressure', np.nan)
                        st.metric("Humidity", f"{humidity:.1f}%" if pd.notna(humidity) else "N/A")
                        st.metric("Pressure", f"{pressure:.1f} hPa" if pd.notna(pressure) else "N/A")
                    with col3:
                        wind_speed = current_weather.get('wind_speed', np.nan)
                        wind_dir = current_weather.get('wind_direction', np.nan)
                        st.metric("Wind Speed", f"{wind_speed:.1f} km/h" if pd.notna(wind_speed) else "N/A")
                        st.metric("Wind Direction", f"{wind_dir:.0f}°" if pd.notna(wind_dir) else "N/A")
                    with col4:
                        rain_status = "🌧️ Yes" if current_weather.get('rain', False) else "☀️ No"
                        st.metric("Rain", rain_status)
                        timestamp = current_weather.get('timestamp', 'N/A')
                        st.caption(f"Last Update: {timestamp}")
                else:
                    st.warning("Could not retrieve current weather data")
                
                # Weather trends
                st.subheader("Weather Trends")
                temp_col = None
                for col in ['AIR_TEMP', 'AIR TEMP', 'TEMPERATURE']:
                    if col in weather_data.columns:
                        temp_col = col
                        break
                
                if temp_col:
                    valid_temp = weather_data[weather_data[temp_col].notna()]
                    if not valid_temp.empty:
                        fig = px.line(
                            valid_temp,
                            x=valid_temp.index,
                            y=temp_col,
                            title="Temperature Over Race",
                            labels={'index': 'Time', temp_col: 'Temperature (°C)'}
                        )
                        fig.update_layout(height=300)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("No valid temperature data for chart")
                else:
                    st.info("Temperature column not found in weather data")
                
                # Weather impact summary
                st.subheader("Weather Impact Summary")
                impact = analyzer.analyze_weather_impact()
                
                if impact:
                    col1, col2 = st.columns(2)
                    with col1:
                        avg_temp = impact.get('avg_temp', np.nan)
                        temp_range = impact.get('temperature_range', np.nan)
                        st.metric("Avg Temperature", f"{avg_temp:.1f}°C" if pd.notna(avg_temp) else "N/A")
                        st.metric("Temperature Range", f"{temp_range:.1f}°C" if pd.notna(temp_range) else "N/A")
                    with col2:
                        avg_humidity = impact.get('avg_humidity', np.nan)
                        st.metric("Avg Humidity", f"{avg_humidity:.1f}%" if pd.notna(avg_humidity) else "N/A")
                        st.metric("Rain Occurred", "Yes" if impact.get('rain_occurred') else "No")
                else:
                    st.info("Weather impact analysis not available")
                
                # Forecast impact calculator
                st.subheader("Forecast Impact Calculator")
                col1, col2 = st.columns(2)
                with col1:
                    forecast_temp = st.number_input("Forecasted Temperature (°C)", value=25.0, min_value=-50.0, max_value=60.0)
                with col2:
                    forecast_humidity = st.number_input("Forecasted Humidity (%)", value=50.0, min_value=0.0, max_value=100.0)
                
                if st.button("Calculate Forecast Impact"):
                    forecast_impact = analyzer.get_weather_forecast_impact(
                        forecast_temp, forecast_humidity
                    )
                    
                    if forecast_impact:
                        st.info(f"**Estimated Impact**: {forecast_impact.get('impact_description', 'N/A')}")
                        col1, col2 = st.columns(2)
                        with col1:
                            temp_change = forecast_impact.get('temp_change', 0)
                            st.metric("Temp Change", f"{temp_change:.1f}°C")
                        with col2:
                            humidity_change = forecast_impact.get('humidity_change', 0)
                            st.metric("Humidity Change", f"{humidity_change:.1f}%")
                    else:
                        st.warning("Could not calculate forecast impact")
            except Exception as e:
                st.error(f"Error analyzing weather data: {str(e)}")
                import traceback
                with st.expander("Error Details"):
                    st.code(traceback.format_exc())
        else:
            st.warning("⚠️ No weather data available for this race")
            st.info("Weather data may not be available for all races. Try selecting a different race.")
    
    with tab5:
        st.header("👤 Driver Performance Insights")
        
        # Get driver numbers - handle different column name formats
        driver_col = None
        for col in ['NUMBER', ' NUMBER', 'DRIVER_NUMBER', 'DRIVER NUMBER']:
            if col in lap_data.columns:
                driver_col = col
                break
        
        if driver_col is None or lap_data.empty:
            st.warning("⚠️ No driver data available. Please load race data first.")
        else:
            # Get unique driver numbers and convert to int, handling any data type issues
            unique_drivers = lap_data[driver_col].dropna().unique()
            driver_numbers = []
            for x in unique_drivers:
                try:
                    num = int(float(x))  # Convert to float first to handle string numbers
                    if num not in driver_numbers:
                        driver_numbers.append(num)
                except (ValueError, TypeError):
                    continue
            driver_numbers = sorted(driver_numbers)
            
            driver_number = st.selectbox(
                "Select Driver",
                driver_numbers if driver_numbers else [],
                key="insights_driver"
            )
            
            if driver_number and driver_numbers:
                try:
                    # Ensure proper type matching for filtering
                    # Convert driver_col to numeric for comparison
                    lap_data_filtered = lap_data.copy()
                    lap_data_filtered[driver_col] = pd.to_numeric(lap_data_filtered[driver_col], errors='coerce')
                    
                    # Filter by driver number
                    driver_data = lap_data_filtered[lap_data_filtered[driver_col] == float(driver_number)].copy()
                    
                    # Debug info (can be removed later)
                    if st.session_state.get('show_debug', False):
                        with st.expander("Debug: Driver Filtering"):
                            st.write(f"Selected driver: {driver_number}")
                            st.write(f"Driver column: {driver_col}")
                            st.write(f"Rows before filter: {len(lap_data)}")
                            st.write(f"Rows after filter: {len(driver_data)}")
                            st.write(f"Unique drivers in filtered data: {driver_data[driver_col].unique() if not driver_data.empty else 'None'}")
                    
                    if not driver_data.empty:
                        # Verify we have the right driver's data
                        actual_drivers = driver_data[driver_col].unique()
                        if len(actual_drivers) > 1 or (len(actual_drivers) == 1 and actual_drivers[0] != driver_number):
                            st.warning(f"⚠️ Warning: Data shows drivers {actual_drivers}, but selected driver is {driver_number}")
                        
                        # Driver stats
                        st.subheader(f"Driver #{driver_number} Statistics")
                        st.caption(f"Showing {len(driver_data)} lap(s) of data")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            best_lap = driver_data['LAP_TIME_SEC'].min() if 'LAP_TIME_SEC' in driver_data.columns else np.nan
                            st.metric("Best Lap", f"{best_lap:.3f}s" if pd.notna(best_lap) else "N/A")
                        with col2:
                            avg_lap = driver_data['LAP_TIME_SEC'].mean() if 'LAP_TIME_SEC' in driver_data.columns else np.nan
                            st.metric("Average Lap", f"{avg_lap:.3f}s" if pd.notna(avg_lap) else "N/A")
                        with col3:
                            avg_speed = driver_data['KPH'].mean() if 'KPH' in driver_data.columns else np.nan
                            st.metric("Avg Speed", f"{avg_speed:.1f} km/h" if pd.notna(avg_speed) else "N/A")
                        with col4:
                            top_speed = driver_data['TOP_SPEED'].max() if 'TOP_SPEED' in driver_data.columns else np.nan
                            st.metric("Top Speed", f"{top_speed:.1f} km/h" if pd.notna(top_speed) else "N/A")
                        
                        # Lap time progression
                        if 'LAP_NUMBER' in driver_data.columns and 'LAP_TIME_SEC' in driver_data.columns:
                            st.subheader("Lap Time Progression")
                            driver_sorted = driver_data.sort_values('LAP_NUMBER')
                            valid_data = driver_sorted[driver_sorted['LAP_TIME_SEC'].notna()]
                            
                            if not valid_data.empty:
                                fig = px.line(
                                    valid_data,
                                    x='LAP_NUMBER',
                                    y='LAP_TIME_SEC',
                                    title=f"Lap Times - Driver #{driver_number}",
                                    labels={'LAP_NUMBER': 'Lap Number', 'LAP_TIME_SEC': 'Lap Time (seconds)'},
                                    markers=True
                                )
                                if pd.notna(best_lap):
                                    fig.add_hline(y=best_lap, line_dash="dash", line_color="green", 
                                                annotation_text=f"Best: {best_lap:.3f}s")
                                if pd.notna(avg_lap):
                                    fig.add_hline(y=avg_lap, line_dash="dash", line_color="orange", 
                                                annotation_text=f"Avg: {avg_lap:.3f}s")
                                fig.update_layout(height=400)
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.warning("No valid lap time data for visualization")
                        
                        # Section analysis - check for both S1_SEC and S1_SECONDS
                        section_cols = []
                        for sec in ['S1', 'S2', 'S3']:
                            if f'{sec}_SEC' in driver_data.columns:
                                section_cols.append(f'{sec}_SEC')
                            elif f'{sec}_SECONDS' in driver_data.columns:
                                section_cols.append(f'{sec}_SECONDS')
                        
                        if len(section_cols) == 3:
                            st.subheader("Section Performance")
                            
                            sections = pd.DataFrame({
                                'Section': ['S1', 'S2', 'S3'],
                                'Best': [
                                    driver_data[section_cols[0]].min(),
                                    driver_data[section_cols[1]].min(),
                                    driver_data[section_cols[2]].min()
                                ],
                                'Average': [
                                    driver_data[section_cols[0]].mean(),
                                    driver_data[section_cols[1]].mean(),
                                    driver_data[section_cols[2]].mean()
                                ]
                            })
                            
                            fig = px.bar(
                                sections,
                                x='Section',
                                y=['Best', 'Average'],
                                title=f"Section Times - Driver #{driver_number}",
                                barmode='group'
                            )
                            fig.update_layout(height=300)
                            st.plotly_chart(fig, use_container_width=True)
                        elif len(section_cols) > 0:
                            st.info(f"Partial section data available. Found: {section_cols}")
                        
                        # Speed analysis
                        if 'KPH' in driver_data.columns and 'LAP_NUMBER' in driver_data.columns:
                            st.subheader("Speed Analysis")
                            driver_sorted = driver_data.sort_values('LAP_NUMBER')
                            valid_speed = driver_sorted[driver_sorted['KPH'].notna()]
                            
                            if not valid_speed.empty:
                                fig = px.line(
                                    valid_speed,
                                    x='LAP_NUMBER',
                                    y='KPH',
                                    title=f"Average Speed per Lap - Driver #{driver_number}",
                                    labels={'LAP_NUMBER': 'Lap Number', 'KPH': 'Speed (km/h)'}
                                )
                                fig.update_layout(height=300)
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.warning("No valid speed data for visualization")
                    else:
                        st.warning(f"No data found for driver #{driver_number}")
                except Exception as e:
                    st.error(f"Error loading driver insights: {str(e)}")
                    import traceback
                    with st.expander("Error Details"):
                        st.code(traceback.format_exc())

if __name__ == "__main__":
    main()

