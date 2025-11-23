"""
Pit Stop Strategy Calculator
Calculates optimal pit stop windows and tire degradation analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional

class StrategyCalculator:
    """Calculates optimal race strategies"""
    
    def __init__(self, lap_data: pd.DataFrame, weather_data: pd.DataFrame = None):
        self.lap_data = lap_data
        self.weather_data = weather_data
        self.pit_stop_time = 30.0  # Estimated pit stop time in seconds
        self.tire_life = 20  # Estimated laps before significant degradation
    
    def calculate_tire_degradation(self, driver_number: Optional[int] = None) -> pd.DataFrame:
        """Calculate tire degradation for a driver or all drivers"""
        if self.lap_data.empty:
            return pd.DataFrame()
        
        data = self.lap_data.copy()
        
        # Find NUMBER column (handle different formats)
        number_col = None
        for col in ['NUMBER', 'DRIVER_NUMBER']:
            if col in data.columns:
                number_col = col
                break
        
        if number_col is None:
            return pd.DataFrame()
        
        if driver_number:
            data = data[data[number_col] == driver_number].copy()
        
        if 'LAP_TIME_SEC' not in data.columns or 'LAP_NUMBER' not in data.columns:
            return pd.DataFrame()
        
        # Calculate degradation (lap time increase over race)
        degradation_data = []
        
        for number in data[number_col].dropna().unique():
            driver_laps = data[data[number_col] == number].sort_values('LAP_NUMBER')
            
            # Filter out rows with invalid lap times
            driver_laps = driver_laps[driver_laps['LAP_TIME_SEC'].notna()]
            
            if len(driver_laps) < 3:
                continue
            
            # Use first 5 valid laps as baseline, or all if less than 5
            baseline_laps = driver_laps['LAP_TIME_SEC'].iloc[:min(5, len(driver_laps))]
            baseline_lap = baseline_laps.median()
            
            if pd.isna(baseline_lap) or baseline_lap <= 0:
                continue
            
            for idx, row in driver_laps.iterrows():
                lap_time = row['LAP_TIME_SEC']
                if pd.notna(lap_time) and lap_time > 0:
                    degradation = lap_time - baseline_lap
                    degradation_pct = (degradation / baseline_lap) * 100
                    
                    degradation_data.append({
                        'NUMBER': number,
                        'LAP_NUMBER': row['LAP_NUMBER'],
                        'LAP_TIME': lap_time,
                        'BASELINE': baseline_lap,
                        'DEGRADATION': degradation,
                        'DEGRADATION_PCT': degradation_pct,
                        'TIRE_AGE': row['LAP_NUMBER']  # Assuming no pit stops for now
                    })
        
        return pd.DataFrame(degradation_data)
    
    def recommend_pit_window(self, driver_number: int, current_lap: int, 
                            total_laps: int = 30) -> Dict:
        """Recommend optimal pit stop window"""
        degradation = self.calculate_tire_degradation(driver_number)
        
        if degradation.empty:
            return {
                'recommended_lap': current_lap + 10,
                'reason': 'Insufficient data',
                'urgency': 'low'
            }
        
        driver_degradation = degradation[degradation['NUMBER'] == driver_number]
        
        if driver_degradation.empty:
            return {
                'recommended_lap': current_lap + 10,
                'reason': 'No degradation data',
                'urgency': 'low'
            }
        
        # Find when degradation exceeds threshold (2% slower)
        threshold = 2.0  # 2% degradation
        critical_laps = driver_degradation[
            driver_degradation['DEGRADATION_PCT'] > threshold
        ]
        
        if not critical_laps.empty:
            critical_lap = critical_laps['LAP_NUMBER'].min()
            recommended_lap = max(current_lap, critical_lap - 2)  # Pit 2 laps before critical
            
            urgency = 'high' if critical_lap - current_lap <= 3 else 'medium'
            
            return {
                'recommended_lap': int(recommended_lap),
                'critical_lap': int(critical_lap),
                'current_degradation': float(driver_degradation['DEGRADATION_PCT'].iloc[-1]) if len(driver_degradation) > 0 else 0,
                'reason': f'Tire degradation at {threshold}% threshold',
                'urgency': urgency,
                'laps_remaining': int(critical_lap - current_lap)
            }
        
        # Default recommendation
        optimal_lap = min(current_lap + self.tire_life, total_laps // 2)
        
        return {
            'recommended_lap': int(optimal_lap),
            'reason': 'Optimal tire life window',
            'urgency': 'low',
            'laps_remaining': int(optimal_lap - current_lap)
        }
    
    def calculate_undercut_overtake(self, driver_number: int, target_position: int,
                                   current_lap: int) -> Dict:
        """Calculate if undercut strategy can gain position"""
        if self.lap_data.empty:
            return {'feasible': False, 'reason': 'No data'}
        
        # Get current positions
        current_lap_data = self.lap_data[
            self.lap_data['LAP_NUMBER'] == current_lap
        ].copy()
        
        if current_lap_data.empty:
            return {'feasible': False, 'reason': 'No current lap data'}
        
        # Sort by lap time
        if 'LAP_TIME_SEC' in current_lap_data.columns:
            current_lap_data = current_lap_data.sort_values('LAP_TIME_SEC')
            current_lap_data['position'] = range(1, len(current_lap_data) + 1)
        
        driver_pos = current_lap_data[
            current_lap_data['NUMBER'] == driver_number
        ]
        
        if driver_pos.empty:
            return {'feasible': False, 'reason': 'Driver not found'}
        
        current_pos = driver_pos['position'].iloc[0]
        
        if current_pos <= target_position:
            return {'feasible': False, 'reason': 'Already at or ahead of target'}
        
        # Calculate gap to target
        target_driver = current_lap_data[
            current_lap_data['position'] == target_position
        ]
        
        if target_driver.empty:
            return {'feasible': False, 'reason': 'Target position not found'}
        
        gap = driver_pos['LAP_TIME_SEC'].iloc[0] - target_driver['LAP_TIME_SEC'].iloc[0]
        
        # Estimate if undercut can work (pit 1 lap early, gain time on fresh tires)
        fresh_tire_gain = 0.5  # Estimated 0.5s gain per lap on fresh tires
        undercut_laps = 2  # Laps to gain advantage
        
        potential_gain = fresh_tire_gain * undercut_laps
        
        feasible = potential_gain > gap + self.pit_stop_time
        
        return {
            'feasible': feasible,
            'current_position': int(current_pos),
            'target_position': target_position,
            'gap_to_target': float(gap),
            'potential_gain': potential_gain,
            'net_advantage': potential_gain - gap - self.pit_stop_time,
            'recommendation': 'Pit now for undercut' if feasible else 'Stay out, gap too large'
        }
    
    def get_strategy_summary(self, driver_number: int, current_lap: int) -> Dict:
        """Get comprehensive strategy summary"""
        pit_recommendation = self.recommend_pit_window(driver_number, current_lap)
        degradation = self.calculate_tire_degradation(driver_number)
        
        driver_degradation = degradation[
            degradation['NUMBER'] == driver_number
        ] if not degradation.empty else pd.DataFrame()
        
        strategy = {
            'pit_recommendation': pit_recommendation,
            'tire_degradation': {
                'current': float(driver_degradation['DEGRADATION_PCT'].iloc[-1]) if len(driver_degradation) > 0 else 0,
                'trend': 'increasing' if len(driver_degradation) > 1 and 
                        driver_degradation['DEGRADATION_PCT'].iloc[-1] > driver_degradation['DEGRADATION_PCT'].iloc[0] else 'stable'
            } if not driver_degradation.empty else {'current': 0, 'trend': 'unknown'}
        }
        
        return strategy

