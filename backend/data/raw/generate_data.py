import numpy as np
import pandas as pd
import random
from pathlib import Path

np.random.seed(42)
random.seed(42)

OUTPUT_PATH = Path("data/raw/student_data.csv")
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

rows = 500
data = []


def gen_advance():
    return {
        "attendance": np.random.randint(75, 95),
        "internal_marks": np.random.randint(70, 90),
        "assignments": np.random.randint(65, 95),
        "study_hours": np.random.uniform(4, 8),
        "backlog_count": np.random.randint(0, 2),
        "stress_level": np.random.randint(1, 5),
        "risk_level": 0,
    }

def gen_hold():
    return {
        "attendance": np.random.randint(60, 80),
        "internal_marks": np.random.randint(55, 75),
        "assignments": np.random.randint(55, 75),
        "study_hours": np.random.uniform(2.5, 5),
        "backlog_count": np.random.randint(1, 4),
        "stress_level": np.random.randint(4, 7),
        "risk_level": 1,
    }

def gen_retreat():
    return {
        "attendance": np.random.randint(40, 65),
        "internal_marks": np.random.randint(35, 60),
        "assignments": np.random.randint(30, 60),
        "study_hours": np.random.uniform(0.5, 3),
        "backlog_count": np.random.randint(3, 8),
        "stress_level": np.random.randint(6, 10),
        "risk_level": 2,
    }

advance_count = int(rows * 0.28)
hold_count = int(rows * 0.42)
retreat_count = rows - advance_count - hold_count

for _ in range(advance_count):
    data.append(gen_advance())

for _ in range(hold_count):
    data.append(gen_hold())

for _ in range(retreat_count):
    data.append(gen_retreat())

for row in data:
    if random.random() < 0.05:
        row["risk_level"] = random.choice([0, 1, 2])

df = pd.DataFrame(data)
df = df.sample(frac=1, random_state=42).reset_index(drop=True)

df.to_csv(OUTPUT_PATH, index=False)
print(f"Stratified dataset generated at {OUTPUT_PATH.resolve()}")