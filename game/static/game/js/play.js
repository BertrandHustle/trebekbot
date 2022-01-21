var timeLimit = 60;
var currentTime = 0;
var currentWager = 0;
var dailyDoubleAsker;
var categorizedQuestions;
var correctAnswer;
var liveQuestion;

$(document).ready( function() {

    const roomName = document.getElementById('roomName').textContent.split(':')[1].trim();

    const demultiplexerSocket = new WebSocket(
        'ws://'
        + window.location.host
        + '/ws/game/demultiplexer/'
        + roomName
        + '/'
    );

    function sendToStream(streamName, payload) {
        demultiplexerSocket.send(JSON.stringify({
            'stream': streamName,
            'payload': payload
        }))
    }

    // used to reset relevant vars after question is completed, either by correct answer or timer
    function terminateQuestion() {
        // server-side resets
        sendToStream('question', 'reset_question')
        sendToStream('timer', 'kill_timer')
        sendToStream('buzzer', 'reset_buzzer')
        // client-side resets
        $('.dot').css({'background-color': 'gray'});
        clearInterval(timerInterval);
        liveQuestion = null;
        currentTime = 0;
    }

    // judge whether an answer is correct
    demultiplexerSocket.addEventListener('message', function(e) {
        const payload = JSON.parse(e.data);
        alert(data.response);
        $('#answerResult').text(data.response);
        // TODO: make sure player score under ACTIVE PLAYERS is updated as well
        $('#playerScore').text('Score: ' + data.player_score);
        // clear timer and reset buzzer if answer is correct
        if (data.correct === true) {
            terminateQuestion();
            $('.questionTimer').text('Correct!');
            $('.dot').css({'background-color': 'gray'});
        }
        else if (data.correct === 'close') {
            buzzerSocket.send('reset_buzzer');
        }
        else if (data.correct === false) {
            buzzerSocket.send('reset_buzzer')
        }
    })

    // timer
    demultiplexerSocket.addEventListener('message', function(e) {
            const payload = JSON.parse(e.data);
            if (payload.message === 'Timer Started!'){
            currentTime = timeLimit;
            timerInterval = setInterval(tickTimer, 1000);
        }
            else if (payload.message === 'Timer Up!'){
                buzzerSocket.send('reset_buzzer');
        }
    })

    // receive a new question
    demultiplexerSocket.addEventListener('message', function(e) {
        const payload = JSON.parse(e.data);
        alert(payload);
        liveQuestion = payload.question;
        $('#questionText').text(liveQuestion['text']);
        if (liveQuestion['valid_links']) {
            $('#validLinks').text(liveQuestion['valid_links']);
        }
        $('#questionValue').text(liveQuestion['value']);
        $('#questionCategory').text(liveQuestion['category']);
        $('#questionDate').text(liveQuestion['date']);
        // set answer to make available to tickTimer
        correctAnswer = liveQuestion['answer'];
        // set and start timer
        currentTime = timeLimit;
        sendToStream('timer', 'start_timer');
    })


    // buzzer
    demultiplexerSocket.addEventListener('message', function(e) {
        const payload = JSON.parse(e.data);
        alert(e.data);
        if (payload.message === 'buzzed_in'){
            $('.dot').css({'background-color': 'red'});
            buzzerSocket.send('buzzed_in_player:' + currentPlayer);
        }
        else if (payload.message === 'buzzer_locked'){
            alert('Player already buzzed in!');
        }
        else if (payload.message.startsWith('buzzed_in_player')){
            $('#buzzerPlayer').text(e.data.split(':')[1]);
        }
    })


//            // TODO: Make new websocket for this
//            else if (data.type === 'player_login') {
//                newPlayer = data['player'];
//                $.ajax({
//                    headers: { "X-CSRFToken": Cookies.get('csrftoken') },
//                    error: function(jqXHR, textStatus, errorThrown) {
//                        alert(jqXHR.status + errorThrown);
//                    },
//                    success: function(data){
//                        $('#players').append(newPlayer['text']);
//                    }
//                })
//            }


    function tickTimer() {
        $('.questionTimer').html(currentTime).show();
        if (currentTime > 0) {
            currentTime--;
        }
        else {
            clearInterval(timerInterval);
            alert('Time Up!')
            $('.dot').css({'background-color': 'gray'});
            $('.questionTimer').text('Ready');
            // set answer to make available to tickTimer
            correctAnswer = liveQuestion['answer'];
            $('#answerResult').text('Answer: ' + correctAnswer);
            $('.question').text('')
        }
    }

    $("#getQuestion").click(function () {
        if (currentTime <= 0) {
            // remove answer from previous question
            $('#answer').text('')
            sendToStream('question', 'get_question')
        }
        else {
            alert('Question is still live!')
        }
    });

    $("#buzzer").click(function () {
        if (liveQuestion == null) {
            alert('Question not active!')
            return;
        }
        sendToStream('buzzer', {'text': 'buzz_in'})
    });

    $("#answerButton").click(function () {
        const givenAnswer = $('form').serializeArray()[1].value;
        sendToStream('answer', JSON.stringify({
            'givenAnswer': givenAnswer,
            'correctAnswer': correctAnswer,
            'questionValue': liveQuestion['value']
        }));
    });
});