import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Configuration
START_DATE = "2025-08-01"
DAYS = 3
SAMPLES_PER_DAY = 86400  # 24*60*60
CHAMBER_VOLUME = 100  # Liters (for leak rate calculations)
BASE_PRESSURE_NORMAL = 5e-8
BASE_PRESSURE_PROBLEM = 2e-6

def generate_pressure_profile(phase, time_elapsed, duration, prev_pressure, day_index):
    """Generate realistic pressure profiles with different behaviors"""
    t = time_elapsed/duration if duration > 0 else 0
    
    if phase == "Vented":
        # Stable atmospheric pressure with minor fluctuations
        return 1013 + np.random.normal(0, 1)
    
    elif phase == "Pumping":
        # Exponential decay with different time constants
        if day_index == 0:  # Normal
            tau = 300 + 50*np.sin(time_elapsed/200)
        elif day_index == 1:  # Degraded performance
            tau = 800 if time_elapsed > duration/2 else 500
        else:  # Problem day
            tau = 1200 if np.random.rand() > 0.7 else 400
            
        base = BASE_PRESSURE_PROBLEM if (day_index >= 1 and time_elapsed > duration/3) else BASE_PRESSURE_NORMAL
        return prev_pressure * np.exp(-t*tau) + base
    
    elif phase == "Process":
        # Process-specific pressure ranges
        processes = {
            "CVD": (1.0, 10.0),
            "PVD": (1e-3, 5e-2),
            "ALD": (1e-2, 0.5)
        }
        p_type = ["CVD", "PVD", "ALD"][int(time_elapsed // (duration/3)) % 3]
        low, high = processes[p_type]
        
        # Add process-specific anomalies on problem days
        if day_index == 1:  # Degradation
            if p_type == "CVD" and t > 0.6:
                drift = 0.1 * t * (high - low)
                return np.clip(low + (high-low)*0.7 + drift + np.random.normal(0, 0.1), low, high), p_type
            elif p_type == "PVD":
                return high * 1.8 + np.random.normal(0, high*0.2), p_type
                
        if day_index == 2:  # Severe problems
            if np.random.rand() < 0.01:  # Random spikes
                return np.random.uniform(10, 100), p_type
            elif t > 0.8 and p_type == "ALD":
                return np.random.uniform(5, 8), p_type
                
        return np.random.uniform(low, high), p_type
    
    elif phase == "Base":
        # Base pressure with potential leaks
        pressure = BASE_PRESSURE_NORMAL
        if day_index >= 1 and time_elapsed > duration/2:
            pressure = BASE_PRESSURE_PROBLEM
            if day_index == 1:  # Small leak
                pressure += 3e-9 * time_elapsed
            elif day_index == 2:  # Large leak
                pressure += 1e-7 * time_elapsed
        return pressure + np.abs(np.random.normal(0, pressure*0.3))
    
    return BASE_PRESSURE_NORMAL

def introduce_data_issues(df, day_index):
    """Introduce data problems for day 3"""
    if day_index != 2:
        return df
    
    # 1. Data dropouts (2% of data missing)
    dropout_mask = np.random.rand(len(df)) < 0.02
    df.loc[dropout_mask, "Pressure"] = np.nan
    
    # 2. Corrupt data (0.5% of data)
    corrupt_mask = np.random.rand(len(df)) < 0.005
    df.loc[corrupt_mask, "Pressure"] = np.random.uniform(-10, 1e6, size=corrupt_mask.sum())
    
    # 3. Noisy data (5% of data)
    noisy_mask = np.random.rand(len(df)) < 0.05
    df.loc[noisy_mask, "Pressure"] *= np.random.uniform(0.1, 10, size=noisy_mask.sum())
    
    # 4. Impossible values
    impossible_mask = np.random.rand(len(df)) < 0.002
    df.loc[impossible_mask, "Pressure"] = np.random.choice([-1e3, 1e10, 1e15], size=impossible_mask.sum())
    
    return df

def generate_vacuum_data(day_index):
    """Generate 24 hours of vacuum system data for one day"""
    start_dt = datetime.strptime(START_DATE, "%Y-%m-%d") + timedelta(days=day_index)
    timestamps = [start_dt + timedelta(seconds=i) for i in range(SAMPLES_PER_DAY)]
    
    # Create timeline of system states
    states = []
    current_time = 0
    
    while current_time < SAMPLES_PER_DAY:
        # Determine next state and duration
        state_type = np.random.choice(
            ["Vented", "Pumping", "Process", "Base"],
            p=[0.15, 0.25, 0.45, 0.15] if day_index < 2 else [0.1, 0.2, 0.5, 0.2]
        )
        
        if state_type == "Vented":
            duration = max(1800, np.random.normal(7200, 1800))  # 0.5-4 hours
        elif state_type == "Pumping":
            duration = max(600, np.random.normal(2700, 600))  # 10-60 minutes
        elif state_type == "Process":
            duration = max(3600, np.random.normal(10800, 1800))  # 1-6 hours
        else:  # Base
            duration = max(1200, np.random.normal(3600, 600))  # 20-90 minutes
            
        states.append((state_type, int(duration)))
        current_time += duration
    
    # Generate pressure data
    pressures = []
    process_states = []
    current_pressure = 1013.0  # Start at atmospheric pressure
    
    for state_type, duration in states:
        for t in range(duration):
            new_pressure = current_pressure
            
            if state_type == "Process":
                new_pressure, process_type = generate_pressure_profile(
                    state_type, t, duration, current_pressure, day_index
                )
                process_states.append(process_type)
            else:
                new_pressure = generate_pressure_profile(
                    state_type, t, duration, current_pressure, day_index
                )
                process_states.append(state_type)
            
            # Smooth transitions
            current_pressure = current_pressure * 0.2 + new_pressure * 0.8
            pressures.append(current_pressure)
    
    # Create DataFrame
    df = pd.DataFrame({
        "Timestamp": timestamps,
        "Pressure": pressures[:SAMPLES_PER_DAY],
        "Process_State": process_states[:SAMPLES_PER_DAY]
    })
    
    # Add temperature data
    df["Temperature"] = np.where(
        df["Process_State"] == "CVD", 
        np.random.normal(300, 5, len(df)),
        np.where(
            df["Process_State"] == "PVD",
            np.random.normal(150, 3, len(df)),
            np.where(
                df["Process_State"] == "ALD",
                np.random.normal(200, 4, len(df)),
                np.random.normal(25, 1, len(df))
            )
        )
    )
    
    # Add status codes
    df["Status_Code"] = 0
    if day_index >= 1:
        problem_mask = (
            (df["Process_State"] == "Base") & 
            (df["Pressure"] > BASE_PRESSURE_NORMAL * 5)
        ) | (
            (df["Process_State"] == "Pumping") & 
            (df["Pressure"] > 1e-4)
        )
        df.loc[problem_mask, "Status_Code"] = 1
    
    # Add data issues for day 3
    if day_index == 2:
        df = introduce_data_issues(df, day_index)
        df.loc[df["Status_Code"] == 0, "Status_Code"] = np.random.choice(
            [0, 1, 2], 
            p=[0.7, 0.2, 0.1], 
            size=(df["Status_Code"] == 0).sum()
        )
    
    return df

# Generate data for all three days
for day_idx in range(DAYS):
    df = generate_vacuum_data(day_idx)
    filename = f"vacuum_data_{datetime.strptime(START_DATE, '%Y-%m-%d').date() + timedelta(days=day_idx)}.csv"
    df.to_csv(filename, index=False)
    print(f"Generated {filename} with {len(df)} records")

print("All files generated successfully")