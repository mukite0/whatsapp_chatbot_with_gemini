# WhatsApp Business CRM Chatbot (Flask + Gemini)

This is a multilingual business chatbot that integrates with **WhatsApp Cloud API** and uses **Google Gemini 1.5 Flash** for intent detection and message generation. It detects leads, stores them in a PostgreSQL database, and only responds to business-related topics.

For this project to work, you have to register Meta Developer Account, if you don't have it already, and then create an app in **https://developers.facebook.com/apps/**.

Set up WhatsApp API and webhook in app settings.

---

## ✅ Features

- Multilingual chatbot (Kazakh, Russian, English)
- Google Gemini 1.5 Flash integration
- Intent detection (`chatbot request`, `website request`, etc.)
- WhatsApp Cloud API messaging
- Lead and message tracking via PostgreSQL
- Auto-ignore non-business queries via system prompt

---

## 🔧 Stack

- Python 3.11+
- Flask
- PostgreSQL
- SQLAlchemy
- Google Generative AI SDK (`google-generativeai`)
- WhatsApp Cloud API
- dotenv

---

## 🚀 Setup Instructions

### 1. Clone the repo

```bash
git clone https://github.com/mukite0/whatsapp_chatbot_with_gemini.git
cd whatsapp_chatbot_with_gemini
```

### 2. Install dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure

- Create and configure your .env file by following example.env
- Do not forget to implement your system prompt in **app/gemini_service.py**. 

### 4. Initialize the database

Ensure your PostgreSQL is connected, and then: 

```bash
flask db upgrade
```

### 5. Expose webhook and run the app

I used ngrok, but you can use your own domain.
Then you can just run the server on the same port as you are running the webhook. 

```bash
flask run
```

---

### 📥 Webhook Endpoint:

  - POST /webhook — receives WhatsApp messages and responds

  - Handles intent detection, generates response, saves lead/message

### 💡 Supported Intents:
  - website request
  - chatbot request
  - design request
  - support request
  - (ignores none)
