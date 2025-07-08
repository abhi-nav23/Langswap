from flask import Flask, request, jsonify
from flask_cors import CORS
from langswap_engine.python_parser import parse_python_code_from_string

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
    app.run(port=8000, debug=True)
