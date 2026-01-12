// State
let currentTab = 'movies';
let radarrDownloaded = new Set();
let radarrDownloading = {};  // {tmdb_id: progress}
let sonarrDownloadedTvdb = new Set();
let sonarrDownloadedTmdb = new Set();
let sonarrDownloadingTvdb = {};  // {tvdb_id: progress}
let sonarrDownloadingTmdb = {};  // {tmdb_id: progress}
let radarrProfiles = [];
let sonarrProfiles = [];
let currentItem = null;
let isSearchMode = false;
let plexUrl = 'https://app.plex.tv/desktop';

// DOM Elements
const moviesTab = document.getElementById('movies-tab');
const showsTab = document.getElementById('shows-tab');
const contentGrid = document.getElementById('content-grid');
const loading = document.getElementById('loading');
const error = document.getElementById('error');
const errorMessage = document.getElementById('error-message');
const searchInput = document.getElementById('search-input');
const searchBtn = document.getElementById('search-btn');
const clearSearchBtn = document.getElementById('clear-search-btn');
const addModal = document.getElementById('add-modal');
const modalTitle = document.getElementById('modal-title');
const qualityProfile = document.getElementById('quality-profile');
const modalCancel = document.getElementById('modal-cancel');
const modalConfirm = document.getElementById('modal-confirm');
const toastContainer = document.getElementById('toast-container');

// Initialize
async function init() {
    // Load libraries, profiles, and plex config
    await Promise.all([
        loadRadarrLibrary(),
        loadSonarrLibrary(),
        loadRadarrProfiles(),
        loadSonarrProfiles(),
        loadPlexConfig(),
    ]);

    // Load initial content
    loadContent();

    // Event listeners
    moviesTab.addEventListener('click', () => switchTab('movies'));
    showsTab.addEventListener('click', () => switchTab('shows'));
    searchBtn.addEventListener('click', search);
    clearSearchBtn.addEventListener('click', clearSearch);
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') search();
    });
    modalCancel.addEventListener('click', closeModal);
    modalConfirm.addEventListener('click', confirmAdd);
    addModal.addEventListener('click', (e) => {
        if (e.target === addModal) closeModal();
    });
}

// Tab switching
function switchTab(tab) {
    currentTab = tab;
    isSearchMode = false;
    clearSearchBtn.classList.add('hidden');
    searchInput.value = '';

    if (tab === 'movies') {
        moviesTab.classList.add('border-blue-500', 'text-blue-500');
        moviesTab.classList.remove('text-gray-400');
        showsTab.classList.remove('border-blue-500', 'text-blue-500');
        showsTab.classList.add('text-gray-400');
    } else {
        showsTab.classList.add('border-blue-500', 'text-blue-500');
        showsTab.classList.remove('text-gray-400');
        moviesTab.classList.remove('border-blue-500', 'text-blue-500');
        moviesTab.classList.add('text-gray-400');
    }

    loadContent();
}

// Load content
async function loadContent() {
    showLoading();
    hideError();

    try {
        const endpoint = currentTab === 'movies' ? '/api/movies' : '/api/shows';
        const response = await fetch(endpoint);
        const data = await response.json();

        if (data.success) {
            renderContent(data.data);
        } else {
            showError(data.error || 'Failed to load content');
        }
    } catch (e) {
        showError('Failed to connect to server');
    }

    hideLoading();
}

// Search
async function search() {
    const query = searchInput.value.trim();
    if (!query) return;

    isSearchMode = true;
    clearSearchBtn.classList.remove('hidden');
    showLoading();
    hideError();

    try {
        const endpoint = currentTab === 'movies' ? '/api/search/movies' : '/api/search/shows';
        const response = await fetch(`${endpoint}?query=${encodeURIComponent(query)}`);
        const data = await response.json();

        if (data.success) {
            renderContent(data.data);
        } else {
            showError(data.error || 'Search failed');
        }
    } catch (e) {
        showError('Failed to search');
    }

    hideLoading();
}

function clearSearch() {
    isSearchMode = false;
    searchInput.value = '';
    clearSearchBtn.classList.add('hidden');
    loadContent();
}

