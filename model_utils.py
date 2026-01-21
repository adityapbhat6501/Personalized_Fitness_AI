import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import LabelEncoder

# ======================================================
# LOAD DATASETS
# ======================================================
food_df = pd.read_csv("data/clean_food_data.csv")
workout_df = pd.read_csv("data/clean_workout_data.csv")
student_df = pd.read_csv("data/student_fitness_data.csv")

# ======================================================
# TRAIN K-MEANS CLUSTERING MODEL (ONCE)
# ======================================================
encoded_df = student_df.copy()

encoders = {}
for col in ['gender', 'goal', 'diet', 'budget', 'equipment']:
    le = LabelEncoder()
    encoded_df[col] = le.fit_transform(encoded_df[col])
    encoders[col] = le

X = encoded_df[['bmi', 'daily_calories', 'time_per_day']]

kmeans = KMeans(n_clusters=4, random_state=42)
kmeans.fit(X)

# ======================================================
# CORE CALCULATIONS
# ======================================================
def calculate_bmi(weight, height_cm):
    height_m = height_cm / 100
    return round(weight / (height_m ** 2), 2)


def calculate_daily_calories(age, weight, height_cm, gender, goal):
    if gender.lower() == "male":
        bmr = 10 * weight + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height_cm - 5 * age - 161

    if goal == "fat_loss":
        bmr -= 300
    elif goal == "muscle_gain":
        bmr += 300

    return int(bmr)

# ======================================================
# CLUSTER PREDICTION
# ======================================================
def predict_cluster(bmi, calories, time_per_day):
    return int(kmeans.predict([[bmi, calories, time_per_day]])[0])

# ======================================================
# CLUSTER PROFILES (HIGH-LEVEL STRATEGY)
# ======================================================
cluster_profiles = {
    0: {
        "goal": "Fat Loss",
        "workout_type": "Bodyweight + Cardio",
        "diet_type": "Low-calorie Indian diet"
    },
    1: {
        "goal": "Muscle Gain",
        "workout_type": "Strength Training",
        "diet_type": "High-protein Indian diet"
    },
    2: {
        "goal": "General Fitness",
        "workout_type": "Mixed Training",
        "diet_type": "Balanced Indian diet"
    },
    3: {
        "goal": "Healthy Weight Gain",
        "workout_type": "Light Strength",
        "diet_type": "Calorie-dense Indian diet"
    }
}

# ======================================================
# HYBRID RECOMMENDATION LOGIC
# ======================================================
def get_recommendation(cluster, calories, time, goal, equipment, diet):
    profile = cluster_profiles[cluster]

    # Workout strategy
    workout_type = profile["workout_type"]

    if equipment == "none":
        workout_type = "Bodyweight + Cardio"
    elif equipment == "gym" and goal == "muscle_gain":
        workout_type = "Strength Training"

    # Diet strategy
    diet_type = profile["diet_type"]
    diet_type += " (Veg)" if diet == "veg" else " (Non-Veg)"

    return {
        "Fitness Goal": profile["goal"],
        "Workout Plan": workout_type,
        "Diet Plan": diet_type,
        "Daily Calories": calories,
        "Time per Day": time
    }

# ======================================================
# DAILY WORKOUT GENERATOR (HARD CONSTRAINTS)
# ======================================================
def generate_workout_plan(workout_type, time_minutes, equipment):
    df = workout_df.copy()

    # HARD EQUIPMENT CONSTRAINT
    if equipment == "none":
        df = df[df['equipment'].str.contains("body", case=False, na=False)]
    elif equipment == "dumbbells":
        df = df[df['equipment'].str.contains("dumbbell|body", case=False, na=False)]
    elif equipment == "gym":
        df = df

    # STRATEGY FILTER
    if workout_type == "Bodyweight + Cardio":
        df = df[df['equipment'].str.contains("body|cardio", case=False, na=False)]
    elif workout_type == "Strength Training":
        df = df[df['muscle'].notna()]

    # SAFETY FALLBACK
    if len(df) < 5:
        df = workout_df[workout_df['equipment'].str.contains("body", case=False, na=False)]

    return df.sample(min(5, len(df)))[['exercise', 'muscle', 'equipment']]

# ======================================================
# DAILY DIET GENERATOR
# ======================================================
def generate_diet_plan(diet_type, calorie_limit):
    df = food_df.copy()

    if "Low-calorie" in diet_type:
        df = df[df['calories'] < 200]
    if "High-protein" in diet_type:
        df = df[df['protein'] > 10]

    return df.sample(min(5, len(df)))[['dish', 'calories', 'protein', 'carbs', 'fats']]

# ======================================================
# WEEKLY WORKOUT PLANNER (STRUCTURED SPLIT)
# ======================================================
def generate_weekly_workout(workout_type, equipment):
    week = {}

    split_plan = {
        "Monday": "Upper",
        "Tuesday": "Lower",
        "Wednesday": "Core",
        "Thursday": "Upper",
        "Friday": "Lower",
        "Saturday": "Full",
        "Sunday": "Rest"
    }

    for day, focus in split_plan.items():

        if focus == "Rest":
            week[day] = [{
                "exercise": "Rest / Light Walking / Stretching",
                "muscle": "-",
                "equipment": "-"
            }]
            continue

        df = workout_df.copy()

        # Equipment constraint
        if equipment == "none":
            df = df[df['equipment'].str.contains("body", case=False, na=False)]
        elif equipment == "dumbbells":
            df = df[df['equipment'].str.contains("dumbbell|body", case=False, na=False)]

        # Muscle focus
        if focus == "Upper":
            df = df[df['muscle'].str.contains(
                "Chest|Back|Shoulder|Biceps|Triceps|Lats",
                case=False, na=False
            )]
        elif focus == "Lower":
            df = df[df['muscle'].str.contains(
                "Leg|Quadriceps|Hamstrings|Glutes|Calves",
                case=False, na=False
            )]
        elif focus == "Core":
            df = df[df['muscle'].str.contains(
                "Ab|Core|Oblique",
                case=False, na=False
            )]

        if len(df) < 5:
            df = workout_df[workout_df['equipment'].str.contains("body", case=False, na=False)]

        week[day] = df.sample(min(5, len(df)))[
            ['exercise', 'muscle', 'equipment']
        ].to_dict(orient="records")

    return week

# ======================================================
# WEEKLY DIET PLANNER
# ======================================================
def generate_weekly_diet(diet_type, calorie_limit):
    week = {}
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    df = food_df.copy()

    if "Low-calorie" in diet_type:
        df = df[df['calories'] < 200]
    if "High-protein" in diet_type:
        df = df[df['protein'] > 10]

    for day in days:
        week[day] = df.sample(min(5, len(df)))[
            ['dish', 'calories', 'protein', 'carbs', 'fats']
        ].to_dict(orient="records")

    return week
