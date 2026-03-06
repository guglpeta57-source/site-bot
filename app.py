import os
from flask import Flask, request, jsonify, render_template
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

GIGACHAT_CREDENTIALS = os.getenv("GIGACHAT_CREDENTIALS")

# История сообщений для контекста (опционально)
conversation_history = []

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask_gigachat():
    data = request.json
    user_message = data.get("message")
    bot_role = data.get("role", "Ты — учитель, который помогает ученикам отвечать на вопросы и готовиться к экзаменам. \
Сейчас ты ведёшь урок по предмету 'математика' для 5 класса. \
Отвечай на вопросы ученика максимально понятно и по делу. \
Если нужно объяснить тему — делай это кратко и с примерами.")

    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    try:
        with GigaChat(
            credentials=GIGACHAT_CREDENTIALS,
            scope="GIGACHAT_API_PERS",
            verify_ssl_certs=False
        ) as giga:
            # Формируем сообщения: роль + история + вопрос пользователя
            messages = [
                Messages(
                    role=MessagesRole.SYSTEM,
                    content=bot_role  # Контекст роли (не мешает ответам)
                )
            ]

            # Добавляем историю (опционально, для контекста диалога)
            for msg in conversation_history:
                messages.append(msg)

            # Добавляем текущий вопрос пользователя
            messages.append(
                Messages(
                    role=MessagesRole.USER,
                    content=user_message
                )
            )

            payload = Chat(messages=messages)
            response = giga.chat(payload)

            # Сохраняем диалог в историю (опционально)
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
