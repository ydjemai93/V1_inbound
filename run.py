import subprocess
import sys
import os
import time
import signal
import logging
from dotenv import load_dotenv

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('run.log')
    ]
)
logger = logging.getLogger(__name__)

# Charger les variables d'environnement
load_dotenv()

# Variables globales pour les processus
agent_process = None
api_process = None

def start_agent():
    """Démarrer l'agent en mode développement"""
    global agent_process
    try:
        logger.info("Démarrage de l'agent...")
        agent_process = subprocess.Popen(
            [sys.executable, "-m", "agent.main", "dev"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        logger.info(f"Agent démarré avec PID: {agent_process.pid}")
        
        # Vérifier rapidement si l'agent s'est arrêté immédiatement
        time.sleep(1)
        if agent_process.poll() is not None:
            logger.error(f"L'agent s'est arrêté avec le code: {agent_process.returncode}")
            output, _ = agent_process.communicate()
            logger.error(f"Output de l'agent: {output}")
            return False
        
        return True
    except Exception as e:
        logger.error(f"Erreur lors du démarrage de l'agent: {e}")
        return False

def start_api():
    """Démarrer l'API Flask"""
    global api_process
    try:
        logger.info("Démarrage de l'API...")
        api_process = subprocess.Popen(
            [sys.executable, "-m", "api.app"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        logger.info(f"API démarrée avec PID: {api_process.pid}")
        
        # Vérifier rapidement si l'API s'est arrêtée immédiatement
        time.sleep(1)
        if api_process.poll() is not None:
            logger.error(f"L'API s'est arrêtée avec le code: {api_process.returncode}")
            output, _ = api_process.communicate()
            logger.error(f"Output de l'API: {output}")
            return False
        
        return True
    except Exception as e:
        logger.error(f"Erreur lors du démarrage de l'API: {e}")
        return False

def monitor_logs():
    """Suivre et afficher les logs des processus"""
    try:
        # Suivre les logs de l'agent
        if agent_process and agent_process.stdout:
            for line in agent_process.stdout:
                print(f"[AGENT] {line.strip()}")
        
        # Suivre les logs de l'API
        if api_process and api_process.stdout:
            for line in api_process.stdout:
                print(f"[API] {line.strip()}")
    except KeyboardInterrupt:
        logger.info("Surveillance des logs interrompue par l'utilisateur")
    except Exception as e:
        logger.error(f"Erreur lors de la surveillance des logs: {e}")

def cleanup(signum=None, frame=None):
    """Nettoyer les processus en cours d'exécution"""
    logger.info("Nettoyage des processus...")
    
    # Arrêter l'agent
    if agent_process:
        try:
            logger.info(f"Arrêt de l'agent (PID: {agent_process.pid})...")
            agent_process.terminate()
            agent_process.wait(timeout=5)
            logger.info("Agent arrêté")
        except subprocess.TimeoutExpired:
            logger.warning("L'agent ne répond pas, force-killing...")
            agent_process.kill()
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt de l'agent: {e}")
    
    # Arrêter l'API
    if api_process:
        try:
            logger.info(f"Arrêt de l'API (PID: {api_process.pid})...")
            api_process.terminate()
            api_process.wait(timeout=5)
            logger.info("API arrêtée")
        except subprocess.TimeoutExpired:
            logger.warning("L'API ne répond pas, force-killing...")
            api_process.kill()
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt de l'API: {e}")
    
    logger.info("Nettoyage terminé")
    
    # Quitter le programme si appelé comme gestionnaire de signal
    if signum is not None:
        sys.exit(0)

def main():
    """Fonction principale"""
    # Enregistrer les gestionnaires de signal pour un nettoyage propre
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    logger.info("Démarrage des services...")
    
    # Démarrer l'agent
    if not start_agent():
        logger.error("Impossible de démarrer l'agent, abandon")
        cleanup()
        return 1
    
    # Démarrer l'API
    if not start_api():
        logger.error("Impossible de démarrer l'API, abandon")
        cleanup()
        return 1
    
    logger.info("Tous les services sont démarrés")
    
    try:
        # Surveiller les logs
        monitor_logs()
    except KeyboardInterrupt:
        logger.info("Interruption par l'utilisateur")
    finally:
        # Nettoyer avant de quitter
        cleanup()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
