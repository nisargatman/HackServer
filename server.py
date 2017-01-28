from flask import Flask, jsonify, request, abort
from google.cloud import vision
from PIL import Image
import io
import os
from tinydb import TinyDB, Query

app = Flask(__name__)
client = vision.Client()
db = TinyDB('db.json')

def _convert_to_image(img_bytearray):
    output = io.BytesIO(img_bytearray)
    #output.flush()
    output.seek(0)
    return Image.open(output)

@app.route('/image/v1/read_text', methods=['POST'])
def get_json():
    if not request.json or not 'image' in request.json:
        abort(400)
    print "\n\n\n\nGood Request\n\n\n\n"
    print type(request.json['image'])
    print request.json['image']
    image = _convert_to_image(bytearray(request.json['image'],'utf8'))
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
    receipt = request.json['image']
    db.insert({'CustomerID':customer_id,'Receipt':receipt})

@app.route('/image/v1/get_image/<int:customer_id>',methods=['GET'])
def get_receipt(customer_id):
    Customer = Query()
    receipts = db.search(Customer.CustomerID == customer_id)
    return jsonify({"receipts":receipts})

if __name__ == '__main__':
    app.run(host='0.0.0.0')