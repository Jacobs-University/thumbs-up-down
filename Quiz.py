import requests
import json
import cv2 as cv
import numpy as np
import mediapipe as mp
import html
from xml.sax.saxutils import unescape
import textwrap 
import HandTrackingModule as htm
import time

# https://google.github.io/mediapipe/solutions/hands
# For the paper use explanations from:
# https://www.youtube.com/watch?v=p5Z_GGRCI5s
# camel case

# Getting data from the API
response = requests.get("https://opentdb.com/api.php?amount=10&type=boolean")
data = response.text
parsed = json.loads(data)
# print(json.dumps(parsed, indent=4))

# # Printing only questions and answers from the API response
# for question in parsed["results"]: 
#   q = question["question"]
#   a = question["correct_answer"]
#   print(html.unescape(q) + " : " + a)

# Video capture from camera
cap = cv.VideoCapture(0)
if not cap.isOpened():
  print("Cannot open camera")
  exit()

fps = cap.get(5)
cap.set(3, 1280)
cap.set(4, 720)

# User input variables
thumb = "None"
tempThumb = "None"
thumbFrames = 0
responseFrames = 1.5 * fps # 3s * 30fps = 90 frames (usually cameras have 30fps)
framesCount = 0
waitStart = 0

# Game related variables
gameIsStarting = False
gameStart = False
gameQuit = False
questionNumber = 0
score = 0
text = ''
questionFrames = 0
answer = None

# Main text parameters to be used in putText() function call
x, y = 15, 15
font = cv.FONT_HERSHEY_SIMPLEX
fontSize = 0.5
fontColor = (255, 255, 255)
fontThickness = 1

# Using hand detector from the HandTrackingModule file, which uses the Google mediapipe library
detector = htm.handDetector(detectionCon=0.75)

# Reading each frame from video capture
while True:
  ret, frame = cap.read()

  if not ret:
    print("Can't receive frame (stream end?). Exiting ...")
    break 

  # Drawing hands in the video input
  frame = detector.findHands(frame)

  # Finding key landmark positions in hands
  lmList = detector.findPosition(frame, draw=False)

  # Statement to check if thumb is up or not
  # If tempThumb remains up or down for at least 3s then thumb value is also set
  # This is to give the user time to think (also the option of changing their mind) and have a slower transitions to questions
  if len(lmList) != 0:
    framesCount += 1
    if lmList[4][2] < lmList[2][2]:
      if framesCount < responseFrames:
        tempThumb = "Up"
      else:
        thumb = "Up"
        # print("Thumb up")
    elif lmList[4][2] > lmList[2][2]:
      if framesCount < responseFrames:
        tempThumb = "Down"
      else:
        thumb = "Down"
        # print("Thumb down")
  else:
    tempThumb = "None"
    thumb = "None"
    framesCount = 0
      
  # Drawing black rectangle to display text
  cv.rectangle(frame, (0, 0), (1280, 50), (0,0,0), -1)

  # Logic of game while user hasn't quit
  if gameQuit is False:
    # Display before game has stared
    if gameStart is False:
      if gameIsStarting is False:
        text = "Thumbs up to START quiz, thumbs down or 'q' to QUIT" 
        cv.putText(frame, text, (15, 30), font, 0.7, fontColor, 2, cv.LINE_4)

        # If thimb is up for at least 2s 
        if tempThumb == "Up":
          cv.putText(frame, "START", (30, 150), font, 2, (0, 255, 0), 3, cv.LINE_4)
          if thumb == "Up":
            gameIsStarting = True
          
        # Quitting the game if thumb is down
        elif tempThumb == "Down":
          cv.putText(frame, "QUIT", (30, 150), font, 2, (0, 0, 255), 3, cv.LINE_4)
          if thumb == "Down":
            break

      # Display once game starts
      elif gameIsStarting is True:
        waitStart += 1
        waitTime = 4 * fps - waitStart
        if waitTime > 0:
          text = "Quiz starting in: " + str(int(waitTime/fps)) + "s"
          cv.putText(frame, text, (15, 30), font, 0.7, (255, 255, 255), 2, cv.LINE_4)
        else:
          gameStart = True

    # Showing current question
    else:
      if questionNumber != 10:
        text = "Question " + str(questionNumber + 1) + ": " + html.unescape(parsed["results"][questionNumber]["question"]) 
        cv.putText(frame, text, (15, 30), font, 0.5, fontColor, fontThickness, cv.LINE_4)

        # Score
        sc = "Score: " + str(score)
        cv.putText(frame, sc, (50, 680), font, 2.5, fontColor, 3, cv.LINE_4)

        questionFrames += 1
        questionTime = 10 * fps - questionFrames

        # Displaying time left for current question
        tm = "Time: " + str(int(questionTime/fps)) + "s"
        cv.putText(frame, tm, (450, 680), font, 2.5, (0, 0, 0), 3, cv.LINE_4)

        if (questionTime > 0) and answer is None:
          # True answer 
          if tempThumb == "Up":
            cv.putText(frame, "TRUE", (30, 150), font, 2, (0, 255, 0), 3, cv.LINE_4)
            if thumb == "Up":
              answer = "True"
            
          # False answer
          elif tempThumb == "Down":
            cv.putText(frame, "FALSE", (30, 150), font, 2, (0, 0, 255), 3, cv.LINE_4)
            if thumb == "Down":
              answer = "False"
        
        elif (questionTime < 0) or answer is not None:
          # Giving time to user to change hand position
          cv.waitKey(1500)
          
          # Checking correctness
          if answer == parsed["results"][questionNumber]["correct_answer"]:
            score += 1

          # Increment question number and reset answer and calculated frames
          framesCount = 0
          questionFrames = 0
          questionNumber += 1
          answer = None          

      else:
        sc = "Final Score: " + str(score)
        cv.putText(frame, sc, (50, 680), font, 2.5, (255, 0, 0), 3, cv.LINE_4)

  else:
    break

  # Display the resulting frame
  cv.imshow('Quiz', frame)
  if cv.waitKey(1) == ord('q'):
    break
# When everything done, release the capture
cap.release()
cv.destroyAllWindows()