// Render content grid
function renderContent(items) {
    contentGrid.innerHTML = '';

    if (!items || items.length === 0) {
        contentGrid.innerHTML = '<p class="col-span-full text-center text-gray-400 py-12">No results found</p>';
        return;
    }

    items.forEach(item => {
        const card = createCard(item);
        contentGrid.appendChild(card);
    });
}

// Get item status and progress
function getItemStatus(item) {
    if (currentTab === 'movies') {
        if (radarrDownloaded.has(item.tmdb_id)) return { status: 'downloaded', progress: 100 };
        if (item.tmdb_id in radarrDownloading) return { status: 'downloading', progress: radarrDownloading[item.tmdb_id] };
    } else {
        if (sonarrDownloadedTvdb.has(item.tvdb_id) || sonarrDownloadedTmdb.has(item.tmdb_id)) return { status: 'downloaded', progress: 100 };
        if (item.tvdb_id in sonarrDownloadingTvdb) return { status: 'downloading', progress: sonarrDownloadingTvdb[item.tvdb_id] };
        if (item.tmdb_id in sonarrDownloadingTmdb) return { status: 'downloading', progress: sonarrDownloadingTmdb[item.tmdb_id] };
    }
    return { status: 'not_added', progress: 0 };
}

// Create card element
function createCard(item) {
    const div = document.createElement('div');
    div.className = 'poster-card bg-gray-800 rounded-lg overflow-hidden';

    const { status, progress } = getItemStatus(item);
    const posterUrl = item.poster || 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="200" height="300" viewBox="0 0 200 300"><rect fill="%23374151" width="200" height="300"/><text fill="%239CA3AF" font-family="sans-serif" font-size="14" x="50%" y="50%" text-anchor="middle">No Poster</text></svg>';
    const plexSearchUrl = `${plexUrl}#!/search?query=${encodeURIComponent(item.title)}`;
    const tmdbUrl = currentTab === 'movies'
        ? `https://www.themoviedb.org/movie/${item.tmdb_id}`
        : `https://www.themoviedb.org/tv/${item.tmdb_id}`;

    let actionButton;
    let statusBadge = '';

    if (status === 'downloaded') {
        actionButton = `<a href="${plexSearchUrl}" target="_blank" class="mt-2 w-full py-1 bg-orange-500 hover:bg-orange-600 rounded text-sm block text-center">Watch in Plex</a>`;
        statusBadge = '<span class="absolute top-2 right-2 bg-green-600 text-xs px-2 py-1 rounded">Downloaded</span>';
    } else if (status === 'downloading') {
        actionButton = `
            <div class="mt-2">
                <div class="flex justify-between text-xs text-gray-400 mb-1">
                    <span>Downloading</span>
                    <span>${progress}%</span>
                </div>
                <div class="w-full bg-gray-700 rounded-full h-2">
                    <div class="bg-yellow-500 h-2 rounded-full transition-all" style="width: ${progress}%"></div>
                </div>
            </div>`;
        statusBadge = `<span class="absolute top-2 right-2 bg-yellow-600 text-xs px-2 py-1 rounded">${progress}%</span>`;
    } else {
        actionButton = `<button class="add-btn mt-2 w-full py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm" data-item='${JSON.stringify(item).replace(/'/g, "&apos;")}'>Add</button>`;
    }

    div.innerHTML = `
        <a href="${tmdbUrl}" target="_blank" class="block relative cursor-pointer">
            <img src="${posterUrl}" alt="${item.title}" class="w-full aspect-[2/3] object-cover">
            ${statusBadge}
            ${item.rating ? `<span class="absolute bottom-2 left-2 bg-black/70 text-xs px-2 py-1 rounded">${item.rating}</span>` : ''}
        </a>
        <div class="p-3">
            <h3 class="font-medium text-sm truncate" title="${item.title}">${item.title}</h3>
            <p class="text-gray-400 text-xs">${item.year || 'N/A'}</p>
            ${actionButton}
        </div>
    `;

    // Add click handler for add button
    const addBtn = div.querySelector('.add-btn');
    if (addBtn) {
        addBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            openAddModal(item);
        });
    }

    return div;
}

