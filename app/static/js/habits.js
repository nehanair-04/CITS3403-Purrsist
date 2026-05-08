document.addEventListener("DOMContentLoaded", () => {
  const addModal = document.getElementById("add-habit-modal");
  const dupModal = document.getElementById("duplicate-modal");
  const editModal = document.getElementById("edit-habit-modal");
  const deleteModal = document.getElementById("delete-habit-modal");

  const form = document.getElementById("add-habit-form");
  const habitList = document.getElementById("habit-list");

  const addHabitName = document.getElementById("add-habit-name");
  const habitValidationMessage = document.getElementById(
    "habit-validation-message"
  );

  const editName = document.getElementById("edit-name");
  const editFreq = document.getElementById("edit-frequency");
  const editCustomDays = document.getElementById("edit-custom-days");

  const addFreq = document.getElementById("add-frequency");
  const addCustomDays = document.getElementById("add-custom-days");

  if (!form) return;

  let pendingHabit = null;

  // ---------------- UTIL ----------------
  function showHabitError(message) {
    if (!habitValidationMessage) return;
    habitValidationMessage.textContent = message;
    habitValidationMessage.style.display = "block";
  }

  function clearHabitError() {
    if (!habitValidationMessage) return;
    habitValidationMessage.textContent = "";
    habitValidationMessage.style.display = "none";
  }

  function closeAllModals() {
    document
      .querySelectorAll(".modal-overlay")
      .forEach((m) => m.classList.remove("active"));
  }

  function resetAddHabitForm() {
    const form = document.getElementById("add-habit-form");
    if (form) form.reset();

    clearHabitError();
    addCustomDays.style.display = "none";
    pendingHabit = null;
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

  // ---------------- CUSTOM DAYS ----------------
  addFreq.addEventListener("change", () => {
    addCustomDays.style.display = addFreq.value === "custom" ? "block" : "none";
  });

  editFreq.addEventListener("change", () => {
    editCustomDays.style.display =
      editFreq.value === "custom" ? "block" : "none";
  });

  // ---------------- INIT TAGS ----------------
  document.querySelectorAll(".habit-tag").forEach((tag) => {
    applyTag(tag, tag.textContent.trim().toLowerCase());
  });

  // ---------------- OPEN ADD MODAL ----------------
  document.getElementById("add-habit-btn").onclick = () => {
    closeAllModals();
    resetAddHabitForm();
    addModal.classList.add("active");
  };

  document.getElementById("close-add-modal").onclick = () => {
    addModal.classList.remove("active");
    resetAddHabitForm();
  };

  // ---------------- CREATE HABIT ----------------
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearHabitError();

    const fd = new FormData(form);
    const name = normalize(fd.get("name") || "");
    const frequency = normalize(fd.get("frequency") || "");
    const customDays = (fd.get("custom_days") || "").trim();

    if (!name) {
      showHabitError("Please enter a valid habit name.");
      addHabitName.focus();
      return;
    }

    if (!frequency) {
      showHabitError("Please select a frequency.");
      return;
    }

    if (frequency === "custom" && (!customDays || Number(customDays) < 1)) {
      showHabitError("Please enter a valid number of days.");
      addCustomDays.focus();
      return;
    }

    fd.set("name", name);
    fd.set("frequency", frequency);

    pendingHabit = { name, frequency };

    const res = await fetch("/habits/create", { method: "POST", body: fd });
    const data = await res.json();

    if (data.success) {
      const displayFrequency =
        data.frequency === "custom"
          ? `${data.frequency_days} day${data.frequency_days > 1 ? "s" : ""}`
          : data.frequency;
      addHabit(data.name, displayFrequency);
      closeAllModals();
      resetAddHabitForm();
      return;
    }

    if (data.duplicate) {
      document.getElementById(
        "dup-message"
      ).textContent = `"${name}" already exists. Edit it instead?`;

      closeAllModals();
      dupModal.classList.add("active");
      return;
    }
    showHabitError(data.message || "Could not create habit. Please try again.");
  });

  // ---------------- DUPLICATE MODAL ----------------
  document.getElementById("go-edit").onclick = () => {
    if (!pendingHabit) return;

    closeAllModals();

    editName.value = pendingHabit.name;
    editFreq.value = pendingHabit.frequency;
    editFreq.dispatchEvent(new Event("change"));

    editModal.classList.add("active");
  };

  document.getElementById("cancel-dup").onclick = () => {
    dupModal.classList.remove("active");
    resetAddHabitForm();
    closeAllModals();
  };

  // ---------------- EDIT SAVE ----------------
  document.getElementById("save-edit").onclick = async () => {
    const name = normalize(editName.value);
    const frequency = normalize(editFreq.value);
    const customDays = editCustomDays.value;

    const res = await fetch("/habits/update", {
      method: "POST",
      body: new URLSearchParams({
        name,
        frequency,
        custom_days: customDays,
      }),
    });

    const data = await res.json();

    const displayFreq =
      data.frequency === "custom"
        ? `${data.frequency_days} day${data.frequency_days > 1 ? "s" : ""}`
        : data.frequency;

    updateHabit(name, displayFreq);
    closeAllModals();
  };

  document.getElementById("cancel-edit").onclick = () => closeAllModals();

  // ---------------- DELETE ----------------
  document.getElementById("delete-habit").onclick = () => {
    closeAllModals();
    deleteModal.classList.add("active");
  };

  document.getElementById("cancel-delete").onclick = () => {
    deleteModal.classList.remove("active");
    editModal.classList.add("active");
  };

  document.getElementById("confirm-delete").onclick = async () => {
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

  // ---------------- ADD HABIT UI ----------------
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
