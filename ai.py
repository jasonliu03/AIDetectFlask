import pprint
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Optional
from uuid import uuid4

from flask import request, jsonify, abort

from pydiagnosis import autoPhoto, autoPhotoTongue, envtDetect, faceKps
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


@detect_photo_errors
def handle_form_photo(photo, photo_type: PhotoType):
    content = photo.read(-1)

    ans = analyze(content, photo_type)

    app.logger.info('output: %s', pprint.pformat(ans))

    if photo_type == PhotoType.faceKps:
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

def analyze(content: bytes, photo_type: PhotoType):
    assert photo_type in (PhotoType.autoPhoto, PhotoType.autoPhotoTongue, PhotoType.envtDetect, PhotoType.faceKps), 'internal error, invalid photo type: %r' % (photo_type, )
    result = ANALYZE_FUNCTIONS[photo_type](content)
    ans = result.to_dict()
    return ans

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, threaded=True)

