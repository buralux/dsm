#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LinkValidator - Validation system for cross-shard references
Simple but effective validation to prevent shard poisoning
"""

class LinkValidator:
    def __init__(self, shards_directory="memory/shards"):
        self.shards_dir = shards_directory
        self.allowed_shards = [
            "shard_projects",
            "shard_insights",
            "shard_people",
            "shard_technical",
            "shard_strategy"
        ]
        self.max_refs_per_transaction = 3
        self.max_cycle_depth = 2

    def validate_link(self, from_shard_id, to_shard_id):
        """
        Validates a cross-shard reference
        
        Returns:
            (is_valid, message)
        """
        # Check if from_shard_id exists
        if from_shard_id not in self.allowed_shards:
            return False, f"Source shard '{from_shard_id}' is not allowed"
        
        # Check if to_shard_id exists
        if to_shard_id not in self.allowed_shards:
            return False, f"Target shard '{to_shard_id}' does not exist"
        
        # Prevent self-references (shard pointing to itself)
        if from_shard_id == to_shard_id:
            return False, "Self-reference not allowed"
        
        # Check if link would create a cycle (simple depth check)
        # In production, this would use graph traversal (A->B->C->A = cycle)
        # For now, we use a simple check
        cycle = self._would_create_cycle(from_shard_id, to_shard_id, visited=set(), depth=0)
        if cycle:
            return False, f"Reference would create a cycle (depth: {cycle['depth']})"
        
        # All checks passed
        return True, "Valid cross-shard reference"

    def _would_create_cycle(self, from_shard, to_shard, visited, depth):
        """Check if adding this link would create a cycle"""
        if depth > self.max_cycle_depth:
            return {"cycle": True, "depth": depth}
        
        if to_shard in visited:
            return {"cycle": True, "depth": depth}
        
        visited.add(to_shard)
        
        # Check if any shard in visited has this as a target (incoming link)
        # This is a simplified cycle detection
        # In production, we'd use a proper graph traversal
        for shard in visited:
            # In a real system, we'd check if shard has from_shard as a target
            # For now, we assume links are bidirectional
            pass
        
        return {"cycle": False, "depth": depth}
