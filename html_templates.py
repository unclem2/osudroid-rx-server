registration_form = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>Register</title>
  </head>
  <body>
    <h1>Register</h1>
    <form method="post" action="/api/register.php">
      <label for="username">Username:</label><br>
      <input type="text" id="username" name="username"><br>
      <label for="password">Password:</label><br>
      <input type="password" id="password" name="password"><br><br>
      <label for="email">Email:</label><br>
      <input type="text" id="email" name="email"><br>

      <input type="submit" value="Register">
    </form>
  </body>
</html>
"""

leaderboard_temp = """
{% extends "base.html" %}

{% block title %}Leaderboard{% endblock %}

{% block content %}
<header>
    <h1>Leaderboard</h1>
</header>
<main>
    <section id="leaderboard">
        <table>
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Player</th>
                    <th>PP</th>
                    <th>Plays</th>
                </tr>
            </thead>
            <tbody>
                {% for player in leaderboard %}
                    <tr>
                        <td>{{ player.rank }}</td>
                        <td><a href="">{{ player.username }}</a></td>
                        <td>{{ player.pp }}</td>
                        <td>{{ player.plays }}</td>
                    </tr>
                {% endfor %}
            </tbody>
        </table>
    </section>
</main>
{% endblock %}
"""

profile_temp = """
{% extends "base.html" %}

{% block title %}Player Profile{% endblock %}

{% block content %}
<h1>Profile of {{ player.name }}</h1>
<h2>Recent Scores</h2>
<table>
    <thead>
        <tr>
            <th>Map title</th>
            <th>Mods</th>
            <th>PP</th>
            <th>Accuracy</th>
            <th>Combo</th>
            <th>Misses</th>
            <th>Date</th>
        </tr>
    </thead>
    <tbody>
        {% for score in recent_scores %}
            <tr>
                <td>{{ score.map }}</td>
                <td>{{ score.mods }}</td>
                <td>{{ score.pp }}</td>
                <td>{{ score.acc }}</td>
                <td>{{ score.combo }}</td>
                <td>{{ score.hitmiss }}</td>
                <td>{{ score.date }}</td>
            </tr>
        {% endfor %}
    </tbody>
</table>
<h2>Top Scores</h2>
<table>
    <thead>
        <tr>
            <th>Map title</th>
            <th>Mods</th>
            <th>PP</th>
            <th>Accuracy</th>
            <th>Combo</th>
            <th>Misses</th>
            <th>Date</th>
        </tr>
    </thead>
    <tbody>
        {% for score in top_scores %}
            <tr>
                <td>{{ score.map }}</td>
                <td>{{ score.mods }}</td>
                <td>{{ score.pp }}</td>
                <td>{{ score.acc }}</td>
                <td>{{ score.combo }}</td>
                <td>{{ score.hitmiss }}</td>
                <td>{{ score.date }}</td>
            </tr>
        {% endfor %}
    </tbody>
</table>
{% endblock %}
"""

set_avatar_temp = """
{% extends "base.html" %}

{% block title %}Set Avatar{% endblock %}

{% block content %}
<h1>Set Avatar</h1>
<form method="post" enctype="multipart/form-data">
    <input type="file" name="avatar" required>
    <input type="submit" value="Upload">
</form>
{% endblock %}
"""

web_login_temp = """
{% extends "base.html" %}

{% block head %}
    <title>Login</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            background-color: #f0f0f0;
        }
        .container {
            background-color: #fff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            width: 300px;
        }
        h1 {
            text-align: center;
            margin-bottom: 20px;
        }
        form {
            display: flex;
            flex-direction: column;
        }
        input[type="text"], input[type="password"] {
            margin-bottom: 10px;
            padding: 8px;
            border: 1px solid #ccc;
            border-radius: 4px;
        }
        input[type="submit"] {
            padding: 10px;
            border: none;
            border-radius: 4px;
            background-color: #007BFF;
            color: #fff;
            cursor: pointer;
        }
        input[type="submit"]:hover {
            background-color: #0056b3;
        }
        .error {
            color: red;
            text-align: center;
            margin-bottom: 10px;
        }
    </style>
{% endblock %}

{% block content %}
    <div class="container">
        <h1>Login</h1>
        {% if error_message %}
            <div class="error">
                <p>{{ error_message }}</p>
            </div>
        {% endif %}
        <form method="post">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <input type="submit" value="Login">
        </form>
    </div>
{% endblock %}
"""

main_page = """
{% extends "base.html" %}

{% block title %}
    {{ title }}
{% endblock %}

{% block content %}
    <h1>{{ title }}</h1>
    <p>Number of players: {{ players }}</p>
    <p>Number of online players: {{ online }}</p>
    <p>Client version: {{ version }}</p>
    <p>Link to client <a href="{{ client_link }}">here</a></p>
    <p>Changelog: {{ changelog }}</p>
{% endblock %}"""

error_template = """
{% extends "base.html" %}

{% block content %}
    {% if error_message %}
        <div class="error">
            <p>{{ error_message }}</p>
        </div>
    {% endif %}
{% endblock %}
"""