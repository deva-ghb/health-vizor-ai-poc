from dotenv import load_dotenv
load_dotenv()

import json
import streamlit as st
from pydantic import BaseModel
from typing import Dict, List, Optional
from llm_utils import call_llm_with_fallback
from prompt import PROMPT
import os
import pandas as pd

st.set_page_config(page_title="HealthVizor", layout="wide")

# Initialize session state for metadata if not present
if 'metadata' not in st.session_state:
    st.session_state.metadata = {
        "name": "Suresh",
        "age": 50,
        "gender": "Male",
        "body_weight": "73",
        "height": "180",
        "body_fat_percentage": "19",
        "waist_circumference": "",
        "diet_type": "Non-Vegetarian",
        "known_medical_conditions": "One functioning Kidney",
        "open_to_supplements": "Yes",
        "current_supplements_medications": "Zinc, Magnesium, Berbering, B12, Lisinopril 5 mg",
        "activity_level": "CrossFit 4 sessions per week, 300 min total per week",
        "competitive_athlete": "Yes",
        "average_sleep_hours": "7",
        "wake_up_time": "7 AM",
        "smoker": "Yes",
        "sun_exposure": "<30 Min",
        "alcohol_intake": "5-10/week",
        "caffeine": "2+/day",
        "health_goals": ["Strength & Endurance", "Longevity"]
    }

# Ensure all required session state keys are initialized
def ensure_session_state():
    """Ensure all required session state variables are properly initialized"""
    if 'metadata' not in st.session_state:
        st.session_state.metadata = {
            "name": "Suresh",
            "age": 50,
            "gender": "Male",
            "body_weight": "73",
            "height": "180",
            "body_fat_percentage": "19",
            "waist_circumference": "",
            "diet_type": "Non-Vegetarian",
            "known_medical_conditions": "One functioning Kidney",
            "open_to_supplements": "Yes",
            "current_supplements_medications": "Zinc, Magnesium, Berbering, B12, Lisinopril 5 mg",
            "activity_level": "CrossFit 4 sessions per week, 300 min total per week",
            "competitive_athlete": "Yes",
            "average_sleep_hours": "7",
            "wake_up_time": "7 AM",
            "smoker": "Yes",
            "sun_exposure": "<30 Min",
            "alcohol_intake": "5-10/week",
            "caffeine": "2+/day",
            "health_goals": ["Strength & Endurance", "Longevity"]
        }

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



# Call the function to ensure initialization
ensure_session_state()

# Initialize additional session state variables
if 'biomarkers_data' not in st.session_state:
    st.session_state.biomarkers_data = """Haemoglobin: 15.6 g/dL (Clinical range: 13.5-18 g/dL, Optimal range: 12-15.5 g/dL, Flag: Yellow) - Categories: Cardiac Health, Cognitive Health, Sleep & Recovery, Strength & Endurance, Nutrient Status
WBC (White Blood Cells): 4960 /UL (Clinical range: 4000-11000 /UL, Optimal range: 4500-6500 /UL, Flag: Green) - Categories: Cardiac Health, Inflammation & Immunity
Neutrophils: 52.5% (Clinical range: 40-75%, Optimal range: 40-60%, Flag: Green) - Categories: Gut Health, Inflammation & Immunity
Lymphocytes: 33.6% (Clinical range: 20-45%, Optimal range: 25-45%, Flag: Green) - Categories: Gut Health, Inflammation & Immunity
Monocytes: 7.8% (Clinical range: 2-10%, Optimal range: 2-8%, Flag: Green) - Categories: Inflammation & Immunity
Eosinophils: 5.6% (Clinical range: 1-6%, Optimal range: 1-4%, Flag: Yellow) - Categories: Gut Health, Inflammation & Immunity
Basophils: 0.5% (Clinical range: 0-1%, Optimal range: 0-1%, Flag: Green) - Categories: Inflammation & Immunity
RBC (Red Blood Cells): 4.78 mil/L (Clinical range: 4.5-6.5 mil/L, Optimal range: 4.5-5.0 mil/L, Flag: Green) - Categories: Strength & Endurance, Cognitive Health, Cardiac Health, Nutrient Status
MCV: 95.3 fL (Clinical range: 76-96 fL, Optimal range: 85-92 fL, Flag: Yellow) - Categories: Cardiac Health, Cognitive Health, Strength & Endurance
MCH: 31.6 pg (Clinical range: 27-32 pg, Optimal range: 27-31 pg, Flag: Yellow) - Categories: Cardiac Health, Cognitive Health, Strength & Endurance
MCHC: 33.1 gm/dL (Clinical range: 30-35 gm/dL, Optimal range: 32-36 gm/dL, Flag: Green) - Categories: Cardiac Health, Cognitive Health, Strength & Endurance
Fasting Glucose: 105.44 mg/dL (Clinical range: 70-110 mg/dL, Optimal range: 70-90 mg/dL, Flag: Yellow) - Categories: Metabolic Health, Sleep & Recovery, Strength & Endurance
HbA1c: 6.0% (Clinical range: 4.5-6.2%, Optimal range: 4.5-5.5%, Flag: Yellow) - Categories: Hormone Health, Metabolic Health, Sleep & Recovery
Fasting Insulin: 2.6 µU/mL (Clinical range: 2.6-24.9 µU/mL, Optimal range: 3-8 µU/mL, Flag: Yellow) - Categories: Hormone Health, Metabolic Health, Sleep & Recovery
IGF-1: 200 ng/mL (Clinical range: 200-350 ng/mL, Optimal range: 200-350 ng/mL, Flag: Green) - Categories: Hormone Health, Strength & Endurance
Total Cholesterol: 250.0 mg/dL (Clinical range: 200-235 mg/dL, Optimal range: 150-180 mg/dL, Flag: Red) - Categories: Cardiac Health, Metabolic Health
LDL: 153 mg/dL (Clinical range: 30-100 mg/dL, Optimal range: 70-100 mg/dL, Flag: Red) - Categories: Cardiac Health, Metabolic Health
HDL: 61.8 mg/dL (Clinical range: 40-150 mg/dL, Optimal range: 60-90 mg/dL, Flag: Green) - Categories: Cardiac Health, Metabolic Health
Triglycerides: 69.2 mg/dL (Clinical range: 60-150 mg/dL, Optimal range: 60-100 mg/dL, Flag: Green) - Categories: Cardiac Health, Hormone Health, Metabolic Health
ESR: 10 mm/hr (Clinical range: 3-15 mm/hr, Optimal range: < 10 mm/hr, Flag: Yellow) - Categories: Metabolic Health
Bilirubin (Total): 0.79 mg/dL (Clinical range: 0.1-1.2 mg/dL, Optimal range: < 1.0 mg/dL, Flag: Green) - Categories: Gut Health, Sleep & Recovery
Albumin: 4.4 g/dL (Clinical range: 3.5-5 g/dL, Optimal range: 4.0-5.0 g/dL, Flag: Green) - Categories: Gut Health, Inflammation & Immunity, Sleep & Recovery
Total Protein: 7.69 g/dL (Clinical range: 6.0-8.2 g/dL, Optimal range: 6.5-7.8 g/dL, Flag: Green) - Categories: Gut Health, Inflammation & Immunity, Sleep & Recovery
BUN: 15.3 mg/dL (Clinical range: 13-43 mg/dL, Optimal range: 10-18 mg/dL, Flag: Green) - Categories: Cardiac Health, Cognitive Health, Inflammation & Immunity, Sleep & Recovery
Creatinine: 1.3 mg/dL (Clinical range: 0.7-1.1 mg/dL, Optimal range: 0.8-1.1 mg/dL, Flag: Red) - Categories: Cardiac Health, Cognitive Health, Hormone Health, Inflammation & Immunity, Sleep & Recovery, Strength & Endurance
eGFR: 51.5 ml/min (Clinical range: >90 ml/min, Optimal range: >90 ml/min, Flag: Red) - Categories: Cardiac Health, Cognitive Health, Hormone Health, Inflammation & Immunity, Sleep & Recovery, Strength & Endurance
ALT: 47.4 U/L (Clinical range: 10-26 U/L, Optimal range: 10-26 U/L, Flag: Red) - Categories: Sleep & Recovery, Gut Health, Nutrient Status
AST: 36 U/L (Clinical range: 10-26 U/L, Optimal range: 10-26 U/L, Flag: Red) - Categories:
ALP: 45.5 U/L (Clinical range: 50-100 U/L, Optimal range: 50-100 U/L, Flag: Red) - Categories: Sleep & Recovery, Gut Health, Nutrient Status
Uric Acid: 4.82 mg/dL (Clinical range: 3.5-7.2 mg/dL, Optimal range: 4.0-6.0 mg/dL, Flag: Green) - Categories: Inflammation & Immunity, Sleep & Recovery, Strength & Endurance
Sodium: 138.63 mmol/L (Clinical range: 136-145 mmol/L, Optimal range: 136-142 mmol/L, Flag: Green) - Categories: Sleep & Recovery
Potassium: 4.98 mmol/L (Clinical range: 3.5-5.1 mmol/L, Optimal range: 3.9-4.5 mmol/L, Flag: Green) - Categories: Sleep & Recovery
Chloride: 109.2 mmol/L (Clinical range: 98-107 mmol/L, Optimal range: 98-106 mmol/L, Flag: Red) - Categories:
TSH: 2.41 µIU/mL (Clinical range: 0.4-4.2 µIU/mL, Optimal range: 0.5-2.5 µIU/mL, Flag: Green) - Categories: Cognitive Health, Hormone Health, Metabolic Health
Free T3: 3.09 pg/mL (Clinical range: 1.17-3.17 pg/mL, Optimal range: 3.0-4.2 pg/mL, Flag: Green) - Categories: Cognitive Health, Hormone Health, Metabolic Health, Strength & Endurance
Free T4: 1.13 ng/dL (Clinical range: 0.70-1.48 ng/dL, Optimal range: 1.0-1.5 ng/dL, Flag: Green) - Categories: Cognitive Health, Hormone Health, Metabolic Health, Strength & Endurance
Total Testosterone: 536 ng/dL (Clinical range: 241-827 ng/dL, Optimal range: 600-900 ng/dL, Flag: Yellow) - Categories: Hormone Health, Inflammation & Immunity, Metabolic Health
SHBG: 34.1 nmol/L (Clinical range: 13-71 nmol/L, Optimal range: 20-40 nmol/L, Flag: Green) - Categories: Hormone Health, Metabolic Health
Cortisol (AM): 11.4 µg/dL (Clinical range: 3.7-19.4 µg/dL, Optimal range: 10-18 µg/dL, Flag: Green) - Categories: Cardiac Health, Cognitive Health, Hormone Health, Inflammation & Immunity, Sleep & Recovery, Strength & Endurance
Vitamin B12: 454 pg/mL (Clinical range: 187-883 pg/mL, Optimal range: 400-800 pg/mL, Flag: Green) - Categories: Cognitive Health, Gut Health, Inflammation & Immunity, Sleep & Recovery
Iron: 122.5 µg/dL (Clinical range: 65-175 µg/dL, Optimal range: 80-120 µg/dL, Flag: Yellow) - Categories: Cognitive Health, Gut Health, Inflammation & Immunity, Sleep & Recovery, Strength & Endurance
Ferritin: 82.23 ng/mL (Clinical range: 22-322 ng/mL, Optimal range: 50-150 ng/mL, Flag: Green) - Categories: Cognitive Health, Gut Health, Inflammation & Immunity, Sleep & Recovery, Strength & Endurance
TIBC: 319.50 µg/dL (Clinical range: 250-450 µg/dL, Optimal range: 250-350 µg/dL, Flag: Green) - Categories: Cognitive Health, Strength & Endurance
Transferrin Saturation: 38.98% (Clinical range: 20-40%, Optimal range: 25-40%, Flag: Green) - Categories: Nutrient Status, Strength & Endurance, Cognitive Health
Homocysteine: 20 µmol/L (Clinical range: 5.4-16.2 µmol/L, Optimal range: 6-8 µmol/L, Flag: Red) - Categories: Cardiac Health, Cognitive Health, Gut Health, Inflammation & Immunity, Sleep & Recovery
Free Testosterone: 17.8 pg/ml (Clinical range: 15-50 pg/ml, Optimal range: 30-50 pg/ml, Flag: Yellow) - Categories: Sleep & recovery, Hormone Health, Metabolic Health
DHEA-S: 102 µg/dL (Clinical range: 80-560 µg/dL, Optimal range: 280-400 µg/dL, Flag: Yellow) - Categories: Cardiac Health, Hormone Health, Inflammation & Immunity, Sleep & Recovery
Anti-TPO: 4.49 IU/mL (Clinical range: 2-5.61 IU/mL, Optimal range: < 9 IU/mL, Flag: Green) - Categories: Gut Health, Inflammation & Immunity
ApoA1: 150 mg/dL (Clinical range: >140 mg/dL, Optimal range: >140 mg/dL, Flag: Green) - Categories: Metabolic Health, Cardiac Health
ApoB: 91 mg/dL (Clinical range: 50-100 mg/dL, Optimal range: 60-90 mg/dL, Flag: Yellow) - Categories: Metabolic Health, Cardiac Health, Cognitive Health
Lp(a): 20 mg/dL (Clinical range: <20 mg/dL, Optimal range: <20 mg/dL, Flag: Yellow) - Categories: Metabolic Health, Cardiac Health
hs-CRP: 0.41 mg/dL (Clinical range: 1-3 mg/dL, Optimal range: <0.5 mg/dL, Flag: Green) - Categories: Strength & Endurance, Cardiac Health, Cognitive Health, Inflammation & Immunity
Vitamin D: 42 ng/mL (Clinical range: 20-100 ng/mL, Optimal range: 40-60 ng/mL, Flag: Green) - Categories: Cognitive Health, Inflammation & Immunity, Gut Health, Nutrient Status
Anti-Thyroglobulin: 3 IU/mL (Clinical range: <4 IU/mL, Optimal range: <4 IU/mL, Flag: Green) - Categories: Gut Health
Zinc: 90 µg/dL (Clinical range: 70-100 µg/dL, Optimal range: 70-110 µg/dL, Flag: Green) - Categories: Sleep & Recovery, Gut Health, Nutrient Status, Gut Health
Magnesium: 2.11 mg/dL (Clinical range: 1.7-2.3 mg/dL, Optimal range: 2.0-2.4 mg/dL, Flag: Green) - Categories: Strength & Endurance, Sleep & Recovery, Cognitive Health, Nutrient Status
Vitamin B6: 40 ng/mL (Clinical range: 20-80 ng/mL, Optimal range: 30-80 ng/mL, Flag: Green) - Categories: Nutrient Status, Cognitive Health
CO2(Bicarbonate): 22 mmol/L (Clinical range: 22-26 mmol/L, Optimal range: 22-26 mmol/L, Flag: Green) - Categories: Metabolic Health
Anion Gap: 10 mmol/L (Clinical range: 10-14 mmol/L, Optimal range: 10-14 mmol/L, Flag: Green) - Categories: Metabolic Health
"""
if 'category_scores' not in st.session_state:
    st.session_state.category_scores = """Metabolic Health: 69/100 - Needs improvement in metabolic health. 
    Strength & Endurance: 85/100 - Optimal strength and endurance levels. 
    Sleep & Recovery: 65/100 - Needs improvement in sleep and recovery. 
    Cognitive Health: 75/100 - Needs improvement in cognitive health. 
    Cardiac Health: 60/100 - Needs improvement in cardiac health. 
    Hormone Health: 70/100 - Needs improvement in hormone health. 
    Inflammation & Immunity: 85/100 - Optimal inflammation and immunity status. 
    Gut Health: 85/100 - Optimal gut health. 
    Nutrient Status: 90/100 - Excellent nutritional status."""

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



