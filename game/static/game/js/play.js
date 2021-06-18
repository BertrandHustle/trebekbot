var timeLimit = 60;
var currentTime = 0;
var currentWager = 0;
var dailyDoubleAsker;
var categorizedQuestions;
var liveQuestion;
var correctAnswer;

$(document).ready( function() {

        const gameSocket = new WebSocket(
            'ws://'
            + window.location.host
            + '/ws/game/play'
            + '/'
        );

        gameSocket.onmessage = function(e) {
            const data = JSON.parse(e.data);
        }

        var correctAnswer;
        $("#getQuestion").click(function () {
            if (currentTime <= 0) {
                // remove answer from previous question
                $('#answer').text('')
                $.ajax({
                    headers: { "X-CSRFToken": Cookies.get('csrftoken') },
                    type: "GET",
                    url: "new_question",
                    dataType: 'JSON',
                    error: function(jqXHR, textStatus, errorThrown) {
                        alert(jqXHR.status + errorThrown);
                    },
                    success: function(data){
                        liveQuestion = data;
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
            }
            else {
                alert('Question is still live!')
            }
        });

        $("#submitButton").click(function () {
            const givenAnswer = $('form').serializeArray()[1].value;
            gameSocket.send(JSON.stringify({
                'givenAnswer': givenAnswer,
                'correctAnswer': correctAnswer,
                'questionValue': liveQuestion['value']
            }));
            alert(data.result);
        });

//                       alert(data.text);
//                       $('#answerResult').text(data.text);
//                       $('#playerScore').text('Score: ' + data.player_score);
//                       // clear timer if answer is correct
//                       if (data.result === true) {
//                            clearInterval(timerInterval);
//                            $('.questionTimer').text('Correct!');
//                            currentTime = 0;


        //TODO: fix 'question is still live' issue
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