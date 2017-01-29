from flask import Flask, jsonify, request, abort
from PIL import Image
import io
import os
import sys
from tinydb import TinyDB, Query
import requests

app = Flask(__name__)
db = TinyDB('db.json')
_key = '127d4e6c2d7e4b22a0e1a1d77cc40d1c'
_url = 'https://westus.api.cognitive.microsoft.com/vision/v1.0/ocr'
headers = {'Content-Type': 'application/octet-stream','Ocp-Apim-Subscription-Key': _key}
params = {'language': 'en','detectOrientation ': 'true'}


@app.route('/image/v1/read_text', methods=['POST'])
def get_json():
    if not request.json or not 'image' in request.json:
        abort(400)
    print "\n\n\n\nGood Request\n\n\n"

    im = base64.b64decode(request.json['image'])
    with open('im.jpg','w') as f:
        f.write(im)
    with open('./im.jpg','rb') as image_file:
        data = image_file.read()

    with open('im.jpg','rb') as image_file:
	    data = image_file.read()

    response = requests.request( 'post', _url, json = None, data = data, headers = headers, params = params )
    os.remove('im.jpg')

    return jsonify({"Text":response.json()})

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