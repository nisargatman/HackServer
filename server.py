from flask import Flask, jsonify, request, abort, make_response
from flask.ext.httpauth import HTTPBasicAuth
import os
import sys
from tinydb import TinyDB, Query
import requests
import json
from nltk.corpus import wordnet
import base64
import time

app = Flask(__name__)
auth = HTTPBasicAuth()

db = TinyDB('db.json')

_key = '127d4e6c2d7e4b22a0e1a1d77cc40d1c'
_url = 'https://westus.api.cognitive.microsoft.com/vision/v1.0/ocr'
headers = {'Content-Type': 'application/octet-stream','Ocp-Apim-Subscription-Key': _key}
params = {'language': 'en','detectOrientation ': 'true'}


@auth.get_password
def get_password(username):
    if username == 'chris':
        return 'python'
    elif username == 'matt':
        return 'java'
    return None

@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized access'}), 401)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

@app.errorhandler(400)
def bad_input(error):
    return make_response(jsonify({'error': 'Bad Input'}), 400)


def _local_encode(output):
    try:
        regions = output["regions"]
    except:
        return
    total = 0
    counter = 0
    classes = ['grocery','drinks','meal','vegetable','clothes','tourism','luxury','furniture','vehicle','name','country','money']
    for entry in classes:
        syns = wordnet.synsets(entry)
        val = syns[0]
        classes[counter] = val
        counter = counter + 1
    
    items = []
    lines = [region["lines"] for region in regions] # now a list of lists
    y_dict = {}
    for sublist in lines:
        for entry in sublist:
            coord = entry["boundingBox"]
            coord = int(coord.split(',')[1])
            if coord not in y_dict:
                y_dict[coord] = [entry["words"]]
            else:
                y_dict[coord].append(entry["words"])
    for ordinate, words in enumerate(y_dict):
        maximum = 0
        counter = 0
        for word in words:
            val = word["text"]
            if val.isalpha():
                sim_vector = list()
                for label in classes:
                    try:
                        syns = wordnet.synsets(val)
                        temp = syns[0]
                        sim_vector.append(temp.wup_similarity(label))
                    except:
                        sim_vector.append(0)
                if max(sim_vector) > maximum:
                    maximum = max(sim_vector)
                    max_id = val
                    label = classes[sim_vector.index(max(sim_vector))]
            else:
                price = 0
                try:
                    num = float(val)
                except:
                    pass
                if isinstance(num,float) and '.' in val:
                    price = num
                #elif u"£" in val:
                    #price = float(val[1:])
                total = total + price
            counter = counter + 1
        items.extend([max_id,label,price])
    
    return json.dumps({time.time():{"vendor":"Sainsburys","total":total,"items":items}})
            
    


def _clean(output):
    try:
        regions = output["regions"]
    except:
        return

    txt_list = list()
    for entry in regions:
        lines = entry["lines"]
        for data in lines:
            words = data["words"]
            for text in words:
                txt_list.append(text["text"].encode('ascii','ignore'))

    counter = 0
    classes = ['grocery','drinks','meal','vegetable','clothes','tourism','luxury','furniture','vehicle','name','country','money']
    for entry in classes:
        syns = wordnet.synsets(entry)
        val = syns[0]
        classes[counter] = val
        counter = counter + 1

    similarity_matrix = list() # text_values x labels
    for each in txt_list:
        sim_vector = list()
        for label in classes:
            try:
                syns = wordnet.synsets(each)
                val = syns[0]
                sim_vector.append(val.wup_similarity(label))
            except:
                sim_vector.append(0)
        similarity_matrix.append(sim_vector)


    def _find_price(ctr):
        for val in [txt_list[n] for n in [ctr + 1, ctr + 2, ctr + 3]]:
            try:
                num = float(val)
            except:
                pass
            if isinstance(num,float) and '.' in val:
                return num
            else:
                return 0
          
    cutoff = 0.25
    output_dict = {}
    ctr = 0
    for entry in similarity_matrix:
        if txt_list[ctr].isalpha() and len(txt_list[ctr])>=2:
            if any(x >= cutoff for x in entry):
                item = txt_list[ctr]
                labelno = entry.index(max(entry))
                label = classes[labelno]
                price = 0
                try:
                    price = _find_price(ctr)
                except:
                    pass
                output_dict[item] = [label.lemmas()[0].name().encode('ascii','ignore'),price]
        ctr = ctr + 1

    return json.dumps(output_dict)


@app.route('/image/v1/read_text', methods=['POST'])
def read_text():
    if not request.json or not 'image' in request.json:
        abort(400)
    print "\n\n\n\nGood Request\n\n\n"

    im = base64.b64decode(request.json['image'])
    with open('im.jpg','w') as f:
        f.write(im)
    with open('im.jpg','rb') as image_file:
	    data = image_file.read()

    response = requests.request( 'post', _url, data=data, headers=headers, params=params)
    os.remove('im.jpg')

    return jsonify({"RawText":response.json(),"CleanText":_clean(response.json()),"LocalFormat":_local_encode(response.json())})

@app.route('/image/v1/post_image', methods=['POST'])
@auth.login_required
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
    return jsonify({"ReturnCode":str(201)})

@app.route('/image/v1/get_image/<int:customer_id>/<int:serial_number>',methods=['GET'])
@auth.login_required
def get_receipt(customer_id,serial_number):
    Customer = Query()
    receipts = db.search((Customer.CustomerID == customer_id) & (Customer.SerialNumber >= serial_number))
    return jsonify({"Receipts":receipts})

@app.route('/image/v1/clean_database',methods=['GET'])
@auth.login_required
def clean_database():
    db.purge()
    return jsonify({"ReturnCode":201})

@app.route('/image/v1/delete_entry/<int:customer_id>/<int:serial_number>',methods=['GET'])
@auth.login_required
def delete_entry(customer_id,serial_number):
    Customer = Query()
    db.remove((Customer.CustomerID == customer_id) & (Customer.SerialNumber == serial_number))


if __name__ == '__main__':
    app.run(host='0.0.0.0')