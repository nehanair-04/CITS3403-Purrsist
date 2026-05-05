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

document.addEventListener("DOMContentLoaded", () => {
  const addModal = document.getElementById("add-habit-modal");
  const dupModal = document.getElementById("duplicate-modal");
  const editModal = document.getElementById("edit-habit-modal");

  const form = document.getElementById("add-habit-form");
  const habitList = document.getElementById("habit-list");

  const editName = document.getElementById("edit-name");
  const editFreq = document.getElementById("edit-frequency");

  let pendingHabit = null;

  // ---------------- UTIL ----------------
  function closeAllModals() {
    document
      .querySelectorAll(".modal-overlay")
      .forEach((m) => m.classList.remove("active"));
  }

  function normalize(str) {
    return str.trim().toLowerCase();
  }

  function format(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
  }

  function stringToColor(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }
    return `hsl(${Math.abs(hash % 360)}, 70%, 45%)`;
  }

  function applyTag(tagEl, frequency) {
    tagEl.textContent = frequency.toUpperCase();
    tagEl.style.backgroundColor = stringToColor(frequency);
  }

  // ---------------- INIT TAGS ----------------
  document.querySelectorAll(".habit-tag").forEach((tag) => {
    applyTag(tag, tag.textContent.trim().toLowerCase());
  });

  // ---------------- EVENT DELEGATION (IMPORTANT FIX) ----------------
  document.addEventListener("click", (e) => {
    if (e.target.classList.contains("edit-btn")) {
      const card = e.target.closest(".habit-card");

      const name = card.querySelector(".habit-name").textContent.trim();
      const freq = card.querySelector(".habit-tag").textContent.trim();

      editName.value = name.toLowerCase();
      editFreq.value = freq.toLowerCase();

      pendingHabit = { name, frequency: freq.toLowerCase(), card };

      closeAllModals();
      editModal.classList.add("active");
    }
  });

  // ---------------- OPEN ADD ----------------
  document.getElementById("add-habit-btn").onclick = () => {
    closeAllModals();
    addModal.classList.add("active");
  };

  document.getElementById("close-add-modal").onclick = () => {
    addModal.classList.remove("active");
  };

  // ---------------- CREATE HABIT ----------------
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const fd = new FormData(form);

    const name = normalize(fd.get("name"));
    const frequency = normalize(fd.get("frequency"));

    fd.set("name", name);
    fd.set("frequency", frequency);

    pendingHabit = { name, frequency };

    const res = await fetch("/habits/create", {
      method: "POST",
      body: fd,
    });

    const data = await res.json();

    if (data.success) {
      addHabit(name, frequency);
      closeAllModals();
      form.reset();
      return;
    }

    if (data.duplicate) {
      document.getElementById(
        "dup-message"
      ).textContent = `"${name}" already exists. Edit it instead?`;

      closeAllModals();
      dupModal.classList.add("active");
    }
  });

  // ---------------- DUPLICATE + EDIT ----------------
  document.getElementById("go-edit").onclick = () => {
    if (!pendingHabit) return;

    closeAllModals();

    editName.value = pendingHabit.name;
    editFreq.value = pendingHabit.frequency;

    editModal.classList.add("active");
  };

  document.getElementById("cancel-dup").onclick = () => {
    dupModal.classList.remove("active");
    pendingHabit = null;
  };

  // ---------------- EDIT SAVE ----------------
  document.getElementById("save-edit").onclick = async () => {
    const name = normalize(editName.value);
    const frequency = normalize(editFreq.value);

    await fetch("/habits/update", {
      method: "POST",
      body: new URLSearchParams({ name, frequency }),
    });

    updateHabit(name, frequency);

    closeAllModals();
  };

  // ---------------- DELETE ----------------
  document.getElementById("delete-habit").onclick = async () => {
    const name = normalize(editName.value);

    await fetch("/habits/delete", {
      method: "POST",
      body: new URLSearchParams({ name }),
    });

    document.querySelectorAll(".habit-card").forEach((card) => {
      const n = card.querySelector(".habit-name").textContent.toLowerCase();
      if (n === name) card.remove();
    });

    closeAllModals();
  };

  // ---------------- ADD UI ----------------
  function addHabit(name, frequency) {
    const card = document.createElement("div");
    card.className = "habit-card";

    card.innerHTML = `
      <div class="habit-row">
        <span class="habit-name">${format(name)}</span>
        <span class="habit-tag"></span>
        <button class="edit-btn">EDIT</button>
      </div>
    `;

    applyTag(card.querySelector(".habit-tag"), frequency);
    habitList.appendChild(card);
  }

  // ---------------- UPDATE UI ----------------
  function updateHabit(name, frequency) {
    document.querySelectorAll(".habit-card").forEach((card) => {
      const n = card.querySelector(".habit-name").textContent.toLowerCase();

      if (n === name) {
        card.querySelector(".habit-name").textContent = format(name);
        applyTag(card.querySelector(".habit-tag"), frequency);
      }
    });
  }
});