from pydantic import Field

# LiteLLM-compatible Pydantic models with non-empty object schemas for Gemini/VertexAI

class SupplementRecommendation(BaseModel):
    supplement_name: str = Field(..., description="Name of the supplement being recommended")
    rationale: str = Field(..., description="Rationale for recommending this supplement based on user profile and biomarkers")
    dosage: str = Field(..., description="Recommended dose using educational language (e.g., 'Studies suggest 500mg may support...')")
    timing: str = Field(..., description="When to take (morning, evening, with meals, etc.)")
    food_timing: str = Field(..., description="Before/with/after food instructions")
    purpose: str = Field(..., description="Purpose and how it helps the user - what it does for you")
    biomarker_connection: str = Field(..., description="How this connects to user's biomarker data and health goals")
    longevity_performance_benefit: str = Field(..., description="How this supports longevity and performance goals")
    duration: str = Field(..., description="How long to take the supplement")
    retest_timing: str = Field(..., description="When to retest biomarkers")
    evidence_source: str = Field(..., description="Scientific evidence source from approved knowledge sources")
    cautions: Optional[str] = Field(None, description="Side effects, cautions, or things to avoid")
    interactions: Optional[str] = Field(None, description="Any interactions with other supplements or medications")
    indian_availability: Optional[str] = Field(None, description="Notes on availability in India or Indian brands if relevant")

class NutritionRecommendation(BaseModel):
    nutrition_name: str = Field(..., description="Name of the nutrition recommendation")
    rationale: str = Field(..., description="Why this is recommended based on biomarker data and personalization data")
    priority_rank: int = Field(..., description="Priority ranking (1-5)")
    evidence_strength: str = Field(..., description="Strength of evidence (High/Medium/Low)")
    biomarker_connection: str = Field(..., description="How this connects to specific biomarker data")
    implementation_tips: List[str] = Field(default_factory=list, description="3-4 practical tips for implementation with Indian context")
    foods_to_include: List[str] = Field(default_factory=list, description="Specific foods to eat more of (Indian foods when possible)")
    foods_to_avoid: List[str] = Field(default_factory=list, description="Foods to avoid or limit")
    meal_timing_guidance: Optional[str] = Field(None, description="Meal timing recommendations if relevant")
    indian_food_examples: List[str] = Field(default_factory=list, description="Examples using Indian cuisine and locally available foods")
    female_specific_notes: Optional[str] = Field(None, description="Special considerations for female users based on cycle status")
    evidence_source: str = Field(..., description="Scientific evidence source with links")

class ExerciseRecommendation(BaseModel):
    exercise_name: str = Field(..., description="Name of the exercise/lifestyle recommendation")
    rationale: str = Field(..., description="Why this is recommended based on biomarker data and personalization data")
    workout_type: str = Field(..., description="Type of workout (strength, cardio, flexibility, etc.)")
    frequency: str = Field(..., description="How often per week")
    duration: str = Field(..., description="Duration per session")
    intensity: str = Field(..., description="Intensity level recommendations")
    volume: str = Field(..., description="Volume recommendations")
    rest_periods: str = Field(..., description="Rest period recommendations")
    biomarker_connection: str = Field(..., description="How this connects to biomarker data and goals")
    current_optimization: Optional[str] = Field(None, description="What user is doing right and how to optimize further")
    athlete_specific_notes: Optional[str] = Field(None, description="Training periodization or protocols for competitive athletes")
    female_specific_notes: Optional[str] = Field(None, description="Recommendations based on cycle status for female users")
    no_intervention_note: Optional[str] = Field(None, description="Note if no intervention needed (e.g., 'well-balanced, no critical changes needed')")
    evidence_source: str = Field(..., description="Scientific evidence source with links")

class CategoryInsight(BaseModel):
    category_name: str = Field(..., description="Name of the health category with emoji (e.g., '💪 Strength & Endurance')")
    score: str = Field(..., description="Category score (e.g., '75/100')")
    summary: str = Field(..., description="Comprehensive 3-4 sentence summary explaining the category's current state, key biomarker patterns, and overall assessment. Should identify multi-marker patterns (e.g., HPA axis fatigue) and explain the functional medicine significance")
    whats_working_well: Optional[str] = Field(None, description="Specific biomarkers and values that are optimal, with exact values and why they support the user's goals")
    what_needs_work: Optional[str] = Field(None, description="Specific biomarkers that are amber/red with exact values and status, explaining the functional implications")
    behavioral_contributors: List[str] = Field(default_factory=list, description="Specific lifestyle factors from user metadata that contribute to this category's performance")
    priority_actions: List[str] = Field(default_factory=list, description="Specific, actionable interventions to improve this category (supplements, lifestyle changes, etc.)")
    how_this_links_to_goals: Optional[str] = Field(None, description="Clear explanation of how optimizing this category directly impacts the user's stated health goals and lifestyle")
    relevance_to_goals: str = Field(..., description="Why this category matters for the user's goals")
    impact_on_goals: str = Field(..., description="How this category impacts user's goals")
    performance_longevity_impact: str = Field(..., description="Why this score matters for performance or longevity")
    biomarker_connections: List[str] = Field(default_factory=list, description="Connected biomarkers")
    interrelated_categories: List[str] = Field(default_factory=list, description="Other categories that are interrelated")
    what_to_continue: Optional[str] = Field(None, description="What's working well to continue (for green categories)")

class BiomarkerInsight(BaseModel):
    biomarker_name: str = Field(..., description="Name of the biomarker")
    status: str = Field(..., description="Status (Red/Amber/Green/Optimal)")
    current_value: str = Field(..., description="Current biomarker value")
    reference_range: str = Field(..., description="Normal reference range")
    what_it_is_why_matters: str = Field(..., description="Explain the biomarker in plain language (2-3 sentences). What does it measure? Why is it important for the user's health goals, longevity, or performance?")
    your_result: str = Field(..., description="State the user's actual value, whether it is in the optimal, yellow, amber, or red range, and what that means for their health")
    likely_contributors: str = Field(..., description="Use user metadata and known lifestyle associations to infer what may be contributing to the value. Be explicit and tie it back to the user's behaviors or reported symptoms")
    health_implications: str = Field(..., description="Explain what happens if this marker remains out of range. Use credible, non-alarmist language to outline risks")
    recommended_next_steps: str = Field(..., description="Suggest 1-2 specific, actionable interventions that can help. Make it practical and tied to this biomarker")
    deviation_severity: Optional[str] = Field(None, description="Mild/Moderate/Severe based on % deviation from optimal")
    what_to_continue: Optional[str] = Field(None, description="What's working well (for Green/Optimal)")
    trend_analysis: Optional[str] = Field(None, description="Trend compared to past data if available")
    related_biomarkers: List[str] = Field(default_factory=list, description="Other biomarkers that are related or show consistent patterns")
    evidence_source: str = Field(..., description="Scientific evidence source")

