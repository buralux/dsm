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
sys.path.insert(0, str(Path(__file__).parent / "src"))

from memory_sharding_system import ShardRouter

def cmd_add(args):
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

    router = ShardRouter()
    router.load_all_shards()

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
        print(f"❌ Erreur: Impossible de trouver le shard cible")

def cmd_query(args):
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

    router = ShardRouter()
    router.load_all_shards()

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

def cmd_search(args):
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

    router = ShardRouter()
    router.load_all_shards()

    if shard_id not in router.shards:
        print(f"❌ Erreur: Shard '{shard_id}' introuvable")
        return

    shard = router.shards[shard_id]
    results = shard.query(query_text, limit=limit)

    print(f"🔍 Recherche dans \"{shard.config['name']}\":")
    print(f"   Texte: {query_text}")
    print(f"   Résultats: {len(results)} trouvés")

    for r in results:
        content = r["content"][:70] + "..." if len(r["content"]) > 70 else r["content"]
        print(f"  • {content}")

def cmd_status(args):
    """Afficher le statut des shards"""
    router = ShardRouter()
    router.load_all_shards()

    print("📊 Statut des Shards DARYL:")
    print()

    status = router.get_all_shards_status()

    for shard_status in status:
        name = shard_status["name"]
        count = shard_status["transactions_count"]
        importance = shard_status["importance_score"]
        last = shard_status["last_updated"][:19]  # Just date et heure

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

def main():
    """Point d'entrée principal"""
    if len(sys.argv) < 2:
        print("=== DARYL Sharding Memory CLI v2.0 ===")
        print()
        print("Usage: daryl-memory <commande> [arguments...]")
        print()
        print("Commandes disponibles:")
        print("  add     \"<contenu>\"         Ajouter une mémoire")
        print("  query   \"<texte>\"           Rechercher des mémoires")
        print("  search  \"<shard_id>\" \"<texte>\"  Rechercher dans un shard")
        print("  status                           Afficher le statut des shards")
        print()
        print("Pour plus d'informations, voir README.md")
        return

    command = sys.argv[1].lower()

    if command == "add":
        cmd_add(sys.argv[2:])
    elif command == "query":
        cmd_query(sys.argv[2:])
    elif command == "search":
        cmd_search(sys.argv[2:])
    elif command == "status":
        cmd_status(sys.argv[2:])
    else:
        print(f"❌ Commande inconnue: {command}")
        print("Utilisez 'daryl-memory help' pour voir les commandes disponibles")

if __name__ == "__main__":
    main()
