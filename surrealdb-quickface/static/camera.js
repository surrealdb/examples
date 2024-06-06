let videoStream;

document.getElementById('toggleCamera').addEventListener('click', function() {
    let button = document.getElementById('toggleCamera');
    let videoContainer = document.getElementById('cameraFeedContainer');
    let capturePhotoButton = document.getElementById('capturePhoto');

    if (videoStream) {
        // Stop the camera
        let tracks = videoStream.getTracks();
        tracks.forEach(track => track.stop());
        videoStream = null;
        let videoElement = document.getElementById('cameraFeed');
        videoElement.srcObject = null;
        button.innerText = "Turn on Camera";
        button.classList.remove('camera-on');
        button.classList.add('camera-off');
        videoContainer.classList.remove('video-on');
        videoContainer.classList.add('video-off');
        cameraIcon.style.display = 'block';
        capturePhotoButton.disabled = true;
    } else {
        // Start the camera
        let constraints = { video: true, audio: false };
        navigator.mediaDevices.getUserMedia(constraints).then(function(stream) {
            videoStream = stream;
            let videoElement = document.getElementById('cameraFeed');
            videoElement.srcObject = stream;
            button.innerText = "Turn Camera Off";
            button.classList.remove('camera-off');
            button.classList.add('camera-on');
            videoContainer.classList.remove('video-off');
            videoContainer.classList.add('video-on');
            cameraIcon.style.display = 'none';
            capturePhotoButton.disabled = false;
        }).catch(function(error) {
            console.error('Error accessing media devices.', error);
        });
    }
});

let constraints = { video: true, audio: false };

navigator.mediaDevices.getUserMedia(constraints).then(function(stream) {
    videoStream = stream;
    let videoElement = document.getElementById('cameraFeed');
    videoElement.srcObject = stream;
    let button = document.getElementById('toggleCamera');
    button.innerText = "Turn Camera Off";
    button.classList.add('camera-on');
    let videoContainer = document.getElementById('cameraFeedContainer');
    videoContainer.classList.add('video-on');
    let capturePhotoButton = document.getElementById('capturePhoto');
    capturePhotoButton.disabled = false;
}).catch(function(error) {
    console.error('Error accessing media devices.', error);
    let capturePhotoButton = document.getElementById('capturePhoto');
    capturePhotoButton.disabled = true;
});

document.getElementById('capturePhoto').addEventListener('click', function() {
    let videoElement = document.getElementById('cameraFeed');
    let canvasElement = document.getElementById('photoCanvas');
    let context = canvasElement.getContext('2d');

    canvasElement.width = videoElement.videoWidth;
    canvasElement.height = videoElement.videoHeight;

    context.drawImage(videoElement, 0, 0, videoElement.videoWidth, videoElement.videoHeight);

    canvasElement.toBlob(function(blob) {
        if (!blob) {
            console.error('Failed to create Blob from canvas');
            return;
        }

        let formData = new FormData();
        formData.append('photo', blob, 'surrealdb-photo.jpg');

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok ' + response.statusText);
            }
            return response.json();
        })
        .then(data => {
            const nameElement = document.getElementById('name');
            const roleElement = document.getElementById('role');
            const departmentElement = document.getElementById('department');

            if (nameElement) nameElement.innerText = data.name || 'N/A';
            if (roleElement) roleElement.innerText = data.role || 'N/A';
            if (departmentElement) departmentElement.innerText = data.dep || 'N/A';
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }, 'image/jpeg');
});