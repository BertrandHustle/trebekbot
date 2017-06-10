# trebekbot
Practice project, a Python slack bot that hosts a game of Jeopardy! in your slack channel.

Installation instructions:

1. Clone repo:
$ git clone https://github.com/BertrandHustle/trebekbot.git

2. Create a new bot-user for your slack channel:
https://my.slack.com/services/new/bot
Take note of the API token you get after configuring your new bot. 

3. Set TREBEKBOT_API_TOKEN variable:

Linux:

3a) add the following to /etc/environment:
TREBEKBOT_API_TOKEN=<API token from step 2>

3b) $ source /etc/environment

Windows:

3a). right-click the start button or hit win+break

3b). select “Advanced system settings” → “Environment Variables”.

// Thank you to https://www.fullstackpython.com/blog/build-first-slack-bot-python.html for this script
4. Get your bot's ID:
$ python3 print_bot_id.py

5. Set TREBEKBOT_ID variable:
Use the same procedure as step 3, but set TREBEKBOT_ID=<output of question 4>

6. Set channel to your desired slack channel:
In main.py, change the following line: 
channel = '#yourchannel'

7. Run trebekbot!
$ python3 main.py
