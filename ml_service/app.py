from flask import Flask, request, jsonify
import joblib
import numpy as np
import os

app = Flask(__name__)

class ModelLoader:
    _instance = None
    _model = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(ModelLoader, cls).__new__(cls)
            cls._load_model()
        return cls._instance

    @classmethod
    def _load_model(cls):
        try:
            model_path = os.getenv('MODEL_PATH', '/app/models/default_model.pkl')
            
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model not found at {model_path}")

            cls._model = joblib.load(model_path)
            print(f"Model loaded successfully from {model_path}")
        except Exception as e:
            print(f"Model loading error: {e}")
            cls._model = None

    @classmethod
    def predict(cls, data):
        if cls._model is None:
            raise RuntimeError("Model not loaded")
        return cls._model.predict(data)

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json['data']
        model_loader = ModelLoader()
        predictions = model_loader.predict(np.array(data))
        return jsonify({'predictions': predictions.tolist()})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)