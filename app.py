from flask import Flask, request, jsonify
from flask_mail import Mail, Message
from dotenv import load_dotenv
import os
from flask_cors import CORS
import mysql.connector
from mysql.connector import errorcode
import time

load_dotenv()

app = Flask(__name__)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = True

mail = Mail(app)

CORS(app)

@app.route('/send-quiz-to-class', methods=['POST'])
def send_to_student_mail():
	try:
		data = request.json
		teacher_name = data.get('teacher_name')
		teacher_email = data.get('teacher_email')
		class_name = data.get('class_name')
		quiz_id = data.get('quiz_id')
		quiz_name = data.get('quiz_name')
		quiz_code = data.get('quiz_code')
		class_id = data.get('class_id')

		# Check if required fields are provided
		print(data)

		if not teacher_name or not teacher_email or not class_name or not quiz_name or not quiz_code or not class_id or not quiz_id:
			return jsonify({'error': 'Missing required fields'}), 400

		# Connect to the database
		db_connection = mysql.connector.connect(
			user=os.getenv('USER'),
			password=os.getenv('PASSWORD'),
			port=os.getenv('PORT'),
			database='kwizania_onlinequizdb'
		)

		cursor = db_connection.cursor()

		# Retrieve all student emails for the specified class
		get_all_student_emails = "SELECT u.email FROM users_table u JOIN enrollment_table e ON u.user_id = e.student_id WHERE e.class_id = %s AND u.role = 'student'"
		cursor.execute(get_all_student_emails, (class_id,))
		student_emails = [row[0] for row in cursor.fetchall()]

		if not student_emails:
			return jsonify({'error': 'No students found in this class'}), 404

		sender_email = app.config['MAIL_USERNAME']
		subject = f'Regarding the Quiz {quiz_name}'
		body = f"Hello {teacher_name},\n\nThis is a notification regarding the upcoming quiz '{quiz_name}' for the Class {class_name} on KWIZANIA. Please use the following code to access the quiz: {quiz_code}.\n\nIf you have any questions or need further details, please feel free to contact me at {teacher_email}.\n\nThank you and best regards,\n{teacher_name}"

		# Send email to all student emails retrieved from the database
		for student_email in student_emails:
			msg = Message(subject=subject, sender=sender_email, recipients=[student_email], body=body)
			mail.send(msg)
			print(f"Email sent successfully to {student_email}")
			time.sleep(5)  # Sleep for 5 second to avoid rate limiting

		cursor.close()
		db_connection.close()

		return jsonify({'message': f'Emails sent successfully to {len(student_emails)} students'}), 200

	except Exception as e:
		return jsonify({'error': str(e)}), 500




@app.route('/send-class-invite', methods=['POST'])
def send_class_invite():
	try:
		data = request.json
		student_email = data.get('student_email')
		teacher_name = data.get('teacher_name')
		teacher_email = data.get('teacher_email')
		class_title = data.get('class_title')
		class_code = data.get('class_code')

		if not teacher_name or not class_code or not class_title or not teacher_email or not student_email:
			return jsonify({'error': 'Missing required fields'}), 400
		
		sender_email = app.config['MAIL_USERNAME']
		subject = f'Invitation to join {class_title}'
		body = f'Hello, I am {teacher_name}. I would like to invite you to join my class "{class_title}" on KWIZANIA. Please use the following code to join the class: {class_code}. If you have any questions, please reach out to me at {teacher_email}.'

		msg = Message(subject=subject, sender=sender_email, recipients=[student_email], body=body)

		mail.send(msg)

		return jsonify({'message': 'Email sent successfully'}), 200
	
	except Exception as e:
		return jsonify({'error': str(e)}), 500
	




@app.route('/send-lecture', methods=['POST'])
def send_lecture():
	try:
		data = request.json
		teacher_name = data.get('teacher_name')
		quiz_name = data.get('quiz_name')
		student_name = data.get('student_name')
		teacher_email = data.get('teacher_email')
		body = data.get('body')  # Body can be lesson text or a message

		# Check if attachment is provided as a file path or URL
		attachment = data.get('attachment')
		attachment_info = None

		if attachment:
			if attachment.startswith('http://') or attachment.startswith('https://'):
				attachment_info = attachment  # Store link to attachment
			else:
				# Assuming attachment is a file path
				if os.path.exists(attachment):
					attachment_size = os.path.getsize(attachment)
					if attachment_size > 20 * 1024 * 1024:  # 20 MB limit
						return jsonify({'error': 'Attachment is too large, provide a link instead'}), 400
					attachment_info = attachment  # Store file path to attachment
				else:
					return jsonify({'error': 'Attachment file not found'}), 400

		if not teacher_name or not quiz_name or not teacher_email:
			return jsonify({'error': 'Missing required fields'}), 400

		sender_email = app.config['MAIL_USERNAME']
		subject = f'Lecture and Reading Materials for {quiz_name}'
		recipient_email = teacher_email  # Sending to the teacher's email

		# Create Message object
		msg = Message(subject=subject, sender=sender_email, recipients=[recipient_email])

		# Compose email body
		msg.body = f'Hello {student_name},\n\nThis is an email from your teacher {teacher_name} regarding Quiz "{quiz_name}". {body}\n\nPlease review the attached materials.'

		# Attach file if provided
		if attachment_info:
			with app.open_resource(attachment_info) as attachment_file:
				msg.attach(attachment_info, attachment_file.read(), 'application/octet-stream')

		# Send email
		mail.send(msg)

		return jsonify({'message': 'Email sent successfully'}), 200

	except Exception as e:
		return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
	app.run(debug=True)
