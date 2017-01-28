from flask import Flask, jsonify, request, abort
from google.cloud import vision
from PIL import Image
import io
import os
from tinydb import TinyDB, Query
import base64

app = Flask(__name__)
client = vision.Client()
if os.path.exists('./db.json'):
    os.remove('db.json')
    db = TinyDB('db.json')

def _convert_to_image(img_bytearray):
    output = io.BytesIO(img_bytearray)
    output.seek(0)
    return Image.open(output)

@app.route('/image/v1/read_text', methods=['POST'])
def get_json():
    if not request.json or not 'image' in request.json:
        abort(400)
    print "\n\n\n\nGood Request\n\n\n\n"
    im = base64.b64decode(request.json['image'])
    image = _convert_to_image(bytearray(im))
    image.save('Image.jpg')
    image = client.image(filename='Image.jpg')
    print "\n\n\n\nImage saved\n\n\n\n"
    texts = image.detect_text()
    print "\n\n\n\nText detected\n\n\n\n"
    os.remove('Image.jpg')
    return jsonify({"Text":texts})

@app.route('/image/v1/post_image', methods=['POST'])
def post_receipt():
    if not request.json or not 'image' in request.json or not 'CustomerID' in request.json:
        abort(400)

    customer_id = request.json['CustomerID']
    print customer_id, '\n'
    receipt = request.json['image']
    print receipt, '\n'
    db.insert({'CustomerID':int(customer_id),'Receipt':receipt})
    #print db.all()
    return str(201)

@app.route('/image/v1/get_image/<int:customer_id>',methods=['GET'])
def get_receipt(customer_id):
    Customer = Query()
    receipts = db.search(Customer.CustomerID == customer_id)
    #print receipts
    return jsonify({"receipts":receipts})

if __name__ == '__main__':
    app.run(host='0.0.0.0')