const API_BASE_URL = 'http://localhost:5001/api';

// Tab navigation
function showSection(sectionId, buttonElement = null) {
    // Hide all sections
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Remove active class from all buttons
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('active');
    });
    
    // Show selected section
    document.getElementById(sectionId).classList.add('active');
    
    // Add active class to clicked button or find it by section
    if (buttonElement) {
        buttonElement.classList.add('active');
    } else {
        // Find button by section ID
        const buttons = document.querySelectorAll('.tab-button');
        const sectionMap = { 'submit': 0, 'list': 1, 'search': 2 };
        if (sectionMap[sectionId] !== undefined) {
            buttons[sectionMap[sectionId]]?.classList.add('active');
        }
    }
    
    // Auto-load posts when switching to list section
    if (sectionId === 'list') {
        loadAllPosts();
    }
}

// Check timer and update UI
async function checkTimer(user) {
    const timerInfo = document.getElementById('timerInfo');
    const submitBtn = document.getElementById('submitBtn');
    
    // Hide timer if no user entered
    if (!user || !user.trim()) {
        timerInfo.style.display = 'none';
        timerInfo.className = 'timer-info';
        submitBtn.disabled = false;
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/posts/timer/${encodeURIComponent(user)}`);
        const timerData = await response.json();
        
        const clockIcon = '<svg class="timer-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>';
        
        if (!timerData.can_post) {
            // Show timer only when there's a restriction
            const minutes = Math.floor(timerData.time_remaining / 60);
            const seconds = timerData.time_remaining % 60;
            timerInfo.className = 'timer-info timer-waiting';
            timerInfo.innerHTML = `${clockIcon} <span>Please wait ${minutes}:${seconds.toString().padStart(2, '0')} before posting again</span>`;
            timerInfo.style.display = 'flex';
            submitBtn.disabled = true;
        } else {
            // Hide timer when user can post (no restriction)
            timerInfo.className = 'timer-info timer-ready';
            timerInfo.style.display = 'none';
            submitBtn.disabled = false;
        }
    } catch (error) {
        // If error (e.g., user doesn't exist in DB), hide timer
        console.error('Error checking timer:', error);
        timerInfo.style.display = 'none';
        timerInfo.className = 'timer-info';
        submitBtn.disabled = false;
    }
}

// Update timer display periodically
let timerInterval = null;
function startTimerCheck(user) {
    if (timerInterval) clearInterval(timerInterval);
    checkTimer(user);
    timerInterval = setInterval(() => checkTimer(user), 1000);
}

function stopTimerCheck() {
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
}

// Extract hashtags from text
function extractHashtags(text) {
    if (!text) return [];
    // Match # followed by word characters, underscores, and unicode letters (supports Cyrillic, etc.)
    // Pattern: # followed by one or more word characters, underscores, or unicode letters
    const hashtagRegex = /#([\w\u0400-\u04FF]+)/g;
    const matches = text.match(hashtagRegex);
    if (!matches) return [];
    // Remove # and convert to lowercase, filter out empty strings
    return matches.map(tag => tag.substring(1).toLowerCase()).filter(tag => tag.length > 0);
}

// Detect language of text (simple heuristic)
function detectLanguage(text) {
    if (!text) return 'en';
    // Check for Cyrillic characters (Russian)
    if (/[\u0400-\u04FF]/.test(text)) {
        return 'ru';
    }
    // Check for German characters
    if (/[äöüßÄÖÜ]/.test(text)) {
        return 'de';
    }
    // Check for Spanish characters
    if (/[ñáéíóúüÑÁÉÍÓÚÜ]/.test(text)) {
        return 'es';
    }
    // Check for French characters
    if (/[àâäéèêëïîôùûüÿçÀÂÄÉÈÊËÏÎÔÙÛÜŸÇ]/.test(text)) {
        return 'fr';
    }
    // Default to English
    return 'en';
}

// Get translate link text based on language
function getTranslateLinkText(lang) {
    const translations = {
        'en': 'Translate text',
        'ru': 'Перевести текст',
        'de': 'Text übersetzen',
        'es': 'Traducir texto',
        'fr': 'Traduire le texte'
    };
    return translations[lang] || 'Translate text';
}

// Get "Show original" text based on language
function getShowOriginalText(lang) {
    const translations = {
        'en': 'Show original',
        'ru': 'Показать оригинал',
        'de': 'Original anzeigen',
        'es': 'Mostrar original',
        'fr': 'Afficher l\'original'
    };
    return translations[lang] || 'Show original';
}

// Get "Translating..." text based on language
function getTranslatingText(lang) {
    const translations = {
        'en': 'Translating...',
        'ru': 'Переводится...',
        'de': 'Übersetze...',
        'es': 'Traduciendo...',
        'fr': 'Traduction...'
    };
    return translations[lang] || 'Translating...';
}

// Generate text for post
async function generateText() {
    const textArea = document.getElementById('text');
    const generateBtn = document.getElementById('generateTextBtn');
    const messageDiv = document.getElementById('submitMessage');
    
    if (!textArea || !generateBtn) return;
    
    const currentText = textArea.value.trim();
    const tags = extractHashtags(currentText);
    
    // Extract text without tags
    const textWithoutTags = currentText.replace(/#[\w\u0400-\u04FF]+/g, '').trim();
    
    // Check if we have text or tags
    if (!textWithoutTags && tags.length === 0) {
        messageDiv.className = 'message error';
        messageDiv.textContent = 'Please enter text or tags to generate a post';
        messageDiv.style.display = 'block';
        messageDiv.style.opacity = '1';
        setTimeout(() => {
            messageDiv.style.opacity = '0';
            setTimeout(() => {
                messageDiv.style.display = 'none';
            }, 300);
        }, 3000);
        return;
    }
    
    // Disable button and show loading
    generateBtn.disabled = true;
    const textSpan = generateBtn.querySelector('span:last-child');
    if (textSpan) {
        textSpan.textContent = 'Generating...';
    }
    
    try {
        const formData = new FormData();
        if (textWithoutTags) {
            formData.append('prompt_text', textWithoutTags);
        }
        if (tags.length > 0) {
            formData.append('tags', tags.join(' '));
        }
        formData.append('max_new_tokens', '60');
        formData.append('temperature', '0.75');
        
        const response = await fetch(`${API_BASE_URL}/posts/generate-text`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok && data.generated_text) {
            // Replace text in textarea with generated text
            textArea.value = data.generated_text;
            
            // Show success message
            messageDiv.className = 'message success';
            messageDiv.textContent = 'Text generated successfully! You can edit it before submitting.';
            messageDiv.style.display = 'block';
            messageDiv.style.opacity = '1';
            
            setTimeout(() => {
                messageDiv.style.opacity = '0';
                setTimeout(() => {
                    messageDiv.style.display = 'none';
                }, 300);
            }, 3000);
        } else {
            throw new Error(data.detail || 'Failed to generate text');
        }
    } catch (error) {
        messageDiv.className = 'message error';
        messageDiv.textContent = `Error: ${error.message}`;
        messageDiv.style.display = 'block';
        messageDiv.style.opacity = '1';
        
        setTimeout(() => {
            messageDiv.style.opacity = '0';
            setTimeout(() => {
                messageDiv.style.display = 'none';
            }, 300);
        }, 5000);
    } finally {
        // Re-enable button
        generateBtn.disabled = false;
        const iconSpan = generateBtn.querySelector('.generate-text-icon');
        const textSpan = generateBtn.querySelector('span:last-child');
        if (textSpan && textSpan.textContent !== 'Generate Text') {
            textSpan.textContent = 'Generate Text';
        }
    }
}

// Submit a new post
async function submitPost(event) {
    event.preventDefault();
    
    const messageDiv = document.getElementById('submitMessage');
    messageDiv.className = 'message';
    messageDiv.textContent = '';
    
    const user = document.getElementById('user').value;
    const text = document.getElementById('text').value;
    const tags = extractHashtags(text);
    const imageInput = document.getElementById('image');
    const imageFileInput = document.getElementById('imageFile');
    
    // Check if file is uploaded or URL is provided
    const hasFile = imageFileInput && imageFileInput.files && imageFileInput.files.length > 0;
    const hasUrl = imageInput && imageInput.value.trim();
    
    if (!hasFile && !hasUrl) {
        messageDiv.className = 'message error';
        messageDiv.textContent = 'Please upload an image file or provide an image URL';
        messageDiv.style.display = 'block';
        messageDiv.style.opacity = '1';
        return;
    }
    
    try {
        let response;
        
        if (hasFile) {
            // Upload file using multipart form data
            const formData = new FormData();
            formData.append('file', imageFileInput.files[0]);
            formData.append('text', text);
            formData.append('user', user);
            if (tags.length > 0) {
                formData.append('tags', tags.join(','));
            }
            
            response = await fetch(`${API_BASE_URL}/posts/upload`, {
                method: 'POST',
                body: formData
            });
        } else {
            // Use URL endpoint (existing functionality)
            const formData = {
                user: user,
                text: text,
                image: imageInput.value,
                tags: tags
            };
            
            response = await fetch(`${API_BASE_URL}/posts`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
        }
        
        const data = await response.json();
        
        if (response.ok) {
            messageDiv.className = 'message success';
            messageDiv.textContent = `Post created successfully. Post ID: ${data.id}`;
            messageDiv.style.display = 'block';
            messageDiv.style.opacity = '1';
            
            // Reset form
            document.getElementById('postForm').reset();
            
            // Reset file upload preview
            const uploadContent = document.getElementById('fileUploadContent');
            const uploadPreview = document.getElementById('fileUploadPreview');
            const fileInput = document.getElementById('imageFile');
            const urlInput = document.getElementById('image');
            const fileUploadUrl = document.getElementById('fileUploadUrl');
            
            if (uploadContent && uploadPreview) {
                uploadContent.style.display = 'flex';
                uploadPreview.style.display = 'none';
            }
            if (fileInput) fileInput.value = '';
            if (urlInput) urlInput.value = '';
            if (fileUploadUrl) fileUploadUrl.style.display = 'none';
            
            // Restart timer check
            startTimerCheck(user);
            
            // Auto-hide success message after 3 seconds
            setTimeout(() => {
                messageDiv.style.opacity = '0';
                setTimeout(() => {
                    messageDiv.style.display = 'none';
                    messageDiv.className = 'message';
                }, 300);
            }, 3000);
            
            // Don't auto-switch to list view - user stays where they are
        } else {
            messageDiv.className = 'message error';
            let errorMsg = data.detail || 'Failed to create post';
            // Make error messages more user-friendly
            if (errorMsg.includes('database is locked')) {
                errorMsg = 'Please wait a moment and try again. Server is busy.';
            } else if (errorMsg.includes('Please wait')) {
                errorMsg = errorMsg; // Keep timer messages as is
            }
            messageDiv.textContent = errorMsg;
            messageDiv.style.display = 'block';
            messageDiv.style.opacity = '1';
            
            // Auto-hide error after 5 seconds
            setTimeout(() => {
                messageDiv.style.opacity = '0';
                setTimeout(() => {
                    messageDiv.style.display = 'none';
                    messageDiv.className = 'message';
                }, 300);
            }, 5000);
        }
    } catch (error) {
        messageDiv.className = 'message error';
        let errorMsg = error.message;
        if (errorMsg.includes('Failed to fetch') || errorMsg.includes('network')) {
            errorMsg = 'Connection problem. Please check your internet and try again.';
        }
        messageDiv.textContent = errorMsg;
        messageDiv.style.display = 'block';
        messageDiv.style.opacity = '1';
        
        // Auto-hide error after 5 seconds
        setTimeout(() => {
            messageDiv.style.opacity = '0';
            setTimeout(() => {
                messageDiv.style.display = 'none';
                messageDiv.className = 'message';
            }, 300);
        }, 5000);
    }
}

// Load all posts
async function loadAllPosts() {
    const postsContainer = document.getElementById('postsList');
    postsContainer.innerHTML = '<p class="loading">Loading posts...</p>';
    
    try {
        const currentUser = document.getElementById('user')?.value || '';
        const url = currentUser ? `${API_BASE_URL}/posts?current_user=${encodeURIComponent(currentUser)}` : `${API_BASE_URL}/posts`;
        const response = await fetch(url);
        const posts = await response.json();
        
        if (posts.length === 0) {
            postsContainer.innerHTML = '<p class="empty">No posts found. Be the first to post!</p>';
            return;
        }
        
        postsContainer.innerHTML = posts.map(post => createPostCard(post, currentUser)).join('');
        
        // Attach event listeners for likes and comments
        attachPostEventListeners();
    } catch (error) {
        postsContainer.innerHTML = `<p class="error">Error loading posts: ${error.message}</p>`;
    }
}

// Search by tag when clicking on a tag button
function searchByTagClick(tag) {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.value = `#${tag}`;
        // Switch to search tab
        showSection('search');
        // Perform search
        setTimeout(() => smartSearch(), 100);
    }
}

