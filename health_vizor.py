from dotenv import load_dotenv
load_dotenv()

import json
import streamlit as st
from openai import OpenAI
from pydantic import BaseModel
from typing import Dict, List, Optional
from llm_utils import call_llm
from prompt import PROMPT
import os
import pandas as pd

st.set_page_config(page_title="HealthVizor", layout="wide")

# Initialize session state for metadata if not present
if 'metadata' not in st.session_state:
    st.session_state.metadata = {
        "name": "Arjun Kumar",
        "age": 30,
        "gender": "male", 
        "height": "5'8\" (173 cm)",
        "body_weight": "72 kg",
        "goal": "improve energy levels and muscle building"
    }

# Initialize additional session state variables
if 'biomarkers_data' not in st.session_state:
    st.session_state.biomarkers_data = """Vitamin D: 18 ng/mL (Low - Normal range: 30-100 ng/mL)
Vitamin B12: 350 pg/mL (Normal range: 300-900 pg/mL)
Iron: 65 μg/dL (Normal range: 60-170 μg/dL)
Ferritin: 45 ng/mL (Normal range: 30-400 ng/mL)
Fasting Glucose: 92 mg/dL (Normal range: 70-100 mg/dL)
HbA1c: 5.4% (Normal range: <5.7%)
Total Cholesterol: 185 mg/dL (Normal range: <200 mg/dL)
HDL Cholesterol: 38 mg/dL (Low - Normal range: >40 mg/dL for men)
LDL Cholesterol: 125 mg/dL (Normal range: <100 mg/dL)
Triglycerides: 110 mg/dL (Normal range: <150 mg/dL)
TSH: 2.8 mIU/L (Normal range: 0.4-4.5 mIU/L)
Cortisol (morning): 15 μg/dL (Normal range: 6-23 μg/dL)
Testosterone: 480 ng/dL (Normal range: 300-1000 ng/dL)
CRP: 1.2 mg/L (Low risk: <1.0 mg/L)"""
if 'category_scores' not in st.session_state:
    st.session_state.category_scores = """Metabolic Health: 75/100 - Good glucose control but room for improvement in lipid profile
Cardiovascular Health: 68/100 - HDL cholesterol below optimal, moderate inflammation markers
Immune Function: 62/100 - Low Vitamin D affecting immune response
Energy & Vitality: 58/100 - Suboptimal iron status and vitamin D affecting energy levels
Hormonal Balance: 72/100 - Testosterone within normal range, cortisol slightly elevated
Nutritional Status: 65/100 - Multiple micronutrient deficiencies detected
Inflammation Status: 70/100 - Mild elevation in inflammatory markers
Sleep Quality: 60/100 - Based on self-reported sleep issues and cortisol patterns
Stress Management: 55/100 - Elevated cortisol suggests stress management needed
Physical Fitness: 70/100 - Active lifestyle but could optimize nutrition for better performance"""

# Initialize user history and personalization tracking
if 'user_history' not in st.session_state:
    st.session_state.user_history = {
        "previous_reports": [],
        "recommendation_feedback": {},
        "preferred_supplements": [],
        "lifestyle_preferences": [],
        "nutrition_preferences": [],
        "interaction_count": 0,
        "last_interaction_date": None
    }

# Initialize personalization preferences
if 'personalization_prefs' not in st.session_state:
    st.session_state.personalization_prefs = {
        "communication_style": "encouraging",  # encouraging, direct, detailed
        "focus_areas": [],  # supplements, lifestyle, nutrition, biomarkers
        "reminder_frequency": "weekly",
        "goal_tracking": True
    }

from pydantic import Field

# LiteLLM-compatible Pydantic models with non-empty object schemas for Gemini/VertexAI

class SupplementRecommendation(BaseModel):
    supplement_name: str = Field(..., description="Name of the supplement being recommended")
    rationale: str = Field(..., description="Rationale for recommending this supplement")
    dosage: str = Field(..., description="Recommended dose using educational language (e.g., 'Studies suggest 500mg may support...')")
    timing: str = Field(..., description="When to take (morning, evening, with meals, etc.)")
    food_timing: str = Field(..., description="Before/with/after food instructions")
    purpose: str = Field(..., description="Purpose and how it helps the user")
    biomarker_connection: str = Field(..., description="How this connects to user's biomarker data and goals")
    duration: str = Field(..., description="How long to take the supplement")
    retest_timing: str = Field(..., description="When to retest biomarkers")
    evidence_source: str = Field(..., description="Scientific evidence source")
    cautions: Optional[str] = Field(None, description="Side effects or cautions")

