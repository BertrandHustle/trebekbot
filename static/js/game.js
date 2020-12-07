var timeLimit = 60;
var currentTime = timeLimit;
var currentWager = 0;
var dailyDoubleAsker;
var questionIsLive;
var categorizedQuestions;
var liveQuestion;
var correctAnswer;

$(document).ready( function() {
        var correctAnswer;
        $("#getQuestion").click(function () {
            // remove answer from previous question
            $('#answer').text('')
            liveQuestion = JSON.parse(document.getElementById('question_json').textContent);
            $('#questionText').text(liveQuestion['text']);
            if (liveQuestion['valid_links']) {
                $('#validLinks').text(liveQuestion['valid_links']);
            }
            $('#questionValue').text(liveQuestion['value']);
            $('#questionCategory').append(liveQuestion['category']);
            $('#questionDate').append(liveQuestion['date']);
            $('#debug').append(liveQuestion['answer']);
            //set answer to make available to tickTimer
            correctAnswer = liveQuestion['answer'];
            setInterval(tickTimer, 1000);
        });

        $("#submitButton").click(function () {
            const givenAnswer = $('form').serializeArray()[1].value;
            $.ajax({
                headers: { "X-CSRFToken": Cookies.get('csrftoken') },
                type: "POST",
                url: "/judge_answer/",
                // TODO: this needs to pass correctAnswer as well
                data: {givenAnswer: givenAnswer, correctAnswer: correctAnswer},
                dataType: 'JSON',
                error: function(jqXHR, textStatus, errorThrown) {
                    alert(jqXHR.status + errorThrown);
                },
                success:  function(data){
                       alert(data.result);
                       $('.answerResult').text(data.result);
                }
            })
        });

        function tickTimer() {
            $('.questionTimer').html(currentTime).show();
            currentTime--;
            if (currentTime <= 0) {
                clearInterval();
                $('.questionTimer').text("Time Up!");
                // set answer to make available to tickTimer
                correctAnswer = liveQuestion['answer'];
                $('#answerResult').text('Answer: ' + correctAnswer);
                $('.question').text('')
            }
        }
});