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
        //alert(payload.response);
        $('#answerResult').text(payload.response);
        // TODO: make sure player score under ACTIVE PLAYERS is updated as well
        $('#playerScore').text('Score: ' + payload.player_score);
        // clear timer and reset buzzer if answer is correct
        if (payload.correct === true) {
            terminateQuestion();
            $('.questionTimer').text('Correct!');
            $('.dot').css({'background-color': 'gray'});
        }
        else if (payload.correct === 'close' || payload.correct === false) {
            demultiplexerSocket.sendToStream('buzzer', 'reset_buzzer');
        }
    })

    // timer
    demultiplexerSocket.addEventListener('message', function(e) {
        let payload = JSON.parse(e.data).payload;
        let stream = JSON.parse(e.data).stream;
        if (stream === 'timer') {
            if (payload.message === 'Timer Started!'){
                currentTime = timeLimit;
                //$('.questionTimer').html(currentTime).show();
            }
            else if (payload.message === 'tick'){
                currentTime--;
                $('.questionTimer').html(currentTime).show();
            }
            else if (payload.message === 'Timer Up!'){
                buzzerSocket.send('reset_buzzer');
                alert('Time Up!')
                $('.dot').css({'background-color': 'gray'});
                $('.questionTimer').text('Ready');
                // set answer to make available to tickTimer
                correctAnswer = liveQuestion['answer'];
                $('#answerResult').text('Answer: ' + correctAnswer);
                $('.question').text('')
            }
        }
    })


    // receive a new question
    demultiplexerSocket.addEventListener('message', function(e) {
        let payload = JSON.parse(e.data).payload;
        let stream = JSON.parse(e.data).stream;
        if (stream === 'question') {
            liveQuestion = payload;
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
        }
    })


    // buzzer
    demultiplexerSocket.addEventListener('message', function(e) {
        const payload = JSON.parse(e.data);
        //alert(payload);
        if (payload.stream === 'buzzer'){
            if (payload === 'buzzed_in'){
                $('.dot').css({'background-color': 'red'});
                demultiplexerSocket.sendToStream('buzzer', 'buzzed_in_player:' + currentPlayer);
            }
            else if (payload === 'buzzer_locked'){
                alert('Player already buzzed in!');
            }
            else if (payload.startsWith('buzzed_in_player')){
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
        if (currentTime <= 0) {
            // remove answer from previous question
            $('#answer').text('')
            sendToStream('question', 'get_question')
            sendToStream('timer', 'start_timer')
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