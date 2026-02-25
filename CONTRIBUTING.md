# Contributing to DSM

Merci de contribuer au projet DSM.

## Pré-requis

- Python 3.10+
- `pip` récent
- `git`

## Setup local

```bash
git clone https://github.com/buralux/dsm.git
cd dsm
python3 -m pip install -e ".[dev,web]"
pre-commit install
```

## Workflow de contribution

1. Crée une branche depuis `main`.
2. Fais des commits petits et descriptifs.
3. Lance les vérifications locales:

```bash
make test
make build
make precommit
```

4. Ouvre une Pull Request avec:
   - contexte,
   - changements,
   - impacts éventuels,
   - stratégie de test.

## Standards attendus

- Code lisible et cohérent avec le style existant.
- Pas de secrets, clés API ou credentials dans le repo.
- Toute évolution significative doit être couverte par des tests.
- Mettre à jour la documentation si le comportement change.

## Versioning / release

- Le projet suit SemVer.
- Les entrées de version doivent être ajoutées dans `CHANGELOG.md`.
- La publication PyPI est déclenchée par tag `v*` via GitHub Actions.
