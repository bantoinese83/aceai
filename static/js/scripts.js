document.addEventListener('DOMContentLoaded', function() {
    function showLoader() {
        const loader = document.getElementById('skeleton-loader');
        if (loader) {
            loader.style.display = 'block';
        } else {
            console.error('Loader element not found');
        }
    }

    function requestAudioPermissions() {
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(function(stream) {
                console.log('Audio permissions granted');
                const checkMark = document.getElementById('check-mark');
                const requestButton = document.getElementById('request-permission-button');
                if (checkMark) {
                    checkMark.classList.add('granted');
                } else {
                    console.error('Check mark element not found');
                }
                if (requestButton) {
                    requestButton.classList.add('granted');
                } else {
                    console.error('Request permission button not found');
                }
            })
            .catch(function(err) {
                console.error('Error accessing audio permissions:', err);
                alert('Error accessing audio permissions. Please check your browser settings.');
            });
    }

    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function(event) {
            showLoader();
        });
    } else {
        console.error('Form element not found');
    }

    const requestPermissionButton = document.getElementById('request-permission-button');
    if (requestPermissionButton) {
        requestPermissionButton.addEventListener('click', function() {
            requestAudioPermissions();
        });
    } else {
        console.error('Request permission button not found');
    }
});