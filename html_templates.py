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
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Leaderboard</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
    <style>
        table, th, td {
            border: 1px solid black;
            border-collapse: collapse;
        }
    </style>
</head>
<body>
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
                            <td>{{ player.username }}</td>
                            <td>{{ player.pp }}</td>
                            <td>{{ player.plays }}</td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        </section>
    </main>
    <script src="{{ url_for('static', filename='scripts.js') }}"></script>
</body>
</html>
"""

profile_temp = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Player Profile</title>
    <style>
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            border: 1px solid black;
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
        }
    </style>
</head>
<body>
    <h1>Profile of {{ player.name }}</h1>
    <h2>Recent Scores</h2>
    <table>
        <thead>
            <tr>
                <th>Map title</th>
                <th>Score</th>
                <th>PP</th>
                <th>Accuracy</th>
                <th>Combo</th>
                <th>Date</th>
            </tr>
        </thead>
        <tbody>
            {% for score in recent_scores %}
                <tr>
                    <td>{{ score.map }}</td>
                    <td>{{ score.score }}</td>
                    <td>{{ score.pp }}</td>
                    <td>{{ score.acc }}</td>
                    <td>{{ score.combo }}</td>
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
                <th>Score</th>
                <th>PP</th>
                <th>Accuracy</th>
                <th>Combo</th>
                <th>Date</th>
            </tr>
        </thead>
        <tbody>
            {% for score in top_scores %}
                <tr>
                    <td>{{ score.map }}</td>
                    <td>{{ score.score }}</td>
                    <td>{{ score.pp }}</td>
                    <td>{{ score.acc }}</td>
                    <td>{{ score.combo }}</td>
                    <td>{{ score.date }}</td>
                </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
"""