from flask import Flask, jsonify, request, abort
from google.cloud import vision
from PIL import Image
import io

app = Flask(__name__)
client = vision.Client()

def _convert_to_image(img_bytearray):
    return Image.open(io.BytesIO(img_bytearray))

@app.route('/image/v1/get_json', methods=['POST'])
def get_json():
    if not request.json or not 'image' in request.json:
        abort(400)
    image = _convert_to_image(request.json['image'])
    image.save('Image.jpg')
    image = client.image(filename='Image.jpg')
    texts = image.detect_text()
    return jsonify({"Text":texts})

if __name__ == '__main__':
    app.run(host='0.0.0.0')