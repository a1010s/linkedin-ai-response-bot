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
            # Initialize OpenAI client (version 1.98.0+)
            try:
                self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
                print("[DEBUG] ✓ OpenAI client initialized successfully")
            except Exception as e:
                print(f"[DEBUG] ✗ Failed to initialize OpenAI client: {str(e)}")
                print("[DEBUG] Falling back to contextual templates")
                self.openai_client = None
        else:
            self.openai_client = None
            
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
    
    def detect_language(self, message_content: str) -> str:
        """
        Detect the language of the incoming message.
        Returns 'de' for German, 'en' for English.
        """
        german_indicators = [
            'hallo', 'guten', 'tag', 'ich', 'bin', 'wir', 'sind', 'haben', 'können',
            'möchten', 'würden', 'stelle', 'position', 'unternehmen', 'firma',
            'bewerbung', 'lebenslauf', 'gehalt', 'vergütung', 'remote', 'homeoffice',
            'interviews', 'gespräche', 'prozess', 'ablauf', 'viele', 'grüße',
            'freundliche', 'beste', 'mit', 'für', 'auf', 'bei', 'zu', 'von'
        ]
        
        message_lower = message_content.lower()
        german_count = sum(1 for word in german_indicators if word in message_lower)
        
        # If we find several German indicators, assume German
        if german_count >= 3:
            return 'de'
        return 'en'
    
    def generate_response(self, message_content, sender_name="Recruiter"):
        """Generate a response to a job offer message.
        
        Args:
            message_content (str): The content of the message
            sender_name (str): The name of the sender
            
        Returns:
            tuple: (is_job_offer, response) where is_job_offer is a boolean and response is a string
        """
        # Classify the message first
        is_job_offer, message_type = self.classify_message(message_content)
        
        # Debug logging to see what's happening
        print(f"[DEBUG] OPENAI_AVAILABLE: {OPENAI_AVAILABLE}")
        print(f"[DEBUG] self.openai_api_key: {bool(self.openai_api_key)}")
        print(f"[DEBUG] API key length: {len(self.openai_api_key) if self.openai_api_key else 0}")
        
        # Use OpenAI API if available, otherwise fall back to contextual templates
        if OPENAI_AVAILABLE and self.openai_api_key:
            print("[DEBUG] ✓ Using OpenAI API for response generation")
            response = self.generate_ai_response(message_content, message_type, sender_name)
        else:
            print("[DEBUG] ✗ Falling back to template response")
            print(f"[DEBUG] Reason: OPENAI_AVAILABLE={OPENAI_AVAILABLE}, has_api_key={bool(self.openai_api_key)}")
            # Fall back to contextual response with language detection
            _, response = self.generate_contextual_response(message_content, sender_name)
        
        return is_job_offer, response
    
    def generate_template_response(self, message_type: str) -> str:
        """Generate a response using templates."""
        if message_type in self.templates and self.templates[message_type]:
            return random.choice(self.templates[message_type])
        return self.templates["job_offer"][0]  # Default to first job offer template
    
    def generate_ai_response(self, message_text: str, message_type: str, sender_name: str) -> str:
        """Generate a response using OpenAI."""
        print(f"[DEBUG] generate_ai_response called with sender: {sender_name}")
        print(f"[DEBUG] OPENAI_AVAILABLE in method: {OPENAI_AVAILABLE}")
        print(f"[DEBUG] API key available in method: {bool(self.openai_api_key)}")
        
        if not OPENAI_AVAILABLE or not self.openai_client:
            print("[DEBUG] ✗ OpenAI not available, falling back to contextual template")
            # Use contextual response with language detection as fallback
            _, contextual_response = self.generate_contextual_response(message_text, sender_name)
            return contextual_response
        
        print("[DEBUG] ✓ Making OpenAI API call...")
        try:
            system_prompt = (
                "You are responding to LinkedIn messages as Andrei Stegaru, a Senior DevOps and Platform Engineer. "
                "Your expertise: Kubernetes, Terraform, Ansible, AWS/Azure, Container technologies, Linux, infrastructure automation, and internal tools/scripts. "
                "You can program in Golang but at DevOps/tooling level, not as a full-time software developer. "
                "Keep responses professional, brief (2–4 sentences), and polite. "
                "Mirror the tone and formality of the message you receive: if the person uses 'Sie' or formal English, reply formally. "
                "If they use 'du' or informal English, reply informally. Use the same language (German or English) as the original message. "
                "Don't commit to anything specific. Ask clarifying questions about the role. "
                "Always ask about: expected salary/salary range, number of planned interviews, and if fully remote work is possible. "
                "If the role doesn't match your DevOps background (e.g., pure software development), express interest but ask if your DevOps expertise could be a fit. "
                "Always sign with 'Viele Grüße, Andrei' (German) or 'Best regards, Andrei' (English). "
                "Be friendly but not overly enthusiastic."
            )
            
            user_prompt = (
                f"Generate a professional response to this LinkedIn message from {sender_name}: \n\n"
                f"{message_text}\n\n"
                f"Message type: {message_type}\n\n"
                f"Important: Analyze if this role matches your DevOps background. If it's a pure software development role, "
                f"express interest but ask if your DevOps expertise and infrastructure automation skills could be a good fit. "
                f"Always include your 3 key questions about salary, interviews, and remote work. "
                f"Sign the message properly with your name."
            )
            
            print(f"[DEBUG] Calling OpenAI with model: gpt-4o-mini")
            print(f"[DEBUG] System prompt: {system_prompt[:100]}...")
            print(f"[DEBUG] User prompt: {user_prompt[:100]}...")
            
            # Use modern OpenAI client API (version 1.98.0+)
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content.strip()
            print(f"[DEBUG] ✓ OpenAI API call successful!")
            print(f"[DEBUG] AI Response: {ai_response[:100]}...")
            return ai_response
        except Exception as e:
            print(f"[DEBUG] ✗ OpenAI API call failed: {str(e)}")
            # Fall back to contextual response with language detection if OpenAI fails
            _, contextual_response = self.generate_contextual_response(message_text, sender_name)
            return contextual_response
    
    # Removed duplicate generate_response method - using the OpenAI-enabled version above
    
    def generate_contextual_response(self, message_content, sender_name="Recruiter"):
        """Generate a contextual response with language detection and specific requirements.
        
        Args:
            message_content (str): The content of the message
            sender_name (str): The name of the sender
            
        Returns:
            tuple: (is_job_offer, response) where is_job_offer is a boolean and response is a string
        """
        # Classify the message and detect language
        is_job_offer, message_type = self.classify_message(message_content)
        language = self.detect_language(message_content)
        
        # Generate appropriate response based on message type and language
        if language == 'de':
            # German responses
            if message_type == "job_offer" or message_type == "technical_recruiter":
                response = (
                    f"Hallo {sender_name},\n\n"
                    "vielen Dank für Ihre Nachricht bezüglich dieser Gelegenheit. "
                    "Ich schätze Ihr Interesse sehr.\n\n"
                    "Als Senior DevOps und Platform Engineer mit Fokus auf Kubernetes, Terraform und Container-Technologien "
                    "bin ich immer interessiert an spannenden Herausforderungen.\n\n"
                    "Könnten Sie mir bitte weitere Details mitteilen:\n"
                    "• Wie ist die Gehaltsvorstellung/der Gehaltsbereich?\n"
                    "• Wie viele Interview-Runden sind im Recruiting-Prozess vorgesehen?\n"
                    "• Ist 100% Remote-Arbeit möglich?\n\n"
                    "Diese Informationen würden mir helfen zu verstehen, ob die Position zu meiner aktuellen Karriererichtung passt.\n\n"
                    "Viele Grüße,\n"
                    "Andrei"
                )
            elif message_type == "sales_pitch":
                response = (
                    f"Hallo {sender_name},\n\n"
                    "vielen Dank für die Information über Ihr Produkt/Ihre Lösung. "
                    "Als DevOps Engineer bin ich immer interessiert an innovativen Tools, "
                    "die unsere Infrastruktur und Prozesse verbessern können.\n\n"
                    "Könnten Sie mir mehr Details über die technische Integration und "
                    "Kompatibilität mit Kubernetes/Container-Umgebungen mitteilen?\n\n"
                    "Beste Grüße,\n"
                    "Andrei"
                )
            else:
                response = (
                    f"Hallo {sender_name},\n\n"
                    "vielen Dank für Ihre Nachricht. Ich schätze es, dass Sie sich gemeldet haben.\n\n"
                    "Könnten Sie mir etwas mehr Kontext zu Ihrer Anfrage geben? "
                    "Gerne setze ich das Gespräch fort, sobald ich Ihre Nachricht besser verstehe.\n\n"
                    "Beste Grüße,\n"
                    "Andrei"
                )
        else:
            # English responses
            if message_type == "job_offer" or message_type == "technical_recruiter":
                response = (
                    f"Hello {sender_name},\n\n"
                    "Thank you for reaching out regarding this opportunity. "
                    "I appreciate your consideration.\n\n"
                    "As a Senior DevOps and Platform Engineer with focus on Kubernetes, Terraform, and container technologies, "
                    "I'm always interested in exciting challenges.\n\n"
                    "Could you please share more details about:\n"
                    "• What is the expected salary range?\n"
                    "• How many interview rounds are in the recruiting process?\n"
                    "• Is 100% remote work possible?\n\n"
                    "This information would help me understand if the role aligns with my current career direction.\n\n"
                    "Best regards,\n"
                    "Andrei"
                )
            elif message_type == "sales_pitch":
                response = (
                    f"Hello {sender_name},\n\n"
                    "Thank you for sharing information about your product/solution. "
                    "As a DevOps Engineer, I'm always interested in innovative tools "
                    "that can improve our infrastructure and processes.\n\n"
                    "Could you provide more details about technical integration and "
                    "compatibility with Kubernetes/container environments?\n\n"
                    "Best regards,\n"
                    "Andrei"
                )
            else:
                response = (
                    f"Hello {sender_name},\n\n"
                    "Thank you for your message. I appreciate you reaching out.\n\n"
                    "Could you provide a bit more context about your inquiry? "
                    "I'd be happy to continue the conversation once I better understand your message.\n\n"
                    "Best regards,\n"
                    "Andrei"
                )
        
        return is_job_offer, response
