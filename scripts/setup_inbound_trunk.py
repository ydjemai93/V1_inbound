import asyncio
import os
import json
import argparse
from dotenv import load_dotenv
from livekit import api
from livekit.protocol.sip import CreateSIPInboundTrunkRequest, SIPInboundTrunkInfo

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
env_path = os.path.join(root_dir, ".env")
load_dotenv(env_path)

async def create_inbound_trunk(trunk_data_file=None):
    print("Initialisation du client LiveKit API...")
    livekit_api = api.LiveKitAPI()

    try:
        if trunk_data_file and os.path.exists(trunk_data_file):
            with open(trunk_data_file, 'r') as f:
                trunk_config = json.load(f)
            trunk_info = trunk_config.get('trunk', {})
        else:
            phone_number = os.environ.get('TWILIO_PHONE_NUMBER')
            if not phone_number:
                phone_number = input("Entrez le numéro de téléphone pour les appels entrants (ex: +15105551234): ")
            trunk_info = {
                "name": "Inbound SIP Trunk",
                "numbers": [phone_number],
                "krisp_enabled": True
            }

        trunk = SIPInboundTrunkInfo(
            name=trunk_info.get('name', 'Inbound SIP Trunk'),
            numbers=trunk_info.get('numbers', []),
            krisp_enabled=trunk_info.get('krisp_enabled', True)
        )

        request = CreateSIPInboundTrunkRequest(trunk=trunk)
        response = await livekit_api.sip.create_sip_inbound_trunk(request)

        print("Réponse complète reçue de LiveKit:", response)

        # Adaptation à la structure réelle de la réponse
        trunk_id = response.trunk.id if hasattr(response, 'trunk') else getattr(response, 'id', None)
        if not trunk_id:
            raise ValueError("La réponse de LiveKit ne contient pas l'ID attendu du trunk.")

        print(f"Trunk SIP entrant créé avec succès: ID = {trunk_id}")

        env_path = os.path.join(root_dir, ".env")
        try:
            with open(env_path, 'r') as env_file:
                env_content = env_file.read()

            if 'INBOUND_TRUNK_ID' in env_content:
                env_lines = env_content.split('\n')
                updated_lines = [f'INBOUND_TRUNK_ID={trunk_id}' if line.startswith('INBOUND_TRUNK_ID=') else line for line in env_lines]
                updated_env = '\n'.join(updated_lines)
            else:
                updated_env = f"{env_content}\nINBOUND_TRUNK_ID={trunk_id}"

            with open(env_path, 'w') as env_file:
                env_file.write(updated_env)

            print(f"L'ID du trunk ({trunk_id}) a été enregistré dans le fichier .env")
        except Exception as e:
            print(f"Attention: Impossible de mettre à jour le fichier .env: {e}")

        return trunk_id
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
