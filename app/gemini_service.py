import os
import logging
import langdetect
from dotenv import load_dotenv
import google.generativeai as genai
from .models import Message, User
from .extensions import db

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-1.5-flash")

def load_history(user_id):
    messages = Message.query.filter_by(user_id=user_id).order_by(Message.timestamp).all()
    history = []
    for m in messages:
        if m.role == "user":
            history.append({"user": m.content})
        elif m.role == "assistant":
            history.append({"bot": m.content})
    return history

def save_message(user_id, user_msg, bot_msg):
    db.session.add(Message(user_id=user_id, role="user", content=user_msg))
    db.session.add(Message(user_id=user_id, role="assistant", content=bot_msg))
    db.session.commit()

def detect_language(text):
    try:
        return langdetect.detect(text)
    except:
        return "ru"

def detect_intent_with_gemini(messages: list[dict]) -> str:
    user_messages = [m["user"] for m in messages if "user" in m][-3:]
    if not user_messages:
        return "none"
    prompt = (
        "Ты помощник CRM. Проанализируй следующие сообщения клиента и верни одно из следующих намерений: "
        "'website request', 'chatbot request', 'design request', 'support request', или 'none'.\n"
        f"Сообщения клиента: {' | '.join(user_messages)}"
    )
    response = model.generate_content(prompt)
    intent = response.text.strip().lower() if response.text else "none"
    return intent if "request" in intent else "none"

def generate_response(message_body, wa_id, name):
    user = User.query.filter_by(phone=wa_id).first()
    if not user:
        user = User(name=name, phone=wa_id, language="en")
        db.session.add(user)
        db.session.commit()

    history = load_history(user.id)

    user_lang = detect_language(message_body)
    if user_lang == "ru":
        lang_note = "Отвечай на русском языке."
    elif user_lang == "kk":
        lang_note = "Жауапты қазақ тілінде бер."
    else:
        lang_note = "Reply in English."

    system_prompt = (
        ""
    )

    chat_history = system_prompt + "\n"
    for turn in history:
        if "user" in turn:
            chat_history += f"User: {turn['user']}\n"
        if "bot" in turn:
            chat_history += f"Bot: {turn['bot']}\n"

    chat_history += f"User: {message_body}\nBot:"
    response = model.generate_content(chat_history)
    reply = response.text.strip() if response.text else ""
    if not reply or any(x in reply.lower() for x in ["я не могу помочь", "не могу помочь", "это вне моей компетенции"]):
        reply = "Извините, я могу помочь только по вопросам веб-сайтов, чат-ботов, дизайна или поддержки."

    logging.info(f"[Gemini] {name} ({wa_id}) → {reply}")
    save_message(user.id, message_body, reply)
    return reply

