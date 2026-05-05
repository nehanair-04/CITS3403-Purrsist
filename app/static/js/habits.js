function completeHabit(event, habitId) {
  const url = COMPLETE_HABIT_URL.replace("0", habitId);

  fetch(url, {
    method: "POST",
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        const btn = event.target;

        // update button
        btn.textContent = "Done";
        btn.disabled = true;

        // update UI
        updateProgress();

        // reward check
        if (
          getRemainingHabits() === 0 &&
          typeof showRewardPopup === "function"
        ) {
          showRewardPopup("All habits complete! 🐱");
        }
      }
    })
    .catch((err) => console.error(err));
}

function updateProgress() {
  const total = document.querySelectorAll(".complete-btn").length;
  const done = document.querySelectorAll(".complete-btn:disabled").length;

  const percent = total === 0 ? 0 : Math.floor((done / total) * 100);

  document.getElementById("progress-text").textContent = percent;

  document.getElementById("progress-bar").style.width = `${percent}%`;

  const remaining = 3 - done;
  const rewardText = document.getElementById("reward-counter");

  if (remaining > 0) {
    rewardText.textContent = `${remaining} to next reward`;
  } else {
    rewardText.textContent = "Reward unlocked!";
  }
}

function getRemainingHabits() {
  const total = document.querySelectorAll(".complete-btn").length;
  const done = document.querySelectorAll(".complete-btn:disabled").length;

  return total - done;
}

window.addEventListener("DOMContentLoaded", () => {
  const bar = document.getElementById("progress-bar");
  const initial = bar.dataset.progress;

  bar.style.width = `${initial}%`;
});
