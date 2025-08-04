#!/usr/bin/env python3
"""
AI Response Generator for LinkedIn Messages
------------------------------------------
This module handles generating appropriate responses to LinkedIn messages,
particularly job offers, using various AI models.
"""

import os
import json
import random
from typing import Dict, List, Optional, Tuple

# Optional: Import OpenAI for AI responses
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class AIResponseGenerator:
    """Generates appropriate responses to LinkedIn messages using AI."""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize the response generator."""
        self.openai_api_key = openai_api_key
        
        if OPENAI_AVAILABLE and self.openai_api_key:
            openai.api_key = self.openai_api_key
            
        # Load response templates
        self.templates = self._load_templates()
        
        # Define message type keywords for classification (including German equivalents)
        self.message_types = {
            "job_offer": [
                # English job offer keywords
                "job", "position", "opportunity", "opening", "role", "vacancy",
                "recruiter", "recruiting", "talent", "hiring", "career", "employment",
                "interview", "application", "apply", "resume", "cv", "profile",
                # German job offer keywords
                "stelle", "position", "rolle", "jobangebot", "stellenangebot", "karriere",
                "bewerbung", "lebenslauf", "berufserfahrung", "arbeitgeber", "unternehmen",
                "herausforderung", "verantwortung", "team", "firma", "gehalt", "vergütung"
            ],
            "technical_recruiter": [
                # English technical keywords
                "experience", "skills", "qualification", "technical", "developer", "engineer", 
                "programming", "code", "software", "devops", "cloud", "aws", "azure", "gcp",
                "kubernetes", "docker", "ci/cd", "pipeline", "infrastructure", "architect",
                # German technical keywords
                "erfahrung", "kenntnisse", "qualifikation", "entwickler", "ingenieur",
                "programmierung", "software", "infrastruktur", "automatisierung", "optimierung",
                "terraform", "ansible", "skalierbar", "transformation", "technologien"
            ],
            "networking": [
                # English networking keywords
                "connect", "network", "introduction", "meetup", "event", "conference",
                "webinar", "community", "group", "forum", "discussion", "chat", "conversation",
                # German networking keywords
                "verbinden", "netzwerk", "vorstellung", "treffen", "veranstaltung", "konferenz",
                "gemeinschaft", "gruppe", "forum", "diskussion", "unterhaltung"
            ],
            "sales_pitch": [
                # English sales keywords
                "product", "service", "solution", "offer", "discount", "price", "cost",
                "demo", "presentation", "showcase", "trial", "free", "premium", "subscription",
                # German sales keywords
                "produkt", "dienst", "lösung", "angebot", "rabatt", "preis", "kosten",
                "demo", "präsentation", "vorführung", "testversion", "kostenlos", "premium", "abonnement"
            ]
        }
        
        # Define recruiter role indicators (words that strongly suggest a recruiter message)
        self.recruiter_indicators = [
            # English
            "recruiter", "talent acquisition", "headhunter", "sourcing", "staffing", "placement",
            "account manager", "recruiting", "talent", "hr", "human resources", "personnel",
            # German
            "personalberater", "personalvermittler", "personalreferent", "personaler",
            "recruiter", "account manager", "personalwesen", "personalsuche"
        ]
    
    def _load_templates(self) -> Dict[str, List[str]]:
        """Load response templates from file or use defaults."""
        templates_path = os.path.join(os.path.dirname(__file__), "response_templates.json")
        
        default_templates = {
            "job_offer": [
                "Thank you for reaching out about this opportunity. I appreciate you considering me for this role. Could you please share more details about the position and requirements? I'd be interested in learning more to see if it aligns with my experience and career goals.",
                "I appreciate your message regarding this opportunity. I'm always open to discussing interesting roles. Could you provide more information about the position, including responsibilities and requirements? This would help me determine if it's a good fit for my background.",
                "Thanks for thinking of me for this position. I'd like to learn more about the role and your company. Could you share details about the team, tech stack, and expectations? This would help me understand if it aligns with my current career direction."
            ],
            "recruiter_intro": [
                "Thank you for connecting. I'm always interested in learning about new opportunities that align with my skills and career goals. Could you tell me more about the specific role you have in mind?",
                "I appreciate you reaching out. I'm selectively exploring new opportunities at the moment. Could you share more details about the position and company you're recruiting for?"
            ],
            "follow_up": [
                "Thank you for the additional information. I've reviewed the details, and I'm interested in discussing this further. Would you be available for a brief call to talk about the role in more depth?",
                "Thanks for sharing more about the position. Based on what you've described, I'd like to learn more. What would be the next steps in the process?"
            ],
            "not_interested": [
                "Thank you for thinking of me for this opportunity. After careful consideration, I don't think this is the right fit for me at this time. I appreciate your consideration and wish you success in finding the right candidate.",
                "I appreciate you reaching out about this role. After reviewing the details, I've decided to focus on opportunities that more closely align with my current career direction. Thank you for considering me, and I wish you all the best in your search."
            ]
        }
        
        try:
            if os.path.exists(templates_path):
                with open(templates_path, 'r') as f:
                    return json.load(f)
            return default_templates
        except Exception:
            return default_templates
    
    def classify_message(self, message_content):
        """Determine if a message is a job offer or recruiter message and classify its type.
        
        Args:
            message_content (str): The content of the message
            
        Returns:
            tuple: (is_job_offer, message_type) where is_job_offer is a boolean and message_type is a string
        """
        # Convert to lowercase for case-insensitive matching
        message_lower = message_content.lower()
        
        # Check for recruiter signature indicators
        has_recruiter_signature = False
        for indicator in self.recruiter_indicators:
            if indicator.lower() in message_lower:
                has_recruiter_signature = True
                break
        
        # Track keyword counts for each message type
        type_scores = {}
        for msg_type, keywords in self.message_types.items():
            # Count keyword occurrences
            keyword_count = sum(1 for keyword in keywords if keyword in message_lower)
            
            # Apply context-based bonuses
            if msg_type == "job_offer" or msg_type == "technical_recruiter":
                # Bonus for longer messages (job offers tend to be longer)
                if len(message_content) > 500:
                    keyword_count += 2
                
                # Bonus if message contains recruiter signature
                if has_recruiter_signature:
                    keyword_count += 3
                
                # Bonus for specific job-related phrases
                job_phrases = ["looking for", "we are seeking", "suche", "stelle", "position", 
                              "opportunity", "opening", "vacancy", "job", "role", "arbeit"]
                for phrase in job_phrases:
                    if phrase in message_lower:
                        keyword_count += 1
                        break
            
            type_scores[msg_type] = keyword_count
        
        # Determine the most likely message type
        max_score = 0
        detected_type = "general_message"
        for msg_type, score in type_scores.items():
            if score > max_score:
                max_score = score
                detected_type = msg_type
        
        # Special case: if it contains technical keywords AND has recruiter signature,
        # it's almost certainly a technical job offer
        if has_recruiter_signature and type_scores["technical_recruiter"] >= 2:
            detected_type = "technical_recruiter"
            max_score = max(max_score, 5)  # Ensure it passes the threshold
        
        # Consider it a job offer if it's classified as job_offer or technical_recruiter
        # and has at least 3 matching keywords
        is_job_related = detected_type in ["job_offer", "technical_recruiter"]
        has_enough_keywords = max_score >= 3
        
        # Special override for German job offers that mention DevOps, Engineer, etc.
        if not (is_job_related and has_enough_keywords):
            tech_terms = ["devops", "engineer", "entwickler", "cloud", "aws", "azure", 
                         "kubernetes", "docker", "terraform", "ansible", "pipeline", "ci/cd"]
            
            tech_term_count = sum(1 for term in tech_terms if term in message_lower)
            if tech_term_count >= 2 and len(message_content) > 300:  # Longer message with tech terms
                return True, "technical_recruiter"
        
        return (is_job_related and has_enough_keywords), detected_type
    
    def generate_response(self, message_content, sender_name="Recruiter"):
        """Generate a response to a job offer message.
        
        Args:
            message_content (str): The content of the message
            sender_name (str): The name of the sender
            
        Returns:
            tuple: (is_job_offer, response) where is_job_offer is a boolean and response is a string
        """
        # Classify the message
        is_job_offer, message_type = self.classify_message(message_content)
        
        # Generate appropriate response based on message type
        if message_type == "job_offer":
            response = (
                f"Hello {sender_name},\n\n"
                "Thank you for reaching out regarding this opportunity. "
                "I appreciate your consideration. \n\n"
                "At the moment, I'm focusing on roles that align with my expertise in DevOps and cloud infrastructure. "
                "Could you share more details about the position, including the tech stack and responsibilities? \n\n"
                "I'm particularly interested in positions involving Kubernetes, CI/CD pipelines, and cloud platforms like AWS or Azure.\n\n"
                "Looking forward to hearing more,\n"
                "[Your Name]"
            )
        elif message_type == "technical_recruiter":
            response = (
                f"Hello {sender_name},\n\n"
                "Thank you for reaching out about this technical opportunity. "
                "I'm always interested in discussing roles that leverage my DevOps and cloud expertise. \n\n"
                "Could you provide more specifics about the technical requirements, team structure, and project scope? "
                "I'd like to understand how my experience with containerization, infrastructure as code, and automation "
                "might be valuable for this position.\n\n"
                "Best regards,\n"
                "[Your Name]"
            )
        elif message_type == "networking":
            response = (
                f"Hello {sender_name},\n\n"
                "Thank you for connecting! I'm always interested in expanding my professional network, "
                "especially with others in the DevOps and cloud infrastructure space. \n\n"
                "Feel free to reach out if you'd like to discuss industry trends or potential collaborations.\n\n"
                "Best regards,\n"
                "[Your Name]"
            )
        elif message_type == "sales_pitch":
            response = (
                f"Hello {sender_name},\n\n"
                "Thank you for sharing information about your product/service. "
                "At the moment, I'm not actively looking for new tools or services, "
                "but I appreciate you thinking of me.\n\n"
                "Best regards,\n"
                "[Your Name]"
            )
        else:
            response = (
                f"Hello {sender_name},\n\n"
                "Thank you for your message. I appreciate you reaching out. "
                "Could you provide a bit more context about your inquiry? "
                "I'd be happy to continue the conversation once I better understand your message.\n\n"
                "Best regards,\n"
                "[Your Name]"
            )
        
        return is_job_offer, response
    
    def generate_template_response(self, message_type: str) -> str:
        """Generate a response using templates."""
        if message_type in self.templates and self.templates[message_type]:
            return random.choice(self.templates[message_type])
        return self.templates["job_offer"][0]  # Default to first job offer template
    
    def generate_ai_response(self, message_text: str, message_type: str, sender_name: str) -> str:
        """Generate a response using OpenAI."""
        if not OPENAI_AVAILABLE or not self.openai_api_key:
            return self.generate_template_response(message_type)
        
        try:
            system_prompt = (
                "You are an assistant helping to respond to LinkedIn messages, particularly job offers. "
                "Keep responses professional, brief (2-4 sentences), and polite. "
                "Don't commit to anything specific. Ask clarifying questions about the role if appropriate. "
                "Be friendly but not overly enthusiastic."
            )
            
            user_prompt = (
                f"Generate a brief, professional response to this LinkedIn message from {sender_name}: \n\n"
                f"{message_text}\n\n"
                f"Message type: {message_type}"
            )
            
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
        except Exception:
            # Fall back to template response if OpenAI fails
            return self.generate_template_response(message_type)
    
    def generate_response(self, message_text: str, sender_name: str) -> Tuple[bool, str]:
        """
        Generate a response to a LinkedIn message.
        
        Args:
            message_text: The text of the message to respond to
            sender_name: The name of the message sender
            
        Returns:
            Tuple of (is_job_offer, suggested_response)
        """
        is_job_offer, message_type = self.classify_message(message_text)
        
        if OPENAI_AVAILABLE and self.openai_api_key:
            response = self.generate_ai_response(message_text, message_type, sender_name)
        else:
            response = self.generate_template_response(message_type)
            
        return is_job_offer, response
