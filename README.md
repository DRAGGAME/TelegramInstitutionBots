<h1 align="center">TelegramInstitutionBots</h1>
<h2 align="center">Bot for receiving reviews and sending them to the DB</h2>
<h3>How to work with a bot?</h3>
<ol>
    <li>Install and configure postgresql, and also make a bot token via BotFather</li>
    <li>Login to the console</li>
    <li>First, go to the TelegramInstitutionBots folder</li>
    <li>Install docker</li>
    <li>Enter: <code>docker build -t yourname/'tgclient in console' .</code></li>
    <li>Once complete, enter: <code>docker run -e API_KEY='Your token' -e ip='Your server IP' -e DATABASE='Database name' -e PG_user='Database user' -e PG_password='Database user password' -d --restart=always --network=host --name tgclient 'Your user'/tgclient:latest</code></li>
</ol>
