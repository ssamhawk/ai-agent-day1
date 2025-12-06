/**
 * Voice UI Module for Day 12 AI Application
 * Handles audio recording and speech-to-text conversion
 */

class VoiceRecorder {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.recordingStartTime = null;
        this.timerInterval = null;
        this.stream = null; // Store stream for reuse

        // UI Elements
        this.voiceButton = document.getElementById('voice-button');
        this.recordingTimer = document.getElementById('recording-timer');
        this.userInput = document.getElementById('user-input');

        // Initialize
        this.init();
    }

    init() {
        // Check browser support
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            console.error('MediaDevices API not supported');
            this.voiceButton.style.display = 'none';
            return;
        }

        // Bind events
        this.voiceButton.addEventListener('click', () => this.toggleRecording());
    }

    async toggleRecording() {
        if (this.isRecording) {
            this.stopRecording();
        } else {
            await this.startRecording();
        }
    }

    async startRecording() {
        try {
            const totalStartTime = performance.now();

            // Request microphone access (or reuse if stream is still active)
            if (!this.stream || !this.stream.active) {
                // Show "Requesting permission..." state
                this.voiceButton.disabled = true;
                this.voiceButton.innerHTML = '⏳ Requesting...';
                console.log('🎤 Requesting microphone access...');

                const micStartTime = performance.now();

                // Request microphone access
                this.stream = await navigator.mediaDevices.getUserMedia({
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true
                    }
                });

                const micDuration = Math.round(performance.now() - micStartTime);
                console.log(`✅ Microphone access granted (took ${micDuration}ms)`);
            } else {
                console.log('✅ Reusing existing microphone stream (0ms delay)');
            }

            // Create MediaRecorder with the stream
            this.mediaRecorder = new MediaRecorder(this.stream);
            this.audioChunks = [];

            // Handle data available
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };

            // Handle recording stop
            this.mediaRecorder.onstop = () => {
                this.processRecording();
            };

            // 🎯 ВАЖЛИВО: Оновлюємо UI ТІЛЬКИ коли запис РЕАЛЬНО почався
            this.mediaRecorder.onstart = () => {
                const totalDuration = Math.round(performance.now() - totalStartTime);
                console.log(`🎤 Recording ACTUALLY started (${totalDuration}ms from click) at:`, new Date().toLocaleTimeString());

                // NOW update UI
                this.voiceButton.disabled = false;
                this.voiceButton.classList.add('recording');
                this.voiceButton.innerHTML = '<span class="recording-pulse"></span> Stop';

                // Show timer
                this.recordingTimer.classList.add('active');

                // Start timer WHEN recording actually starts
                this.recordingStartTime = Date.now();
                this.startTimer();

                // Play a short beep sound (optional)
                this.playBeep();
            };

            // Start recording (will trigger onstart when ready)
            this.mediaRecorder.start();
            this.isRecording = true;

            console.log('⏳ Waiting for recording to start...');

        } catch (error) {
            console.error('Error starting recording:', error);

            // Reset button state
            this.voiceButton.disabled = false;
            this.voiceButton.innerHTML = '🎤 Voice';

            // Handle permission denied
            if (error.name === 'NotAllowedError') {
                this.showError('Microphone access denied. Please allow permissions in browser settings.');
            } else if (error.name === 'NotFoundError') {
                this.showError('No microphone found. Please connect a microphone.');
            } else {
                this.showError('Failed to start recording: ' + error.message);
            }
        }
    }

    stopRecording() {
        if (!this.mediaRecorder || !this.isRecording) {
            return;
        }

        // Stop ALL stream tracks to turn off microphone indicator
        if (this.stream && this.stream.active) {
            this.stream.getTracks().forEach(track => {
                track.stop();
                console.log('🛑 Stopped track:', track.kind);
            });
            this.stream = null; // Reset stream so next recording will request new one
        }

        // Stop recording
        this.mediaRecorder.stop();
        this.isRecording = false;

        // Update UI
        this.voiceButton.classList.remove('recording');
        this.voiceButton.innerHTML = '🎤 Voice';

        // Hide timer
        this.recordingTimer.classList.remove('active');

        // Stop timer
        this.stopTimer();

        console.log('🛑 Recording stopped and microphone released');
    }

    async processRecording() {
        try {
            // Create audio blob
            const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });

            console.log(`📦 Audio blob created: ${(audioBlob.size / 1024).toFixed(1)}KB`);

            // Show processing state
            this.showProcessing();

            // Send to server for transcription
            const text = await this.transcribeAudio(audioBlob);

            // Hide processing state
            this.hideProcessing();

            if (text) {
                // Show voice message in chat UI (won't persist after reload - that's OK)
                this.showVoiceMessage(text, audioBlob);

                // Send transcription to AI (will save text to database for persistence)
                await this.sendToAI(text, audioBlob);
            }

        } catch (error) {
            console.error('Error processing recording:', error);
            this.hideProcessing();
        }
    }

    showVoiceMessage(text, audioBlob) {
        // Create voice message element in chat
        const messagesContainer = document.getElementById('chat-messages');
        if (!messagesContainer) return;

        // Remove welcome message if exists
        const welcomeMsg = messagesContainer.querySelector('.welcome-message');
        if (welcomeMsg) {
            welcomeMsg.remove();
        }

        // Create audio URL for playback
        const audioUrl = URL.createObjectURL(audioBlob);

        // Create voice message container (user side - right)
        const voiceMsg = document.createElement('div');
        voiceMsg.className = 'message user-message';
        voiceMsg.innerHTML = `
            <div class="message-content voice-message-content">
                <div class="voice-message-player">
                    <button class="btn-play-audio" type="button" title="Play audio">
                        <span class="play-icon">▶</span>
                    </button>
                    <div class="voice-waveform">
                        <span class="voice-duration">Voice message</span>
                    </div>
                    <button class="btn-show-transcription" type="button" title="Show transcription">
                        <span>📝</span>
                    </button>
                </div>
                <div class="voice-transcription-hidden" style="display: none;">
                    <div class="transcription-label">Transcription:</div>
                    <div class="transcription-text">${this.escapeHtml(text)}</div>
                </div>
                <audio preload="auto" style="display: none;"></audio>
            </div>
        `;

        messagesContainer.appendChild(voiceMsg);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // Get elements
        const audio = voiceMsg.querySelector('audio');
        const btnPlay = voiceMsg.querySelector('.btn-play-audio');
        const playIcon = voiceMsg.querySelector('.play-icon');
        const btnShowTranscription = voiceMsg.querySelector('.btn-show-transcription');
        const transcriptionDiv = voiceMsg.querySelector('.voice-transcription-hidden');

        //Set audio source - create source element for better compatibility
        const source = document.createElement('source');
        source.src = audioUrl;
        source.type = 'audio/webm';
        audio.appendChild(source);
        audio.load();

        // Log for debugging
        console.log('🔊 Audio element created:', {
            src: audioUrl,
            blobSize: audioBlob.size,
            canPlayWebm: audio.canPlayType('audio/webm')
        });

        // Play/Pause audio
        let isPlaying = false;
        btnPlay.addEventListener('click', async (e) => {
            e.preventDefault();
            e.stopPropagation();

            if (isPlaying) {
                audio.pause();
                playIcon.textContent = '▶';
                btnPlay.classList.remove('playing');
                isPlaying = false;
                console.log('⏸ Audio paused');
            } else {
                try {
                    await audio.play();
                    playIcon.textContent = '⏸';
                    btnPlay.classList.add('playing');
                    isPlaying = true;
                    console.log('🔊 Playing audio...');
                } catch (error) {
                    console.error('Error playing audio:', error);
                    isPlaying = false;
                }
            }
        });

        // Reset play button when audio ends
        audio.addEventListener('ended', () => {
            playIcon.textContent = '▶';
            btnPlay.classList.remove('playing');
            isPlaying = false;
        });

        // Show/Hide transcription
        btnShowTranscription.addEventListener('click', () => {
            if (transcriptionDiv.style.display === 'none') {
                transcriptionDiv.style.display = 'block';
                btnShowTranscription.innerHTML = '<span>📝 ✓</span>';
                btnShowTranscription.classList.add('active');
            } else {
                transcriptionDiv.style.display = 'none';
                btnShowTranscription.innerHTML = '<span>📝</span>';
                btnShowTranscription.classList.remove('active');
            }
        });
    }

    async sendToAI(text) {
        try {
            // Send directly to AI API without creating text message
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': getCsrfToken()
                },
                body: JSON.stringify({
                    message: text,
                    conversation_id: window.currentConversationId || null
                })
            });

            const data = await response.json();

            if (data.response) {
                // Update conversation ID if new conversation was created
                if (data.conversation_id && !window.currentConversationId) {
                    window.currentConversationId = data.conversation_id;
                    console.log('✅ New conversation created:', data.conversation_id);

                    // Reload sidebar to show new conversation
                    if (window.loadConversations) {
                        window.loadConversations();
                    }
                }

                // Show AI response in chat
                if (window.appendMessage) {
                    window.appendMessage('assistant', data.response);
                }
                console.log('✅ AI response received');
            } else {
                throw new Error(data.error || 'No response from AI');
            }
        } catch (error) {
            console.error('Error sending to AI:', error);
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    async transcribeAudio(audioBlob) {
        try {
            // Create FormData
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.webm');

            // Optional: Add language preference (auto-detect if not specified)
            // formData.append('language', 'en'); // or 'uk', 'ru', etc.

            // Send to server
            const response = await fetch('/api/speech-to-text', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRF-Token': getCsrfToken()
                }
            });

            const data = await response.json();

            if (data.success) {
                console.log('✅ Transcription successful:', data.text);
                console.log(`Language: ${data.language}, Duration: ${data.duration}s`);
                return data.text;
            } else {
                throw new Error(data.error || 'Transcription failed');
            }

        } catch (error) {
            console.error('Error transcribing audio:', error);
            throw error;
        }
    }

    startTimer() {
        this.timerInterval = setInterval(() => {
            const elapsed = Math.floor((Date.now() - this.recordingStartTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            this.recordingTimer.textContent =
                `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }, 1000);
    }

    stopTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
        this.recordingTimer.textContent = '00:00';
    }

    showProcessing() {
        this.voiceButton.disabled = true;
        this.voiceButton.innerHTML = '⏳ Processing...';
        this.voiceButton.classList.add('processing');
    }

    hideProcessing() {
        this.voiceButton.disabled = false;
        this.voiceButton.innerHTML = '🎤 Voice';
        this.voiceButton.classList.remove('processing');
    }

    playBeep() {
        // Play a short beep to indicate recording has started
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();

            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);

            // Short, pleasant beep (800Hz for 150ms)
            oscillator.frequency.value = 800;
            oscillator.type = 'sine';
            gainNode.gain.value = 0.1; // Quiet volume

            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.15); // 150ms duration
        } catch (error) {
            // Beep failed, no problem - just continue
            console.log('Beep sound unavailable');
        }
    }

    showError(message) {
        // Use existing notification system if available
        if (window.showNotification) {
            window.showNotification(message, 'error');
        } else {
            alert(message);
        }
    }

    showSuccess(message) {
        // Use existing notification system if available
        if (window.showNotification) {
            window.showNotification(message, 'success');
        } else {
            console.log('✅', message);
        }
    }
}

// Helper to get CSRF token
function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.content : '';
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.voiceRecorder = new VoiceRecorder();
    console.log('🎤 Voice recorder initialized');

    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
        if (window.voiceRecorder && window.voiceRecorder.stream) {
            window.voiceRecorder.stream.getTracks().forEach(track => track.stop());
            console.log('🧹 Microphone stream cleaned up');
        }
    });
});

// Simple notification system (if not already exists)
if (!window.showNotification) {
    window.showNotification = (message, type = 'info') => {
        // Find voice control container
        const voiceControl = document.querySelector('.voice-control');
        if (!voiceControl) {
            console.warn('Voice control container not found');
            return;
        }

        // Remove any existing notification
        const existing = voiceControl.querySelector('.voice-notification');
        if (existing) {
            existing.remove();
        }

        // Create notification element
        const notification = document.createElement('div');
        notification.className = `voice-notification voice-notification--${type}`;
        notification.textContent = message;

        // Add to voice control container (shows above button)
        voiceControl.appendChild(notification);

        // Animate in
        setTimeout(() => notification.classList.add('show'), 10);

        // Remove after 3 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    };
}
