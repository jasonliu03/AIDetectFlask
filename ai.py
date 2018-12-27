import pprint
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Optional
from uuid import uuid4

from flask import request, jsonify, abort

from pydiagnosis import glassDetect
from flask import Flask
app = Flask(__name__)

@app.route("/testGlassDetect")
def testGlassDetect():
    return "glassDetect"


class PhotoType(Enum):
    faceDetect = 1
    tongueDetect = 2
    glassDetect = 3


ANALYZE_FUNCTIONS = {
    PhotoType.glassDetect: glassDetect,
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

    return jsonify({
        'status': ans['status'],
        'x_point': ans['x_point'],
        'y_point': ans['y_point'],
        'width': ans['width'],
        'height': ans['height'],
    })


@app.route('/api/photos/glassDetect', methods=['POST'])
def glass_detect():
    return handle_form_photo(PhotoType.glassDetect)


def analyze(content: bytes, photo_type: PhotoType):
    assert photo_type in (PhotoType.glassDetect, PhotoType.faceDetect, PhotoType.tongueDetect), 'internal error, invalid photo type: %r' % (photo_type, )
    result = ANALYZE_FUNCTIONS[photo_type](content)
    ans = result.to_dict()
    return ans



if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, threaded=True)

