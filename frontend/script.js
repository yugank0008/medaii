const API_BASE_URL = 'https://medaii.onrender.com';
let currentUser = null;
let chatHistory = [];

class MedAIApp {
    constructor() {
        this.initializeEventListeners();
        this.loadUserData();
        this.testApiConnection();
    }

    initializeEventListeners() {
        // Chat input
        const messageInput = document.getElementById('messageInput');
        const sendBtn = document.getElementById('sendBtn');

        messageInput.addEventListener('input', this.autoResizeTextarea.bind(this));
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        sendBtn.addEventListener('click', () => this.sendMessage());

        // Mobile navigation toggle
        const sidebarToggle = document.getElementById('sidebarToggle');
        const sidebar = document.getElementById('sidebar');
        
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
            sidebarToggle.classList.toggle('active');
        });
        
        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 768 && 
                !sidebar.contains(e.target) && 
                !sidebarToggle.contains(e.target) &&
                !sidebar.classList.contains('collapsed')) {
                sidebar.classList.add('collapsed');
                sidebarToggle.classList.remove('active');
            }
        });

        // Modal buttons
        document.getElementById('predictBtn').addEventListener('click', () => this.showModal('predictionModal'));
        document.getElementById('analyzeBtn').addEventListener('click', () => this.showModal('analyzeModal'));
        document.getElementById('generateBtn').addEventListener('click', () => this.generateReport());
        
        // Close modals
        document.querySelectorAll('.close-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const modalId = e.target.closest('.close-btn').dataset.modal;
                this.hideModal(modalId);
            });
        });

        // Overlay click to close
        document.getElementById('modalOverlay').addEventListener('click', (e) => {
            if (e.target === document.getElementById('modalOverlay')) {
                this.hideAllModals();
            }
        });

        // Quick actions - using event delegation to prevent duplicate events
        document.addEventListener('click', (e) => {
            const quickBtn = e.target.closest('.quick-btn');
            if (quickBtn) {
                e.preventDefault();
                e.stopPropagation();
                
                const prompt = quickBtn.dataset.prompt;
                document.getElementById('messageInput').value = prompt;
                this.sendMessage();
            }
        });

        // File upload
        const fileInput = document.getElementById('reportFile');
        fileInput.addEventListener('change', (e) => this.handleFileSelect(e));

        // Analyze file button
        document.getElementById('analyzeFileBtn').addEventListener('click', () => this.analyzeReport());

        // Forms
        document.getElementById('predictionForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitPredictionForm();
        });

        // Drag and drop
        const uploadArea = document.getElementById('fileUploadArea');
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = '#10a37f';
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.style.borderColor = '#d1d5db';
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = '#d1d5db';
            
            if (e.dataTransfer.files.length > 0) {
                fileInput.files = e.dataTransfer.files;
                this.handleFileSelect({ target: fileInput });
            }
        });

        // New chat button
        document.getElementById('newChatBtn').addEventListener('click', () => this.startNewChat());
        
        // Keyboard accessibility for sidebar toggle
        sidebarToggle.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                sidebar.classList.toggle('collapsed');
                sidebarToggle.classList.toggle('active');
            }
        });
    }

    async testApiConnection() {
        try {
            const response = await fetch(`${API_BASE_URL}/health`);
            if (response.ok) {
                console.log('API connection successful');
            } else {
                console.warn('API health check failed');
            }
        } catch (error) {
            console.warn('API connection test failed:', error);
        }
    }

    autoResizeTextarea() {
        const textarea = document.getElementById('messageInput');
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
    }

    async sendMessage() {
        const messageInput = document.getElementById('messageInput');
        const message = messageInput.value.trim();

        if (!message) return;

        // Add user message to chat
        this.addMessage(message, 'user');
        messageInput.value = '';
        this.autoResizeTextarea();

        // Show loading state
        const sendBtn = document.getElementById('sendBtn');
        sendBtn.disabled = true;

        try {
            // Create user if not exists
            if (!currentUser) {
                currentUser = await this.createUser('Guest User', 'guest@example.com');
            }

            // Send to API
            const response = await this.callGeminiAPI(message);
            
            // Add bot response
            this.addMessage(response, 'bot');
            
            // Save to chat history
            this.saveChatHistory(message, response);

        } catch (error) {
            console.error('Error sending message:', error);
            this.showToast('Error sending message. Please try again.', 'error');
            this.addMessage('Sorry, I encountered an error. Please try again.', 'bot');
        } finally {
            sendBtn.disabled = false;
        }
    }

    addMessage(content, type) {
        const chatContainer = document.getElementById('chatContainer');
        
        // Hide welcome screen if it's the first message
        if (chatContainer.querySelector('.welcome-screen')) {
            chatContainer.innerHTML = '';
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        if (type === 'bot') {
            // Preprocess content for markdown conversion
            let processedContent = this.preprocessMarkdown(content);
            
            // Convert markdown to HTML using marked.js
            try {
                messageContent.innerHTML = marked.parse(processedContent);
            } catch (error) {
                console.error('Markdown parsing error:', error);
                // Fallback to plain text if parsing fails
                messageContent.textContent = content;
            }
        } else {
            // User messages remain plain text (escape HTML)
            messageContent.textContent = content;
        }

        const messageTime = document.createElement('div');
        messageTime.className = 'message-time';
        messageTime.textContent = new Date().toLocaleTimeString();

        messageDiv.appendChild(messageContent);
        messageDiv.appendChild(messageTime);
        chatContainer.appendChild(messageDiv);

        // Scroll to bottom
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    preprocessMarkdown(content) {
        // Convert headings with "Heading:" or "Heading" at start of line to markdown
        let processed = content.replace(/^(\s*)([A-Z][a-zA-Z\s]+):/gm, '$1## $2');
        processed = processed.replace(/^(\s*)([A-Z][a-zA-Z\s]+)$/gm, '$1## $2');
        
        // Ensure bullet points are properly formatted
        processed = processed.replace(/^(\s*)[•\-]\s+/gm, '$1* ');
        
        return processed;
    }

    async callGeminiAPI(query) {
        if (!currentUser) {
            throw new Error('User not created');
        }

        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: currentUser.id,
                query: query
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API request failed: ${response.status} ${errorText}`);
        }

        const data = await response.json();
        return data.answer || data.response || 'I received your message but got an unexpected response.';
    }

    async createUser(name, email) {
        try {
            // Generate a unique email for guest users
            const uniqueEmail = `guest-${Date.now()}@example.com`;
            
            const response = await fetch(`${API_BASE_URL}/users`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    name: name || 'Guest User',
                    email: email || uniqueEmail
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                if (response.status === 400 && errorData.detail === 'Email already registered') {
                    // Use a different email
                    return await this.createUser(name, `guest-${Date.now()}-retry@example.com`);
                }
                throw new Error(`Failed to create user: ${response.status}`);
            }

            const user = await response.json();
            localStorage.setItem('medai_user', JSON.stringify(user));
            this.showToast('User profile created successfully!');
            return user;
        } catch (error) {
            console.error('Error creating user:', error);
            // Return a mock user for demo purposes
            const mockUser = { 
                id: Math.floor(Math.random() * 1000) + 1, 
                name: 'Guest User', 
                email: `guest-${Date.now()}@example.com` 
            };
            localStorage.setItem('medai_user', JSON.stringify(mockUser));
            return mockUser;
        }
    }

    loadUserData() {
        const savedUser = localStorage.getItem('medai_user');
        if (savedUser) {
            currentUser = JSON.parse(savedUser);
        }

        const savedHistory = localStorage.getItem('medai_chat_history');
        if (savedHistory) {
            chatHistory = JSON.parse(savedHistory);
        }
    }

    saveChatHistory(query, response) {
        chatHistory.push({
            query,
            response,
            timestamp: new Date().toISOString()
        });

        // Keep only last 50 messages
        if (chatHistory.length > 50) {
            chatHistory = chatHistory.slice(-50);
        }

        localStorage.setItem('medai_chat_history', JSON.stringify(chatHistory));
    }

    showModal(modalId) {
        document.getElementById('modalOverlay').classList.add('active');
        document.getElementById(modalId).style.display = 'block';
    }

    hideModal(modalId) {
        document.getElementById(modalId).style.display = 'none';
        document.getElementById('modalOverlay').classList.remove('active');
    }

    hideAllModals() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.style.display = 'none';
        });
        document.getElementById('modalOverlay').classList.remove('active');
    }

    showLoading(message = 'Processing your request...') {
        document.getElementById('loadingText').textContent = message;
        this.showModal('loadingModal');
    }

    hideLoading() {
        this.hideModal('loadingModal');
    }

    showToast(message, type = 'success') {
        const toastContainer = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        toast.innerHTML = `
            <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i>
            <span>${message}</span>
        `;

        toastContainer.appendChild(toast);

        // Remove toast after 5 seconds
        setTimeout(() => {
            toast.remove();
        }, 5000);
    }

    async submitPredictionForm() {
        const form = document.getElementById('predictionForm');
        const formData = new FormData(form);
        
        if (!currentUser) {
            currentUser = await this.createUser('Guest User', 'guest@example.com');
        }

        const predictionData = {
            user_id: currentUser.id,
            demographics: {
                age: parseInt(formData.get('age')) || 30,
                gender: formData.get('gender') || 'unknown'
            },
            lifestyle: {
                description: formData.get('lifestyle') || 'Not specified'
            },
            symptoms: {
                description: formData.get('symptoms') || 'No symptoms reported'
            },
            vitals: {
                bmi: parseFloat(formData.get('bmi')) || 25,
                glucose: parseInt(formData.get('glucose')) || 100,
                blood_pressure: parseInt(formData.get('blood_pressure')) || 120,
                diabetes_pedigree: parseFloat(formData.get('diabetes_pedigree')) || 0.5,
                pregnancies: parseInt(formData.get('pregnancies')) || 0,
                skin_thickness: parseFloat(formData.get('skin_thickness')) || 20,
                insulin: parseInt(formData.get('insulin')) || 80
            }
        };

        this.showLoading('Calculating your health risk...');

        try {
            const response = await fetch(`${API_BASE_URL}/predict`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(predictionData)
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Prediction failed: ${response.status} ${errorText}`);
            }

            const result = await response.json();
            
            // Add prediction result to chat
            const predictionMessage = `
Disease: ${result.disease}
Risk: ${(result.risk * 100).toFixed(1)}%

Explanation:
${result.explanation}

Recommendations:
${result.recommendations}
            `;

            this.addMessage(predictionMessage, 'bot');
            this.hideModal('predictionModal');
            form.reset();
            this.showToast('Risk assessment completed successfully!');

        } catch (error) {
            console.error('Prediction error:', error);
            this.showToast('Error calculating risk. Please try again.', 'error');
        } finally {
            this.hideLoading();
        }
    }

    handleFileSelect(event) {
        const file = event.target.files[0];
        if (!file) return;

        if (file.type !== 'application/pdf') {
            this.showToast('Please select a PDF file', 'error');
            this.clearFile();
            return;
        }

        if (file.size > 10 * 1024 * 1024) { // 10MB limit
            this.showToast('File too large. Please select a file under 10MB.', 'error');
            this.clearFile();
            return;
        }

        const uploadArea = document.getElementById('fileUploadArea');
        const uploadPreview = document.getElementById('uploadPreview');
        const fileName = document.getElementById('fileName');
        const fileSize = document.getElementById('fileSize');

        uploadArea.style.display = 'none';
        uploadPreview.style.display = 'block';

        fileName.textContent = file.name;
        fileSize.textContent = this.formatFileSize(file.size);
    }

    clearFile() {
        const fileInput = document.getElementById('reportFile');
        const uploadArea = document.getElementById('fileUploadArea');
        const uploadPreview = document.getElementById('uploadPreview');

        fileInput.value = '';
        uploadArea.style.display = 'block';
        uploadPreview.style.display = 'none';
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    async analyzeReport() {
        const fileInput = document.getElementById('reportFile');
        const file = fileInput.files[0];

        if (!file) {
            this.showToast('Please select a PDF file first', 'error');
            return;
        }

        if (!currentUser) {
            currentUser = await this.createUser('Guest User', 'guest@example.com');
        }

        this.showLoading('Analyzing your medical report...');

        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('user_id', currentUser.id);

            const response = await fetch(`${API_BASE_URL}/analyze-report`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Report analysis failed: ${response.status} ${errorText}`);
            }

            const result = await response.json();
            
            // Add analysis result to chat
            const analysisMessage = `
Medical Report Analysis:

Findings:
${result.findings || 'No specific findings'}

Advice:
${result.advice || 'Please consult with a healthcare professional'}
            `;

            this.addMessage(analysisMessage, 'bot');
            this.hideModal('analyzeModal');
            this.clearFile();
            this.showToast('Report analysis completed successfully!');

        } catch (error) {
            console.error('Analysis error:', error);
            this.showToast('Error analyzing report. Please try again.', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async generateReport() {
        if (!currentUser) {
            currentUser = await this.createUser('Guest User', 'guest@example.com');
        }

        this.showLoading('Generating your health report...');

        try {
            // Try to get the latest prediction data
            let predictionId = null;
            let chatId = null;
            let reportId = null;

            // Get latest prediction
            try {
                const predictionsResponse = await fetch(`${API_BASE_URL}/history/predictions/${currentUser.id}`);
                if (predictionsResponse.ok) {
                    const predictions = await predictionsResponse.json();
                    if (predictions.length > 0) {
                        predictionId = predictions[0].id;
                    }
                }
            } catch (e) {
                console.log('Could not fetch prediction history');
            }

            // Get latest chat
            try {
                const chatsResponse = await fetch(`${API_BASE_URL}/history/chats/${currentUser.id}`);
                if (chatsResponse.ok) {
                    const chats = await chatsResponse.json();
                    if (chats.length > 0) {
                        chatId = chats[0].id;
                    }
                }
            } catch (e) {
                console.log('Could not fetch chat history');
            }

            // Get latest report
            try {
                const reportsResponse = await fetch(`${API_BASE_URL}/history/reports/${currentUser.id}`);
                if (reportsResponse.ok) {
                    const reports = await reportsResponse.json();
                    if (reports.length > 0) {
                        reportId = reports[0].id;
                    }
                }
            } catch (e) {
                console.log('Could not fetch report history');
            }

            // If no data available, create fallback report
            if (!predictionId && !chatId && !reportId) {
                this.hideLoading();
                await this.createFallbackReport();
                return;
            }

            const response = await fetch(`${API_BASE_URL}/generate-report`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: currentUser.id,
                    prediction_id: predictionId,
                    chat_id: chatId,
                    report_id: reportId
                })
            });

            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }

            // Check if response is PDF
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/pdf')) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `health-report-${new Date().toISOString().split('T')[0]}.pdf`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                this.showToast('Health report downloaded successfully!');
            } else {
                const result = await response.json();
                console.log('Report generation result:', result);
                this.showToast('Report generated successfully!');
            }

        } catch (error) {
            console.error('Report generation error:', error);
            this.showToast('Error generating report. Please try again.', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async createFallbackReport() {
        // Create a simple report based on chat history
        const reportMessage = `
# Health Summary Report

Based on our conversation, here's a summary of your health inquiries:

## Topics Discussed
${chatHistory.map(chat => `* ${chat.query.substring(0, 50)}...`).join('\n')}

## General Health Advice
* Maintain a balanced diet with plenty of fruits and vegetables
* Exercise regularly (at least 30 minutes most days)
* Get 7-9 hours of quality sleep each night
* Stay hydrated by drinking plenty of water
* Manage stress through relaxation techniques

*Note: This is a general health summary. For personalized medical advice, please consult with a healthcare professional.*
        `;

        this.addMessage(reportMessage, 'bot');
        this.showToast('Health summary created based on our conversation');
    }

    startNewChat() {
        const chatContainer = document.getElementById('chatContainer');
        chatContainer.innerHTML = `
            <div class="welcome-screen">
                <div class="welcome-content">
                    <div class="welcome-icon">
                        <i class="fas fa-comment-medical"></i>
                    </div>
                    <h2>Welcome to MedAI</h2>
                    <p>Your AI-powered health assistant. Ask medical questions, analyze reports, or assess health risks.</p>
                    <div class="welcome-actions">
                        <button class="quick-btn large" data-prompt="What are common symptoms of diabetes?">
                            <div class="quick-btn-icon">
                                <i class="fas fa-syringe"></i>
                            </div>
                            <span>Diabetes Symptoms</span>
                        </button>
                        <button class="quick-btn large" data-prompt="How can I improve my sleep quality?">
                            <div class="quick-btn-icon">
                                <i class="fas fa-bed"></i>
                            </div>
                            <span>Sleep Improvement</span>
                        </button>
                        <button class="quick-btn large" data-prompt="What exercises are good for heart health?">
                            <div class="quick-btn-icon">
                                <i class="fas fa-running"></i>
                            </div>
                            <span>Heart Healthy Exercises</span>
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Clear chat history
        chatHistory = [];
        localStorage.removeItem('medai_chat_history');
        
        this.showToast('New conversation started');
    }
}

// Initialize the app when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    new MedAIApp();
});