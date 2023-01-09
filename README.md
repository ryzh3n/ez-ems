# EZ-EMS 

This project has 2 parts: The `server` & the `attendance machine`

Please ensure the `server` is running before any attempt to run the `attendance machine`.

### HOW TO RUN THE SERVER:
1. Make sure your Python Intepreter has the following libraries/packages installed:
```
flask
flask_login
flask_sqlalchemy
colorama
apcheduler
flask_restful
flask_wtf
flask_limiter
flask_limiter.util
os
sqlalchemy
werkzeug
datetime
```
2. Setup your mySQL Server & remember the user credentials
3. Run main.py
4. Follow the steps 

### HOW TO RUN THE ATTENDANCE MACHINE:
1. Make sure your Python Intepreter has the following libraries/packages installed:
```
cv2
numpy
face_recognition (by Adam Getgey)
os
requests
```
2. Run Attendance_Machine.py
