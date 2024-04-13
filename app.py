from flask import Flask, request, jsonify
from flask_mail import Mail, Message
from dotenv import load_dotenv
import os
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME') 
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = True

mail = Mail(app)

CORS(app)

@app.route('/send-to-student-mail', methods=['POST'])
def send_to_student_mail():
    try:
        data = request.json
        teacher_name = data.get('teacher_name')
        quiz_code = data.get('quiz_code')
        student_email = data.get('student_email')

        if not teacher_name or not quiz_code or not student_email:
            return jsonify({'error': 'Missing required fields'}), 400

        sender_email = app.config['MAIL_USERNAME']
        subject = f'Regarding Quiz {quiz_code}'
        body = f'Hello {teacher_name},\n\nThis is a notification regarding Quiz {quiz_code}. Please reach out to {student_email} for further details.'

        msg = Message(subject=subject, sender=sender_email, recipients=[student_email], body=body)

        mail.send(msg)

        return jsonify({'message': 'Email sent successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
