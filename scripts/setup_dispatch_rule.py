import asyncio
import os
import json
import argparse
from dotenv import load_dotenv
from livekit import api
from livekit.protocol.sip import CreateSIPDispatchRuleRequest, SIPDispatchRule, SIPDispatchRuleIndividual, RoomConfiguration, AgentDispatch

# Chercher le fichier .env à la racine du projet
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
env_path = os.path.join(root_dir, ".env")
load_dotenv(env_path)

async def create_dispatch_rule(rule_file=None, agent_name=None):
    """
    Crée une règle de dispatch SIP dans LiveKit
    
    Args:
        rule_file: Chemin vers un fichier JSON contenant la configuration de la règle (optionnel)
        agent_name: Nom de l'agent à dispatcher (optionnel)
    
    Returns:
        L'ID de la règle créée
    """
    # Initialisation du client LiveKit
    print("Initialisation du client LiveKit API...")
    livekit_api = api.LiveKitAPI()
    
    try:
        # Déterminer la configuration de la règle
        if rule_file and os.path.exists(rule_file):
            # Chargement des données depuis le fichier
            print(f"Chargement des données depuis le fichier {rule_file}...")
            with open(rule_file, 'r') as f:
                rule_config = json.load(f)
        else:
            # Utiliser les valeurs par défaut ou de la ligne de commande
            if not agent_name:
                agent_name = "inbound-agent"  # Valeur par défaut
            
            print(f"Configuration d'une règle de dispatch SIP pour l'agent: {agent_name}")
            
            # Configuration par défaut: chaque appelant dans sa propre room
            rule_config = {
                "name": "Inbound Call Rule",
                "rule": {
                    "dispatchRuleIndividual": {
                        "roomPrefix": "call-"
                    }
                },
                "room_config": {
                    "agents": [
                        {
                            "agent_name": agent_name
                        }
                    ]
                }
            }
        
        # Création de la règle
        # Partie 1: Configuration de la règle de dispatch
        dispatch_rule = None
        if "dispatchRuleIndividual" in rule_config.get("rule", {}):
            # Règle individuelle: chaque appelant dans sa propre room
            individual_config = rule_config["rule"]["dispatchRuleIndividual"]
            dispatch_rule = SIPDispatchRule(
                dispatch_rule_individual=SIPDispatchRuleIndividual(
                    room_prefix=individual_config.get("roomPrefix", "call-")
                )
            )
        elif "dispatchRuleDirect" in rule_config.get("rule", {}):
            # Règle directe: tous les appelants dans une seule room
            from livekit.protocol.sip import SIPDispatchRuleDirect
            direct_config = rule_config["rule"]["dispatchRuleDirect"]
            dispatch_rule = SIPDispatchRule(
                dispatch_rule_direct=SIPDispatchRuleDirect(
                    room_name=direct_config.get("roomName", "shared-room"),
                    pin=direct_config.get("pin", "")
                )
            )
        else:
            # Par défaut, utiliser une règle individuelle
            dispatch_rule = SIPDispatchRule(
                dispatch_rule_individual=SIPDispatchRuleIndividual(
                    room_prefix="call-"
                )
            )
        
        # Partie 2: Configuration de la room
        room_config = None
        if "room_config" in rule_config and "agents" in rule_config["room_config"]:
            # Ajouter les agents à dispatcher
            agents = []
            for agent_config in rule_config["room_config"]["agents"]:
                agents.append(
                    AgentDispatch(
                        agent_name=agent_config.get("agent_name", agent_name),
                        metadata=agent_config.get("metadata", "")
                    )
                )
            
            room_config = RoomConfiguration(agents=agents)
        
        # Création de la requête
        request = CreateSIPDispatchRuleRequest(
            name=rule_config.get("name", "Inbound Call Rule"),
            rule=dispatch_rule,
            room_config=room_config
