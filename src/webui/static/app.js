// DARYL Web UI - JavaScript (AJAX)
// Phase 3.5: MultiversX UX (Top-K/Min-Score inputs + Status indicator)

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

// Fonction pour définir le status (loading/ready)
function setStatus(s) {
    const statusEl = document.getElementById("status");
    if (statusEl) {
        statusEl.textContent = s;
    }
}

// Fonction générique pour afficher les messages
function displayMessage(msg) {
    const out = document.getElementById("out");
    out.textContent = msg;
    out.style.color = "#f1c40f";  // Bleu clair
}

// Fonction pour afficher les résultats en cards (MultiversX style)
function displayResultsCards(results) {
    const cardsContainer = document.getElementById("results-cards");
    
    if (!cardsContainer) {
        // Si le container n'existe pas (fallback), afficher dans le output JSON
        return;
    }
    
    cardsContainer.innerHTML = "";
    
    results.forEach((r, i) => {
        const card = document.createElement("div");
        card.className = "glass card-item p-4 hover-glow"; // MultiversX style: glass + glow
        
        // Header du card (Shard badge + Score badge)
        const header = document.createElement("div");
        header.className = "flex items-center justify-between";
        header.innerHTML = `
            <span class="chip text-white/60">${r.shard_name || r.shard_id}</span>
            <span class="score-badge">${(r.score * 100).toFixed(1)}%</span>
        `;
        
        // Content du card
        const content = document.createElement("div");
        content.className = "text-sm text-white/70 mt-2";
        content.innerHTML = `<p>${r.content.substring(0, 100)}...</p>`;
        
        // Footer du card (TX ID + Importance)
        const footer = document.createElement("div");
        footer.className = "flex items-center justify-between text-xs text-white/50 mt-2 pt-2 border-t border-white/10";
        footer.innerHTML = `
            <span>${r.transaction_id.substring(0, 15)}...</span>
            <span>imp: ${r.importance.toFixed(2)}</span>
        `;
        
        card.appendChild(header);
        card.appendChild(content);
        card.appendChild(footer);
        
        cardsContainer.appendChild(card);
    });
}

// Fonction pour afficher les stats en cards
function displayStatsCards(data) {
    const cardsContainer = document.getElementById("results-cards");
    
    if (!cardsContainer) {
        return;
    }
    
    cardsContainer.innerHTML = "";
    
    if (data.shards && data.shards.length > 0) {
        data.shards.forEach((s, i) => {
            const card = document.createElement("div");
            card.className = "glass p-4 hover-glow"; // MultiversX style: glass + glow
            
            const header = document.createElement("div");
            header.className = "flex items-center justify-between";
            header.innerHTML = `
                <span class="chip text-white/60">${s.shard_id}</span>
                <span class="text-xs text-white/50">${s.transactions} tx</span>
            `;
            
            const content = document.createElement("div");
            content.className = "text-sm text-white/70 mt-2";
            content.innerHTML = `<p><strong>${s.name}</strong> (${s.domain})</p>`;
            
            card.appendChild(header);
            card.appendChild(content);
            
            cardsContainer.appendChild(card);
        });
    }
}

// 1. Recherche Sémantique / Hybride (MultiversX: Top-K / Min-Score)
async function doSearch(kind) {
    const q = document.getElementById("q").value.trim();
    const top_k = document.getElementById("top_k").value.trim() || "5";
    const min_score = document.getElementById("min_score").value.trim() || "0.0";
    
    if (!q) {
        setStatus("⚠️ Veuillez entrer une recherche");
        return;
    }
    
    setStatus("loading…");
    
    // Construction de l'URL avec top_k et min_score
    const url = `/${kind}?q=${encodeURIComponent(q)}&top_k=${encodeURIComponent(top_k)}&min_score=${encodeURIComponent(min_score)}`;
    
    try {
        const res = await fetch(url);
        const data = await res.json();
        
        if (data.error) {
            setStatus("error: " + data.error);
            displayOutput(data, data.error);
        } else {
            let output = "";
            output += `🔍 Recherche ${kind.toUpperCase()}: "${data.query}"\n`;
            output += `Top-k: ${data.top_k} | Min-score: ${data.min_score}\n\n`;
            
            // Afficher les résultats en cards
            if (data.results && data.results.length > 0) {
                output += `📊 Résultats (${data.total_results}):\n\n`;
                displayResultsCards(data.results); // Afficher les cards
            } else {
                output += `ℹ️ Aucun résultat trouvé (score < ${data.min_score})\n\n`;
            }
            
            setStatus("ready");
            displayOutput({"kind": kind, "data": data}); // Fallback JSON
        }
    } catch (error) {
        setStatus("error");
        displayOutput(null, "Erreur lors de la recherche: " + error);
    }
}

// 2. Charger les Stats
async function loadStats() {
    setStatus("loading…");
    
    try {
        const res = await fetch("/stats");
        const data = await res.json();
        
        if (data.error) {
            setStatus("error: " + data.error);
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
            
            displayStatsCards(data); // Afficher les cards
            setStatus("ready");
            displayOutput({"kind": "stats", "data": data});
        }
    } catch (error) {
        setStatus("error");
        displayOutput(null, "Erreur lors du chargement des stats: " + error);
    }
}

// 3. Charger les Shards
async function loadShards() {
    setStatus("loading…");
    
    try {
        const res = await fetch("/shards");
        const data = await res.json();
        
        if (data.error) {
            setStatus("error: " + data.error);
            displayOutput(data, data.error);
        } else {
            let output = "";
            output += "📦 Shards DARYL\n\n";
            output += `Total: ${data.total}\n\n`;
            
            displayStatsCards(data); // Afficher les cards
            setStatus("ready");
            displayOutput({"kind": "shards", "data": data});
        }
    } catch (error) {
        setStatus("error");
        displayOutput(null, "Erreur lors du chargement des shards: " + error);
    }
}

// 4. Compresser la Mémoire
async function compressMemory() {
    setStatus("loading…");
    
    try {
        const res = await fetch("/compress");
        const data = await res.json();
        
        if (data.error) {
            setStatus("error: " + data.error);
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
            
            setStatus("ready");
            displayOutput({"kind": "compress", "data": data});
        }
    } catch (error) {
        setStatus("error");
        displayOutput(null, "Erreur lors de la compression: " + error);
    }
}

// 5. Nettoyer la Mémoire (TTL)
async function cleanupMemory() {
    setStatus("loading…");
    
    try {
        const res = await fetch("/cleanup");
        const data = await res.json();
        
        if (data.error) {
            setStatus("error: " + data.error);
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
            
            setStatus("ready");
            displayOutput({"kind": "cleanup", "data": data});
        }
    } catch (error) {
        setStatus("error");
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
