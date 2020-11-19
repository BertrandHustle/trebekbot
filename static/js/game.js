//import Cookies from '/static/js.cookie.min.js'

var timeLimit = 60;
var currentTime = timeLimit;
var currentWager = 0;
var dailyDoubleAsker;
var questionIsLive;
var categorizedQuestions;

$(document).ready( function() {
        var correctAnswer;
        $("#getQuestion").click(function () {
            const liveQuestion = JSON.parse(document.getElementById('question_json').textContent);
            $('.questionText').text(liveQuestion['text']);
            if (liveQuestion['valid_links']) {
                $('.validLinks').text(liveQuestion['valid_links']);
            }
            $('.questionValue').text(liveQuestion['value']);
            $('.questionCategory').append(liveQuestion['category']);
            $('.questionDate').append(liveQuestion['date']);
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
                data: {text: givenAnswer},
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
                $('.answer').text('Answer: ' + correctAnswer);
            }
        }
});