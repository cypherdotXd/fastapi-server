import cv2
import numpy as np
import requests
from io import BytesIO
from PIL import Image


def load_models():
    path = 'age_gender_recognition/models'
    faceProto = path + '/opencv_face_detector.pbtxt'
    faceModel = path + '/opencv_face_detector_uint8.pb'
    ageProto = path + '/age_deploy.prototxt'
    ageModel = path + '/age_net.caffemodel'
    genderProto = path + '/gender_deploy.prototxt'
    genderModel = path + '/gender_net.caffemodel'
    
    faceNet = cv2.dnn.readNet(faceModel, faceProto)
    ageNet = cv2.dnn.readNet(ageModel, ageProto)
    genderNet = cv2.dnn.readNet(genderModel, genderProto)
    
    return faceNet, ageNet, genderNet

def detect_face(face_net, image, confidence_threshold=0.7):
    image_copy = image.copy()
    frameHeight = image_copy.shape[0]
    frameWidth = image_copy.shape[1]
    
    # Create input form image for nn
    blob = cv2.dnn.blobFromImage(image_copy, 1.0, (227, 227), [124.96, 115.97, 106.13], swapRB=True, crop=False)
    face_net.setInput(blob)
    detections = face_net.forward()
    
    # Extract and Arange faceboxes in array
    faceBoxes = []
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > confidence_threshold:
            x1 = int(detections[0, 0, i, 3] * frameWidth)
            y1 = int(detections[0, 0, i, 4] * frameHeight)
            x2 = int(detections[0, 0, i, 5] * frameWidth)
            y2 = int(detections[0, 0, i, 6] * frameHeight)
            faceBoxes.append([x1, y1, x2, y2])
            
    return image_copy, faceBoxes

def predict_age_and_gender(faceNet, ageNet, genderNet, frame):
    genderList = ['Male', 'Female']
    ageList = ['(0-2)', '(4-6)', '(8-12)', '(15-20)', '(25-32)', '(38-43)', '(48-53)', '(60-100)']
    padding = 30

    image, faceBoxes = detect_face(faceNet, frame)

    predictions = []
    for faceBox in faceBoxes:
        x1, y1, x2, y2 = faceBox
        # Crop face from the whole image using faceBox coordinates
        face = frame[max(0, y1 - padding):min(y2 + padding, frame.shape[0] - 1),
                     max(0, x1 - padding):min(x2 + padding, frame.shape[1] - 1)]
        
        if face.size == 0:
            print(f"Skipping empty face region: {faceBox}")
            continue

        # Create input form image for nn
        blob = cv2.dnn.blobFromImage(face, 1.0, (227, 227), [124.96, 115.97, 106.13], swapRB=True, crop=False)
        
        genderNet.setInput(blob)
        genderPreds = genderNet.forward()
        gender = genderList[genderPreds[0].argmax()]

        ageNet.setInput(blob)
        agePreds = ageNet.forward()
        age = ageList[agePreds[0].argmax()]

        predictions.append({'box': faceBox, 'gender': gender, 'age': age})
    
    return predictions

faceNet, ageNet, genderNet = load_models()

def process_image(image_url):

    response = requests.get(image_url)
    image = Image.open(BytesIO(response.content))
    frame = np.array(image)

    # Convert image to RGB (if it's in BGR)
    if frame.shape[2] == 3:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Predict age and gender
    predictions = predict_age_and_gender(faceNet, ageNet, genderNet, frame)

    # Draw results on the image
    for index, prediction in enumerate(predictions):
        faceBox = prediction['box']
        gender = prediction['gender']
        age = prediction['age']
        
        cv2.rectangle(frame, (faceBox[0], faceBox[1]), (faceBox[2], faceBox[3]), (0, 255, 0), 2)

        # Text parameters
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.9
        font_thickness = 2
        font_color = (0, 255, 255)  # Yellow color
        background_color = (0, 0, 0)  # Black color

        # Calculate text size
        (gender_text_width, gender_text_height), _ = cv2.getTextSize(f"{gender},", font, font_scale, font_thickness)
        (age_text_width, age_text_height), _ = cv2.getTextSize(f"{age}", font, font_scale, font_thickness)

        # Position for the first line (gender)
        gender_position = (faceBox[0] + 5, faceBox[1] + 20)

        # Position for the second line (age)
        age_position = (faceBox[0] + 5, faceBox[1] + 20 + gender_text_height + 10)  # 10 is the space between lines

        # Draw background rectangles
        cv2.rectangle(frame, (gender_position[0], gender_position[1] - gender_text_height - 10), 
                    (gender_position[0] + gender_text_width, gender_position[1] + 10), background_color, -1)
        cv2.rectangle(frame, (age_position[0], age_position[1] - age_text_height - 10), 
                    (age_position[0] + age_text_width, age_position[1] + 10), background_color, -1)

        # Put gender text
        cv2.putText(frame, f"{gender},", gender_position, font, font_scale, font_color, font_thickness, cv2.LINE_AA)

        # Put age text
        cv2.putText(frame, f"{age}", age_position, font, font_scale, font_color, font_thickness, cv2.LINE_AA)


    # Display the result
    temp_path = "temp/output_image.jpg"
    cv2.imwrite(temp_path, frame)

    return temp_path

# cv2.imshow("Age and Gender Detection", frame)
# cv2.waitKey(0)
# cv2.destroyAllWindows()