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
model = genai.GenerativeModel(model_name="models/gemini-1.5-flash-latest")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RecommendationInput(BaseModel):
    dietary_preferences: str
    fitness_goals: str
    lifestyle_factors: str
    dietary_restrictions: str
    health_conditions: str
    specific_concerns_or_questions: str
@app.get("/")
def read_root():
    return {"message": "FitGenie API is live!"}
@app.post("/recommendations")
async def get_recommendations(data: RecommendationInput) -> Dict[str, List[str]]:
    prompt = f"""
You are a smart AI named FitGenie.

Analyze the following user's profile and return only valid JSON that includes diet and workout plans.

User Profile:
- Dietary Preferences: {data.dietary_preferences}
- Fitness Goals: {data.fitness_goals}
- Lifestyle Factors: {data.lifestyle_factors}
- Dietary Restrictions: {data.dietary_restrictions}
- Health Conditions: {data.health_conditions}
- specific_concerns_or_questions: {data.specific_concerns_or_questions}

Return a JSON response in exactly this format with no extra explanation or markdown:

{{
  "diet_types": ["Type 1", "Type 2", "Type 3", "Type 4", "Type 5"],
  "workouts": ["Workout 1", "Workout 2", "Workout 3", "Workout 4", "Workout 5"],
  "breakfasts": ["Breakfast 1", "Breakfast 2", "Breakfast 3", "Breakfast 4", "Breakfast 5"],
  "dinners": ["Dinner 1", "Dinner 2", "Dinner 3", "Dinner 4", "Dinner 5"],
  "additional_tips": ["Tip 1", "Tip 2", "Tip 3"],
  "concern_response": ["Answer directly here based on the user's specific concern or question."]
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
        
        if "concern_response" in parsed and isinstance(parsed["concern_response"], list):
            if parsed["concern_response"] and isinstance(parsed["concern_response"][0], str):
                text = parsed["concern_response"][0]
                text = re.sub(r"\s*[;—-]\s*", ", ", text)  
                text = re.sub(r",\s*,", ",", text)        
                text = re.sub(r"\s+", " ", text)           
                parsed["concern_response"][0] = text.strip()

        required_keys = {"diet_types", "workouts", "breakfasts", "dinners", "additional_tips","concern_response"}

        if not required_keys.issubset(parsed.keys()):
            raise HTTPException(status_code=500, detail="Missing expected keys in AI response.")

        return parsed

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Error: {str(e)}")
