#!/usr/bin/env python3
"""
Scheduled LinkedIn Job Offer Auto-Responder using Playwright
This script runs the LinkedIn agent periodically according to a schedule.
"""

import os
import time
import asyncio
import schedule
from datetime import datetime
from dotenv import load_dotenv
from rich.console import Console
from linkedin_agent_playwright import LinkedInAgentPlaywright

# Initialize Rich console for better terminal output
console = Console()

# Load environment variables
load_dotenv()

# Default active hours (8 AM to 8 PM)
DEFAULT_START_HOUR = 8
DEFAULT_END_HOUR = 20
DEFAULT_CHECK_INTERVAL = 60  # minutes

# Get active hours from environment or use defaults
start_hour = int(os.getenv("ACTIVE_START_HOUR", DEFAULT_START_HOUR))
end_hour = int(os.getenv("ACTIVE_END_HOUR", DEFAULT_END_HOUR))
check_interval = int(os.getenv("CHECK_INTERVAL_MINUTES", DEFAULT_CHECK_INTERVAL))

def is_active_hour():
    """Check if current time is within active hours."""
    current_hour = datetime.now().hour
    return start_hour <= current_hour < end_hour

async def check_linkedin_messages():
    """Run the LinkedIn agent if within active hours."""
    if not is_active_hour():
        console.print("[bold yellow]Outside of active hours. Skipping check.[/bold yellow]")
        return
    
    console.print(f"[bold blue]Running scheduled check at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/bold blue]")
    
    agent = LinkedInAgentPlaywright()
    await agent.run()

async def main():
    """Main function to run the scheduled LinkedIn agent."""
    console.print(f"[bold green]Starting LinkedIn scheduled agent[/bold green]")
    console.print(f"[bold blue]Active hours: {start_hour}:00 to {end_hour}:00[/bold blue]")
    console.print(f"[bold blue]Check interval: {check_interval} minutes[/bold blue]")
    
    # Schedule the job
    schedule.every(check_interval).minutes.do(lambda: asyncio.create_task(check_linkedin_messages()))
    
    # Run once immediately
    await check_linkedin_messages()
    
    # Keep the script running
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
