import os
from flask import Flask, request, jsonify, render_template
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

GIGACHAT_CREDENTIALS = os.getenv("GIGACHAT_CREDENTIALS")

# Глобальная история сообщений (для каждого пользователя можно сделать отдельную сессию)
conversation_history = []

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask_gigachat():
    data = request.json
    user_message = data.get("message")
    bot_role = data.get("role", "Ты — учитель, который помогает ученикам в подготовке к экзаменам и изучении материала.\nСейчас ты ведёшь урок по предмету 'математика' для 5 класса.\nОбъясняй темы подробно, с примерами и проверяй понимание ученика.\nЕсли ученик не понимает — разбирай тему с нуля.")

    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    try:
        with GigaChat(
            credentials=GIGACHAT_CREDENTIALS,
            scope="GIGACHAT_API_PERS",
            verify_ssl_certs=False
        ) as giga:
            # Всегда добавляем системное сообщение с ролью в начало истории
            messages = [
                Messages(
                    role=MessagesRole.SYSTEM,
                    content=bot_role
                )
            ]

            # Добавляем историю сообщений (если нужна)
            for msg in conversation_history:
                messages.append(msg)

            # Добавляем текущее сообщение пользователя
            messages.append(
                Messages(
                    role=MessagesRole.USER,
                    content=user_message
                )
            )

            payload = Chat(messages=messages)
            response = giga.chat(payload)

            # Сохраняем ответ бота в историю
            conversation_history.append(
                Messages(
                    role=MessagesRole.USER,
                    content=user_message
                )
            )
            conversation_history.append(
                Messages(
                    role=MessagesRole.ASSISTANT,
                    content=response.choices[0].message.content
                )
            )

            return jsonify({"answer": response.choices[0].message.content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