class NutritionRecommendation(BaseModel):
    nutrition_name: str = Field(..., description="Name of the nutrition recommendation")
    rationale: str = Field(..., description="Why this is recommended based on biomarker data")
    priority_rank: int = Field(..., description="Priority ranking (1-5)")
    evidence_strength: str = Field(..., description="Strength of evidence (High/Medium/Low)")
    implementation_tips: List[str] = Field(default_factory=list, description="3-4 practical tips for implementation")
    foods_to_avoid: List[str] = Field(default_factory=list, description="Foods to avoid or limit")
    evidence_source: str = Field(..., description="Scientific evidence source")

class ExerciseRecommendation(BaseModel):
    exercise_name: str = Field(..., description="Name of the exercise/lifestyle recommendation")
    rationale: str = Field(..., description="Why this is recommended based on biomarker data")
    workout_type: str = Field(..., description="Type of workout (strength, cardio, flexibility, etc.)")
    frequency: str = Field(..., description="How often per week")
    duration: str = Field(..., description="Duration per session")
    intensity: str = Field(..., description="Intensity level recommendations")
    volume: str = Field(..., description="Volume recommendations")
    rest_periods: str = Field(..., description="Rest period recommendations")
    biomarker_connection: str = Field(..., description="How this connects to biomarker data and goals")
    evidence_source: str = Field(..., description="Scientific evidence source")

class CategoryInsight(BaseModel):
    category_name: str = Field(..., description="Name of the health category")
    score: str = Field(..., description="Category score (e.g., '75/100')")
    summary: str = Field(..., description="3-5 sentence summary of category trends")
    impact_on_goals: str = Field(..., description="How this category impacts user's goals")
    improvement_importance: str = Field(..., description="Why improving this category is important")
    biomarker_connections: List[str] = Field(default_factory=list, description="Connected biomarkers")
    what_to_continue: Optional[str] = Field(None, description="What's working well to continue (for green categories)")

class BiomarkerInsight(BaseModel):
    biomarker_name: str = Field(..., description="Name of the biomarker")
    status: str = Field(..., description="Status (Red/Amber/Green/Optimal)")
    current_value: str = Field(..., description="Current biomarker value")
    reference_range: str = Field(..., description="Normal reference range")
    health_impact: str = Field(..., description="What this means for health (3-5 sentences)")
    goal_connection: str = Field(..., description="How addressing this helps achieve goals")
    longevity_performance_impact: str = Field(..., description="Impact on longevity and performance")
    consequences_if_ignored: Optional[str] = Field(None, description="What happens if not addressed (for Red/Amber)")
    what_to_continue: Optional[str] = Field(None, description="What's working well (for Green/Optimal)")
    evidence_source: str = Field(..., description="Scientific evidence source")

class MonthlyPlan(BaseModel):
    month_range: str = Field(..., description="Month range (e.g., 'Months 0-2')")
    focus_areas: List[str] = Field(default_factory=list, description="Key focus areas for this period")
    supplement_adjustments: List[str] = Field(default_factory=list, description="Supplement plan for this period")
    nutrition_focus: List[str] = Field(default_factory=list, description="Nutrition focus for this period")
    exercise_goals: List[str] = Field(default_factory=list, description="Exercise goals for this period")
    lifestyle_targets: List[str] = Field(default_factory=list, description="Lifestyle targets")
    retest_schedule: List[str] = Field(default_factory=list, description="When to retest biomarkers")

class ActionPlan(BaseModel):
    supplements: List[SupplementRecommendation] = Field(default_factory=list, description="Supplement recommendations (max 10)")
    supplement_schedule_summary: str = Field(..., description="Daily supplement schedule organized by time")
    nutrition: List[NutritionRecommendation] = Field(default_factory=list, description="Nutrition recommendations (max 5)")
    exercise_lifestyle: List[ExerciseRecommendation] = Field(default_factory=list, description="Exercise and lifestyle recommendations (max 5)")
    six_month_timeline: List[MonthlyPlan] = Field(default_factory=list, description="6-month action plan timeline")

class HealthVizorResponse(BaseModel):
    # A) Overall Health Summary & Personalization
    overall_health_summary: str = Field(..., description="Fun, highly personalized health summary with congratulations, wins, and priorities")
    top_priority_categories: List[str] = Field(default_factory=list, description="Top 3 health categories to prioritize for improvement")
    
    # B) Category Level Insights & Personalization  
    category_insights: List[CategoryInsight] = Field(default_factory=list, description="Detailed insights for each health category")
    
    # C) Biomarker Level Findings & Personalization
    biomarker_insights: List[BiomarkerInsight] = Field(default_factory=list, description="Detailed insights for each biomarker")
    
    # D) Personalized Action Plan
    action_plan: ActionPlan = Field(default_factory=ActionPlan, description="Comprehensive personalized action plan")
    
    # Disclaimer
    disclaimer: str = Field(
        default="These recommendations are for educational purposes only and do not constitute medical advice. Please consult a healthcare provider before starting any new regimen.",
        description="Medical disclaimer"
    )

