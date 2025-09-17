import pandas as pd
from datetime import datetime, timedelta
import random

# starting timestamp (string in quotes)
start_str = "2025-09-16 13:48:01.000"

# convert string to datetime
start_time = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S.%f")

# how many timestamps to generate
n = 144  # change this as needed

timestamps = []
current_time = start_time

for _ in range(n):
    # random increment: 1-3 minutes + 1-59 seconds
    minutes = random.randint(1, 3)
    seconds = random.randint(1, 59)
    current_time += timedelta(minutes=minutes, seconds=seconds)

    # keep quotes + .000
    timestamps.append(f'"{current_time.strftime("%Y-%m-%d %H:%M:%S")}.000"')

# create DataFrame
df = pd.DataFrame(timestamps, columns=["Timestamps"])

# export to Excel
output_file = "timestamps_random.xlsx"
df.to_excel(output_file, index=False)

print(f"✅ Excel file saved: {output_file}")
