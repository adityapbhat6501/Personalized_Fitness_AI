import os
from flask import Flask, render_template, request
from model_utils import (
    calculate_bmi,
    calculate_daily_calories,
    predict_cluster,
    get_recommendation,
    generate_workout_plan,
    generate_diet_plan,
    generate_weekly_workout,
    generate_weekly_diet
)

app = Flask(__name__)

# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html")


# --------------------------------------------------
# PREDICTION / DASHBOARD
# --------------------------------------------------
@app.route("/predict", methods=["POST"])
def predict():
    # -------- USER INPUTS --------
    age = int(request.form["age"])
    gender = request.form["gender"]
    height = int(request.form["height"])
    weight = int(request.form["weight"])
    goal = request.form["goal"]
    diet = request.form["diet"]
    budget = request.form["budget"]
    equipment = request.form["equipment"]
    time = int(request.form["time"])

    # -------- CORE AI CALCULATIONS --------
    bmi = calculate_bmi(weight, height)
    calories = calculate_daily_calories(age, weight, height, gender, goal)

    cluster = predict_cluster(bmi, calories, time)

    recommendation = get_recommendation(
        cluster,
        calories,
        time,
        goal,
        equipment,
        diet
    )

    # -------- DAILY PLANS --------
    workout = generate_workout_plan(
        recommendation["Workout Plan"],
        time,
        equipment
    )

    diet_plan = generate_diet_plan(
        recommendation["Diet Plan"],
        calories
    )

    # -------- WEEKLY PLANS --------
    weekly_workout = generate_weekly_workout(
        recommendation["Workout Plan"],
        equipment
    )

    weekly_diet = generate_weekly_diet(
        recommendation["Diet Plan"],
        calories
    )

    # -------- RENDER DASHBOARD --------
    return render_template(
        "result.html",
        bmi=bmi,
        calories=calories,
        recommendation=recommendation,
        workout=workout.to_dict(orient="records"),
        diet=diet_plan.to_dict(orient="records"),
        weekly_workout=weekly_workout,
        weekly_diet=weekly_diet
    )


# --------------------------------------------------
# RUN APP (DEPLOYMENT READY)
# --------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
