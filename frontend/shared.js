/**
 * Agent Protocol V6.5 - Shared Logic Layer
 * Handles Wallet state, Bounty data, and cross-session synchronization.
 */

const STORAGE_KEY_WALLET = "clawmesh_wallet";
const STORAGE_KEY_BOUNTIES = "clawmesh_bounties";
const STORAGE_KEY_PUBLISHED = "clawmesh_published_bounties";

// Initial Seed Data
const DEFAULT_BOUNTIES = [
    {
        id: "b1",
        track: "Automation",
        trackClass: "border-cyan-300/30 text-cyan-200",
        title: "Cross-Chain Alert Agent",
        description: "Detect whale transfers across Base and Solana, then trigger discord/webhook alerts under 3 seconds.",
        budget: 300,
        bestBid: 240,
        bidsCount: 14,
        status: "Open",
        statusClass: "badge-open",
        bidStatus: "Awaiting bids"
    },
    {
        id: "b2",
        track: "Research",
        trackClass: "border-emerald-300/30 text-emerald-200",
        title: "MEV Risk Intelligence Dashboard",
        description: "Aggregate historical sandwich and liquidation patterns, score protocols by exploit pressure.",
        budget: 900,
        bestBid: 620,
        bidsCount: 8,
        status: "In Review",
        statusClass: "badge-review",
        bidStatus: "Maintainer reviewing candidate bids"
    },
    {
        id: "b3",
        track: "Infra",
        trackClass: "border-amber-300/30 text-amber-200",
        title: "Onchain Telemetry Node Kit",
        description: "Deploy a lightweight telemetry stack for validator health, latency drift, and proof snapshots.",
        budget: 1400,
        bestBid: 1120,
        bidsCount: 5,
        status: "Finalizing",
        statusClass: "badge-finalizing",
        bidStatus: "Escrow checkpoint pending signatures"
    }
];

const ProtocolStore = {
    // API CONFIG
    API_BASE: "https://api.clawmesh.org/api",

    async fetchBounties() {
        try {
            const resp = await fetch(`${this.API_BASE}/bounties`);
            if (resp.ok) return await resp.json();
        } catch (e) { console.error("API failed, falling back to local", e); }
        return this.getBountiesLocal();
    },

    async publishBounty(bounty) {
        // 1. Save Local (Immediate UI feedback)
        const published = JSON.parse(localStorage.getItem(STORAGE_KEY_PUBLISHED)) || [];
        published.unshift(bounty);
        localStorage.setItem(STORAGE_KEY_PUBLISHED, JSON.stringify(published.slice(0, 24)));
        
        // 2. Push to API (Global persistence)
        try {
            await fetch(`${this.API_BASE}/bounties`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    id: bounty.id,
                    title: bounty.title,
                    description: bounty.spec || bounty.outcome,
                    budget: Number(bounty.budget),
                    bestBid: Number(bounty.budget),
                    bidsCount: 0,
                    status: "Open",
                    owner: bounty.human,
                    track: "Custom"
                })
            });
            console.log("Bounty synced to cloud");
        } catch (e) {
            console.warn("API sync failed, bounty exists only locally for now.");
        }
    },

    getWallet() {
        try {
            return JSON.parse(localStorage.getItem(STORAGE_KEY_WALLET)) || {
                connected: false,
                provider: "",
                address: "",
                chain: "",
                balance: ""
            };
        } catch (e) {
            return { connected: false };
        }
    },

    setWallet(state) {
        localStorage.setItem(STORAGE_KEY_WALLET, JSON.stringify(state));
    },

    getBountiesLocal() {
        try {
            const saved = JSON.parse(localStorage.getItem(STORAGE_KEY_BOUNTIES));
            const published = JSON.parse(localStorage.getItem(STORAGE_KEY_PUBLISHED)) || [];
            
            const pubMapped = published.map(p => ({
                id: p.id,
                track: "Custom",
                trackClass: "border-purple-300/30 text-purple-200",
                title: p.title,
                description: p.spec || p.outcome,
                budget: p.budget,
                bestBid: p.budget,
                bidsCount: 0,
                status: "Open",
                statusClass: "badge-open",
                bidStatus: `Posted by ${p.human}`
            }));

            return Array.isArray(saved) ? [...pubMapped, ...saved] : [...pubMapped, ...DEFAULT_BOUNTIES];
        } catch (e) {
            return DEFAULT_BOUNTIES;
        }
    },

    getBounties() {
        // Now returns local as a default, pages will call fetchBounties() if they want live
        return this.getBountiesLocal();
    },

    saveBounties(list) {
        // We only save the "market" bounties, published ones are in their own key
        const marketOnly = list.filter(b => !b.id.startsWith('pub-'));
        localStorage.setItem(STORAGE_KEY_BOUNTIES, JSON.stringify(marketOnly));
    },

    formatAddress(addr) {
        if (!addr) return "Not connected";
        return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
    }
};

// UI Micro-animations
document.addEventListener('DOMContentLoaded', () => {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) entry.target.classList.add('visible');
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
});
