"""LangGraph workflow for comprehensive content safety filtering."""

from typing import Any, Dict, List, TypedDict
import re
import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph

from app.core.config import settings

logger = logging.getLogger(__name__)


class ContentSafetyState(TypedDict):
    """State for content safety workflow."""
    # Input
    content: str
    child_age: int
    language: str
    context: str  # "story", "choice", "general"
    
    # Safety analysis results
    moderation_result: Dict[str, Any]
    age_appropriateness_score: float
    cultural_sensitivity_score: float
    educational_value_score: float
    
    # Issue detection
    safety_issues: List[Dict[str, Any]]
    recommendations: List[str]
    
    # Final assessment
    overall_safety_score: float
    is_approved: bool
    needs_review: bool


def run_openai_moderation(state: ContentSafetyState) -> Dict[str, Any]:
    """Run OpenAI's moderation API on the content."""
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        moderation_response = client.moderations.create(input=state["content"])
        result = moderation_response.results[0]
        
        # Convert to dictionary format for easier handling
        moderation_result = {
            "flagged": result.flagged,
            "categories": {k: v for k, v in result.categories.__dict__.items()},
            "category_scores": {k: v for k, v in result.category_scores.__dict__.items()},
        }
        
        return {"moderation_result": moderation_result}
        
    except Exception as e:
        logger.error(f"OpenAI moderation failed: {e}")
        # Return safe defaults if moderation fails
        return {
            "moderation_result": {
                "flagged": False,
                "categories": {},
                "category_scores": {},
                "error": str(e)
            }
        }


def analyze_age_appropriateness(state: ContentSafetyState) -> Dict[str, Any]:
    """Analyze if content is appropriate for the child's age."""
    content = state["content"].lower()
    child_age = state["child_age"]
    
    age_issues = []
    score = 1.0  # Start with perfect score
    
    # Age-specific content guidelines
    age_guidelines = {
        7: {
            "avoid": ["death", "violence", "scary", "nightmare", "monster", "ghost"],
            "prefer": ["friendship", "family", "animals", "adventure", "learning"],
            "max_complexity": 2,  # Simple sentences
        },
        8: {
            "avoid": ["death", "serious illness", "violence", "horror"],
            "prefer": ["friendship", "problem-solving", "creativity", "nature"],
            "max_complexity": 3,
        },
        9: {
            "avoid": ["graphic violence", "death", "horror", "adult themes"],
            "prefer": ["adventure", "mystery", "science", "friendship"],
            "max_complexity": 4,
        },
        10: {
            "avoid": ["graphic violence", "inappropriate relationships", "mature themes"],
            "prefer": ["mystery", "adventure", "learning", "challenges"],
            "max_complexity": 5,
        },
        11: {
            "avoid": ["graphic content", "inappropriate relationships", "extreme violence"],
            "prefer": ["complex stories", "moral dilemmas", "growth"],
            "max_complexity": 6,
        },
        12: {
            "avoid": ["explicit content", "inappropriate relationships"],
            "prefer": ["coming of age", "responsibility", "complex themes"],
            "max_complexity": 7,
        }
    }
    
    # Get guidelines for this age (with fallback)
    guidelines = age_guidelines.get(child_age, age_guidelines[9])
    
    # Check for inappropriate content
    for avoid_term in guidelines["avoid"]:
        if avoid_term in content:
            age_issues.append({
                "type": "inappropriate_content",
                "issue": f"Contains '{avoid_term}' which may be inappropriate for age {child_age}",
                "severity": "high"
            })
            score -= 0.3
    
    # Check sentence complexity (rough estimate)
    sentences = re.split(r'[.!?]+', state["content"])
    avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
    
    if avg_sentence_length > guidelines["max_complexity"] * 5:
        age_issues.append({
            "type": "complexity",
            "issue": f"Content may be too complex for age {child_age}",
            "severity": "medium"
        })
        score -= 0.1
    
    # Check for positive themes
    positive_themes_found = sum(1 for theme in guidelines["prefer"] if theme in content)
    if positive_themes_found > 0:
        score += 0.1  # Bonus for positive themes
    
    return {
        "age_appropriateness_score": max(0.0, min(1.0, score)),
        "safety_issues": age_issues
    }


def analyze_cultural_sensitivity(state: ContentSafetyState) -> Dict[str, Any]:
    """Analyze cultural sensitivity of the content."""
    try:
        llm = ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.2,  # Low temperature for consistent analysis
        )
        
        analysis_prompt = f"""
        Please analyze this children's content for cultural sensitivity and inclusivity.
        
        Content: {state["content"]}
        Child age: {state["child_age"]}
        Language: {state["language"]}
        
        Evaluate for:
        1. Cultural stereotypes or biases
        2. Inclusive representation
        3. Respectful portrayal of different cultures
        4. Age-appropriate cultural themes
        5. Language sensitivity
        
        Rate from 0-1 (1 being perfectly sensitive and inclusive).
        Return only a JSON object with:
        - score: float between 0-1
        - issues: array of any cultural sensitivity concerns
        - recommendations: array of suggestions for improvement
        """
        
        messages = [
            SystemMessage(content="You are a cultural sensitivity expert for children's educational content."),
            HumanMessage(content=analysis_prompt)
        ]
        
        response = llm.invoke(messages)
        
        # Try to parse the response
        import json
        try:
            result = json.loads(response.content.strip())
            cultural_issues = [
                {"type": "cultural", "issue": issue, "severity": "medium"}
                for issue in result.get("issues", [])
            ]
            
            return {
                "cultural_sensitivity_score": result.get("score", 0.8),
                "safety_issues": cultural_issues,
                "recommendations": result.get("recommendations", [])
            }
            
        except json.JSONDecodeError:
            # Fallback to default safe score if parsing fails
            return {
                "cultural_sensitivity_score": 0.8,
                "safety_issues": [],
                "recommendations": ["Manual cultural sensitivity review recommended"]
            }
            
    except Exception as e:
        logger.error(f"Cultural sensitivity analysis failed: {e}")
        return {
            "cultural_sensitivity_score": 0.7,  # Conservative default
            "safety_issues": [{"type": "cultural", "issue": "Cultural analysis failed", "severity": "low"}],
            "recommendations": ["Manual review recommended due to analysis failure"]
        }


