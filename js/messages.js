
export const Messages = {
    key: 'englishbus_messages',

    init() {
        console.log("Messages System Initialized");
        this.injectPanelStructure();
        this.selfTestInjection(); // Self-test logic
        this.checkMessages();

        // Auto-check every 30 seconds
        setInterval(() => this.checkMessages(), 30000);
    },

    selfTestInjection() {
        const existing = localStorage.getItem(this.key);
        if (!existing || JSON.parse(existing).length === 0) {
            const demoMessage = [{
                id: Date.now(),
                sender: "Sistem",
                target: "all",
                title: "Sistem Başlatıldı",
                body: "Mesajlaşma servisi başarıyla aktive edildi. Artık bildirimleri buradan alabileceksiniz.",
                type: "success",
                date: new Date().toISOString(),
                read: false
            }];
            localStorage.setItem(this.key, JSON.stringify(demoMessage));
            console.log("Self-Test Message Injected");
        }
    },

    checkMessages() {
        const raw = localStorage.getItem(this.key);
        const messages = raw ? JSON.parse(raw) : [];
        this.updateBadge(messages);
        return messages;
    },

    updateBadge(messages) {
        const unreadCount = messages.filter(m => !m.read).length;
        const badge = document.getElementById('dashboard-msg-badge');

        if (badge) {
            if (unreadCount > 0) {
                badge.innerText = unreadCount;
                badge.classList.remove('hidden');
                badge.classList.add('flex', 'animate-pulse'); // Add animation to catch attention
            } else {
                badge.classList.add('hidden');
                badge.classList.remove('flex', 'animate-pulse');
            }
        }
    },

    togglePanel() {
        const panel = document.getElementById('messages-panel');
        if (!panel) return;

        panel.classList.toggle('hidden');
        if (!panel.classList.contains('hidden')) {
            this.renderMessages();
        }
    },

    renderMessages() {
        // Refresh data from storage
        const messages = this.checkMessages();
        // Sort: Newest first
        messages.sort((a, b) => new Date(b.date) - new Date(a.date));

        const list = document.getElementById('messages-list');
        if (!list) return;

        if (messages.length === 0) {
            list.innerHTML = `
                <div class="flex flex-col items-center justify-center py-10 text-gray-400">
                    <span class="material-symbols-outlined text-4xl mb-2 opacity-20">inbox</span>
                    <p>Henüz mesajınız yok</p>
                </div>`;
            return;
        }

        list.innerHTML = messages.map(msg => {
            const isUnread = !msg.read;
            const dateStr = new Date(msg.date).toLocaleDateString('tr-TR', {
                day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit'
            });

            // Type styling
            let icon = 'info';
            let colorClass = 'bg-blue-50 text-blue-500';

            if (msg.type === 'warning') { icon = 'warning'; colorClass = 'bg-orange-50 text-orange-500'; }
            if (msg.type === 'success') { icon = 'check_circle'; colorClass = 'bg-green-50 text-green-500'; }

            return `
                <div onclick="markMessageRead(${msg.id})" 
                     class="relative p-4 rounded-xl border transition-all cursor-pointer group hover:bg-gray-50 
                     ${isUnread ? 'bg-white border-brand-200 shadow-sm' : 'bg-gray-50/50 border-gray-100 opacity-60'}">
                    
                    ${isUnread ? '<div class="absolute top-4 right-4 size-2 bg-red-500 rounded-full ring-2 ring-white"></div>' : ''}
                    
                    <div class="flex items-start gap-3">
                        <div class="size-10 rounded-lg ${colorClass} flex items-center justify-center shrink-0">
                            <span class="material-symbols-outlined">${icon}</span>
                        </div>
                        <div class="flex-1 min-w-0">
                            <div class="flex justify-between items-start">
                                <p class="text-[10px] font-bold text-gray-400 uppercase tracking-wide">${msg.sender}</p>
                            </div>
                            <h4 class="font-bold text-gray-800 text-sm truncate pr-4">${msg.title}</h4>
                            <p class="text-xs text-gray-600 mt-1 line-clamp-2">${msg.body}</p>
                            <p class="text-[10px] text-gray-400 mt-2 text-right">${dateStr}</p>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    },

    markRead(id) {
        const raw = localStorage.getItem(this.key);
        if (!raw) return;

        let messages = JSON.parse(raw);
        const index = messages.findIndex(m => m.id === id);

        if (index !== -1 && !messages[index].read) {
            messages[index].read = true;
            localStorage.setItem(this.key, JSON.stringify(messages));

            // Re-render and update badge
            this.checkMessages();
            this.renderMessages();
        }
    },

    injectPanelStructure() {
        const panel = document.getElementById('messages-panel');
        // Check if the internal structure is missing (specifically the list container)
        if (panel && !document.getElementById('messages-list')) {
            panel.innerHTML = `
                <div class="bg-white w-full max-w-md rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[80vh] animate-bounce-soft mx-4">
                    <div class="p-4 border-b border-gray-100 flex justify-between items-center bg-gray-50">
                        <h3 class="font-bold text-gray-800 flex items-center gap-2">
                            <span class="material-symbols-outlined text-brand-500">mail</span> 
                            Bildirimler
                        </h3>
                        <button onclick="toggleMessagesPanel()" class="size-8 rounded-full hover:bg-gray-200 flex items-center justify-center text-gray-500 transition-colors">
                            <span class="material-symbols-outlined">close</span>
                        </button>
                    </div>
                    <div id="messages-list" class="flex-1 overflow-y-auto p-4 space-y-3 bg-white min-h-[200px]">
                        <!-- Rendered by JS -->
                    </div>
                    <div class="p-3 bg-gray-50 text-center border-t border-gray-100">
                         <button onclick="Messages.clearAll()" class="text-[10px] font-bold text-gray-400 hover:text-brand-500 uppercase tracking-wider transition-colors">Tümünü Okundu İşaretle</button>
                    </div>
                </div>
            `;
        }
    },

    clearAll() {
        if (!confirm('Tüm mesajları okundu işaretlemek istiyor musunuz?')) return;
        const raw = localStorage.getItem(this.key);
        if (raw) {
            let messages = JSON.parse(raw);
            messages.forEach(m => m.read = true);
            localStorage.setItem(this.key, JSON.stringify(messages));
            this.checkMessages();
            this.renderMessages();
        }
    }
};

// Global Exposure
window.Messages = Messages;
window.toggleMessagesPanel = () => Messages.togglePanel();
window.markMessageRead = (id) => Messages.markRead(id);

// Initialize on load if document is ready, or wait
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => Messages.init());
} else {
    Messages.init();
}
