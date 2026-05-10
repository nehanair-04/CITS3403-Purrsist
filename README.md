# Purrsist!

## Description

Purrsist! is a habit tracking web application that motivates users to build positive habits through gamification. Users create and track daily habits (e.g., studying, exercising, reading), earning virtual cat companions as rewards for maintaining streaks and completing habits. The app encourages consistent habit-building through gamification. The more habits you complete, the more cats you unlock in your shelter. Users can view other users' profiles, compare streaks on the leaderboard, and add friends. This encourages accountability and friendly competition.

### How It Works

1. **Register** and create an account
2. **Add habits** with custom frequencies (daily, weekly, biweekly, monthly, or custom)
3. **Complete habits** on your dashboard each day
4. **Unlock cats** by reaching milestones (e.g., completing 3 habits unlocks Luna, a common cat)
5. **Visit your Cat Shelter** to view your collection and cat happiness
6. **Compare with others** on the leaderboard or view friends' profiles

### Design

The app uses a pixel art aesthetic with a soft pink and cream colour palette. Key pages include:

1. **Dashboard** — view and complete today's habits, track progress
2. **Habit Manager** — create, edit and delete habits with custom frequencies
3. **Cat Shelter** — view your unlocked cat collection, see overall cat happiness
4. **Leaderboard** — compare streaks with other users
5. **Friends** — add friends and view their profiles
6. **Profile** — view your stats, streak history and cat collection

## Group Members

| UWA ID   | Name       | GitHub Username |
| -------- | ---------- | --------------- |
| 24263541 | Neha Nair  | nehanair-04     |
| 24106351 | Yixuan Hu  | Yixuan-Hu       |
| 22757835 | Zhaokun Li | ChatBWS         |

## How to Launch

1. Clone the repository:

```bash
   git clone https://github.com/nehanair-04/CITS3403-Group-Project.git
   cd CITS3403-Group-Project
```

2. Create and activate a virtual environment:

```bash
   python -m venv .venv
   source .venv/bin/activate
```

3. Install dependencies:

```bash
   pip install -r requirements.txt
```

4. Set the secret key environment variable:

```bash
   export PURRSIST_SECRET_KEY='your-secret-key-here'
```

5. Set up the database:

```bash
   flask db upgrade
```

6. Seed the cat data:

```bash
   flask shell
   >>> from app.models import seed_cats
   >>> seed_cats()
   >>> exit()
```

7. Run the application:

```bash
   flask run
```

8. Open your browser and navigate to `http://127.0.0.1:5000`

## How to Run Tests

This project uses Python’s built-in unittest framework for both unit testing and Selenium testing.

1. Install test dependencies
   Make sure your virtual environment is activated, then install dependencies:

```bash
pip install -r requirements.txt
```

2. Run unit tests
   To run all unit tests:

```bash
python -m unittest tests.unittests -v
```

3. Run Selenium tests
   Selenium tests simulate real user interactions with the web application using a headless Chrome browser.
   Run them with:

```bash
python -m unittest tests.seleniumtests -v
```

This project also includes automate tests with GitHub workflows.
