var timeLimit = 60;
var currentTime = timeLimit;
var timerActive = false;
var currentWager = 0;
var dailyDoubleAsker;
var categorizedQuestions;
var correctAnswer;
var liveQuestion;
var timerInterval;

$(document).ready( function() {

    const roomName = document.getElementById('roomName').textContent.split(':')[1].trim();
    const playerName = document.getElementById('playerName').textContent.split(':')[1].trim();

    const buzzerSocket = new WebSocket(
        'ws://'
        + window.location.host
        + '/ws/game/buzzer/'
        + roomName
        + '/'
    );

    const answerSocket = new WebSocket(
        'ws://'
        + window.location.host
        + '/ws/game/answer/'
        + roomName
        + '/'
    );

    const questionSocket = new WebSocket(
        'ws://'
        + window.location.host
        + '/ws/game/question/'
        + roomName
        + '/'
    );

    function sendStringAsJson(websocket, message) {
        websocket.send(JSON.stringify({'content': message}));
    }

    // used to reset relevant vars after question is completed, either by correct answer or timer
    function terminateQuestion() {
        // server-side resets
        sendStringAsJson(questionSocket, 'reset_question');
        sendStringAsJson(buzzerSocket, 'reset_buzzer');
        // client-side resets
        $('.dot').css({'background-color': 'gray'});
        clearInterval(timerInterval);
        timerInterval = null;
        timerActive = false;
        liveQuestion = null;
        currentTime = timeLimit;
    }

    function tickTimer() {
        $('.questionTimer').html(currentTime).show();
        if (currentTime > 0) {
            currentTime--;
        }
        else {
            terminateQuestion();
            alert('Time Up!');
            $('.dot').css({'background-color': 'gray'});
            $('.questionTimer').text('Ready');
            $('#answerResult').text('Answer: ' + correctAnswer);
            $('.question').text('');
        }
    }


    // judge whether an answer is correct
    answerSocket.addEventListener('message', function(e) {
        let payload = JSON.parse(e.data)
        let msg = payload.message
        let event = payload.event
        if (event === 'answer') {
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
                sendStringAsJson(buzzerSocket, 'reset_buzzer');
                currentTime = timeLimit;
                $('.dot').css({'background-color': 'gray'});
            }
        }
    })


    // receive a new question
    questionSocket.addEventListener('message', function(e) {
        let payload = JSON.parse(e.data)
        let msg = payload.message
        let event = payload.event
        if (event === 'question') {
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
            if (timerActive === false){
                timerInterval = setInterval(tickTimer, 1000);
                timerActive = true;
            }
        }
    })


    // buzzer
    buzzerSocket.addEventListener('message', function(e) {
        let payload = JSON.parse(e.data)
        let msg = payload.message
        let event = payload.event
        if (event === 'buzzer'){
            if (msg === 'buzzed_in'){
                $('.dot').css({'background-color': 'red'});
                sendStringAsJson(buzzerSocket, 'buzzed_in_player: ' + currentPlayer);
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
        if (liveQuestion == null) {
            // remove answer from previous question
            $('#answer').text('');
            sendStringAsJson(questionSocket, 'get_question');
        }
        else {
            alert('Question is still live!');
        }
    });

    $("#buzzer").click(function () {
        if (liveQuestion == null) {
            alert('Question not active!');
            return;
        }
        sendStringAsJson(buzzerSocket, 'buzz_in');
    });

    $("#answerButton").click(function () {
        let buzzed_in_player = sendStringAsJson(buzzerSocket, 'status');
        if (buzzed_in_player === playerName) {
            let givenAnswer = $('form').serializeArray()[1].value;
            answerSocket.send(JSON.stringify({
                'givenAnswer': givenAnswer,
                'correctAnswer': correctAnswer,
                'questionValue': liveQuestion['value']
            }));
        }
        else {
            alert('A player is already buzzed in!');
        }
    });
});