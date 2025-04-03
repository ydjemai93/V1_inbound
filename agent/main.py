import asyncio
import os
import logging
import json
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.llm import ChatContext, ChatMessage
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.agents import AutoSubscribe
from livekit.plugins import deepgram, silero, openai, cartesia
from dotenv import load_dotenv

from call_actions import CallActions
from inbound_handler import InboundCallHandler

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('agent.log')
    ]
)
logger = logging.getLogger(__name__)

# Chargement des variables d'environnement
load_dotenv()

def prewarm(proc):
    """Fonction de préchauffage pour charger les modèles IA à l'avance"""
    # Préchargement du modèle VAD
    proc.userdata["vad"] = silero.VAD.load()

async def entrypoint(ctx: JobContext):
    """Point d'entrée principal de l'agent pour les appels entrants"""
    logger.info(f"DEBUT DE L'ENTRYPOINT POUR L'APPEL ENTRANT")
    logger.info(f"Métadonnées du job: {ctx.job.metadata}")
    logger.info(f"Room: {ctx.room.name}")
    
    # Initialisation du contexte de conversation
    initial_ctx = ChatContext().append(
        role="system",
        content=(
            "Vous êtes un assistant téléphonique professionnel pour une entreprise. "
            "Vous parlez de manière naturelle et concise. "
            "Vous êtes poli et serviable. "
            "Si un client appelle, présentez-vous en disant 'Bonjour, merci d'avoir appelé. "
            "Je suis l'assistant IA de l'entreprise. Comment puis-je vous aider aujourd'hui?'. "
            "Évitez d'utiliser des formulations robotiques. "
            "Si le client pose une question complexe nécessitant l'intervention d'un humain, "
            "proposez de transférer l'appel à un agent humain."
        ),
    )

    try:
        # Connexion à la room LiveKit
        await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
        
        # Initialisation du gestionnaire d'appels entrants
        inbound_handler = InboundCallHandler(ctx.api, ctx.room)
        
        # Attendre qu'un participant SIP rejoigne
        logger.info("En attente d'un participant SIP entrant...")
        
        # Fonction pour trouver un participant SIP parmi les participants existants
        def find_sip_participant():
            for participant in ctx.room.remote_participants.values():
                if "sip." in str(participant.attributes):
                    return participant
            return None
        
        # Vérifier s'il y a déjà un participant SIP dans la room
        sip_participant = find_sip_participant()
        
        if not sip_participant:
            # Attendre un maximum de 30 secondes pour qu'un participant SIP rejoigne
            timeout = 30
            start_time = asyncio.get_event_loop().time()
            
            while asyncio.get_event_loop().time() - start_time < timeout:
                sip_participant = find_sip_participant()
                if sip_participant:
                    break
                await asyncio.sleep(0.5)
            
            if not sip_participant:
                logger.warning("Aucun participant SIP n'a rejoint après le délai d'attente")
                ctx.shutdown(reason="Aucun participant SIP")
                return
        
        logger.info(f"Participant SIP détecté: {sip_participant.identity}")
        
        # Initialisation des actions d'appel
        call_actions = CallActions(api=ctx.api, participant=sip_participant, room=ctx.room)
        
        # Initialisation de l'agent vocal avec les plugins spécifiés
        agent = VoicePipelineAgent(
            vad=ctx.proc.userdata["vad"],
            stt=deepgram.STT(model="nova-2-general"),  # Utilisation de Deepgram
            llm=openai.LLM(
                model="gpt-4o-mini",               # Utilisation d'OpenAI GPT-4o mini
                fnc_ctx=call_actions              # Actions d'appel disponibles pour le LLM
            ),
            tts=cartesia.TTS(model="sonic-2"),     # Utilisation de Cartesia
            chat_ctx=initial_ctx,
            allow_interruptions=True,
        )
        
        # Démarrage de l'agent avec le participant SIP
        agent.start(ctx.room, sip_participant)
        
        # Message de bienvenue
        welcome_message = (
            "Bonjour, merci d'avoir appelé. Je suis l'assistant IA de l'entreprise. "
            "Comment puis-je vous aider aujourd'hui?"
        )
        await agent.say(welcome_message, allow_interruptions=True)
        
        # Attendre que l'appel soit terminé (le participant SIP quitte la room)
        while sip_participant.identity in ctx.room.remote_participants:
            await asyncio.sleep(1)
        
        logger.info(f"Le participant SIP {sip_participant.identity} a quitté la room, fin de l'appel")
        
    except Exception as e:
        logger.exception(f"Erreur dans l'entrypoint: {e}")
        ctx.shutdown(reason=f"Erreur: {e}")

async def request_handler(req):
    """
    Gère les requêtes de dispatch d'agent
    - Vérifie si l'agent doit accepter cette requête
    - Configurable selon des critères spécifiques
    """
    logger.info(f"Nouvelle requête reçue: {req}")
    
    # Accepter toutes les requêtes pour cet agent
    await req.accept(
        name="Inbound Assistant",
        identity="inbound-agent"
    )

if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            request_fnc=request_handler,
            prewarm_fnc=prewarm,
            # Nom de l'agent pour le dispatch explicite
            agent_name="inbound-agent",
        )
    )
