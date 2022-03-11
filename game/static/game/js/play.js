var timeLimit = 60;
var currentTime = 60;
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
        sendToStream('buzzer', 'reset_buzzer')
        // client-side resets
        $('.dot').css({'background-color': 'gray'});
        clearInterval(timerInterval);
        liveQuestion = null;
        currentTime = timeLimit;
    }

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


    // judge whether an answer is correct
    demultiplexerSocket.addEventListener('message', function(e) {
        let msg = JSON.parse(e.data).payload.message;
        let eventType = JSON.parse(e.data).payload.event;
        if (eventType === 'answer') {
            $('#answerResult').text(msg.response);
            // TODO: make sure player score under ACTIVE PLAYERS is updated as well
            $('#playerScore').text('Score: ' + msg.player_score);
            // clear timer and reset buzzer if answer is correct
            if (msg.correct === true) {
                terminateQuestion();
                $('.questionTimer').text('Correct!');
                $('.dot').css({'background-color': 'gray'});
            }
            else if (msg.correct === 'close' || msg.correct === false) {
                demultiplexerSocket.sendToStream('buzzer', 'reset_buzzer');
                currentTime = timeLimit;
                $('.dot').css({'background-color': 'gray'});
            }
        }
    })


    // receive a new question
    demultiplexerSocket.addEventListener('message', function(e) {
        let msg = JSON.parse(e.data).payload.message;
        let eventType = JSON.parse(e.data).payload.event;
        if (eventType === 'question') {
            liveQuestion = msg;
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
            timerInterval = setInterval(tickTimer, 1000);
        }
    })


    // buzzer
    demultiplexerSocket.addEventListener('message', function(e) {
        let msg = JSON.parse(e.data).payload.message;
        let eventType = JSON.parse(e.data).payload.event;
        if (eventType === 'buzzer'){
            if (msg === 'buzzed_in'){
                $('.dot').css({'background-color': 'red'});
                demultiplexerSocket.sendToStream('buzzer', 'buzzed_in_player:' + currentPlayer);
            }
            else if (msg === 'buzzer_locked'){
                alert('Player already buzzed in!');
            }
            else if (msg.startsWith('buzzed_in_player')){
                $('#buzzerPlayer').text(e.data.split(':')[1]);
            }
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

    $("#getQuestion").click(function () {
        if (typeof liveQuestion === 'undefined') {
            // remove answer from previous question
            $('#answer').text('')
            sendToStream('question', 'get_question')
        }
        else {
            alert('Question is still live!')
        }
    });

    $("#buzzer").click(function () {
        if (typeof liveQuestion === 'undefined') {
            alert('Question not active!')
            return;
        }
        sendToStream('buzzer', 'buzz_in')
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