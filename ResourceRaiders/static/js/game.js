// Initialize sound effects
const clickSound = new Tone.Synth({
    oscillator: { type: "sine" },
    envelope: { attack: 0.001, decay: 0.1, sustain: 0, release: 0.1 }
}).toDestination();

function playClickSound() {
    clickSound.triggerAttackRelease("C5", "32n", undefined, 0.1);
}

function vibrate() {
    if (navigator.vibrate) {
        navigator.vibrate(50);
    }
}

function updateResources() {
    fetch('/game')
        .then(response => response.text())
        .then(html => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');

            // Update resource counts
            ['wood', 'stone', 'food', 'leather'].forEach(resource => {
                const element = document.getElementById(resource);
                const newValue = doc.getElementById(resource).textContent;
                if (element.textContent !== newValue) {
                    element.textContent = newValue;
                    element.classList.add('resource-flash');
                    setTimeout(() => element.classList.remove('resource-flash'), 500);
                }
            });

            // Update production rates
            ['wood-rate', 'stone-rate', 'food-rate'].forEach(rate => {
                document.getElementById(rate).textContent = doc.getElementById(rate).textContent;
            });

            // Update building levels
            ['woodcutter-level', 'quarry-level', 'farm-level'].forEach(level => {
                document.getElementById(level).textContent = doc.getElementById(level).textContent;
            });
        });
}

// Handle building buttons
document.querySelectorAll('.build-btn').forEach(button => {
    button.addEventListener('click', function() {
        const building = this.dataset.building;
        fetch(`/api/build/${building}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const countElement = document.getElementById(`${building}-count`);
                countElement.textContent = parseInt(countElement.textContent) + 1;
                updateResources();

                // Add animation to the building card
                this.closest('.card').classList.add('building-upgrade');
                setTimeout(() => {
                    this.closest('.card').classList.remove('building-upgrade');
                }, 700);

                vibrate();
            } else {
                alert(data.message || 'Could not build structure');
            }
        });
    });
});

// Handle upgrade buttons
document.querySelectorAll('.upgrade-btn').forEach(button => {
    button.addEventListener('click', function() {
        const building = this.dataset.building;
        fetch(`/api/upgrade/${building}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const levelElement = document.getElementById(`${building}-level`);
                levelElement.textContent = parseInt(levelElement.textContent) + 1;
                updateResources();

                // Add animation to the building card
                this.closest('.card').classList.add('building-upgrade');
                setTimeout(() => {
                    this.closest('.card').classList.remove('building-upgrade');
                }, 700);

                vibrate();
            } else {
                alert(data.message || 'Could not upgrade building');
            }
        });
    });
});

// Handle resource gathering buttons
document.querySelectorAll('.gather-btn').forEach(button => {
    button.addEventListener('click', function() {
        const resource = this.dataset.resource;
        let clicks = parseInt(this.dataset.clicks);

        // Only process click if we haven't reached 10 yet
        if (clicks < 10) {
            clicks += 1;
            this.dataset.clicks = clicks;
            this.textContent = `${getResourceAction(resource)} (${clicks}/10)`;

            // Update progress bar
            const progressBar = this.querySelector('.gather-progress');
            progressBar.style.width = `${(clicks / 10) * 100}%`;

            // Play sound and vibrate
            playClickSound();
            if (clicks % 3 === 0) vibrate(); // Vibrate every 3 clicks

            // If we just hit 10 clicks, give the resource
            if (clicks === 10) {
                fetch(`/api/gather/${resource}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                })
                .then(function(response) {
                    return response.json();
                })
                .then(data => {
                    if (data.success) {
                        updateResources();
                        vibrate(); // Vibrate on resource gain
                    }
                    // Reset clicks and progress bar
                    clicks = 0;
                    button.dataset.clicks = "0";
                    button.textContent = `${getResourceAction(resource)} (0/10)`;
                    progressBar.style.width = '0%';
                });
            }
        }
    });
});

// Handle hunting button
document.getElementById('hunt-btn').addEventListener('click', function() {
    fetch('/api/hunt', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateResources();
            this.disabled = true;
            vibrate();

            // Start cooldown animation
            const overlay = this.querySelector('.cooldown-overlay');
            overlay.style.width = '100%';

            setTimeout(() => {
                this.disabled = false;
                overlay.style.width = '0%';
            }, 60000); // Re-enable after 1 minute
        }
        alert(data.message);
    });
});

function getResourceAction(resource) {
    switch(resource) {
        case 'wood': return 'Chop Wood';
        case 'stone': return 'Mine Stone';
        case 'food': return 'Gather Food';
        default: return 'Gather';
    }
}

// Update resources every second
setInterval(updateResources, 1000);