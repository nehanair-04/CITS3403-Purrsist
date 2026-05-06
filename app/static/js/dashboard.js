const COMPLETE_HABIT_URL = "/habits/0/complete";

function completeHabit(event, habitId) {
  const url = COMPLETE_HABIT_URL.replace("0", habitId);

  fetch(url, { method: "POST" })
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        const btn = event.target;
        btn.textContent = "Completed";
        btn.disabled = true;
        btn.classList.add("completed");
        updateProgress();

        if (data.new_cats && data.new_cats.length > 0) {
          data.new_cats.forEach((name) => {
            showCatPopup(name);
          });
        }
      }
    })
    .catch((err) => console.error(err));
}

function showCatPopup(catName) {
  const modal = document.getElementById("cat-unlock-modal");
  const message = document.getElementById("cat-unlock-message");
  message.textContent = `You unlocked ${catName}!`;
  modal.classList.add("active");
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("close-cat-modal").onclick = () => {
    document.getElementById("cat-unlock-modal").classList.remove("active");
  };
});
function updateProgress() {
  const total = document.querySelectorAll(".complete-btn").length;
  const done = document.querySelectorAll(".complete-btn:disabled").length;
  const percent = total === 0 ? 0 : Math.floor((done / total) * 100);

  document.getElementById("progress-text").textContent = percent;
  document.getElementById("progress-bar").style.width = `${percent}%`;

  document.getElementById(
    "reward-counter"
  ).textContent = `${done}/${total} habits done today`;
}

window.addEventListener("DOMContentLoaded", () => {
  const bar = document.getElementById("progress-bar");
  if (bar) {
    bar.style.width = `${bar.dataset.progress}%`;
  }
});

// check if day has changed and reload
const pageLoadDate = new Date().toDateString();

setInterval(() => {
  if (new Date().toDateString() !== pageLoadDate) {
    location.reload();
  }
}, 60000);
