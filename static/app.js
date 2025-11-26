const API_BASE_URL = 'http://localhost:5001/api';

// Tab navigation
function showSection(sectionId) {
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
    
    // Add active class to clicked button
    event.target.classList.add('active');
    
    // Auto-load posts when switching to list section
    if (sectionId === 'list') {
        loadAllPosts();
    }
}

// Submit a new post
async function submitPost(event) {
    event.preventDefault();
    
    const messageDiv = document.getElementById('submitMessage');
    messageDiv.className = 'message';
    messageDiv.textContent = '';
    
    const formData = {
        user: document.getElementById('user').value,
        text: document.getElementById('text').value,
        image: document.getElementById('image').value
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
            messageDiv.textContent = `Post created successfully! Post ID: ${data.id}`;
            document.getElementById('postForm').reset();
            
            // Auto-switch to list view after 2 seconds
            setTimeout(() => {
                showSection('list');
                document.querySelectorAll('.tab-button')[1].classList.add('active');
            }, 2000);
        } else {
            messageDiv.className = 'message error';
            messageDiv.textContent = `Error: ${data.error || 'Failed to create post'}`;
        }
    } catch (error) {
        messageDiv.className = 'message error';
        messageDiv.textContent = `Error: ${error.message}`;
    }
}

// Load all posts
async function loadAllPosts() {
    const postsContainer = document.getElementById('postsList');
    postsContainer.innerHTML = '<p class="loading">Loading posts...</p>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/posts`);
        const posts = await response.json();
        
        if (posts.length === 0) {
            postsContainer.innerHTML = '<p class="empty">No posts found. Be the first to post!</p>';
            return;
        }
        
        postsContainer.innerHTML = posts.map(post => createPostCard(post)).join('');
    } catch (error) {
        postsContainer.innerHTML = `<p class="error">Error loading posts: ${error.message}</p>`;
    }
}

// Search posts by user
async function searchByUser() {
    const searchInput = document.getElementById('searchUser');
    const username = searchInput.value.trim();
    const resultsContainer = document.getElementById('searchResults');
    
    if (!username) {
        resultsContainer.innerHTML = '<p class="error">Please enter a username to search.</p>';
        return;
    }
    
    resultsContainer.innerHTML = '<p class="loading">Searching...</p>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/posts/search?user=${encodeURIComponent(username)}`);
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
            resultsContainer.innerHTML = `<p class="empty">No posts found for user "${username}".</p>`;
            return;
        }
        
        resultsContainer.innerHTML = `
            <h3>Found ${data.length} post(s) by ${username}:</h3>
            ${data.map(post => createPostCard(post)).join('')}
        `;
    } catch (error) {
        resultsContainer.innerHTML = `<p class="error">Error searching posts: ${error.message}</p>`;
    }
}

// Create post card HTML
function createPostCard(post) {
    const date = new Date(post.created_at);
    const formattedDate = date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
    
    return `
        <div class="post-card">
            <div class="post-header">
                <span class="post-user">@${post.user}</span>
                <span class="post-date">${formattedDate}</span>
            </div>
            <div class="post-text">${escapeHtml(post.text)}</div>
            <img src="${escapeHtml(post.image)}" alt="Post image" class="post-image" onerror="this.style.display='none'">
        </div>
    `;
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
});

