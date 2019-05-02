from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/ask', methods=['POST'])
def ask():
    payload = {'text': 'working!!!'}
    payload = jsonify(payload)
    payload.status_code = 200
    return payload


if __name__=='__main__':
    print('starting')
    app.run()
