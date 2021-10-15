var timeLimit = 60;
var currentTime = 0;
var currentWager = 0;
var dailyDoubleAsker;
var categorizedQuestions;
var liveQuestion;
var correctAnswer;
var buzzerLocked = false;
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

        const questionSocket = new WebSocket(
            'ws://'
            + window.location.host
            + '/ws/game/question'
            + '/'
        )

        answerSocket.onmessage = function(e) {
            const data = JSON.parse(e.data);
            if (data.type === 'answer_result') {
                alert(data.response);
                $('#answerResult').text(data.response);
                $('#playerScore').text('Score: ' + data.player_score);
                // clear timer if answer is correct
                if (data.correct === true) {
                    timerSocket.send('kill timer');
                    clearInterval(timerInterval);
                    $('.questionTimer').text('Correct!');
                    currentTime = 0;
                }
            }
            else if (data.type === 'buzzer') {
                buzzedInPlayer = data.player
            }
            else if (data.type === 'player_login') {
                newPlayer = data['player'];
                $.ajax({
                    headers: { "X-CSRFToken": Cookies.get('csrftoken') },
                    error: function(jqXHR, textStatus, errorThrown) {
                        alert(jqXHR.status + errorThrown);
                    },
                    success: function(data){
                        $('#players').append(newPlayer['text']);
                    }
                })
            }
        }

        timerSocket.onmessage = function(e) {
            currentTime = 0;
            alert(e.data);
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
                    timerSocket.send('start timer');
                    timerInterval = setInterval(tickTimer, 1000);
                }
            }
            else {
                alert('Question is still live!')
            }
        });

        $("#buzzer").click(function () {
            buzzerLocked = true;
            gameSocket.send(JSON.stringify({
                'buzzer': ''
            }));
        });

        $("#submitButton").click(function () {
            const givenAnswer = $('form').serializeArray()[1].value;
            gameSocket.send(JSON.stringify({
                'givenAnswer': givenAnswer,
                'correctAnswer': correctAnswer,
                'questionValue': liveQuestion['value']
            }));
        });

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
});