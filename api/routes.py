import os
import json
import logging
import subprocess
import traceback
import asyncio
import secrets
from flask import request, jsonify

# Configuration du logger
logger = logging.getLogger(__name__)

def register_routes(app):
    @app.route("/health", methods=["GET"])
    def health_check():
        """Endpoint de vérification de santé pour Railway"""
        return jsonify({"status": "ok", "message": "L'API d'agent téléphonique est opérationnelle"})
    
    @app.route("/api/twilio/test", methods=["GET"])
    def test_twilio_env():
        """Endpoint pour tester les variables d'environnement Twilio"""
        account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        auth_token = os.environ.get("TWILIO_AUTH_TOKEN") 
        phone_number = os.environ.get("TWILIO_PHONE_NUMBER")
        
        return jsonify({
            "variables_present": {
                "TWILIO_ACCOUNT_SID": bool(account_sid),
                "TWILIO_AUTH_TOKEN": bool(auth_token),
                "TWILIO_PHONE_NUMBER": bool(phone_number)
            },
            "account_sid_prefix": account_sid[:4] + "..." if account_sid else None,
            "all_variables_present": all([account_sid, auth_token, phone_number])
        })
    
    @app.route("/api/livekit/test", methods=["GET"])
    def test_livekit():
        """Endpoint pour tester la connexion à LiveKit"""
        try:
            from livekit import api
            
            async def test_livekit_connection():
                livekit_api = None
                try:
                    livekit_api = api.LiveKitAPI()
                    # Tester la connexion en listant les rooms
                    response = await livekit_api.room.list_rooms(api.ListRoomsRequest())
                    return {
                        "success": True,
                        "connection": "OK",
                        "rooms_count": len(response.rooms)
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "error": str(e)
                    }
                finally:
                    if livekit_api:
                        await livekit_api.aclose()
            
            result = asyncio.run(test_livekit_connection())
            return jsonify(result)
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }), 500
    
    @app.route("/api/inbound/trunk/setup", methods=["POST"])
    def setup_inbound_trunk():
        """Endpoint pour configurer un trunk SIP entrant"""
        try:
            data = request.json or {}
            phone_number = data.get("phone_number", os.environ.get("TWILIO_PHONE_NUMBER"))
            
            if not phone_number:
                return jsonify({
                    "success": False,
                    "error": "Numéro de téléphone manquant"
                }), 400
            
            # Créer un fichier temporaire de configuration
            trunk_config = {
                "trunk": {
                    "name": "Inbound SIP Trunk",
                    "numbers": [phone_number],
                    "krisp_enabled": True
                }
            }
            
            temp_file = "temp_inbound_trunk.json"
            with open(temp_file, "w") as f:
                json.dump(trunk_config, f)
            
            # Importer et exécuter le script de configuration directement
            from scripts.setup_inbound_trunk import create_inbound_trunk
            
            trunk_id = asyncio.run(create_inbound_trunk(temp_file))
            
            # Supprimer le fichier temporaire
            try:
                os.remove(temp_file)
            except:
                pass
            
            return jsonify({
                "success": True,
                "trunk_id": trunk_id,
                "phone_number": phone_number,
                "message": "Trunk SIP entrant configuré avec succès"
            })
            
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }), 500
    
    @app.route("/api/inbound/dispatch/setup", methods=["POST"])
    def setup_dispatch_rule():
        """Endpoint pour configurer une règle de dispatch pour les appels entrants"""
        try:
            data = request.json or {}
            agent_name = data.get("agent_name", "inbound-agent")
            room_prefix = data.get("room_prefix", "call-")
            
            # Créer un fichier temporaire de configuration
            rule_config = {
                "name": "Inbound Call Rule",
                "rule": {
                    "dispatchRuleIndividual": {
                        "roomPrefix": room_prefix
                    }
                },
                "agent_name": agent_name  # Simplifié pour s'adapter à la nouvelle structure
            }
            
            temp_file = "temp_dispatch_rule.json"
            with open(temp_file, "w") as f:
                json.dump(rule_config, f)
            
            # Importer et exécuter le script de configuration directement
            from scripts.setup_dispatch_rule import create_dispatch_rule
            
            rule_id = asyncio.run(create_dispatch_rule(temp_file))
            
            # Supprimer le fichier temporaire
            try:
                os.remove(temp_file)
            except:
                pass
            
            return jsonify({
                "success": True,
                "rule_id": rule_id,
                "agent_name": agent_name,
                "room_prefix": room_prefix,
                "message": "Règle de dispatch configurée avec succès"
            })
            
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }), 500
    
    @app.route("/api/agent/status", methods=["GET"])
    def check_agent_status():
        """Endpoint pour vérifier si l'agent est en cours d'exécution et disponible"""
        try:
            from livekit import api
            
            async def check_agents():
                livekit_api = None
                try:
                    livekit_api = api.LiveKitAPI()
                    
                    # Nous ne pouvons pas récupérer les agents avec list_agent_info
                    # À la place, nous allons essayer de créer un dispatch pour voir si l'agent est disponible
                    
                    # Création d'un dispatch temporaire pour tester si l'agent est disponible
                    try:
                        # Nom unique pour éviter des conflits
                        test_room = f"test-agent-{secrets.token_hex(4)}"
                        test_dispatch = await livekit_api.agent_dispatch.create_dispatch(
                            api.CreateAgentDispatchRequest(
                                agent_name="inbound-agent",
                                room=test_room,
                                metadata=json.dumps({"test": True})
                            )
                        )
                        
                        # Si on arrive ici, le dispatch a été créé, donc l'agent est disponible
                        # Suppression de la room de test
                        await livekit_api.room.delete_room(api.DeleteRoomRequest(room=test_room))
                        
                        return {
                            "success": True,
                            "agents": [
                                {
                                    "name": "inbound-agent",
                                    "status": "active",
                                    "capacity": 1.0
                                }
                            ],
                            "inbound_agent_available": True
                        }
                        
                    except Exception as e:
                        # Si une erreur se produit, l'agent n'est probablement pas disponible
                        logger.error(f"Erreur lors du test de l'agent: {e}")
                        return {
                            "success": True,
                            "agents": [],
                            "inbound_agent_available": False
                        }
                    
                except Exception as e:
                    return {
                        "success": False,
                        "error": str(e),
                        "traceback": traceback.format_exc()
                    }
                finally:
                    if livekit_api:
                        await livekit_api.aclose()
            
            result = asyncio.run(check_agents())
            return jsonify(result)
        
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }), 500
    
    @app.route("/api/inbound/status", methods=["GET"])
    def check_inbound_setup():
        """Endpoint pour vérifier l'état de la configuration des appels entrants"""
        try:
            from livekit import api
            
            async def check_inbound_configuration():
                livekit_api = None
                try:
                    livekit_api = api.LiveKitAPI()
                    
                    # Vérifier le trunk entrant
                    inbound_trunk_id = os.environ.get("INBOUND_TRUNK_ID")
                    inbound_trunk = None
                    
                    if inbound_trunk_id:
                        try:
                            inbound_trunks = await livekit_api.sip.list_sip_inbound_trunk(
                                api.ListSIPInboundTrunkRequest(ids=[inbound_trunk_id])
                            )
                            if inbound_trunks.trunks:
                                inbound_trunk = inbound_trunks.trunks[0]
                        except:
                            pass
                    
                    # Vérifier la règle de dispatch
                    dispatch_rule_id = os.environ.get("DISPATCH_RULE_ID")
                    dispatch_rule = None
                    
                    if dispatch_rule_id:
                        try:
                            dispatch_rules = await livekit_api.sip.list_sip_dispatch_rule(
                                api.ListSIPDispatchRuleRequest(ids=[dispatch_rule_id])
                            )
                            if dispatch_rules.rules:
                                dispatch_rule = dispatch_rules.rules[0]
                        except:
                            pass
                    
                    # Vérifier l'agent
                    agent_available = False
                    
                    try:
                        # Nom unique pour éviter des conflits
                        test_room = f"test-agent-{secrets.token_hex(4)}"
                        test_dispatch = await livekit_api.agent_dispatch.create_dispatch(
                            api.CreateAgentDispatchRequest(
                                agent_name="inbound-agent",
                                room=test_room,
                                metadata=json.dumps({"test": True})
                            )
                        )
                        
                        # Si on arrive ici, le dispatch a été créé, donc l'agent est disponible
                        # Suppression de la room de test
                        await livekit_api.room.delete_room(api.DeleteRoomRequest(room=test_room))
                        
                        agent_available = True
                    except:
                        pass
                    
                    return {
                        "success": True,
                        "inbound_trunk": {
                            "configured": inbound_trunk is not None,
                            "id": inbound_trunk_id,
                            "numbers": inbound_trunk.numbers if inbound_trunk else None
                        },
                        "dispatch_rule": {
                            "configured": dispatch_rule is not None,
                            "id": dispatch_rule_id,
                            "name": dispatch_rule.name if dispatch_rule else None
                        },
                        "agent": {
                            "available": agent_available,
                            "name": "inbound-agent"
                        },
                        "ready_for_calls": all([
                            inbound_trunk is not None,
                            dispatch_rule is not None,
                            agent_available
                        ])
                    }
                    
                except Exception as e:
                    return {
                        "success": False,
                        "error": str(e),
                        "traceback": traceback.format_exc()
                    }
                finally:
                    if livekit_api:
                        await livekit_api.aclose()
            
            result = asyncio.run(check_inbound_configuration())
            return jsonify(result)
        
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }), 500

    
    @app.route("/api/inbound/direct-setup", methods=["POST"])
    def direct_setup():
        """Configuration directe sans passer par les scripts complexes"""
        try:
            from livekit import api
            
            async def setup_directly():
                data = request.json or {}
                agent_name = data.get("agent_name", "inbound-agent")
                room_prefix = data.get("room_prefix", "call-")
                
                livekit_api = api.LiveKitAPI()
                try:
                    # Utilisation de l'API de base sans dépendre de la structure exacte
                    # Envoyer directement la requête JSON
                    request_data = {
                        "name": "Inbound Call Rule", 
                        "rule": {
                            "dispatchRuleIndividual": {
                                "roomPrefix": room_prefix
                            }
                        },
                        "metadata": json.dumps({"agent_name": agent_name})
                    }
                    
                    # Utiliser l'API HTTP brute si nécessaire
                    response = await livekit_api.sip.create_sip_dispatch_rule(
                        api.CreateSIPDispatchRuleRequest(**request_data)
                    )
                    
                    # Extraire l'ID de façon sécurisée
                    response_dict = response.__dict__ if hasattr(response, "__dict__") else {}
                    rule_id = response_dict.get("id", str(response))
                    
                    # Mettre à jour les variables d'environnement
                    os.environ["DISPATCH_RULE_ID"] = rule_id
                    
                    return {
                        "success": True,
                        "rule_id": rule_id,
                        "agent_name": agent_name
                    }
                except Exception as e:
                    return {
                        "success": False, 
                        "error": str(e),
                        "traceback": traceback.format_exc()
                    }
                finally:
                    await livekit_api.aclose()
            
            result = asyncio.run(setup_directly())
            return jsonify(result)
        
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }), 500
    @app.route("/api/twilio/twiml", methods=["GET"])
    def get_twiml():
        """Endpoint pour générer un TwiML pour les appels entrants"""
        try:
            # Récupérer l'hôte SIP de LiveKit
            sip_host = os.environ.get("LIVEKIT_SIP_HOST")
            if not sip_host:
                # Extraire de l'URL LiveKit
                livekit_url = os.environ.get("LIVEKIT_URL")
                if livekit_url:
                    # Format typique: wss://project-id.livekit.cloud
                    # On transforme en: project-id.sip.livekit.cloud
                    livekit_url = livekit_url.replace("wss://", "").replace("ws://", "")
                    if "." in livekit_url:
                        project_id = livekit_url.split(".")[0]
                        sip_host = f"{project_id}.sip.livekit.cloud"
            
            # Obtenir le paramètres d'authentification
            sip_username = request.args.get("username", "livekit_user")
            sip_password = request.args.get("password", "s3cur3p@ssw0rd")
            
            # Obtenir le numéro de téléphone
            phone_number = os.environ.get("TWILIO_PHONE_NUMBER", "your_phone_number")
            
            # Générer le TwiML
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Dial>
    <Sip username="{sip_username}" password="{sip_password}">
      sip:{phone_number}@{sip_host};transport=tcp
    </Sip>
  </Dial>