class TopPriority(BaseModel):
    priority_number: int = Field(..., description="Priority ranking (1, 2, or 3)")
    priority_name: str = Field(..., description="Name of the priority area (e.g., 'Rebuild Adrenal Resilience')")
    detailed_narrative: str = Field(default="", description="Comprehensive narrative paragraph integrating biomarker evidence, lifestyle factors, functional medicine insights, and impact on user's goals")
    # Legacy fields for backward compatibility
    biomarker_evidence: List[str] = Field(default_factory=list, description="Specific biomarkers and their values that support this priority")
    lifestyle_evidence: List[str] = Field(default_factory=list, description="User's lifestyle factors, symptoms, or behaviors that support this priority")
    functional_significance: str = Field(default="", description="Explanation of the functional medicine significance and patterns identified")
    impact_statement: str = Field(default="", description="Why addressing this priority is essential for the user's goals, energy, health, etc.")

class MonthlyPlan(BaseModel):
    month_range: str = Field(..., description="Month range (e.g., 'Months 0-2')")
    focus_areas: List[str] = Field(default_factory=list, description="Key focus areas for this period")
    supplement_adjustments: List[str] = Field(default_factory=list, description="Supplement plan for this period")
    nutrition_focus: List[str] = Field(default_factory=list, description="Nutrition focus for this period")
    exercise_goals: List[str] = Field(default_factory=list, description="Exercise goals for this period")
    lifestyle_targets: List[str] = Field(default_factory=list, description="Lifestyle targets")
    retest_schedule: List[str] = Field(default_factory=list, description="When to retest biomarkers")

class ActionPlan(BaseModel):
    supplements: List[SupplementRecommendation] = Field(default_factory=list, description="Supplement recommendations (max 5, no duplicates)")
    supplement_schedule_summary: str = Field(..., description="Daily supplement schedule organized by time of day for easy reading")
    supplement_disclaimer: str = Field(default="These suggestions are for educational purposes only and do not constitute medical advice. Please consult a healthcare provider before beginning any supplement regimen.", description="Supplement disclaimer")
    nutrition: List[NutritionRecommendation] = Field(default_factory=list, description="Nutrition recommendations (max 5, ranked by priority)")
    exercise_lifestyle: List[ExerciseRecommendation] = Field(default_factory=list, description="Exercise and lifestyle recommendations (max 5)")
    six_month_timeline: List[MonthlyPlan] = Field(default_factory=list, description="6-month action plan timeline with logical progression")

class HealthVizorResponse(BaseModel):
    # A) Overall Health Summary & Personalization
    overall_health_summary: str = Field(..., description="Warm, celebratory 5-6 sentence paragraph in second person that commends the user for taking charge of their health, personalizes using age, gender, health goals, habits, or activity level, reflects overall impression based on biomarkers, reinforces hope and actionability")
    congratulations_message: str = Field(..., description="Congratulate user on taking this step")
    wins_to_celebrate: List[str] = Field(default_factory=list, description="What's Working Well - highlight key green biomarkers and high-performing categories, reinforce positive behaviors")
    what_to_continue: List[str] = Field(default_factory=list, description="What the user should continue doing - encourage to continue or double down on these habits")
    what_needs_work: List[str] = Field(default_factory=list, description="What Needs Attention - flag notable amber/red biomarkers or risk patterns with constructive language")
    top_3_priorities_detailed: List[TopPriority] = Field(default_factory=list, description="Detailed breakdown of top 3 health priorities with comprehensive narrative format integrating biomarker evidence, lifestyle factors, and impact statements")
    biomarker_snapshot: str = Field(..., description="Simple count of red, amber, and green biomarkers with encouraging message (e.g., 'You have 4 red, 6 amber, and 12 green biomarkers. That's a strong foundation — and a great place to start.')")
    goal_relevance: str = Field(..., description="How this relates to the user's goals")
    longevity_performance_impact: str = Field(..., description="What this means for overall longevity and performance")

    # B) Category Level Insights & Personalization
    category_insights: List[CategoryInsight] = Field(default_factory=list, description="Detailed insights for each health category")

    # C) Biomarker Level Findings & Personalization
    biomarker_insights: List[BiomarkerInsight] = Field(default_factory=list, description="Detailed insights for each biomarker")
    biomarker_pattern_analysis: Optional[str] = Field(None, description="Analysis of biomarker patterns across multiple systems")

    # D) Personalized Action Plan
    action_plan: ActionPlan = Field(default_factory=ActionPlan, description="Comprehensive personalized action plan")

    # Escalation flags
    escalation_needed: bool = Field(default=False, description="Whether escalation is needed (under 18, pregnant, critical biomarkers)")
    escalation_reason: Optional[str] = Field(None, description="Reason for escalation if needed")

    # Disclaimer
    disclaimer: str = Field(
        default="These recommendations are for educational purposes only and do not constitute medical advice. Please consult a healthcare provider before starting any new regimen.",
        description="Medical disclaimer"
    )

# Helper functions for displaying structured data
def display_category_insight(insight, user_name="User"):
    if isinstance(insight, dict):
        category_name = insight.get('category_name', '')
        score = insight.get('score', '')
        summary = insight.get('summary', '')
        whats_working_well = insight.get('whats_working_well', '')
        what_needs_work = insight.get('what_needs_work', insight.get('what_needs_attention', ''))  # New field with fallback
        behavioral_contributors = insight.get('behavioral_contributors', [])
        priority_actions = insight.get('priority_actions', [])  # New field
        how_this_links_to_goals = insight.get('how_this_links_to_goals', '')  # New field
        relevance_to_goals = insight.get('relevance_to_goals', '')
        impact_on_goals = insight.get('impact_on_goals', '')
        performance_longevity_impact = insight.get('performance_longevity_impact', '')
        biomarker_connections = insight.get('biomarker_connections', [])
        interrelated_categories = insight.get('interrelated_categories', [])
        what_to_continue = insight.get('what_to_continue', '')
    else:
        category_name = getattr(insight, 'category_name', '')
        score = getattr(insight, 'score', '')
        summary = getattr(insight, 'summary', '')
        whats_working_well = getattr(insight, 'whats_working_well', '')
        what_needs_work = getattr(insight, 'what_needs_work', getattr(insight, 'what_needs_attention', ''))
        behavioral_contributors = getattr(insight, 'behavioral_contributors', [])
        priority_actions = getattr(insight, 'priority_actions', [])
        how_this_links_to_goals = getattr(insight, 'how_this_links_to_goals', '')
        relevance_to_goals = getattr(insight, 'relevance_to_goals', '')
        impact_on_goals = getattr(insight, 'impact_on_goals', '')
        performance_longevity_impact = getattr(insight, 'performance_longevity_impact', '')
        biomarker_connections = getattr(insight, 'biomarker_connections', [])
        interrelated_categories = getattr(insight, 'interrelated_categories', [])
        what_to_continue = getattr(insight, 'what_to_continue', '')

    # Create title with score and status indicator
    title = f"🎯 {category_name}"
    if score:
        score_num = int(score.split('/')[0]) if '/' in score else 0
        if score_num >= 80:
            title += f" - {score} ✅"
        elif score_num >= 60:
            title += f" - {score} ⚠️"
        else:
            title += f" - {score} 🚨"

    with st.expander(title, expanded=False):
        # Summary - Main overview
        if summary:
            st.markdown(f"**Summary:** {summary}")

        # What's working well
        if whats_working_well:
            st.success(f"**What's Working Well**\n{whats_working_well}")

        # What needs work (new enhanced field)
        if what_needs_work:
            st.warning(f"**What Needs Work**\n{what_needs_work}")

        # Behavioral contributors
        if behavioral_contributors:
            st.markdown("**Behavioral Contributors**")
            for contributor in behavioral_contributors:
                st.markdown(f"• {contributor}")

        # Priority actions (new field)
        if priority_actions:
            st.markdown("**Priority Actions**")
            for action in priority_actions:
                st.markdown(f"• {action}")

        # How this links to goals (new enhanced field)
        if how_this_links_to_goals:
            st.info(f"**How this Links to Your Goals:**\n{how_this_links_to_goals}")

        # Legacy fields for backward compatibility
        if relevance_to_goals and not how_this_links_to_goals:
            st.info(f"**Why This Matters for {user_name}:** {relevance_to_goals}")

        if impact_on_goals:
            st.markdown(f"**🎯 Impact on Your Goals:** {impact_on_goals}")

        # Performance/longevity impact
        if performance_longevity_impact:
            st.markdown(f"**🏃‍♂️ Performance & Longevity Impact:** {performance_longevity_impact}")

        # Connected biomarkers
        if biomarker_connections:
            st.markdown(f"**🔬 Connected Biomarkers:** {', '.join(biomarker_connections)}")

        # Interrelated categories
        if interrelated_categories:
            st.markdown(f"**🔗 Related Categories:** {', '.join(interrelated_categories)}")

        # What to continue
        if what_to_continue:
            st.success(f"**Keep Doing:** {what_to_continue}")

def display_top_priority_detailed(priority, user_name="User"):
    """Display enhanced top 3 priorities with detailed breakdown"""
    if isinstance(priority, dict):
        priority_number = priority.get('priority_number', 0)
        priority_name = priority.get('priority_name', '')
        detailed_narrative = priority.get('detailed_narrative', '')
        # Legacy fields for backward compatibility
        biomarker_evidence = priority.get('biomarker_evidence', [])
        lifestyle_evidence = priority.get('lifestyle_evidence', [])
        functional_significance = priority.get('functional_significance', '')
        impact_statement = priority.get('impact_statement', '')
    else:
        priority_number = getattr(priority, 'priority_number', 0)
        priority_name = getattr(priority, 'priority_name', '')
        detailed_narrative = getattr(priority, 'detailed_narrative', '')
        # Legacy fields for backward compatibility
        biomarker_evidence = getattr(priority, 'biomarker_evidence', [])
        lifestyle_evidence = getattr(priority, 'lifestyle_evidence', [])
        functional_significance = getattr(priority, 'functional_significance', '')
        impact_statement = getattr(priority, 'impact_statement', '')

    with st.expander(f"🎯 {priority_number}. {priority_name}", expanded=True):
        # New detailed narrative format (preferred)
        if detailed_narrative:
            st.markdown(detailed_narrative)
        else:
            # Legacy format for backward compatibility
            # Biomarker evidence
            if biomarker_evidence:
                st.markdown("**Biomarker Evidence:**")
                for evidence in biomarker_evidence:
                    st.markdown(f"• {evidence}")

            # Lifestyle evidence
            if lifestyle_evidence:
                st.markdown("**Lifestyle Evidence:**")
                for evidence in lifestyle_evidence:
                    st.markdown(f"• {evidence}")

            # Functional significance
            if functional_significance:
                st.info(f"**Functional Significance:** {functional_significance}")

            # Impact statement
            if impact_statement:
                st.success(f"**Why This Matters:** {impact_statement}")

