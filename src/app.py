# coding: utf-8

import os
import requests
import sys
from bottle import route, run, static_file, get, post, request, template
from dotenv import load_dotenv
import speech_recognition as sr

reload(sys)
sys.setdefaultencoding('utf8')

# Load environment file for config.
load_dotenv(os.getcwd() + '/.env')

@route('/')
def indexReq():
  return template(os.getcwd() + '/src/templates/index.tpl', phone = os.getenv('PHONE_NUMBER'))

# Serve media files for call response.
@get('/media/<file>')
def mediaReq(file):
  return static_file(file, root = os.getcwd() + '/media')

# Server styles
@get('/styles/<file>')
def styleReq(file):
  return static_file(file, root = os.getcwd() + '/styles')

# Set route for receiving calls and playing sound.
@post('/call')
def callReq():
  return {
    'play': os.getenv('PUBLIC_URL') + '/media/audio.mp3',
    'skippable': False,
    'next': {
      'play': 'sound/beep',
      'next': {
        'record': os.getenv('PUBLIC_URL') + '/recording'
      }
    }
  }

@post('/recording')
def recordingReq():
  # Just make sure you get "wav", "from" and "to" in the request.
  if (request.forms.get('wav') != 'None' and request.forms.get('from') != 'None' and request.forms.get('to') != 'None'):
    # Download the .wav file to the server with API credentials
    extFilePath = request.forms.get('wav')
    localFilePath = os.getcwd() + '/recordings/' + os.path.basename(extFilePath)
    recFile = requests.get(extFilePath, auth = (os.getenv('API_USER'), os.getenv('API_PASS')))
    open(localFilePath, 'wb').write(recFile.content)

    # Run the recording the speech recognizer to get it in text.
    r = sr.Recognizer()
    audioFile = sr.AudioFile(localFilePath)
    with audioFile as source:
      audio = r.record(source)
    
    try:
      recInText = r.recognize_google(audio) # Actual text to send.

      # Delete recording file from disk.
      os.remove(localFilePath)

      # Send recording in text format via MMS to the caller.
      mmsData = {
        'to': request.forms.get('from'),
        'from': request.forms.get('to'),
        'message': 'You received a message:\n\n' + recInText,
        'image': 'https://www.46elks.se/static/images/media/46elks-horizontal.png'
      }
      mmsReq = requests.post('https://api.46elks.com/a1/mms', data = mmsData, auth = (os.getenv('API_USER'), os.getenv('API_PASS')))

      return { 'success': True }
    except:
      # Failed to recognize audio.
      return { 'success': False }
  else:
    return {
      'success': False,
      'message': 'Request failed, missing vital parameters.'
    }


run(host='0.0.0.0', port=5550)