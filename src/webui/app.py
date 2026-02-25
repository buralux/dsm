#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DARYL Web UI - Interface d'inspection pour Sharding Memory
FastAPI minimaliste pour exposer les fonctions Phase 2
"""

from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import os
import sys

# Ajouter src/ au PYTHONPATH
BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR.parent
sys.path.insert(0, str(SRC_DIR))

try:
    from memory_sharding_system import ShardRouter
except ImportError as e:
    print(f"❌ Erreur import ShardRouter: {e}", file=sys.stderr)
    ShardRouter = None

# Configuration FastAPI
app = FastAPI(title="DARYL Web UI", version="0.1", docs_url="/docs", redoc_url=None)

# Chemins
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Instance globale ShardRouter (MVP simple)
try:
    if ShardRouter:
        daryl = ShardRouter(verbose=False)
        print(f"✅ DARYL ShardRouter initialisé ({len(daryl.shards)} shards)")
    else:
        daryl = None
        print("⚠️ ShardRouter non disponible (import échoué)", file=sys.stderr)
except Exception as e:
    print(f"❌ Erreur initialisation ShardRouter: {e}", file=sys.stderr)
    daryl = None

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """
    Page d'accueil avec formulaire de recherche
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/stats")
def stats():
    """
    Statistiques globales de DARYL
    """
    if not daryl:
        return {"error": "DARYL ShardRouter non disponible"}
    
    if hasattr(daryl, "get_all_shards_status"):
        try:
            shards_status = daryl.get_all_shards_status()
            
            # Calculer des statistiques supplémentaires
            total_transactions = sum(s["transactions_count"] for s in shards_status)
            total_importance = sum(s["importance_score"] * s["transactions_count"] for s in shards_status)
            
            return {
                "total_shards": len(shards_status),
                "total_transactions": total_transactions,
                "total_importance": round(total_importance, 2),
                "shards": shards_status,
                "daryl_status": {
                    "active": daryl is not None,
                    "shards_loaded": len(daryl.shards) if daryl else 0
                }
            }
        except Exception as e:
            return {"error": f"Erreur récupération stats: {e}"}
    else:
        return {"error": "Méthode get_all_shards_status() non trouvée"}

@app.get("/shards")
def shards():
    """
    Liste de tous les shards avec leurs métadonnées
    """
    if not daryl:
        return {"error": "DARYL ShardRouter non disponible"}
    
    try:
        shards_list = daryl.get_all_shards_status()
        return {
            "shards": shards_list,
            "total": len(shards_list)
        }
    except Exception as e:
        return {"error": f"Erreur liste shards: {e}"}

@app.get("/shard/{shard_id}")
def shard_detail(shard_id: str):
    """
    Détails d'un shard spécifique
    """
    if not daryl:
        return {"error": "DARYL ShardRouter non disponible"}
    
    try:
        shard = daryl.get_shard_by_id(shard_id)

        if not shard:
            return {"error": f"Shard {shard_id} introuvable"}

        shard_data = {
            "id": shard.shard_id,
            "domain": shard.domain,
            "name": shard.config.get("name"),
            "description": shard.config.get("description"),
            "keywords": shard.config.get("keywords", []),
            "metadata": shard.metadata,
        }
        transactions = shard.transactions

        return {
            "shard": shard_data,
            "transactions_count": len(transactions),
            "transactions_preview": transactions[:5]  # 5 premières transactions
        }
    except Exception as e:
        return {"error": f"Erreur récupération shard: {e}"}

@app.get("/search")
def search(q: str = Query(..., min_length=1), min_score: float = 0.0, top_k: int = 5):
    """
    Recherche sémantique dans tous les shards
    """
    if not daryl:
        return {"error": "DARYL ShardRouter non disponible"}
    
    if not q:
        return {"error": "Paramètre q requis"}
    
    try:
        # Méthode de recherche sémantique
        if hasattr(daryl, "semantic_search"):
            results = daryl.semantic_search(q, threshold=min_score, top_k=top_k)
        else:
            return {"error": "Méthode semantic_search() non disponible"}
        
        return {
            "query": q,
            "min_score": min_score,
            "top_k": top_k,
            "results": results,
            "total_results": len(results)
        }
    except Exception as e:
        return {"error": f"Erreur recherche: {e}"}

