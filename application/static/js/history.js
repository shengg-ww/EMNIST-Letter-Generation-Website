let currentPage = 1;
const perPage = 20;
let loading = false;
let hasMoreEntries = true;
let debounceTimer;

// Variables to store active filters
let activeSearchLetters = '';
let activeSortBy = 'recent';
let activeFavorites = false;

let activeColormaps = [];  // New variable to store selected colormaps






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

            } else {
                starIcon.classList.remove('fa-solid', 'favorited');
                starIcon.classList.add('fa-regular');

            }
        } 
    })
    .catch(error => {
        console.error('Error toggling favorite:', error);

    });
}

document.addEventListener('DOMContentLoaded', () => {
    // Debounced letter search
    document.getElementById('search-letters').addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            activeSearchLetters = document.getElementById('search-letters').value.trim();
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

    document.getElementById('colormap-filter').addEventListener('change', () => {
        activeColormaps = Array.from(document.querySelectorAll("#colormap-filter input[type='checkbox']:checked"))
            .map(checkbox => checkbox.value);

        resetAndLoadEntries();  // Reload entries with the updated colormap filter
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
    });

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

function loadEntries(page) {
    loading = true;
    document.getElementById('loading').style.display = 'block';

    let url = `/history?page=${page}&per_page=${perPage}&sort_by=${activeSortBy}`;
    if (activeSearchLetters) url += `&search=${encodeURIComponent(activeSearchLetters)}`;  // Match Flask filter name

    if (activeFavorites) url += `&favorites=true`;

    if (activeColormaps.length > 0) url += `&colormaps=${activeColormaps.join(',')}`;

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
                const MAX_TEXT_LENGTH = 40; // Adjust limit as needed
                const isTextLong = entry.letter.length > MAX_TEXT_LENGTH;
                const shortText = entry.letter.substring(0, MAX_TEXT_LENGTH) + (isTextLong ? "..." : "");
            
                const wordCount = entry.letter.split(/\s+/).filter(word => word.length > 0).length; // Count words
                const charCount = entry.letter.length; // Count characters including spaces
            
                const card = document.createElement('div');
                card.classList.add('prediction-card');
                card.innerHTML = `
                    <div class="image-container">
                        <img src="data:image/png;base64,${entry.image_data}" class="prediction-image" alt="Generated Text ${entry.letter}">
                    </div>
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
                                     <h5 style='color:gray' class="text-preview" data-full-text="${entry.letter}">
                                        ${entry.letter.length === 1 ? "Generated Letter:" : "Generated Text:"} ${shortText}
                                    </h5>
                                    ${isTextLong ? `<button class="read-more-btn" data-expanded="false">Read More</button>` : ""}
                                    <h6 class="colormap-title">Color: ${entry.colormap}</h6>
                                    <h6 class="word-count">Words: ${wordCount} | Characters: ${charCount}</h6> 
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

// ✅ **Fix for Read More Button using Event Delegation**
document.addEventListener("click", function (event) {
    if (event.target.classList.contains("read-more-btn")) {
        const button = event.target;
        const textElement = button.previousElementSibling;
        const fullText = textElement.dataset.fullText;
        const MAX_TEXT_LENGTH = 40;

        if (button.dataset.expanded === "false") {
            textElement.textContent ="Generated Text: "+ fullText;
            button.textContent = "Show Less";
            button.dataset.expanded = "true";
        } else {
            textElement.textContent = "Generated Text: "+ fullText.substring(0, MAX_TEXT_LENGTH) + "...";
            button.textContent = "Read More";
            button.dataset.expanded = "false";
        }
    }
});

document.addEventListener('DOMContentLoaded', () => {
    // List of available colormaps
    const colormapOptions = [
        {name:'Black (Default)',value:'gray_r'},
        {name:'Inverse Background',value:'gray'},
        { name: 'Blue', value: 'Blues' },
        { name: 'Green', value: 'Greens' },
        { name: 'Red', value: 'Reds' },
        { name: 'Purple', value: 'Purples' },
        { name: 'Yellow-Blue', value: 'YlGnBu' },
        { name: 'Twilight', value: 'twilight' },
        { name: 'Inferno', value: 'inferno' },
        { name: 'Magma', value: 'magma' },
        { name: 'Plasma', value: 'plasma' },
        { name: 'Viridis', value: 'viridis' },
        { name: 'Cividis', value: 'cividis' },
        { name: 'Spectral', value: 'Spectral' },
        { name: 'CoolWarm', value: 'coolwarm' },
        { name: 'HSV', value: 'hsv' }
    ];

    // Select the dropdown container
    const colormapFilter = document.getElementById('colormap-filter');

    // Dynamically add checkboxes for each colormap
    colormapOptions.forEach(colormap => {
        const listItem = document.createElement('li');
        listItem.innerHTML = `
            <div class="form-check">
                <input class="form-check-input" type="checkbox" value="${colormap.value}" id="colormap-${colormap.value}">
                <label class="form-check-label" for="colormap-${colormap.value}">${colormap.name}</label>
            </div>
        `;
        colormapFilter.appendChild(listItem);
    });
});


document.getElementById('reset-filters').addEventListener('click', () => {
    // Reset all filter variables
    document.getElementById('search-letters').value = '';
    document.getElementById('sort-by').value = 'recent';
    document.getElementById('show-favorites').checked = false;
    document.getElementById('date-range').value = '';
    
    activeSearchLetters = '';
    activeSortBy = 'recent';
    activeFavorites = false;
  

    // Uncheck all colormap checkboxes
    document.querySelectorAll("#colormap-filter input[type='checkbox']").forEach(checkbox => {
        checkbox.checked = false;
    });
    activeColormaps = [];

    // Reload the entries with the default filters
    resetAndLoadEntries();
});
