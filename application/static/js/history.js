let currentPage = 1;
const perPage = 20;
let loading = false;
let hasMoreEntries = true;
let debounceTimer;

// Variables to store active filters
let activeSearchLetters = '';
let activeSortBy = 'recent';
let activeFavorites = false;
let activeStartDate = '';
let activeEndDate = '';


// Initialize Flatpickr Date Range Picker
flatpickr("#date-range", {
    mode: "range",
    dateFormat: "Y-m-d",
    onChange: (selectedDates) => {
        if (selectedDates.length === 2) {
            activeStartDate = selectedDates[0].toISOString().split('T')[0];
            activeEndDate = selectedDates[1].toISOString().split('T')[0];
        } else {
            activeStartDate = '';
            activeEndDate = '';
        }
        resetAndLoadEntries();  // Reload entries with new date range
    }
});
// Function to display flash messages
function showFlashMessage(message, type = 'success') {
    const flashContainer = document.getElementById('flash-messages');
    const flashMessage = document.createElement('div');
    flashMessage.className = `flash-message flash-${type}`;
    flashMessage.textContent = message;

    flashContainer.appendChild(flashMessage);

    // Remove the flash message after 3 seconds
    setTimeout(() => {
        flashMessage.remove();
    }, 3000);
}

function toggleFavorite(entryId, form) {
    fetch(`/toggle_favorite/${entryId}`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const starIcon = form.querySelector('i');
            if (data.is_favorite) {
                starIcon.classList.remove('fa-regular');
                starIcon.classList.add('fa-solid', 'favorited');
                showFlashMessage('Added to favorites!');
            } else {
                starIcon.classList.remove('fa-solid', 'favorited');
                starIcon.classList.add('fa-regular');
                showFlashMessage('Removed from favorites!', 'info');
            }
        } else {
            showFlashMessage('Failed to update favorite.', 'error');
        }
    })
    .catch(error => {
        console.error('Error toggling favorite:', error);
        showFlashMessage('An error occurred while updating favorite.', 'error');
    });
}




document.addEventListener('DOMContentLoaded', () => {
    // Debounced letter search
    document.getElementById('search-letters').addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            activeSearchLetters = document.getElementById('search-letters').value.trim().toUpperCase();
            resetAndLoadEntries();  // Reload entries with new search letters
        }, 300);
    });

    // Favorites filter toggle
    document.getElementById('show-favorites').addEventListener('change', () => {
        activeFavorites = document.getElementById('show-favorites').checked;
        resetAndLoadEntries();  // Reload entries with new favorites filter
    });

    // Sorting filter change
    document.getElementById('sort-by').addEventListener('change', () => {
        activeSortBy = document.getElementById('sort-by').value;
        resetAndLoadEntries();  // Reload entries with new sort order
    });

    // Infinite scroll trigger
    window.addEventListener('scroll', () => {
        if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - 100 && !loading && hasMoreEntries) {
            currentPage++;
            loadEntries(currentPage);  // Load next page with current filters
        }
    });
  // Delegate the favorite and delete actions
  document.getElementById('entries-container').addEventListener('click', function(event) {
      // Handle Favorite Click
      if (event.target.closest('.favorite-btn')) {
          event.preventDefault();
          const form = event.target.closest('form');
          const entryId = form.dataset.entryId;
          toggleFavorite(entryId, form);
      }


  })
    // Initial load
    loadEntries(currentPage);
});

// Function to reset entries and reload the first page
function resetAndLoadEntries() {
    currentPage = 1;
    hasMoreEntries = true;
    document.getElementById('entries-container').innerHTML = '';
    loadEntries(currentPage);
}

// Load entries with current filters
function loadEntries(page) {
    loading = true;
    document.getElementById('loading').style.display = 'block';

    // Build URL with active filters
    let url = `/history?page=${page}&per_page=${perPage}&sort_by=${activeSortBy}`;

    if (activeSearchLetters) url += `&letters=${activeSearchLetters}`;
    if (activeFavorites) url += `&favorites=true`;
    if (activeStartDate && activeEndDate) {
        url += `&start_date=${activeStartDate}&end_date=${activeEndDate}`;
    }

    fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('entries-container');

            if (data.entries.length === 0 && page === 1) {
                container.innerHTML = '<p class="text-center" style="color:white">No entries found for the selected filters.</p>';
                hasMoreEntries = false;
                document.getElementById('loading').style.display = 'none';
                return;
            }

            data.entries.forEach(entry => {
                const card = document.createElement('div');
                card.classList.add('prediction-card');
                card.innerHTML = `
                    <img src="data:image/png;base64,${entry.image_data}" class="prediction-image" alt="Generated Letter ${entry.letter}">
                    <div class="card-content">
                        <div class="card-header">
                            <div class="row">
                                <div class="col-3">
                                    <form action="/toggle_favorite/${entry.id}" method="POST" class="favorite-form" data-entry-id="${entry.id}">
                                        <button type="submit" class="favorite-btn" title="Mark as Favorite">
                                            ${entry.is_favorite 
                                                ? '<i class="fa-solid fa-star favorited"></i>' 
                                                : '<i class="fa-regular fa-star"></i>'}
                                        </button>
                                    </form>
                                </div>
                                <div class="col-9">
                                    <h5 class="prediction-letter">Generated Letter: ${entry.letter}</h5>
                                </div>
                            </div>
                        </div>
                        <p class="prediction-date">Generated on: ${entry.timestamp}</p>
                        <form action="/remove/${entry.id}" method="POST" class="delete-form" data-entry-id="${entry.id}">
                            <button type="submit" class="delete-btn">
                                <i class="fa-solid fa-trash"></i> Delete
                            </button>
                        </form>
                    </div>
                `;
                container.appendChild(card);
            });
            

            if (!data.has_next) {
                hasMoreEntries = false;
                document.getElementById('end-of-content').style.display = 'block';
            }

            document.getElementById('loading').style.display = 'none';
            loading = false;
        })
        .catch(error => {
            console.error('Error loading entries:', error);
            document.getElementById('loading').style.display = 'none';
            loading = false;
        });
}

