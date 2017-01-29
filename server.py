from flask import Flask, jsonify, request, abort
from google.cloud import vision
from PIL import Image
import io
import os
import sys
from tinydb import TinyDB, Query
import base64

app = Flask(__name__)
client = vision.Client()
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
    im = request.json['image'].decode('UTF-8')
    #image = _convert_to_image(bytearray(im))
    #image.save('Image.jpg')
    image = client.image(content=im.read())
    print "\n\n\n\nImage saved\n\n\n\n"
    texts = image.detect_text()
    print "\n\n\n\nText detected\n\n\n\n"
    os.remove('Image.jpg')
    return jsonify({"Text":texts})

@app.route('/image/v1/post_image', methods=['POST'])
def post_receipt():
    if not request.json or not 'image' in request.json or not 'CustomerID' in request.json:
        abort(400)
    customer_id = int(request.json['CustomerID'])
    receipt = request.json['image']

    Customer = Query()
    nums = db.search(Customer.CustomerID == customer_id)
    print nums, '\n\n'
    serial_number = 0
    for entry in nums:
        print entry
        if entry['SerialNumber'] > serial_number:
            serial_number = entry['SerialNumber']

    db.insert({'CustomerID':customer_id, 'Receipt':receipt, 'SerialNumber':serial_number+1})
    #print db.all()
    return str(201)

@app.route('/image/v1/get_image/<int:customer_id>/<int:serial_number>',methods=['GET'])
def get_receipt(customer_id,serial_number):
    Customer = Query()
    print "SNO", serial_number
    print "CID", customer_id
    receipts = db.search((Customer.CustomerID == customer_id) & (Customer.SerialNumber >= serial_number))
    return jsonify({"receipts":receipts})

if __name__ == '__main__':
    app.run(host='0.0.0.0')