var timeLimit = 60;
var currentTime = 0;
var currentWager = 0;
var dailyDoubleAsker;
var categorizedQuestions;
var liveQuestion = null;
var correctAnswer;
var buzzedInPlayer;

$(document).ready( function() {

        const answerSocket = new WebSocket(
            'ws://'
            + window.location.host
            + '/ws/game/answer'
            + '/'
        );

        const timerSocket = new WebSocket(
            'ws://'
            + window.location.host
            + '/ws/game/timer'
            + '/'
        )

        const buzzerSocket = new WebSocket(
            'ws://'
            + window.location.host
            + '/ws/game/buzzer'
            + '/'
        )

        const questionSocket = new WebSocket(
            'ws://'
            + window.location.host
            + '/ws/game/question'
            + '/'
        )

        // used to reset relevant vars after question is completed, either by correct answer or timer
        function terminateQuestion() {
            var liveQuestion = null;
            timerSocket.send('kill_timer');
            buzzerSocket.send('reset_buzzer');
            clearInterval(timerInterval);
            currentTime = 0;
        }

        answerSocket.onmessage = function(e) {
            const data = JSON.parse(e.data);
            if (data.type === 'answer_result') {
                alert(data.response);
                $('#answerResult').text(data.response);
                // TODO: make sure player score under ACTIVE PLAYERS is updated as well
                $('#playerScore').text('Score: ' + data.player_score);
                // clear timer and reset buzzer if answer is correct
                if (data.correct === true) {
                    terminateQuestion();
                    $('.questionTimer').text('Correct!');
                }
                else if (data.correct === 'close') {
                    buzzerSocket.send('reset_buzzer');
                }
                else if (data.correct === false) {
                    buzzerSocket.send('reset_buzzer')
                }
            }
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
        }

        timerSocket.onmessage = function(e) {
            if (e.data === 'Timer Started!'){
                currentTime = timeLimit;
                timerInterval = setInterval(tickTimer, 1000);
            }
            else if (e.data === 'Timer Up!'){
                buzzerSocket.send('reset_buzzer');
            }
        }

        function tickTimer() {
            $('.questionTimer').html(currentTime).show();
            if (currentTime > 0) {
                currentTime--;
            }
            else {
                clearInterval(timerInterval);
                alert('Time Up!')
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
                questionSocket.send('get_question')
                questionSocket.onmessage = function(e) {
                    liveQuestion = JSON.parse(e.data);
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
                    timerSocket.send('start_timer');
                }
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
            buzzerSocket.send('buzz_in')
            buzzerSocket.onmessage = function(e) {
                alert(e.data)
                if (e.data === 'buzzed_in'){
                    $('.dot').css({'background-color': 'red'});
                    buzzedInPlayer = $('buzzer').value.text;
                }
                else if (e.data === 'buzzer_locked'){
                    alert('Player already buzzed in!');
                }
            }
        });

        $("#answerButton").click(function () {
            const givenAnswer = $('form').serializeArray()[1].value;
            answerSocket.send(JSON.stringify({
                'givenAnswer': givenAnswer,
                'correctAnswer': correctAnswer,
                'questionValue': liveQuestion['value']
            }));
        });
});