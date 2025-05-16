from flask import Flask, jsonify
import json
from flask_cors import CORS
CORS(app)

app = Flask(__name__)

@app.route('/prediccion', methods=['GET'])
def obtener_prediccion():
    try:
        # Leer el archivo JSON con la predicción
        with open('../prediccion_mes.json', 'r', encoding='utf-8') as f:
            prediccion = json.load(f)
        return jsonify(prediccion)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