@app.get("/hybrid")
def hybrid(q: str = Query(..., min_length=1), min_score: float = 0.0, top_k: int = 5):
    """
    Recherche hybride (sémantique + mots-clés)
    """
    if not daryl:
        return {"error": "DARYL ShardRouter non disponible"}
    
    if not q:
        return {"error": "Paramètre q requis"}
    
    try:
        # Méthode de recherche hybride
        if hasattr(daryl, "hybrid_search"):
            results = daryl.hybrid_search(q, threshold=min_score, top_k=top_k)
        else:
            return {"error": "Méthode hybrid_search() non disponible"}
        
        return {
            "query": q,
            "min_score": min_score,
            "top_k": top_k,
            "results": results,
            "total_results": len(results)
        }
    except Exception as e:
        return {"error": f"Erreur recherche hybride: {e}"}

@app.get("/compress")
def compress():
    """
    Compression de mémoire (doublons, consolidation)
    """
    if not daryl:
        return {"error": "DARYL ShardRouter non disponible"}
    
    try:
        # Méthode de compression de mémoire
        if hasattr(daryl, "compress_memory"):
            compression_results = daryl.compress_memory(shard_id=None, force=False)
        else:
            return {"error": "Méthode compress_memory() non disponible"}
        
        return {
            "compression_results": compression_results,
            "timestamp": str(Path(__file__).stat().st_mtime)
        }
    except Exception as e:
        return {"error": f"Erreur compression: {e}"}

@app.get("/cleanup")
def cleanup():
    """
    Nettoyage TTL (expiration automatique)
    """
    if not daryl:
        return {"error": "DARYL ShardRouter non disponible"}
    
    try:
        # Méthode de nettoyage TTL
        if hasattr(daryl, "cleanup_expired"):
            cleanup_results = daryl.cleanup_expired(shard_id=None, dry_run=True)
        else:
            return {"error": "Méthode cleanup_expired() non disponible"}
        
        return {
            "cleanup_results": cleanup_results,
            "timestamp": str(Path(__file__).stat().st_mtime)
        }
    except Exception as e:
        return {"error": f"Erreur nettoyage TTL: {e}"}

@app.get("/api-docs")
def api_docs():
    """
    Documentation API
    """
    return {
        "title": "DARYL Web UI API Documentation",
        "version": "0.1",
        "endpoints": {
            "GET /": "Page d'accueil avec formulaire de recherche",
            "GET /stats": "Statistiques globales de DARYL",
            "GET /shards": "Liste de tous les shards",
            "GET /shard/{id}": "Détails d'un shard spécifique",
            "GET /search": "Recherche sémantique (query, min_score, top_k)",
            "GET /hybrid": "Recherche hybride (query, min_score, top_k)",
            "GET /compress": "Compression de mémoire",
            "GET /cleanup": "Nettoyage TTL",
            "GET /api-docs": "Documentation API",
            "GET /docs": "OpenAPI Swagger UI"
        },
        "shard_router_methods": {
            "semantic_search()": "Recherche vectorielle",
            "hybrid_search()": "Recherche hybride",
            "compress_memory()": "Compression de mémoire",
            "cleanup_expired()": "Nettoyage TTL",
            "list_shards()": "Liste des shards",
            "get_shard_by_id(id)": "Détails d'un shard spécifique",
            "get_all_shards_status()": "Statistiques globales"
        }
    }


def serve():
    """Entry point de déploiement (sans reload par défaut)."""
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser(description="Run DSM Web UI server")
    parser.add_argument("--host", default=os.getenv("DSM_WEB_HOST", "0.0.0.0"), help="Host bind address")
    parser.add_argument("--port", type=int, default=int(os.getenv("DSM_WEB_PORT", "8000")), help="Host bind port")
    parser.add_argument("--reload", action="store_true", help="Enable uvicorn auto-reload")
    args = parser.parse_args()

    uvicorn.run("webui.app:app", host=args.host, port=args.port, reload=args.reload)

if __name__ == "__main__":
    import uvicorn
    print("🚀 DARYL Web UI - Démarrage du serveur FastAPI")
    print("📍 Dashboard: http://localhost:8000/")
    print("📚 Documentation: http://localhost:8000/docs")
    print("⚡ Reloading activé (--reload)")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
