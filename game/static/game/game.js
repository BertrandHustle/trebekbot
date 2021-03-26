var timeLimit = 60;
var currentTime = 0;
var currentWager = 0;
var dailyDoubleAsker;
var categorizedQuestions;
var liveQuestion;
var correctAnswer;

$(document).ready( function() {
        var correctAnswer;
        $("#getQuestion").click(function () {
            if (currentTime <= 0) {
                // remove answer from previous question
                $('#answer').text('')
                $.ajax({
                    headers: { "X-CSRFToken": Cookies.get('csrftoken') },
                    type: "GET",
                    url: "/new_question/",
                    dataType: 'JSON',
                    error: function(jqXHR, textStatus, errorThrown) {
                        alert(jqXHR.status + errorThrown);
                    },
                    success:  function(data){
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
                        setInterval(tickTimer, 1000);
                    }
                })
            }
            else {
                alert('Question is still live!')
            }
        });

        $("#submitButton").click(function () {
            const givenAnswer = $('form').serializeArray()[1].value;
            $.ajax({
                headers: { "X-CSRFToken": Cookies.get('csrftoken') },
                type: "POST",
                url: "/judge_answer/",
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