/**
 * WhatsApp-style Chat JavaScript Module
 * Provides real-time chat functionality with WhatsApp-like UI
 */

class WhatsAppChat {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            currentUserId: options.currentUserId || 'user1',
            otherUserId: options.otherUserId || 'user2',
            currentUserName: options.currentUserName || 'You',
            otherUserName: options.otherUserName || 'Other User',
            socketUrl: options.socketUrl || null,
            onMessageSent: options.onMessageSent || (() => {}),
            onMessageReceived: options.onMessageReceived || (() => {}),
            ...options
        };
        
        this.messages = [];
        this.isConnected = false;
        this.isTyping = false;
        
        this.init();
    }

    init() {
        this.render();
        this.bindEvents();
        this.connectSocket();
    }

    render() {
        this.container.innerHTML = `
            <div class="whatsapp-chat-container">
                <!-- Chat Header -->
                <div class="chat-header">
                    <div class="avatar">${this.getInitials(this.options.otherUserName)}</div>
                    <div class="info">
                        <div class="name">${this.options.otherUserName}</div>
                        <div class="status">
                            <span class="status-dot ${this.options.isOnline ? '' : 'offline'}"></span>
                            <span class="status-text">${this.options.isOnline ? 'Online' : 'Offline'}</span>
                        </div>
                    </div>
                    <div class="chat-input-actions">
                        <button class="icon-button video-call" title="Video Call">
                            <i class="fas fa-video"></i>
                        </button>
                        <button class="icon-button voice-call" title="Voice Call">
                            <i class="fas fa-phone"></i>
                        </button>
                        <button class="icon-button more-options" title="More Options">
                            <i class="fas fa-ellipsis-v"></i>
                        </button>
                    </div>
                </div>

                <!-- Chat Messages -->
                <div class="chat-messages" id="chatMessages-${this.container.id}">
                    <!-- Messages will be rendered here -->
                </div>

                <!-- Chat Input -->
                <div class="chat-input-container">
                    <button class="icon-button attach-file" title="Attach File">
                        <i class="fas fa-plus"></i>
                    </button>
                    <div class="chat-input-wrapper" style="flex: 1; position: relative;">
                        <textarea 
                            class="chat-input" 
                            id="messageInput-${this.container.id}"
                            placeholder="Type a message..."
                            rows="1"></textarea>
                        <button class="icon-button emoji-picker" title="Emoji">
                            <i class="fas fa-smile"></i>
                        </button>
                    </div>
                    <button class="icon-button voice-record" title="Voice Record">
                        <i class="fas fa-microphone"></i>
                    </button>
                    <button class="icon-button send-message" title="Send Message">
                        <i class="fas fa-paper-plane"></i>
                    </button>
                </div>
            </div>
        `;

        this.messagesContainer = document.getElementById(`chatMessages-${this.container.id}`);
        this.messageInput = document.getElementById(`messageInput-${this.container.id}`);
        this.sendButton = this.container.querySelector('.send-message');
        this.voiceButton = this.container.querySelector('.voice-record');
        this.statusDot = this.container.querySelector('.status-dot');
        this.statusText = this.container.querySelector('.status-text');
    }

    bindEvents() {
        // Send message
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Enter to send, Shift+Enter for new line
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Auto-resize textarea
        this.messageInput.addEventListener('input', () => {
            this.autoResizeTextarea();
            this.handleTyping();
        });

        // Voice recording
        this.voiceButton.addEventListener('mousedown', () => this.startVoiceRecording());
        this.voiceButton.addEventListener('mouseup', () => this.stopVoiceRecording());
        this.voiceButton.addEventListener('mouseleave', () => this.stopVoiceRecording());

        // Touch events for mobile
        this.voiceButton.addEventListener('touchstart', (e) => {
            e.preventDefault();
            this.startVoiceRecording();
        });
        this.voiceButton.addEventListener('touchend', (e) => {
            e.preventDefault();
            this.stopVoiceRecording();
        });

        // File attachment
        this.container.querySelector('.attach-file').addEventListener('click', () => {
            this.showFilePicker();
        });

        // Emoji picker
        this.container.querySelector('.emoji-picker').addEventListener('click', () => {
            this.showEmojiPicker();
        });

        // Video/Voice calls
        this.container.querySelector('.video-call').addEventListener('click', () => {
            this.startVideoCall();
        });

        this.container.querySelector('.voice-call').addEventListener('click', () => {
            this.startVoiceCall();
        });

        // More options
        this.container.querySelector('.more-options').addEventListener('click', () => {
            this.showMoreOptions();
        });

        // Scroll to bottom on new messages
        this.messagesContainer.addEventListener('DOMNodeInserted', () => {
            this.scrollToBottom();
        });
    }

    connectSocket() {
        if (!this.options.socketUrl) return;

        try {
            this.socket = io(this.options.socketUrl);
            
            this.socket.on('connect', () => {
                this.isConnected = true;
                this.updateConnectionStatus();
                console.log('Connected to chat server');
            });

            this.socket.on('disconnect', () => {
                this.isConnected = false;
                this.updateConnectionStatus();
                console.log('Disconnected from chat server');
            });

            this.socket.on('new_message', (data) => {
                this.receiveMessage(data);
            });

            this.socket.on('user_typing', (data) => {
                this.showTypingIndicator(data.userId);
            });

            this.socket.on('user_stop_typing', (data) => {
                this.hideTypingIndicator(data.userId);
            });

            this.socket.on('user_status', (data) => {
                this.updateUserStatus(data);
            });

        } catch (error) {
            console.error('Failed to connect to socket:', error);
        }
    }

    sendMessage() {
        const text = this.messageInput.value.trim();
        if (!text) return;

        const message = {
            id: Date.now(),
            text: text,
            senderId: this.options.currentUserId,
            receiverId: this.options.otherUserId,
            timestamp: new Date().toISOString(),
            type: 'text',
            status: 'sent'
        };

        // Add to local messages
        this.addMessage(message);
        
        // Clear input
        this.messageInput.value = '';
        this.autoResizeTextarea();

        // Send via socket if connected
        if (this.socket && this.isConnected) {
            this.socket.emit('send_message', {
                message: text,
                receiverId: this.options.otherUserId
            });
        }

        // Update send button
        this.updateSendButton();

        // Call callback
        this.options.onMessageSent(message);
    }

    receiveMessage(data) {
        const message = {
            id: data.id || Date.now(),
            text: data.message,
            senderId: data.sender_id,
            receiverId: data.receiver_id,
            timestamp: data.timestamp || new Date().toISOString(),
            type: data.type || 'text',
            status: 'delivered'
        };

        this.addMessage(message);
        this.options.onMessageReceived(message);

        // Mark as read
        if (this.socket && this.isConnected) {
            this.socket.emit('mark_read', { messageId: message.id });
        }
    }

    addMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${message.senderId === this.options.currentUserId ? 'sent' : 'received'}`;
        messageDiv.setAttribute('data-message-id', message.id);

        const avatar = document.createElement('div');
        avatar.className = 'avatar';
        avatar.textContent = this.getInitials(
            message.senderId === this.options.currentUserId ? 
            this.options.currentUserName : 
            this.options.otherUserName
        );

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        // Handle different message types
        let messageBubble;
        switch (message.type) {
            case 'image':
                messageBubble = this.createImageMessage(message);
                break;
            case 'voice':
                messageBubble = this.createVoiceMessage(message);
                break;
            case 'location':
                messageBubble = this.createLocationMessage(message);
                break;
            case 'file':
                messageBubble = this.createFileMessage(message);
                break;
            default:
                messageBubble = this.createTextMessage(message);
        }

        const messageTime = document.createElement('div');
        messageTime.className = 'message-time';
        messageTime.textContent = this.formatTime(message.timestamp);

        // Add read receipt for sent messages
        if (message.senderId === this.options.currentUserId) {
            const readReceipt = this.createReadReceipt(message.status);
            messageTime.appendChild(readReceipt);
        }

        messageContent.appendChild(messageBubble);
        messageContent.appendChild(messageTime);

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);

        this.messagesContainer.appendChild(messageDiv);
        this.messages.push(message);

        this.scrollToBottom();
    }

    createTextMessage(message) {
        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        bubble.textContent = message.text;
        return bubble;
    }

    createImageMessage(message) {
        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        bubble.innerHTML = `
            <img src="${message.imageUrl}" alt="Image" style="max-width: 200px; border-radius: 4px;">
            <div>${message.text || ''}</div>
        `;
        return bubble;
    }

    createVoiceMessage(message) {
        const bubble = document.createElement('div');
        bubble.className = 'voice-message';
        bubble.innerHTML = `
            <button class="icon-button play-btn">
                <i class="fas fa-play"></i>
            </button>
            <div class="voice-waveform">
                ${this.createWaveform()}
            </div>
            <div class="voice-duration">${message.duration || '0:00'}</div>
        `;
        return bubble;
    }

    createLocationMessage(message) {
        const bubble = document.createElement('div');
        bubble.className = 'location-message';
        bubble.innerHTML = `
            <div class="location-preview">
                <i class="fas fa-map-marker-alt fa-2x"></i>
            </div>
            <div class="location-text">${message.text || 'Live Location'}</div>
        `;
        return bubble;
    }

    createFileMessage(message) {
        const bubble = document.createElement('div');
        bubble.className = 'attachment-preview';
        bubble.innerHTML = `
            <div class="attachment-icon">
                <i class="fas fa-file-alt"></i>
            </div>
            <div class="attachment-info">
                <div class="attachment-name">${message.fileName || 'Document'}</div>
                <div class="attachment-size">${message.fileSize || 'Unknown size'}</div>
            </div>
        `;
        return bubble;
    }

    createReadReceipt(status) {
        const receipt = document.createElement('span');
        receipt.className = 'read-receipt';
        
        if (status === 'read') {
            receipt.classList.add('read');
            receipt.innerHTML = '<i class="fas fa-check"></i><i class="fas fa-check"></i>';
        } else {
            receipt.innerHTML = '<i class="fas fa-check"></i>';
        }
        
        return receipt;
    }

    createWaveform() {
        let waveform = '';
        for (let i = 0; i < 5; i++) {
            waveform += `<div class="wave-bar"></div>`;
        }
        return waveform;
    }

    showTypingIndicator(userId) {
        if (userId !== this.options.otherUserId) return;

        // Remove existing typing indicator
        this.hideTypingIndicator(userId);

        // Add new typing indicator
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message received typing-message';
        typingDiv.innerHTML = `
            <div class="avatar">${this.getInitials(this.options.otherUserName)}</div>
            <div class="message-content">
                <div class="typing-indicator active">
                    <div class="typing-dots">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    </div>
                </div>
            </div>
        `;

        this.messagesContainer.appendChild(typingDiv);
        this.scrollToBottom();
    }

    hideTypingIndicator(userId) {
        const typingMessage = this.messagesContainer.querySelector('.typing-message');
        if (typingMessage) {
            typingMessage.remove();
        }
    }

    handleTyping() {
        if (!this.isTyping && this.messageInput.value.trim()) {
            this.isTyping = true;
            if (this.socket && this.isConnected) {
                this.socket.emit('typing', { receiverId: this.options.otherUserId });
            }
        }

        clearTimeout(this.typingTimeout);
        this.typingTimeout = setTimeout(() => {
            this.isTyping = false;
            if (this.socket && this.isConnected) {
                this.socket.emit('stop_typing', { receiverId: this.options.otherUserId });
            }
        }, 1000);
    }

    autoResizeTextarea() {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 100) + 'px';
        this.updateSendButton();
    }

    updateSendButton() {
        const hasText = this.messageInput.value.trim().length > 0;
        
        if (hasText) {
            this.sendButton.style.display = 'flex';
            this.voiceButton.style.display = 'none';
        } else {
            this.sendButton.style.display = 'none';
            this.voiceButton.style.display = 'flex';
        }
    }

    updateConnectionStatus() {
        if (this.isConnected) {
            this.statusDot.classList.remove('offline');
            this.statusText.textContent = 'Online';
        } else {
            this.statusDot.classList.add('offline');
            this.statusText.textContent = 'Connecting...';
        }
    }

    updateUserStatus(status) {
        if (status[this.options.otherUserId]) {
            const userStatus = status[this.options.otherUserId];
            if (userStatus.isOnline) {
                this.statusDot.classList.remove('offline');
                this.statusText.textContent = 'Online';
            } else {
                this.statusDot.classList.add('offline');
                this.statusText.textContent = 'Last seen ' + this.formatTime(userStatus.last_seen);
            }
        }
    }

    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    formatTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    getInitials(name) {
        return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
    }

    // Media handling methods
    showFilePicker() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*,video/*,.pdf,.doc,.docx';
        input.onchange = (e) => this.handleFileSelect(e.target.files[0]);
        input.click();
    }

    handleFileSelect(file) {
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (e) => {
            if (file.type.startsWith('image/')) {
                this.sendImageMessage(e.target.result, file.name);
            } else {
                this.sendFileMessage(file.name, file.size);
            }
        };
        reader.readAsDataURL(file);
    }

    sendImageMessage(imageUrl, fileName) {
        const message = {
            id: Date.now(),
            imageUrl: imageUrl,
            fileName: fileName,
            senderId: this.options.currentUserId,
            receiverId: this.options.otherUserId,
            timestamp: new Date().toISOString(),
            type: 'image',
            status: 'sent'
        };

        this.addMessage(message);
        this.options.onMessageSent(message);
    }

    sendFileMessage(fileName, fileSize) {
        const message = {
            id: Date.now(),
            fileName: fileName,
            fileSize: this.formatFileSize(fileSize),
            senderId: this.options.currentUserId,
            receiverId: this.options.otherUserId,
            timestamp: new Date().toISOString(),
            type: 'file',
            status: 'sent'
        };

        this.addMessage(message);
        this.options.onMessageSent(message);
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Voice recording
    startVoiceRecording() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            alert('Voice recording is not supported in your browser');
            return;
        }

        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                this.mediaRecorder = new MediaRecorder(stream);
                this.mediaRecorder.start();
                this.isRecording = true;
                this.voiceButton.classList.add('recording');
            })
            .catch(err => {
                console.error('Error accessing microphone:', err);
                alert('Could not access microphone');
            });
    }

    stopVoiceRecording() {
        if (!this.isRecording || !this.mediaRecorder) return;

        this.mediaRecorder.stop();
        this.isRecording = false;
        this.voiceButton.classList.remove('recording');

        this.mediaRecorder.ondataavailable = (event) => {
            const audioBlob = event.data;
            this.sendVoiceMessage(audioBlob);
        };
    }

    sendVoiceMessage(audioBlob) {
        const audioUrl = URL.createObjectURL(audioBlob);
        const duration = Math.floor(audioBlob.size / 1000); // Rough estimate
        
        const message = {
            id: Date.now(),
            audioUrl: audioUrl,
            duration: `0:${duration.toString().padStart(2, '0')}`,
            senderId: this.options.currentUserId,
            receiverId: this.options.otherUserId,
            timestamp: new Date().toISOString(),
            type: 'voice',
            status: 'sent'
        };

        this.addMessage(message);
        this.options.onMessageSent(message);
    }

    // UI methods
    showEmojiPicker() {
        // Simple emoji picker implementation
        const emojis = ['😀', '😂', '😍', '🤔', '😎', '😢', '😡', '👍', '👎', '❤️', '🎉', '🔥', '💯', '🙏', '💪'];
        const emojiPicker = document.createElement('div');
        emojiPicker.className = 'emoji-picker';
        emojiPicker.style.cssText = `
            position: absolute;
            bottom: 60px;
            left: 20px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 10px;
            display: grid;
            grid-template-columns: repeat(8, 1fr);
            gap: 5px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            z-index: 1000;
        `;

        emojis.forEach(emoji => {
            const emojiButton = document.createElement('button');
            emojiButton.textContent = emoji;
            emojiButton.style.cssText = `
                font-size: 20px;
                border: none;
                background: none;
                cursor: pointer;
                padding: 5px;
                border-radius: 4px;
            `;
            emojiButton.onmouseover = () => emojiButton.style.background = '#f0f0f0';
            emojiButton.onmouseout = () => emojiButton.style.background = 'none';
            emojiButton.onclick = () => {
                this.messageInput.value += emoji;
                this.messageInput.focus();
                document.body.removeChild(emojiPicker);
            };
            emojiPicker.appendChild(emojiButton);
        });

        document.body.appendChild(emojiPicker);

        // Close on outside click
        setTimeout(() => {
            document.addEventListener('click', function closeEmojiPicker(e) {
                if (!emojiPicker.contains(e.target)) {
                    document.body.removeChild(emojiPicker);
                    document.removeEventListener('click', closeEmojiPicker);
                }
            });
        }, 100);
    }

    startVideoCall() {
        alert('Video call feature coming soon!');
    }

    startVoiceCall() {
        alert('Voice call feature coming soon!');
    }

    showMoreOptions() {
        alert('More options coming soon!');
    }

    // Public methods
    clearMessages() {
        this.messagesContainer.innerHTML = '';
        this.messages = [];
    }

    setOnlineStatus(isOnline) {
        this.options.isOnline = isOnline;
        this.updateConnectionStatus();
    }

    getMessages() {
        return this.messages;
    }

    destroy() {
        if (this.socket) {
            this.socket.disconnect();
        }
        this.container.innerHTML = '';
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WhatsAppChat;
}