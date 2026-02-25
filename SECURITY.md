# Security Policy

## Supported versions

Les versions supportées sont les dernières versions mineures publiées.

| Version | Support |
| --- | --- |
| 0.4.x | ✅ |
| < 0.4.0 | ❌ |

## Reporting a vulnerability

Merci de **ne pas** ouvrir d’issue publique pour une vulnérabilité.

Procédure recommandée:

1. Ouvre une GitHub Security Advisory (private disclosure) sur le repository.
2. Décris le contexte, l’impact, et des étapes de reproduction minimales.
3. Si possible, propose un correctif ou un contournement.

Nous faisons le maximum pour:

- accuser réception rapidement,
- qualifier la sévérité,
- publier un correctif et une note de sécurité.

## Security hardening guidance

- Ne stockez pas de secrets dans les shards.
- Exécutez DSM avec des permissions minimales.
- Isolez les volumes de données en production (`DSM_MEMORY_DIR`).
- Maintenez vos dépendances à jour (`pip list --outdated`).