// Smart search - detects @username, #tag, or plain text
async function smartSearch() {
    const searchInput = document.getElementById('searchInput');
    const query = searchInput.value.trim();
    const resultsContainer = document.getElementById('searchResults');
    
    if (!query) {
        resultsContainer.innerHTML = '<p class="error">Please enter a search query.</p>';
        return;
    }
    
    resultsContainer.innerHTML = '<p class="loading">Searching...</p>';
    
    try {
        const currentUser = document.getElementById('user')?.value || '';
        let url = '';
        
        // Detect search type
        if (query.startsWith('@')) {
            // User search
            const username = query.substring(1);
            url = currentUser 
                ? `${API_BASE_URL}/posts/search?user=${encodeURIComponent(username)}&current_user=${encodeURIComponent(currentUser)}`
                : `${API_BASE_URL}/posts/search?user=${encodeURIComponent(username)}`;
        } else if (query.startsWith('#')) {
            // Tag search - only when # is present
            const tag = query.substring(1).trim().toLowerCase();
            if (!tag) {
                resultsContainer.innerHTML = '<p class="error">Please enter a tag after # (e.g., #study)</p>';
                return;
            }
            url = currentUser 
                ? `${API_BASE_URL}/posts/search?tag=${encodeURIComponent(tag)}&current_user=${encodeURIComponent(currentUser)}`
                : `${API_BASE_URL}/posts/search?tag=${encodeURIComponent(tag)}`;
        } else {
            // Text search - searches in post content, NOT in tags
            url = currentUser 
                ? `${API_BASE_URL}/posts/search?text=${encodeURIComponent(query)}&current_user=${encodeURIComponent(currentUser)}`
                : `${API_BASE_URL}/posts/search?text=${encodeURIComponent(query)}`;
        }
        
        const response = await fetch(url);
        const data = await response.json();
        
        if (!response.ok) {
            let errorMsg = 'Failed to search posts';
            if (data.detail) {
                if (Array.isArray(data.detail)) {
                    errorMsg = data.detail.map(e => e.msg || e).join(', ');
                } else if (typeof data.detail === 'string') {
                    errorMsg = data.detail;
                } else {
                    errorMsg = JSON.stringify(data.detail);
                }
            }
            resultsContainer.innerHTML = `<p class="error">Error: ${errorMsg}</p>`;
            return;
        }
        
        if (!Array.isArray(data)) {
            resultsContainer.innerHTML = `<p class="error">Error: Invalid response format</p>`;
            return;
        }
        
        if (data.length === 0) {
            resultsContainer.innerHTML = `<p class="empty">No posts found for "${query}".</p>`;
            return;
        }
        
        const searchType = query.startsWith('@') ? 'user' : query.startsWith('#') ? 'tag' : 'text';
        resultsContainer.innerHTML = `
            <h3>Found ${data.length} post(s):</h3>
            ${data.map(post => createPostCard(post, currentUser)).join('')}
        `;
        
        attachPostEventListeners();
    } catch (error) {
        resultsContainer.innerHTML = `<p class="error">Error searching posts: ${error.message}</p>`;
    }
}