# Helper functions for displaying structured data
def display_biomarker_insight(insight, icon):
    if isinstance(insight, dict):
        biomarker_name = insight.get('biomarker_name', '')
        current_value = insight.get('current_value', '')
        reference_range = insight.get('reference_range', '')
        health_impact = insight.get('health_impact', '')
        goal_connection = insight.get('goal_connection', '')
        consequences = insight.get('consequences_if_ignored', '')
        what_to_continue = insight.get('what_to_continue', '')
        evidence_source = insight.get('evidence_source', '')
    else:
        biomarker_name = getattr(insight, 'biomarker_name', '')
        current_value = getattr(insight, 'current_value', '')
        reference_range = getattr(insight, 'reference_range', '')
        health_impact = getattr(insight, 'health_impact', '')
        goal_connection = getattr(insight, 'goal_connection', '')
        consequences = getattr(insight, 'consequences_if_ignored', '')
        what_to_continue = getattr(insight, 'what_to_continue', '')
        evidence_source = getattr(insight, 'evidence_source', '')
    
    with st.expander(f"{icon} {biomarker_name}: {current_value}", expanded=False):
        st.markdown(f"**Reference Range:** {reference_range}")
        st.markdown(f"**Health Impact:** {health_impact}")
        st.markdown(f"**Connection to Your Goals:** {goal_connection}")
        if consequences:
            st.warning(f"**If Not Addressed:** {consequences}")
        if what_to_continue:
            st.success(f"**Keep Doing:** {what_to_continue}")
        if evidence_source:
            st.caption(f"**Evidence:** {evidence_source}")

def display_supplement_recommendation(supp, index, user_name):
    if isinstance(supp, dict):
        supp_name = supp.get('supplement_name', '')
        dosage = supp.get('dosage', '')
        timing = supp.get('timing', '')
        food_timing = supp.get('food_timing', '')
        purpose = supp.get('purpose', '')
        biomarker_connection = supp.get('biomarker_connection', '')
        duration = supp.get('duration', '')
        retest_timing = supp.get('retest_timing', '')
        evidence_source = supp.get('evidence_source', '')
        cautions = supp.get('cautions', '')
    else:
        supp_name = getattr(supp, 'supplement_name', '')
        dosage = getattr(supp, 'dosage', '')
        timing = getattr(supp, 'timing', '')
        food_timing = getattr(supp, 'food_timing', '')
        purpose = getattr(supp, 'purpose', '')
        biomarker_connection = getattr(supp, 'biomarker_connection', '')
        duration = getattr(supp, 'duration', '')
        retest_timing = getattr(supp, 'retest_timing', '')
        evidence_source = getattr(supp, 'evidence_source', '')
        cautions = getattr(supp, 'cautions', '')
    
    with st.expander(f"💊 {index + 1}. {supp_name}", expanded=False):
        st.markdown(f"**Dosage:** {dosage}")
        st.markdown(f"**Timing:** {timing}")
        st.markdown(f"**With Food:** {food_timing}")
        st.markdown(f"**Purpose:** {purpose}")
        st.markdown(f"**Connection to Your Data:** {biomarker_connection}")
        st.markdown(f"**Duration:** {duration}")
        st.markdown(f"**Retest:** {retest_timing}")
        if cautions:
            st.warning(f"**Cautions:** {cautions}")
        if evidence_source:
            st.caption(f"**Evidence:** {evidence_source}")
        
        # Add to user preferences
        if st.button(f"✅ Add {supp_name} to my supplements", key=f"add_supp_{index}"):
            if supp_name not in st.session_state.user_history["preferred_supplements"]:
                st.session_state.user_history["preferred_supplements"].append(supp_name)
                st.success(f"Added {supp_name} to your supplement preferences!")

