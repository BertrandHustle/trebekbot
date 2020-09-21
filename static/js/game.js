var timer = 0;
var timeLimit = 60;
var currentWager = 0;
var dailyDoubleAsker;
var questionIsLive;
var categorizedQuestions;

$(document).ready( function() {

        $("#getQuestion").click(function (event) {
            const liveQuestion = JSON.parse(document.getElementById('question_json').textContent);
            alert(JSON.stringify(liveQuestion));
        });

        $("#getQuestion").click(function (event) {
            timer = setInterval(startQuestionTimer(), timeLimit);
            function startQuestionTimer() {
                var d = new Date();
                var t = d.toLocaleTimeString();
                $("#h1").append(t);
            }
        });
});

setInterval(function() {
    $('.Timer')
})