#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MemoryCleaner - Nettoyage TTL pour DARYL Sharding Memory
Supprime les transactions expirées selon la configuration TTL
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

# Import absolu pour éviter les problèmes de module relatif
try:
    from semantic_search import SemanticSearch
except ImportError as e:
    raise ImportError(f"semantic_search non disponible. Vérifiez l'installation / le PYTHONPATH : {e}")


class MemoryCleaner:
    """Module de nettoyage TTL pour DARYL"""
    
    def __init__(
        self,
        shards_directory: str = "memory/shards",
        ttl_config_file: str = "src/config/ttl_config.json",
        verbose: bool = False,
    ):
        """
        Initialise le module de nettoyage TTL
        
        Args:
            shards_directory: Répertoire des shards JSON
            ttl_config_file: Fichier de configuration TTL
        """
        self.shards_dir = shards_directory
        self.ttl_config_file = ttl_config_file
        self.verbose = verbose
        self.ttl_config: Dict[str, Dict[str, int]] = {
            "shard_projects": {"ttl_days": 30, "max_transactions": 100},
            "shard_insights": {"ttl_days": 90, "max_transactions": 50},
            "shard_people": {"ttl_days": 90, "max_transactions": 50},
            "shard_technical": {"ttl_days": 180, "max_transactions": 200},
            "shard_strategy": {"ttl_days": 180, "max_transactions": 200}
        }
        self.stats: Dict[str, Any] = {
            "total_shards": 0,
            "expired_transactions": 0,
            "expired_transactions_by_shard": {},
            "archived_transactions": 0,
            "last_cleanup": None
        }
        self.shards_data: Dict[str, Dict[str, Any]] = {}
        self._load_ttl_config()
        self._load_all_shards()

    def _log(self, message: str):
        if self.verbose:
            stream = sys.stderr if message.startswith(("❌", "⚠️")) else sys.stdout
            print(message, file=stream)
    
    def _load_ttl_config(self) -> None:
        """Charge la configuration TTL depuis un fichier JSON"""
        config_path = Path(self.ttl_config_file)
        
        if config_path.exists():
            try:
                with config_path.open("r", encoding="utf-8") as f:
                    self.ttl_config = json.load(f)
                self._log(f"✅ Configuration TTL chargée depuis {config_path}")
            except Exception as e:
                self._log(f"⚠️ Erreur chargement TTL config, utilisation des valeurs par défaut: {e}")
        else:
            # Créer la configuration par défaut
            self._create_default_ttl_config()
    
    def _create_default_ttl_config(self) -> None:
        """Crée la configuration TTL par défaut"""
        config_path = Path(self.ttl_config_file)
        config_dir = config_path.parent
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration par défaut
        default_config = {
            "shard_projects": {"ttl_days": 30, "max_transactions": 100},
            "shard_insights": {"ttl_days": 90, "max_transactions": 50},
            "shard_people": {"ttl_days": 90, "max_transactions": 50},
            "shard_technical": {"ttl_days": 180, "max_transactions": 200},
            "shard_strategy": {"ttl_days": 180, "max_transactions": 200}
        }
        
        try:
            with config_path.open("w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            self._log(f"✅ Configuration TTL par défaut créée: {config_path}")
        except Exception as e:
            self._log(f"❌ Erreur création config TTL: {e}")
    
    def _load_all_shards(self) -> None:
        """Charge toutes les données de shards"""
        shards_path = Path(self.shards_dir)
        
        if not shards_path.exists():
            self._log(f"❌ Répertoire des shards non trouvé: {self.shards_dir}")
            return
        
        # Parcourir tous les fichiers .json
        shard_files = list(shards_path.glob("*.json"))
        
        self._log(f"📁 Chargement de {len(shard_files)} shards depuis {self.shards_dir}")
        
        for shard_file in shard_files:
            shard_id = shard_file.stem
            try:
                with shard_file.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    # ✅ assure une structure minimale
                    if "transactions" not in data or not isinstance(data["transactions"], list):
                        data["transactions"] = []
                    if "metadata" not in data or not isinstance(data["metadata"], dict):
                        data["metadata"] = {}
                    self.shards_data[shard_id] = data
                    self._log(f"   ✅ {shard_id}: {len(data.get('transactions', []))} transactions chargées")
            except Exception as e:
                self._log(f"   ❌ {shard_id}: Erreur de chargement - {e}")
    
    def _is_transaction_expired(self, transaction: Dict[str, Any], shard_id: str, current_date: datetime) -> bool:
        """
        Vérifie si une transaction est expirée selon la configuration TTL
        
        Args:
            transaction: Transaction à vérifier
            shard_id: ID du shard
            current_date: Date actuelle
            
        Returns:
            True si expirée, False sinon
        """
        # Récupérer la configuration TTL du shard
        shard_ttl = self.ttl_config.get(shard_id, {"ttl_days": 180})
        ttl_days = int(shard_ttl.get("ttl_days", 180))
        
        # Extraire la date de la transaction
        timestamp_str = transaction.get("timestamp", "")
        
        if not timestamp_str:
            # Sans timestamp, considérer comme expirée (ancienne)
            return True
        
        try:
            # Parser la date ISO 8601
            transaction_date = datetime.fromisoformat(timestamp_str)
            
            # Calculer l'âge en jours
            age_days = (current_date - transaction_date).days
            
            # Vérifier si TTL dépassé
            if age_days > ttl_days:
                return True
            
            return False
        except Exception as e:
            # Erreur de parsing -> considérer comme expirée
            self._log(f"⚠️ Erreur parsing timestamp '{timestamp_str}': {e}")
            return True
    
    def _check_max_transactions(self, shard_id: str) -> bool:
        """
        Vérifie si un shard dépasse le nombre maximum de transactions
        
        Args:
            shard_id: ID du shard
            
        Returns:
            True si dépasse, False sinon
        """
        shard_ttl = self.ttl_config.get(shard_id, {"max_transactions": 200})
        max_transactions = int(shard_ttl.get("max_transactions", 200))
        
        if shard_id not in self.shards_data:
            return False
        
        transactions = self.shards_data[shard_id].get("transactions", [])
        
        return len(transactions) > max_transactions
    
    def cleanup_expired_transactions(self, shard_id: str, dry_run: bool = False) -> Dict[str, Any]:
        """
        Nettoie les transactions expirées d'un shard
        
        Args:
            shard_id: ID du shard à nettoyer
            dry_run: Si True, ne supprime pas, seulement compte
            
        Returns:
            Dictionnaire avec les stats de nettoyage
        """
        if shard_id not in self.shards_data:
            return {"error": "Shard not found", "shard_id": shard_id}
        
        shard_data = self.shards_data[shard_id]
        transactions = shard_data.get("transactions", [])
        
        # Filtrer les transactions expirées
        current_date = datetime.now()
        expired: List[Dict[str, Any]] = []
        kept: List[Dict[str, Any]] = []
        
        for tx in transactions:
            if self._is_transaction_expired(tx, shard_id, current_date):
                expired.append(tx)
            else:
                kept.append(tx)
        
        stats: Dict[str, Any] = {
            "shard_id": shard_id,
            "total_transactions": len(transactions),
            "expired_transactions": len(expired),
            "kept_transactions": len(kept),
            "dry_run": dry_run,
        }
        
        # Si pas dry_run, supprimer les expirées
        if not dry_run and len(expired) > 0:
            shard_data["transactions"] = kept
            # ✅ metadata safe
            shard_data.setdefault("metadata", {})
            shard_data["metadata"]["last_cleanup"] = current_date.isoformat()
            shard_data["metadata"]["expired_transactions"] = len(expired)
            self._save_shard(shard_id, shard_data)
        
        return stats
    
    def archive_transactions(self, transactions: List[Dict[str, Any]], archive_file: str = "memory/archives/expired.json") -> bool:
        """
        Archive les transactions expirées
        
        Args:
            transactions: Liste de transactions à archiver
            archive_file: Fichier d'archive
            
        Returns:
            True si succès, False sinon
        """
        archive_path = Path(archive_file)
        
        try:
            # Créer le répertoire d'archives si nécessaire
            archive_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Lire l'archive existante
            existing_archives: List[Dict[str, Any]] = []
            if archive_path.exists():
                with archive_path.open("r", encoding="utf-8") as f:
                    existing_archives = json.load(f)
                    # Si jamais le fichier est corrompu / pas une liste
                    if not isinstance(existing_archives, list):
                        existing_archives = []
            
            # Ajouter les nouvelles transactions
            existing_archives.extend(transactions)
            
            # Sauvegarder
            with archive_path.open("w", encoding="utf-8") as f:
                json.dump(existing_archives, f, indent=2, ensure_ascii=False)
            
            self._log(f"✅ {len(transactions)} transactions archivées dans {archive_file}")
            return True
        except Exception as e:
            self._log(f"❌ Erreur archivage: {e}")
            return False
    
    def cleanup_max_transactions(self, shard_id: str, dry_run: bool = False) -> Dict[str, Any]:
        """
        Nettoie un shard en supprimant les transactions au-delà du maximum
        
        Args:
            shard_id: ID du shard à nettoyer
            dry_run: Si True, ne supprime pas
            
        Returns:
            Dictionnaire avec les stats de nettoyage
        """
        if shard_id not in self.shards_data:
            return {"error": "Shard not found", "shard_id": shard_id}
        
        shard_ttl = self.ttl_config.get(shard_id, {"max_transactions": 200})
        max_transactions = int(shard_ttl.get("max_transactions", 200))
        
        shard_data = self.shards_data[shard_id]
        transactions = shard_data.get("transactions", [])
        
        # Trier par timestamp (plus récents en premier)
        transactions_sorted = sorted(
            transactions,
            key=lambda x: x.get("timestamp", ""),
            reverse=True,
        )
        
        # Garder seulement le top-N
        kept = transactions_sorted[:max_transactions]
        removed = transactions_sorted[max_transactions:]
        
        stats: Dict[str, Any] = {
            "shard_id": shard_id,
            "total_transactions": len(transactions),
            "removed_transactions": len(removed),
            "kept_transactions": len(kept),
            "max_transactions": max_transactions,
            "dry_run": dry_run,
        }
        
        # Si pas dry_run, supprimer
        if not dry_run and len(removed) > 0:
            shard_data["transactions"] = kept
            # Archiver les transactions supprimées
            self.archive_transactions(removed, f"memory/archives/shard_{shard_id}_expired.json")
            # metadata safe
            shard_data.setdefault("metadata", {})
            shard_data["metadata"]["last_cleanup_max"] = datetime.now().isoformat()
            shard_data["metadata"]["removed_for_max"] = len(removed)
            self._save_shard(shard_id, shard_data)
        
        return stats
    
    def run_cleanup_all_shards(self, dry_run: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        Lance le nettoyage sur tous les shards
        
        Args:
            dry_run: Si True, ne supprime pas, seulement compte
            
        Returns:
            Dictionnaire avec les stats de nettoyage par shard
        """
        results: Dict[str, Dict[str, Any]] = {}
        total_expired = 0
        total_removed_max = 0
        
        for shard_id in list(self.shards_data.keys()):
            # 1. Nettoyer les transactions expirées
            expired_stats = self.cleanup_expired_transactions(shard_id, dry_run=dry_run)
            results[f"{shard_id}_expired"] = expired_stats
            total_expired += int(expired_stats.get("expired_transactions", 0))
            
            # 2. Nettoyer si nombre max dépassé
            max_stats = self.cleanup_max_transactions(shard_id, dry_run=dry_run)
            results[f"{shard_id}_max"] = max_stats
            total_removed_max += int(max_stats.get("removed_transactions", 0))
        
        # Mettre à jour les stats globales
        self.stats["total_shards"] = len(self.shards_data)
        self.stats["expired_transactions"] = total_expired
        self.stats["expired_transactions_by_shard"] = {
            shard_id: int(results.get(f"{shard_id}_expired", {}).get("expired_transactions", 0))
            for shard_id in self.shards_data.keys()
        }
        self.stats["archived_transactions"] = total_expired + total_removed_max
        self.stats["last_cleanup"] = datetime.now().isoformat()
        
        if not dry_run:
            self._log(f"🧹 Nettoyage terminé: {total_expired} expirées, {total_removed_max} supprimées (max)")
        else:
            self._log(f"🧹 DRY RUN: {total_expired} expirées, {total_removed_max} supprimées (max)")
        
        return results
    
    def _save_shard(self, shard_id: str, shard_data: Dict[str, Any]) -> None:
        """
        Sauvegarde les données d'un shard
        
        Args:
            shard_id: ID du shard
            shard_data: Données du shard
        """
        shard_path = Path(self.shards_dir) / f"{shard_id}.json"
        
        try:
            with shard_path.open("w", encoding="utf-8") as f:
                json.dump(shard_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self._log(f"❌ Erreur sauvegarde shard {shard_id}: {e}")
    
    def get_cleanup_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques de nettoyage
        
        Returns:
            Dictionnaire avec les stats globales
        """
        return self.stats


if __name__ == "__main__":
    # Test du module de nettoyage TTL
    cleaner = MemoryCleaner(shards_directory="memory/shards")
    
    print("🧪 Test du module MemoryCleaner")
    print(f"   Shards chargés: {len(cleaner.shards_data)}")
    print("   Configuration TTL:")
    for shard_id, ttl in cleaner.ttl_config.items():
        print(f"      {shard_id}: {ttl['ttl_days']} jours, max {ttl['max_transactions']} tx")
    print()
    
    # Test 1: Vérifier une transaction récente
    print("🔍 Test 1: Vérification transactions expirées")
    current_date = datetime.now()
    
    # Trouver une transaction récente (< 30 jours)
    recent_tx = None
    shard_id_recent = None
    for sid, shard_data in cleaner.shards_data.items():
        transactions = shard_data.get("transactions", [])
        for tx in transactions:
            ts = tx.get("timestamp", "")
            if not ts:
                continue
            try:
                tx_date = datetime.fromisoformat(ts)
                if (current_date - tx_date).days < 30:
                    recent_tx = tx
                    shard_id_recent = sid
                    break
            except Exception:
                continue
    
    if recent_tx and shard_id_recent:
        content_preview = str(recent_tx.get("content", ""))[:50]
        print(f"   Transaction récente trouvée: {content_preview}...")
        print(f"   Shard: {shard_id_recent}")
        print(f"   Date: {recent_tx.get('timestamp')}")
        print(f"   Expired (si on se place +60j): {cleaner._is_transaction_expired(recent_tx, shard_id_recent, current_date - timedelta(days=60))}")
    else:
        print("   Aucune transaction récente trouvée")
    print()
    
    # Test 2: dry run
    print("🗜️ Test 2: Nettoyage complet (dry run)")
    results = cleaner.run_cleanup_all_shards(dry_run=True)
    
    for key, value in results.items():
        print(f"   {key}: {value.get('expired_transactions', 0)} expirées")
    
    print()
    print("📊 Statistiques globales:")
    stats = cleaner.get_cleanup_stats()
    for k, v in stats.items():
        print(f"   {k}: {v}")
