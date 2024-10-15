let recognition;
let isRecording = false;
let final_transcript = '';
let countdownInterval;
let mediaRecorder;
let audioChunks = [];
const countdownTime = 60; // Set the countdown time in seconds
const fillerWords = ['uh', 'oh', 'um', 'like', 'you know', 'so', 'actually', 'basically', 'literally', 'I mean', 'well', 'sort of', 'kind of'];

function startRecording() {
    if (!('webkitSpeechRecognition' in window) || !('MediaRecorder' in window)) {
        alert('Your browser does not support speech recognition or media recording. Please use Google Chrome.');
        return;
    }

    recognition = new webkitSpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onstart = function () {
        isRecording = true;
        const transcriptionElement = document.getElementById('transcription');
        if (transcriptionElement) {
            transcriptionElement.innerText = '';
        }
        startCountdown();

        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                mediaRecorder = new MediaRecorder(stream);
                mediaRecorder.start();

                mediaRecorder.ondataavailable = event => {
                    audioChunks.push(event.data);
                };

                mediaRecorder.onstop = () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    audioChunks = [];
                    evaluateAnswer(audioBlob);
                };
            })
            .catch(err => {
                console.error('Error accessing microphone:', err);
                alert('Error accessing microphone. Please check your browser permissions.');
            });
    };

    recognition.onresult = function (event) {
        let interim_transcript = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
                final_transcript += highlightFillerWords(event.results[i][0].transcript);
            } else {
                interim_transcript += highlightFillerWords(event.results[i][0].transcript);
            }
        }
        const transcriptionElement = document.getElementById('transcription');
        if (transcriptionElement) {
            transcriptionElement.innerHTML = final_transcript + interim_transcript;
        }
    };

    recognition.onerror = function (event) {
        console.error('Speech recognition error', event);
    };

    recognition.onend = function () {
        isRecording = false;
        stopCountdown();
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
        }
    };

    recognition.start();
}

function stopRecording() {
    if (isRecording) {
        recognition.stop();
    }
}

function startCountdown() {
    let remainingTime = countdownTime;
    const countdownElement = document.getElementById('countdown');
    if (countdownElement) {
        countdownElement.innerText = formatTime(remainingTime);
    }
    countdownInterval = setInterval(() => {
        remainingTime--;
        if (countdownElement) {
            countdownElement.innerText = formatTime(remainingTime);
        }
        if (remainingTime <= 0) {
            stopRecording();
        }
    }, 1000);
}

function stopCountdown() {
    clearInterval(countdownInterval);
}

function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds < 10 ? '0' : ''}${remainingSeconds}`;
}

function updateFillerWordCounts(fillerWordCounts) {
    for (const [word, count] of Object.entries(fillerWordCounts)) {
        const progressBar = document.getElementById(`filler-word-progress-${word}`);
        if (progressBar) {
            progressBar.value = count;
            progressBar.max = 10;  // Set a reasonable max value for the progress bar
        }
        const countElement = document.getElementById(`filler-word-count-${word}`);
        if (countElement) {
            countElement.innerText = count;
        }
    }
}

function evaluateAnswer(audioBlob) {
    const loader = document.getElementById('skeleton-loader');
    if (loader) {
        loader.style.display = 'block';
    }

    const candidateNameElement = document.getElementById('candidate_name');
    const jobRoleElement = document.getElementById('job_role');
    const companyNameElement = document.getElementById('company_name');
    const questionElement = document.getElementById('question');
    const audioElement = document.getElementById('audio');

    if (!candidateNameElement || !jobRoleElement || !companyNameElement || !questionElement || !audioElement) {
        console.error('One or more required elements are missing from the DOM.');
        if (loader) {
            loader.style.display = 'none';
        }
        return;
    }

    const candidate_name = candidateNameElement.value;
    const job_role = jobRoleElement.dataset.value;
    const company_name = companyNameElement.value;
    const question = questionElement.dataset.value;
    const audio_filename = audioElement.dataset.value;

    const formData = new FormData();
    formData.append('audio_file', audioBlob);

    fetch(`/interview/${encodeURIComponent(candidate_name)}/${encodeURIComponent(job_role)}/${encodeURIComponent(company_name)}/${encodeURIComponent(question)}/${encodeURIComponent(audio_filename)}`, {
        method: 'POST',
        body: formData
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            const transcriptionElement = document.getElementById('transcription');
            if (transcriptionElement) {
                transcriptionElement.innerText = data.transcription;
            }
            const scoreElement = document.getElementById('score');
            if (scoreElement) {
                scoreElement.innerText = `Score: ${data.score}/10 🏆`;
            }
            updateFillerWordCounts(data.filler_word_counts);
            const reviewElement = document.getElementById('review');
            if (reviewElement) {
                reviewElement.innerText = data.review;  // Display the review and advice
            }
            const perfectAnswerElement = document.getElementById('perfect-answer');
            if (perfectAnswerElement) {
                perfectAnswerElement.innerText = data.perfect_answer;  // Display the perfect answer
            }
            if (loader) {
                loader.style.display = 'none';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            if (loader) {
                loader.style.display = 'none';
            }
        });
}

function highlightFillerWords(text) {
    const words = text.split(' ');
    return words.map(word => {
        if (fillerWords.includes(word.toLowerCase())) {
            return `<span class="highlight">${word}</span>`;
        }
        return word;
    }).join(' ');
}

function initAudioPlayer() {
    const audio = document.getElementById('audio');
    const playButton = document.getElementById('play-button');
    const progressBar = document.getElementById('progress-bar');
    const loader = document.getElementById('skeleton-loader');

    if (playButton) {
        playButton.addEventListener('click', () => {
            if (audio.paused) {
                audio.play();
                playButton.innerHTML = '<i class="fas fa-pause"></i>';
            } else {
                audio.pause();
                playButton.innerHTML = '<i class="fas fa-play"></i>';
            }
        });
    }

    if (audio) {
        audio.addEventListener('timeupdate', () => {
            if (progressBar) {
                progressBar.value = (audio.currentTime / audio.duration) * 100;
            }
        });

        if (progressBar) {
            progressBar.addEventListener('input', () => {
                audio.currentTime = (progressBar.value / 100) * audio.duration;
            });
        }

        audio.addEventListener('error', (e) => {
            console.error('Error loading audio:', e);
            alert('Error loading audio. Please try again.');
        });

        audio.addEventListener('loadeddata', () => {
            console.log('Audio loaded successfully');
            if (loader) {
                loader.style.display = 'none';
            }
        });

        if (loader) {
            loader.style.display = 'block';
        }
    }
}

function revealHint() {
    const hintElement = document.getElementById('hint');
    if (hintElement) {
        hintElement.style.display = 'block';
    }
}

document.addEventListener('DOMContentLoaded', initAudioPlayer);