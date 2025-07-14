/**
 * BITTEN Squad Chat Interface
 * Real-time tactical communications frontend
 * Handles WebSocket connections, message display, and user interactions
 */

class SquadChatInterface {
    constructor(userData) {
        this.userData = userData;
        this.socket = null;
        this.currentRoom = null;
        this.isConnected = false;
        this.typingTimer = null;
        this.typingUsers = new Set();
        this.messageHistory = new Map(); // room_id -> messages[]
        this.unreadCounts = new Map(); // room_id -> count
        this.isVisible = false;
        this.lastMessageTime = null;
        
        // Audio context for notifications
        this.audioContext = null;
        this.notificationSounds = new Map();
        
        // File upload handling
        this.maxFileSize = 10 * 1024 * 1024; // 10MB
        this.allowedFileTypes = [
            'image/png', 'image/jpeg', 'image/gif', 'image/webp',
            'application/pdf', 'text/plain', 'application/zip'
        ];
        
        // Initialize the interface
        this.init();
    }
    
    async init() {
        try {
            // Join chat session first
            await this.joinChatSession();
            
            // Initialize WebSocket connection
            this.initializeSocket();
            
            // Setup UI event listeners
            this.setupEventListeners();
            
            // Initialize audio notifications
            this.initializeAudio();
            
            // Setup visibility detection
            this.setupVisibilityDetection();
            
            console.log('BITTEN Squad Chat initialized for user:', this.userData.username);
            
        } catch (error) {
            console.error('Failed to initialize chat:', error);
            this.showError('Failed to connect to tactical communications');
        }
    }
    