def display_nutrition_recommendation(nutrition, index, user_name):
    if isinstance(nutrition, dict):
        nutrition_name = nutrition.get('nutrition_name', '')
        rationale = nutrition.get('rationale', '')
        priority_rank = nutrition.get('priority_rank', 0)
        evidence_strength = nutrition.get('evidence_strength', '')
        implementation_tips = nutrition.get('implementation_tips', [])
        foods_to_avoid = nutrition.get('foods_to_avoid', [])
        evidence_source = nutrition.get('evidence_source', '')
    else:
        nutrition_name = getattr(nutrition, 'nutrition_name', '')
        rationale = getattr(nutrition, 'rationale', '')
        priority_rank = getattr(nutrition, 'priority_rank', 0)
        evidence_strength = getattr(nutrition, 'evidence_strength', '')
        implementation_tips = getattr(nutrition, 'implementation_tips', [])
        foods_to_avoid = getattr(nutrition, 'foods_to_avoid', [])
        evidence_source = getattr(nutrition, 'evidence_source', '')
    
    with st.expander(f"🥗 Priority #{priority_rank}: {nutrition_name} ({evidence_strength} Evidence)", expanded=False):
        st.markdown(f"**Why This Matters:** {rationale}")
        if implementation_tips:
            st.markdown("**How to Implement:**")
            for tip in implementation_tips:
                st.markdown(f"• {tip}")
        if foods_to_avoid:
            st.markdown("**Foods to Limit/Avoid:**")
            for food in foods_to_avoid:
                st.markdown(f"• {food}")
        if evidence_source:
            st.caption(f"**Evidence:** {evidence_source}")
        
        # Add to user preferences
        if st.button(f"✅ Add to my nutrition plan", key=f"add_nutrition_{index}"):
            if nutrition_name not in st.session_state.user_history["nutrition_preferences"]:
                st.session_state.user_history["nutrition_preferences"].append(nutrition_name)
                st.success(f"Added to your nutrition preferences!")

def display_exercise_recommendation(exercise, index, user_name):
    if isinstance(exercise, dict):
        exercise_name = exercise.get('exercise_name', '')
        rationale = exercise.get('rationale', '')
        workout_type = exercise.get('workout_type', '')
        frequency = exercise.get('frequency', '')
        duration = exercise.get('duration', '')
        intensity = exercise.get('intensity', '')
        volume = exercise.get('volume', '')
        rest_periods = exercise.get('rest_periods', '')
        biomarker_connection = exercise.get('biomarker_connection', '')
        evidence_source = exercise.get('evidence_source', '')
    else:
        exercise_name = getattr(exercise, 'exercise_name', '')
        rationale = getattr(exercise, 'rationale', '')
        workout_type = getattr(exercise, 'workout_type', '')
        frequency = getattr(exercise, 'frequency', '')
        duration = getattr(exercise, 'duration', '')
        intensity = getattr(exercise, 'intensity', '')
        volume = getattr(exercise, 'volume', '')
        rest_periods = getattr(exercise, 'rest_periods', '')
        biomarker_connection = getattr(exercise, 'biomarker_connection', '')
        evidence_source = getattr(exercise, 'evidence_source', '')
    
    with st.expander(f"🏋️ {exercise_name}", expanded=False):
        st.markdown(f"**Why This Works for You:** {rationale}")
        st.markdown(f"**Type:** {workout_type}")
        st.markdown(f"**Frequency:** {frequency}")
        st.markdown(f"**Duration:** {duration}")
        st.markdown(f"**Intensity:** {intensity}")
        if volume:
            st.markdown(f"**Volume:** {volume}")
        if rest_periods:
            st.markdown(f"**Rest Periods:** {rest_periods}")
        st.markdown(f"**Connection to Your Data:** {biomarker_connection}")
        if evidence_source:
            st.caption(f"**Evidence:** {evidence_source}")
        
        # Add to user preferences
        if st.button(f"✅ Add to my exercise routine", key=f"add_exercise_{index}"):
            if exercise_name not in st.session_state.user_history["lifestyle_preferences"]:
                st.session_state.user_history["lifestyle_preferences"].append(exercise_name)
                st.success(f"Added to your exercise preferences!")

def display_monthly_plan(plan, user_name):
    if isinstance(plan, dict):
        month_range = plan.get('month_range', '')
        focus_areas = plan.get('focus_areas', [])
        supplement_adjustments = plan.get('supplement_adjustments', [])
        nutrition_focus = plan.get('nutrition_focus', [])
        exercise_goals = plan.get('exercise_goals', [])
        lifestyle_targets = plan.get('lifestyle_targets', [])
        retest_schedule = plan.get('retest_schedule', [])
    else:
        month_range = getattr(plan, 'month_range', '')
        focus_areas = getattr(plan, 'focus_areas', [])
        supplement_adjustments = getattr(plan, 'supplement_adjustments', [])
        nutrition_focus = getattr(plan, 'nutrition_focus', [])
        exercise_goals = getattr(plan, 'exercise_goals', [])
        lifestyle_targets = getattr(plan, 'lifestyle_targets', [])
        retest_schedule = getattr(plan, 'retest_schedule', [])
    
    with st.expander(f"📅 {month_range}", expanded=False):
        if focus_areas:
            st.markdown("**🎯 Focus Areas:**")
            for area in focus_areas:
                st.markdown(f"• {area}")
        
        col1, col2 = st.columns(2)
        with col1:
            if supplement_adjustments:
                st.markdown("**💊 Supplements:**")
                for supp in supplement_adjustments:
                    st.markdown(f"• {supp}")
            if nutrition_focus:
                st.markdown("**🥗 Nutrition:**")
                for nutrition in nutrition_focus:
                    st.markdown(f"• {nutrition}")
        
        with col2:
            if exercise_goals:
                st.markdown("**🏋️ Exercise:**")
                for exercise in exercise_goals:
                    st.markdown(f"• {exercise}")
            if lifestyle_targets:
                st.markdown("**🧘 Lifestyle:**")
                for lifestyle in lifestyle_targets:
                    st.markdown(f"• {lifestyle}")
        
        if retest_schedule:
            st.markdown("**🔬 Testing Schedule:**")
            for retest in retest_schedule:
                st.markdown(f"• {retest}")

