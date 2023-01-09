import cv2
import numpy as np
import face_recognition
import os
import requests

# Initialize some variables
auth_key = ''
server_ip = ''
server_port = ''

if os.path.exists(os.getcwd() + '/config.txt'):  # Check for config file
    file = open('config.txt', 'r')
    config = file.readlines()
    server_ip = config[0]
    server_port = config[1]
    auth_key = config[2]
else:  # Prompts User Input and Creates New Config File
    print('Config File Not Found!')
    new_config = []
    server_ip = input('Server IP >> ')
    new_config.append(server_ip)
    server_port = input('Server Port >> ')
    new_config.append(server_port)
    auth_key = input('Authentication Key >> ')
    new_config.append(auth_key)
    file = open('config.txt', 'w')
    file.writelines(new_config)
    file.close()

path = os.getcwd() + '/faces'  # Path to store the faces (photos)
if not os.path.exists(path):
    os.mkdir('faces')

# setup server ip
# request to ezapi ask for employee_profiles
# check with current /faces count
# if not same, request for update
# if same, continue program
base_url = f'http://{server_ip}:{server_port}/ezapi?category=att_mach&auth_key={auth_key}'

print('Connecting to Server to Update Resources...')
total_employees = requests.get(base_url + '&action=update')  # Update the /face folder
try:
    num = int(total_employees.text)
    print('Server >> Connected!')
except:
    print(f'Server >> {total_employees.text}')
    exit()

path_items = os.listdir(path)  # Count the number of items in /faces

if len(path_items) < int(total_employees.text):
    # If the total employees count on the server is larger than the number of items in /faces
    missing_profiles = int(total_employees.text) - len(path_items)  # Count the number of missing faces
    print(f'{missing_profiles} updates left...')
    start_update_id = len(path_items) + 1  # Start on next count
    print(f'starting update on no. {start_update_id}')
    for missing_id in range(start_update_id, int(total_employees.text) + 1):  # Loop missing faces times
        print(f'fetching from http://{server_ip}:{server_port}/static/uploads/employee_profile_pic/{missing_id}.jpg ...')
        # Fetch the new photos
        update_employee = requests.get(f'http://{server_ip}:{server_port}/static/uploads/employee_profile_pic/{missing_id}.jpg')
        os.chdir(path)
        open(f'{missing_id}.jpg', 'wb').write(update_employee.content)  # Download the photos

# Initialize some variables
images = []
names = []
attendance = []
persons = []

for p in path_items:
    names.append(p)  # Insert the name of each photo in /faces
    attendance.append(0)  # Initialize variable as 0 first, this is used for counting frames later
    persons.append('')  # Initialize variable as '' first, this is used to store employee names later

for c in names:
    curImg = cv2.imread(f'{path}/{c}')  # Read each photo in /faces
    print(f'Reading {c}...')
    images.append(curImg)  # Save the read photo into the List


def findEncodings(images):  # Function to get the face encoding of all photos in /faces
    encodeList = []
    for img in images:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encoded_face = face_recognition.face_encodings(img)[0]
        encodeList.append(encoded_face)
    return encodeList


print('Reading stored images into memory..')
encoded_face_train = findEncodings(images)  # Trains the images, loads to memory

print('Initializing video camera...')
cap = cv2.VideoCapture(0)  # Start the webcam
last_matchIndex = ''
# Initialize Variable as '' first, to check whether the face in the current frame is same face from the previous frame
face_found = False  # Initialize variable first, used to determine whether a face is found
frame_counter = 0  # Frame counter

while True:
    success, img = cap.read()  # Read each frames from the webcam
    if not success:  # Fails to read camera
        print('Failed to capture from video camera')
        break  # Exit the loop, ends the program
    imgS = cv2.resize(img, (0, 0), fx=0.25, fy=0.25)  # Resize the frame by 4 times, reduce lag
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB in each frame
    faces_in_frame = face_recognition.face_locations(imgS)  # Find the face locations in each frame
    encoded_faces = face_recognition.face_encodings(imgS, faces_in_frame)  # Gets the face encodings of found faces
    if face_found:  # If a face was found
        if frame_counter < 20:  # 20 frames
            frame_counter += 1
            cv2.rectangle(img, (0, 0), (500, 35), (255, 0, 0), cv2.FILLED)  # Draw a rectangle on the top left corner
            cv2.putText(img, 'Attendance Taken', (5, 27), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
            # Write 'Attendance Taken' in the rectangle drew on the top left corner
        else:  # < 20 frames
            frame_counter = 0
            face_found = False
    for encode_face, faceloc in zip(encoded_faces, faces_in_frame):
        # loop through each trained faces and compares with the found faces in each frame
        matches = face_recognition.compare_faces(encoded_face_train, encode_face)
        name = 'Unknown'  # Initialize as 'Unknown' before any faces were found
        faceDist = face_recognition.face_distance(encoded_face_train, encode_face)  # Determine who's face it is
        matchIndex = np.argmin(faceDist)
        if matches[matchIndex]:  # Found the matching face
            name = names[matchIndex].upper().lower()
            y1, x2, y2, x1 = faceloc  # Coordinates of the found face in each frame
            y1 *= 4
            x2 *= 4
            y2 *= 4
            x1 *= 4
            # Multiply the coordinates by 4, because already shrinked at first
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 1)  # Draw rectangle on the face in each frame
            if last_matchIndex == matchIndex:  # If last frame is same person with current frame
                if persons[matchIndex] != '':  # If the name of the found face was not stored previously
                    cv2.rectangle(img, (x1, y2), (x2, y2 + 35), (0, 255, 0), cv2.FILLED)
                    # Draw a rectangle under the face in each frame
                    cv2.putText(img, persons[matchIndex], (x1 + 6, y2 + 27), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
                    # Write the name of the person
                if attendance[matchIndex] < 20:  # If the captured frames of the same person is < 20 frames
                    attendance[matchIndex] += 1  # Increment the frame
                elif attendance[matchIndex] == 20:  # Same person stayed in front of camera for 20 frames
                    face_found = True
                    attendance[matchIndex] += 1  # Make it become 21, so won't capture again next loop
                    print(f'Captured {name[:-4]} within 5 frames')
                    print('Saving captured photo..')
                    cv2.imwrite(f'{name[:-4]} taken.jpg', img)  # Save the image
                    print('Done!')
                    print('Uploading attendance to Server ...')
                    response = requests.get(base_url + '&action=attendance&id=' + name[:-4])  # Take Attendance
                    persons[matchIndex] = response.json()['name']  # Store the person's name retrieve from server
                    print(response.json()['name'])
                    print(response.json()['department'])
                    print(response.json()['position'])
                    print(response.json()['date'])
                    print(response.json()['time'])
                    print(response.json()['day'])
            else:
                attendance[matchIndex] = 0  # Reset the frame count
            last_matchIndex = matchIndex  # Stores the current match index for next loop to compare with
    cv2.imshow('webcam', img)  # Show the webcam
    if cv2.waitKey(1) & 0xFF == ord('q'):  # Press Q to quit to app
        break