// Modal functions
function openAddModal(item) {
    currentItem = item;
    modalTitle.textContent = `Add "${item.title}"`;

    // Load appropriate profiles
    const profiles = currentTab === 'movies' ? radarrProfiles : sonarrProfiles;
    qualityProfile.innerHTML = profiles.map(p =>
        `<option value="${p.id}">${p.name}</option>`
    ).join('');

    addModal.classList.remove('hidden');
}

function closeModal() {
    addModal.classList.add('hidden');
    currentItem = null;
}

async function confirmAdd() {
    if (!currentItem) return;

    const profileId = parseInt(qualityProfile.value);
    const endpoint = currentTab === 'movies' ? '/api/radarr/add' : '/api/sonarr/add';

    const body = currentTab === 'movies'
        ? { tmdb_id: currentItem.tmdb_id, quality_profile_id: profileId }
        : { tmdb_id: currentItem.tmdb_id, tvdb_id: currentItem.tvdb_id, quality_profile_id: profileId };

    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });

        const data = await response.json();

        if (data.success) {
            showToast(`Added "${currentItem.title}" successfully!`, 'success');

            // Update local library state (mark as downloading with 0% progress)
            if (currentTab === 'movies') {
                radarrDownloading[currentItem.tmdb_id] = 0;
            } else {
                if (currentItem.tvdb_id) sonarrDownloadingTvdb[currentItem.tvdb_id] = 0;
                if (currentItem.tmdb_id) sonarrDownloadingTmdb[currentItem.tmdb_id] = 0;
            }

            // Refresh display
            if (isSearchMode) {
                search();
            } else {
                loadContent();
            }
        } else {
            showToast(data.error || 'Failed to add', 'error');
        }
    } catch (e) {
        showToast('Failed to add: ' + e.message, 'error');
    }

    closeModal();
}

// Library loading
async function loadRadarrLibrary() {
    try {
        const response = await fetch('/api/radarr/library');
        const data = await response.json();
        if (data.success) {
            radarrDownloaded = new Set(data.data.downloaded);
            radarrDownloading = data.data.downloading;  // {tmdb_id: progress}
        }
    } catch (e) {
        console.error('Failed to load Radarr library:', e);
    }
}

async function loadSonarrLibrary() {
    try {
        const response = await fetch('/api/sonarr/library');
        const data = await response.json();
        if (data.success) {
            sonarrDownloadedTvdb = new Set(data.data.downloaded.tvdb);
            sonarrDownloadedTmdb = new Set(data.data.downloaded.tmdb);
            sonarrDownloadingTvdb = data.data.downloading.tvdb;  // {tvdb_id: progress}
            sonarrDownloadingTmdb = data.data.downloading.tmdb;  // {tmdb_id: progress}
        }
    } catch (e) {
        console.error('Failed to load Sonarr library:', e);
    }
}

async function loadRadarrProfiles() {
    try {
        const response = await fetch('/api/radarr/profiles');
        const data = await response.json();
        if (data.success) {
            radarrProfiles = data.data;
        }
    } catch (e) {
        console.error('Failed to load Radarr profiles:', e);
    }
}

async function loadSonarrProfiles() {
    try {
        const response = await fetch('/api/sonarr/profiles');
        const data = await response.json();
        if (data.success) {
            sonarrProfiles = data.data;
        }
    } catch (e) {
        console.error('Failed to load Sonarr profiles:', e);
    }
}

async function loadPlexConfig() {
    try {
        const response = await fetch('/api/plex/config');
        const data = await response.json();
        if (data.success) {
            plexUrl = data.url;
        }
    } catch (e) {
        console.error('Failed to load Plex config:', e);
    }
}

// UI helpers
function showLoading() {
    loading.classList.remove('hidden');
    contentGrid.classList.add('hidden');
}

function hideLoading() {
    loading.classList.add('hidden');
    contentGrid.classList.remove('hidden');
}

function showError(message) {
    errorMessage.textContent = message;
    error.classList.remove('hidden');
}

function hideError() {
    error.classList.add('hidden');
}

function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast px-4 py-3 rounded-lg shadow-lg ${type === 'success' ? 'bg-green-600' : 'bg-red-600'}`;
    toast.textContent = message;

    toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Start the app
init();
