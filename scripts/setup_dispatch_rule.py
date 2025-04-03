import asyncio
import os
import json
import argparse
from dotenv import load_dotenv
from livekit import api
from livekit.protocol.sip import CreateSIPDispatchRuleRequest, SIPDispatchRule, SIPDispatchRuleIndividual

# Chercher le fichier .env à la racine du projet
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
env_path = os.path.join(root_dir, ".env")
load_dotenv(env_path)

async def create_dispatch_rule(rule_file=None, agent_name=None):
    """
    Crée une règle de dispatch SIP dans LiveKit
    """
    # Initialisation du client LiveKit
    print("Initialisation du client LiveKit API...")
    livekit_api = api.LiveKitAPI()
    
    try:
        # Configuration par défaut si aucun fichier n'est fourni
        if not rule_file or not os.path.exists(rule_file):
            if not agent_name:
                agent_name = "inbound-agent"  # Valeur par défaut
            
            print(f"Configuration d'une règle de dispatch SIP pour l'agent: {agent_name}")
            
            # Configuration de base pour la règle de dispatch individuelle
            dispatch_rule = SIPDispatchRule(
                dispatch_rule_individual=SIPDispatchRuleIndividual(
                    room_prefix="call-"
                )
            )
            
            # Création de la requête avec l'agent comme métadonnées
            # (format adapté à la version plus récente de LiveKit)
            request = CreateSIPDispatchRuleRequest(
                name="Inbound Call Rule",
                rule=dispatch_rule,
                # Passer l'agent dans les métadonnées au lieu d'utiliser room_config
                metadata=json.dumps({"agent_name": agent_name})
            )
        else:
            # Chargement des données depuis le fichier
            print(f"Chargement des données depuis le fichier {rule_file}...")
            with open(rule_file, 'r') as f:
                rule_config = json.load(f)
            
            # Création de la règle selon la configuration du fichier
            dispatch_rule = SIPDispatchRule(
                dispatch_rule_individual=SIPDispatchRuleIndividual(
                    room_prefix=rule_config.get("rule", {}).get("dispatchRuleIndividual", {}).get("roomPrefix", "call-")
                )
            )
            
            # Création de la requête 
            request = CreateSIPDispatchRuleRequest(
                name=rule_config.get("name", "Inbound Call Rule"),
                rule=dispatch_rule,
                metadata=json.dumps({"agent_name": agent_name or "inbound-agent"})
            )
        
        # Envoi de la requête à LiveKit
        print("Envoi de la requête pour créer la règle de dispatch SIP...")
        response = await livekit_api.sip.create_sip_dispatch_rule(request)       
        print(f"Règle de dispatch SIP créée avec succès: ID = {rule_id}")
        
        
        # Mise à jour du fichier .env
        # [Code inchangé pour mettre à jour le fichier .env]
        
        return response.id
    except Exception as e:
        print(f"Erreur lors de la création de la règle de dispatch SIP: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        await livekit_api.aclose()
def main():
    parser = argparse.ArgumentParser(description='Créer une règle de dispatch SIP dans LiveKit')
    parser.add_argument('--file', '-f', help='Chemin vers le fichier JSON contenant la configuration de la règle')
    parser.add_argument('--agent', '-a', help='Nom de l\'agent à dispatcher (par défaut: inbound-agent)')
    args = parser.parse_args()
    
    asyncio.run(create_dispatch_rule(args.file, args.agent))

if __name__ == "__main__":
    main()
