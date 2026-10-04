# 🩺 Vision Health Assistant — "What Am I Looking At?"

A Streamlit chat app where a user enters their name and WhatsApp number once, then chats with an AI health buddy by typing a question or attaching a photo. It explains what is visible and recommends professional care when appropriate. One button sends a summary of the conversation to WhatsApp.

Built with **Gemini** (chat + vision), **Streamlit** (UI) and **Twilio** (WhatsApp).

> ⚠️ **Educational use only.** This assistant does not diagnose diseases or prescribe medicines. In an emergency, call 112 / 108 or go to the nearest hospital.

## Live demo

- App: `ADD-YOUR-STREAMLIT-URL-HERE`
- Demo video: `ADD-LINK-HERE`

## What it does

| Input | What the assistant does |
|---|---|
| 🍽️ Food photo | Identifies the meal, estimates calories and macros, and comments on diet suitability (e.g. high-protein) |
| 💊 Medicine photo or label | Reads the visible label text, explains general use, directions and warnings, and advises confirming the dose with a doctor or pharmacist |
| 🩹 First-aid photo | Describes what is visibly observable, gives safe general first-aid guidance and warning signs |
| 💬 Text question | Answers healthcare, medicine, nutrition and fitness questions in plain language |
| 🚫 Off-topic question | Politely declines and steers back to health topics |

## Safety design

- Scoped by the system prompt to healthcare, medicine, first aid, nutrition and fitness only.
- Does not diagnose and does not give personal dosage instructions.
- Reads only label text that is actually visible and asks for a clearer photo if unreadable.
- Tells users to contact emergency services when an image or description suggests an emergency.
- Recommends a doctor or pharmacist for anything uncertain, persistent or serious.

## Project structure

```
vision-health-assistant/
├── app.py                        # the app itself
├── prompts.py                    # the AI's personality, kept separate
├── requirements.txt              # dependencies
├── .gitignore                    # keeps secrets.toml out of GitHub
└── .streamlit/
    └── secrets.toml.example      # template - copy to secrets.toml and fill in
```

## Setup

**Requirements:** Python 3.9+, a free [Google AI Studio](https://aistudio.google.com) API key, and a [Twilio](https://www.twilio.com/try-twilio) account with the WhatsApp sandbox.

1. Create and activate a virtual environment:
   ```
   python -m venv venv
   # Windows PowerShell
   .\venv\Scripts\Activate.ps1
   # macOS / Linux
   source venv/bin/activate
   ```
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and fill in your keys:
   ```
   GEMINI_API_KEY = "..."
   TWILIO_ACCOUNT_SID = "..."
   TWILIO_AUTH_TOKEN = "..."
   TWILIO_WHATSAPP_FROM = "whatsapp:+14155238886"
   TWILIO_CONTENT_SID = ""
   ```
4. From your phone, send the sandbox join message (`join your-code`) to the Twilio sandbox WhatsApp number.
5. Run the app:
   ```
   streamlit run app.py
   ```

## WhatsApp sending

- **Template mode:** if `TWILIO_CONTENT_SID` holds a Content Template SID (starts with `HX`), the summary is sent through Twilio's Content API. Template creation requires a paid Twilio account.
- **Free-text mode:** if it is empty, the app attempts a plain-text message inside the sandbox's 24-hour window.
- **Fallback:** if Twilio cannot send the message, the app shows the summary on screen with a download button and an **Open in WhatsApp** link that opens a chat with the summary pre-filled.

## Deploying on Streamlit Community Cloud

1. Push this repo to GitHub (never commit `secrets.toml`).
2. Go to [share.streamlit.io](https://share.streamlit.io), click **Create app**, and pick the repo, branch `main` and `app.py`.
3. In **Advanced settings → Secrets**, paste the contents of your local `secrets.toml`.
4. Click **Deploy**.

## Tech stack

Python · Streamlit · Google Gemini (`google-genai`) · Twilio WhatsApp API

## Disclaimer

Vision Health Assistant provides general educational information only. It is not a substitute for professional medical advice, diagnosis or treatment. Always consult a qualified healthcare provider about medical concerns.