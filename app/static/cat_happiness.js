// Decide cat happiness based on user's streak and activity
function getCatHappiness(streak, completedToday) {
  if (completedToday && streak >= 7) {
    return "happy";
  }

  if (completedToday || streak >= 3) {
    return "neutral";
  }

  return "sad";
}

// Update each cat card with the correct happiness status
function updateCatHappiness() {
  const catSlots = document.querySelectorAll(".cat-slot:not(.empty)");

  catSlots.forEach(function(cat) {
    const streak = Number(cat.dataset.streak);

    const completedTodayText = cat.dataset.completedToday;
    const completedToday = completedTodayText === "true";

    const happiness = getCatHappiness(streak, completedToday);
    const happinessText = cat.querySelector(".happiness-text");

    if (happinessText) {
      happinessText.textContent = `Happiness: ${happiness}`;
    }

    cat.classList.remove("happy", "neutral", "sad");
    cat.classList.add(happiness);
  });
}

document.addEventListener("DOMContentLoaded", updateCatHappiness);