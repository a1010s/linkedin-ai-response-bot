#!/usr/bin/env python3
"""
LinkedIn Cookie Saver Script

This script helps you manually log in to LinkedIn and save your session cookies
for later use by the LinkedIn agent. This approach bypasses LinkedIn's security
measures since you'll be using a manually authenticated session.

Usage:
    python save_linkedin_cookies.py

The script will:
1. Open a browser window for you to manually log in to LinkedIn
2. Wait for you to complete the login process (including any security verifications)
3. Save the authenticated session cookies to a file
4. Close the browser
"""

import os
import json
import asyncio
import time
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from rich.console import Console

# Initialize rich console for prettier output
console = Console()

async def main():
    # Load environment variables
    load_dotenv()
    
    console.print("[bold green]LinkedIn Cookie Saver[/bold green]")
    console.print("This script will help you manually log in to LinkedIn and save your session cookies.")
    console.print("Follow the instructions in the browser window that will open.")
    
    # Start Playwright
    async with async_playwright() as playwright:
        # Launch the browser in non-headless mode so you can interact with it
        console.print("[bold blue]Launching browser...[/bold blue]")
        browser = await playwright.chromium.launch(headless=False)
        
        # Create a new browser context
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
        )
        
        # Create a new page
        page = await context.new_page()
        
        # Navigate to LinkedIn
        console.print("[bold blue]Navigating to LinkedIn...[/bold blue]")
        await page.goto("https://www.linkedin.com/")
        
        # Wait for user to manually log in
        console.print("[bold yellow]Please log in to LinkedIn in the browser window.[/bold yellow]")
        console.print("[bold yellow]Complete any security verifications if prompted.[/bold yellow]")
        console.print("[bold yellow]Once you are fully logged in and can see your LinkedIn feed,[/bold yellow]")
        console.print("[bold yellow]the script will automatically detect it and save your cookies.[/bold yellow]")
        
        # Wait for login to complete by checking for feed elements
        console.print("[bold blue]Waiting for successful login...[/bold blue]")
        try:
            # Wait for either the feed or the global navigation to appear
            await page.wait_for_selector(".feed-identity-module, .global-nav", timeout=300000)  # 5 minute timeout
            console.print("[bold green]Login detected![/bold green]")
            
            # Export cookies
            cookies = await context.cookies()
            cookies_file = "linkedin_cookies.json"
            
            with open(cookies_file, "w") as f:
                json.dump(cookies, f)
            
            console.print(f"[bold green]Cookies saved to {cookies_file}![/bold green]")
            console.print("[bold yellow]Keep this file secure as it contains your LinkedIn session data.[/bold yellow]")
            
            # Wait a moment before closing
            await asyncio.sleep(2)
        except Exception as e:
            console.print(f"[bold red]Error waiting for login: {str(e)}[/bold red]")
            console.print("[bold red]Login process timed out or failed.[/bold red]")
        
        # Close the browser
        await browser.close()
        console.print("[bold blue]Browser closed.[/bold blue]")
        console.print("[bold green]You can now copy the linkedin_cookies.json file to your Docker container.[/bold green]")

if __name__ == "__main__":
    asyncio.run(main())
