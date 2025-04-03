# Agent Téléphonique IA pour Appels Entrants

Ce projet implémente un agent téléphonique IA capable de répondre aux appels entrants via Twilio et LiveKit. L'agent utilise Deepgram pour la reconnaissance vocale (STT), OpenAI GPT-4o Mini pour le traitement du langage naturel (LLM), et Cartesia pour la synthèse vocale (TTS).

## Architecture

Le système est composé des éléments suivants:

1. **API REST** - Point d'entrée pour la configuration et les tests
2. **Agent LiveKit** - Traitement des conversations téléphoniques
3. **Service SIP** - Gestion de la connexion entre Twilio et LiveKit
4. **Intégration Twilio** - Gestion des appels téléphoniques entrants

## Prérequis

- Un compte [LiveKit Cloud](https://livekit.io)
- Un compte [Twilio](https://twilio.com) avec un numéro de téléphone
- Des clés API pour:
  - OpenAI (pour le LLM)
  - Deepgram (pour le STT)
  - Cartesia (pour le TTS)

## Configuration

1. Clonez ce dépôt
2. Copiez `.env.example` vers `.env` et remplissez les variables
3. Installez les dépendances: `pip install -r requirements.txt`

## Configuration de Twilio pour les appels entrants

Pour configurer Twilio afin qu'il redirige les appels entrants vers votre agent:

1. Connectez-vous à votre compte Twilio
2. Accédez à **Phone Numbers** et sélectionnez votre numéro
3. Dans la section **Voice & Fax**:
   - Pour "A CALL COMES IN", sélectionnez "TwiML"
   - Créez un nouveau TwiML Bin ou utilisez l'URL de votre API déployée
   - Utilisez le TwiML fourni par l'endpoint `/twiml` ou `/api/twilio/twiml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Dial>
    <Sip username="livekit_user" password="s3cur3p@ssw0rd">
      sip:+15105551234@your-project-id.sip.livekit.cloud;transport=tcp
    </Sip>
  </Dial>
</Response>
```

## Configuration de LiveKit SIP

Dans votre application déployée, utilisez les endpoints API suivants pour configurer LiveKit SIP:

1. **Configurer un trunk SIP entrant**
   ```bash
   curl -X POST https://your-app.com/api/inbound/trunk/setup \
     -H "Content-Type: application/json" \
     -d '{"phone_number": "+15105551234"}'
   ```

2. **Configurer une règle de dispatch**
   ```bash
   curl -X POST https://your-app.com/api/inbound/dispatch/setup \
     -H "Content-Type: application/json" \
     -d '{"agent_name": "inbound-agent"}'
   ```

3. **Vérifier la configuration**
   ```bash
   curl https://your-app.com/api/inbound/status
   ```

## Démarrage de l'agent

Pour démarrer l'agent localement:

```bash
cd agent
python main.py dev
```

## Démarrage de l'API

Pour démarrer l'API localement:

```bash
cd api
python app.py
```

## Déploiement sur Railway

Ce projet est configuré pour être déployé sur [Railway](https://railway.app). Il suffit de connecter votre dépôt GitHub et de configurer les variables d'environnement requises dans les paramètres du projet Railway.

### Variables d'environnement requises pour Railway:

- `LIVEKIT_URL`
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`
- `LIVEKIT_SIP_HOST`
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_PHONE_NUMBER`
- `OPENAI_API_KEY`
- `DEEPGRAM_API_KEY`
- `CARTESIA_API_KEY`

## API Endpoints

L'API expose les endpoints suivants pour faciliter la configuration et les tests:

- `GET /health` - Vérification de santé de l'API
- `GET /api/twilio/test` - Tester les variables d'environnement Twilio
- `GET /api/livekit/test` - Tester la connexion à LiveKit
- `POST /api/inbound/trunk/setup` - Configurer un trunk SIP entrant
- `POST /api/inbound/dispatch/setup` - Configurer une règle de dispatch
- `GET /api/agent/status` - Vérifier l'état de l'agent
- `GET /api/inbound/status` - Vérifier l'état de la configuration des appels entrants
- `GET /api/twilio/twiml` - Obtenir un TwiML pour Twilio
- `POST /api/twilio/setup` - Instructions pour configurer Twilio
- `GET/POST /twiml` - Endpoint TwiML directement accessible pour Twilio

## Tester un appel entrant

Pour simuler un appel entrant (à des fins de test):

```bash
cd scripts
python test_inbound_call.py --phone +15105551234
```

## Structure du projet

```
/
├── agent/                  # Code de l'agent LiveKit
│   ├── main.py             # Point d'entrée principal de l'agent
│   ├── call_actions.py     # Actions que l'agent peut effectuer
│   └── inbound_handler.py  # Gestionnaire d'appels entrants
├── api/                    # API REST Flask
│   ├── app.py              # Application Flask principale
│   └── routes.py           # Endpoints API pour les tests et la configuration
├── scripts/                # Scripts utilitaires
│   ├── setup_inbound_trunk.py  # Configuration du trunk SIP entrant
│   ├── setup_dispatch_rule.py  # Configuration de la règle de dispatch
│   └── test_inbound_call.py    # Test d'appel entrant
├── .env.example            # Exemple de fichier d'environnement
├── requirements.txt        # Dépendances Python
├── Dockerfile              # Pour le déploiement sur Railway
├── Procfile                # Configuration pour Railway
└── README.md               # Documentation
```

## Dépannage

### Problèmes courants

1. **L'agent ne répond pas aux appels**
   - Vérifiez que l'agent est en cours d'exécution: `GET /api/agent/status`
   - Vérifiez que le trunk SIP entrant est configuré: `GET /api/inbound/status`
   - Vérifiez que la règle de dispatch est configurée: `GET /api/inbound/status`
   - Vérifiez que Twilio est correctement configuré avec le TwiML

2. **Erreurs de permission LiveKit**
   - Vérifiez que les clés API et le secret LiveKit sont corrects
   - Assurez-vous que les clés ont les permissions nécessaires pour la SIP et les agents

3. **Erreurs Twilio**
   - Vérifiez que le numéro de téléphone est correctement configuré
   - Vérifiez que le TwiML Bin est correctement configuré

## Contribuer

Les contributions sont les bienvenues! N'hésitez pas à ouvrir des issues ou des pull requests.

## Licence

MIT
