const API_LOGGING_PREFIX = '🌐 [API]';

// Axios request interceptor
axios.interceptors.request.use(
  config => {
    const timestamp = new Date().toISOString();
    console.groupCollapsed(`${API_LOGGING_PREFIX} → [${timestamp}] ${config.method?.toUpperCase()} ${config.url}`);
    console.log('Request Headers:', config.headers);
    if (config.data) {
      if (config.data instanceof FormData) {
        console.log('Request Data: [FormData]');
        for (let pair of config.data.entries()) {
          console.log(`${pair[0]}:`, pair[1]);
        }
      } else {
        console.log('Request Data:', config.data);
      }
    }
    console.groupEnd();
    config.metadata = { startTime: Date.now() };
    return config;
  },
  error => {
    console.error(`${API_LOGGING_PREFIX} Request Error:`, error);
    return Promise.reject(error);
  }
);

// Axios response interceptor
axios.interceptors.response.use(
  response => {
    const endTime = Date.now();
    const duration = endTime - (response.config.metadata?.startTime || endTime);
    const timestamp = new Date().toISOString();
    
    console.groupCollapsed(`${API_LOGGING_PREFIX} ← [${timestamp}] ${response.status} ${response.config.method?.toUpperCase()} ${response.config.url} (${duration}ms)`);
    console.log('Response Status:', response.status, response.statusText);
    console.log('Response Headers:', response.headers);
    console.log('Response Data:', response.data);
    console.groupEnd();
    
    return response;
  },
  error => {
    const endTime = Date.now();
    const duration = endTime - (error.config?.metadata?.startTime || endTime);
    const timestamp = new Date().toISOString();
    
    console.group(`${API_LOGGING_PREFIX} ← [${timestamp}] Error ${error.config?.method?.toUpperCase()} ${error.config?.url} (${duration}ms)`);
    console.error('Error:', error);
    if (error.response) {
      console.error('Response Status:', error.response.status, error.response.statusText);
      console.error('Response Data:', error.response.data);
      console.error('Response Headers:', error.response.headers);
    } else if (error.request) {
      console.error('No response received:', error.request);
    }
    console.groupEnd();
    
    return Promise.reject(error);
  }
);

const chatContainer = document.getElementById('chatMessages');
const messageInput = document.getElementById('userInput');
const sendButton = document.getElementById('sendBtn');
const fileInput = document.getElementById('fileInput');
const uploadButton = document.getElementById('uploadBtn');
const fileNameElement = document.getElementById('fileName');
const fileSizeElement = document.getElementById('fileSize');
const uploadProgress = document.getElementById('uploadProgress');
const progressBar = document.getElementById('progressBar');
const uploadStatus = document.getElementById('uploadStatus');
const filesList = document.getElementById('filesList');
const fileListContent = document.getElementById('fileListContent');

let sessionId = '';
let currentFileId = '';
const chatHistory = [];

fileInput.addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (!file) return;
  
  // Update UI to show selected file
  const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2);
  fileNameElement.textContent = file.name;
  fileSizeElement.textContent = `(${fileSizeMB} MB)`;
  uploadButton.disabled = false;
  
  // Show file size validation
  const maxSizeMB = 10; // 10MB max file size
  if (file.size > maxSizeMB * 1024 * 1024) {
    console.error(`File size exceeds ${maxSizeMB}MB limit`);
    uploadButton.disabled = true;
  }
});

uploadButton.addEventListener('click', async () => {
  const file = fileInput.files[0];
  if (!file) return;
  
  const formData = new FormData();
  formData.append('file', file);
  formData.append('session_id', sessionId);
  
  console.groupCollapsed('📤 Starting file upload');
  console.log('File:', file.name, `(${(file.size / (1024 * 1024)).toFixed(2)} MB)`);
  console.log('Session ID:', sessionId);
  console.groupEnd();
  
  try {
    // Show upload progress
    uploadProgress.classList.remove('hidden');
    uploadButton.disabled = true;
    
    // Upload file
    const response = await axios.post('/api/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        progressBar.style.width = `${progress}%`;
        uploadStatus.textContent = `Uploading: ${progress}%`;
        console.log(`📤 Upload progress: ${progress}%`);
      },
    });
    
    console.groupCollapsed('✅ File upload completed');
    console.log('Response:', response.data);
    console.groupEnd();
    
    // Update session ID from response
    if (response.data.session_id) {
      sessionId = response.data.session_id;
      console.log('Updated session ID:', sessionId);
    }
    
    // Handle successful upload
    currentFileId = response.data.file_id;
    addMessage('assistant', `File "${file.name}" uploaded successfully! You can now ask questions about it.`);
    
    // Enable chat
    messageInput.disabled = false;
    sendButton.disabled = false;
    messageInput.focus();
    
    // Update file list
    updateFileList();
    
  } catch (error) {
    console.error('Upload error:', error);
    console.error('Failed to upload file. Please try again.');
    addMessage('assistant', 'Sorry, there was an error uploading your file. Please try again.');
  } finally {
    uploadProgress.classList.add('hidden');
    uploadButton.disabled = false;
    progressBar.style.width = '0%';
    uploadStatus.textContent = '';
  }
});

