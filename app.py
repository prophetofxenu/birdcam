from flask import Flask, render_template, request
from picamera import PiCamera
from base64 import b64encode
import board
from adafruit_dht import DHT11
import subprocess
import os
from threading import Lock
from time import sleep


app = Flask(__name__)
camera_lock = Lock()

dht = DHT11(board.D4)
last_temp = 0
last_humidity = 0

img_counter = 0
vid_counter = 0

pic_resolutions = {
  '640x480': (640, 480),
  '1296x730': (1296, 730),
  '1296x972': (1296, 972),
  '1920x1080': (1920, 1080),
  '2592x1944': (2592, 1944)
}
isos = {
  '0': 0,
  '100': 100,
  '200': 200,
  '320': 320,
  '400': 400,
  '500': 500,
  '640': 640,
  '800': 800
}


@app.route('/')
def main():
  return render_template('app.html')


@app.route('/api/environment')
def environment():
  global last_temp
  global last_humidity
  temp_c = 0
  humidity = 0
  current = False
  for _ in range(1):
    try:
      temp_c = dht.temperature
      humidity = dht.humidity
      if temp_c == None or humidity == None:
        sleep(0.2)
        continue
      last_temp = temp_c
      last_humidity = humidity
      current = True
      break
    except RuntimeError:
      sleep(0.2)
    except OSError:
      sleep(0.2)
  if current:
    temp_f = temp_c * (9 / 5) + 32
    return {
      'ok': True,
      'current': current,
      'temp_c': round(temp_c),
      'temp_f': round(temp_f),
      'humidity': humidity
    }
  elif not current and last_temp != None and last_humidity != None:
    temp_c = last_temp
    humidity = last_humidity
    temp_f = temp_c * (9 / 5) + 32
    return {
      'ok': True,
      'current': current,
      'temp_c': round(temp_c),
      'temp_f': round(temp_f),
      'humidity': humidity
    }
  else:
    return {
      'ok': False
    }

@app.route('/api/preview')
def preview():
  iso = isos[request.args.get('iso', default='auto')]
  awb_mode = request.args.get('awb', default='auto')
  brightness = request.args.get('brigthness', default=50, type=int)
  contrast = request.args.get('contrast', default=0, type=int)
  exposure_mode = request.args.get('exposuremode', default='auto')
  exposure_compensation = request.args.get('exposurecompensation', default=0, type=int)
  image_effect = request.args.get('imageeffect', default='none')
  meter_mode = request.args.get('metermode', default='average')
  rotation = request.args.get('rotation', default=0, type=int)
  saturation = request.args.get('saturation', default=0, type=int)
  sharpness = request.args.get('sharpness', default=0, type=int)
  shutter_speed = request.args.get('shutterspeed', default=0, type=int)
  video_stabilization = request.args.get('videostabilization', default=False, type=bool)

  output = bytearray(250000)
  with camera_lock, PiCamera() as camera:
    camera.ISO = iso
    camera.awb_mode = awb_mode
    camera.brightness = brightness
    camera.contrast = contrast
    camera.exposure_mode = exposure_mode
    camera.exposure_compensation = exposure_compensation
    camera.image_effect = image_effect
    camera.meter_mode = meter_mode
    camera.rotation = rotation
    camera.saturation = saturation
    camera.sharpness = sharpness
    camera.shutter_speed = shutter_speed
    camera.video_stabilization = video_stabilization
    camera.capture(output, 'jpeg', use_video_port=True)
  return { 'data': b64encode(bytes(output)) }


