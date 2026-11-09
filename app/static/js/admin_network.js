
/* Administration réseau de Pythonpédia. */

const API = "/admin/network";

let apiKey = null;

const $ = (id) => document.getElementById(id);

function log(message) {
    $("operation-log").textContent =
        typeof message === "string"
            ? message
            : JSON.stringify(message, null, 2);
}


function setConnected(connected) {
    // Afficher ou masquer le panneau d'administration.
    $("admin-content").hidden = !connected;

    // Masquer le formulaire une fois connecté.
    $("auth-form").hidden = connected;

    // Afficher l'état de connexion.
    $("auth-status").textContent = connected
        ? "Connecté à l'administration"
        : "Non connecté";
}


async function request(path, options = {}) {
    if (!apiKey) {
        throw new Error("Authentification nécessaire.");
    }

    const response = await fetch(API + path, {
        ...options,
        headers: {
            "X-API-Key": apiKey,
            ...(options.body
                ? { "Content-Type": "application/json" }
                : {}),
            ...(options.headers || {}),
        },
    });

    const data = await response.json().catch(() => null);

    if (!response.ok) {
        const detail = data?.detail;

        const message = typeof detail === "string"
            ? detail
            : JSON.stringify(detail ?? "Erreur inconnue");

        throw new Error(
            `HTTP ${response.status} : ${message}`
        );
    }

    return data;
}

async function perform(button, action) {
    button.disabled = true;

    try {
        await action();
    } catch (error) {
        log(`Erreur : ${error.message}`);
    } finally {
        button.disabled = false;
    }
}


function createPeerCard(peer, index) {
    const card = document.createElement("div");
    card.className = "peer-card";

    // Informations du serveur.
    const information = document.createElement("div");
    information.className = "peer-information";

    const url = document.createElement("strong");
    url.className = "peer-url";
    url.textContent = peer.url;

    const status = document.createElement("p");
    status.className = "admin-muted";
    status.textContent = peer.approved
        ? "Serveur approuvé"
        : "En attente d'approbation";

    information.append(url, status);

    // Boutons disponibles pour ce serveur.
    const actions = document.createElement("div");
    actions.className = "peer-actions";

    if (!peer.approved) {
        const approveButton = document.createElement("button");
        approveButton.className = "admin-button secondary";
        approveButton.textContent = "Approuver";

        approveButton.addEventListener("click", () => {
            perform(approveButton, async () => {
                await request(
                    `/peers/${index}/approve`,
                    { method: "PATCH" }
                );

                await loadPeers();

                log({
                    operation: "Approbation",
                    server: peer.url,
                    success: true,
                });
            });
        });

        actions.appendChild(approveButton);

    } else {
        // Consulter les topics distants.
        const topicsButton = document.createElement("button");
        topicsButton.className = "admin-button secondary";
        topicsButton.textContent = "Voir les topics";

        topicsButton.addEventListener("click", () => {
            perform(topicsButton, async () => {
                const topics = await request(
                    `/peers/${index}/topics`
                );

                log({
                    operation: "Consultation des topics",
                    server: peer.url,
                    count: topics.length,
                    topics: topics,
                });
            });
        });

        // Synchroniser uniquement ce serveur.
        const syncButton = document.createElement("button");
        syncButton.className = "admin-button";
        syncButton.textContent = "Synchroniser";

        syncButton.addEventListener("click", () => {
            perform(syncButton, async () => {
                log(`Synchronisation de ${peer.url} en cours...`);

                const result = await request(
                    `/peers/${index}/sync`,
                    { method: "POST" }
                );

                await loadPeers();

                log({
                    operation: "Synchronisation individuelle",
                    server: peer.url,
                    report: result,
                });
            });
        });

        actions.append(topicsButton, syncButton);
    }

    card.append(information, actions);

    return card;
}


async function loadPeers() {
    const peers = await request("/peers");

    const list = $("peers-list");
    list.replaceChildren();

    $("total-peers").textContent = peers.length;

    const approved = peers.filter(
        (peer) => peer.approved
    ).length;

    $("approved-peers").textContent = approved;
    $("pending-peers").textContent =
        peers.length - approved;

    if (peers.length === 0) {
        const empty = document.createElement("p");
        empty.className = "admin-muted";
        empty.textContent = "Aucun serveur enregistré.";

        list.appendChild(empty);
        return;
    }

    peers.forEach((peer, index) => {
        list.appendChild(createPeerCard(peer, index));
    });
}

/* Authentification */

$("auth-form").addEventListener("submit", async (event) => {
    event.preventDefault();

    const candidate = $("api-key").value.trim();

    if (!candidate) return;

    apiKey = candidate;

    try {
        await loadPeers();

        $("api-key").value = "";
        setConnected(true);

        log("Connexion réussie.");
    } catch (error) {
        apiKey = null;
        setConnected(false);

        $("auth-status").textContent =
            `Connexion refusée : ${error.message}`;
    }
});

$("logout-button").addEventListener("click", () => {
    apiKey = null;

    $("api-key").value = "";
    setConnected(false);

    log("Déconnecté.");
});

/* Découverte */

$("discover-button").addEventListener("click", () => {
    perform($("discover-button"), async () => {
        log("Découverte réseau en cours...");

        const result = await request("/discover", {
            method: "POST",
        });

        await loadPeers();
        log(result);
    });
});

/* Ajout manuel */

$("add-peer-form").addEventListener("submit", (event) => {
    event.preventDefault();

    perform($("add-peer-form").querySelector("button"), async () => {
        const url = $("peer-url").value.trim();

        const result = await request("/peers", {
            method: "POST",
            body: JSON.stringify({
                url: url,
                approved: true,
            }),
        });

        $("peer-url").value = "";

        await loadPeers();

        log({
            operation: "Ajout manuel",
            url: url,
            ...result,
        });
    });
});

/* Actualisation */

$("refresh-button").addEventListener("click", () => {
    perform($("refresh-button"), async () => {
        await loadPeers();
        log("Annuaire actualisé.");
    });
});

/* Synchronisation */

$("sync-button").addEventListener("click", () => {
    perform($("sync-button"), async () => {
        log("Synchronisation en cours...");

        const results = await request("/sync", {
            method: "POST",
        });

        await loadPeers();
        log(results);
    });
});