def display_biomarker_insight(insight, icon):
    if isinstance(insight, dict):
        biomarker_name = insight.get('biomarker_name', '')
        current_value = insight.get('current_value', '')
        reference_range = insight.get('reference_range', '')
        what_it_is_why_matters = insight.get('what_it_is_why_matters', '')
        your_result = insight.get('your_result', '')
        likely_contributors = insight.get('likely_contributors', '')
        health_implications = insight.get('health_implications', '')
        recommended_next_steps = insight.get('recommended_next_steps', '')
        deviation_severity = insight.get('deviation_severity', '')
        what_to_continue = insight.get('what_to_continue', '')
        trend_analysis = insight.get('trend_analysis', '')
        related_biomarkers = insight.get('related_biomarkers', [])
        evidence_source = insight.get('evidence_source', '')

        # Fallback to old field names for backward compatibility
        if not what_it_is_why_matters:
            what_it_is_why_matters = insight.get('health_impact', '')
        if not your_result:
            your_result = insight.get('goal_connection', '')
        if not likely_contributors:
            lifestyle_contributors = insight.get('lifestyle_contributors', [])
            likely_contributors = '; '.join(lifestyle_contributors) if lifestyle_contributors else ''
        if not health_implications:
            health_implications = insight.get('consequences_if_ignored', '')
        if not recommended_next_steps:
            recommended_next_steps = insight.get('longevity_performance_impact', '')
    else:
        biomarker_name = getattr(insight, 'biomarker_name', '')
        current_value = getattr(insight, 'current_value', '')
        reference_range = getattr(insight, 'reference_range', '')
        what_it_is_why_matters = getattr(insight, 'what_it_is_why_matters', '')
        your_result = getattr(insight, 'your_result', '')
        likely_contributors = getattr(insight, 'likely_contributors', '')
        health_implications = getattr(insight, 'health_implications', '')
        recommended_next_steps = getattr(insight, 'recommended_next_steps', '')
        deviation_severity = getattr(insight, 'deviation_severity', '')
        what_to_continue = getattr(insight, 'what_to_continue', '')
        trend_analysis = getattr(insight, 'trend_analysis', '')
        related_biomarkers = getattr(insight, 'related_biomarkers', [])
        evidence_source = getattr(insight, 'evidence_source', '')

    title = f"{icon} {biomarker_name}: {current_value}"
    if deviation_severity:
        title += f" ({deviation_severity})"

    with st.expander(title, expanded=False):
        if reference_range:
            st.markdown(f"**Reference Range:** {reference_range}")

        if what_it_is_why_matters:
            st.markdown(f"**What it is & why it matters:** {what_it_is_why_matters}")

        if your_result:
            st.markdown(f"**Your result:** {your_result}")

        if likely_contributors:
            st.markdown(f"**Likely contributors:** {likely_contributors}")

        if health_implications:
            st.warning(f"**Health implications:** {health_implications}")

        if recommended_next_steps:
            st.markdown(f"**Recommended next steps:** {recommended_next_steps}")

        if trend_analysis:
            st.info(f"**Trend Analysis:** {trend_analysis}")

        if related_biomarkers:
            st.markdown(f"**Related Biomarkers:** {', '.join(related_biomarkers)}")

        if what_to_continue:
            st.success(f"**Keep Doing:** {what_to_continue}")

        if evidence_source:
            st.caption(f"**Evidence:** {evidence_source}")

def display_supplement_recommendation(supp, index, user_name):
    if isinstance(supp, dict):
        supp_name = supp.get('supplement_name', '')
        rationale = supp.get('rationale', '')
        dosage = supp.get('dosage', '')
        timing = supp.get('timing', '')
        food_timing = supp.get('food_timing', '')
        purpose = supp.get('purpose', '')
        biomarker_connection = supp.get('biomarker_connection', '')
        longevity_performance_benefit = supp.get('longevity_performance_benefit', '')
        duration = supp.get('duration', '')
        retest_timing = supp.get('retest_timing', '')
        evidence_source = supp.get('evidence_source', '')
        cautions = supp.get('cautions', '')
        interactions = supp.get('interactions', '')
        indian_availability = supp.get('indian_availability', '')
    else:
        supp_name = getattr(supp, 'supplement_name', '')
        rationale = getattr(supp, 'rationale', '')
        dosage = getattr(supp, 'dosage', '')
        timing = getattr(supp, 'timing', '')
        food_timing = getattr(supp, 'food_timing', '')
        purpose = getattr(supp, 'purpose', '')
        biomarker_connection = getattr(supp, 'biomarker_connection', '')
        longevity_performance_benefit = getattr(supp, 'longevity_performance_benefit', '')
        duration = getattr(supp, 'duration', '')
        retest_timing = getattr(supp, 'retest_timing', '')
        evidence_source = getattr(supp, 'evidence_source', '')
        cautions = getattr(supp, 'cautions', '')
        interactions = getattr(supp, 'interactions', '')
        indian_availability = getattr(supp, 'indian_availability', '')

    with st.expander(f"💊 {index + 1}. {supp_name}", expanded=False):
        if rationale:
            st.markdown(f"**{rationale}**")
        st.markdown(f"**Dosage:** {dosage}")
        st.markdown(f"**Timing:** {timing}")
        st.markdown(f"**With Food:** {food_timing}")
        st.markdown(f"**Purpose:** {purpose}")
        st.markdown(f"**Connection to Your Data:** {biomarker_connection}")
        if longevity_performance_benefit:
            st.markdown(f"**Longevity & Performance Benefits:** {longevity_performance_benefit}")
        st.markdown(f"**Duration:** {duration}")
        st.markdown(f"**Retest:** {retest_timing}")
        if indian_availability:
            st.info(f"**Indian Availability:** {indian_availability}")
        if cautions:
            st.warning(f"**Cautions:** {cautions}")
        if interactions:
            st.warning(f"**Interactions:** {interactions}")
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
        biomarker_connection = nutrition.get('biomarker_connection', '')
        implementation_tips = nutrition.get('implementation_tips', [])
        foods_to_include = nutrition.get('foods_to_include', [])
        foods_to_avoid = nutrition.get('foods_to_avoid', [])
        meal_timing_guidance = nutrition.get('meal_timing_guidance', '')
        indian_food_examples = nutrition.get('indian_food_examples', [])
        female_specific_notes = nutrition.get('female_specific_notes', '')
        evidence_source = nutrition.get('evidence_source', '')
    else:
        nutrition_name = getattr(nutrition, 'nutrition_name', '')
        rationale = getattr(nutrition, 'rationale', '')
        priority_rank = getattr(nutrition, 'priority_rank', 0)
        evidence_strength = getattr(nutrition, 'evidence_strength', '')
        biomarker_connection = getattr(nutrition, 'biomarker_connection', '')
        implementation_tips = getattr(nutrition, 'implementation_tips', [])
        foods_to_include = getattr(nutrition, 'foods_to_include', [])
        foods_to_avoid = getattr(nutrition, 'foods_to_avoid', [])
        meal_timing_guidance = getattr(nutrition, 'meal_timing_guidance', '')
        indian_food_examples = getattr(nutrition, 'indian_food_examples', [])
        female_specific_notes = getattr(nutrition, 'female_specific_notes', '')
        evidence_source = getattr(nutrition, 'evidence_source', '')

    with st.expander(f"🥗 Priority #{priority_rank}: {nutrition_name} ({evidence_strength} Evidence)", expanded=False):
        st.markdown(f"**{rationale}**")
        if biomarker_connection:
            st.markdown(f"**Biomarker Connection:** {biomarker_connection}")
        if implementation_tips:
            st.markdown("**How to Implement:**")
            for tip in implementation_tips:
                st.markdown(f"• {tip}")
        if foods_to_include:
            st.markdown("**Foods to Include More:**")
            for food in foods_to_include:
                st.markdown(f"• {food}")
        if indian_food_examples:
            st.markdown("**Indian Food Examples:**")
            for example in indian_food_examples:
                st.markdown(f"• {example}")
        if foods_to_avoid:
            st.markdown("**Foods to Limit/Avoid:**")
            for food in foods_to_avoid:
                st.markdown(f"• {food}")
        if meal_timing_guidance:
            st.info(f"**Meal Timing:** {meal_timing_guidance}")
        if female_specific_notes:
            st.info(f"**For Women:** {female_specific_notes}")
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
        current_optimization = exercise.get('current_optimization', '')
        athlete_specific_notes = exercise.get('athlete_specific_notes', '')
        female_specific_notes = exercise.get('female_specific_notes', '')
        no_intervention_note = exercise.get('no_intervention_note', '')
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
        current_optimization = getattr(exercise, 'current_optimization', '')
        athlete_specific_notes = getattr(exercise, 'athlete_specific_notes', '')
        female_specific_notes = getattr(exercise, 'female_specific_notes', '')
        no_intervention_note = getattr(exercise, 'no_intervention_note', '')
        evidence_source = getattr(exercise, 'evidence_source', '')
    
    with st.expander(f"🏋️ {exercise_name}", expanded=False):
        st.markdown(f"**{rationale}**")
        st.markdown(f"**Type:** {workout_type}")
        st.markdown(f"**Frequency:** {frequency}")
        st.markdown(f"**Duration:** {duration}")
        st.markdown(f"**Intensity:** {intensity}")
        if volume:
            st.markdown(f"**Volume:** {volume}")
        if rest_periods:
            st.markdown(f"**Rest Periods:** {rest_periods}")
        st.markdown(f"**Connection to Your Data:** {biomarker_connection}")
        if current_optimization:
            st.success(f"**What You're Doing Right:** {current_optimization}")
        if athlete_specific_notes:
            st.info(f"**Advanced Notes:** {athlete_specific_notes}")
        if female_specific_notes:
            st.info(f"**For Women:** {female_specific_notes}")
        if no_intervention_note:
            st.success(f"**Good News:** {no_intervention_note}")
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

# Azure OpenAI is configured in llm_utils.py via LiteLLM

# Ensure all session state is properly initialized before any access
ensure_session_state()

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

# --- Comprehensive User Profile ---
st.markdown("#### User Profile")

# Basic Information
st.markdown("**Basic Information**")
col1, col2, col3, col4 = st.columns(4)

with col1:
    name_input = st.text_input("Name", value=st.session_state.metadata.get('name', ''), key="user_name")
    st.session_state.metadata["name"] = name_input
with col2:
    age_input = st.number_input("Age", value=int(st.session_state.metadata.get('age', 30)), min_value=1, max_value=120, key="user_age")
    st.session_state.metadata["age"] = age_input
with col3:
    gender_input = st.selectbox("Gender", ["Male", "Female", "Other"],
                               index=["Male", "Female", "Other"].index(st.session_state.metadata.get('gender', 'Male')), key="user_gender")
    st.session_state.metadata["gender"] = gender_input
with col4:
    diet_type_input = st.selectbox("Diet Type", ["Vegetarian", "Non-Vegetarian", "Vegan", "Pescatarian"],
                                  index=["Vegetarian", "Non-Vegetarian", "Vegan", "Pescatarian"].index(st.session_state.metadata.get('diet_type', 'Non-Vegetarian')), key="diet_type")
    st.session_state.metadata["diet_type"] = diet_type_input

