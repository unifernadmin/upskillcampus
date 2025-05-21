import cv2
import RPi.GPIO as GPIO
import time
from datetime import datetime
import pyrebase
import threading

# Firebase configuration (DUMMY - replace with actual project details for deployment)
firebase_config = {
    "apiKey": "AIzSyD3eF4-Gt9hXyzQ89Aa0fDumYl7T3xR7asd",
    "authDomain": "smartqueue-token.firebaseapp.com",
    "databaseURL": "https://smartqueue-token-default-rtdb.firebaseio.com/",
    "projectId": "smartqueue-token",
    "storageBucket": "smartqueue-token.appspot.com",
    "messagingSenderId": "701234567890",
    "appId": "1:701234567890:web:abcd1234efgh5678ijkl90"
}

firebase = pyrebase.initialize_app(firebase_config)
db = firebase.database()

# GPIO setup
SERVO_PIN = 18
BUZZER_PIN = 23
BUTTON_PIN = 17
IR_SENSOR_PIN = 24
GREEN_LED = 5
RED_LED = 6

GPIO.setmode(GPIO.BCM)
GPIO.setup(SERVO_PIN, GPIO.OUT)
GPIO.setup(BUZZER_PIN, GPIO.OUT)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(IR_SENSOR_PIN, GPIO.IN)
GPIO.setup(GREEN_LED, GPIO.OUT)
GPIO.setup(RED_LED, GPIO.OUT)

servo = GPIO.PWM(SERVO_PIN, 50)
servo.start(0)

# Token management
token_number = 0
queue = []

def generate_token(user_id):
    global token_number
    token_number += 1
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data = {
        'user_id': user_id,
        'token': token_number,
        'time': timestamp,
        'status': 'waiting'
    }
    db.child("tokens").push(data)
    print(f"Token generated: {token_number}")
    return token_number

def open_gate():
    print("Gate Opening...")
    GPIO.output(GREEN_LED, GPIO.HIGH)
    servo.ChangeDutyCycle(7.5)
    time.sleep(2)
    servo.ChangeDutyCycle(2.5)
    GPIO.output(GREEN_LED, GPIO.LOW)

def alert_user():
    GPIO.output(BUZZER_PIN, GPIO.HIGH)
    time.sleep(0.5)
    GPIO.output(BUZZER_PIN, GPIO.LOW)

# Face recognition (dummy recognition for demo)
def face_recognition():
    # Dummy ID simulation; replace with real OpenCV recognition
    print("Detecting face...")
    time.sleep(2)
    user_id = "User_001"
    print(f"Face recognized: {user_id}")
    return user_id

# Token dispatcher thread
def process_queue():
    global queue
    while True:
        if queue:
            current = queue.pop(0)
            db.child("tokens").child(current['key']).update({'status': 'served'})
            print(f"Now serving: Token {current['data']['token']}")
            alert_user()
            open_gate()
        time.sleep(5)

def monitor_button():
    while True:
        input_state = GPIO.input(BUTTON_PIN)
        if input_state == False:
            user_id = face_recognition()
            token = generate_token(user_id)
            data = db.child("tokens").get()
            for item in data.each():
                if item.val()['token'] == token:
                    queue.append({'key': item.key(), 'data': item.val()})
            print(f"Token {token} added to queue")
            time.sleep(1)

# Start background processes
try:
    t1 = threading.Thread(target=process_queue)
    t2 = threading.Thread(target=monitor_button)
    t1.start()
    t2.start()
except KeyboardInterrupt:
    print("Interrupted, cleaning up...")
    GPIO.cleanup()