</Response>"""
            
            return jsonify({
                "success": True,
                "twiml": twiml,
                "sip_host": sip_host,
                "phone_number": phone_number
            })
            
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }), 500
    
    @app.route("/api/twilio/setup", methods=["POST"])
    def setup_twilio():
        """Endpoint pour configurer Twilio avec TwiML Bin"""
        try:
            # Nous ne pouvons pas configurer Twilio programmatiquement via l'API de Railway
            # mais nous pouvons fournir des instructions détaillées
            
            # Générer le TwiML
            sip_host = os.environ.get("LIVEKIT_SIP_HOST", "your-project-id.sip.livekit.cloud")
            phone_number = os.environ.get("TWILIO_PHONE_NUMBER", "your_phone_number")
            
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Dial>
    <Sip username="livekit_user" password="s3cur3p@ssw0rd">
      sip:{phone_number}@{sip_host};transport=tcp
    </Sip>
  </Dial>
</Response>"""
            
            # Instructions pour configurer Twilio
            instructions = [
                "1. Connectez-vous à votre compte Twilio",
                "2. Allez dans TwiML Bins et créez un nouveau bin",
                f"3. Collez le TwiML suivant: \n{twiml}",
                "4. Enregistrez le TwiML Bin",
                "5. Allez dans Phone Numbers et sélectionnez votre numéro",
                "6. Dans 'Voice & Fax', configurez 'A CALL COMES IN' pour utiliser le TwiML Bin que vous venez de créer",
                "7. Enregistrez les modifications"
            ]
            
            return jsonify({
                "success": True,
                "twiml": twiml,
                "instructions": instructions,
                "sip_host": sip_host,
                "phone_number": phone_number
            })
            
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }), 500

    # Endpoint TwiML directement accessible pour Twilio
    @app.route("/twiml", methods=["GET", "POST"])
    def twiml_endpoint():
        """Endpoint TwiML pour configurer Twilio"""
        try:
            # Récupérer l'hôte SIP de LiveKit
            sip_host = os.environ.get("LIVEKIT_SIP_HOST")
            if not sip_host:
                # Extraire de l'URL LiveKit
                livekit_url = os.environ.get("LIVEKIT_URL")
                if livekit_url:
                    # Format typique: wss://project-id.livekit.cloud
                    # On transforme en: project-id.sip.livekit.cloud
                    livekit_url = livekit_url.replace("wss://", "").replace("ws://", "")
                    if "." in livekit_url:
                        project_id = livekit_url.split(".")[0]
                        sip_host = f"{project_id}.sip.livekit.cloud"
            
            # Obtenir le numéro de téléphone
            phone_number = os.environ.get("TWILIO_PHONE_NUMBER", "your_phone_number")
            
            # Générer le TwiML
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Dial>
    <Sip username="livekit_user" password="s3cur3p@ssw0rd">
      sip:{phone_number}@{sip_host};transport=tcp
    </Sip>
  </Dial>
</Response>"""
            
            # Renvoyer directement le XML
            return twiml, 200, {'Content-Type': 'text/xml'}
            
        except Exception as e:
            logger.error(f"Erreur dans l'endpoint TwiML: {e}")
            # En cas d'erreur, renvoyer un TwiML d'erreur
            return """<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say>Sorry, an error occurred with the voice assistant service. Please try again later.</Say>
</Response>""", 200, {'Content-Type': 'text/xml'}
