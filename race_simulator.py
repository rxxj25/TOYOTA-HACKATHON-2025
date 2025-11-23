"""
Real-Time Race Simulation Engine
Simulates race progress using historical data for real-time analytics
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import time

class RaceSimulator:
    """Simulates race in real-time for analytics"""
    
    def __init__(self, lap_data: pd.DataFrame, results_data: pd.DataFrame):
        self.lap_data = lap_data
        self.results_data = results_data
        self.current_lap = 1
        self.simulation_start_time = None
        self.race_start_time = None
        self.speed_multiplier = 1.0  # For faster simulation
        
    def start_simulation(self, speed_multiplier: float = 60.0):
        """Start the race simulation"""
        self.speed_multiplier = speed_multiplier
        self.simulation_start_time = datetime.now()
        self.race_start_time = datetime.now()
        self.current_lap = 1
    
    def get_current_race_state(self) -> Dict:
        """Get current state of the race simulation"""
        if self.simulation_start_time is None:
            return {}
        
        elapsed_real = (datetime.now() - self.simulation_start_time).total_seconds()
        elapsed_race = elapsed_real * self.speed_multiplier
        
        # Calculate current lap based on average lap time
        if not self.lap_data.empty and 'LAP_TIME_SEC' in self.lap_data.columns:
            avg_lap_time = self.lap_data['LAP_TIME_SEC'].median()
            if pd.notna(avg_lap_time) and avg_lap_time > 0:
                self.current_lap = min(
                    int(elapsed_race / avg_lap_time) + 1,
                    int(self.lap_data['LAP_NUMBER'].max()) if 'LAP_NUMBER' in self.lap_data.columns else 50
                )
        
        # Get data for current lap
        current_lap_data = self.lap_data[
            self.lap_data['LAP_NUMBER'] == self.current_lap
        ].copy() if 'LAP_NUMBER' in self.lap_data.columns else pd.DataFrame()
        
        # Calculate positions
        positions = self._calculate_positions(current_lap_data)
        
        return {
            'current_lap': self.current_lap,
            'elapsed_time': elapsed_race,
            'elapsed_time_formatted': self._format_time(elapsed_race),
            'positions': positions,
            'lap_data': current_lap_data.to_dict('records') if not current_lap_data.empty else []
        }
    
    def _calculate_positions(self, lap_data: pd.DataFrame) -> List[Dict]:
        """Calculate current race positions"""
        if lap_data.empty:
            return []
        
        # Sort by lap time (best first)
        if 'LAP_TIME_SEC' in lap_data.columns:
            lap_data = lap_data.sort_values('LAP_TIME_SEC', na_position='last')
        
        positions = []
        for idx, row in lap_data.iterrows():
            positions.append({
                'position': len(positions) + 1,
                'number': int(row.get('NUMBER', 0)) if pd.notna(row.get('NUMBER')) else 0,
                'lap_time': row.get('LAP_TIME', 'N/A'),
                'lap_time_sec': row.get('LAP_TIME_SEC', np.nan),
                'kph': row.get('KPH', np.nan),
                's1': row.get('S1', 'N/A'),
                's2': row.get('S2', 'N/A'),
                's3': row.get('S3', 'N/A')
            })
        
        return positions
    
    def _format_time(self, seconds: float) -> str:
        """Format time in seconds to MM:SS.mmm"""
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}:{secs:06.3f}"
    
    def get_lap_history(self, driver_number: Optional[int] = None) -> pd.DataFrame:
        """Get lap history for a driver or all drivers"""
        if self.lap_data.empty:
            return pd.DataFrame()
        
        if driver_number:
            history = self.lap_data[
                (self.lap_data['NUMBER'] == driver_number) &
                (self.lap_data['LAP_NUMBER'] <= self.current_lap)
            ].copy()
        else:
            history = self.lap_data[
                self.lap_data['LAP_NUMBER'] <= self.current_lap
            ].copy()
        
        return history
    
    def get_driver_stats(self, driver_number: int) -> Dict:
        """Get statistics for a specific driver"""
        driver_data = self.lap_data[
            (self.lap_data['NUMBER'] == driver_number) &
            (self.lap_data['LAP_NUMBER'] <= self.current_lap)
        ].copy()
        
        if driver_data.empty:
            return {}
        
        stats = {
            'driver_number': driver_number,
            'laps_completed': len(driver_data),
            'best_lap': driver_data['LAP_TIME_SEC'].min() if 'LAP_TIME_SEC' in driver_data.columns else np.nan,
            'avg_lap': driver_data['LAP_TIME_SEC'].mean() if 'LAP_TIME_SEC' in driver_data.columns else np.nan,
            'last_lap': driver_data['LAP_TIME_SEC'].iloc[-1] if 'LAP_TIME_SEC' in driver_data.columns else np.nan,
            'avg_speed': driver_data['KPH'].mean() if 'KPH' in driver_data.columns else np.nan,
            'top_speed': driver_data['TOP_SPEED'].max() if 'TOP_SPEED' in driver_data.columns else np.nan
        }
        
        return stats