# Physical Metrics
st.markdown("**Physical Metrics**")
col1, col2, col3, col4 = st.columns(4)
with col1:
    weight_input = st.text_input("Body Weight (kg)", value=str(st.session_state.metadata.get('body_weight', '')), key="user_weight")
    st.session_state.metadata["body_weight"] = weight_input
with col2:
    height_input = st.text_input("Height (cm)", value=str(st.session_state.metadata.get('height', '')), key="user_height")
    st.session_state.metadata["height"] = height_input
with col3:
    body_fat_input = st.text_input("Body Fat %", value=str(st.session_state.metadata.get('body_fat_percentage', '')), key="body_fat")
    st.session_state.metadata["body_fat_percentage"] = body_fat_input
with col4:
    waist_input = st.text_input("Waist Circumference (cm)", value=str(st.session_state.metadata.get('waist_circumference', '')), key="waist")
    st.session_state.metadata["waist_circumference"] = waist_input

# Health Information
st.markdown("**Health Information**")
col1, col2 = st.columns(2)
with col1:
    medical_conditions_input = st.text_area("Known Medical Conditions",
                                           value=st.session_state.metadata.get('known_medical_conditions', ''),
                                           height=100, key="medical_conditions")
    st.session_state.metadata["known_medical_conditions"] = medical_conditions_input
with col2:
    supplements_input = st.text_area("Current Supplements & Medications",
                                    value=st.session_state.metadata.get('current_supplements_medications', ''),
                                    height=100, key="supplements")
    st.session_state.metadata["current_supplements_medications"] = supplements_input

col1, col2 = st.columns(2)
with col1:
    open_to_supplements = st.selectbox("Open to Supplements", ["Yes", "No"],
                                      index=["Yes", "No"].index(st.session_state.metadata.get('open_to_supplements', 'Yes')), key="open_supplements")
    st.session_state.metadata["open_to_supplements"] = open_to_supplements
with col2:
    competitive_athlete = st.selectbox("Competitive Athlete", ["Yes", "No"],
                                      index=["Yes", "No"].index(st.session_state.metadata.get('competitive_athlete', 'No')), key="athlete")
    st.session_state.metadata["competitive_athlete"] = competitive_athlete

# Activity and Lifestyle
st.markdown("**Activity & Lifestyle**")
activity_input = st.text_area("Activity Level (describe your exercise routine)",
                             value=st.session_state.metadata.get('activity_level', ''),
                             height=80, key="activity")
st.session_state.metadata["activity_level"] = activity_input

col1, col2, col3, col4 = st.columns(4)
with col1:
    sleep_hours = st.text_input("Average Sleep Hours/Night",
                               value=str(st.session_state.metadata.get('average_sleep_hours', '')), key="sleep")
    st.session_state.metadata["average_sleep_hours"] = sleep_hours
with col2:
    wake_time = st.text_input("Wake Up Time",
                             value=st.session_state.metadata.get('wake_up_time', ''), key="wake_time")
    st.session_state.metadata["wake_up_time"] = wake_time
with col3:
    smoker = st.selectbox("Smoker", ["Yes", "No"],
                         index=["Yes", "No"].index(st.session_state.metadata.get('smoker', 'No')), key="smoker")
    st.session_state.metadata["smoker"] = smoker
with col4:
    sun_exposure = st.selectbox("Daily Sun Exposure", ["<30 Min", "30-60 Min", ">60 Min"],
                               index=["<30 Min", "30-60 Min", ">60 Min"].index(st.session_state.metadata.get('sun_exposure', '<30 Min')), key="sun")
    st.session_state.metadata["sun_exposure"] = sun_exposure

col1, col2 = st.columns(2)
with col1:
    alcohol_intake = st.text_input("Alcohol Intake (drinks/week)",
                                  value=st.session_state.metadata.get('alcohol_intake', ''), key="alcohol")
    st.session_state.metadata["alcohol_intake"] = alcohol_intake
with col2:
    caffeine = st.text_input("Caffeine Intake (cups/day)",
                            value=st.session_state.metadata.get('caffeine', ''), key="caffeine")
    st.session_state.metadata["caffeine"] = caffeine

# Health Goals
st.markdown("**Health Goals**")
goal_options = ["Weight Loss", "Weight Gain", "Muscle Building", "Strength & Endurance", "Longevity",
               "Energy Improvement", "Sleep Quality", "Stress Management", "Heart Health", "Brain Health"]
health_goals = st.multiselect("Select Your Health Goals", goal_options,
                             default=st.session_state.metadata.get('health_goals', []), key="health_goals")
st.session_state.metadata["health_goals"] = health_goals