async function sendMessage() {
  const message = messageInput.value.trim();
  if (!message || !currentFileId) return;
  
  // Add user message to chat
  addMessage('user', message);
  logChatMessage('user', message);
  messageInput.value = '';
  
  // Add typing indicator
  const typingIndicator = addTypingIndicator();
  
  try {
    const requestData = {
      messages: [
        ...chatHistory,
        { role: 'user', content: message }
      ],
      file_id: currentFileId,
      session_id: sessionId
    };
    
    console.groupCollapsed('📤 Sending chat message');
    console.log('Request Data:', requestData);
    console.groupEnd();
    
    const response = await axios.post('/api/files/chat', requestData);
    
    // Log the response
    console.groupCollapsed('📥 Received chat response');
    console.log('Response:', response.data);
    console.groupEnd();
    
    // Remove typing indicator
    typingIndicator.remove();
    
    // Add assistant's response
    addMessage('assistant', response.data.response);
    logChatMessage('assistant', response.data.response);
    
  } catch (error) {
    console.error('Chat error:', error);
    console.error('Failed to get response. Please try again.');
  }
}

messageInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

sendButton.addEventListener('click', sendMessage);

function addMessage(role, content) {
  const messageDiv = document.createElement('div');
  messageDiv.className = `flex ${role === 'user' ? 'justify-end' : 'justify-start'}`;
  
  const messageBubble = document.createElement('div');
  messageBubble.className = `max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
    role === 'user' 
      ? 'bg-blue-500 text-white rounded-br-none' 
      : 'bg-gray-200 text-gray-800 rounded-bl-none'
  }`;
  
  messageBubble.textContent = content;
  messageDiv.appendChild(messageBubble);
  chatContainer.appendChild(messageDiv);
  
  // Auto-scroll to bottom
  chatContainer.scrollTop = chatContainer.scrollHeight;
  
  // Add to chat history
  chatHistory.push({ role, content });
}

function logChatMessage(role, content) {
  console.groupCollapsed(`💬 [CHAT] ${role === 'user' ? '👤 User' : '🤖 Assistant'}`);
  console.log(content);
  console.groupEnd();
}

function addTypingIndicator() {
  const typingDiv = document.createElement('div');
  typingDiv.className = 'flex justify-start';
  typingDiv.id = 'typing-indicator';
  
  const typingBubble = document.createElement('div');
  typingBubble.className = 'bg-gray-200 text-gray-800 px-4 py-2 rounded-lg rounded-bl-none';
  
  const dot1 = document.createElement('span');
  dot1.className = 'inline-block w-2 h-2 bg-gray-500 rounded-full mx-1 animate-bounce';
  
  const dot2 = document.createElement('span');
  dot2.className = 'inline-block w-2 h-2 bg-gray-500 rounded-full mx-1 animate-bounce';
  dot2.style.animationDelay = '0.2s';
  
  const dot3 = document.createElement('span');
  dot3.className = 'inline-block w-2 h-2 bg-gray-500 rounded-full mx-1 animate-bounce';
  dot3.style.animationDelay = '0.4s';
  
  typingBubble.appendChild(dot1);
  typingBubble.appendChild(dot2);
  typingBubble.appendChild(dot3);
  typingDiv.appendChild(typingBubble);
  chatContainer.appendChild(typingDiv);
  
  // Auto-scroll to bottom
  chatContainer.scrollTop = chatContainer.scrollHeight;
  
  return typingDiv;
}

async function updateFileList() {
  try {
    const response = await axios.get(`/api/files/list?session_id=${sessionId}`);
    const files = response.data;
    
    fileListContent.innerHTML = ''; // Clear current list
    
    if (files.length === 0) {
      filesList.style.display = 'none';
      return;
    }
    
    filesList.style.display = 'block';
    
    files.forEach(file => {
      const fileItem = document.createElement('div');
      fileItem.className = 'flex justify-between items-center p-2 hover:bg-gray-50 rounded';
      
      const fileInfo = document.createElement('div');
      fileInfo.className = 'flex-1';
      
      const fileName = document.createElement('div');
      fileName.className = 'font-medium';
      fileName.textContent = file.filename;
      
      const fileMeta = document.createElement('div');
      fileMeta.className = 'text-sm text-gray-500';
      fileMeta.textContent = `${(file.size / 1024 / 1024).toFixed(2)} MB • ${new Date(file.created_at).toLocaleString()}`;
      
      fileInfo.appendChild(fileName);
      fileInfo.appendChild(fileMeta);
      
      const selectButton = document.createElement('button');
      selectButton.className = 'text-blue-500 hover:text-blue-700';
      selectButton.textContent = file.file_id === currentFileId ? 'Selected' : 'Select';
      selectButton.disabled = file.file_id === currentFileId;
      
      selectButton.addEventListener('click', () => {
        currentFileId = file.file_id;
        addMessage('assistant', `Now chatting about "${file.filename}"`);
        updateFileList(); // Refresh the list to update the selected state
      });
      
      fileItem.appendChild(fileInfo);
      fileItem.appendChild(selectButton);
      fileListContent.appendChild(fileItem);
    });
    
  } catch (error) {
    console.error('Error fetching file list:', error);
    console.error('Failed to load file list');
  }
}

async function init() {
  try {
    console.log('🚀 Initializing chat interface...');
    
    // Enable file input
    fileInput.disabled = false;
    
    // Show welcome message
    addMessage('assistant', 'Welcome! Please upload a file to get started.');
    
    console.log('✅ Chat interface initialized');
  } catch (error) {
    console.error('Error initializing chat interface:', error);
    // Still show the welcome message even if there's an error
    addMessage('assistant', 'Welcome! Please upload a file to get started.');
  }
}

document.addEventListener('DOMContentLoaded', init);
