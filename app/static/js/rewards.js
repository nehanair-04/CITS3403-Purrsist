function showRewardPopup(message) {
  const popup = document.getElementById("reward-modal");
  const text = document.getElementById("reward-text");

  text.textContent = message || "You unlocked a cat!";
  popup.classList.add("active");

  setTimeout(() => {
    closeRewardModal();
  }, 4000);
}

function closeRewardModal() {
  document.getElementById("reward-modal").classList.remove("active");
}
