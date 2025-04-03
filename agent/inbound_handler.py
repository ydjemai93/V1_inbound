import asyncio
import logging
from livekit import rtc
from livekit.api import RoomParticipantIdentity

logger = logging.getLogger(__name__)

class InboundCallHandler:
    """
    Classe gérant les appels entrants via SIP
    """
    
    def __init__(self, api, room):
        """
        Initialisation du gestionnaire d'appels entrants
        
        Args:
            api: Instance API LiveKit
            room: Room LiveKit actuelle
        """
        self.api = api
        self.room = room
        self.participants = {}
        self.setup_room_listeners()
    
    def setup_room_listeners(self):
        """Configure les écouteurs d'événements de la room"""
        @self.room.on("participant_connected")
        def on_participant_connected(participant, *_):
            logger.info(f"Participant connecté: {participant.identity}")
            # Enregistrer le participant
            self.participants[participant.identity] = participant
            # Vérifier si c'est un participant SIP
            if self.is_sip_participant(participant):
                logger.info(f"Participant SIP détecté: {participant.identity}")
                self.handle_sip_participant(participant)
    
    def is_sip_participant(self, participant):
        """
        Détermine si un participant est un appelant SIP
        
        Args:
            participant: Participant à vérifier
            
        Returns:
            bool: True si le participant est un appelant SIP
        """
        # On peut identifier les participants SIP par leurs attributs
        return "sip.callStatus" in participant.attributes or "sip.from" in participant.attributes
    
    def handle_sip_participant(self, participant):
        """
        Gère un nouvel appelant SIP entrant
        
        Args:
            participant: Participant SIP à gérer
        """
        logger.info(f"Traitement de l'appelant SIP: {participant.identity}")
        # Démarrer la surveillance de l'état de l'appel
        asyncio.create_task(self.monitor_call_status(participant))
    
    async def monitor_call_status(self, participant, check_interval=0.5):
        """
        Surveille l'état d'un appel entrant
        
        Args:
            participant: Participant SIP à surveiller
            check_interval: Intervalle entre les vérifications en secondes
        """
        try:
            logger.info(f"Début de la surveillance de l'appel pour {participant.identity}")
            
            # Obtenir et journaliser les métadonnées de l'appel
            caller_number = participant.attributes.get("sip.from", "Inconnu")
            called_number = participant.attributes.get("sip.to", "Inconnu")
            
            logger.info(f"Détails de l'appel entrant:")
            logger.info(f"  De: {caller_number}")
            logger.info(f"  Vers: {called_number}")
            
            # Journaliser tous les attributs disponibles
            logger.info("Attributs du participant SIP:")
            for key, value in participant.attributes.items():
                logger.info(f"  {key}: {value}")
            
            # Surveiller l'état de l'appel
            while True:
                # Vérifier si le participant est toujours connecté
                if participant.identity not in self.room.remote_participants:
                    logger.info(f"Le participant {participant.identity} a quitté la room")
                    return
                
                # Récupérer le participant à jour
                participant = self.room.remote_participants.get(participant.identity)
                
                # Vérifier l'état de l'appel
                call_status = participant.attributes.get("sip.callStatus")
                
                if call_status == "hangup":
                    logger.info(f"L'appel avec {participant.identity} a été raccroché")
                    return
                
                await asyncio.sleep(check_interval)
        
        except Exception as e:
            logger.error(f"Erreur lors de la surveillance de l'appel: {e}")
            logger.exception("Détails de l'erreur:")
    
    async def end_call(self, participant):
        """
        Termine un appel entrant
        
        Args:
            participant: Participant SIP à déconnecter
        """
        try:
            logger.info(f"Fin de l'appel pour {participant.identity}")
            await self.api.room.remove_participant(
                RoomParticipantIdentity(
                    room=self.room.name,
                    identity=participant.identity,
                )
            )
            logger.info(f"Appel avec {participant.identity} terminé avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de la terminaison de l'appel: {e}")
            logger.exception("Détails de l'erreur:")
