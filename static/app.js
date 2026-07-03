async function loadAlbums() {
    const albumGrid = document.querySelector("[data-albums-grid]");

    if (!albumGrid) {
        return;
    }

    try {
        const response = await fetch("/api/albums");
        if (!response.ok) {
            throw new Error("Failed to load albums");
        }

        const albums = await response.json();
        const createTile = albumGrid.querySelector(".create-tile");
        albumGrid.innerHTML = "";

        if (createTile) {
            albumGrid.appendChild(createTile);
        }

        albums.forEach((album) => {
            const tile = document.createElement("article");
            tile.className = "album-tile album-record";
            tile.innerHTML = `
                <div class="album-cover ${album.cover_url ? "has-cover" : "no-cover"}">
                    ${album.cover_url ? `<img src="${escapeAttribute(album.cover_url)}" alt="${escapeAttribute(album.name)} cover">` : `<span class="album-cover-placeholder">No cover</span>`}
                </div>
                <span class="album-tile-title">${escapeHtml(album.name)}</span>
                <span class="album-tile-text">Created ${formatDate(album.created_at)}</span>
            `;
            albumGrid.appendChild(tile);
        });
    } catch (error) {
        albumGrid.insertAdjacentHTML(
            "beforeend",
            '<p class="album-message">Albums could not be loaded right now.</p>'
        );
    }
}

function formatDate(value) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return "recently";
    }

    return date.toLocaleDateString([], {
        year: "numeric",
        month: "short",
        day: "numeric",
    });
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}

function escapeAttribute(value) {
    return escapeHtml(value);
}

async function setupCreateAlbumForm() {
    const form = document.querySelector("[data-create-album-form]");
    const status = document.querySelector("[data-form-status]");

    if (!form) {
        return;
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const formData = new FormData(form);
        const name = String(formData.get("album-name") || "").trim();

        if (!name) {
            if (status) {
                status.textContent = "Please enter an album name.";
            }
            return;
        }

        if (status) {
            status.textContent = "Creating album...";
        }

        try {
            const formData = new FormData(form);
            const response = await fetch("/api/albums", {
                method: "POST",
                body: formData,
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Unable to create album");
            }

            form.reset();
            if (status) {
                status.textContent = `Created album ${data.name}.`;
            }

            window.setTimeout(() => {
                window.location.href = "/";
            }, 600);
        } catch (error) {
            if (status) {
                status.textContent = error.message;
            }
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    loadAlbums();
    setupCreateAlbumForm();
});