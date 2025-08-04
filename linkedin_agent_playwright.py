#!/usr/bin/env python3
"""
LinkedIn Job Offer Auto-Responder using Playwright
This script logs into LinkedIn, checks for unread messages,
identifies job offers, and suggests AI-generated responses for approval.
"""

import os
import asyncio
import json
import random
import re
import select
import sys
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from dotenv import load_dotenv
from playwright.async_api import async_playwright, Browser, Page, Playwright
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from ai_response_generator import AIResponseGenerator

# Initialize Rich console for better terminal output
console = Console()

class LinkedInAgentPlaywright:
    """LinkedIn agent using Playwright for automation."""
    
    def __init__(self):
        """Initialize the LinkedIn agent."""
        # Load environment variables
        load_dotenv()
        self.email = os.getenv("LINKEDIN_EMAIL")
        self.password = os.getenv("LINKEDIN_PASSWORD")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # Initialize AI response generator with OpenAI API key
        self.ai_response_generator = AIResponseGenerator(openai_api_key=self.openai_api_key)
        
        # Log AI configuration status
        if self.openai_api_key:
            console.print("[bold green]✓ OpenAI API configured - using AI-generated responses[/bold green]")
        else:
            console.print("[bold yellow]⚠ OpenAI API not configured - using improved template responses[/bold yellow]")
            console.print("[dim]Add OPENAI_API_KEY to .env file for AI-generated responses[/dim]")
        
        # Initialize Playwright objects
        self.playwright = None
        self.browser = None
        self.page = None
        self.context = None
        
        # Non-interactive mode settings
        self.non_interactive = os.getenv("NON_INTERACTIVE", "false").lower() == "true"
        self.auto_approve = os.getenv("AUTO_APPROVE", "false").lower() == "true"
        self.response_timeout = int(os.getenv("RESPONSE_TIMEOUT", "30"))  # Default 30 seconds
        
        # Check if credentials are available
        if not self.email or not self.password:
            console.print("[bold red]LinkedIn credentials not found in .env file![/bold red]")
            if self.non_interactive:
                console.print("[bold red]Cannot prompt for credentials in non-interactive mode![/bold red]")
                sys.exit(1)
            else:
                self.email = Prompt.ask("[bold blue]Enter your LinkedIn email[/bold blue]")
                self.password = Prompt.ask("[bold blue]Enter your LinkedIn password[/bold blue]", password=True)
    
    async def setup_browser(self):
        """Set up and configure the Playwright browser."""
        console.print("[bold blue]Setting up browser...[/bold blue]")
        
        self.playwright = await async_playwright().start()
        
        # Configure browser with more realistic settings to avoid detection
        console.print("[bold blue]Launching browser with human-like properties...[/bold blue]")
        browser_type = self.playwright.chromium
        self.browser = await browser_type.launch(
            headless=True,  # Set to True for Docker compatibility
            slow_mo=100,  # Increase delay for better visibility
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox'
            ]
        )
        
        # Create a context with viewport and user agent
        self.context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='Europe/Berlin',
            has_touch=False,
            is_mobile=False
        )
        
        # Enable JavaScript permissions that LinkedIn might require
        await self.context.grant_permissions(['geolocation', 'notifications'])
        
        # Create page from context
        self.page = await self.context.new_page()
        
        # Add additional headers to appear more like a real browser
        await self.page.set_extra_http_headers({
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'sec-ch-ua': '"Chromium";v="116", "Not A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"'
        })
        
        console.print("[bold green]Browser setup complete[/bold green]")
    
    async def human_delay(self, min_seconds, max_seconds):
        """Wait for a random amount of time to simulate human behavior."""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)
    
    async def slow_scroll(self):
        """Scroll down slowly like a human would."""
        # Get the page height
        page_height = await self.page.evaluate("document.body.scrollHeight")
        viewport_height = await self.page.evaluate("window.innerHeight")
        
        # Scroll in small increments with random delays
        current_position = 0
        while current_position < page_height:
            scroll_amount = random.randint(100, 300)  # Random scroll amount
            current_position += scroll_amount
            await self.page.evaluate(f"window.scrollTo(0, {current_position})")
            await self.human_delay(0.3, 0.7)  # Random delay between scrolls
    
    async def login(self):
        """Log in to LinkedIn using saved cookies or credentials."""
        console.print("[bold blue]Logging in to LinkedIn...[/bold blue]")
        
        try:
            # First, check if we have saved cookies
            cookies_file = "linkedin_cookies.json"
            
            if os.path.exists(cookies_file):
                console.print(f"[bold blue]Found saved cookies at {cookies_file}[/bold blue]")
                
                try:
                    # Load cookies from file
                    with open(cookies_file, "r") as f:
                        cookies = json.load(f)
                    
                    # Add cookies to browser context
                    console.print("[bold blue]Loading saved cookies...[/bold blue]")
                    await self.context.add_cookies(cookies)
                    
                    # Add random delay before navigation (more human-like)
                    await self.human_delay(1, 3)
                    
                    # Navigate to LinkedIn homepage with increased timeout
                    console.print("[bold blue]Navigating to LinkedIn with cookies...[/bold blue]")
                    try:
                        # Use a longer timeout for the initial navigation
                        await self.page.goto("https://www.linkedin.com/feed/", timeout=60000)  # 60 seconds timeout
                        
                        # Wait like a human would
                        await self.human_delay(2, 4)
                        
                        # Check if we're logged in
                        if await self.page.locator(".feed-identity-module, .global-nav").count() > 0:
                            console.print("[bold green]Cookie login successful![/bold green]")
                            return True
                        else:
                            console.print("[bold yellow]Cookie login failed. Cookies may be expired.[/bold yellow]")
                            console.print("[bold yellow]Please run save_linkedin_cookies.py to create new cookies.[/bold yellow]")
                            return False
                    except Exception as e:
                        console.print(f"[bold yellow]Navigation with cookies timed out: {str(e)}[/bold yellow]")
                        console.print("[bold yellow]LinkedIn may be detecting and blocking automated access.[/bold yellow]")
                        return False
                        
                except Exception as e:
                    console.print(f"[bold red]Error loading cookies: {str(e)}[/bold red]")
                    console.print("[bold yellow]Falling back to credential login...[/bold yellow]")
            else:
                console.print(f"[bold yellow]No saved cookies found at {cookies_file}[/bold yellow]")
                console.print("[bold yellow]Please run save_linkedin_cookies.py to create cookies.[/bold yellow]")
                console.print("[bold yellow]Falling back to credential login...[/bold yellow]")
            
            # If we reach here, cookie login failed or wasn't available
            # Proceed with standard credential login as a fallback
            
            # Navigate to LinkedIn homepage first (more natural flow)
            console.print("[bold blue]Navigating to LinkedIn homepage...[/bold blue]")
            await self.page.goto("https://www.linkedin.com/")
            await self.human_delay(2, 4)  # Wait like a human
            
            # Look for sign-in button on homepage
            console.print("[bold blue]Looking for sign-in button...[/bold blue]")
            try:
                sign_in_button = await self.page.wait_for_selector("a.nav__button-secondary", timeout=5000)
                console.print("[bold green]Sign-in button found![/bold green]")
                await sign_in_button.click()
                await self.human_delay(1, 2)  # Wait like a human
            except Exception as e:
                # We might already be on the login page
                console.print(f"[bold yellow]No sign-in button found or error: {str(e)}[/bold yellow]")
            
            # Wait for the login form
            console.print("[bold blue]Waiting for username field...[/bold blue]")
            try:
                await self.page.wait_for_selector("#username", state="visible", timeout=10000)
                
                # Type credentials with human-like delays
                console.print("[bold blue]Entering email...[/bold blue]")
                await self.page.focus("#username")
                await self.page.type("#username", self.email, delay=random.uniform(100, 200))
                await self.human_delay(0.5, 1.5)
                
                console.print("[bold blue]Entering password...[/bold blue]")
                await self.page.focus("#password")
                await self.page.type("#password", self.password, delay=random.uniform(100, 200))
                await self.human_delay(0.5, 1.5)
                
                # Click submit and wait for navigation
                console.print("[bold blue]Clicking submit button...[/bold blue]")
                await self.page.click("button[type='submit']")
                
                # Wait for navigation with increased timeout
                console.print("[bold blue]Waiting for login to complete...[/bold blue]")
                await self.page.wait_for_selector(".feed-identity-module, .global-nav", timeout=30000)
                
                # Check for PIN verification
                if await self.page.locator("input#input__email_verification_pin, #verification-code").count() > 0:
                    console.print("[bold yellow]Security verification required![/bold yellow]")
                    console.print("[bold blue]Check your email for a verification PIN from LinkedIn[/bold blue]")
                    pin = Prompt.ask("[bold blue]Enter the verification PIN sent to your email[/bold blue]")
                    
                    # Find the right input field for the PIN
                    pin_field = await self.page.locator("input#input__email_verification_pin, #verification-code").first
                    await pin_field.fill(pin)
                    
                    # Find and click submit button
                    submit_button = await self.page.locator("button[type='submit']").first
                    await submit_button.click()
                    
                    await self.page.wait_for_load_state("networkidle", timeout=30000)
                
                # Check if login was successful
                if await self.page.locator(".feed-identity-module, .global-nav").count() > 0:
                    console.print("[bold green]Login successful![/bold green]")
                    
                    # Save cookies for future use
                    console.print("[bold blue]Saving cookies for future use...[/bold blue]")
                    cookies = await self.context.cookies()
                    with open(cookies_file, "w") as f:
                        json.dump(cookies, f)
                    console.print(f"[bold green]Cookies saved to {cookies_file}![/bold green]")
                    
                    return True
                else:
                    console.print("[bold red]Login failed or additional steps required[/bold red]")
                    return False
            except Exception as e:
                console.print(f"[bold red]Error during login: {str(e)}[/bold red]")
                return False
            
        except Exception as e:
            console.print(f"[bold red]Error during login: {str(e)}[/bold red]")
            await self.page.screenshot(path="login_error.png")
            console.print("[bold yellow]Screenshot of error saved as login_error.png[/bold yellow]")
            return False
    
    async def check_messages(self):
        """Navigate to LinkedIn messages and check for unread conversations."""
        console.print("[bold blue]Checking for unread messages...[/bold blue]")
        try:
            # Navigate to LinkedIn messaging with shorter timeouts
            console.print("[bold blue]Navigating to LinkedIn messaging...[/bold blue]")
            try:
                await self.page.goto("https://www.linkedin.com/messaging/", timeout=15000)
                await self.page.wait_for_load_state("domcontentloaded", timeout=10000)
                await self.page.wait_for_timeout(2000)  # Extra wait for UI to fully load
            except Exception as e:
                console.print(f"[bold yellow]Navigation issue: {str(e)}[/bold yellow]")
                # Try to continue anyway, the page might have partially loaded
            
            # Wait for messaging interface to load
            console.print("Waiting for messaging interface to load...")
            
            # Check for multiple selectors to find the messaging interface
            interface_loaded = False
            selectors = [
                ".msg-conversations-container__conversations-list",
                ".msg-overlay-list-bubble",
                ".msg-conversation-listitem",
                ".msg-conversation-card",
                ".msg-selectable-entity",
                ".msg-thread",
                ".msg-thread-list",
                ".msg-s-message-list-container"
            ]
            
            # Take a screenshot before checking selectors
            try:
                await self.page.screenshot(path="messaging_page.png")
                console.print("[bold blue]Saved screenshot of messaging page[/bold blue]")
            except Exception as e:
                console.print(f"[bold yellow]Could not save screenshot: {str(e)}[/bold yellow]")
            
            for selector in selectors:
                try:
                    # Use shorter timeout for each selector
                    await self.page.wait_for_selector(selector, timeout=3000)
                    console.print(f"[bold green]Messaging interface found using selector: {selector}[/bold green]")
                    interface_loaded = True
                    break
                except Exception:
                    console.print(f"[bold yellow]Selector {selector} not found[/bold yellow]")
                    continue
            
            if not interface_loaded:
                console.print("[bold red]Could not find messaging interface with any selector[/bold red]")
                # Take another screenshot to debug
                try:
                    await self.page.screenshot(path="interface_not_found.png")
                    console.print("[bold blue]Saved debug screenshot as interface_not_found.png[/bold blue]")
                except Exception as e:
                    console.print(f"[bold yellow]Could not save debug screenshot: {str(e)}[/bold yellow]")
                return []
            
            # First identify unread conversations by their indicators
            unread_indicators = [
                ".msg-conversation-card__unread-count",  # Primary unread count indicator
                ".notification-badge--show",  # Notification badge
                ".msg-conversation-listitem--unread",  # Alternative unread indicator
                ".artdeco-badge",  # Generic badge
                ".artdeco-notification-badge"  # Generic notification badge
            ]
            
            # Find all conversation elements first
            conversation_selectors = [
                ".msg-conversation-listitem",  # Primary conversation selector
                ".msg-conversation-card",  # Alternative conversation card
                ".msg-thread-list-item",  # Another possible conversation item
                ".msg-selectable-entity",  # Generic selectable entity
                "[data-control-name='overlay.conversation_item']"  # Data attribute selector
            ]
            
            # Get all conversation elements
            all_conversations = []
            for selector in conversation_selectors:
                try:
                    # Wait a bit before trying each selector
                    await self.page.wait_for_timeout(1000)
                    items = await self.page.locator(selector).all()
                    if items and len(items) > 0:
                        all_conversations = items
                        console.print(f"[bold green]Found {len(items)} conversation items with selector: {selector}[/bold green]")
                        break
                except Exception as e:
                    console.print(f"[bold yellow]Error with selector {selector}: {str(e)}[/bold yellow]")
                    continue
            
            if not all_conversations:
                console.print("[bold red]Could not find any conversation elements[/bold red]")
                return []
            
            # Now identify which conversations are unread
            unread_conversations = []
            for i, conversation in enumerate(all_conversations):
                try:
                    # Check if this conversation has any unread indicators
                    is_unread = False
                    for indicator in unread_indicators:
                        try:
                            has_indicator = await conversation.locator(indicator).count() > 0
                            if has_indicator:
                                is_unread = True
                                break
                        except Exception:
                            continue
                    
                    # If we couldn't find unread indicators, check if the conversation has a bold title
                    # which often indicates unread status
                    if not is_unread:
                        try:
                            # Check if the conversation title is bold (font-weight > 400)
                            title_elements = await conversation.locator(".msg-conversation-listitem__participant-names, .msg-conversation-card__participant-names").all()
                            for title in title_elements:
                                font_weight = await self.page.evaluate(
                                    "(element) => window.getComputedStyle(element).fontWeight", title
                                )
                                if font_weight and int(font_weight) > 400:  # Bold text
                                    is_unread = True
                                    break
                        except Exception:
                            pass
                    
                    if is_unread:
                        unread_conversations.append(conversation)
                        console.print(f"[bold green]Conversation {i+1} is unread[/bold green]")
                except Exception as e:
                    console.print(f"[bold yellow]Error checking conversation {i+1}: {str(e)}[/bold yellow]")
                    continue
            
            if not unread_conversations:
                console.print("[bold green]No unread messages found[/bold green]")
                return []
            
            console.print(f"[bold green]Found {len(unread_conversations)} total unread conversations[/bold green]")
            
            # Limit processing to a reasonable number to avoid excessive processing
            max_to_process = min(len(unread_conversations), 20)  # Process at most 20 conversations
            if len(unread_conversations) > max_to_process:
                console.print(f"[bold yellow]Limiting to processing {max_to_process} out of {len(unread_conversations)} unread conversations[/bold yellow]")
                unread_conversations = unread_conversations[:max_to_process]
            
            # Process each unread conversation IMMEDIATELY after clicking (like test script)
            for i, unread in enumerate(unread_conversations):
                try:
                    # Click on the conversation to open it
                    console.print(f"[bold blue]Opening conversation {i+1}/{len(unread_conversations)}...[/bold blue]")
                    
                    # Make sure the element is visible in the viewport before clicking
                    await unread.scroll_into_view_if_needed()
                    await self.human_delay(0.5, 1)  # Wait after scrolling
                    
                    # Try to click the conversation element
                    try:
                        await unread.click(timeout=5000)
                        console.print("[bold green]Successfully clicked on conversation[/bold green]")
                    except Exception:
                        # If direct click fails, try JavaScript click
                        console.print("[bold yellow]Direct click failed, trying JavaScript click...[/bold yellow]")
                        await self.page.evaluate("(element) => element.click()", unread)
                        console.print("[bold green]Successfully clicked on conversation using JavaScript[/bold green]")
                    
                    await self.human_delay(2, 3)  # Wait for conversation to fully load
                    
                    # Wait for conversation to fully load
                    try:
                        await self.page.wait_for_selector(".msg-s-message-list-container", timeout=10000)
                        console.print("[bold green]Conversation UI loaded successfully[/bold green]")
                    except Exception as e:
                        console.print(f"[bold yellow]Conversation UI load warning: {str(e)}[/bold yellow]")
                    
                    # Take a screenshot of the conversation for debugging
                    try:
                        await self.page.screenshot(path=f"conversation_{i+1}.png")
                        console.print(f"[bold blue]Saved screenshot of conversation {i+1}[/bold blue]")
                    except Exception:
                        pass
                    
                    # Get sender name quickly
                    sender_name = "Unknown Contact"
                    try:
                        # Try to get the name from the profile section at the top
                        profile_selectors = [
                            ".msg-entity-lockup__entity-title",  # Main profile title
                            ".profile-card-one-to-one__profile-title",  # Profile card title
                            ".msg-thread__profile-info h2",  # Thread profile header
                            ".msg-overlay-bubble-header__title",  # Overlay header
                            ".msg-conversation-card__participant-names",  # Participant names
                            ".msg-s-message-group__profile-link strong",  # Message group profile
                            ".msg-s-message-group__name",  # Message group name
                            ".msg-thread__link-to-profile",  # Link to profile
                            ".artdeco-entity-lockup__title"  # Entity lockup title
                        ]
                        
                        # Try each selector
                        for selector in profile_selectors:
                            try:
                                profile_elements = await self.page.locator(selector).all()
                                for element in profile_elements:
                                    name_text = await element.inner_text()
                                    if name_text and len(name_text.strip()) > 0:
                                        clean_name = name_text.strip()
                                        # Remove common LinkedIn suffixes
                                        clean_name = re.sub(r'\s+\(LinkedIn Member\)$', '', clean_name)
                                        clean_name = re.sub(r'\s+\(2nd\)$', '', clean_name)
                                        clean_name = re.sub(r'\s+\(3rd\)$', '', clean_name)
                                        clean_name = re.sub(r'\s+\(1st\)$', '', clean_name)
                                        
                                        if clean_name and len(clean_name) < 50:
                                            sender_name = clean_name
                                            console.print(f"[bold green]Found sender name from profile: {sender_name}[/bold green]")
                                            break
                                if sender_name != "Unknown Contact":
                                    break
                            except Exception:
                                continue
                    except Exception as e:
                        console.print(f"[bold yellow]Error getting sender name from profile: {str(e)}[/bold yellow]")
                    
                    # NOW PROCESS THIS CONVERSATION IMMEDIATELY (like test script)
                    console.print("[bold blue]Staying in conversation to process message...[/bold blue]")
                    
                    # Get message content quickly
                    message_content = ""
                    try:
                        # Get all message content with multiple selectors
                        message_selectors = [
                            ".msg-s-event-listitem__body",
                            ".msg-s-event__content",
                            ".msg-thread__message-text",
                            ".msg-s-message-group__content"
                        ]
                        
                        message_texts = []
                        for selector in message_selectors:
                            try:
                                message_elements = await self.page.locator(selector).all()
                                for msg_elem in message_elements:
                                    msg_text = await msg_elem.inner_text()
                                    if msg_text:
                                        message_texts.append(msg_text)
                                if message_texts:
                                    break
                            except Exception:
                                continue
                        
                        # Combine all message texts
                        message_content = "\n".join(message_texts)
                        
                    except Exception as e:
                        console.print(f"[bold yellow]Error getting message content: {str(e)}[/bold yellow]")
                        message_content = "Could not retrieve message content"
                    
                    # NOW PROCESS THIS MESSAGE IMMEDIATELY (like test script)
                    if message_content:
                        # Display the message
                        console.print(Panel(f"[bold]From: {sender_name}[/bold]\n\n{message_content}", 
                                           title=f"Unread Message {i+1}/{len(unread_conversations)}", 
                                           border_style="blue"))
                        
                        # Check if the message is a job offer
                        is_job_offer, message_type = self.ai_response_generator.classify_message(message_content)
                        
                        if is_job_offer:
                            console.print(f"[bold green]This appears to be a {message_type} message[/bold green]")
                            
                            # Generate AI response
                            is_job_offer, response = self.ai_response_generator.generate_response(message_content, sender_name)
                            
                            console.print(Panel(response, title="Suggested Response", border_style="green"))
                            
                            # Handle user approval
                            action = self.get_non_interactive_approval()
                            
                            if action == "send":
                                # Send the response directly in this conversation (we're already here!)
                                console.print("[bold blue]Sending response in current conversation...[/bold blue]")
                                success = await self.send_response_in_current_conversation(response)
                                
                                if success:
                                    console.print("[bold green]Response sent successfully![/bold green]")
                                else:
                                    console.print("[bold red]Failed to send response![/bold red]")
                                    
                            elif action == "edit":
                                if not self.non_interactive:
                                    try:
                                        from rich.prompt import Prompt
                                        edited_response = Prompt.ask("[bold blue]Edit the response[/bold blue]", default=response)
                                        
                                        # Send the edited response in this conversation
                                        console.print("[bold blue]Sending edited response in current conversation...[/bold blue]")
                                        success = await self.send_response_in_current_conversation(edited_response)
                                        
                                        if success:
                                            console.print("[bold green]Edited response sent successfully![/bold green]")
                                        else:
                                            console.print("[bold red]Failed to send edited response![/bold red]")
                                            
                                    except (EOFError, KeyboardInterrupt):
                                        console.print("[bold yellow]Edit interrupted, skipping message[/bold yellow]")
                                else:
                                    console.print("[bold yellow]Cannot edit in non-interactive mode, sending original response[/bold yellow]")
                                    success = await self.send_response_in_current_conversation(response)
                                    
                            else:
                                console.print("[bold yellow]Skipping this message[/bold yellow]")
                        else:
                            console.print(f"[bold yellow]Message classified as: {message_type} - skipping[/bold yellow]")
                    
                    # Return to conversation list for next conversation
                    await self.return_to_conversation_list()
                    
                except Exception as e:
                    console.print(f"[bold red]Error processing conversation {i+1}: {str(e)}[/bold red]")
                    # Try to return to conversation list on error
                    try:
                        await self.return_to_conversation_list()
                    except Exception:
                        pass
                    continue
            
            console.print("[bold green]All unread conversations processed![/bold green]")
            return  # Don't return a list, just process everything
        
        except Exception as e:
            console.print(f"[bold red]Error in check_messages: {str(e)}[/bold red]")
            return
    
    async def process_messages(self, unread_messages):
        """Process unread messages and generate responses."""
        if not unread_messages:
            console.print("[bold yellow]No messages to process[/bold yellow]")
            return
        
        console.print("[bold blue]Processing unread messages...[/bold blue]")
        
        from rich.panel import Panel
        
        # First navigate to messaging page
        await self.page.goto("https://www.linkedin.com/messaging/")
        await self.human_delay(2, 3)  # Wait for page to load
        
        # Process each conversation one at a time
        for message_data in unread_messages:
            sender = message_data["sender"]
            content = message_data["content"]
            conversation_index = message_data["conversation_index"]
            
            console.print(Panel(f"[bold]From: {sender}[/bold]\n\n{content}", 
                               title=f"Unread Message {conversation_index + 1}/{len(unread_messages)}", 
                               border_style="blue"))
            
            # Check if the message is a job offer
            is_job_offer, message_type = self.ai_response_generator.classify_message(content)
            
            if is_job_offer:
                console.print(f"[bold green]This appears to be a {message_type} message[/bold green]")
                
                # Generate AI response
                is_job_offer, response = self.ai_response_generator.generate_response(content, sender)
                
                console.print(Panel(response, title="Suggested Response", border_style="green"))
                
                # Handle user approval based on interactive/non-interactive mode
                action = self.get_non_interactive_approval()
                
                if action == "send":
                    # We need to open the conversation first since we're not in it yet
                    console.print("[bold blue]Opening conversation to send response...[/bold blue]")
                    
                    # Open the specific conversation
                    open_success = await self.open_conversation(conversation_index)
                    if not open_success:
                        console.print("[bold red]Failed to open conversation for sending![/bold red]")
                        return
                    
                    # Now send the response in the opened conversation
                    success = await self.send_response_in_current_conversation(response)
                    
                    if success:
                        console.print("[bold green]Response sent successfully![/bold green]")
                    else:
                        console.print("[bold red]Failed to send response![/bold red]")
                    
                    # Return to conversation list after sending
                    await self.return_to_conversation_list()
                    
                elif action == "edit":
                    if self.non_interactive:
                        console.print("[bold yellow]Cannot edit in non-interactive mode, sending original response[/bold yellow]")
                        
                        # Open the conversation first
                        console.print("[bold blue]Opening conversation to send response...[/bold blue]")
                        open_success = await self.open_conversation(conversation_index)
                        if not open_success:
                            console.print("[bold red]Failed to open conversation for sending![/bold red]")
                            return
                        
                        # Send the response in the opened conversation
                        success = await self.send_response_in_current_conversation(response)
                        
                        if success:
                            console.print("[bold green]Response sent successfully![/bold green]")
                        else:
                            console.print("[bold red]Failed to send response![/bold red]")
                            
                        # Return to conversation list
                        await self.return_to_conversation_list()
                    else:
                        try:
                            edited_response = Prompt.ask("[bold blue]Edit the response[/bold blue]", default=response)
                            
                            # Open the conversation first
                            console.print("[bold blue]Opening conversation to send edited response...[/bold blue]")
                            open_success = await self.open_conversation(conversation_index)
                            if not open_success:
                                console.print("[bold red]Failed to open conversation for sending![/bold red]")
                                return
                            
                            # Send the edited response in the opened conversation
                            success = await self.send_response_in_current_conversation(edited_response)
                            
                            if success:
                                console.print("[bold green]Edited response sent successfully![/bold green]")
                            else:
                                console.print("[bold red]Failed to send edited response![/bold red]")
                            
                            # Return to conversation list
                            await self.return_to_conversation_list()
                            
                        except (EOFError, KeyboardInterrupt):
                            console.print("[bold yellow]Edit interrupted, skipping message[/bold yellow]")
                else:
                    console.print("[bold yellow]Skipping this message[/bold yellow]")
                    # No need to open the conversation if we're skipping
            else:
                console.print(f"[bold yellow]This does not appear to be a job offer - detected as '{message_type}' - skipping[/bold yellow]")
                # No need to open the conversation if it's not a job offer
    
    async def open_conversation(self, conversation_index):
        """Open a specific conversation by its index - STAY IN CURRENT CONTEXT."""
        console.print(f"[bold blue]Opening conversation {conversation_index + 1}...[/bold blue]")
        
        try:
            # DO NOT navigate away - we should already be on the messaging page
            # Just find and click the conversation directly
            
            # Find all conversation elements (should already be loaded)
            conversation_selectors = [
                ".msg-conversation-listitem",
                ".msg-conversation-card",
                ".msg-thread-list-item"
            ]
            
            all_conversations = []
            for selector in conversation_selectors:
                try:
                    items = await self.page.locator(selector).all()
                    if items and len(items) > 0:
                        all_conversations = items
                        console.print(f"[bold green]Found {len(items)} conversations with selector: {selector}[/bold green]")
                        break
                except Exception as e:
                    console.print(f"[bold yellow]Error with selector {selector}: {str(e)}[/bold yellow]")
                    continue
            
            if not all_conversations or conversation_index >= len(all_conversations):
                console.print("[bold red]Could not find the specified conversation[/bold red]")
                return False
            
            # Click on the conversation to open it
            conversation = all_conversations[conversation_index]
            await conversation.scroll_into_view_if_needed()
            await self.human_delay(0.5, 1)  # Wait after scrolling
            
            try:
                await conversation.click(timeout=5000)
                console.print("[bold green]Successfully clicked on conversation[/bold green]")
            except Exception:
                # If direct click fails, try JavaScript click
                console.print("[bold yellow]Direct click failed, trying JavaScript click...[/bold yellow]")
                await self.page.evaluate("(element) => element.click()", conversation)
                console.print("[bold green]Successfully clicked on conversation using JavaScript[/bold green]")
            
            # Wait for conversation to load
            await self.human_delay(2, 3)  # Give more time for conversation to fully load
            
            # Wait for the conversation UI to appear
            try:
                await self.page.wait_for_selector(".msg-s-message-list-container", timeout=10000)
                console.print("[bold green]Conversation UI loaded successfully[/bold green]")
            except Exception as e:
                console.print(f"[bold yellow]Conversation UI load warning: {str(e)}[/bold yellow]")
                # Continue anyway, might still work
            
            # Take screenshot for debugging
            try:
                await self.page.screenshot(path="conversation_opened.png")
                console.print("[bold green]Conversation opened successfully - staying in conversation[/bold green]")
            except Exception:
                pass
            
            return True
        except Exception as e:
            console.print(f"[bold red]Error opening conversation: {str(e)}[/bold red]")
            return False
    
    async def return_to_conversation_list(self):
        """Return to the conversation list after processing a conversation."""
        console.print("[bold blue]Returning to conversation list...[/bold blue]")
        
        try:
            # Find back button with multiple selectors
            back_button_selectors = [
                ".msg-overlay-bubble-header__back-button",
                ".msg-thread-actions__back-button",
                "button[data-control-name='overlay.close_conversation_window']"
            ]
            
            back_clicked = False
            for selector in back_button_selectors:
                try:
                    back_button = await self.page.locator(selector).first()
                    if back_button:
                        await back_button.click()
                        await self.human_delay(1, 2)  # Wait like a human would
                        back_clicked = True
                        break
                except Exception:
                    continue
            
            if not back_clicked:
                console.print("[bold yellow]Could not find back button, navigating to messages directly...[/bold yellow]")
                await self.page.goto("https://www.linkedin.com/messaging/")
                await self.human_delay(2, 3)  # Wait for page to load
            
            # Wait for conversation list to load
            await self.page.wait_for_selector(".msg-conversations-container, .msg-conversation-listitem", timeout=10000)
            
            return True
        except Exception as e:
            console.print(f"[bold red]Error returning to conversation list: {str(e)}[/bold red]")
            # Try direct navigation as fallback
            try:
                await self.page.goto("https://www.linkedin.com/messaging/")
                await self.human_delay(2, 3)
                return True
            except Exception:
                return False
    
    async def send_response_in_current_conversation(self, response):
        """Send a response in the currently open conversation."""
        console.print("[bold blue]Sending response in current conversation...[/bold blue]")
        
        try:
            # Take screenshot before sending for debugging
            try:
                await self.page.screenshot(path="before_sending.png")
                console.print("[bold yellow]Saved screenshot before sending[/bold yellow]")
            except Exception:
                pass
                
            # Wait for the conversation container to be visible
            await self.page.wait_for_selector(".msg-s-message-list-container", timeout=10000)
            
            # Find the message input field with multiple selectors (including exact user-provided selector)
            input_selectors = [
                # Exact selector provided by user
                "div.msg-form__contenteditable.t-14.t-black--light.t-normal.flex-grow-1.full-height.notranslate[contenteditable='true'][role='textbox']",
                # Generic class-based selector
                ".msg-form__contenteditable[contenteditable='true']",
                "div.msg-form__contenteditable[contenteditable='true']",
                # Generic role-based selector
                "div[role='textbox'][contenteditable='true']",
                # Aria-label based (for German interface)
                "div[aria-label*='Nachricht'][contenteditable='true']",
                "div[aria-label*='Message'][contenteditable='true']",
                # Parent-child selectors
                ".msg-form__message-texteditor div[contenteditable='true']",
                "form div[contenteditable='true']",
                # Fallback selectors
                "div.msg-form__contenteditable",
                "div[contenteditable='true']"
            ]
            
            # Try each input selector with simple approach
            input_found = False
            for selector in input_selectors:
                try:
                    # Check if selector exists
                    count = await self.page.locator(selector).count()
                    if count > 0:
                        console.print(f"[bold green]Found {count} elements with selector: {selector}[/bold green]")
                        
                        # Try to click and type using page methods directly
                        try:
                            await self.page.click(selector)
                            await self.human_delay(0.5, 1)
                            await self.page.fill(selector, '')  # Clear any existing text
                            await self.human_delay(0.3, 0.7)
                            await self.page.type(selector, response, delay=random.uniform(50, 150))
                            console.print(f"[bold green]Successfully typed message using selector: {selector}[/bold green]")
                            input_found = True
                            break
                        except Exception as e:
                            console.print(f"[bold yellow]Error with selector {selector}: {str(e)}[/bold yellow]")
                            continue
                except Exception as e:
                    console.print(f"[bold yellow]Error with input selector {selector}: {str(e)}[/bold yellow]")
                    continue
            
            if not input_found:
                console.print("[bold red]Could not find message input field[/bold red]")
                # Take screenshot for debugging
                try:
                    await self.page.screenshot(path="no_input_field_found.png")
                    console.print("[bold yellow]Saved screenshot when no input field found[/bold yellow]")
                    
                    # Try to get HTML for debugging
                    html = await self.page.content()
                    with open("conversation_html.txt", "w", encoding="utf-8") as f:
                        f.write(html)
                    console.print("[bold yellow]Saved HTML content for debugging[/bold yellow]")
                    
                    # Try JavaScript fallback for input field detection and typing (same as working test script)
                    console.print("[bold blue]Trying JavaScript fallback for message input...[/bold blue]")
                    try:
                        js_result = await self.page.evaluate("""
                            (message) => {
                                // Try various selectors including the exact one provided by user
                                const possibleInputs = [
                                    // Exact selector from user
                                    document.querySelector('div.msg-form__contenteditable.t-14.t-black--light.t-normal.flex-grow-1.full-height.notranslate[contenteditable="true"][role="textbox"]'),
                                    // Generic selectors as fallback
                                    document.querySelector('div[role="textbox"][contenteditable="true"]'),
                                    document.querySelector('.msg-form__contenteditable[contenteditable="true"]'),
                                    document.querySelector('div[contenteditable="true"]'),
                                    document.querySelector('div[aria-label*="Nachricht"][contenteditable="true"]'),
                                    document.querySelector('div[aria-label*="Message"][contenteditable="true"]'),
                                    document.querySelector('form div[contenteditable="true"]')
                                ];
                                
                                // Find first non-null element
                                const input = possibleInputs.find(el => el !== null);
                                if (input) {
                                    input.textContent = message;
                                    // Also try to focus the element
                                    input.focus();
                                    return 'Found and set input with JavaScript';
                                }
                                return 'No input found with JavaScript';
                            }
                        """, response)
                        
                        if "Found and set input" in js_result:
                            console.print("[bold green]Successfully set message using JavaScript fallback[/bold green]")
                            input_found = True  # Set input_found to True so we continue to send button
                        else:
                            console.print(f"[bold red]JavaScript fallback failed: {js_result}[/bold red]")
                    except Exception as js_error:
                        console.print(f"[bold red]JavaScript fallback error: {str(js_error)}[/bold red]")
                        
                except Exception as debug_error:
                    console.print(f"[bold red]Debug screenshot/HTML save failed: {str(debug_error)}[/bold red]")
                
                # If we still haven't found input, return False
                if not input_found:
                    return False
            
            # Look for send button with multiple selectors
            send_button_selectors = [
                "button.msg-form__send-button",  # Primary send button
                "button[type='submit']",  # Generic submit button
                "button:has(span:text-is('Send'))",  # Button with Send text
                "button:has(span:text-is('Senden'))",  # German Send button
                "footer button",  # Footer button
                "form button[type='submit']",  # Form submit button
                "button.artdeco-button--primary"  # Primary button
            ]
            
            # Try to click send button with simple approach
            send_clicked = False
            for selector in send_button_selectors:
                try:
                    # Check if button exists and click directly
                    count = await self.page.locator(selector).count()
                    if count > 0:
                        await self.page.click(selector)
                        await self.human_delay(1, 2)  # Wait like a human would
                        send_clicked = True
                        console.print(f"[bold green]Clicked send button with selector: {selector}[/bold green]")
                        break
                except Exception as e:
                    console.print(f"[bold yellow]Error with send button selector {selector}: {str(e)}[/bold yellow]")
                    continue
            
            if not send_clicked:
                console.print("[bold yellow]Could not click send button, trying to press Enter key...[/bold yellow]")
                try:
                    # Try pressing Enter as an alternative
                    await self.page.keyboard.press('Enter')
                    await self.human_delay(1, 2)  # Wait like a human would
                    send_clicked = True
                    console.print("[bold green]Pressed Enter key to send message[/bold green]")
                except Exception as e:
                    console.print(f"[bold red]Error pressing Enter key: {str(e)}[/bold red]")
            
            # Take screenshot after sending
            try:
                await self.page.screenshot(path="after_sending.png")
                console.print("[bold yellow]Saved screenshot after sending[/bold yellow]")
            except Exception:
                pass
            
            return send_clicked or input_found  # Return True if we either typed the message or clicked send
            
        except Exception as e:
            console.print(f"[bold red]Error sending response: {str(e)}[/bold red]")
            # Take screenshot for debugging
            try:
                await self.page.screenshot(path="send_error.png")
                console.print("[bold yellow]Screenshot of error saved as send_error.png[/bold yellow]")
            except Exception:
                pass
            return False
    
    async def send_response(self, conversation_index, response):
        """Legacy method - kept for compatibility.
        Use open_conversation() and send_response_in_current_conversation() instead."""
        console.print("[bold yellow]Warning: Using legacy send_response method[/bold yellow]")
        
        try:
            # Take screenshot before navigation for debugging
            try:
                await self.page.screenshot(path="before_send_navigation.png")
                console.print("[bold yellow]Saved screenshot before navigation[/bold yellow]")
            except Exception:
                pass
                
            # Navigate to messaging page with human-like behavior
            await self.page.goto("https://www.linkedin.com/messaging/")
            await self.human_delay(2, 4)  # Wait like a human would
            
            # Take screenshot after navigation for debugging
            try:
                await self.page.screenshot(path="after_send_navigation.png")
                console.print("[bold yellow]Saved screenshot after navigation[/bold yellow]")
            except Exception:
                pass
            
            # Wait for the messaging interface to load with multiple possible selectors
            interface_selectors = [
                ".msg-conversations-container",
                ".msg-conversation-listitem",
                ".msg-overlay-list-bubble",
                ".msg-overlay-conversation-bubble"
            ]
            
            # Try each selector
            interface_loaded = False
            for selector in interface_selectors:
                try:
                    await self.page.wait_for_selector(selector, state="visible", timeout=10000)
                    console.print(f"[bold green]Found messaging interface with selector: {selector}[/bold green]")
                    interface_loaded = True
                    break
                except Exception:
                    continue
            
            if not interface_loaded:
                console.print("[bold red]Could not find messaging interface[/bold red]")
                return False
            
            # Get all conversation items with multiple possible selectors
            conversation_selectors = [
                ".msg-conversation-listitem",
                ".msg-conversation-card",
                ".msg-thread",
                "li.msg-conversation-listitem"
            ]
            
            conversation_items = []
            for selector in conversation_selectors:
                try:
                    items = await self.page.locator(selector).all()
                    if items and len(items) > 0:
                        conversation_items = items
                        console.print(f"[bold green]Found {len(items)} conversations with selector: {selector}[/bold green]")
                        break
                except Exception as e:
                    console.print(f"[bold yellow]Error finding conversations with selector {selector}: {str(e)}[/bold yellow]")
                    continue
            
            if not conversation_items:
                console.print("[bold red]Could not find any conversations[/bold red]")
                # Take screenshot for debugging
                try:
                    await self.page.screenshot(path="no_conversations_found.png")
                    console.print("[bold yellow]Saved screenshot when no conversations found[/bold yellow]")
                except Exception:
                    pass
                return False
            
            if conversation_index >= len(conversation_items):
                console.print(f"[bold red]Conversation index {conversation_index} out of range (max: {len(conversation_items)-1})[/bold red]")
                return False
            
            # Click on the conversation to open it
            console.print(f"[bold blue]Clicking on conversation {conversation_index+1}...[/bold blue]")
            await conversation_items[conversation_index].click()
            await self.human_delay(2, 3)  # Wait longer for conversation to load
            
            # Take screenshot after clicking conversation
            try:
                await self.page.screenshot(path="after_conversation_click.png")
                console.print("[bold yellow]Saved screenshot after clicking conversation[/bold yellow]")
            except Exception:
                pass
            
            # Wait for conversation to load
            conversation_loaded_selectors = [
                ".msg-form",
                ".msg-s-message-list-container",
                ".msg-s-message-list"
            ]
            
            conversation_loaded = False
            for selector in conversation_loaded_selectors:
                try:
                    await self.page.wait_for_selector(selector, state="visible", timeout=10000)
                    console.print(f"[bold green]Conversation loaded with selector: {selector}[/bold green]")
                    conversation_loaded = True
                    break
                except Exception:
                    continue
                    
            if not conversation_loaded:
                console.print("[bold red]Conversation did not load properly[/bold red]")
                return False
            
            # Type and send the response with multiple possible selectors
            message_input_selectors = [
                # Exact selector from user-provided element
                "div.msg-form__contenteditable[contenteditable='true'][role='textbox']",
                # More specific selectors based on the exact HTML structure
                "div.msg-form__contenteditable[role='textbox']",
                "div[contenteditable='true'][role='textbox']",
                # Fallback selectors
                ".msg-form__contenteditable",
                "div.msg-form__contenteditable",
                "div[role='textbox']",
                "[contenteditable='true']",
                "div[aria-label='Nachricht verfassen…']",
                "div[aria-label='Write a message…']",
                "div[aria-multiline='true']",
                ".msg-form__message-texteditor",
                ".msg-form__contenteditable p",
                ".msg-compose-form__message-text",
                ".msg-form__text-editor"
            ]
            
            # Try each message input selector
            input_found = False
            for selector in message_input_selectors:
                try:
                    # Check if selector exists
                    count = await self.page.locator(selector).count()
                    if count > 0:
                        console.print(f"[bold green]Found {count} elements with selector: {selector}[/bold green]")
                        
                        # Try to click and type - fix the syntax error with .first()
                        message_input = await self.page.locator(selector).first()
                        await message_input.click()
                        await self.human_delay(0.5, 1)
                        await message_input.fill('')  # Clear any existing text
                        await self.human_delay(0.3, 0.7)
                        
                        # Try different typing methods
                        try:
                            # First try to fill directly
                            await message_input.fill(response)
                        except Exception as e1:
                            console.print(f"[bold yellow]Fill method failed: {str(e1)}[/bold yellow]")
                            try:
                                # Then try typing with delays
                                await message_input.type(response, delay=random.uniform(50, 150))
                            except Exception as e2:
                                console.print(f"[bold yellow]Type method failed: {str(e2)}[/bold yellow]")
                                try:
                                    # Last resort: use page.type
                                    await self.page.type(selector, response, delay=random.uniform(50, 150))
                                except Exception as e3:
                                    console.print(f"[bold yellow]Page type method failed: {str(e3)}[/bold yellow]")
                                    # Try JavaScript as a last resort
                                    try:
                                        js_code = """(el) => { el.textContent = arguments[1]; }"""
                                        await self.page.evaluate(js_code, message_input, response)
                                        console.print("[bold blue]Used JavaScript to set text content[/bold blue]")
                                    except Exception as e4:
                                        console.print(f"[bold red]All typing methods failed: {str(e4)}[/bold red]")
                                        raise Exception("Could not input text with any method")
                            
                        input_found = True
                        console.print(f"[bold green]Successfully typed message using selector: {selector}[/bold green]")
                        break
                except Exception as e:
                    console.print(f"[bold yellow]Error with input selector {selector}: {str(e)}[/bold yellow]")
                    continue
            
            if not input_found:
                console.print("[bold red]Could not find message input field[/bold red]")
                # Take screenshot for debugging
                try:
                    await self.page.screenshot(path="no_input_field_found.png")
                    console.print("[bold yellow]Saved screenshot when no input field found[/bold yellow]")
                    
                    # Try to get HTML for debugging
                    html = await self.page.content()
                    with open("conversation_html.txt", "w", encoding="utf-8") as f:
                        f.write(html)
                    console.print("[bold yellow]Saved HTML content for debugging[/bold yellow]")
                    
                    # Last resort: try to find any input field using JavaScript
                    try:
                        console.print("[bold blue]Attempting to find message input with JavaScript...[/bold blue]")
                        js_result = await self.page.evaluate("""
                            () => {
                                // Try to find the element using various attributes
                                const possibleElements = [
                                    document.querySelector('div.msg-form__contenteditable[contenteditable="true"][role="textbox"]'),
                                    document.querySelector('div.msg-form__contenteditable'),
                                    document.querySelector('div[contenteditable="true"][role="textbox"]'),
                                    document.querySelector('div[role="textbox"]'),
                                    document.querySelector('[contenteditable="true"]'),
                                    document.querySelector('div[aria-label="Write a message…"]'),
                                    document.querySelector('div[aria-label="Nachricht verfassen…"]')
                                ];
                                
                                // Find the first non-null element
                                const element = possibleElements.find(el => el !== null);
                                
                                if (element) {
                                    // Try to focus and make it visible
                                    element.focus();
                                    element.click();
                                    // Set content
                                    element.textContent = 'Message from JavaScript injection';
                                    return true;
                                }
                                return false;
                            }
                        """)
                        
                        if js_result:
                            console.print("[bold green]Found and filled message input using JavaScript![/bold green]")
                            input_found = True
                    except Exception as js_error:
                        console.print(f"[bold yellow]JavaScript fallback failed: {str(js_error)}[/bold yellow]")
                except Exception:
                    pass
                    
                if not input_found:
                    return False
            
            # Find and click send button with multiple possible selectors
            send_button_selectors = [
                ".msg-form__send-button",
                "button[type='submit']",
                "[data-control-name='send']",
                "button.msg-form__send-button",
                "button[aria-label='Send']",
                "button[aria-label='Senden']"
            ]
            
            # Try each send button selector
            send_clicked = False
            for selector in send_button_selectors:
                try:
                    count = await self.page.locator(selector).count()
                    if count > 0:
                        console.print(f"[bold green]Found {count} send buttons with selector: {selector}[/bold green]")
                        
                        send_button = await self.page.locator(selector).first
                        await self.human_delay(0.5, 1)  # Pause before sending like a human would
                        await send_button.click()
                        await self.human_delay(1, 2)  # Wait for the message to be sent
                        send_clicked = True
                        console.print(f"[bold green]Successfully clicked send button using selector: {selector}[/bold green]")
                        break
                except Exception as e:
                    console.print(f"[bold yellow]Error with send button selector {selector}: {str(e)}[/bold yellow]")
                    continue
            
            if not send_clicked:
                console.print("[bold red]Could not find send button[/bold red]")
                # Take screenshot for debugging
                try:
                    await self.page.screenshot(path="no_send_button_found.png")
                    console.print("[bold yellow]Saved screenshot when no send button found[/bold yellow]")
                except Exception:
                    pass
                return False
            
            # Take screenshot after sending
            try:
                await self.page.screenshot(path="after_sending.png")
                console.print("[bold yellow]Saved screenshot after sending message[/bold yellow]")
            except Exception:
                pass
                
            return True
            
        except Exception as e:
            console.print(f"[bold red]Error sending response: {str(e)}[/bold red]")
            # Take screenshot for debugging
            try:
                await self.page.screenshot(path="send_error.png")
                console.print("[bold yellow]Screenshot of error saved as send_error.png[/bold yellow]")
            except Exception:
                pass
            return False
    
    async def run(self):
        """Main method to run the LinkedIn agent."""
        try:
            console.print("Setting up browser...")
            await self.setup_browser()
            
            console.print("Logging in to LinkedIn...")
            await self.login()
            
            try:
                console.print("Checking for unread messages...")
                unread_messages = await self.check_messages()
                
                if unread_messages:
                    console.print(f"[bold green]Found {len(unread_messages)} unread messages to process[/bold green]")
                    await self.process_messages(unread_messages)
                    
                    # After processing all messages, return to conversation list
                    console.print("[bold blue]All messages processed, returning to conversation list...[/bold blue]")
                    await self.return_to_conversation_list()
                else:
                    console.print("[bold yellow]No unread messages found to process[/bold yellow]")
            except Exception as e:
                console.print(f"[bold red]Error checking messages: {str(e)}[/bold red]")
                # Save screenshot for debugging
                try:
                    await self.page.screenshot(path="message_error.png")
                    console.print("[bold yellow]Screenshot of error saved as message_error.png[/bold yellow]")
                except Exception as screenshot_error:
                    console.print(f"[bold red]Failed to save error screenshot: {str(screenshot_error)}[/bold red]")
                    traceback.print_exc()
            
            # Add a final pause to ensure user has time to interact
            console.print("[bold green]LinkedIn agent workflow completed![/bold green]")
            console.print("[bold blue]Press Enter to exit the application...[/bold blue]")
            
            # Use a more reliable way to wait for user input
            import sys
            import time
            
            # Flush any pending input
            sys.stdout.flush()
            
            # Wait for user input with a timeout
            wait_time = 60  # Wait up to 60 seconds
            start_time = time.time()
            
            # Print a message every 10 seconds
            while time.time() - start_time < wait_time:
                if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                    _ = sys.stdin.readline()  # Read and discard input
                    break
                await asyncio.sleep(10)
                console.print("[bold blue]Still waiting for Enter key to exit...[/bold blue]")
            
        except Exception as e:
            console.print(f"[bold red]Error in LinkedIn agent: {str(e)}[/bold red]")
            traceback.print_exc()
            
            # Save screenshot for any error
            try:
                await self.page.screenshot(path="agent_error.png")
                console.print("[bold yellow]Screenshot of error saved as agent_error.png[/bold yellow]")
            except Exception:
                pass
            
            # Add error pause with more reliable waiting
            console.print("[bold red]An error occurred. Press Enter to exit or wait 30 seconds...[/bold red]")
            
            # Wait a fixed time instead of trying to capture input which might fail
            await asyncio.sleep(30)
            
        finally:
            console.print("Cleaning up resources...")
            await self.cleanup()
            console.print("Cleanup complete")
    
    async def cleanup(self):
        """Clean up resources."""
        console.print("[bold blue]Cleaning up resources...[/bold blue]")
        
        if self.browser:
            await self.browser.close()
        
        if self.playwright:
            await self.playwright.stop()
        
        console.print("[bold green]Cleanup complete[/bold green]")

    def get_non_interactive_approval(self):
        """Get approval in non-interactive mode using timeout or auto-approve."""
        if self.auto_approve:
            return "send"  # Auto-approve all responses
        
        # Use timeout-based approval with clear instructions
        console.print("[bold green]╭──────────────────────────────------─────────────────────╮[/bold green]")
        console.print("[bold green]│                                                         │[/bold green]")
        console.print("[bold green]│  WAITING FOR YOUR ACTION:                               │[/bold green]")
        console.print("[bold green]│                                                         │[/bold green]")
        console.print("[bold green]│  Type 'a' and press Enter to SEND                       │[/bold green]")
        console.print("[bold green]│  Type 'e' and press Enter to EDIT                       │[/bold green]")
        console.print("[bold green]│  Press Enter or any other key to SKIP                   │[/bold green]")
        console.print("[bold green]│                                                         │[/bold green]")
        console.print(f"[bold green]│  Waiting {self.response_timeout} seconds for input...  │[/bold green]")
        console.print("[bold green]╰────────────────────────────────────────────────------───╯[/bold green]")
        
        # Set up a timeout for input
        action = "skip"  # Default action
        
        # Simple input approach that works better in Docker
        def input_thread():
            nonlocal action
            try:
                # Use standard input with timeout
                import sys
                import select
                
                # Flush any pending input
                while select.select([sys.stdin], [], [], 0.0)[0]:
                    sys.stdin.readline()
                
                # Wait for new input
                console.print("[bold blue]Type your choice and press Enter...[/bold blue]")
                user_input = input().strip().lower()
                
                if user_input == 'a':
                    action = "send"
                    console.print("[bold green]✓ SEND action selected[/bold green]")
                elif user_input == 'e':
                    action = "edit"
                    console.print("[bold yellow]✎ EDIT action selected[/bold yellow]")
                else:
                    console.print("[bold red]✗ SKIP action selected[/bold red]")
            except Exception as e:
                console.print(f"[bold red]Error reading input: {str(e)}[/bold red]")
        
        try:
            # Start input thread with a longer timeout
            thread = threading.Thread(target=input_thread)
            thread.daemon = True
            thread.start()
            
            # Wait for timeout - use a longer timeout to ensure user has time to respond
            actual_timeout = max(self.response_timeout, 120)  # At least 2 minutes
            thread.join(actual_timeout)
            
            if action == "skip":
                console.print("[bold yellow]Timeout reached, defaulting to SKIP[/bold yellow]")
        except Exception as e:
            console.print(f"[bold red]Error in input handling: {str(e)}[/bold red]")
        
        return action

async def main():
    """Main function to run the LinkedIn agent."""
    agent = LinkedInAgentPlaywright()
    await agent.run()

if __name__ == "__main__":
    asyncio.run(main())
