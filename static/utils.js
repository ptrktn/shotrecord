async function loadTarget(id) {
    const response = await fetch(`/fragment/target/${id}`);
    if (response.ok) {
        const blob = await response.blob();
        const imgURL = URL.createObjectURL(blob);

        const img = document.createElement('img');
        img.src = imgURL;
        img.alt = `Image ${id}`;
        img.style.maxWidth = '100%';

        const container = document.getElementById('image-container');
        container.innerHTML = ''; // Clear previous content
        container.appendChild(img);
    } else {
        console.error('Failed to load image:', response.status);
    }
}

function heatMapStartDate() {
    var d = new Date();
    var y = d.getFullYear();
    var m = d.getMonth();

    if (11 == m) {
        m = 0;
    } else {
        d.setFullYear(d.getFullYear() - 1);
        d.setMonth(d.getMonth() + 1);
    }

    return d;
}

