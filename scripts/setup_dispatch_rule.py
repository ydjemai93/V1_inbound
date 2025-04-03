import asyncio
import argparse
import os
from dotenv import load_dotenv
from livekit import api
from livekit.protocol.sip import CreateSIPDispatchRuleRequest, SIPDispatchRule, SIPDispatchRuleIndividual

# Charger les variables d'environnement
load_dotenv()

async def create_dispatch_rule(room_prefix="call-", include_agent=True):
    """
    Crée une règle de dispatch SIP pour gérer les appels entrants
    
    Args:
        room_prefix: Préfixe pour les noms de room
        include_agent: Si True, inclut l'agent outbound-caller dans la configuration
    """
    # Initialisation du client LiveKit
    livekit_api = api.LiveKitAPI()
    
    try:
        print(f"Configuration de la règle de dispatch SIP avec le préfixe '{room_prefix}'...")
        
        # Configuration de l'agent si demandé
        room_config = None
        if include_agent:
            room_config = api.RoomConfiguration(
                agents=[
                    api.RoomAgentDispatch(
                        agent_name="outbound-caller"
                    )
                ]
            )
            print("L'agent 'outbound-caller' sera automatiquement attaché à chaque appel entrant")
        
        # Création de la règle de dispatch avec les objets appropriés du SDK
        request = CreateSIPDispatchRuleRequest(
            rule=SIPDispatchRule(
                dispatch_rule_individual=SIPDispatchRuleIndividual(
                    room_prefix=room_prefix
                )
            ),
            room_config=room_config
        )
        
        # Envoi de la requête à LiveKit
        print("Envoi de la requête de création de règle...")
        response = await livekit_api.sip.create_sip_dispatch_rule(request)
        
        print(f"Règle de dispatch SIP créée avec succès!")
        print(f"ID de la règle: {response.id}")
        
        return response.id
        
    except Exception as e:
        print(f"Erreur lors de la création de la règle de dispatch SIP: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        await livekit_api.aclose()

def main():
    parser = argparse.ArgumentParser(description='Créer une règle de dispatch SIP dans LiveKit')
    parser.add_argument('--prefix', '-p', default="call-", help='Préfixe pour les noms de room (défaut: call-)')
    parser.add_argument('--no-agent', action='store_true', help="Ne pas inclure l'agent outbound-caller")
    args = parser.parse_args()
    
    rule_id = asyncio.run(create_dispatch_rule(args.prefix, not args.no_agent))
    
    if rule_id:
        print("\nConfiguration réussie! Vous pouvez maintenant recevoir des appels SIP entrants.")
        print("Les appels seront dirigés vers des rooms avec le préfixe spécifié.")
    else:
        print("\nLa configuration a échoué. Veuillez vérifier les messages d'erreur ci-dessus.")

if __name__ == "__main__":
    main()