    async joinChatSession() {
        try {
            const response = await fetch('/api/join_chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(this.userData)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            console.log('Chat session joined:', result);
            
        } catch (error) {
            console.error('Failed to join chat session:', error);
            throw error;
        }
    }
    
    initializeSocket() {
        // Initialize SocketIO connection
        this.socket = io({
            transports: ['websocket', 'polling'],
            autoConnect: true,
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionAttempts: 5,
            timeout: 20000
        });
        
        this.setupSocketEventHandlers();
    }
    
    setupSocketEventHandlers() {
        // Connection events
        this.socket.on('connect', () => {
            console.log('Connected to BITTEN tactical network');
            this.isConnected = true;
            this.updateConnectionStatus('SECURE', true);
            this.joinSquadRoom();
        });
        
        this.socket.on('disconnect', (reason) => {
            console.log('Disconnected from tactical network:', reason);
            this.isConnected = false;
            this.updateConnectionStatus('DISCONNECTED', false);
            this.showError('Connection to tactical network lost');
        });
        
        this.socket.on('connect_error', (error) => {
            console.error('Connection error:', error);
            this.updateConnectionStatus('CONNECTION ERROR', false);
            this.showError('Failed to establish secure connection');
        });
        
        // Chat events
        this.socket.on('room_history', (data) => {
            this.handleRoomHistory(data);
        });
        
        this.socket.on('new_message', (message) => {
            this.handleNewMessage(message);
        });
        
        this.socket.on('user_joined', (data) => {
            this.handleUserJoined(data);
        });
        
        this.socket.on('user_typing', (data) => {
            this.handleUserTyping(data);
        });
        
        this.socket.on('user_stopped_typing', (data) => {
            this.handleUserStoppedTyping(data);
        });
        
        this.socket.on('reaction_added', (data) => {
            this.handleReactionAdded(data);
        });
        
        this.socket.on('moderation_notice', (data) => {
            this.handleModerationNotice(data);
        });
        
        // Error handling
        this.socket.on('error', (error) => {
            console.error('Socket error:', error);
            this.showError(error.message || 'Unknown communication error');
        });
    }
    
    setupEventListeners() {
        const messageInput = document.getElementById('messageInput');
        const sendBtn = document.getElementById('sendBtn');
        const roomSelect = document.getElementById('roomSelect');
        
        // Message input events
        if (messageInput) {
            messageInput.addEventListener('input', () => {
                this.handleTyping();
                this.autoResizeTextarea(messageInput);
            });
            
            messageInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
            
            messageInput.addEventListener('paste', (e) => {
                this.handlePaste(e);
            });
        }
        
        // Send button
        if (sendBtn) {
            sendBtn.addEventListener('click', () => {
                this.sendMessage();
            });
        }
        
        // Room selection
        if (roomSelect) {
            roomSelect.addEventListener('change', (e) => {
                this.switchRoom(e.target.value);
            });
        }
        
        // File drag and drop
        this.setupDragAndDrop();
        
        // Context menu for messages
        this.setupMessageContextMenu();
    }
    
    setupDragAndDrop() {
        const chatContainer = document.getElementById('chatContainer');
        const fileUpload = document.getElementById('fileUpload');
        
        if (!chatContainer || !fileUpload) return;
        
        chatContainer.addEventListener('dragover', (e) => {
            e.preventDefault();
            fileUpload.classList.add('active');
        });
        
        chatContainer.addEventListener('dragleave', (e) => {
            if (!chatContainer.contains(e.relatedTarget)) {
                fileUpload.classList.remove('active');
            }
        });
        
        chatContainer.addEventListener('drop', (e) => {
            e.preventDefault();
            fileUpload.classList.remove('active');
            
            const files = Array.from(e.dataTransfer.files);
            if (files.length > 0) {
                this.handleFileUpload(files);
            }
        });
    }
    
    setupMessageContextMenu() {
        const messagesContainer = document.getElementById('messagesContainer');
        
        if (!messagesContainer) return;
        
        messagesContainer.addEventListener('contextmenu', (e) => {
            const messageElement = e.target.closest('.message');
            if (messageElement) {
                e.preventDefault();
                this.showMessageContextMenu(e, messageElement);
            }
        });
    }
    
    setupVisibilityDetection() {
        document.addEventListener('visibilitychange', () => {
            this.isVisible = !document.hidden;
            
            if (this.isVisible && this.currentRoom) {
                // Mark messages as read when user returns
                this.markMessagesAsRead(this.currentRoom);
            }
        });
    }
    
    initializeAudio() {
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // Create notification sounds
            this.createNotificationSound('message', [800, 600], 200);
            this.createNotificationSound('mention', [1000, 800, 1000], 150);
            this.createNotificationSound('error', [400, 300], 300);
            
        } catch (error) {
            console.warn('Audio notifications not available:', error);
        }
    }
    
