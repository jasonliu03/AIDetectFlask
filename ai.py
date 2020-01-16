import os
import pprint
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Optional
from uuid import uuid4

from flask import request, jsonify, abort
import json
import numpy as np

import cv2

from pydiagnosis import autoPhoto, autoPhotoTongue, envtDetect, faceKps, faceVerify, faceCompare, faceCompareEmd, getEmdDirect
from flask import Flask
app = Flask(__name__)

@app.route("/")
def testGlassDetect():
    return "ai detect"


class PhotoType(Enum):
    autoPhoto = 1
    autoPhotoTongue = 2
    envtDetect = 3
    faceKps = 4
    genderDetect = 5
    faceMatch = 6
    faceMatchEmd = 7
    getEmdDirect = 8


ANALYZE_FUNCTIONS = {
    #PhotoType.faceDetect: faceDetect,
    #PhotoType.tongueDetect: tongueDetect,
    #PhotoType.glassDetect: glassDetect,
    PhotoType.autoPhoto: autoPhoto,
    PhotoType.autoPhotoTongue: autoPhotoTongue,
    PhotoType.envtDetect: envtDetect,
    PhotoType.faceKps: faceKps,
}

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp'}
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def detect_photo_errors(f):
    @wraps(f)
    def _f(*args, **kwargs):
        if 'photo' not in request.files:
            return jsonify({'error': 'no file submitted'})
        photo = request.files['photo']
        if not photo.filename or not allowed_file(photo.filename):
            return jsonify({'error': 'invalid file type'})
        return f(photo, *args, **kwargs)
    return _f

def detect_photos_errors(f):
    @wraps(f)
    def _f(*args, **kwargs):
        if 'photo01' not in request.files:
            return jsonify({'error': 'no file submitted'})
        photo01 = request.files['photo01']
        if 'photo02' not in request.files:
            return jsonify({'error': 'no file submitted'})
        photo02 = request.files['photo02']
        if not photo01.filename or not allowed_file(photo01.filename):
            return jsonify({'error': 'invalid file type'})
        if not photo02.filename or not allowed_file(photo02.filename):
            return jsonify({'error': 'invalid file type'})
        return f(photo01, photo02, *args, **kwargs)
    return _f

def detect_emds_errors(f):
    @wraps(f)
    def _f(*args, **kwargs):
        # bytes to dict 
        params = eval(request.data)
        #params = json.loads(request.data.decode())
        photo01 = params['photo01']
        photo02 = params['photo02']
        #if not photo01.filename or not allowed_file(photo01.filename):
        #    return jsonify({'error': 'invalid file type'})
        #if not photo02.filename or not allowed_file(photo02.filename):
        #    return jsonify({'error': 'invalid file type'})
        return f(photo01, photo02, *args, **kwargs)
    return _f

@detect_photo_errors
def handle_form_photo(photo, photo_type: PhotoType):
    content = photo.read(-1)

    ans = analyze(content, photo_type)

    app.logger.info('output: %s', pprint.pformat(ans))

    if photo_type == PhotoType.faceKps:
        return jsonify(ans)
    elif photo_type == PhotoType.genderDetect:
        return jsonify(ans)
    elif photo_type == PhotoType.faceMatch:
        return jsonify(ans)
    elif photo_type == PhotoType.faceMatchEmd:
        return jsonify(ans)
    elif photo_type == PhotoType.envtDetect:
        return jsonify({
            'level': ans['level'],
            'brightness': ans['brightness'],
        })
    else:
        return jsonify({
            'status': ans['status'],
            'x_point': ans['x_point'],
            'y_point': ans['y_point'],
            'width': ans['width'],
            'height': ans['height'],
        })