// Highlight hashtags in text
function highlightHashtags(text) {
    return text.replace(/#(\w+)/g, '<span class="hashtag-in-text">#$1</span>');
}

// Remove hashtags from text (since they're displayed as tags below)
function removeHashtags(text) {
    if (!text) return '';
    // Remove all hashtags (#word) from text
    let cleaned = text.replace(/#\w+/g, '').trim();
    // Replace multiple spaces with single space
    cleaned = cleaned.replace(/\s+/g, ' ');
    return cleaned;
}

// Create post card HTML
function createPostCard(post, currentUser = '') {
    const date = new Date(post.created_at);
    const formattedDate = date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
    
    // Get tags from post or extract from text if not available
    let tags = post.tags || [];
    if ((!tags || tags.length === 0) && post.text) {
        tags = extractHashtags(post.text);
    }
    
    // Always show tags section if tags exist
    const tagsHtml = tags && tags.length > 0 
        ? `<div class="post-tags-below-image">${tags.map(tag => `<span class="tag-button" onclick="searchByTagClick('${escapeHtml(tag)}')">#${escapeHtml(tag)}</span>`).join('')}</div>`
        : '';
    
    const likeClass = post.is_liked ? 'liked' : '';
    const likeIconSvg = post.is_liked 
        ? '<svg class="like-icon-svg" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>'
        : '<svg class="like-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>';
    
    const commentIconSvg = '<svg class="comment-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>';
    
    // Use thumbnail if available, otherwise use full image
    const imageUrl = post.image_thumbnail || post.image;
    const fullImageUrl = post.image;
    const hasThumbnail = post.image_thumbnail && post.image_thumbnail !== post.image;
    
    // Sentiment icon (green for positive, red for negative, yellow for neutral)
    let sentimentIcon = '';
    if (post.sentiment) {
        let sentimentColor = '';
        let sentimentIconName = '';
        if (post.sentiment === 'POSITIVE') {
            sentimentColor = '#2E7D32'; // Dark green
            sentimentIconName = 'sentiment_very_satisfied';
        } else if (post.sentiment === 'NEGATIVE') {
            sentimentColor = '#C62828'; // Dark red
            sentimentIconName = 'mood_bad';
        } else {
            sentimentColor = '#F57F17'; // Dark yellow/orange
            sentimentIconName = 'sentiment_neutral';
        }
        sentimentIcon = `<div class="sentiment-btn" style="background-color: ${sentimentColor};" title="Sentiment: ${post.sentiment}">
            <span class="material-symbols-outlined sentiment-icon">${sentimentIconName}</span>
        </div>`;
    }
    
    // Image HTML with click handler for full-size view with comments
    const imageHtml = `<div class="post-image-container">
        <img src="${escapeHtml(imageUrl)}" alt="Post image" class="post-image ${hasThumbnail ? 'post-image-thumbnail' : ''}" 
             onclick="showFullImageWithComments(${post.id}, '${escapeHtml(fullImageUrl)}', '${escapeHtml(post.user)}', '${escapeHtml(removeHashtags(post.text).replace(/'/g, "\\'"))}', '${escapeHtml(currentUser)}')" 
             onerror="this.style.display='none'"
             style="cursor: pointer;">
       </div>`;
    
    return `
        <div class="post-card" data-post-id="${post.id}">
            <div class="post-header">
                <span class="post-user">@${escapeHtml(post.user)}</span>
                <span class="post-date">${formattedDate}</span>
            </div>
            <div class="post-text" id="post-text-${post.id}">${escapeHtml(removeHashtags(post.text))}</div>
            <div class="translate-link-container">
                <a href="#" class="translate-link" data-post-id="${post.id}" data-original-text="${escapeHtml(removeHashtags(post.text).replace(/"/g, '&quot;'))}" data-post-lang="${detectLanguage(post.text)}">${getTranslateLinkText(detectLanguage(post.text))}</a>
            </div>
            ${imageHtml}
            ${tagsHtml}
            <div class="post-actions">
                <div class="post-actions-left">
                    <button class="like-btn ${likeClass}" data-post-id="${post.id}" data-user="${escapeHtml(currentUser)}">
                        <span class="like-icon">${likeIconSvg}</span>
                        <span class="like-count">${post.likes_count || 0}</span>
                    </button>
                    <button class="comment-btn" data-post-id="${post.id}">
                        <span class="comment-icon">${commentIconSvg}</span>
                        <span class="comment-count">${post.comments_count || 0}</span>
                    </button>
                </div>
                ${sentimentIcon}
            </div>
            <div class="comments-section" id="comments-${post.id}" style="display: none;">
                <div class="comments-list" id="comments-list-${post.id}"></div>
                <div class="add-comment">
                    <input type="text" id="comment-input-${post.id}" placeholder="Write a comment..." class="comment-input" data-post-id="${post.id}" data-user="${escapeHtml(currentUser)}">
                    <button class="btn btn-primary btn-small comment-submit-btn" data-post-id="${post.id}" data-user="${escapeHtml(currentUser)}">Post</button>
                </div>
            </div>
        </div>
    `;
}

// Toggle like on a post
async function toggleLike(postId, user) {
    if (!user) {
        alert('Please enter your username in the form first');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/posts/${postId}/like?user=${encodeURIComponent(user)}`, {
            method: 'POST'
        });
        const data = await response.json();
        
        // Update the like button
        const likeBtn = document.querySelector(`.like-btn[data-post-id="${postId}"]`);
        const likeIcon = likeBtn.querySelector('.like-icon');
        const likeCount = likeBtn.querySelector('.like-count');
        
        if (data.liked) {
            likeBtn.classList.add('liked');
            likeIcon.innerHTML = '<svg class="like-icon-svg" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>';
        } else {
            likeBtn.classList.remove('liked');
            likeIcon.innerHTML = '<svg class="like-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>';
        }
        likeCount.textContent = data.likes_count;
    } catch (error) {
        console.error('Error toggling like:', error);
        alert('Failed to toggle like');
    }
}

// Toggle comments section
async function toggleComments(postId) {
    const commentsSection = document.getElementById(`comments-${postId}`);
    const commentsList = document.getElementById(`comments-list-${postId}`);
    
    if (commentsSection.style.display === 'none') {
        commentsSection.style.display = 'block';
        await loadComments(postId);
    } else {
        commentsSection.style.display = 'none';
    }
}

// Load comments for a post
async function loadComments(postId) {
    const commentsList = document.getElementById(`comments-list-${postId}`);
    commentsList.innerHTML = '<p class="loading">Loading comments...</p>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/posts/${postId}/comments`);
        const comments = await response.json();
        
        if (comments.length === 0) {
            commentsList.innerHTML = '<p class="empty">No comments yet. Be the first to comment!</p>';
            return;
        }
        
        commentsList.innerHTML = comments.map(comment => {
            const date = new Date(comment.created_at);
            const formattedDate = date.toLocaleString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
            return `
                <div class="comment">
                    <div class="comment-header">
                        <span class="comment-user">@${escapeHtml(comment.user)}</span>
                        <span class="comment-date">${formattedDate}</span>
                    </div>
                    <div class="comment-text">${escapeHtml(comment.text)}</div>
                </div>
            `;
        }).join('');
    } catch (error) {
        commentsList.innerHTML = `<p class="error">Error loading comments: ${error.message}</p>`;
    }
}

// Add a comment
async function addComment(postId, user) {
    if (!user) {
        alert('Please enter your username in the form first');
        return;
    }
    
    const commentInput = document.getElementById(`comment-input-${postId}`);
    const text = commentInput.value.trim();
    
    if (!text) {
        alert('Please enter a comment');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/posts/${postId}/comments`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user: user,
                text: text
            })
        });
        
        if (response.ok) {
            commentInput.value = '';
            await loadComments(postId);
            
            // Update comment count
            const commentBtn = document.querySelector(`.comment-btn[data-post-id="${postId}"]`);
            const commentCount = commentBtn.querySelector('.comment-count');
            const currentCount = parseInt(commentCount.textContent) || 0;
            commentCount.textContent = currentCount + 1;
        } else {
            const data = await response.json();
            alert(`Error: ${data.detail || 'Failed to add comment'}`);
        }
    } catch (error) {
        console.error('Error adding comment:', error);
        alert('Failed to add comment');
    }
}

// Attach event listeners for post interactions
function attachPostEventListeners() {
    // Like buttons
    document.querySelectorAll('.like-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const postId = parseInt(this.getAttribute('data-post-id'));
            const user = this.getAttribute('data-user') || document.getElementById('user')?.value || '';
            toggleLike(postId, user);
        });
    });
    
    // Comment toggle buttons
    document.querySelectorAll('.comment-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const postId = parseInt(this.getAttribute('data-post-id'));
            toggleComments(postId);
        });
    });
    
    // Comment submit buttons
    document.querySelectorAll('.comment-submit-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const postId = parseInt(this.getAttribute('data-post-id'));
            const user = this.getAttribute('data-user') || document.getElementById('user')?.value || '';
            addComment(postId, user);
        });
    });
    
    // Comments can be submitted with Enter key
    document.querySelectorAll('.comment-input').forEach(input => {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const postId = parseInt(this.getAttribute('data-post-id'));
                const user = this.getAttribute('data-user') || document.getElementById('user')?.value || '';
                addComment(postId, user);
            }
        });
    });
    
    // Translate links
    document.querySelectorAll('.translate-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const postId = parseInt(this.getAttribute('data-post-id'));
            const originalText = this.getAttribute('data-original-text');
            const postLang = this.getAttribute('data-post-lang') || 'en';
            translatePost(postId, originalText, this, postLang);
        });
    });
}

// Translate post text
async function translatePost(postId, originalText, linkElement, postLang = 'en') {
    if (linkElement.classList.contains('translating')) {
        return; // Already translating
    }
    
    const postTextElement = document.getElementById(`post-text-${postId}`);
    if (!postTextElement) {
        return;
    }
    
    // Decode HTML entities for comparison
    const decodeHtml = (html) => {
        const txt = document.createElement('textarea');
        txt.innerHTML = html;
        return txt.value;
    };
    
    const decodedOriginal = decodeHtml(originalText);
    const currentText = postTextElement.textContent.trim();
    const isTranslated = currentText !== decodedOriginal;
    
    // Determine target language (translate to German if post is not German, otherwise translate to English)
    const targetLang = postLang === 'en' ? 'de' : 'en';
    
    if (isTranslated) {
        // Revert to original
        postTextElement.textContent = decodedOriginal;
        linkElement.textContent = getTranslateLinkText(postLang);
        linkElement.classList.remove('translating');
        return;
    }
    
    // Start translation
    linkElement.classList.add('translating');
    linkElement.textContent = getTranslatingText(postLang);
    
    try {
        const formData = new FormData();
        formData.append('target_lang', targetLang);
        formData.append('source_lang', postLang);
        
        const response = await fetch(`${API_BASE_URL}/posts/${postId}/translate`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(errorData.detail || `HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.translated_text) {
            // Replace text with translated version
            postTextElement.textContent = data.translated_text;
            linkElement.textContent = getShowOriginalText(postLang);
            linkElement.classList.remove('translating');
        } else {
            throw new Error(data.detail || 'Failed to translate text');
        }
    } catch (error) {
        console.error('Error translating post:', error);
        const errorMsg = postLang === 'ru' 
            ? `Ошибка перевода: ${error.message}` 
            : `Translation error: ${error.message}`;
        alert(errorMsg);
        linkElement.textContent = getTranslateLinkText(postLang);
        linkElement.classList.remove('translating');
    }
}

