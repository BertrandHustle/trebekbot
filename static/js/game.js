var timeLimit = 60;
var currentTime = timeLimit;
var currentWager = 0;
var dailyDoubleAsker;
var questionIsLive;
var categorizedQuestions;

$(document).ready( function() {

        $("#getQuestion").click(function () {
            const liveQuestion = JSON.parse(document.getElementById('question_json').textContent);
            alert(JSON.stringify(liveQuestion));
            setInterval(tickTimer, 1000);
        });

        function tickTimer() {
            $('.questionTimer').html(currentTime).show();
            currentTime--;
            if (currentTime <= 0) {
                clearInterval();
                $('.questionTimer').text("Time Up!");
            }
        }
});