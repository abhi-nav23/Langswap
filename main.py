from flask import Flask, request, jsonify
from flask_cors import CORS
from python_parser import parse_python_code_from_string

import os

app = Flask(__name__)
CORS(app)

@app.route('/translate', methods=['POST'])
def translate_code():
    data = request.get_json()
    python_code = data.get("code", "")

    if not python_code.strip():
        return jsonify({"error": "No code provided"}), 400

    cpp_code = parse_python_code_from_string(python_code)
    return jsonify({"cpp": cpp_code})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)