// Show full-size image in modal
function showFullImage(imageUrl) {
    // Create modal overlay
    const modal = document.createElement('div');
    modal.className = 'image-modal';
    modal.innerHTML = `
        <div class="image-modal-content">
            <span class="image-modal-close" onclick="this.parentElement.parentElement.remove()">&times;</span>
            <img src="${escapeHtml(imageUrl)}" alt="Full size image" class="image-modal-image">
        </div>
    `;
    
    // Close on background click
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.remove();
        }
    });
    
    // Close on Escape key
    const closeHandler = function(e) {
        if (e.key === 'Escape') {
            modal.remove();
            document.removeEventListener('keydown', closeHandler);
        }
    };
    document.addEventListener('keydown', closeHandler);
    
    document.body.appendChild(modal);
}

// Show full-size image with comments in Instagram-like modal
async function showFullImageWithComments(postId, imageUrl, postUser, postText, currentUser) {
    // Create modal overlay
    const modal = document.createElement('div');
    modal.className = 'image-modal-instagram';
    modal.id = `image-modal-${postId}`;
    
    // Load comments
    let commentsHtml = '<div class="modal-comments-loading">Loading comments...</div>';
    try {
        const commentsResponse = await fetch(`${API_BASE_URL}/posts/${postId}/comments`);
        const comments = await commentsResponse.json();
        
        if (comments.length === 0) {
            commentsHtml = '<div class="modal-comments-empty">No comments yet. Be the first to comment!</div>';
        } else {
            commentsHtml = comments.map(comment => {
                const date = new Date(comment.created_at);
                const formattedDate = date.toLocaleString('en-US', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });
                return `
                    <div class="modal-comment">
                        <div class="modal-comment-header">
                            <span class="modal-comment-user">@${escapeHtml(comment.user)}</span>
                            <span class="modal-comment-date">${formattedDate}</span>
                        </div>
                        <div class="modal-comment-text">${escapeHtml(comment.text)}</div>
                    </div>
                `;
            }).join('');
        }
    } catch (error) {
        commentsHtml = '<div class="modal-comments-error">Error loading comments</div>';
    }
    
    // Get tags from stored post data or extract from text
    const postData = window.currentPostData && window.currentPostData[postId];
    let tags = [];
    if (postData && postData.tags) {
        tags = postData.tags;
    } else {
        // Try to extract from text
        const hashtagMatches = postText.match(/#[\w\u0400-\u04FF]+/g);
        if (hashtagMatches) {
            tags = hashtagMatches.map(tag => tag.substring(1).toLowerCase());
        }
    }
    const tagsHtml = tags && tags.length > 0 
        ? `<div class="modal-tags">${tags.map(tag => `<span class="modal-tag">#${escapeHtml(tag)}</span>`).join('')}</div>`
        : '';
    
    modal.innerHTML = `
        <div class="image-modal-instagram-content">
            <button class="image-modal-close-btn" onclick="document.getElementById('image-modal-${postId}').remove()">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
            </button>
            <div class="modal-left">
                <img src="${escapeHtml(imageUrl)}" alt="Full size image" class="modal-full-image">
            </div>
            <div class="modal-right">
                <div class="modal-header">
                    <span class="modal-username">@${escapeHtml(postUser)}</span>
                </div>
                <div class="modal-post-text">${escapeHtml(postText)}</div>
                ${tagsHtml}
                <div class="modal-comments-section">
                    <div class="modal-comments-list" id="modal-comments-${postId}">
                        ${commentsHtml}
                    </div>
                </div>
                <div class="modal-add-comment">
                    <input type="text" id="modal-comment-input-${postId}" placeholder="Add a comment..." class="modal-comment-input" data-post-id="${postId}" data-user="${escapeHtml(currentUser)}">
                    <button class="modal-comment-submit" data-post-id="${postId}" data-user="${escapeHtml(currentUser)}">Post</button>
                </div>
            </div>
        </div>
    `;
    
    // Close on background click
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.remove();
        }
    });
    
    // Close on Escape key
    const closeHandler = function(e) {
        if (e.key === 'Escape') {
            modal.remove();
            document.removeEventListener('keydown', closeHandler);
        }
    };
    document.addEventListener('keydown', closeHandler);
    
    // Add comment functionality
    const commentInput = modal.querySelector(`#modal-comment-input-${postId}`);
    const commentSubmit = modal.querySelector(`.modal-comment-submit[data-post-id="${postId}"]`);
    const commentsList = modal.querySelector(`#modal-comments-${postId}`);
    
    const submitComment = async () => {
        if (!currentUser) {
            alert('Please enter your username first');
            return;
        }
        
        const text = commentInput.value.trim();
        if (!text) return;
        
        try {
            const response = await fetch(`${API_BASE_URL}/posts/${postId}/comments`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user: currentUser,
                    text: text
                })
            });
            
            if (response.ok) {
                commentInput.value = '';
                // Reload comments
                const commentsResponse = await fetch(`${API_BASE_URL}/posts/${postId}/comments`);
                const comments = await commentsResponse.json();
                
                if (comments.length === 0) {
                    commentsList.innerHTML = '<div class="modal-comments-empty">No comments yet. Be the first to comment!</div>';
                } else {
                    commentsList.innerHTML = comments.map(comment => {
                        const date = new Date(comment.created_at);
                        const formattedDate = date.toLocaleString('en-US', {
                            year: 'numeric',
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                        });
                        return `
                            <div class="modal-comment">
                                <div class="modal-comment-header">
                                    <span class="modal-comment-user">@${escapeHtml(comment.user)}</span>
                                    <span class="modal-comment-date">${formattedDate}</span>
                                </div>
                                <div class="modal-comment-text">${escapeHtml(comment.text)}</div>
                            </div>
                        `;
                    }).join('');
                }
            }
        } catch (error) {
            console.error('Error adding comment:', error);
            alert('Failed to add comment');
        }
    };
    
    if (commentSubmit) {
        commentSubmit.addEventListener('click', submitComment);
    }
    
    if (commentInput) {
        commentInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                submitComment();
            }
        });
    }
    
    document.body.appendChild(modal);
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// File upload drag and drop functionality
function initFileUpload() {
    const dropzone = document.getElementById('fileDropzone');
    const fileInput = document.getElementById('imageFile');
    const uploadContent = document.getElementById('fileUploadContent');
    const uploadPreview = document.getElementById('fileUploadPreview');
    const previewImage = document.getElementById('previewImage');
    const previewFilename = document.getElementById('previewFilename');
    const removeImageBtn = document.getElementById('removeImageBtn');
    const urlToggleBtn = document.getElementById('urlToggleBtn');
    const fileUploadUrl = document.getElementById('fileUploadUrl');
    const urlInput = document.getElementById('image');
    const urlRemoveBtn = document.getElementById('urlRemoveBtn');
    
    if (!dropzone || !fileInput) return;
    
    // Click to browse
    dropzone.addEventListener('click', function(e) {
        // Don't trigger if clicking on remove button, preview image, or URL elements
        if (e.target !== removeImageBtn && 
            !e.target.closest('.remove-image-btn') && 
            e.target.tagName !== 'IMG' &&
            !e.target.closest('.file-upload-preview') &&
            !e.target.closest('.file-upload-url') &&
            e.target !== urlToggleBtn &&
            !e.target.closest('.url-toggle-btn')) {
            fileInput.click();
        }
    });
    
    // Also make the browse text clickable
    const browseText = dropzone.querySelector('.upload-browse');
    if (browseText) {
        browseText.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            fileInput.click();
        });
    }
    
    // File input change - Safari compatible
    fileInput.addEventListener('change', function(e) {
        const files = e.target.files || (e.dataTransfer && e.dataTransfer.files);
        if (files && files.length > 0) {
            handleFileSelect(files);
        }
    });
    
    // Safari fallback - if change event doesn't fire properly
    fileInput.addEventListener('input', function(e) {
        const files = e.target.files;
        if (files && files.length > 0) {
            handleFileSelect(files);
        }
    });
    
    // Drag and drop events (Safari compatible with better visual feedback)
    let dragCounter = 0;
    
    dropzone.addEventListener('dragenter', function(e) {
        e.preventDefault();
        e.stopPropagation();
        dragCounter++;
        // Safari fix - force repaint
        dropzone.style.display = 'none';
        dropzone.offsetHeight; // Trigger reflow
        dropzone.style.display = '';
        dropzone.classList.add('drag-over');
    });
    
    dropzone.addEventListener('dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
        // Safari fix
        if (e.dataTransfer) {
            e.dataTransfer.dropEffect = 'copy';
        }
        // Keep drag-over class active
        if (!dropzone.classList.contains('drag-over')) {
            dropzone.classList.add('drag-over');
        }
    });
    
    dropzone.addEventListener('dragleave', function(e) {
        e.preventDefault();
        e.stopPropagation();
        dragCounter--;
        // Only remove class if truly leaving the dropzone
        if (dragCounter === 0) {
            dropzone.classList.remove('drag-over');
        }
    });
    
    dropzone.addEventListener('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        dragCounter = 0;
        dropzone.classList.remove('drag-over');
        
        const files = e.dataTransfer ? e.dataTransfer.files : null;
        if (files && files.length > 0) {
            handleFileSelect(files);
        }
    });
    
    // Handle file selection
    function handleFileSelect(files) {
        const file = files[0];
        if (!file) return;
        
        // Check if it's an image
        if (!file.type.startsWith('image/')) {
            alert('Please select an image file');
            return;
        }
        
        // Check file size (10MB max)
        if (file.size > 10 * 1024 * 1024) {
            alert('File size must be less than 10MB');
            return;
        }
        
        // Hide URL input if shown
        fileUploadUrl.style.display = 'none';
        urlInput.value = '';
        
        // Show preview
        const reader = new FileReader();
        reader.onload = function(e) {
            previewImage.src = e.target.result;
            previewFilename.textContent = file.name;
            uploadContent.style.display = 'none';
            uploadPreview.style.display = 'block';
        };
        reader.readAsDataURL(file);
        
        // Set file input (Safari compatible)
        try {
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            fileInput.files = dataTransfer.files;
        } catch (e) {
            // Safari fallback - use FileList directly if DataTransfer not supported
            // The file is already selected via the input change event
            console.log('Using fallback file selection method');
        }
    }
    
    // Remove image
    if (removeImageBtn) {
        removeImageBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            fileInput.value = '';
            uploadContent.style.display = 'flex';
            uploadPreview.style.display = 'none';
            previewImage.src = '';
            previewFilename.textContent = '';
        });
    }
    
    // Toggle URL input
    if (urlToggleBtn) {
        urlToggleBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            if (fileUploadUrl.style.display === 'none') {
                fileUploadUrl.style.display = 'flex';
                // Clear file input
                fileInput.value = '';
                uploadContent.style.display = 'flex';
                uploadPreview.style.display = 'none';
            } else {
                fileUploadUrl.style.display = 'none';
                urlInput.value = '';
            }
        });
    }
    
    // Remove URL
    if (urlRemoveBtn) {
        urlRemoveBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            urlInput.value = '';
            fileUploadUrl.style.display = 'none';
        });
    }
}

