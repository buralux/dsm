#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI pour le Système de Sharding de Mémoire DARYL v2.0
Adaptée pour la nouvelle structure de dépôt (src/, cli/, docs/)
"""

import sys
import json
import os
from pathlib import Path

# Ajouter le chemin src au sys.path pour les imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from memory_sharding_system import ShardRouter


def build_router(verbose: bool = False):
    """Construit un routeur DSM avec niveau de logs configurable."""
    return ShardRouter(verbose=verbose)


def cmd_add(args, verbose=False):
    """Ajouter une mémoire"""
    if not args:
        print("Usage: daryl-memory add \"<contenu>\" [--importance <0.5-1.0>] [--source <manual|moltbook>]")
        print()
        print("  --importance : Importance de la mémoire (0.5-1.0, défaut: 0.5)")
        print("  --source       : Source de la mémoire (manual, moltbook, défaut: manual)")
        return

    content = args[0]
    importance = 0.5
    source = "manual"

    # Parser les options
    i = 1
    while i < len(args):
        if args[i] == "--importance":
            importance = float(args[i+1])
            i += 2
        elif args[i] == "--source":
            source = args[i+1]
            i += 2
        else:
            i += 1

    router = build_router(verbose=verbose)

    transaction_id = router.add_memory(content, source=source, importance=importance)

    # Extraire l'info de la transaction
    parts = transaction_id.split("_")
    shard_id = "_".join(parts[:-2])
    shard = router.shards.get(shard_id)

    if shard:
        print(f"✅ Mémoire ajoutée")
        print(f"   Shard: {shard.config['name']}")
        print(f"   ID: {transaction_id}")
        print(f"   Source: {source}")
        print(f"   Importance: {importance}")
    else:
        print(f"❌ Erreur: Impossible de trouver le shard cible", file=sys.stderr)

def cmd_query(args, verbose=False):
    """Rechercher des mémoires"""
    if len(args) < 1:
        print("Usage: daryl-memory query \"<texte>\" [--limit <n>] [--cross]")
        print()
        print("  --limit : Nombre maximum de résultats (défaut: 10)")
        print("  --cross : Recherche cross-shard")
        return

    query_text = args[0]
    limit = 10
    cross_shard = False

    # Parser les options
    i = 1
    while i < len(args):
        if args[i] == "--limit":
            limit = int(args[i+1])
            i += 2
        elif args[i] == "--cross":
            cross_shard = True
            i += 1
        else:
            i += 1

    router = build_router(verbose=verbose)

    if cross_shard:
        results = router.cross_shard_search(query_text)
        print(f"🔍 Recherche cross-shard: \"{query_text}\"")
    else:
        results = router.query(query_text, limit=limit)

    print(f"   Limit: {limit}")
    print(f"   Cross-shard: {cross_shard}")
    print(f"   Résultats: {len(results)} trouvés")

    for r in results[:limit]:
        shard_name = r.get("shard_name", "Inconnu")
        content = r["content"][:70] + "..." if len(r["content"]) > 70 else r["content"]
        print(f"  • [{shard_name}] {content}")

def cmd_search(args, verbose=False):
    """Rechercher dans un shard spécifique"""
    if len(args) < 2:
        print("Usage: daryl-memory search \"<shard_id>\" \"<texte>\" [--limit <n>]")
        return

    shard_id = args[0]
    query_text = args[1]
    limit = 5

    # Parser l'option --limit
    i = 2
    while i < len(args):
        if args[i] == "--limit":
            limit = int(args[i+1])
            i += 2
        else:
            i += 1

    router = build_router(verbose=verbose)

    if shard_id not in router.shards:
        print(f"❌ Erreur: Shard '{shard_id}' introuvable", file=sys.stderr)
        return

    shard = router.shards[shard_id]
    results = shard.query(query_text, limit=limit)

    print(f"🔍 Recherche dans \"{shard.config['name']}\":")
    print(f"   Texte: {query_text}")
    print(f"   Résultats: {len(results)} trouvés")

    for r in results:
        content = r["content"][:70] + "..." if len(r["content"]) > 70 else r["content"]
        print(f"  • {content}")

def cmd_status(args, verbose=False):
    """Afficher le statut des shards"""
    router = build_router(verbose=verbose)

    print("📊 Statut des Shards DARYL:")
    print()

    status = router.get_all_shards_status()

    for shard_status in status:
        name = shard_status["name"]
        count = shard_status["transactions_count"]
        importance = shard_status["importance_score"]
        last_updated = shard_status.get("last_updated")
        last = last_updated[:19] if isinstance(last_updated, str) else "N/A"

        # Émoji basé sur le nombre de transactions
        if count == 0:
            emoji = "📭"
        elif count < 5:
            emoji = "📁"
        elif count < 20:
            emoji = "📚"
        else:
            emoji = "📖"

        print(f"  {emoji} {name}: {count} transactions (importance: {importance:.2f}) | {last}")

    summary = router.export_shards_summary()
    print(f"\n📊 Total: {summary['total_shards']} shards, {summary['total_transactions']} transactions")

def cmd_help(args, verbose=False):
    """Afficher l'aide"""
    print("=== DARYL Sharding Memory CLI v2.0 ===")
    print()
    print("Usage: daryl-memory [--verbose|-v] <commande> [arguments...]")
    print()
    print("Options globales:")
    print("  -v, --verbose                    Activer les logs détaillés")
    print()
    print("Commandes disponibles:")
    print("  add     \"<contenu>\"         Ajouter une mémoire")
    print("  query   \"<texte>\"           Rechercher des mémoires")
    print("  search  \"<shard_id>\" \"<texte>\"  Rechercher dans un shard")
    print("  status                           Afficher le statut des shards")
    print("  help                             Afficher cette aide")
    print()
    print("Exemples:")
    print("  daryl-memory add \"Projet: Finaliser la doc\" --importance 0.8")
    print("  daryl-memory --verbose query \"stratégie\" --limit 5")
    print("  daryl-memory search shard_projects \"GitHub\"")
    print()
    print("Pour plus d'informations, voir README.md")

def main():
    """Point d'entrée principal"""
    if len(sys.argv) < 2:
        cmd_help([], verbose=False)
        return

    raw_args = sys.argv[1:]
    verbose = False
    help_requested = False
    filtered_args = []

    for arg in raw_args:
        if arg in ("-v", "--verbose"):
            verbose = True
        elif arg in ("-h", "--help"):
            help_requested = True
        else:
            filtered_args.append(arg)

    if help_requested and not filtered_args:
        cmd_help([], verbose=verbose)
        return

    if not filtered_args:
        cmd_help([], verbose=verbose)
        return

    if help_requested:
        cmd_help([], verbose=verbose)
        return

    command = filtered_args[0].lower()
    cmd_args = filtered_args[1:]

    if command == "add":
        cmd_add(cmd_args, verbose=verbose)
    elif command == "query":
        cmd_query(cmd_args, verbose=verbose)
    elif command == "search":
        cmd_search(cmd_args, verbose=verbose)
    elif command == "status":
        cmd_status(cmd_args, verbose=verbose)
    elif command == "help":
        cmd_help(cmd_args, verbose=verbose)
    else:
        print(f"❌ Commande inconnue: {command}", file=sys.stderr)
        print("Utilisez 'daryl-memory help' pour voir les commandes disponibles", file=sys.stderr)

if __name__ == "__main__":
    main()
