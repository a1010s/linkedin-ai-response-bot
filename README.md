# LinkedIn Job Offer Auto-Responder

An AI-powered tool that helps you respond to LinkedIn job offers and recruiter messages. This tool monitors your LinkedIn messages, identifies job offers, and suggests AI-generated responses for your approval before sending.

## Features

- **Automated Message Checking**: Monitors your LinkedIn inbox for new messages
- **Job Offer Detection**: Identifies messages that are likely job offers or recruiter outreach
- **AI-Generated Responses**: Creates professional, brief responses using AI (OpenAI) or templates
- **User Approval**: Always requires your approval before sending any message
- **Scheduled Mode**: Can run on a schedule to periodically check for new messages
- **Customizable Templates**: Includes pre-defined response templates that can be customized

## Requirements

- Python 3.6+
- Chrome browser
- LinkedIn account
- OpenAI API key (optional, for AI-generated responses)

## Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd linkedin-agent
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your credentials (copy from `.env.example`):
   ```
   cp .env.example .env
   ```

4. Edit the `.env` file with your LinkedIn credentials and OpenAI API key (optional):
   ```
   # LinkedIn credentials
   LINKEDIN_EMAIL=your_email@example.com
   LINKEDIN_PASSWORD=your_password

   # OpenAI API key (optional, for AI-generated responses)
   OPENAI_API_KEY=your_openai_api_key
   
   # Scheduled mode settings (optional)
   CHECK_INTERVAL_MINUTES=60
   ACTIVE_HOURS_START=9
   ACTIVE_HOURS_END=18
   ```

## Usage

### One-time Check

To check for new messages once:

```
python linkedin_agent.py
```

### Scheduled Mode

To run the agent on a schedule (checks periodically):

```
python scheduled_agent.py
```

## How It Works

1. The tool logs into your LinkedIn account using Selenium
2. It navigates to your messages and checks for unread conversations
3. For each unread conversation, it analyzes the message content
4. If a message appears to be a job offer, it generates a suggested response
5. You review the suggested response and can:
   - Send it as is
   - Edit it before sending
   - Skip responding entirely
6. The tool handles sending the approved message

## Customizing Responses

You can customize the response templates by editing the `response_templates.json` file. The file contains templates for different message types:

- `job_offer`: Responses to direct job offers
- `recruiter_intro`: Responses to initial recruiter outreach
- `follow_up`: Responses to follow-up messages
- `not_interested`: Polite rejection responses
- `other`: Generic responses for other message types

## Security Considerations

- Your LinkedIn credentials are stored locally in the `.env` file
- The tool does not share your credentials with any external services
- Always review messages before sending to ensure appropriate responses
- LinkedIn may detect automation if used too frequently or aggressively

## Limitations

- LinkedIn's UI may change, which could break the automation
- Message classification is not perfect and may misclassify some messages
- LinkedIn may have measures to detect and prevent automation
- The tool requires a browser window to be open while running

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational purposes only. Use of automation tools may violate LinkedIn's terms of service. Use at your own risk.