// Load posts when page loads (if on list section)
document.addEventListener('DOMContentLoaded', () => {
    // Initialize file upload
    initFileUpload();
    
    // Check if we're on the list section
    const listSection = document.getElementById('list');
    if (listSection && listSection.classList.contains('active')) {
        loadAllPosts();
    }
    
    // Start timer check when user enters username
    const userInput = document.getElementById('user');
    if (userInput) {
        userInput.addEventListener('input', function() {
            const user = this.value.trim();
            const timerInfo = document.getElementById('timerInfo');
            if (user) {
                startTimerCheck(user);
            } else {
                stopTimerCheck();
                // Hide timer when username is cleared
                if (timerInfo) {
                    timerInfo.style.display = 'none';
                    timerInfo.className = 'timer-info';
                }
                const submitBtn = document.getElementById('submitBtn');
                if (submitBtn) {
                    submitBtn.disabled = false;
                }
            }
        });
        
        // Check timer on page load if username is already filled
        if (userInput.value.trim()) {
            startTimerCheck(userInput.value.trim());
        } else {
            // Hide timer if username is empty
            const timerInfo = document.getElementById('timerInfo');
            if (timerInfo) {
                timerInfo.style.display = 'none';
                timerInfo.className = 'timer-info';
            }
        }
    }
    
    // Search on Enter key
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                smartSearch();
            }
        });
    }
    
    // Generate text button
    const generateTextBtn = document.getElementById('generateTextBtn');
    if (generateTextBtn) {
        generateTextBtn.addEventListener('click', generateText);
    }
});

