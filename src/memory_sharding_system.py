#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DARYL Sharding Memory - Production-Grade Distributed Memory System
Core system code with automatic cross-reference detection
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from link_validator import LinkValidator

# Configuration
MEMORY_DIR = Path("/home/buraluxtr/clawd/memory/")
SHARDS_DIR = Path("/home/buraluxtr/clawd/memory/shards/")
SHARD_CONFIG_FILE = Path("/home/buraluxtr/clawd/memory/shard_config.json")

# Shard domain definitions
SHARD_DOMAINS = {
    "projects": {
        "name": "Projets en cours",
        "description": "Projets actifs, tâches en cours, objectifs",
        "keywords": ["projet", "task", "project", "todo", "goal", "objective"]
    },
    "insights": {
        "name": "Insights et Leçons",
        "description": "Leçons apprises, patterns identifiés, décisions importantes",
        "keywords": ["leçon", "lesson", "pattern", "insight", "décision", "decision"]
    },
    "people": {
        "name": "Personnes et Relations",
        "description": "Contacts, experts, builders, relations importantes",
        "keywords": ["@", "contact", "person", "expert", "builder", "relation"]
    },
    "technical": {
        "name": "Technique et Architecture",
        "description": "Architecture, code, protocoles, frameworks",
        "keywords": ["architecture", "framework", "code", "protocol", "shard", "layer", "pillar"]
    },
    "strategy": {
        "name": "Stratégie et Vision",
        "description": "Vision à long terme, priorités, stratégies de contenu",
        "keywords": ["stratégie", "vision", "priority", "stratégie", "tendance", "trend"]
    }
}
