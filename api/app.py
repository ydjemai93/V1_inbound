from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import logging
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('api.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialisation de l'application Flask
app = Flask(__name__)
CORS(app)

# Import des routes
from .routes import register_routes

# Enregistrement des routes
register_routes(app)

@app.route("/", methods=["GET"])
def index():
    """Page d'accueil pour l'API"""
    return jsonify({
        "name": "Agent Téléphonique IA - API",
        "description": "API pour gérer les appels entrants avec un agent IA",
        "documentation": "Voir les endpoints API disponibles ci-dessous",
        "endpoints": [
            {
                "path": "/health",
                "method": "GET",
                "description": "Vérification de santé de l'API"
            },
            {
                "path": "/api/twilio/test",
                "method": "GET",
                "description": "Tester les variables d'environnement Twilio"
            },
            {
                "path": "/api/livekit/test",
                "method": "GET",
                "description": "Tester la connexion à LiveKit"
            },
            {
                "path": "/api/inbound/trunk/setup",
                "method": "POST",
                "description": "Configurer un trunk SIP entrant"
            },
            {
                "path": "/api/inbound/dispatch/setup",
                "method": "POST",
                "description": "Configurer une règle de dispatch pour les appels entrants"
            },
            {
                "path": "/api/agent/status",
                "method": "GET",
                "description": "Vérifier l'état de l'agent"
            },
            {
                "path": "/api/inbound/status",
                "method": "GET",
                "description": "Vérifier l'état de la configuration des appels entrants"
            },
            {
                "path": "/api/twilio/twiml",
                "method": "GET",
                "description": "Obtenir un TwiML pour configurer Twilio"
            },
            {
                "path": "/api/twilio/setup",
                "method": "POST",
                "description": "Instructions pour configurer Twilio avec TwiML Bin"
            },
            {
                "path": "/twiml",
                "method": "GET/POST",
                "description": "Endpoint TwiML directement accessible pour Twilio"
            }
        ]
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Démarrage de l'API sur le port {port}")
    app.run(host="0.0.0.0", port=port)
