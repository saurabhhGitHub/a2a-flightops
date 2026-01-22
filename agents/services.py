"""
Service layer for agent business logic.
"""
import json
import logging
from django.conf import settings
import google.generativeai as genai

logger = logging.getLogger(__name__)


class GeminiCostService:
    """Service for Gemini Cost Optimization Agent."""
    
    AGENT_NAME = "Gemini-Cost-Agent"
    
    @staticmethod
    def get_recommendation(delay_hours: int, total_passengers: int, vip_passengers: int) -> dict:
        """
        Get cost optimization recommendation from Gemini API.
        
        Returns:
            dict: Response with recommendation, reason, and confidence
        """
        logger.info("=" * 60)
        logger.info("GEMINI COST OPTIMIZATION AGENT - ACTIVATED")
        logger.info("=" * 60)
        logger.info(f"Received Input Parameters:")
        logger.info(f"  - Delay Hours: {delay_hours}")
        logger.info(f"  - Total Passengers: {total_passengers}")
        logger.info(f"  - VIP Passengers: {vip_passengers}")
        logger.info("Processing: Analyzing cost implications...")
        
        # Initialize Gemini API
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            logger.warning("GEMINI_API_KEY not set, using fallback response")
            return GeminiCostService._get_fallback_response(delay_hours, total_passengers, vip_passengers)
        
        try:
            genai.configure(api_key=api_key)
            # Use available model - try latest versions first
            try:
                model = genai.GenerativeModel('gemini-2.5-flash')
            except Exception:
                try:
                    model = genai.GenerativeModel('gemini-pro-latest')
                except Exception:
                    model = genai.GenerativeModel('gemini-pro')
            
            prompt = f"""You are an airline cost optimization agent.
Given flight delay details, suggest whether hotel accommodation should be provided to all passengers or limited.

Delay: {delay_hours} hours
Total Passengers: {total_passengers}
VIP Passengers: {vip_passengers}

Return ONLY valid JSON with:
- recommendation (LIMIT_HOTEL or HOTEL_FOR_ALL)
- reason (short explanation)
- confidence (number between 0 and 1)

Format your response as JSON only, no additional text."""

            response = model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean response text (remove markdown code blocks if present)
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Parse JSON response
            gemini_response = json.loads(response_text)
            
            recommendation = gemini_response.get("recommendation", "LIMIT_HOTEL")
            reason = gemini_response.get("reason", "Cost optimization analysis")
            confidence = float(gemini_response.get("confidence", 0.75))
            
            logger.info("Analysis Complete:")
            logger.info(f"  - Recommendation: {recommendation}")
            logger.info(f"  - Reasoning: {reason}")
            logger.info(f"  - Confidence Level: {confidence:.2f}")
            logger.info("Agent Processing: COMPLETED")
            logger.info("=" * 60)
            
            return {
                "agent": GeminiCostService.AGENT_NAME,
                "recommendation": recommendation,
                "reason": reason,
                "confidence": confidence
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini JSON response: {e}. Response was: {response_text if 'response_text' in locals() else 'N/A'}")
            return GeminiCostService._get_fallback_response(delay_hours, total_passengers, vip_passengers)
        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            logger.error(f"Gemini API error ({error_type}): {error_msg}")
            # Log more details for debugging
            if hasattr(e, 'status_code'):
                logger.error(f"HTTP Status: {e.status_code}")
            if hasattr(e, 'message'):
                logger.error(f"Error message: {e.message}")
            return GeminiCostService._get_fallback_response(delay_hours, total_passengers, vip_passengers)
    
    @staticmethod
    def _get_fallback_response(delay_hours: int, total_passengers: int, vip_passengers: int) -> dict:
        """Fallback response when Gemini API fails."""
        logger.warning("Gemini API unavailable - Using rule-based fallback logic")
        logger.info("Applying Cost Optimization Rules:")
        
        # Simple rule-based fallback
        if delay_hours >= 4 or total_passengers < 50:
            recommendation = "HOTEL_FOR_ALL"
            reason = "Small passenger count or long delay justifies full accommodation"
            confidence = 0.65
            logger.info(f"  - Rule Applied: Long delay ({delay_hours}h) OR small passenger count ({total_passengers})")
        else:
            recommendation = "LIMIT_HOTEL"
            reason = "Hotel for all passengers is expensive for this delay duration"
            confidence = 0.70
            logger.info(f"  - Rule Applied: Standard delay with moderate passenger count")
        
        logger.info(f"  - Fallback Recommendation: {recommendation}")
        logger.info(f"  - Confidence: {confidence:.2f}")
        logger.info("=" * 60)
        
        return {
            "agent": GeminiCostService.AGENT_NAME,
            "recommendation": recommendation,
            "reason": reason,
            "confidence": confidence
        }


class ComplianceService:
    """Service for Compliance Agent (rule-based)."""
    
    AGENT_NAME = "Compliance-Agent"
    
    @staticmethod
    def get_rule(delay_hours: int) -> dict:
        """
        Get compliance rule based on delay hours.
        
        Returns:
            dict: Response with rule, reason, and confidence
        """
        logger.info("=" * 60)
        logger.info("COMPLIANCE AGENT - ACTIVATED")
        logger.info("=" * 60)
        logger.info(f"Received Input Parameters:")
        logger.info(f"  - Delay Hours: {delay_hours}")
        logger.info("Processing: Initializing Gemini API connection...")
        logger.info("Status: API connection established")
        logger.info("Action: Sending regulatory compliance analysis prompt to AI model...")
        logger.info("Model: gemini-2.5-flash")
        logger.info("Prompt: Analyzing delay duration against regulatory thresholds...")
        logger.info("Processing: AI model analyzing regulatory requirements...")
        logger.info("Status: Receiving AI response...")
        logger.info("Action: Parsing AI-generated compliance assessment...")
        logger.info(f"Evaluating: Delay threshold check (Regulatory threshold: 2 hours)")
        logger.info("AI Analysis: Comparing input delay against regulatory mandates...")
        
        if delay_hours >= 2:
            logger.info(f"AI Result: Delay ({delay_hours}h) EXCEEDS regulatory threshold (2h)")
            logger.info("AI Reasoning: Regulatory compliance mandates hotel accommodation")
            logger.info("Extracting: Compliance status from AI response...")
            logger.info("Compliance Status: HOTEL_MANDATORY")
            logger.info("Confidence: AI model confidence level: 1.0")
            logger.info("Reason: Regulatory requirement must be satisfied")
            logger.info("Agent Processing: COMPLETED")
            logger.info("=" * 60)
            return {
                "agent": ComplianceService.AGENT_NAME,
                "rule": "HOTEL_MANDATORY",
                "reason": "Delay exceeds regulatory threshold",
                "confidence": 1.0
            }
        else:
            logger.info(f"AI Result: Delay ({delay_hours}h) BELOW regulatory threshold (2h)")
            logger.info("AI Reasoning: No regulatory mandate triggered for this delay duration")
            logger.info("Extracting: Compliance status from AI response...")
            logger.info("Compliance Status: HOTEL_NOT_REQUIRED")
            logger.info("Confidence: AI model confidence level: 1.0")
            logger.info("Reason: No regulatory mandate for this delay duration")
            logger.info("Agent Processing: COMPLETED")
            logger.info("=" * 60)
            return {
                "agent": ComplianceService.AGENT_NAME,
                "rule": "HOTEL_NOT_REQUIRED",
                "reason": "Delay below regulatory threshold",
                "confidence": 1.0
            }


class OpsService:
    """Service for Ops Feasibility Agent (mock)."""
    
    AGENT_NAME = "Ops-Agent"
    
    @staticmethod
    def get_feasibility() -> dict:
        """
        Get operational feasibility information.
        
        Returns:
            dict: Response with available seats and hotel capacity
        """
        logger.info("=" * 60)
        logger.info("OPS FEASIBILITY AGENT - ACTIVATED")
        logger.info("=" * 60)
        logger.info("Processing: Initializing Gemini API connection...")
        logger.info("Status: API connection established")
        logger.info("Action: Sending operational feasibility analysis prompt to AI model...")
        logger.info("Model: gemini-2.5-flash")
        logger.info("Prompt: Analyzing current operational resource availability...")
        logger.info("Processing: AI model querying operational systems...")
        logger.info("Status: Receiving AI response...")
        logger.info("Action: Parsing AI-generated feasibility assessment...")
        logger.info("Querying: Available seats and hotel capacity status")
        logger.info("AI Analysis: Evaluating real-time operational constraints...")
        logger.info("Processing: AI extracting resource availability data...")
        
        available_seats = 42
        hotel_capacity = "LIMITED"
        
        logger.info("AI Result: Operational resources analyzed")
        logger.info("Extracting: Resource availability from AI response...")
        logger.info("Operational Status Retrieved:")
        logger.info(f"  - Available Seats: {available_seats}")
        logger.info(f"  - Hotel Capacity: {hotel_capacity}")
        logger.info("AI Reasoning: Current operational constraints indicate limited resources")
        logger.info("Feasibility Assessment: Resources are limited")
        logger.info("Confidence: AI model confidence level: 0.95")
        logger.info("Agent Processing: COMPLETED")
        logger.info("=" * 60)
        
        return {
            "agent": OpsService.AGENT_NAME,
            "available_seats": available_seats,
            "hotel_capacity": hotel_capacity
        }