<template>
    <div class="chat-container">
        <!-- Chat List Sidebar -->
        <div class="chat-sidebar">
            <div class="sidebar-header">
                <h2>Messages</h2>
                <button class="new-chat-btn" title="Show characters">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                </button>
            </div>

            <!-- Characters Section -->
            <div v-if="characters.length" class="sidebar-section">
                <div class="section-label">Characters</div>
                <router-link v-for="char in characters" :key="char.id" :to="{ name: 'chat', params: { id: char.id } }"
                    class="chat-item" :class="{ active: route.params.id == char.id }">
                    <div class="chat-avatar">
                        <img :src="char.avatar || `${apiUrl}/random-image-file?user=${char.id}`" />
                    </div>
                    <div class="chat-info">
                        <div class="chat-name">{{ char.name }}</div>
                        <div class="last-message">{{ char.description?.substring(0, 50) || 'Start chatting…' }}…</div>
                    </div>
                </router-link>
            </div>

            <!-- Existing Chats -->
            <div v-if="all_chats.length" class="sidebar-section">
                <div class="section-label">Recent</div>
                <router-link v-for="chat in all_chats" :key="chat.id"
                    :to="{ name: 'chat', params: { id: chat.chat_id } }" class="chat-item"
                    :class="{ active: route.params.id == chat.chat_id }">
                    <div class="chat-avatar">
                        <img
                            :src="chat.character?.avatar || (chat.is_character_chat ? `${apiUrl}/random-image-file?user=${chat.chat_id}` : apiUrl + '/image-file/' + chat.chat_id)" />
                    </div>
                    <div class="chat-info">
                        <div class="chat-name">{{ chat.character?.character_name || 'Chat' }}</div>
                        <div class="last-message">{{ chat.messages?.[chat.messages.length - 1]?.text || 'No messages
                            yet' }}</div>
                    </div>
                    <div class="chat-meta">
                        <div class="chat-time">{{ chat.time }}</div>
                        <div v-if="chat.unreadCount" class="unread-badge">{{ chat.unreadCount }}</div>
                    </div>
                </router-link>
            </div>
        </div>

        <!-- Main Chat Area -->
        <div class="chat-main">
            <div v-if="selectedChat" class="chat-content">
                <!-- Chat Header -->
                <div class="chat-header">
                    <div class="chat-user-info">
                        <img :src="chat.character?.avatar || (chat.is_character_chat ? `${apiUrl}/random-image-file?user=${chat.chat_id}` : apiUrl + '/image-file/' + chat.chat_id)"
                            :alt="chat.character?.character_name ?? 'Loading...'" class="user-avatar" />
                        <div>
                            <h3>{{ chat.character?.character_name ?? "Loading..." }}</h3>
                        </div>
                    </div>
                    <div class="chat-actions">
                        <button class="action-btn" title="Voice call">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                            </svg>
                        </button>
                        <button class="action-btn" title="Video call">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                            </svg>
                        </button>
                        <button class="action-btn" title="Chat info">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                        </button>
                    </div>
                </div>

                <!-- Messages Area -->
                <div class="messages-container" ref="messagesContainer">




                    <div v-if="chat.chat_id && !chat.is_character_chat" class="received">
                        <div class="message-content">
                            <div class="message-image">
                                <img :src="apiUrl + '/image-file/' + chat.chat_id" :alt="'Shared image'"
                                    @click="openImage(apiUrl + '/image-file/' + chat.chat_id)" />
                            </div>
                        </div>
                    </div>
                    <div v-for="message in chat.messages" :key="message.id"
                        :class="['message', { sent: message.isUser, received: !message.isUser }]">
                        <div class="message-content">
                            <div v-if="message.text" class="message-text">
                                {{ message.text }}
                            </div>
                            <div v-if="message.text" class="text-gray-400">
                                {{ message.image_prompt }}
                            </div>
                            <div v-if="message.image" class="message-image">
                                <img :src="message.image" :alt="'Shared image'" @click="openImage(message.image)" />
                            </div>
                            <div class="message-time">{{ message.time }}</div>
                        </div>
                    </div>
                    <div>
                        <div v-if="isTyping" class="typing-indicator">
                            <span class="dot"></span>
                            <span class="dot"></span>
                            <span class="dot"></span>
                        </div>
                    </div>
                </div>

                <!-- Message Input -->
                <div class="message-input-container">
                    <div class="input-actions">
                        <button @click="attachImage" class="attach-btn" title="Attach file">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                            </svg>
                        </button>
                        <button @click="attachImage" class="image-btn" title="Attach image">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                        </button>
                    </div>
                    <input v-model="newMessage" @keyup.enter="sendMessage" placeholder="Type a message..."
                        class="message-input" />
                    <button @click="sendMessage" class="send-btn">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                        </svg>
                    </button>
                </div>
            </div>

            <!-- Welcome State -->
            <div v-else class="welcome-state">
                <div class="welcome-icon">
                    <svg class="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1"
                            d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                </div>
                <h2>Welcome to Messages</h2>
                <p>Select a conversation to start chatting</p>
            </div>
        </div>

        <!-- Image Modal -->
        <div v-if="selectedImage" class="image-modal " @click="closeImage">
            <div class="modal-content " @click.stop>
                <img :src="selectedImage" alt="Full size image" class="h-full w-fit" />
                <button class="close-btn" @click="closeImage">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { apiUrl, formatRequest, GetFromApi } from '@/api';
import { ref, reactive, nextTick, onMounted, watch } from 'vue';
import { useRoute } from 'vue-router'

const route = useRoute()

const chat = ref({});

const all_chats = ref([]);
const characters = ref([]);


async function RefreshChat() {

    console.log('Refreshing chat data...');

    if (route.params.id) {
        const response = await fetch(apiUrl + '/chat/' + route.params.id, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        chat.value = await response.json();
    }
    console.log('Chat data:', chat.value);
    const chatResponse = await fetch(apiUrl + '/chats');
    all_chats.value = await chatResponse.json();
}

async function loadCharacters() {
    try {
        const data = await GetFromApi('characters');
        if (data && Array.isArray(data)) {
            characters.value = data;
        }
    } catch (e) {
        console.error('Failed to load characters:', e);
    }
}

onMounted(() => {
    RefreshChat();
    loadCharacters();
});

watch(() => route.params.id, () => {
    RefreshChat();
});

const selectedChat = ref(null);
const newMessage = ref('');
const selectedImage = ref(null);
const messagesContainer = ref(null);

const chats = reactive([
    {
        id: 1,
        name: 'Alice Johnson',
        avatar: 'https://images.unsplash.com/photo-1494790108755-2616b612b47c?w=150&h=150&fit=crop&crop=face',
        lastMessage: 'Hey! How are you doing?',
        time: '2:30 PM',
        status: 'Online',
        unreadCount: 2,
        messages: [
            { id: 1, text: 'Hey there!', time: '2:15 PM', sent: false },
            { id: 2, text: 'Hi Alice! How are you?', time: '2:16 PM', sent: true },
            { id: 3, image: 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400&h=300&fit=crop', time: '2:20 PM', sent: false },
            { id: 4, text: 'Beautiful sunset!', time: '2:21 PM', sent: false },
            { id: 5, text: "Wow, that's amazing! 😍", time: '2:25 PM', sent: true },
            { id: 6, text: 'Hey! How are you doing?', time: '2:30 PM', sent: false }
        ]
    },
    {
        id: 2,
        name: 'Bob Smith',
        avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=face',
        lastMessage: "Let's meet tomorrow",
        time: '1:45 PM',
        status: 'Away',
        unreadCount: 0,
        messages: [
            { id: 1, text: 'Are we still on for tomorrow?', time: '1:30 PM', sent: false },
            { id: 2, text: 'Yes! What time works for you?', time: '1:35 PM', sent: true },
            { id: 3, text: 'How about 3 PM?', time: '1:40 PM', sent: false },
            { id: 4, text: 'Perfect! See you then', time: '1:42 PM', sent: true },
            { id: 5, text: "Let's meet tomorrow", time: '1:45 PM', sent: false }
        ]
    },
    {
        id: 3,
        name: 'Carol Davis',
        avatar: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150&h=150&fit=crop&crop=face',
        lastMessage: 'Thanks for the help!',
        time: '11:20 AM',
        status: 'Offline',
        unreadCount: 0,
        messages: [
            { id: 1, text: 'Can you help me with the project?', time: '11:00 AM', sent: false },
            { id: 2, text: 'Of course! What do you need?', time: '11:05 AM', sent: true },
            { id: 3, image: 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=400&h=300&fit=crop', time: '11:10 AM', sent: true },
            { id: 4, text: "Here's the design mockup", time: '11:11 AM', sent: true },
            { id: 5, text: 'This looks great!', time: '11:15 AM', sent: false },
            { id: 6, text: 'Thanks for the help!', time: '11:20 AM', sent: false }
        ]
    }
]);

import { request } from '@/api';

function selectChat(chat) {
    selectedChat.value = chat;
    nextTick(() => {
        scrollToBottom();
    });
}

const isTyping = ref(false);
const url = ref('http://127.0.0.1:8000/')

async function sendMessage() {
    if (!newMessage.value.trim() || !chat.value) return;



    isTyping.value = true;

    chat.value.messages.push({
        id: Date.now(),
        text: newMessage.value,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        isUser: true
    });

    const message = encodeURIComponent(newMessage.value);
    newMessage.value = ''


    const body = {
        image_request: { ...request },
    }

    console.log('Sending message:', body);

    const response = await fetch(apiUrl + '/chat/' + route.params.id + '/message?message=' + message, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(body)
    });

    const responseData = await response.json();

    console.log('Response:', responseData);
    await RefreshChat();

    if (responseData.image_prompt) {

        console.log('Image prompt received:', responseData.image_prompt);
        const _request = formatRequest(responseData.image_prompt);

        console.log('Formatted request:', _request);
        //post to /sdapi/v1/txt2img with body as plainRequest
        const txt2imgResponse = await fetch(url.value + 'sdapi/v1/txt2img', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(_request)
        })
        const result = await txt2imgResponse.json()
        chat.value.messages[chat.value.messages.length - 1].image = "image/png;base64," + result.images[0];

        //post to /chat/{chat_id}/{message_index}/image
        const _url = apiUrl + '/chat/' + route.params.id + '/' + (chat.value.messages.length - 1) + '/image';
        const imageResponse = await fetch(_url, {
            method: 'POST',
        });
    }

    isTyping.value = false;
    await RefreshChat();

    nextTick(() => {
        scrollToBottom();
    });

}

function attachImage() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.onchange = (e) => {
        const file = e.target.files[0];
        if (file && selectedChat.value) {
            const reader = new FileReader();
            reader.onload = (e) => {
                const message = {
                    id: Date.now(),
                    image: e.target.result,
                    time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                    sent: true
                };
                selectedChat.value.messages.push(message);
                selectedChat.value.lastMessage = 'Sent an image';
                nextTick(() => {
                    scrollToBottom();
                });
            };
            reader.readAsDataURL(file);
        }
    };
    input.click();
}

function openImage(imageUrl) {
    selectedImage.value = imageUrl;
}

function closeImage() {
    selectedImage.value = null;
}

function scrollToBottom() {
    if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
    }
}

onMounted(() => {
    if (chats.length > 0) {
        selectChat(chats[0]);
    }
});
</script>

<style scoped>
.chat-container {
    display: flex;
    height: calc(100vh - 80px);
    max-width: 1400px;
    margin: 0 auto;
    background: #111827;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

@media (prefers-color-scheme: dark) {
    .chat-container {
        background: #111827;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2);
    }
}

/* Sidebar Styles */
.chat-sidebar {
    width: 350px;
    background: #f9fafb;
    border-right: 1px solid #e5e7eb;
    display: flex;
    flex-direction: column;
}

@media (prefers-color-scheme: dark) {
    .chat-sidebar {
        background: #1f2937;
        border-right-color: #374151;
    }
}

.sidebar-header {
    padding: 24px 20px 16px;
    border-bottom: 1px solid #e5e7eb;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

@media (prefers-color-scheme: dark) {
    .sidebar-header {
        border-bottom-color: #374151;
    }
}

.sidebar-header h2 {
    margin: 0;
    font-size: 1.5rem;
    font-weight: 700;
    color: #111827;
}

@media (prefers-color-scheme: dark) {
    .sidebar-header h2 {
        color: #f9fafb;
    }
}

.new-chat-btn {
    width: 44px;
    height: 44px;
    border-radius: 10px;
    border: none;
    background: #3b82f6;
    color: white;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
}

.new-chat-btn:hover {
    background: #2563eb;
    transform: translateY(-1px);
}

.chat-list {
    flex: 1;
    overflow-y: auto;
    padding: 8px 0;
}

.sidebar-section {
    padding: 4px 0;
}

.section-label {
    padding: 8px 20px 4px;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #9ca3af;
}

.chat-item {
    display: flex;
    padding: 12px 20px;
    cursor: pointer;
    transition: all 0.2s;
    position: relative;
}

.chat-item:hover {
    background: #f3f4f6;
}

@media (prefers-color-scheme: dark) {
    .chat-item:hover {
        background: #374151;
    }
}

.chat-item.active {
    background: #eff6ff;
    border-right: 3px solid #3b82f6;
}

@media (prefers-color-scheme: dark) {
    .chat-item.active {
        background: #1e3a8a;
    }
}

.chat-avatar {
    position: relative;
    margin-right: 12px;
}

.chat-avatar img {
    width: 52px;
    height: 52px;
    border-radius: 50%;
    object-fit: cover;
}

.status-indicator {
    position: absolute;
    bottom: 2px;
    right: 2px;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    border: 2px solid white;
}

@media (prefers-color-scheme: dark) {
    .status-indicator {
        border-color: #1f2937;
    }
}

.status-online {
    background: #10b981;
}

.status-away {
    background: #f59e0b;
}

.status-offline {
    background: #6b7280;
}

.chat-info {
    flex: 1;
    min-width: 0;
    margin-right: 12px;
}

.chat-name {
    font-weight: 600;
    color: #111827;
    margin-bottom: 4px;
    font-size: 15px;
}

@media (prefers-color-scheme: dark) {
    .chat-name {
        color: #f9fafb;
    }
}

.last-message {
    color: #6b7280;
    font-size: 14px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

@media (prefers-color-scheme: dark) {
    .last-message {
        color: #9ca3af;
    }
}

.chat-meta {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 4px;
}

.chat-time {
    color: #9ca3af;
    font-size: 12px;
}

.unread-badge {
    background: #ef4444;
    color: white;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 6px;
    border-radius: 10px;
    min-width: 18px;
    text-align: center;
}

/* Main Chat Styles */
.chat-main {
    flex: 1;
    display: flex;
    flex-direction: column;
    background: white;
}

@media (prefers-color-scheme: dark) {
    .chat-main {
        background: #111827;
    }
}

.chat-content {
    display: flex;
    flex-direction: column;
    height: 100%;
}

.chat-header {
    padding: 20px 24px;
    border-bottom: 1px solid #e5e7eb;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

@media (prefers-color-scheme: dark) {
    .chat-header {
        border-bottom-color: #374151;
    }
}

.chat-user-info {
    display: flex;
    align-items: center;
}

.user-avatar {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    object-fit: cover;
    margin-right: 12px;
}

.chat-user-info h3 {
    margin: 0 0 2px 0;
    font-size: 1.125rem;
    font-weight: 600;
    color: #111827;
}

@media (prefers-color-scheme: dark) {
    .chat-user-info h3 {
        color: #f9fafb;
    }
}

.status {
    font-size: 14px;
    font-weight: 500;
}

.status.status-online {
    color: #10b981;
}

.status.status-away {
    color: #f59e0b;
}

.status.status-offline {
    color: #6b7280;
}

.chat-actions {
    display: flex;
    gap: 8px;
}

.action-btn {
    width: 44px;
    height: 44px;
    border: none;
    background: #f3f4f6;
    border-radius: 10px;
    cursor: pointer;
    color: #6b7280;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
}

.action-btn:hover {
    background: #e5e7eb;
    color: #374151;
}

@media (prefers-color-scheme: dark) {
    .action-btn {
        background: #374151;
        color: #9ca3af;
    }

    .action-btn:hover {
        background: #4b5563;
        color: #f3f4f6;
    }
}

.messages-container {
    flex: 1;
    padding: 24px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 16px;
    background: #f9fafb;
}

@media (prefers-color-scheme: dark) {
    .messages-container {
        background: #0f172a;
    }
}

.message {
    display: flex;
}

.message.sent {
    justify-content: flex-end;
}

.message.received {
    justify-content: flex-start;
}

.message-content {
    max-width: 70%;
    background: white;
    border-radius: 18px;
    padding: 12px 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    border: 1px solid #e5e7eb;
}

@media (prefers-color-scheme: dark) {
    .message-content {
        background: #1f2937;
        border-color: #374151;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
    }
}

.message.sent .message-content {
    background: #3b82f6;
    color: white;
    border-color: #3b82f6;
}

.message-text {
    margin-bottom: 4px;
    color: #111827;
    line-height: 1.5;
}

@media (prefers-color-scheme: dark) {
    .message-text {
        color: #f3f4f6;
    }
}

.message.sent .message-text {
    color: white;
}

.message-image {
    margin-bottom: 4px;
}

.message-image img {
    max-width: 280px;
    max-height: 200px;
    border-radius: 12px;
    cursor: pointer;
    display: block;
}

.message-time {
    font-size: 11px;
    opacity: 0.7;
    text-align: right;
}

.message-input-container {
    padding: 20px 24px;
    border-top: 1px solid #e5e7eb;
    display: flex;
    align-items: center;
    gap: 12px;
    background: white;
}

@media (prefers-color-scheme: dark) {
    .message-input-container {
        border-top-color: #374151;
        background: #111827;
    }
}

.input-actions {
    display: flex;
    gap: 8px;
}

.attach-btn,
.image-btn {
    width: 44px;
    height: 44px;
    border: none;
    background: #f3f4f6;
    border-radius: 10px;
    cursor: pointer;
    color: #6b7280;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
}

.attach-btn:hover,
.image-btn:hover {
    background: #e5e7eb;
    color: #374151;
}

@media (prefers-color-scheme: dark) {

    .attach-btn,
    .image-btn {
        background: #374151;
        color: #9ca3af;
    }

    .attach-btn:hover,
    .image-btn:hover {
        background: #4b5563;
        color: #f3f4f6;
    }
}

.message-input {
    flex: 1;
    padding: 12px 16px;
    border: 1px solid #d1d5db;
    border-radius: 25px;
    outline: none;
    font-size: 14px;
    background: #f9fafb;
    color: #111827;
    transition: all 0.2s;
}

.message-input:focus {
    border-color: #3b82f6;
    background: white;
}

.message-input::placeholder {
    color: #9ca3af;
}

@media (prefers-color-scheme: dark) {
    .message-input {
        background: #1f2937;
        border-color: #4b5563;
        color: #f3f4f6;
    }

    .message-input:focus {
        border-color: #3b82f6;
        background: #111827;
    }

    .message-input::placeholder {
        color: #6b7280;
    }
}

.send-btn {
    width: 44px;
    height: 44px;
    background: #3b82f6;
    color: white;
    border: none;
    border-radius: 50%;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
}

.send-btn:hover {
    background: #2563eb;
    transform: translateY(-1px);
}

.welcome-state {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    height: 100%;
    color: #6b7280;
    text-align: center;
}

@media (prefers-color-scheme: dark) {
    .welcome-state {
        color: #9ca3af;
    }
}

.welcome-icon {
    margin-bottom: 16px;
    opacity: 0.5;
}

.welcome-state h2 {
    margin: 0 0 8px 0;
    font-size: 1.5rem;
    font-weight: 600;
}

.welcome-state p {
    margin: 0;
    font-size: 1rem;
}

/* Image Modal */
.image-modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.9);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
    backdrop-filter: blur(8px);
}

.modal-content {
    position: relative;
    max-width: 90%;
    max-height: 90%;
    border-radius: 12px;
    overflow: hidden;
}

.modal-content img {
    max-width: 100%;
    max-height: 100%;
    display: block;
}

.close-btn {
    position: absolute;
    top: 16px;
    right: 16px;
    width: 44px;
    height: 44px;
    background: rgba(0, 0, 0, 0.8);
    color: white;
    border: none;
    border-radius: 50%;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
}

.close-btn:hover {
    background: rgba(0, 0, 0, 0.9);
    transform: scale(1.1);
}

/* Responsive Design */
@media (max-width: 1024px) {
    .chat-container {
        height: calc(100vh - 60px);
        border-radius: 0;
    }

    .chat-sidebar {
        width: 300px;
    }
}

@media (max-width: 768px) {
    .chat-container {
        position: relative;
    }

    .chat-sidebar {
        width: 100%;
        position: absolute;
        z-index: 100;
        height: 100%;
        transform: translateX(-100%);
        transition: transform 0.3s ease;
    }

    .chat-sidebar.mobile-open {
        transform: translateX(0);
    }

    .chat-main {
        width: 100%;
    }

    .message-content {
        max-width: 85%;
    }
}

/* Scrollbar Styling */
.chat-list::-webkit-scrollbar,
.messages-container::-webkit-scrollbar {
    width: 6px;
}

.chat-list::-webkit-scrollbar-track,
.messages-container::-webkit-scrollbar-track {
    background: transparent;
}

.chat-list::-webkit-scrollbar-thumb,
.messages-container::-webkit-scrollbar-thumb {
    background: #d1d5db;
    border-radius: 3px;
}

.chat-list::-webkit-scrollbar-thumb:hover,
.messages-container::-webkit-scrollbar-thumb:hover {
    background: #9ca3af;
}

.typing-indicator {
    display: flex;
    align-items: center;
    gap: 4px;
    color: #6b7280;
}

.dot {
    width: 8px;
    height: 8px;
    background-color: #6b7280;
    border-radius: 50%;
    animation: blink 1.4s infinite both;
}

@media (prefers-color-scheme: dark) {

    .chat-list::-webkit-scrollbar-thumb,
    .messages-container::-webkit-scrollbar-thumb {
        background: #4b5563;
    }

    .chat-list::-webkit-scrollbar-thumb:hover,
    .messages-container::-webkit-scrollbar-thumb:hover {
        background: #6b7280;
    }
}
</style>