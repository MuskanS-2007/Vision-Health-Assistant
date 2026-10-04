import json
import time
from urllib.parse import quote

import streamlit as st
from google import genai
from google.genai import types
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client as TwilioClient

from prompts import SUMMARY_REQUEST_PROMPT, SYSTEM_PROMPT, WELCOME_MESSAGE_TEMPLATE

MODEL_NAME = "gemini-3.5-flash"
st.set_page_config(page_title="Vision Health Assistant", page_icon="🩺")

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
TWILIO_ACCOUNT_SID = st.secrets["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = st.secrets["TWILIO_AUTH_TOKEN"]
TWILIO_WHATSAPP_FROM = st.secrets["TWILIO_WHATSAPP_FROM"]
# Optional: leave blank (or remove) on a Twilio trial account to send plain text
# inside the sandbox's 24-hour window instead of using a Content Template.
TWILIO_CONTENT_SID = st.secrets.get("TWILIO_CONTENT_SID", "").strip()


@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=GEMINI_API_KEY)


@st.cache_resource
def get_twilio_client():
    return TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


gemini_client = get_gemini_client()
twilio_client = get_twilio_client()


def render_message(message):
    with st.chat_message(message["role"]):
        if message["kind"] == "text":
            st.write(message["content"])
        elif message["kind"] == "image":
            st.image(message["content"])


def add_message(role, kind, content):
    st.session_state.messages.append({"role": role, "kind": kind, "content": content})
    render_message(st.session_state.messages[-1])


def ask_gemini(parts, retries=3):
    for attempt in range(retries):
        try:
            return st.session_state.chat.send_message(parts).text
        except Exception as error:
            overloaded = "503" in str(error) or "UNAVAILABLE" in str(error)
            if overloaded and attempt < retries - 1:
                time.sleep(2 * (attempt + 1))  # wait 2s, then 4s, then give up
                continue
            return f"Sorry, something went wrong: {error}"


def clean_whatsapp_text(text):
    if not text:
        return "No health summary available."
    text = " ".join(text.split())  # collapse whitespace/newlines
    return text[:1500] + "..." if len(text) > 1500 else text


def send_whatsapp(to_number, user_name, summary):
    # Content template expects {{1}} = name, {{2}} = summary.
    try:
        if TWILIO_CONTENT_SID.startswith("HX"):
            # Template mode (works outside the 24-hour window, needs a paid account)
            content_variables = json.dumps(
                {"1": user_name, "2": clean_whatsapp_text(summary)}, ensure_ascii=False
            )
            message = twilio_client.messages.create(
                from_=TWILIO_WHATSAPP_FROM,
                to=f"whatsapp:{to_number}",
                content_sid=TWILIO_CONTENT_SID,
                content_variables=content_variables,
            )
        else:
            # Free-text mode (trial/sandbox): works if this phone messaged the
            # sandbox number within the last 24 hours.
            text = (summary or "No health summary available.").strip()
            text = text[:1400] + "..." if len(text) > 1400 else text
            message = twilio_client.messages.create(
                from_=TWILIO_WHATSAPP_FROM,
                to=f"whatsapp:{to_number}",
                body=f"Hi {user_name}, here's your Vision Health Assistant summary:\n\n{text}",
            )
        return True, message.sid
    except TwilioRestException as error:
        return False, f"Twilio error {error.code}: {error.msg}"
    except Exception as error:
        return False, str(error)


# Step 1: onboarding
if "onboarded" not in st.session_state:
    st.title("🩺 Vision Health Assistant")
    st.caption("What am I looking at? Snap it. Understand it. Text yourself the results.")
    with st.form("onboarding_form"):
        name = st.text_input("Your name")
        whatsapp_number = st.text_input(
            "WhatsApp number (with country code)",
            placeholder="+91XXXXXXXXXX",
            help="This is the number Vision Health Assistant will text your summary to.",
        )
        submitted = st.form_submit_button("Let's go 🚀")
    if submitted:
        if not name.strip() or not whatsapp_number.strip():
            st.warning("Please fill in both your name and WhatsApp number.")
        else:
            st.session_state.name = name.strip()
            st.session_state.whatsapp_number = whatsapp_number.strip()
            st.session_state.chat = gemini_client.chats.create(
                model=MODEL_NAME,
                config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
            )
            st.session_state.messages = []
            st.session_state.onboarded = True
            st.rerun()
    st.stop()

# Step 2: chat interface
header_col, button_col = st.columns([5, 2], vertical_alignment="center")

with header_col:
    st.title("🩺 Vision Health Assistant")

with button_col:
    send_disabled = len(st.session_state.messages) <= 2
    if st.button("📤 Send to WhatsApp", disabled=send_disabled, use_container_width=True):
        with st.spinner("Summarizing your conversation..."):
            summary = ask_gemini([SUMMARY_REQUEST_PROMPT])
        success, info = send_whatsapp(st.session_state.whatsapp_number, st.session_state.name, summary)
        st.session_state.last_summary = summary
        st.session_state.send_status = ("ok", info) if success else ("err", info)

st.caption(f"Logged in as {st.session_state.name} - updates go to {st.session_state.whatsapp_number}")
st.caption("⚠️ Educational information only - not a medical diagnosis. In an emergency, call 112 / 108.")

# Result of the last "Send to WhatsApp" click, plus a free fallback if Twilio fails
send_status = st.session_state.get("send_status")
last_summary = st.session_state.get("last_summary")

if send_status:
    if send_status[0] == "ok":
        st.success("Sent! Check your WhatsApp 📲")
    else:
        st.warning(
            f"Automatic WhatsApp sending didn't work ({send_status[1]}). "
            "You can still share your summary below."
        )

if last_summary:
    with st.expander("📄 Your summary", expanded=bool(send_status and send_status[0] == "err")):
        st.write(last_summary)
        st.download_button(
            "⬇️ Download summary",
            data=last_summary,
            file_name="health_summary.txt",
            mime="text/plain",
        )
        phone_digits = "".join(ch for ch in st.session_state.whatsapp_number if ch.isdigit())
        share_text = f"Hi {st.session_state.name}, here's your Vision Health Assistant summary:\n\n{last_summary}"
        wa_link = f"https://wa.me/{phone_digits}?text={quote(share_text[:1200])}"
        st.link_button("💬 Open in WhatsApp", wa_link)

if not st.session_state.messages:
    add_message("assistant", "text", WELCOME_MESSAGE_TEMPLATE.format(name=st.session_state.name))
else:
    for message in st.session_state.messages:
        render_message(message)

user_input = st.chat_input(
    "Ask a health question, or attach a photo (meal, medicine label, first-aid)",
    accept_file=True,
    file_type=["jpg", "jpeg", "png"],
)

if user_input:
    photo = user_input.files[0] if user_input.files else None
    text = user_input.text
    parts = []

    if photo is not None:
        photo_bytes = photo.getvalue()
        add_message("user", "image", photo_bytes)
        parts.append(types.Part.from_bytes(data=photo_bytes, mime_type=photo.type))
    if text:
        add_message("user", "text", text)
        parts.append(text)
    elif photo is not None:
        parts.append(
            "What am I looking at? If this is a meal, tell me what it is and "
            "estimate the calories and macros. If it is a medicine or label, "
            "read out what is visible and explain what it is generally used "
            "for. If it is a first-aid situation, describe what is visible and "
            "give safe general guidance and when to seek care."
        )

    with st.spinner("Analyzing..."):
        answer = ask_gemini(parts)
    add_message("assistant", "text", answer)
    st.rerun()  # refresh so the WhatsApp button unlocks right away