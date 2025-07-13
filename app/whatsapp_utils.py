import logging
from flask import current_app, jsonify
import json
import requests

from app import db
from app.gemini_service import generate_response, detect_intent_with_gemini, load_history
from app.models import Lead, User, Message
from datetime import datetime

import re


def log_http_response(response):
    logging.info(f"Status: {response.status_code}")
    logging.info(f"Content-type: {response.headers.get('content-type')}")
    logging.info(f"Body: {response.text}")


def get_text_message_input(recipient, text):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
    )

def send_message(payload):
    headers = {
        "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}",
        "Content-Type": "application/json",
    }
    url = f"https://graph.facebook.com/v18.0/{current_app.config['PHONE_NUMBER_ID']}/messages"
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Request failed due to: {e}")
    else:
        log_http_response(response)

def process_text_for_whatsapp(text):
    # Remove brackets
    pattern = r"\【.*?\】"
    # Substitute the pattern with an empty string
    text = re.sub(pattern, "", text).strip()

    # Pattern to find double asterisks including the word(s) in between
    pattern = r"\*\*(.*?)\*\*"

    # Replacement pattern with single asterisks
    replacement = r"*\1*"

    # Substitute occurrences of the pattern with the replacement
    whatsapp_style_text = re.sub(pattern, replacement, text)

    return whatsapp_style_text


def process_whatsapp_message(body):
    wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
    name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]
    message = body["entry"][0]["changes"][0]["value"]["messages"][0]
    message_body = message["text"]["body"]

    user = User.query.filter_by(phone=wa_id).first()
    if not user:
        user = User(name=name, phone=wa_id, language="auto", created_at=datetime.utcnow())
        db.session.add(user)
        db.session.commit()

    history = load_history(user.id)
    intent = detect_intent_with_gemini(history)
    reply = generate_response(message_body, wa_id, name)

    last_lead = Lead.query.filter_by(user_id=user.id).order_by(Lead.created_at.desc()).first()
    if intent and intent != "none" and (not last_lead or last_lead.intent != intent):
            db.session.add(Lead(user_id=user.id, intent=intent, created_at=datetime.utcnow()))
            db.session.commit()

    response = process_text_for_whatsapp(reply)

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": current_app.config["RECIPIENT_WAID"],
        "type": "text",
        "text": {
            "preview_url": False,
            "body": response
        }
    }
    logging.info(f"Sending message payload: {payload}")
    logging.info(f"Extracted wa_id: {wa_id}")
    send_message(payload)


def is_valid_whatsapp_message(body):
    """
    Check if the incoming webhook event has a valid WhatsApp message structure.
    """
    return (
        body.get("object")
        and body.get("entry")
        and body["entry"][0].get("changes")
        and body["entry"][0]["changes"][0].get("value")
        and body["entry"][0]["changes"][0]["value"].get("messages")
        and body["entry"][0]["changes"][0]["value"]["messages"][0]
    )