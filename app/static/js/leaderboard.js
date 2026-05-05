// Sample user data for the leaderboard
const users = [
  { name: "Alan", streak: 10, completedHabits: 25 },
  { name: "Bela", streak: 7, completedHabits: 30 },
  { name: "Chloe", streak: 10, completedHabits: 18 },
  { name: "Daniel", streak: 4, completedHabits: 40 },
];

// Sort users by streak first, then by completed habits
function sortLeaderboard(users) {
  return users.sort(function(a, b) {
    if (b.streak !== a.streak) {
      return b.streak - a.streak;
    }

    return b.completedHabits - a.completedHabits;
  });
}

// Display the sorted leaderboard on the page
function updateLeaderboard() {
  const leaderboardList = document.getElementById("leaderboard-list");
  const sortedUsers = sortLeaderboard(users);

  leaderboardList.innerHTML = "";

  sortedUsers.forEach(function(user, index) {
    const entry = document.createElement("div");
    entry.classList.add("leaderboard-entry");

    if (index === 0) {
      entry.classList.add("first-place");
    } else if (index === 1) {
      entry.classList.add("second-place");
    } else if (index === 2) {
      entry.classList.add("third-place");
    }

    entry.innerHTML = `
      <span class="friend-name">#${index + 1} ${user.name}</span>
      <span class="friend-streak">${user.streak} days | ${user.completedHabits} habits</span>
    `;

    leaderboardList.appendChild(entry);
  });
}

document.addEventListener("DOMContentLoaded", updateLeaderboard);