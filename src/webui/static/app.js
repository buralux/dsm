// DARYL Web UI - JavaScript (AJAX)
// Minimaliste pour Phase 3 MVP

// Fonction générique pour afficher les résultats
function displayOutput(data, error = null) {
    const out = document.getElementById("out");
    
    if (error) {
        out.textContent = "❌ Erreur: " + error;
        out.style.color = "#e74c3c";  // Rouge
    } else if (data.error) {
        out.textContent = "⚠️ Erreur: " + data.error;
        out.style.color = "#e67e22";  // Orange
    } else {
        out.textContent = JSON.stringify(data, null, 2);
        out.style.color = "#2ecc71";  // Vert
    }
}

// Fonction générique pour afficher les messages
function displayMessage(msg) {
    const out = document.getElementById("out");
    out.textContent = msg;
    out.style.color = "#f1c40f";  // Bleu clair
}

// 1. Recherche Sémantique / Hybride
async function doSearch(kind) {
    const q = document.getElementById("q").value.trim();
    
    if (!q) {
        displayMessage("⚠️ Veuillez entrer une recherche");
        return;
    }
    
    const url = `/${kind}?q=${encodeURIComponent(q)}&top_k=5&min_score=0.0`;
    
    try {
        const res = await fetch(url);
        const data = await res.json();
        
        if (data.error) {
            displayOutput(data, data.error);
        } else {
            let output = "";
            output += `🔍 Recherche ${kind.toUpperCase()}: "${data.query}"\n\n`;
            output += `Total résultats: ${data.total_results}\n\n`;
            
            // Afficher les résultats
            if (data.results && data.results.length > 0) {
                output += "📊 Résultats:\n";
                data.results.forEach((r, i) => {
                    output += `\n${i+1}. [${r.shard_name}] Score: ${r.score.toFixed(3)}\n`;
                    output += `   Content: ${r.content.substring(0, 80)}...\n`;
                    output += `   Transaction ID: ${r.transaction_id}\n`;
                });
            } else {
                output += "ℹ️ Aucun résultat trouvé (score < 0.7)\n";
            }
            
            displayOutput({"kind": kind, "data": data});
        }
    } catch (error) {
        displayOutput(null, "Erreur lors de la recherche: " + error);
    }
}

// 2. Charger les Stats
async function loadStats() {
    try {
        const res = await fetch("/stats");
        const data = await res.json();
        
        if (data.error) {
            displayOutput(data, data.error);
        } else {
            let output = "";
            output += "📊 Statistiques DARYL\n\n";
            output += `Total Shards: ${data.total_shards}\n`;
            output += `Total Transactions: ${data.total_transactions}\n`;
            output += `Total Importance: ${data.total_importance}\n\n`;
            
            if (data.daryl_status) {
                output += "DARYL Status:\n";
                output += `  Active: ${data.daryl_status.active ? "✅" : "❌"}\n`;
                output += `  Shards Loaded: ${data.daryl_status.shards_loaded}\n`;
            }
            
            displayOutput({"kind": "stats", "data": data});
        }
    } catch (error) {
        displayOutput(null, "Erreur lors du chargement des stats: " + error);
    }
}

// 3. Charger les Shards
async function loadShards() {
    try {
        const res = await fetch("/shards");
        const data = await res.json();
        
        if (data.error) {
            displayOutput(data, data.error);
        } else {
            let output = "";
            output += "📦 Shards DARYL\n\n";
            output += `Total: ${data.total}\n\n`;
            
            if (data.shards && data.shards.length > 0) {
                output += "Liste des shards:\n";
                data.shards.forEach((shard, i) => {
                    output += `\n${i+1}. ${shard.shard_id}: ${shard.name} (${shard.domain})\n`;
                    output += `   Transactions: ${shard.transactions}\n`;
                });
            }
            
            displayOutput({"kind": "shards", "data": data});
        }
    } catch (error) {
        displayOutput(null, "Erreur lors du chargement des shards: " + error);
    }
}

// 4. Compresser la Mémoire
async function compressMemory() {
    try {
        const res = await fetch("/compress");
        const data = await res.json();
        
        if (data.error) {
            displayOutput(data, data.error);
        } else {
            let output = "";
            output += "🗜️ Compression de Mémoire\n\n";
            output += `Timestamp: ${data.timestamp}\n\n`;
            
            if (data.compression_results) {
                output += "Résultats de compression:\n";
                const results = data.compression_results;
                for (const [key, value] of Object.entries(results)) {
                    if (typeof value === "object" && value !== null) {
                        output += `\n${key}:\n`;
                        output += `  Doublons supprimés: ${value.removed_duplicates || 0}\n`;
                        output += `  Transactions consolidées: ${value.consolidated_transactions || 0}\n`;
                        output += `  Avant compression: ${value.total_before || 0}\n`;
                        output += `  Après compression: ${value.total_after || 0}\n`;
                    }
                }
            }
            
            displayOutput({"kind": "compress", "data": data});
        }
    } catch (error) {
        displayOutput(null, "Erreur lors de la compression: " + error);
    }
}

// 5. Nettoyer la Mémoire (TTL)
async function cleanupMemory() {
    try {
        const res = await fetch("/cleanup");
        const data = await res.json();
        
        if (data.error) {
            displayOutput(data, data.error);
        } else {
            let output = "";
            output += "🧹 Nettoyage TTL (Expiration Automatique)\n\n";
            output += `Timestamp: ${data.timestamp}\n\n`;
            
            if (data.cleanup_results) {
                output += "Résultats du nettoyage:\n";
                const results = data.cleanup_results;
                for (const [key, value] of Object.entries(results)) {
                    if (typeof value === "object" && value !== null) {
                        output += `\n${key}:\n`;
                        output += `  Transactions expirées: ${value.expired_transactions || 0}\n`;
                        output += `  Transactions gardées: ${value.kept_transactions || 0}\n`;
                        output += `  Transactions supprimées (max): ${value.removed_transactions || 0}\n`;
                    }
                }
            }
            
            displayOutput({"kind": "cleanup", "data": data});
        }
    } catch (error) {
        displayOutput(null, "Erreur lors du nettoyage: " + error);
    }
}

// Entrée: focus sur l'input
document.addEventListener("DOMContentLoaded", function() {
    const input = document.getElementById("q");
    if (input) {
        input.focus();
    }
});