def analyze_educational_value(state: ContentSafetyState) -> Dict[str, Any]:
    """Analyze the educational value of the content."""
    content = state["content"].lower()
    
    educational_indicators = {
        "vocabulary": ["learn", "discover", "understand", "explain", "describe"],
        "problem_solving": ["solve", "figure out", "think", "decide", "choose"],
        "moral_values": ["kind", "help", "share", "honest", "brave", "friend"],
        "creativity": ["imagine", "create", "build", "draw", "story", "idea"],
        "science": ["nature", "animal", "plant", "earth", "space", "experiment"],
        "social_skills": ["together", "team", "cooperation", "communicate", "respect"]
    }
    
    educational_score = 0.5  # Base score
    found_elements = []
    
    for category, keywords in educational_indicators.items():
        found_keywords = [word for word in keywords if word in content]
        if found_keywords:
            educational_score += 0.1
            found_elements.append(f"{category}: {', '.join(found_keywords[:2])}")
    
    # Cap at 1.0
    educational_score = min(1.0, educational_score)
    
    recommendations = []
    if educational_score < 0.7:
        recommendations.extend([
            "Consider adding more educational elements",
            "Include vocabulary building opportunities",
            "Add problem-solving scenarios"
        ])
    
    return {
        "educational_value_score": educational_score,
        "educational_elements": found_elements,
        "recommendations": recommendations
    }


def calculate_overall_safety(state: ContentSafetyState) -> Dict[str, Any]:
    """Calculate the overall safety score and make final decision."""
    # Weight different aspects
    weights = {
        "moderation": 0.4,      # OpenAI moderation is most important
        "age_appropriate": 0.3,  # Age appropriateness is crucial
        "cultural": 0.2,        # Cultural sensitivity important
        "educational": 0.1      # Educational value is bonus
    }
    
    # Get individual scores
    moderation_score = 0.0 if state["moderation_result"].get("flagged", False) else 1.0
    age_score = state.get("age_appropriateness_score", 0.8)
    cultural_score = state.get("cultural_sensitivity_score", 0.8)
    educational_score = state.get("educational_value_score", 0.5)
    
    # Calculate weighted average
    overall_score = (
        moderation_score * weights["moderation"] +
        age_score * weights["age_appropriate"] +
        cultural_score * weights["cultural"] +
        educational_score * weights["educational"]
    )
    
    # Determine approval status
    is_approved = overall_score >= settings.CONTENT_SAFETY_THRESHOLD
    needs_review = overall_score < 0.8  # Flag for manual review if below 0.8
    
    # Collect all recommendations
    all_recommendations = []
    
    # Add moderation recommendations
    if state["moderation_result"].get("flagged", False):
        flagged_categories = [
            cat for cat, flagged in state["moderation_result"]["categories"].items()
            if flagged
        ]
        all_recommendations.extend([
            f"Address {cat} content flagged by moderation" for cat in flagged_categories
        ])
    
    # Add existing recommendations
    all_recommendations.extend(state.get("recommendations", []))
    
    # Add score-based recommendations
    if overall_score < 0.5:
        all_recommendations.append("Content requires significant revision before approval")
    elif overall_score < 0.7:
        all_recommendations.append("Content needs improvement in multiple areas")
    
    return {
        "overall_safety_score": overall_score,
        "is_approved": is_approved,
        "needs_review": needs_review,
        "recommendations": list(set(all_recommendations))  # Remove duplicates
    }


def aggregate_safety_issues(state: ContentSafetyState) -> Dict[str, Any]:
    """Aggregate all safety issues from different analysis steps."""
    all_issues = []
    
    # Collect issues from all analysis steps
    for key in ["safety_issues"]:
        if key in state:
            all_issues.extend(state[key])
    
    # Sort by severity
    severity_order = {"high": 0, "medium": 1, "low": 2}
    all_issues.sort(key=lambda x: severity_order.get(x.get("severity", "low"), 2))
    
    return {"safety_issues": all_issues}


# Create the workflow
def create_content_safety_workflow():
    """Create the content safety workflow graph."""
    
    workflow = StateGraph(ContentSafetyState)
    
    # Add nodes
    workflow.add_node("moderation_check", run_openai_moderation)
    workflow.add_node("age_analysis", analyze_age_appropriateness) 
    workflow.add_node("cultural_analysis", analyze_cultural_sensitivity)
    workflow.add_node("educational_analysis", analyze_educational_value)
    workflow.add_node("aggregate_issues", aggregate_safety_issues)
    workflow.add_node("final_assessment", calculate_overall_safety)
    
    # Add edges - run analyses in parallel then aggregate
    workflow.set_entry_point("moderation_check")
    workflow.add_edge("moderation_check", "age_analysis")
    workflow.add_edge("age_analysis", "cultural_analysis")
    workflow.add_edge("cultural_analysis", "educational_analysis")
    workflow.add_edge("educational_analysis", "aggregate_issues")
    workflow.add_edge("aggregate_issues", "final_assessment")
    workflow.add_edge("final_assessment", END)
    
    return workflow.compile()


# Create singleton instance
content_safety_workflow = create_content_safety_workflow()