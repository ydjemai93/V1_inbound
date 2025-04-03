import asyncio
import os
import logging
import argparse
from dotenv import load_dotenv
from livekit import api
from livekit.protocol.sip import CreateSIPParticipantRequest

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Chargement des variables d'environnement
load_dotenv()

async def simulate_inbound_call(phone_number=None):
    """
    Simule un appel entrant en créant un participant SIP entrant
    
    Args:
        phone_number: Numéro de téléphone simulant l'appel (optionnel)
    """
    # Initialisation du client LiveKit
    livekit_api = api.LiveKitAPI()
    
    try:
        # Utiliser le numéro de téléphone Twilio par défaut
        if not phone_number:
            phone_number = os.environ.get("TWILIO_PHONE_NUMBER", "+15105551234")
        
        # Formater le numéro de téléphone
        if not phone_number.startswith("+"):
            phone_number = f"+{phone_number}"
        
        # Supprimer les caractères spéciaux comme tirets ou espaces
        phone_number = ''.join(c for c in phone_number if c.isdigit() or c == '+')
        
        logger.info(f"====== SIMULATION D'APPEL ENTRANT ======")
        logger.info(f"Numéro d'appel simulé: {phone_number}")
        
        # Créer une room pour la simulation
        import secrets
        room_name = f"test-inbound-{secrets.token_hex(4)}"
        
        logger.info(f"Room pour le test: {room_name}")
        
        # Vérifier si le trunk entrant est configuré
        inbound_trunk_id = os.environ.get("INBOUND_TRUNK_ID")
        if not inbound_trunk_id:
            logger.error("Erreur: INBOUND_TRUNK_ID n'est pas configuré dans les variables d'environnement")
            return
        
        # Créer le participant SIP simulant un appel entrant
        request = CreateSIPParticipantRequest(
            room_name=room_name,
            sip_trunk_id=inbound_trunk_id,
            # Pour un appel entrant simulé, nous définissons les attributs SIP
            # qui seraient normalement définis par le fournisseur SIP
            participant_identity=f"sim_caller_{phone_number}",
            participant_name=f"Simulated Inbound Call {phone_number}",
            participant_metadata=f"Simulated inbound call from {phone_number}",
            attributes={
                "sip.from": phone_number,
                "sip.to": os.environ.get("TWILIO_PHONE_NUMBER", "+15105551234"),
                "sip.callStatus": "active"
            }
        )
        
        # Envoyer la requête
        logger.info(f"Envoi de la requête SIP pour simuler un appel entrant...")
        response = await livekit_api.sip.create_sip_participant(request)
        logger.info(f"Réponse SIP reçue: {response}")
        
        # Surveiller la room pendant un certain temps
        logger.info("Surveillance de la room pour 60 secondes...")
        for i in range(12):  # 60 secondes au total
            await asyncio.sleep(5)
            room_info = await livekit_api.room.list_rooms(api.ListRoomsRequest(names=[room_name]))
            if not room_info.rooms:
                logger.info("La room n'existe plus, l'appel s'est terminé")
                break
                
            room = room_info.rooms[0]
            logger.info(f"Statut de la room après {(i+1)*5} secondes: {room.num_participants} participants")
        
        logger.info("Fin de la simulation d'appel entrant")
        
    except Exception as e:
        logger.error(f"Erreur lors de la simulation d'appel entrant: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await livekit_api.aclose()

def main():
    parser = argparse.ArgumentParser(description='Simuler un appel entrant via SIP')
    parser.add_argument('--phone', '-p', help='Numéro de téléphone simulant l\'appel')
    args = parser.parse_args()
    
    asyncio.run(simulate_inbound_call(args.phone))

if __name__ == "__main__":
    main()
