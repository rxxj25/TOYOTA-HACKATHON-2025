"""
Data Processing Module for GR Cup Race Analytics
Handles loading and preprocessing of race data from multiple sources
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import re

class RaceDataProcessor:
    """Processes and loads race data from CSV files"""
    
    def __init__(self, data_root: str = "."):
        self.data_root = Path(data_root)
        self.tracks = {
            'barber': 'barber',
            'circuit-of-the-americas': 'circuit-of-the-americas/COTA',
            'indianapolis': 'indianapolis/indianapolis',
            'road-america': 'road-america/Road America',
            'sebring': 'sebring/Sebring',
            'sonoma': 'sonoma/Sonoma',
            'virginia-international-raceway': 'virginia-international-raceway/VIR'
        }
    
    def load_results(self, track: str, race: int) -> pd.DataFrame:
        """Load race results data"""
        track_path = self.data_root / self.tracks[track]
        race_folder = f"Race {race}"
        
        # Try different result file patterns
        patterns = [
            f"03_Provisional Results_Race {race}_Anonymized.CSV",
            f"03_Provisional Results_Race {race}.CSV",
            f"03_GR Cup Race {race} Official Results.CSV",
            f"00_Results GR Cup Race {race} Official_Anonymized.CSV"
        ]
        
        for pattern in patterns:
            file_path = track_path / race_folder / pattern
            if not file_path.exists():
                # Try without race folder
                file_path = track_path / pattern
            if file_path.exists():
                try:
                    df = pd.read_csv(file_path, sep=';', encoding='utf-8')
                    return df
                except:
                    try:
                        df = pd.read_csv(file_path, sep=',', encoding='utf-8')
                        return df
                    except Exception as e:
                        continue
        
        # Fallback: try barber format (no race folder)
        if track == 'barber':
            pattern = f"03_Provisional Results_Race {race}_Anonymized.CSV"
            file_path = track_path / pattern
            if file_path.exists():
                return pd.read_csv(file_path, sep=';', encoding='utf-8')
        
        return pd.DataFrame()
    
    def load_lap_times(self, track: str, race: int) -> pd.DataFrame:
        """Load detailed lap time data"""
        track_path = self.data_root / self.tracks[track]
        race_folder = f"Race {race}"
        
        # Try different lap time file patterns
        patterns = [
            f"23_AnalysisEnduranceWithSections_Race {race}_Anonymized.CSV",
            f"23_AnalysisEnduranceWithSections_Race {race}.CSV"
        ]
        
        for pattern in patterns:
            file_path = track_path / race_folder / pattern
            if not file_path.exists():
                file_path = track_path / pattern
            
            if file_path.exists():
                try:
                    df = pd.read_csv(file_path, sep=';', encoding='utf-8', low_memory=False)
                    # Clean column names
                    df.columns = df.columns.str.strip()
                    return df
                except Exception as e:
                    continue
        
        return pd.DataFrame()
    
    def load_weather(self, track: str, race: int) -> pd.DataFrame:
        """Load weather data"""
        track_path = self.data_root / self.tracks[track]
        race_folder = f"Race {race}"
        
        patterns = [
            f"26_Weather_Race {race}_Anonymized.CSV",
            f"26_Weather_Race {race}.CSV"
        ]
        
        for pattern in patterns:
            file_path = track_path / race_folder / pattern
            if not file_path.exists():
                file_path = track_path / pattern
            
            if file_path.exists():
                try:
                    df = pd.read_csv(file_path, sep=';', encoding='utf-8')
                    return df
                except:
                    try:
                        df = pd.read_csv(file_path, sep=',', encoding='utf-8')
                        return df
                    except:
                        continue
        
        return pd.DataFrame()
    
    def load_best_laps(self, track: str, race: int) -> pd.DataFrame:
        """Load best lap times by driver"""
        track_path = self.data_root / self.tracks[track]
        race_folder = f"Race {race}"
        
        patterns = [
            f"99_Best 10 Laps By Driver_Race {race}_Anonymized.CSV",
            f"99_Best 10 Laps By Driver_Race {race}.CSV"
        ]
        
        for pattern in patterns:
            file_path = track_path / race_folder / pattern
            if not file_path.exists():
                file_path = track_path / pattern
            
            if file_path.exists():
                try:
                    df = pd.read_csv(file_path, sep=';', encoding='utf-8')
                    return df
                except:
                    continue
        
        return pd.DataFrame()
    
    def parse_lap_time(self, time_str: str) -> float:
        """Convert lap time string (MM:SS.mmm) to seconds"""
        if pd.isna(time_str) or time_str == '':
            return np.nan
        
        try:
            # Handle format like "1:39.167" or "1:39:167"
            parts = str(time_str).split(':')
            if len(parts) == 2:
                minutes = float(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
            elif len(parts) == 3:
                minutes = float(parts[0])
                seconds = float(parts[1])
                milliseconds = float(parts[2]) / 1000
                return minutes * 60 + seconds + milliseconds
            else:
                return float(time_str)
        except:
            return np.nan
    
    def process_lap_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process and clean lap time data"""
        if df.empty:
            return df
        
        # Normalize column names (strip whitespace)
        df.columns = df.columns.str.strip()
        
        # Convert lap times to seconds
        time_cols = ['LAP_TIME', 'S1', 'S2', 'S3']
        for col in time_cols:
            if col in df.columns:
                df[col + '_SEC'] = df[col].apply(self.parse_lap_time)
        
        # Handle S1_SECONDS, S2_SECONDS, S3_SECONDS if they exist
        section_cols = ['S1_SECONDS', 'S2_SECONDS', 'S3_SECONDS']
        for col in section_cols:
            if col in df.columns:
                # If already in seconds format, use directly
                df[col.replace('_SECONDS', '_SEC')] = pd.to_numeric(df[col], errors='coerce')
        
        # Ensure numeric columns - handle different column name formats
        numeric_cols = ['NUMBER', 'LAP_NUMBER', 'KPH', 'TOP_SPEED', 'DRIVER_NUMBER']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # If DRIVER_NUMBER exists but NUMBER doesn't, copy it
        if 'DRIVER_NUMBER' in df.columns and 'NUMBER' not in df.columns:
            df['NUMBER'] = df['DRIVER_NUMBER']
        
        return df
    
    def get_available_tracks(self) -> List[str]:
        """Get list of available tracks"""
        return list(self.tracks.keys())
    
    def get_track_display_name(self, track: str) -> str:
        """Get display name for track"""
        names = {
            'barber': 'Barber Motorsports Park',
            'circuit-of-the-americas': 'Circuit of the Americas',
            'indianapolis': 'Indianapolis Motor Speedway',
            'road-america': 'Road America',
            'sebring': 'Sebring International Raceway',
            'sonoma': 'Sonoma Raceway',
            'virginia-international-raceway': 'Virginia International Raceway'
        }
        return names.get(track, track)