@detect_photo_errors
def handle_form_photo_py(photo, photo_type: PhotoType):
    content = photo.read(-1)
    tmpGenderImg = os.path.join(".",photo.name)
    destination = open(tmpGenderImg,'wb+')    # 打开特定的文件进行二进制的写操作
    destination.write(content)
    destination.close()
    rst = 0
    if photo_type == PhotoType.genderDetect:
        rst = predictGender(tmpGenderImg)
    if photo_type == PhotoType.faceMatch:
        rst = faceVerify(tmpGenderImg)
    if photo_type == PhotoType.getEmdDirect:
        rst = getEmdDirect(tmpGenderImg)
        rst = json.dumps(rst)
    ans = {}
    ans['status'] = rst
    return jsonify({'status': str(ans['status'])})
    
@detect_photos_errors
def handle_form_photos_py(photo01, photo02, photo_type: PhotoType):
    content = photo01.read(-1)
    content02 = photo02.read(-1)
    tmpGenderImg = os.path.join(".",photo01.name)
    tmpGenderImg02 = os.path.join(".",photo02.name)
    destination = open(tmpGenderImg,'wb+')    # 打开特定的文件进行二进制的写操作
    destination.write(content)
    destination.close()
    destination02 = open(tmpGenderImg02,'wb+')    # 打开特定的文件进行二进制的写操作
    destination02.write(content02)
    destination02.close()
    rst = 0
    if photo_type == PhotoType.genderDetect:
        rst = predictGender(tmpGenderImg)
    if photo_type == PhotoType.faceMatch:
        rst = faceCompare(tmpGenderImg, tmpGenderImg02)
    ans = {}
    ans['status'] = rst
    return jsonify({'status': float(ans['status'])})
    
@detect_emds_errors
def handle_form_emds_py(photo01, photo02, photo_type: PhotoType):
    emd1 = np.asarray(photo01)
    emd2 = np.asarray(photo02)
    rst = 0
    if photo_type == PhotoType.faceMatchEmd:
        rst = faceCompareEmd(emd1, emd2)
    ans = {}
    ans['status'] = rst
    print("ans:", ans)
    return jsonify({'status': float(ans['status'])})


#@app.route('/api/photos/faceDetect', methods=['POST'])
#def face_detect():
#    return handle_form_photo(PhotoType.faceDetect)

#@app.route('/api/photos/tongueDetect', methods=['POST'])
#def tongue_detect():
#    return handle_form_photo(PhotoType.tongueDetect)

#@app.route('/api/photos/glassDetect', methods=['POST'])
#def glass_detect():
#    return handle_form_photo(PhotoType.glassDetect)

@app.route('/api/photos/autoPhoto', methods=['POST'])
def auto_photo():
    return handle_form_photo(PhotoType.autoPhoto)

@app.route('/api/photos/autoPhotoTongue', methods=['POST'])
def auto_photo_tongue():
    return handle_form_photo(PhotoType.autoPhotoTongue)

@app.route('/api/photos/envtDetect', methods=['POST'])
def envt_detect():
    return handle_form_photo(PhotoType.envtDetect)

@app.route('/api/photos/faceKps', methods=['POST'])
def faceKps():
    return handle_form_photo(PhotoType.faceKps)

@app.route('/api/photos/genderDetect', methods=['POST'])
def genderDetect():
    return handle_form_photo_py(PhotoType.genderDetect)

@app.route('/api/photos/faceVerify', methods=['POST'])
def faceMatch():
    return handle_form_photos_py(PhotoType.faceMatch)

@app.route('/api/photos/faceVerifyEmd', methods=['POST'])
def faceMatchEmd():
    return handle_form_emds_py(PhotoType.faceMatchEmd)

@app.route('/api/photos/getEmdDirect', methods=['POST'])
def getEmbedding():
    return handle_form_photo_py(PhotoType.getEmdDirect)

def analyze(content: bytes, photo_type: PhotoType):
    assert photo_type in (PhotoType.autoPhoto, PhotoType.autoPhotoTongue, PhotoType.envtDetect, PhotoType.faceKps), 'internal error, invalid photo type: %r' % (photo_type, )
    result = ANALYZE_FUNCTIONS[photo_type](content)
    ans = result.to_dict()
    return ans

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, threaded=True)

