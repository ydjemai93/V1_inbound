import asyncio
import os
import json
import argparse
from dotenv import load_dotenv
from livekit import api
from livekit.protocol.sip import CreateSIPInboundTrunkRequest, SIPInboundTrunkInfo

# Chercher le fichier .env à la racine du projet
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
env_path = os.path.join(root_dir, ".env")
load_dotenv(env_path)

async def create_inbound_trunk(trunk_data_file=None):
    """
    Crée un trunk SIP entrant dans LiveKit
    
    Args:
        trunk_data_file: Chemin vers un fichier JSON contenant les informations du trunk (optionnel)
    
    Returns:
        L'ID du trunk créé
    """
    # Initialisation du client LiveKit
    print("Initialisation du client LiveKit API...")
    livekit_api = api.LiveKitAPI()
    
    try:
        # Déterminer les données du trunk
        if trunk_data_file and os.path.exists(trunk_data_file):
            # Chargement des données depuis le fichier
            print(f"Chargement des données depuis le fichier {trunk_data_file}...")
            with open(trunk_data_file, 'r') as f:
                trunk_config = json.load(f)
            
            # Extraction des informations du trunk
            trunk_info = trunk_config.get('trunk', {})
        else:
            # Utiliser les valeurs par défaut ou de la ligne de commande
            phone_number = os.environ.get('TWILIO_PHONE_NUMBER')
            if not phone_number:
                phone_number = input("Entrez le numéro de téléphone pour les appels entrants (ex: +15105551234): ")
            
            print(f"Configuration du trunk SIP entrant pour le numéro: {phone_number}")
            
            trunk_info = {
                "name": "Inbound SIP Trunk",
                "numbers": [phone_number],
                # Activer les fonctionnalités de suppression de bruit Krisp
                "krisp_enabled": True
            }
        
        # Création de l'objet trunk
        trunk = SIPInboundTrunkInfo(
            name=trunk_info.get('name', 'Inbound SIP Trunk'),
            numbers=trunk_info.get('numbers', []),
            krisp_enabled=trunk_info.get('krisp_enabled', True)
        )
        
        # Création de la requête
        request = CreateSIPInboundTrunkRequest(trunk=trunk)
        
        # Envoi de la requête à LiveKit
        print("Envoi de la requête pour créer le trunk SIP entrant...")
        response = await livekit_api.sip.create_sip_inbound_trunk(request)
        print(f"Trunk SIP entrant créé avec succès: ID = {response.id}")
        
        # Ajout au fichier .env
        env_path = os.path.join(root_dir, ".env")
        try:
            with open(env_path, 'r') as env_file:
                env_content = env_file.read()
            
            if 'INBOUND_TRUNK_ID' in env_content:
                # Mise à jour de la valeur existante
                env_lines = env_content.split('\n')
                updated_lines = []
                for line in env_lines:
                    if line.startswith('INBOUND_TRUNK_ID='):
                        updated_lines.append(f'INBOUND_TRUNK_ID={response.id}')
                    else:
                        updated_lines.append(line)
                updated_env = '\n'.join(updated_lines)
            else:
                # Ajout de la nouvelle valeur
                updated_env = f"{env_content}\nINBOUND_TRUNK_ID={response.id}"
            
            with open(env_path, 'w') as env_file:
                env_file.write(updated_env)
            
            print(f"L'ID du trunk ({response.id}) a été enregistré dans le fichier .env")
        except Exception as e:
            print(f"Attention: Impossible de mettre à jour le fichier .env: {e}")
        
        return response.id
    except Exception as e:
        print(f"Erreur lors de la création du trunk SIP entrant: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        await livekit_api.aclose()

def main():
    parser = argparse.ArgumentParser(description='Créer un trunk SIP entrant dans LiveKit')
    parser.add_argument('--file', '-f', help='Chemin vers le fichier JSON contenant les informations du trunk')
    args = parser.parse_args()
    
    asyncio.run(create_inbound_trunk(args.file))

if __name__ == "__main__":
    main()
