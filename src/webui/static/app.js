// DARYL Web UI - JavaScript (AJAX)
// Phase 3.5: UX améliorée (cards, filtres, dry-run toggle)

// Fonction générique pour afficher les résultats
function displayOutput(data, error = null) {
    const out = document.getElementById("out");
    const cardsContainer = document.getElementById("results-cards");
    
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
    
    // Afficher les résultats en cards
    if (data.results && data.results.length > 0) {
        displayResultsCards(data.results);
    }
}

// Fonction générique pour afficher les messages
function displayMessage(msg) {
    const out = document.getElementById("out");
    out.textContent = msg;
    out.style.color = "#f1c40f";  // Bleu clair
}

// Fonction pour afficher les résultats en cards
function displayResultsCards(results) {
    const cardsContainer = document.getElementById("results-cards");
    cardsContainer.innerHTML = "";
    
    results.forEach((r, i) => {
        const card = document.createElement("div");
        card.className = "result-card";
        
        // Header du card
        const header = document.createElement("div");
        header.className = "card-header";
        header.innerHTML = `<span class="shard-badge">${r.shard_name}</span> <span class="score-badge">${(r.score * 100).toFixed(1)}%</span>`;
        
        // Content du card
        const content = document.createElement("div");
        content.className = "card-content";
        content.innerHTML = `<p>${r.content.substring(0, 150)}...</p>`;
        
        // Footer du card
        const footer = document.createElement("div");
        footer.className = "card-footer";
        footer.innerHTML = `<span class="tx-id">${r.transaction_id.substring(0, 20)}...</span> <span class="importance">${r.importance.toFixed(2)}</span>`;
        
        card.appendChild(header);
        card.appendChild(content);
        card.appendChild(footer);
        
        cardsContainer.appendChild(card);
    });
}

// Fonction pour afficher les stats en cards
function displayStatsCards(data) {
    const cardsContainer = document.getElementById("results-cards");
    cardsContainer.innerHTML = "";
    
    if (data.shards && data.shards.length > 0) {
        data.shards.forEach((s, i) => {
            const card = document.createElement("div");
            card.className = "result-card";
            
            const header = document.createElement("div");
            header.className = "card-header";
            header.innerHTML = `<span class="shard-badge">${s.shard_id}</span> <span class="tx-count">${s.transactions} tx</span>`;
            
            const content = document.createElement("div");
            content.className = "card-content";
            content.innerHTML = `<p><strong>${s.name}</strong> (${s.domain})</p>`;
            
            cardsContainer.appendChild(card);
        });
    }
}

// Filtre par shard
function filterByShard() {
    const shardFilter = document.getElementById("shard_filter").value;
    const out = document.getElementById("out");
    
    out.textContent = `🔍 Filtre appliqué: ${shardFilter || "Tous les shards"}`;
    out.style.color = "#f1c40f";  // Bleu clair
}

// 1. Recherche Sémantique / Hybride
async function doSearch(kind) {
    const q = document.getElementById("q").value.trim();
    const shardFilter = document.getElementById("shard_filter").value;
    const dryRun = document.getElementById("dry_run").checked;
    
    if (!q) {
        displayMessage("⚠️ Veuillez entrer une recherche");
        return;
    }
    
    // Construction de l'URL avec filtre shard et dry-run
    let url = `/${kind}?q=${encodeURIComponent(q)}&top_k=5&min_score=0.0`;
    
    if (shardFilter) {
        url += `&shard=${encodeURIComponent(shardFilter)}`;
    }
    
    if (dryRun && kind === "search") {
        url += "&dry_run=true";
    }
    
    try {
        const res = await fetch(url);
        const data = await res.json();
        
        if (data.error) {
            displayOutput(data, data.error);
        } else {
            let output = "";
            output += `🔍 Recherche ${kind.toUpperCase()}: "${data.query}"\n`;
            output += `Top-k: ${data.top_k} | Min-score: ${data.min_score}\n`;
            output += `Shard: ${shardFilter || "Tous les shards"}\n`;
            output += `Dry-run: ${dryRun ? "OUI" : "NON"}\n\n`;
            
            // Afficher les résultats en cards
            if (data.results && data.results.length > 0) {
                output += `📊 Résultats (${data.total_results}):\n\n`;
                displayResultsCards(data.results);
            } else {
                output += `ℹ️ Aucun résultat trouvé (score < ${data.min_score})\n\n`;
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
            
            displayStatsCards(data);
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
            
            // Afficher les shards en cards
            if (data.shards && data.shards.length > 0) {
                output += "Liste des shards:\n\n";
                displayStatsCards(data);
            }
            
            displayOutput({"kind": "shards", "data": data});
        }
    } catch (error) {
        displayOutput(null, "Erreur lors du chargement des shards: " + error);
    }
}

// 4. Compresser la Mémoire
async function compressMemory() {
    const dryRun = document.getElementById("dry_run").checked;
    
    try {
        const res = await fetch(`/compress?dry_run=${dryRun}`);
        const data = await res.json();
        
        if (data.error) {
            displayOutput(data, data.error);
        } else {
            let output = "";
            output += "🗜️ Compression de Mémoire\n";
            output += `Dry-run: ${dryRun ? "OUI" : "NON"}\n`;
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
    const dryRun = document.getElementById("dry_run").checked;
    
    try {
        const res = await fetch(`/cleanup?dry_run=${dryRun}`);
        const data = await res.json();
        
        if (data.error) {
            displayOutput(data, data.error);
        } else {
            let output = "";
            output += "🧹 Nettoyage TTL (Expiration Automatique)\n";
            output += `Dry-run: ${dryRun ? "OUI" : "NON"}\n`;
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
