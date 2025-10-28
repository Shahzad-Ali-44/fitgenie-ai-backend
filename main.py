from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List
from dotenv import load_dotenv
import google.generativeai as genai
import os
import json
import re

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise RuntimeError("GOOGLE_API_KEY is missing in your .env file")

genai.configure(api_key=api_key)
model = genai.GenerativeModel(model_name="models/gemini-2.5-flash-lite")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RecommendationInput(BaseModel):
    name: str = ""
    age: str = ""
    gender: str = ""
    height: str = ""
    weight: str = ""
    activity_level: str = ""
    current_fitness_level: str = ""
    target_weight: str = ""
    dietary_preferences: str = ""
    dietary_restrictions: str = ""
    fitness_goals: str = ""
    health_conditions: str = ""
    allergies: str = ""
@app.get("/")
def read_root():
    return {"message": "FitGenie API is live!"}

@app.post("/recommendations")
async def get_recommendations(data: RecommendationInput):
    bmi_info = ""
    if data.height and data.weight:
        try:
            height_str = data.height.strip()
            height_cm = 0
            
            if "'" in height_str:
                parts = height_str.split("'")
                if len(parts) >= 2:
                    feet = float(parts[0].strip())
                    inches_str = parts[1].replace('"', "").strip()
                    if inches_str and inches_str.replace('.', '', 1).isdigit():
                        inches = float(inches_str)
                    else:
                        inches = 0
                    height_cm = (feet * 12 + inches) * 2.54
                elif len(parts) == 1:
                    feet = float(parts[0].strip())
                    height_cm = feet * 30.48
            elif "cm" in height_str.lower():
                height_cm = float(height_str.replace("cm", "").strip())
            else:
                height_num = float(height_str)
                if height_num > 10:
                    height_cm = height_num
                else:
                    height_cm = height_num * 30.48
            
            weight_str = data.weight.strip()
            weight_kg = 0
            
            if "lbs" in weight_str.lower() or "lb" in weight_str.lower():
                weight_kg = float(weight_str.replace("lbs", "").replace("lb", "").strip()) * 0.453592
            elif "kg" in weight_str.lower():
                weight_kg = float(weight_str.replace("kg", "").strip())
            else:
                weight_num = float(weight_str)
                if weight_num > 50:
                    weight_kg = weight_num
                else:
                    weight_kg = weight_num * 0.453592
            if height_cm > 0 and weight_kg > 0:
                bmi = weight_kg / ((height_cm / 100) ** 2)
                bmi_category = ""
                if bmi < 18.5:
                    bmi_category = "Underweight"
                elif bmi < 25:
                    bmi_category = "Normal weight"
                elif bmi < 30:
                    bmi_category = "Overweight"
                else:
                    bmi_category = "Obese"
                
                bmi_info = f"BMI: {bmi:.1f} ({bmi_category})"
            else:
                bmi_info = f"BMI calculation failed - Height: {data.height}, Weight: {data.weight}"
        except Exception as e:
            bmi_info = f"BMI calculation error - Height: {data.height}, Weight: {data.weight}, Error: {str(e)}"

    prompt = f"""
You are FitGenie AI, an expert nutritionist and fitness trainer. Create a personalized diet and fitness plan.

USER PROFILE:
Name: {data.name}
Age: {data.age} years
Gender: {data.gender}
Height: {data.height}
Weight: {data.weight}
{bmi_info}

HEALTH METRICS:
Activity Level: {data.activity_level}
Current Fitness Level: {data.current_fitness_level}
Target Weight: {data.target_weight}

DIETARY PREFERENCES:
Diet Type: {data.dietary_preferences}
Restrictions: {data.dietary_restrictions}

GOALS & LIFESTYLE:
Fitness Goals: {data.fitness_goals}

HEALTH CONDITIONS:
Medical Conditions: {data.health_conditions}
Allergies: {data.allergies}

CRITICAL: Return ONLY valid JSON. No markdown, no explanations, no extra text. Start with {{ and end with }}.

IMPORTANT: 
- For bmi_analysis field, use exactly this: {bmi_info}. Do NOT generate your own BMI analysis or calculations.
- For supplements, lifestyle_tips, and progress_tracking arrays: provide EXACTLY 4 items each, no more, no less.

{{
  "personalized_summary": "Brief summary of recommendations for this {data.gender} aged {data.age} with {data.fitness_goals} goals",
  "bmi_analysis": "{bmi_info}",
  "diet_plan": {{
    "diet_types": ["Balanced Diet", "High Protein", "Low Carb"],
    "daily_calories": "1800-2200 calories per day",
    "macros": "Protein: 120-150g, Carbs: 180-220g, Fats: 60-80g",
    "meal_timing": ["Breakfast: 7-8 AM", "Lunch: 12-1 PM", "Dinner: 7-8 PM"],
    "hydration": ["Drink 8-10 glasses of water daily"]
  }},
  "workout_plan": {{
    "workout_types": ["Cardio", "Strength Training", "Flexibility"],
    "frequency": "4-5 times per week",
    "duration": "45-60 minutes per session",
    "intensity": "{data.current_fitness_level}",
    "schedule": ["Monday: Upper Body", "Tuesday: Cardio", "Wednesday: Lower Body", "Thursday: Cardio", "Friday: Full Body"]
  }},
  "meal_suggestions": {{
    "breakfast": ["Oatmeal with berries and nuts", "Greek yogurt with granola", "Scrambled eggs with whole grain toast"],
    "lunch": ["Grilled chicken salad", "Quinoa bowl with vegetables", "Turkey and avocado wrap"],
    "dinner": ["Baked salmon with sweet potato", "Lean beef with brown rice", "Vegetable stir-fry with tofu"],
    "snacks": ["Apple with almond butter", "Greek yogurt with honey", "Mixed nuts and dried fruits"]
  }},
  "supplements": ["**Whey Protein:** To aid muscle recovery and meet protein targets", "**Multivitamin:** To ensure you're getting essential vitamins and minerals", "**Omega-3 Fatty Acids:** Supports heart and brain function", "**Vitamin D:** Supports bone health and immune function"],
  "lifestyle_tips": ["**Prioritize Sleep:** Get 7-8 hours of quality sleep per night", "**Stay Hydrated:** Drink 8-10 glasses of water throughout the day", "**Take Breaks:** Stand up and stretch every 30-60 minutes", "**Manage Stress:** Practice mindfulness or short meditation sessions"],
  "progress_tracking": ["**Weekly Weigh-ins:** Weigh yourself at the same time each week", "**Body Measurements:** Take key measurements monthly", "**Fitness Journal:** Track workouts and progress", "**Progress Photos:** Take photos every 4 weeks"]
}}
"""

    try:
        response = model.generate_content(prompt)
        text = (response.text or "").strip()
        
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            raise HTTPException(status_code=500, detail="Could not find JSON in AI response.")

        json_str = match.group(0)
        parsed = json.loads(json_str)
        
        required_keys = {
            "personalized_summary", "bmi_analysis", "diet_plan", "workout_plan", 
            "meal_suggestions", "supplements", "lifestyle_tips", "progress_tracking"
        }

        for key in required_keys:
            if key not in parsed:
                if key == "personalized_summary":
                    parsed[key] = f"Personalized recommendations for {data.gender} aged {data.age} with {data.fitness_goals} goals"
                elif key == "bmi_analysis":
                    parsed[key] = bmi_info if bmi_info else "BMI calculation not available"
                elif key == "diet_plan":
                    parsed[key] = {
                        "diet_types": ["Balanced Diet", "High Protein"],
                        "daily_calories": "1800-2200 calories per day",
                        "macros": "Protein: 120-150g, Carbs: 180-220g, Fats: 60-80g",
                        "meal_timing": ["Breakfast: 7-8 AM", "Lunch: 12-1 PM", "Dinner: 7-8 PM"],
                        "hydration": ["Drink 8-10 glasses of water daily"]
                    }
                elif key == "workout_plan":
                    parsed[key] = {
                        "workout_types": ["Cardio", "Strength Training"],
                        "frequency": "4-5 times per week",
                        "duration": "45-60 minutes per session",
                        "intensity": data.current_fitness_level or "Intermediate",
                        "schedule": ["Monday: Upper Body", "Tuesday: Cardio", "Wednesday: Lower Body"]
                    }
                elif key == "meal_suggestions":
                    parsed[key] = {
                        "breakfast": ["Oatmeal with berries", "Greek yogurt with granola", "Scrambled eggs"],
                        "lunch": ["Grilled chicken salad", "Quinoa bowl", "Turkey wrap"],
                        "dinner": ["Baked salmon", "Lean beef with rice", "Vegetable stir-fry"],
                        "snacks": ["Apple with almond butter", "Greek yogurt", "Mixed nuts"]
                    }
                elif key == "supplements":
                    parsed[key] = ["**Whey Protein:** For muscle recovery", "**Multivitamin:** For essential vitamins", "**Omega-3:** For heart health", "**Vitamin D:** For bone health"]
                elif key == "lifestyle_tips":
                    parsed[key] = ["**Prioritize Sleep:** Get 7-8 hours of quality sleep", "**Stay Hydrated:** Drink 8-10 glasses of water", "**Take Breaks:** Stand up every 30-60 minutes", "**Manage Stress:** Practice mindfulness"]
                elif key == "progress_tracking":
                    parsed[key] = ["**Weekly Weigh-ins:** Weigh yourself at the same time each week", "**Body Measurements:** Take key measurements monthly", "**Fitness Journal:** Track workouts and progress", "**Progress Photos:** Take photos every 4 weeks"]

        if "bmi_analysis" in parsed:
            parsed["bmi_analysis"] = bmi_info if bmi_info else "BMI calculation not available"

        return parsed

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Error: {str(e)}")
