console.log("Test");

var timer = 0;
var timeLimit = 60;
var currentWager = 0;
var dailyDoubleAsker;
var questionIsLive;
var categorizedQuestions;

$(document).ready( function() {
        $("#answer").click(function (event) {
            const liveQuestion = JSON.parse(document.getElementById('qj').textContent);
            alert(JSON.stringify(liveQuestion));
            //alert(liveQuestion);
        });
});