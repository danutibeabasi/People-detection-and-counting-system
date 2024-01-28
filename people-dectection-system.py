import cv2
import numpy as np
import requests
import json
import threading
import time

# Firebase configuration
FIREBASE_URL = 'https://smart-ease-and-green-default-rtdb.firebaseio.com/'
API_KEY = 'your_firebase_api_key'

detection_enabled = True  # Initial state

def fetch_detection_state():
    global detection_enabled
    while True:
        try:
            response = requests.get(FIREBASE_URL + 'detection_control.json?auth=' + API_KEY)
            detection_enabled = response.json() == True
        except Exception as e:
            print(f"Error fetching state: {e}")
        time.sleep(2)  # Check every 2 seconds

def send_people_count_to_firebase(people_count):
    endpoint = FIREBASE_URL + 'people_count.json?auth=' + API_KEY
    data = {"count": people_count}
    response = requests.post(endpoint, data=json.dumps(data))
    print("Data sent to Firebase:", response.text)

# Start thread to fetch detection state
threading.Thread(target=fetch_detection_state, daemon=True).start()

# Load YOLO
net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")
layer_names = net.getLayerNames()
out_layer_indexes = net.getUnconnectedOutLayers()
output_layers = [layer_names[i - 1] for i in out_layer_indexes]

# Initialize webcam
cap = cv2.VideoCapture(0)

prev_people_count = -1  # To track changes in people count

while True:
    _, frame = cap.read()
    height, width, channels = frame.shape

    if detection_enabled:
        # Detecting objects
        blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
        net.setInput(blob)
        outs = net.forward(output_layers)

        class_ids = []
        confidences = []
        boxes = []
        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > 0.5 and class_id == 0:  # Filter for 'person' class
                    # Object detected
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)
                    boxes.append([x, y, w, h])
                    confidences.append(float(confidence))

        indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
        people_count = len(indexes)

        if people_count != prev_people_count:
            send_people_count_to_firebase(people_count)
            prev_people_count = people_count

        for i in range(len(boxes)):
            if i in indexes:
                x, y, w, h = boxes[i]
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        cv2.putText(frame, f'People Count: {people_count}', (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("People Detection", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