@app.route('/api/takepicture')
def takePicture():
  global img_counter
  path = f'static/images/IMG_{img_counter:04}.jpg'

  resolution = pic_resolutions[request.args.get('resolution', default='2592x1944')]
  iso = isos[request.args.get('iso', default='auto')]
  awb_mode = request.args.get('awb', default='auto')
  brightness = request.args.get('brigthness', default=50, type=int)
  contrast = request.args.get('contrast', default=0, type=int)
  exposure_mode = request.args.get('exposuremode', default='auto')
  exposure_compensation = request.args.get('exposurecompensation', default=0, type=int)
  image_effect = request.args.get('imageeffect', default='none')
  meter_mode = request.args.get('metermode', default='average')
  rotation = request.args.get('rotation', default=0, type=int)
  saturation = request.args.get('saturation', default=0, type=int)
  sharpness = request.args.get('sharpness', default=0, type=int)
  shutter_speed = request.args.get('shutterspeed', default=0, type=int)
  video_stabilization = request.args.get('videostabilization', default=False, type=bool)

  img_counter += 1
  with camera_lock, PiCamera() as camera:
    camera.resolution = resolution
    camera.ISO = iso
    camera.awb_mode = awb_mode
    camera.brightness = brightness
    camera.contrast = contrast
    camera.exposure_mode = exposure_mode
    camera.exposure_compensation = exposure_compensation
    camera.image_effect = image_effect
    camera.meter_mode = meter_mode
    camera.rotation = rotation
    camera.saturation = saturation
    camera.sharpness = sharpness
    camera.shutter_speed = shutter_speed
    camera.video_stabilization = video_stabilization
    camera.capture(path, 'jpeg')
  return { 'ok': True, 'path': path }


@app.route('/api/takevideo')
def takeVideo():
  global vid_counter

  resolution = pic_resolutions[request.args.get('resolution', default='2592x1944')]
  iso = isos[request.args.get('iso', default='auto')]
  awb_mode = request.args.get('awb', default='auto')
  brightness = request.args.get('brigthness', default=50, type=int)
  contrast = request.args.get('contrast', default=0, type=int)
  exposure_mode = request.args.get('exposuremode', default='auto')
  exposure_compensation = request.args.get('exposurecompensation', default=0, type=int)
  meter_mode = request.args.get('metermode', default='average')
  rotation = request.args.get('rotation', default=0, type=int)
  saturation = request.args.get('saturation', default=0, type=int)
  sharpness = request.args.get('sharpness', default=0, type=int)
  shutter_speed = request.args.get('shutterspeed', default=0, type=int)
  video_stabilization = request.args.get('videostabilization', default=False,
    type=(lambda x: True if x == 'true' else False))
  duration = request.args.get('duration', default=15, type=int)
  framerate = request.args.get('framerate', default=15, type=int)
  video_effect = request.args.get('videoeffect', default='none')

  h264_path = f'static/videos/VID_{vid_counter:04}.h264'
  mp4_path = f'static/videos/VID_{vid_counter:04}.mp4'
  vid_counter += 1
  with camera_lock, PiCamera() as camera:
    camera.resolution = resolution
    camera.ISO = iso
    camera.awb_mode = awb_mode
    camera.brightness = brightness
    camera.contrast = contrast
    camera.exposure_mode = exposure_mode
    camera.exposure_compensation = exposure_compensation
    camera.meter_mode = meter_mode
    camera.rotation = rotation
    camera.saturation = saturation
    camera.sharpness = sharpness
    camera.shutter_speed = shutter_speed
    camera.video_stabilization = video_stabilization
    camera.framerate = framerate
    camera.image_effect = video_effect
    camera.start_recording(h264_path)
    sleep(duration)
    camera.stop_recording()
  subprocess.run(['ffmpeg', '-y', '-r', str(framerate), '-i', h264_path, '-c', 'copy', mp4_path])
  os.remove(h264_path) 
  return { 'ok': True, 'path': mp4_path }


if __name__ == '__main__':

  print('Starting')

  for image in os.listdir('static/images'):
    print(f'Removing {image}')
    os.remove(f'static/images/{image}')
  for video in os.listdir('static/videos'):
    print(f'Removing {video}')
    os.remove(f'static/videos/{video}')

  print('Attempting to get temperature')
  dht_tries = 0
  while True:
    try:
      last_temp = dht.temperature
      last_humidity = dht.humidity
      if last_temp != None and last_humidity != None or dht_tries >= 300:
        print('Got temperature')
        break
      else:
        dht_tries += 1
        sleep(0.2)
    except RuntimeError:
      dht_tries += 1
      sleep(0.2)

  app.run('0.0.0.0', 8080, debug=False)

