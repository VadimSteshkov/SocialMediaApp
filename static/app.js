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

// Submit a new post
async function submitPost(event) {
    event.preventDefault();
    
    const messageDiv = document.getElementById('submitMessage');
    messageDiv.className = 'message';
    messageDiv.textContent = '';
    
    const user = document.getElementById('user').value;
    const text = document.getElementById('text').value;
    const tags = extractHashtags(text);
    
    const formData = {
        user: user,
        text: text,
        image: document.getElementById('image').value,
        tags: tags
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/posts`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            messageDiv.className = 'message success';
            messageDiv.textContent = `Post created successfully. Post ID: ${data.id}`;
            messageDiv.style.display = 'block';
            messageDiv.style.opacity = '1';
            document.getElementById('postForm').reset();
            
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
    
    return `
        <div class="post-card" data-post-id="${post.id}">
            <div class="post-header">
                <span class="post-user">@${escapeHtml(post.user)}</span>
                <span class="post-date">${formattedDate}</span>
            </div>
            <div class="post-text">${escapeHtml(removeHashtags(post.text))}</div>
            <img src="${escapeHtml(post.image)}" alt="Post image" class="post-image" onerror="this.style.display='none'">
            ${tagsHtml}
            <div class="post-actions">
                <button class="like-btn ${likeClass}" data-post-id="${post.id}" data-user="${escapeHtml(currentUser)}">
                    <span class="like-icon">${likeIconSvg}</span>
                    <span class="like-count">${post.likes_count || 0}</span>
                </button>
                <button class="comment-btn" data-post-id="${post.id}">
                    <span class="comment-icon">${commentIconSvg}</span>
                    <span class="comment-count">${post.comments_count || 0}</span>
                </button>
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
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Load posts when page loads (if on list section)
document.addEventListener('DOMContentLoaded', () => {
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
});