# --- User Conversation and Recommendations (Single Text Areas) ---
st.markdown("#### User Conversation (Q/A)")
st.text_area(
    "Paste or type the conversation (Q/A messages) here:",
    value=st.session_state.get("user_conversation", """Q: Have you tried to lose weight or body fat in the last 12 months? 
A: No- Haven't tried
Q: How easily do you build or maintain muscle mass? 
A: With effort
Q: How would you describe your typical energy through the day? 
A: Crashes post-meals
Q: How are your hunger and cravings? 
A: In control
Q: Do you experience bloating or digestive heaviness after meals? 
A: Rarely
Q: Do you feel low or foggy after eating certain foods (e.g., gluten, dairy, sugar)? 
A: Rarely
Q: Do you regularly feel stressed, wired, or on edge? 
A: Sometimes
Q: How well do you sleep on most nights? 
A: Struggle to fall/stay asleep

Q: How often do you feel fully recovered between training sessions? 
A: Sometimes - depends on the workout
Q: Do you experience muscle soreness or fatigue lasting more than 48 hours after a workout? 
A: Often
Q: How would you describe your energy during workouts? 
A: Consistent and strong from start to finish
Q: How easy is it for you to build or maintain strength or stamina? 
A: Takes effort but I progress
Q: Do you experience frequent colds, injuries, or joint pain? 
A: Occasionally
Q: How would you rate your stress levels over the past month? 
A: High
Q: How would you describe your sleep quality on most nights? 
A: Poor and inconsistent
Q: Have you noticed joint stiffness or brittle nails, or hair thinning lately? 
A: Yes - multiple or persistent issues

Q: How often do you feel mentally overwhelmed or emotionally reactive during the day? 
A: Occasionally
Q: How would you describe your ability to bounce back after stress or conflict? 
A: Slower than I would like
Q: How well do you fall asleep and stay asleep through the night? 
A: Often difficult - trouble falling or staying asleep
Q: Do you rely on caffeine, sugar, or stimulants to stay alert during the day? 
A: Occasionally
Q: How often do you feel low motivation, apathy, or emotional flatness? 
A: Frequently
Q: How does your body physically respond to stress? 
A: No clear pattern
Q: How often do you experience symptoms like anxiety, racing thoughts, or inner restlessness? 
A: Most days
Q: Under emotional or physical stress, do you ever feel chest tightness, skipped heartbeats, or palpitations? 
A: Occasionally

Q: How easily do you fall asleep at night? 
A: Often difficult - I lie awake or need aids to fall asleep
Q: How often do you wake up in the middle of the night? 
A: Most nights
Q: How would you describe your sleep quality? 
A: Unrefreshing or very disrupted
Q: How do you feel on waking in the morning? 
A: Exhausted or groggy
Q: Do you use screens or bright lights within an hour of bed? 
A: Daily
Q: How often do you feel sore, inflamed, or under-recovered even with sleep? 
A: Frequently
Q: Do you consume caffeine after 2 pm? 
A: Occasionally

Q: How often do you struggle with brain fog or slow thinking during the day? 
A: Occasionally
Q: How would you rate your ability to focus on tasks for extended periods? 
A: Excellent - I stay focused for long periods
Q: Do you experience memory lapses (e.g., names, tasks, short-term recall)? 
A: Often
Q: How sharp do you feel after lunch or mid-afternoon? 
A: A bit sluggish
Q: Do you regularly multitask or feel mentally wired but tired? 
A: Occasionally
Q: How well do you perform under pressure or deadline? 
A: Mixed - sometimes focused, sometimes scattered
Q: How often do you use caffeine or nootropics to stay sharp? 
A: Occasionally
Q: Do you feel shaky, lightheaded, or irritable if you delay or skip meals? 
A: Rarely

Q: How often do you wake up feeling truly refreshed and mentally clear? 
A: Occasionally
Q: How would you describe your energy levels across the day? 
A: Variable - some dips or crashes
Q: How often do you feel sharp, focused, and in mental flow? 
A: Some days
Q: How often do you experience bloating, heaviness, or sluggish digestion? 
A: Occasionally
Q: How well does your body respond to your workouts or training? 
A: I feel sore, flat, or under-recovered often
Q: Do you need caffeine or stimulants to perform or feel alert during the day? 
A: Occasionally
Q: How adaptable are you when dealing with stress, change, or emotional load? 
A: Somewhat reactive """),
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

# --- Model Configuration ---
st.markdown("#### Model Configuration")

# Available LLM models
model_options = {
    "azure/o1": "Azure o1(Original endpoint)",
    "azure/o4-mini": "Azure O4 Mini (New endpoint - O-Series)",
    "openai/o3": "OpenAI O3",
    "gemini/gemini-2.0-flash": "Google Gemini 2.0 Flash"
}

selected_model = st.selectbox(
    "Select LLM Model",
    options=list(model_options.keys()),
    format_func=lambda x: model_options[x],
    index=0,  # Default to GPT-4.1 mini
    key="model_selection"
)

st.info(f"🤖 Using {model_options[selected_model]}")

# --- JSON File Viewer ---
st.markdown("#### JSON File Viewer")
st.markdown("Upload a JSON file to view its contents in the same interface as the health report results.")

uploaded_json_file = st.file_uploader(
    "Choose a JSON file",
    type=['json'],
    help="Upload a JSON file to view its contents in a structured format",
    key="json_file_uploader"
)

if uploaded_json_file is not None:
    try:
        # Read and parse the JSON file
        json_content = json.loads(uploaded_json_file.read().decode('utf-8'))

        st.success(f"✅ Successfully loaded JSON file: {uploaded_json_file.name}")

        # Show file info
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**File Name:** {uploaded_json_file.name}")
        with col2:
            st.info(f"**File Size:** {uploaded_json_file.size} bytes")

        # Handle nested JSON structure (our saved format has data under "result" key)
        if isinstance(json_content, dict) and "result" in json_content:
            # This is our saved format with metadata
            actual_report_data = json_content["result"]
            file_metadata = {
                'filename': uploaded_json_file.name,
                'size': uploaded_json_file.size,
                'original_timestamp': json_content.get('timestamp', ''),
                'original_user': json_content.get('user_name', ''),
                'original_model': json_content.get('model_name', ''),
                'provider': json_content.get('provider', '')
            }
        else:
            # This is direct health report data
            actual_report_data = json_content
            file_metadata = {
                'filename': uploaded_json_file.name,
                'size': uploaded_json_file.size
            }

        # Store in session state for persistence and display
        st.session_state['uploaded_json_report'] = actual_report_data
        st.session_state['uploaded_json_meta'] = file_metadata

        # Display the JSON using the same UI structure as health reports
        st.markdown("### 📄 Uploaded JSON Report")
        st.markdown("*Displaying your uploaded JSON data using the health report interface*")

        # Quick summary of data available
        if isinstance(actual_report_data, dict):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                category_count = len(actual_report_data.get('category_insights', []))
                st.metric("Categories", category_count)
            with col2:
                biomarker_count = len(actual_report_data.get('biomarker_insights', []))
                st.metric("Biomarkers", biomarker_count)
            with col3:
                supplement_count = 0
                action_plan = actual_report_data.get('action_plan', {})
                if isinstance(action_plan, dict):
                    supplement_count = len(action_plan.get('supplements', []))
                st.metric("Supplements", supplement_count)
            with col4:
                has_pattern_analysis = bool(actual_report_data.get('biomarker_pattern_analysis'))
                st.metric("Pattern Analysis", "✅" if has_pattern_analysis else "❌")

    except json.JSONDecodeError as e:
        st.error(f"❌ Invalid JSON file. Error: {str(e)}")
    except Exception as e:
        st.error(f"❌ Error reading file: {str(e)}")

# Show previously uploaded JSON if exists
if 'uploaded_json_meta' in st.session_state and uploaded_json_file is None:
    st.info(f"📁 Previously uploaded: {st.session_state['uploaded_json_meta']['filename']}")
    if st.button("🗑️ Clear uploaded JSON", key="clear_json"):
        if 'uploaded_json_report' in st.session_state:
            del st.session_state['uploaded_json_report']
        if 'uploaded_json_meta' in st.session_state:
            del st.session_state['uploaded_json_meta']
        st.rerun()

st.markdown("---")  # Separator line

if st.button("Generate Personalized Report", key="generate_single"):
    with st.spinner(f"Creating personalized health insights for {st.session_state.metadata.get('name', 'you')}..."):
        # Update interaction count
        st.session_state.user_history["interaction_count"] += 1
        st.session_state.user_history["last_interaction_date"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        
        personal_details = f"""
Name: {st.session_state.metadata.get('name', '')}
Age: {st.session_state.metadata.get('age', '')}
Gender: {st.session_state.metadata.get('gender', '')}
Body Weight: {st.session_state.metadata.get('body_weight', '')}
Height: {st.session_state.metadata.get('height', '')}
Body Fat%: {st.session_state.metadata.get('body_fat_percentage', '')}
Waist Circumference: {st.session_state.metadata.get('waist_circumference', '')}
Diet Type: {st.session_state.metadata.get('diet_type', '')}
Known Medical Conditions: {st.session_state.metadata.get('known_medical_conditions', '')}
Open to Supplements: {st.session_state.metadata.get('open_to_supplements', '')}
Supplements & Medications: {st.session_state.metadata.get('current_supplements_medications', '')}
Activity Level: {st.session_state.metadata.get('activity_level', '')}
Competitive Athlete: {st.session_state.metadata.get('competitive_athlete', '')}
Average Hours of Sleep/Night: {st.session_state.metadata.get('average_sleep_hours', '')}
Wake Up Time: {st.session_state.metadata.get('wake_up_time', '')}
Smoker: {st.session_state.metadata.get('smoker', '')}
Sun Exposure: {st.session_state.metadata.get('sun_exposure', '')}
Alcohol Intake: {st.session_state.metadata.get('alcohol_intake', '')}
Caffeine: {st.session_state.metadata.get('caffeine', '')}
Health Goals: {', '.join(st.session_state.metadata.get('health_goals', []))}
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
            "interaction_count": st.session_state.user_history.get('interaction_count', 1),
            "preferences_summary": f"Supplements: {', '.join(st.session_state.user_history.get('preferred_supplements', [])[:3])}; Lifestyle: {', '.join(st.session_state.user_history.get('lifestyle_preferences', [])[:3])}; Nutrition: {', '.join(st.session_state.user_history.get('nutrition_preferences', [])[:3])}"
        }
        
        messages = [{"role": "user", "content": prompt}]

        # Show progress indicator
        with st.spinner(f"🤖 Generating personalized health report using {selected_model}..."):
            try:
                # Capture console output to detect fallback usage
                import io
                import sys
                from contextlib import redirect_stdout, redirect_stderr

                captured_output = io.StringIO()
                with redirect_stdout(captured_output), redirect_stderr(captured_output):
                    report = call_llm_with_fallback(selected_model, messages, HealthVizorResponse, user_context)

                # Check if fallback was used
                output_text = captured_output.getvalue()
                if "fallback model:" in output_text.lower():
                    # Extract the fallback model name
                    lines = output_text.split('\n')
                    for line in lines:
                        if "Successfully used fallback model:" in line:
                            fallback_model = line.split(":")[-1].strip()
                            st.warning(f"🔄 **Note:** Primary model hit rate limits, successfully used fallback model: `{fallback_model}`")
                            break

                # Convert Pydantic object to dict for better Streamlit session state compatibility
                if hasattr(report, 'model_dump'):
                    # Use model_dump for Pydantic v2
                    st.session_state.report_single = report.model_dump()
                elif hasattr(report, 'dict'):
                    # Fallback for older Pydantic versions
                    st.session_state.report_single = report.dict()
                else:
                    # Store as-is if it's already a dict or other type
                    st.session_state.report_single = report

                # Store report in history
                st.session_state.user_history["previous_reports"].append({
                    "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "model_used": selected_model,
                    "report_summary": str(report)[:200] + "..." if len(str(report)) > 200 else str(report)
                })

                st.success(f"✨ Personalized analysis complete for {st.session_state.metadata.get('name', 'you')}!")
            except Exception as e:
                error_msg = str(e)
                if "rate limit" in error_msg.lower() or "429" in error_msg or "quota" in error_msg.lower():
                    if "all available models" in error_msg.lower():
                        st.error(f"❌ All Models Rate Limited: {error_msg}")
                        st.warning("⏰ **All models are currently rate limited. Please:**")
                        st.markdown("""
                        - **Wait 60 seconds** and try again
                        - **Try again later** when usage resets
                        - **Check your API quotas** for each provider
                        """)

                        # Add retry button with countdown
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("🔄 Retry Now", key="retry_rate_limit"):
                                st.rerun()
                        with col2:
                            st.info("💡 **Tip:** Wait 60 seconds for best results")
                    else:
                        st.error(f"❌ Rate Limit Reached: {error_msg}")
                        st.info("🔄 **The system automatically tried fallback models but they were also rate limited.**")

                        # Add retry button
                        if st.button("🔄 Retry with Fallback Models", key="retry_fallback"):
                            st.rerun()
                else:
                    st.error(f"❌ LLM call failed: {error_msg}")
                    st.info("💡 **Tip:** Try adjusting your inputs or try again in a few moments.")

# Display the generated report
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
        st.json(report, expanded=True)

    # Handle both dict and pydantic object response
    if isinstance(report, dict) or hasattr(report, 'overall_health_summary'):
        
        # A) OVERALL HEALTH SUMMARY & PERSONALIZATION
        overall_summary = ''
        congratulations = ''
        wins = []
        continue_doing = []
        needs_work = []
        biomarker_snapshot = ''
        goal_relevance = ''
        longevity_impact = ''
        pattern_analysis = ''

        # Extract values based on report type (dict or Pydantic model)
        if isinstance(report, dict):
            overall_summary = report.get('overall_health_summary', '')
            congratulations = report.get('congratulations_message', '')
            wins = report.get('wins_to_celebrate', [])
            continue_doing = report.get('what_to_continue', [])
            needs_work = report.get('what_needs_work', [])
            biomarker_snapshot = report.get('biomarker_snapshot', '')
            goal_relevance = report.get('goal_relevance', '')
            longevity_impact = report.get('longevity_performance_impact', '')
            pattern_analysis = report.get('biomarker_pattern_analysis', '')
        else:
            overall_summary = getattr(report, 'overall_health_summary', '')
            congratulations = getattr(report, 'congratulations_message', '')
            wins = getattr(report, 'wins_to_celebrate', [])
            continue_doing = getattr(report, 'what_to_continue', [])
            needs_work = getattr(report, 'what_needs_work', [])
            biomarker_snapshot = getattr(report, 'biomarker_snapshot', '')
            goal_relevance = getattr(report, 'goal_relevance', '')
            longevity_impact = getattr(report, 'longevity_performance_impact', '')
            pattern_analysis = getattr(report, 'biomarker_pattern_analysis', '')

        if overall_summary:
            st.markdown(f"## 🌟 Overall Health Summary for {user_name}")

            # Congratulations message
            if congratulations:
                st.success(congratulations)

            st.markdown(overall_summary)

            # Wins to celebrate
            if wins:
                st.markdown("### ✅ What's Working Well")
                for win in wins:
                    st.markdown(f"✅ {win}")

            # What to continue
            if continue_doing:
                st.markdown("### 💪 Keep Doing")
                for item in continue_doing:
                    st.markdown(f"🔄 {item}")

            # What needs work
            if needs_work:
                st.markdown("### ⚠️ What Needs Attention")
                for item in needs_work:
                    st.markdown(f"⚠️ {item}")

            # Enhanced Top 3 Priorities Detailed
            top_3_priorities_detailed = []
            if isinstance(report, dict):
                top_3_priorities_detailed = report.get('top_3_priorities_detailed', [])
            else:
                top_3_priorities_detailed = getattr(report, 'top_3_priorities_detailed', [])

            if top_3_priorities_detailed:
                st.markdown("### 🎯 Your Top 3 Priorities (Detailed Analysis)")
                st.markdown("*Based on your biomarker data, symptoms, lifestyle, and goals*")
                for priority in top_3_priorities_detailed:
                    display_top_priority_detailed(priority, user_name)

            # Biomarker Snapshot
            if biomarker_snapshot:
                st.markdown("### 📊 Biomarker Snapshot")
                st.info(biomarker_snapshot)

            # Goal relevance and longevity impact
            if goal_relevance or longevity_impact:
                col1, col2 = st.columns(2)
                with col1:
                    if goal_relevance:
                        st.info(f"**Goal Connection:** {goal_relevance}")
                with col2:
                    if longevity_impact:
                        st.info(f"**Longevity & Performance:** {longevity_impact}")

            # Biomarker pattern analysis
            if pattern_analysis:
                st.markdown("### 🔬 Biomarker Pattern Analysis")
                st.info(pattern_analysis)
        
        # B) CATEGORY LEVEL INSIGHTS & PERSONALIZATION
        category_insights = []
        if isinstance(report, dict):
            category_insights = report.get('category_insights', [])
        else:
            category_insights = getattr(report, 'category_insights', [])

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
        biomarker_insights = []
        if isinstance(report, dict):
            biomarker_insights = report.get('biomarker_insights', [])
        else:
            biomarker_insights = getattr(report, 'biomarker_insights', [])

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
        action_plan = None
        if isinstance(report, dict):
            action_plan = report.get('action_plan', {})
        else:
            action_plan = getattr(report, 'action_plan', None)

        if action_plan:
            st.markdown(f"## 🎯 Your Personalized Action Plan, {user_name}")

            # Extract action plan components
            supplements = []
            schedule_summary = ''
            nutrition_recs = []
            exercise_recs = []
            timeline = []

            if isinstance(action_plan, dict):
                supplements = action_plan.get('supplements', [])
                schedule_summary = action_plan.get('supplement_schedule_summary', '')
                nutrition_recs = action_plan.get('nutrition', [])
                exercise_recs = action_plan.get('exercise_lifestyle', [])
                timeline = action_plan.get('six_month_timeline', [])
            else:
                supplements = getattr(action_plan, 'supplements', [])
                schedule_summary = getattr(action_plan, 'supplement_schedule_summary', '')
                nutrition_recs = getattr(action_plan, 'nutrition', [])
                exercise_recs = getattr(action_plan, 'exercise_lifestyle', [])
                timeline = getattr(action_plan, 'six_month_timeline', [])

            # Supplements
            if supplements:
                st.markdown("### 💊 Your Supplement Protocol")

                # Show supplement schedule summary first
                if schedule_summary:
                    st.markdown("#### 📅 Daily Schedule Summary")
                    st.info(schedule_summary)

                # Display individual supplements
                for i, supp in enumerate(supplements):
                    display_supplement_recommendation(supp, i, user_name)

                st.warning("⚠️ These suggestions are for educational purposes only and do not constitute medical advice. Please consult a healthcare provider before beginning any supplement regimen.")

            # Nutrition
            if nutrition_recs:
                st.markdown("### 🥗 Your Nutrition Protocol")
                for i, nutrition in enumerate(nutrition_recs):
                    display_nutrition_recommendation(nutrition, i, user_name)

            # Exercise & Lifestyle
            if exercise_recs:
                st.markdown("### 🏋️ Your Exercise & Lifestyle Protocol")
                for i, exercise in enumerate(exercise_recs):
                    display_exercise_recommendation(exercise, i, user_name)

            # 6-Month Timeline
            if timeline:
                st.markdown("### 📅 Your 6-Month Journey Timeline")
                for plan in timeline:
                    display_monthly_plan(plan, user_name)
        
        # Escalation flags
        escalation_needed = False
        escalation_reason = ''

        if isinstance(report, dict):
            escalation_needed = report.get('escalation_needed', False)
            escalation_reason = report.get('escalation_reason', '')
        else:
            escalation_needed = getattr(report, 'escalation_needed', False)
            escalation_reason = getattr(report, 'escalation_reason', '')

        if escalation_needed:
            st.error(f"⚠️ **IMPORTANT HEALTH ALERT FOR {user_name.upper()}** ⚠️")
            st.error(f"This report has been flagged for escalation: {escalation_reason}")
            st.error("Please consult with a healthcare provider immediately.")

        # Disclaimer
        disclaimer = ''
        if isinstance(report, dict):
            disclaimer = report.get('disclaimer', '')
        else:
            disclaimer = getattr(report, 'disclaimer', '')

        if disclaimer:
            st.info(f"**Important Note for {user_name}:** {disclaimer}")
            
    # Show user's personalization summary
    if st.session_state.user_history.get("interaction_count", 0) > 1:
        with st.expander(f"📊 {user_name}'s Profile Summary", expanded=False):
            col_stats1, col_stats2 = st.columns(2)
            with col_stats1:
                st.write(f"**Total Reports Generated:** {len(st.session_state.user_history.get('previous_reports', []))}")
                st.write(f"**Preferred Supplements:** {len(st.session_state.user_history.get('preferred_supplements', []))}")
            with col_stats2:
                st.write(f"**Lifestyle Goals:** {len(st.session_state.user_history.get('lifestyle_preferences', []))}")
                st.write(f"**Nutrition Focus:** {len(st.session_state.user_history.get('nutrition_preferences', []))}")

# --- Display Uploaded JSON Report ---
if st.session_state.get("uploaded_json_report"):
    uploaded_report = st.session_state.uploaded_json_report
    file_meta = st.session_state.get('uploaded_json_meta', {})

    st.markdown("---")  # Separator
    st.markdown(f"### 📄 Uploaded JSON Report: {file_meta.get('filename', 'Unknown File')}")

    # Show additional metadata if available (from our saved format)
    if file_meta.get('original_timestamp') or file_meta.get('original_user'):
        col1, col2, col3 = st.columns(3)
        with col1:
            if file_meta.get('original_user'):
                st.info(f"**Original User:** {file_meta['original_user']}")
        with col2:
            if file_meta.get('original_model'):
                st.info(f"**Model Used:** {file_meta['original_model']}")
        with col3:
            if file_meta.get('provider'):
                st.info(f"**Provider:** {file_meta['provider']}")

        if file_meta.get('original_timestamp'):
            st.caption(f"**Generated:** {file_meta['original_timestamp']}")

    st.markdown("*Displaying your uploaded JSON data using the health report interface*")

    # Show the raw JSON in expandable format first
    with st.expander("📊 Raw JSON Data", expanded=False):
        st.json(uploaded_report, expanded=True)

    # Display JSON structure info and show field mapping
    if isinstance(uploaded_report, dict):
        st.info(f"📋 **JSON Structure:** Found {len(uploaded_report.keys())} top-level fields: {', '.join(list(uploaded_report.keys())[:5])}{'...' if len(uploaded_report.keys()) > 5 else ''}")

        # Show which fields were successfully mapped
        mapped_fields = []
        for key in uploaded_report.keys():
            # Check if this key matches any of our expected field variations
            field_mappings = {
                'Health Summary': ['overall_health_summary', 'health_summary', 'summary', 'overall_summary', 'health_overview', 'overview'],
                'Congratulations': ['congratulations_message', 'congratulations', 'good_news', 'positive_message'],
                'Wins/Achievements': ['wins_to_celebrate', 'wins', 'achievements', 'positives', 'strengths'],
                'Areas to Continue': ['what_to_continue', 'continue_doing', 'keep_doing', 'maintain'],
                'Areas Needing Work': ['what_needs_work', 'needs_work', 'areas_for_improvement', 'concerns', 'issues'],
                'Category Insights': ['category_insights', 'categories', 'category_analysis', 'health_categories', 'category_data'],
                'Biomarker Insights': ['biomarker_insights', 'biomarkers', 'biomarker_analysis', 'lab_results'],
                'Action Plan': ['action_plan', 'recommendations', 'plan', 'treatment_plan', 'personalized_plan'],
                'Supplements': ['supplements', 'supplement_recommendations', 'vitamins', 'supplementation'],
                'Nutrition': ['nutrition_recommendations', 'nutrition', 'diet_recommendations', 'dietary_advice'],
                'Exercise': ['exercise_recommendations', 'exercise', 'fitness_recommendations', 'workout_plan'],
                'Timeline': ['six_month_timeline', 'timeline', 'schedule', 'plan_timeline', 'monthly_plan', 'progression']
            }

            for category, variations in field_mappings.items():
                if key.lower() in [v.lower() for v in variations]:
                    mapped_fields.append(f"{category} ({key})")
                    break

        if mapped_fields:
            st.success(f"✅ **Recognized Fields:** {', '.join(mapped_fields)}")
        else:
            st.warning("⚠️ **No standard health report fields detected.** Will attempt to display available data.")

    # Now display using the same structure as health reports
    # Handle both dict and pydantic object response (same logic as health report)
    # Make the condition more flexible - if it's a dict, try to display it
    if isinstance(uploaded_report, dict):

        # A) OVERALL HEALTH SUMMARY & PERSONALIZATION
        overall_summary = ''
        congratulations = ''
        wins = []
        continue_doing = []
        needs_work = []
        priority_categories = []
        goal_relevance = ''
        longevity_impact = ''
        pattern_analysis = ''

        # Helper function to find field with multiple possible names
        def get_field_value(data, field_variations, default=''):
            """Get field value trying multiple possible field names"""
            if isinstance(field_variations, str):
                field_variations = [field_variations]

            for field_name in field_variations:
                if field_name in data:
                    return data[field_name]
            return default

        # Extract values with flexible field name matching
        # Prioritize exact field names from our saved format first
        if isinstance(uploaded_report, dict):
            # Overall health summary - exact field name first, then variations
            overall_summary = get_field_value(uploaded_report, [
                'overall_health_summary',  # Our exact field name
                'health_summary', 'summary', 'overall_summary', 'health_overview', 'overview'
            ])

            # Congratulations message - exact field name first
            congratulations = get_field_value(uploaded_report, [
                'congratulations_message',  # Our exact field name
                'congratulations', 'good_news', 'positive_message', 'celebration_message'
            ])

            # Wins to celebrate - exact field name first
            wins = get_field_value(uploaded_report, [
                'wins_to_celebrate',  # Our exact field name
                'wins', 'achievements', 'positives', 'strengths', 'good_results', 'what_is_working_well'
            ], [])

            # What to continue - exact field name first
            continue_doing = get_field_value(uploaded_report, [
                'what_to_continue',  # Our exact field name
                'continue_doing', 'keep_doing', 'maintain', 'continue', 'keep_up'
            ], [])

            # What needs work - exact field name first
            needs_work = get_field_value(uploaded_report, [
                'what_needs_work',  # Our exact field name
                'needs_work', 'areas_for_improvement', 'concerns', 'issues', 'problems',
                'needs_attention', 'areas_to_improve', 'improvement_areas'
            ], [])

            # Goal relevance - exact field name first
            goal_relevance = get_field_value(uploaded_report, [
                'goal_relevance',  # Our exact field name
                'goal_connection', 'how_this_relates_to_goals', 'goal_alignment', 'personal_goals'
            ])

            # Longevity impact - exact field name first
            longevity_impact = get_field_value(uploaded_report, [
                'longevity_performance_impact',  # Our exact field name
                'longevity_impact', 'performance_impact', 'long_term_impact', 'health_impact'
            ])

            # Pattern analysis - exact field name first
            pattern_analysis = get_field_value(uploaded_report, [
                'biomarker_pattern_analysis',  # Our exact field name
                'pattern_analysis', 'biomarker_patterns', 'analysis', 'patterns', 'biomarker_analysis'
            ])
        else:
            overall_summary = getattr(uploaded_report, 'overall_health_summary', '')
            congratulations = getattr(uploaded_report, 'congratulations_message', '')
            wins = getattr(uploaded_report, 'wins_to_celebrate', [])
            continue_doing = getattr(uploaded_report, 'what_to_continue', [])
            needs_work = getattr(uploaded_report, 'what_needs_work', [])
            goal_relevance = getattr(uploaded_report, 'goal_relevance', '')
            longevity_impact = getattr(uploaded_report, 'longevity_performance_impact', '')
            pattern_analysis = getattr(uploaded_report, 'biomarker_pattern_analysis', '')

        # Always show the health summary section, even if some fields are empty
        st.markdown("## 🌟 Overall Health Summary")

        # Congratulations message
        if congratulations:
            st.success(congratulations)

        # Overall summary
        if overall_summary:
            st.markdown(overall_summary)
        else:
            st.info("No overall health summary found in the uploaded JSON.")

        # Wins to celebrate
        if wins:
            st.markdown("### ✅ What's Working Well")
            for win in wins:
                st.markdown(f"✅ {win}")

        # What to continue
        if continue_doing:
            st.markdown("### 💪 Keep Doing")
            for item in continue_doing:
                st.markdown(f"🔄 {item}")

        # What needs work
        if needs_work:
            st.markdown("### ⚠️ What Needs Attention")
            for item in needs_work:
                st.markdown(f"⚠️ {item}")

        # Enhanced Top 3 Priorities Detailed
        top_3_priorities_detailed = []
        if isinstance(uploaded_report, dict):
            top_3_priorities_detailed = get_field_value(uploaded_report, [
                'top_3_priorities_detailed',  # Our exact field name
                'detailed_priorities', 'priority_details', 'priorities_detailed', 'top_priorities_detailed'
            ], [])
        else:
            top_3_priorities_detailed = getattr(uploaded_report, 'top_3_priorities_detailed', [])

        if top_3_priorities_detailed:
            st.markdown("### 🎯 Your Top 3 Priorities (Detailed Analysis)")
            st.markdown("*Based on your biomarker data, symptoms, lifestyle, and goals*")
            user_name = file_meta.get('original_user', 'User')
            for priority in top_3_priorities_detailed:
                display_top_priority_detailed(priority, user_name)

        # Goal relevance
        if goal_relevance:
            st.markdown("### 🎯 How This Relates to Your Goals")
            st.info(goal_relevance)

        # Longevity impact
        if longevity_impact:
            st.markdown("### 🧬 Longevity & Performance Impact")
            st.markdown(longevity_impact)

        # Pattern analysis
        if pattern_analysis:
            st.markdown("### 🔍 Biomarker Pattern Analysis")
            st.markdown(pattern_analysis)

        # Show a message if no summary data was found, but also try to display any available data
        if not any([overall_summary, congratulations, wins, continue_doing, needs_work, priority_categories, goal_relevance, longevity_impact, pattern_analysis]):
            st.warning("No health summary data found in the expected format. Attempting to display available data...")

            # Try to display any available data in a structured way
            st.markdown("### 📊 Available Data from JSON")

            # Display all top-level keys and their values
            for key, value in uploaded_report.items():
                if isinstance(value, str) and value.strip():
                    st.markdown(f"**{key.replace('_', ' ').title()}:**")
                    st.write(value)
                elif isinstance(value, list) and value:
                    st.markdown(f"**{key.replace('_', ' ').title()}:**")
                    for i, item in enumerate(value, 1):
                        if isinstance(item, str):
                            st.markdown(f"{i}. {item}")
                        elif isinstance(item, dict):
                            st.json(item)
                        else:
                            st.write(f"{i}. {item}")
                elif isinstance(value, dict) and value:
                    st.markdown(f"**{key.replace('_', ' ').title()}:**")
                    with st.expander(f"View {key}", expanded=False):
                        st.json(value)
                elif isinstance(value, (int, float, bool)):
                    st.markdown(f"**{key.replace('_', ' ').title()}:** {value}")

            st.info("💡 **Tip:** For best results, ensure your JSON follows the health report structure with fields like 'overall_health_summary', 'wins_to_celebrate', 'category_insights', 'biomarker_insights', 'action_plan', etc.")

        # B) CATEGORY LEVEL INSIGHTS & PERSONALIZATION
        category_insights = []
        if isinstance(uploaded_report, dict):
            category_insights = get_field_value(uploaded_report, [
                'category_insights',  # Our exact field name
                'categories', 'category_analysis', 'health_categories', 'category_data', 'category_scores'
            ], [])
        else:
            category_insights = getattr(uploaded_report, 'category_insights', [])

        if category_insights:
            st.markdown("## 🔍 Category Health Insights")
            user_name = file_meta.get('original_user', 'User')
            for insight in category_insights:
                display_category_insight(insight, user_name)

        # C) BIOMARKER INSIGHTS
        biomarker_insights = []
        if isinstance(uploaded_report, dict):
            biomarker_insights = get_field_value(uploaded_report, [
                'biomarker_insights',  # Our exact field name
                'biomarkers', 'biomarker_analysis', 'lab_results', 'test_results', 'biomarker_data'
            ], [])
        else:
            biomarker_insights = getattr(uploaded_report, 'biomarker_insights', [])

        if biomarker_insights:
            st.markdown("## 🧪 Biomarker Analysis")

            # Categorize biomarkers by status
            red_biomarkers = []
            amber_biomarkers = []
            green_biomarkers = []

            for insight in biomarker_insights:
                if isinstance(insight, dict):
                    status = insight.get('status', '').lower()
                else:
                    status = getattr(insight, 'status', '').lower()

                if 'critical' in status or 'red' in status or 'urgent' in status:
                    red_biomarkers.append(insight)
                elif 'amber' in status or 'yellow' in status or 'monitor' in status or 'suboptimal' in status:
                    amber_biomarkers.append(insight)
                else:
                    green_biomarkers.append(insight)

            if red_biomarkers:
                st.markdown("### 🚨 Critical Biomarkers - Immediate Action Required")
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

        # D) BIOMARKER PATTERN ANALYSIS
        biomarker_pattern_analysis = None
        if isinstance(uploaded_report, dict):
            biomarker_pattern_analysis = get_field_value(uploaded_report, [
                'biomarker_pattern_analysis',  # Our exact field name
                'pattern_analysis', 'cross_system_analysis', 'multi_marker_patterns', 'system_analysis'
            ])
        else:
            biomarker_pattern_analysis = getattr(uploaded_report, 'biomarker_pattern_analysis', None)

        if biomarker_pattern_analysis:
            st.markdown("## 🔬 Cross-System Biomarker Pattern Analysis")
            st.markdown(biomarker_pattern_analysis)

        # E) PERSONALIZED ACTION PLAN
        action_plan = None
        if isinstance(uploaded_report, dict):
            action_plan = get_field_value(uploaded_report, [
                'action_plan',  # Our exact field name
                'recommendations', 'plan', 'treatment_plan', 'personalized_plan', 'action_items', 'next_steps'
            ], {})
        else:
            action_plan = getattr(uploaded_report, 'action_plan', None)

        if action_plan:
            st.markdown("## 🎯 Personalized Action Plan")

            # Extract action plan components
            supplements = []
            schedule_summary = ''
            nutrition_recs = []
            exercise_recs = []
            timeline = []

            if isinstance(action_plan, dict):
                # Supplements - exact field name first
                supplements = get_field_value(action_plan, [
                    'supplements',  # Our exact field name
                    'supplement_recommendations', 'supplement_plan', 'vitamins', 'pills', 'supplementation'
                ], [])

                # Schedule summary - exact field name first
                schedule_summary = get_field_value(action_plan, [
                    'supplement_schedule_summary',  # Our exact field name
                    'schedule_summary', 'schedule', 'timing', 'overview', 'plan_summary', 'summary'
                ])

                # Nutrition recommendations - exact field name first
                nutrition_recs = get_field_value(action_plan, [
                    'nutrition_recommendations',  # Our exact field name
                    'nutrition', 'diet_recommendations', 'dietary_advice', 'food_recommendations',
                    'nutrition_plan', 'diet_plan', 'eating_plan'
                ], [])

                # Exercise recommendations - exact field name first
                exercise_recs = get_field_value(action_plan, [
                    'exercise_recommendations',  # Our exact field name
                    'exercise', 'fitness_recommendations', 'workout_plan', 'physical_activity',
                    'fitness_plan', 'exercise_plan', 'lifestyle_recommendations'
                ], [])

                # Timeline - exact field name first
                timeline = get_field_value(action_plan, [
                    'six_month_timeline',  # Our exact field name
                    'timeline', 'schedule', 'plan_timeline', 'monthly_plan', 'progression', 'phases', 'journey'
                ], [])
            else:
                supplements = getattr(action_plan, 'supplements', [])
                schedule_summary = getattr(action_plan, 'schedule_summary', '')
                nutrition_recs = getattr(action_plan, 'nutrition_recommendations', [])
                exercise_recs = getattr(action_plan, 'exercise_recommendations', [])
                timeline = getattr(action_plan, 'timeline', [])

            # Supplements
            if supplements:
                st.markdown("### 💊 Your Supplement Protocol")

                # Show supplement schedule summary first
                if schedule_summary:
                    st.markdown("#### 📅 Daily Schedule Summary")
                    st.info(schedule_summary)

                # Display individual supplements
                for i, supplement in enumerate(supplements):
                    display_supplement_recommendation(supplement, i, "User")

                st.warning("⚠️ These suggestions are for educational purposes only and do not constitute medical advice. Please consult a healthcare provider before beginning any supplement regimen.")

            # Nutrition
            if nutrition_recs:
                st.markdown("### 🥗 Your Nutrition Protocol")
                for i, nutrition in enumerate(nutrition_recs):
                    display_nutrition_recommendation(nutrition, i, "User")

            # Exercise & Lifestyle
            if exercise_recs:
                st.markdown("### 🏋️ Your Exercise & Lifestyle Protocol")
                for i, exercise in enumerate(exercise_recs):
                    display_exercise_recommendation(exercise, i, "User")

            # 6-Month Timeline
            if timeline:
                st.markdown("### 📅 Your 6-Month Journey Timeline")
                for plan in timeline:
                    display_monthly_plan(plan, "User")

        # Escalation flags
        escalation_needed = False
        escalation_reason = ''

        if isinstance(uploaded_report, dict):
            escalation_needed = get_field_value(uploaded_report, [
                'escalation_needed', 'medical_consultation_needed', 'urgent',
                'requires_medical_attention', 'see_doctor'
            ], False)
            escalation_reason = get_field_value(uploaded_report, [
                'escalation_reason', 'medical_reason', 'urgent_reason',
                'consultation_reason', 'warning'
            ])
        else:
            escalation_needed = getattr(uploaded_report, 'escalation_needed', False)
            escalation_reason = getattr(uploaded_report, 'escalation_reason', '')

        if escalation_needed:
            st.error("🚨 **IMPORTANT: Medical Consultation Required**")
            if escalation_reason:
                st.error(f"**Reason:** {escalation_reason}")
            st.error("Please consult with a healthcare provider immediately for proper medical evaluation and guidance.")

    else:
        # If the JSON is not a dictionary, try to handle other formats
        st.warning("⚠️ The uploaded JSON is not in dictionary format. Displaying as formatted data:")

        with st.expander("📊 JSON Content", expanded=True):
            st.json(uploaded_report, expanded=True)

        # Try to display any recognizable data
        if isinstance(uploaded_report, (list, tuple)):
            st.markdown("### 📋 List Data")
            st.write(f"Found {len(uploaded_report)} items:")
            for i, item in enumerate(uploaded_report[:10], 1):  # Show first 10 items
                if isinstance(item, dict):
                    st.markdown(f"**Item {i}:**")
                    with st.expander(f"View Item {i}", expanded=False):
                        st.json(item)
                else:
                    st.write(f"{i}. {item}")
            if len(uploaded_report) > 10:
                st.info(f"... and {len(uploaded_report) - 10} more items")
        else:
            st.markdown("### 📄 Raw Data")
            st.code(str(uploaded_report), language='json')

