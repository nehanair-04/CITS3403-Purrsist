function showRewardPopup(message) {
  const popup = document.getElementById("reward-modal");
  const text = document.getElementById("reward-text");

  text.textContent = message || "You unlocked a cat!";
  popup.classList.add("active");

  setTimeout(() => {
    closeRewardPopup();
  }, 4000);
}

function closeRewardPopup() {
  document.getElementById("reward-modal").classList.remove("active");
}