    createNotificationSound(name, frequencies, duration) {
        if (!this.audioContext) return;
        
        const sound = {
            play: () => {
                const oscillator = this.audioContext.createOscillator();
                const gainNode = this.audioContext.createGain();
                
                oscillator.connect(gainNode);
                gainNode.connect(this.audioContext.destination);
                
                oscillator.type = 'sine';
                oscillator.frequency.setValueAtTime(frequencies[0], this.audioContext.currentTime);
                
                frequencies.forEach((freq, index) => {
                    if (index > 0) {
                        oscillator.frequency.setValueAtTime(
                            freq,
                            this.audioContext.currentTime + (duration * index / 1000)
                        );
                    }
                });
                
                gainNode.gain.setValueAtTime(0.1, this.audioContext.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(
                    0.01,
                    this.audioContext.currentTime + (duration * frequencies.length / 1000)
                );
                
                oscillator.start();
                oscillator.stop(this.audioContext.currentTime + (duration * frequencies.length / 1000));
            }
        };
        
        this.notificationSounds.set(name, sound);
    }
    
    joinSquadRoom() {
        if (!this.isConnected) return;
        
        const roomId = `squad_${this.userData.squad_id}`;
        this.currentRoom = roomId;
        
        this.socket.emit('join_squad_room', {
            squad_id: this.userData.squad_id
        });
        
        // Update room selector
        this.updateRoomSelector();
        
        console.log(`Joined squad room: ${roomId}`);
    }
    
    updateRoomSelector() {
        const roomSelect = document.getElementById('roomSelect');
        if (!roomSelect) return;
        
        // Clear existing options
        roomSelect.innerHTML = '';
        
        // Add current squad room
        const option = document.createElement('option');
        option.value = this.currentRoom;
        option.textContent = `Squad ${this.userData.squad_id.toUpperCase()}`;
        option.selected = true;
        roomSelect.appendChild(option);
    }
    
    updateConnectionStatus(status, isConnected) {
        const statusIndicator = document.getElementById('statusIndicator');
        const connectionStatus = document.getElementById('connectionStatus');
        
        if (statusIndicator) {
            statusIndicator.className = `status-indicator ${isConnected ? '' : 'offline'}`;
        }
        
        if (connectionStatus) {
            connectionStatus.textContent = status;
        }
    }
    
    handleRoomHistory(data) {
        const { room_id, messages } = data;
        
        // Store messages in history
        this.messageHistory.set(room_id, messages);
        
        // Display messages if this is the current room
        if (room_id === this.currentRoom) {
            this.displayMessages(messages);
        }
        
        // Hide loading indicator
        const loadingIndicator = document.getElementById('loadingIndicator');
        if (loadingIndicator) {
            loadingIndicator.style.display = 'none';
        }
        
        console.log(`Loaded ${messages.length} messages for room ${room_id}`);
    }
    
    handleNewMessage(message) {
        // Add to message history
        if (!this.messageHistory.has(message.room_id)) {
            this.messageHistory.set(message.room_id, []);
        }
        
        this.messageHistory.get(message.room_id).push(message);
        
        // Display if current room
        if (message.room_id === this.currentRoom) {
            this.appendMessage(message);
            this.scrollToBottom();
        } else {
            // Increment unread count
            const currentCount = this.unreadCounts.get(message.room_id) || 0;
            this.unreadCounts.set(message.room_id, currentCount + 1);
        }
        
        // Play notification sound if not own message
        if (message.user_id !== this.userData.user_id && !this.isVisible) {
            this.playNotificationSound('message');
            this.showBrowserNotification(message);
        }
        
        // Check for mentions
        if (this.isMentioned(message)) {
            this.playNotificationSound('mention');
            this.highlightMention(message);
        }
        
        this.lastMessageTime = new Date(message.timestamp);
    }
    
    handleUserJoined(data) {
        this.addSystemMessage(`${data.username} joined the tactical channel`, data.timestamp);
    }
    
    handleUserTyping(data) {
        if (data.user_id === this.userData.user_id) return;
        
        this.typingUsers.add(data.username);
        this.updateTypingIndicator();
    }
    
    handleUserStoppedTyping(data) {
        this.typingUsers.delete(data.username);
        this.updateTypingIndicator();
    }
    
    handleReactionAdded(data) {
        const messageElement = document.querySelector(`[data-message-id="${data.message_id}"]`);
        if (messageElement) {
            this.updateMessageReactions(messageElement, data.reactions);
        }
    }
    
    handleModerationNotice(data) {
        this.showError(`You have been ${data.action}: ${data.reason}`, 'warning');
    }
    
    sendMessage() {
        const messageInput = document.getElementById('messageInput');
        if (!messageInput || !this.isConnected || !this.currentRoom) return;
        
        const content = messageInput.value.trim();
        if (!content) return;
        
        // Clear typing indicator
        this.stopTyping();
        
        // Send message
        this.socket.emit('send_message', {
            room_id: this.currentRoom,
            content: content,
            type: 'text',
            metadata: {
                client_timestamp: new Date().toISOString()
            }
        });
        
        // Clear input
        messageInput.value = '';
        messageInput.style.height = 'auto';
        
        // Focus back to input
        messageInput.focus();
    }
    
    handleTyping() {
        if (!this.isConnected || !this.currentRoom) return;
        
        // Send typing start
        this.socket.emit('typing_start', {
            room_id: this.currentRoom
        });
        
        // Clear existing timer
        if (this.typingTimer) {
            clearTimeout(this.typingTimer);
        }
        
        // Set timer to stop typing
        this.typingTimer = setTimeout(() => {
            this.stopTyping();
        }, 3000);
    }
    
    stopTyping() {
        if (this.typingTimer) {
            clearTimeout(this.typingTimer);
            this.typingTimer = null;
        }
        
        if (this.isConnected && this.currentRoom) {
            this.socket.emit('typing_stop', {
                room_id: this.currentRoom
            });
        }
    }
    
    displayMessages(messages) {
        const messagesContainer = document.getElementById('messagesContainer');
        if (!messagesContainer) return;
        
        // Clear existing messages
        messagesContainer.innerHTML = '';
        
        // Add all messages
        messages.forEach(message => {
            this.appendMessage(message, false);
        });
        
        // Scroll to bottom
        this.scrollToBottom();
    }
    
    appendMessage(message, animate = true) {
        const messagesContainer = document.getElementById('messagesContainer');
        if (!messagesContainer) return;
        
        const messageElement = this.createMessageElement(message);
        
        if (animate) {
            messageElement.style.opacity = '0';
            messageElement.style.transform = 'translateX(-20px)';
        }
        
        messagesContainer.appendChild(messageElement);
        
        if (animate) {
            // Trigger animation
            requestAnimationFrame(() => {
                messageElement.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                messageElement.style.opacity = '1';
                messageElement.style.transform = 'translateX(0)';
            });
        }
    }
    
    createMessageElement(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = this.getMessageClasses(message);
        messageDiv.setAttribute('data-message-id', message.message_id);
        messageDiv.setAttribute('data-user-id', message.user_id);
        
        const messageHeader = document.createElement('div');
        messageHeader.className = 'message-header';
        
        const sender = document.createElement('div');
        sender.className = 'message-sender';
        
        const senderName = document.createElement('span');
        senderName.textContent = message.callsign;
        sender.appendChild(senderName);
        
        // Add rank indicator
        if (message.user_id !== 'SYSTEM') {
            const rankBadge = document.createElement('span');
            rankBadge.className = 'rank-indicator';
            rankBadge.textContent = this.getUserRank(message.user_id);
            sender.appendChild(rankBadge);
        }
        
        const timestamp = document.createElement('div');
        timestamp.className = 'message-time';
        timestamp.textContent = this.formatTimestamp(message.timestamp);
        
        messageHeader.appendChild(sender);
        messageHeader.appendChild(timestamp);
        
        const content = document.createElement('div');
        content.className = 'message-content';
        content.innerHTML = this.formatMessageContent(message.content, message.message_type);
        
        messageDiv.appendChild(messageHeader);
        messageDiv.appendChild(content);
        
        // Add reactions if any
        if (message.reactions && Object.keys(message.reactions).length > 0) {
            const reactionsDiv = this.createReactionsElement(message.reactions);
            messageDiv.appendChild(reactionsDiv);
        }
        
        return messageDiv;
    }
    
    getMessageClasses(message) {
        let classes = ['message'];
        
        if (message.user_id === this.userData.user_id) {
            classes.push('own');
        }
        
        if (message.message_type === 'system') {
            classes.push('system');
        }
        
        if (this.isMentioned(message)) {
            classes.push('mentioned');
        }
        
        return classes.join(' ');
    }
    
    formatMessageContent(content, messageType) {
        switch (messageType) {
            case 'text':
                return this.escapeHtml(content)
                    .replace(/\n/g, '<br>')
                    .replace(/@(\w+)/g, '<span class="mention">@$1</span>');
                    
            case 'image':
                return `<img src="${content}" alt="Shared image" style="max-width: 200px; border-radius: 5px;">`;
                
            case 'file':
                return `<a href="${content}" target="_blank" class="file-link"><i class="fas fa-file"></i> Shared file</a>`;
                
            case 'system':
                return `<i class="fas fa-info-circle"></i> ${this.escapeHtml(content)}`;
                
            default:
                return this.escapeHtml(content);
        }
    }
    
    createReactionsElement(reactions) {
        const reactionsDiv = document.createElement('div');
        reactionsDiv.className = 'message-reactions';
        
        for (const [emoji, userIds] of Object.entries(reactions)) {
            if (userIds.length > 0) {
                const reactionSpan = document.createElement('span');
                reactionSpan.className = 'reaction';
                reactionSpan.textContent = `${emoji} ${userIds.length}`;
                reactionSpan.title = `Reacted by: ${userIds.join(', ')}`;
                
                // Highlight if current user reacted
                if (userIds.includes(this.userData.user_id)) {
                    reactionSpan.classList.add('own-reaction');
                }
                
                reactionSpan.addEventListener('click', () => {
                    this.toggleReaction(reactions.message_id, emoji);
                });
                
                reactionsDiv.appendChild(reactionSpan);
            }
        }
        
        return reactionsDiv;
    }
    
    updateMessageReactions(messageElement, reactions) {
        const existingReactions = messageElement.querySelector('.message-reactions');
        if (existingReactions) {
            existingReactions.remove();
        }
        
        if (reactions && Object.keys(reactions).length > 0) {
            const reactionsDiv = this.createReactionsElement(reactions);
            messageElement.appendChild(reactionsDiv);
        }
    }
    
    updateTypingIndicator() {
        const messagesContainer = document.getElementById('messagesContainer');
        if (!messagesContainer) return;
        
        // Remove existing typing indicator
        const existingIndicator = messagesContainer.querySelector('.typing-indicator');
        if (existingIndicator) {
            existingIndicator.remove();
        }
        
        // Add new indicator if users are typing
        if (this.typingUsers.size > 0) {
            const typingDiv = document.createElement('div');
            typingDiv.className = 'typing-indicator';
            
            const userList = Array.from(this.typingUsers).slice(0, 3).join(', ');
            const verb = this.typingUsers.size === 1 ? 'is' : 'are';
            
            typingDiv.innerHTML = `${userList} ${verb} typing<span class="typing-dots">...</span>`;
            
            messagesContainer.appendChild(typingDiv);
            this.scrollToBottom();
        }
    }
    
    addSystemMessage(content, timestamp) {
        const message = {
            message_id: `system_${Date.now()}`,
            user_id: 'SYSTEM',
            username: 'BITTEN Command',
            callsign: 'HQ',
            squad_id: 'SYSTEM',
            room_id: this.currentRoom,
            content: content,
            message_type: 'system',
            timestamp: timestamp || new Date().toISOString(),
            reactions: {}
        };
        
        this.appendMessage(message);
        this.scrollToBottom();
    }
    
    scrollToBottom() {
        const messagesContainer = document.getElementById('messagesContainer');
        if (messagesContainer) {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    }
    
    autoResizeTextarea(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 100) + 'px';
    }
    
    handleFileUpload(files) {
        if (!this.isConnected || !this.currentRoom) {
            this.showError('Cannot upload files: not connected');
            return;
        }
        
        Array.from(files).forEach(file => {
            // Validate file
            if (!this.validateFile(file)) {
                return;
            }
            
            // Upload file
            this.uploadFile(file);
        });
    }
    
    validateFile(file) {
        if (file.size > this.maxFileSize) {
            this.showError(`File too large: ${file.name} (max ${this.maxFileSize / 1024 / 1024}MB)`);
            return false;
        }
        
        if (!this.allowedFileTypes.includes(file.type)) {
            this.showError(`File type not allowed: ${file.name}`);
            return false;
        }
        
        return true;
    }
    
    async uploadFile(file) {
        try {
            // Create form data
            const formData = new FormData();
            formData.append('file', file);
            formData.append('room_id', this.currentRoom);
            formData.append('user_id', this.userData.user_id);
            
            // Show upload progress
            this.showProgress(`Uploading ${file.name}...`);
            
            // Upload file
            const response = await fetch('/api/upload_file', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`Upload failed: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            // Send file message
            this.socket.emit('send_message', {
                room_id: this.currentRoom,
                content: result.file_url,
                type: file.type.startsWith('image/') ? 'image' : 'file',
                metadata: {
                    filename: file.name,
                    filesize: file.size,
                    filetype: file.type
                }
            });
            
            this.hideProgress();
            this.showSuccess(`${file.name} uploaded successfully`);
            
        } catch (error) {
            console.error('File upload error:', error);
            this.hideProgress();
            this.showError(`Failed to upload ${file.name}: ${error.message}`);
        }
    }
    
    handlePaste(event) {
        const items = event.clipboardData?.items;
        if (!items) return;
        
        for (const item of items) {
            if (item.type.startsWith('image/')) {
                event.preventDefault();
                const file = item.getAsFile();
                if (file) {
                    this.handleFileUpload([file]);
                }
                break;
            }
        }
    }
    
    showMessageContextMenu(event, messageElement) {
        // Create context menu for message actions
        const menu = document.createElement('div');
        menu.className = 'context-menu';
        menu.style.cssText = `
            position: fixed;
            top: ${event.clientY}px;
            left: ${event.clientX}px;
            background: var(--bitten-primary);
            border: 1px solid var(--bitten-border);
            border-radius: 5px;
            padding: 5px 0;
            z-index: 1002;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
        `;
        
        const messageId = messageElement.getAttribute('data-message-id');
        const userId = messageElement.getAttribute('data-user-id');
        
        // Add menu items
        const menuItems = [
            {
                text: 'React with 👍',
                action: () => this.addReaction(messageId, '👍')
            },
            {
                text: 'React with ❤️',
                action: () => this.addReaction(messageId, '❤️')
            },
            {
                text: 'Copy Message',
                action: () => this.copyMessage(messageElement)
            }
        ];
        
        // Add moderation options if user has permissions
        if (this.hasModeratorPermissions() && userId !== this.userData.user_id) {
            menuItems.push(
                { text: '---', divider: true },
                {
                    text: 'Mute User',
                    action: () => this.moderateUser(userId, 'mute', 300)
                },
                {
                    text: 'Report User',
                    action: () => this.moderateUser(userId, 'report', 0)
                }
            );
        }
        
        menuItems.forEach(item => {
            if (item.divider) {
                const divider = document.createElement('hr');
                divider.style.cssText = 'margin: 5px 0; border: 0; border-top: 1px solid var(--bitten-border);';
                menu.appendChild(divider);
            } else {
                const menuItem = document.createElement('div');
                menuItem.className = 'context-menu-item';
                menuItem.textContent = item.text;
                menuItem.style.cssText = `
                    padding: 8px 15px;
                    cursor: pointer;
                    color: var(--bitten-text);
                    font-size: 0.9em;
                `;
                
                menuItem.addEventListener('click', () => {
                    item.action();
                    document.body.removeChild(menu);
                });
                
                menuItem.addEventListener('mouseenter', () => {
                    menuItem.style.background = 'rgba(0, 255, 0, 0.1)';
                });
                
                menuItem.addEventListener('mouseleave', () => {
                    menuItem.style.background = 'transparent';
                });
                
                menu.appendChild(menuItem);
            }
        });
        
        document.body.appendChild(menu);
        
        // Remove menu when clicking outside
        const removeMenu = (e) => {
            if (!menu.contains(e.target)) {
                document.body.removeChild(menu);
                document.removeEventListener('click', removeMenu);
            }
        };
        
        setTimeout(() => {
            document.addEventListener('click', removeMenu);
        }, 100);
    }
    
    addReaction(messageId, emoji) {
        if (!this.isConnected) return;
        
        this.socket.emit('add_reaction', {
            message_id: messageId,
            emoji: emoji
        });
    }
    
    copyMessage(messageElement) {
        const contentElement = messageElement.querySelector('.message-content');
        if (contentElement) {
            const text = contentElement.textContent;
            navigator.clipboard.writeText(text).then(() => {
                this.showSuccess('Message copied to clipboard');
            }).catch(() => {
                this.showError('Failed to copy message');
            });
        }
    }
    
    moderateUser(userId, action, duration) {
        if (!this.isConnected) return;
        
        const reason = prompt(`Reason for ${action}:`);
        if (reason === null) return;
        
        this.socket.emit('moderate_user', {
            target_user_id: userId,
            action: action,
            duration: duration,
            reason: reason
        });
    }
    
    // Utility methods
    
    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        
        if (diff < 60000) { // Less than 1 minute
            return 'now';
        } else if (diff < 3600000) { // Less than 1 hour
            return `${Math.floor(diff / 60000)}m`;
        } else if (diff < 86400000) { // Less than 1 day
            return `${Math.floor(diff / 3600000)}h`;
        } else {
            return date.toLocaleDateString();
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    isMentioned(message) {
        const content = message.content.toLowerCase();
        const username = this.userData.username.toLowerCase();
        const callsign = this.userData.callsign.toLowerCase();
        
        return content.includes(`@${username}`) || 
               content.includes(`@${callsign}`) ||
               content.includes('@everyone') ||
               content.includes('@squad');
    }
    
    getUserRank(userId) {
        // In a real implementation, this would fetch from user data
        if (userId === this.userData.user_id) {
            return this.userData.rank;
        }
        return 'RECRUIT'; // Default rank
    }
    
    hasModeratorPermissions() {
        return ['commander', 'sergeant'].includes(this.userData.role?.toLowerCase());
    }
    
    playNotificationSound(soundName) {
        if (this.notificationSounds.has(soundName)) {
            try {
                this.notificationSounds.get(soundName).play();
            } catch (error) {
                console.warn('Failed to play notification sound:', error);
            }
        }
    }
    
    showBrowserNotification(message) {
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(`${message.callsign}: ${message.content.substring(0, 50)}...`, {
                icon: '/static/images/bitten-icon.png',
                badge: '/static/images/bitten-badge.png',
                tag: 'bitten-chat',
                renotify: false
            });
        }
    }
    
    markMessagesAsRead(roomId) {
        this.unreadCounts.set(roomId, 0);
        // Update UI to reflect read status
    }
    
    // UI Helper methods
    
    showError(message, type = 'error') {
        this.showNotification(message, type);
        this.playNotificationSound('error');
    }
    
    showSuccess(message) {
        this.showNotification(message, 'success');
    }
    
    showProgress(message) {
        // Implementation for showing progress
        const notification = this.showNotification(message, 'info');
        notification.id = 'progress-notification';
        return notification;
    }
    
    hideProgress() {
        const notification = document.getElementById('progress-notification');
        if (notification) {
            notification.remove();
        }
    }
    
    showNotification(message, type = 'info') {
        const notificationArea = document.getElementById('notificationArea');
        if (!notificationArea) return;
        
        const notification = document.createElement('div');
        notification.className = 'notification';
        notification.textContent = message;
        
        // Set color based on type
        switch (type) {
            case 'error':
                notification.style.background = 'var(--bitten-danger)';
                break;
            case 'success':
                notification.style.background = 'var(--bitten-success)';
                break;
            case 'warning':
                notification.style.background = 'var(--bitten-warning)';
                break;
            default:
                notification.style.background = 'var(--bitten-accent)';
        }
        
        notificationArea.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
        
        return notification;
    }
}

// Request notification permission on load
if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SquadChatInterface;
} else if (typeof window !== 'undefined') {
    window.SquadChatInterface = SquadChatInterface;
}