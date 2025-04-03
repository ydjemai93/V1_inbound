#!/usr/bin/env python
import os
import sys
import argparse
import asyncio
from dotenv import load_dotenv

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Charger les variables d'environnement
load_dotenv()

async def setup_inbound_environment():
    """Configure l'environnement pour les appels entrants"""
    print("Configuration de l'environnement pour les appels entrants...")
    
    # Importer les fonctions de configuration
    from scripts.setup_inbound_trunk import create_inbound_trunk
    from scripts.setup_dispatch_rule import create_dispatch_rule
    
    # Configurer le trunk SIP entrant
    print("\n1. Configuration du trunk SIP entrant...")
    phone_number = os.environ.get('TWILIO_PHONE_NUMBER')
    if not phone_number:
        phone_number = input("Entrez le numéro de téléphone pour les appels entrants (ex: +15105551234): ")
    
    trunk_id = await create_inbound_trunk()
    print(f"Trunk SIP entrant configuré avec succès. ID: {trunk_id}")
    
    # Configurer la règle de dispatch
    print("\n2. Configuration de la règle de dispatch...")
    agent_name = "inbound-agent"
    rule_id = await create_dispatch_rule(agent_name=agent_name)
    print(f"Règle de dispatch configurée avec succès. ID: {rule_id}")
    
    print("\nConfiguration de l'environnement terminée.")
    print("\nÉTAPES SUIVANTES:")
    print("1. Démarrez l'agent: python -m agent.main dev")
    print("2. Démarrez l'API: python -m api.app")
    print("3. Configurez Twilio avec le TwiML de l'endpoint /twiml")
    print("4. Testez un appel entrant!")

def main():
    parser = argparse.ArgumentParser(description='Configure l\'environnement pour les appels entrants')
    args = parser.parse_args()
    
    asyncio.run(setup_inbound_environment())

if __name__ == "__main__":
    main()