# Add breezy, light, semi-transparent background
st.markdown(
    """
    <style>
    .stApp {
        background: rgba(220, 240, 255, 0.6) !important;
        /* fallback for older browsers */
        background-color: #eaf6ff !important;
    }
    /* Make form fields a little darker and add border */
    input[type="text"], input[type="number"], textarea, .stTextInput > div > input, .stNumberInput > div > input, .stTextArea > div > textarea {
        background-color: #f7fbff !important;
        border: 1.5px solid #b3c6d9 !important;
        border-radius: 6px !important;
        color: #222 !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
        transition: border 0.2s;
    }
    input[type="text"]:focus, input[type="number"]:focus, textarea:focus, .stTextInput > div > input:focus, .stNumberInput > div > input:focus, .stTextArea > div > textarea:focus {
        border: 2px solid #30A0E0 !important;
        outline: none !important;
    }
    select, .stSelectbox > div, .stSelectSlider > div {
        background-color: #f7fbff !important;
        border: 1.5px solid #b3c6d9 !important;
        border-radius: 6px !important;
        color: #222 !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Display personalized greeting
user_name = st.session_state.metadata.get('name', '')
if user_name:
    interaction_count = st.session_state.user_history.get('interaction_count', 0)
    if interaction_count == 0:
        greeting = f"Welcome to HealthVizor, {user_name}! 🌟"
    elif interaction_count < 5:
        greeting = f"Welcome back, {user_name}! 👋"
    else:
        greeting = f"Great to see you again, {user_name}! 💪"
    
    st.markdown(f"### {greeting}")
    if interaction_count > 0:
        st.markdown(f"*This is your #{interaction_count + 1} health analysis session*")
else:
    st.markdown("### Welcome to HealthVizor! 🌟")

# --- Personal Details: Compact Row ---
st.markdown("#### User Profile")
col1, col2, col3, col4, col5, col6 = st.columns(6)
with col1:
    st.session_state.metadata["name"] = st.text_input("Name", value=st.session_state.metadata.get('name', ''))
with col2:
    st.session_state.metadata["age"] = st.text_input("Age", value=str(st.session_state.metadata.get('age', '')))
with col3:
    st.session_state.metadata["gender"] = st.text_input("Gender", value=st.session_state.metadata.get('gender', ''))
with col4:
    st.session_state.metadata["height"] = st.text_input("Height", value=st.session_state.metadata.get('height', ''))
with col5:
    st.session_state.metadata["body_weight"] = st.text_input("Body Weight", value=st.session_state.metadata.get('body_weight', ''))
with col6:
    st.session_state.metadata["goal"] = st.text_input("Primary Goal", value=st.session_state.metadata.get('goal', ''))

# Personalization preferences section
st.markdown("#### Personalization Preferences")
col_pref1, col_pref2, col_pref3 = st.columns(3)
with col_pref1:
    st.session_state.personalization_prefs["communication_style"] = st.selectbox(
        "Communication Style",
        ["encouraging", "direct", "detailed"],
        index=["encouraging", "direct", "detailed"].index(st.session_state.personalization_prefs.get("communication_style", "encouraging"))
    )
with col_pref2:
    focus_options = ["supplements", "lifestyle", "nutrition", "biomarkers"]
    st.session_state.personalization_prefs["focus_areas"] = st.multiselect(
        "Primary Focus Areas",
        focus_options,
        default=st.session_state.personalization_prefs.get("focus_areas", [])
    )
with col_pref3:
    st.session_state.personalization_prefs["goal_tracking"] = st.checkbox(
        "Enable Goal Tracking", 
        value=st.session_state.personalization_prefs.get("goal_tracking", True)
    )

# --- User Conversation and Recommendations (Single Text Areas) ---
st.markdown("#### User Conversation (Q/A)")
st.text_area(
    "Paste or type the conversation (Q/A messages) here:",
    value=st.session_state.get("user_conversation", """Q: What are your main health goals?
A: I want to build lean muscle mass and increase my energy levels. I work in IT and often feel tired by evening.

Q: How is your current diet?
A: I eat mostly home-cooked meals - dal, rice, roti, vegetables. I have milk tea 3-4 times a day and occasionally eat out on weekends.

Q: What's your exercise routine?
A: I go to the gym 4 times a week for weight training, 45 minutes each session. I also play cricket on Sundays.

Q: Any health concerns?
A: I feel low energy in the afternoons and sometimes get muscle cramps after workouts. My family has a history of diabetes.

Q: Sleep pattern?
A: I sleep around 11:30 PM and wake up at 7 AM on weekdays. Sometimes I stay up late watching Netflix on weekends.

Q: Stress levels?
A: Work can be stressful with tight deadlines. I live with my parents in Mumbai, which is generally supportive.

Q: Any supplements currently?
A: I take whey protein post-workout and a basic multivitamin occasionally."""),
    key="user_conversation"
)

st.markdown("#### Biomarkers Data")
st.text_area(
    "Paste or type the biomarkers data here:",
    value=st.session_state.get("biomarkers_data", ""),
    key="biomarkers_data",
    help="Enter any relevant biomarker data, lab results, or health metrics"
)

st.markdown("#### Category Scores")
st.text_area(
    "Paste or type the HealthVizor category scores here:",
    value=st.session_state.get("category_scores", ""),
    key="category_scores",
    help="Enter category scores and health assessment data"
)

st.markdown("#### Recommendations")
st.text_area(
    "Paste or type the required recommendations here:",
    value=st.session_state.get("user_recommendations_text", """Focus on addressing Vitamin D deficiency which is affecting energy and immune function.
Improve HDL cholesterol through targeted nutrition and exercise modifications.
Optimize iron absorption with proper food combinations.
Manage afternoon energy dips through strategic meal timing and nutrient density.
Support muscle building goals with enhanced protein timing and micronutrient optimization.
Address stress management to improve cortisol patterns and sleep quality.
Incorporate anti-inflammatory foods suitable for Indian cuisine preferences.
Consider traditional Indian herbs and spices known for their health benefits."""),
    key="user_recommendations_text"
)

# --- Model Selection (Single Dropdown) ---
model_options = {
    "GPT-4.1": "gpt-4.1",
    "GPT-4.1 Mini": "gpt-4.1-mini",
    "GPT-4.1 Nano": "gpt-4.1-nano",
    "O4 Mini": "o4-mini",
    "O3 Mini": "o3-mini",
    "O3": "o3",
    "Gemini 1.5 Pro Latest": "gemini/gemini-1.5-pro-latest",
    "Gemini 2.0 Flash": "gemini/gemini-2.0-flash",
    "Gemini 2.0 Flash Exp": "gemini/gemini-2.0-flash-exp",
    "Gemini 2.0 Flash Lite Preview 02-05": "gemini/gemini-2.0-flash-lite-preview-02-05"
}
model_names = list(model_options.keys())

st.markdown("#### Model Selection")
selected_model_label = st.selectbox(
    "Select LLM Model",
    model_names,
    key="model_select_single"
)
selected_model = model_options[selected_model_label]
st.caption(f"**Exact model name:** `{selected_model}`")

if st.button("Generate Personalized Report", key="generate_single"):
    with st.spinner(f"Creating personalized health insights for {st.session_state.metadata.get('name', 'you')}..."):
        # Update interaction count
        st.session_state.user_history["interaction_count"] += 1
        st.session_state.user_history["last_interaction_date"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        
        personal_details = f"""
Name: {st.session_state.metadata.get('name', '')}
Age: {st.session_state.metadata.get('age', '')}
Gender: {st.session_state.metadata.get('gender', '')}
Height: {st.session_state.metadata.get('height', '')}
Body Weight: {st.session_state.metadata.get('body_weight', '')}
Primary Goal: {st.session_state.metadata.get('goal', '')}
Communication Preference: {st.session_state.personalization_prefs.get('communication_style', 'encouraging')}
Focus Areas: {', '.join(st.session_state.personalization_prefs.get('focus_areas', []))}
"""
        
        # Build user history context
        user_history_context = f"""
Interaction Count: {st.session_state.user_history.get('interaction_count', 0)}
Previous Reports Generated: {len(st.session_state.user_history.get('previous_reports', []))}
Preferred Supplements from Past: {', '.join(st.session_state.user_history.get('preferred_supplements', []))}
Lifestyle Preferences: {', '.join(st.session_state.user_history.get('lifestyle_preferences', []))}
Nutrition Preferences: {', '.join(st.session_state.user_history.get('nutrition_preferences', []))}
Last Interaction: {st.session_state.user_history.get('last_interaction_date', 'First time')}
"""
        
        prompt = PROMPT.format(
            onboarding_questions=st.session_state.user_conversation,
            personal_details=personal_details,
            biomarkers_data=st.session_state.biomarkers_data,
            category_scores=st.session_state.category_scores,
            recommendations=st.session_state.user_recommendations_text,
            user_history=user_history_context
        )
        # Create user context for personalized LLM call
        user_context = {
            "name": st.session_state.metadata.get('name', 'User'),
            "communication_style": st.session_state.personalization_prefs.get('communication_style', 'encouraging'),
            "focus_areas": st.session_state.personalization_prefs.get('focus_areas', []),
            "interaction_count": st.session_state.user_history.get('interaction_count', 1),
            "preferences_summary": f"Supplements: {', '.join(st.session_state.user_history.get('preferred_supplements', [])[:3])}; Lifestyle: {', '.join(st.session_state.user_history.get('lifestyle_preferences', [])[:3])}; Nutrition: {', '.join(st.session_state.user_history.get('nutrition_preferences', [])[:3])}"
        }
        
        messages = [{"role": "user", "content": prompt}]
        try:
            report = call_llm(selected_model, messages, HealthVizorResponse, user_context)
            st.session_state.report_single = report
            
            # Store report in history
            st.session_state.user_history["previous_reports"].append({
                "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                "model_used": selected_model,
                "report_summary": str(report)[:200] + "..." if len(str(report)) > 200 else str(report)
            })
            
            st.success(f"✨ Personalized analysis complete for {st.session_state.metadata.get('name', 'you')}!")
        except Exception as e:
            st.error(f"LLM call failed: {str(e)}")

if st.session_state.get("report_single"):
    report = st.session_state.report_single
    user_name = st.session_state.metadata.get('name', 'User')
    
    st.markdown(f"### 🎯 Your Comprehensive Health Report, {user_name}")
    
    # Add quick feedback buttons at the top
    col_feedback1, col_feedback2, col_feedback3, col_feedback4 = st.columns(4)
    with col_feedback1:
        if st.button("👍 Great recommendations!", key="feedback_great"):
            st.success("Thank you for your feedback!")
    with col_feedback2:
        if st.button("🎯 Very personalized", key="feedback_personal"):
            st.success("Wonderful! We'll keep it personal.")
    with col_feedback3:
        if st.button("💡 Want more details", key="feedback_details"):
            st.info("We'll provide more detailed analysis next time.")
    with col_feedback4:
        if st.button("🔄 Different approach", key="feedback_different"):
            st.info("We'll adjust our approach for future reports.")
    
    # Show the JSON response in a neat, expandable way
    with st.expander("📊 Raw JSON Response", expanded=False):
        st.json(report, expanded=False)

    # Handle both dict and pydantic object response
    if isinstance(report, dict) or hasattr(report, 'overall_health_summary'):
        
        # A) OVERALL HEALTH SUMMARY & PERSONALIZATION
        overall_summary = getattr(report, 'overall_health_summary', None) or report.get('overall_health_summary', '')
        if overall_summary:
            st.markdown(f"## 🌟 Overall Health Summary for {user_name}")
            st.markdown(overall_summary)
            
            # Top Priority Categories
            priority_categories = getattr(report, 'top_priority_categories', []) or report.get('top_priority_categories', [])
            if priority_categories:
                st.markdown("### 🎯 Your Top 3 Priority Areas")
                for i, category in enumerate(priority_categories, 1):
                    st.markdown(f"**{i}.** {category}")
        
        # B) CATEGORY LEVEL INSIGHTS & PERSONALIZATION
        category_insights = getattr(report, 'category_insights', []) or report.get('category_insights', [])
        if category_insights:
            st.markdown(f"## 🔍 Category Health Insights for {user_name}")
            for insight in category_insights:
                if isinstance(insight, dict):
                    category_name = insight.get('category_name', '')
                    score = insight.get('score', '')
                    summary = insight.get('summary', '')
                    impact_on_goals = insight.get('impact_on_goals', '')
                    improvement_importance = insight.get('improvement_importance', '')
                    what_to_continue = insight.get('what_to_continue', '')
                else:
                    category_name = getattr(insight, 'category_name', '')
                    score = getattr(insight, 'score', '')
                    summary = getattr(insight, 'summary', '')
                    impact_on_goals = getattr(insight, 'impact_on_goals', '')
                    improvement_importance = getattr(insight, 'improvement_importance', '')
                    what_to_continue = getattr(insight, 'what_to_continue', '')
                
                with st.expander(f"📊 {category_name} ({score})", expanded=True):
                    st.markdown(f"**Summary:** {summary}")
                    if impact_on_goals:
                        st.markdown(f"**Impact on Your Goals:** {impact_on_goals}")
                    if improvement_importance:
                        st.markdown(f"**Why This Matters:** {improvement_importance}")
                    if what_to_continue:
                        st.success(f"**Keep Doing:** {what_to_continue}")
        
        # C) BIOMARKER LEVEL FINDINGS & PERSONALIZATION
        biomarker_insights = getattr(report, 'biomarker_insights', []) or report.get('biomarker_insights', [])
        if biomarker_insights:
            st.markdown(f"## 🧬 Biomarker Analysis for {user_name}")
            
            # Group biomarkers by status
            red_biomarkers = []
            amber_biomarkers = []
            green_biomarkers = []
            
            for insight in biomarker_insights:
                if isinstance(insight, dict):
                    status = insight.get('status', '').lower()
                else:
                    status = getattr(insight, 'status', '').lower()
                
                if 'red' in status:
                    red_biomarkers.append(insight)
                elif 'amber' in status or 'yellow' in status:
                    amber_biomarkers.append(insight)
                else:
                    green_biomarkers.append(insight)
            
            # Display critical biomarkers first
            if red_biomarkers:
                st.markdown("### 🚨 Critical Priority Biomarkers")
                for insight in red_biomarkers:
                    display_biomarker_insight(insight, "🚨")
            
            if amber_biomarkers:
                st.markdown("### ⚠️ Monitor & Improve Biomarkers")
                for insight in amber_biomarkers:
                    display_biomarker_insight(insight, "⚠️")
            
            if green_biomarkers:
                st.markdown("### ✅ Optimal Biomarkers")
                for insight in green_biomarkers:
                    display_biomarker_insight(insight, "✅")
        
        # D) PERSONALIZED ACTION PLAN
        action_plan = getattr(report, 'action_plan', None) or report.get('action_plan', {})
        if action_plan:
            st.markdown(f"## 🎯 Your Personalized Action Plan, {user_name}")
            
            # Supplements
            supplements = getattr(action_plan, 'supplements', []) or action_plan.get('supplements', [])
            if supplements:
                st.markdown("### 💊 Your Supplement Protocol")
                
                # Show supplement schedule summary first
                schedule_summary = getattr(action_plan, 'supplement_schedule_summary', '') or action_plan.get('supplement_schedule_summary', '')
                if schedule_summary:
                    st.markdown("#### 📅 Daily Schedule Summary")
                    st.info(schedule_summary)
                
                # Display individual supplements
                for i, supp in enumerate(supplements):
                    display_supplement_recommendation(supp, i, user_name)
                
                st.warning("⚠️ These suggestions are for educational purposes only and do not constitute medical advice. Please consult a healthcare provider before beginning any supplement regimen.")
            
            # Nutrition
            nutrition_recs = getattr(action_plan, 'nutrition', []) or action_plan.get('nutrition', [])
            if nutrition_recs:
                st.markdown("### 🥗 Your Nutrition Protocol")
                for i, nutrition in enumerate(nutrition_recs):
                    display_nutrition_recommendation(nutrition, i, user_name)
            
            # Exercise & Lifestyle
            exercise_recs = getattr(action_plan, 'exercise_lifestyle', []) or action_plan.get('exercise_lifestyle', [])
            if exercise_recs:
                st.markdown("### 🏋️ Your Exercise & Lifestyle Protocol")
                for i, exercise in enumerate(exercise_recs):
                    display_exercise_recommendation(exercise, i, user_name)
            
            # 6-Month Timeline
            timeline = getattr(action_plan, 'six_month_timeline', []) or action_plan.get('six_month_timeline', [])
            if timeline:
                st.markdown("### 📅 Your 6-Month Journey Timeline")
                for plan in timeline:
                    display_monthly_plan(plan, user_name)
        
        # Disclaimer
        disclaimer = getattr(report, 'disclaimer', '') or report.get('disclaimer', '')
        if disclaimer:
            st.info(f"**Important Note for {user_name}:** {disclaimer}")
            
    # Show user's personalization summary
    if st.session_state.user_history.get("interaction_count", 0) > 1:
        with st.expander(f"📊 {user_name}'s Personalization Profile", expanded=False):
            col_stats1, col_stats2 = st.columns(2)
            with col_stats1:
                st.write(f"**Total Reports Generated:** {len(st.session_state.user_history.get('previous_reports', []))}")
                st.write(f"**Preferred Supplements:** {len(st.session_state.user_history.get('preferred_supplements', []))}")
                st.write(f"**Communication Style:** {st.session_state.personalization_prefs.get('communication_style', 'encouraging').title()}")
            with col_stats2:
                st.write(f"**Lifestyle Goals:** {len(st.session_state.user_history.get('lifestyle_preferences', []))}")
                st.write(f"**Nutrition Focus:** {len(st.session_state.user_history.get('nutrition_preferences', []))}")
                st.write(f"**Focus Areas:** {', '.join(st.session_state.personalization_prefs.get('focus_areas', []))}")

