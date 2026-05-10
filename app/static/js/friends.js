document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("friend-search-input");
  const addButton = document.getElementById("add-friend-btn");
  const message = document.getElementById("friend-message");
  const resultsBox = document.getElementById("friend-search-results");
  const friendsList = document.getElementById("friends-list");

  if (!input || !addButton || !message || !resultsBox || !friendsList) return;

  let selectedUser = null;

  function showMessage(text, isError = true) {
    message.textContent = text;
    message.style.display = "block";
    message.style.color = isError ? "#c0392b" : "#5e4b43";
  }

  function clearMessage() {
    message.textContent = "";
    message.style.display = "none";
  }

  function clearResults() {
    resultsBox.innerHTML = "";
  }

  function renderResults(users) {
    clearResults();

    if (users.length === 0) {
      selectedUser = null;
      showMessage("User not found.");
      return;
    }

    users.forEach((user) => {
      const result = document.createElement("button");
      result.type = "button";
      result.className = "friend-search-result";
      result.textContent = user.already_friend
        ? `${user.username} (already added)`
        : user.username;

      result.disabled = user.already_friend;

      result.addEventListener("click", () => {
        selectedUser = user;
        input.value = user.username;
        clearResults();
        clearMessage();

        if (user.already_friend) {
          showMessage("This user is already your friend.");
        }
      });

      resultsBox.appendChild(result);
    });
  }

  async function searchUsers() {
    const query = input.value.trim();

    selectedUser = null;
    clearMessage();

    if (!query) {
      clearResults();
      return;
    }

    const res = await fetch(`/friends/search?q=${encodeURIComponent(query)}`);
    const users = await res.json();

    renderResults(users);
  }

  async function addFriend() {
    const query = input.value.trim();

    if (!query) {
      showMessage("Please enter a username.");
      return;
    }

    if (!selectedUser) {
      const res = await fetch(`/friends/search?q=${encodeURIComponent(query)}`);
      const users = await res.json();

      if (users.length === 0) {
        showMessage("User not found.");
        return;
      }

      selectedUser = users[0];
    }

    const formData = new FormData();
    formData.append("friend_id", selectedUser.id);

    const res = await fetch("/friends/add", {
      method: "POST",
      body: formData,
    });

    const data = await res.json();

    if (!data.success) {
      showMessage(data.message || "Could not add friend.");
      return;
    }

    showMessage("Friend added.", false);
    addButton.textContent = "Added";

    const friend = data.friend;

    const friendItem = document.createElement("a");
    friendItem.href = `/profile/${friend.id}`;
    friendItem.className = "friend-item";

    friendItem.innerHTML = `
      <div class="avatar">
        <img
          src="/static/${friend.profile_image || "images/default-profile.jpg"}"
          alt="${friend.username} profile picture"
        />
      </div>
      <span class="friend-name">${friend.username}</span>
    `;

    friendsList.appendChild(friendItem);

    input.value = "";
    selectedUser = null;
    clearResults();

    setTimeout(() => {
      addButton.innerHTML = '<i class="bi bi-person-plus"></i> Add';
    }, 1200);
  }

  input.addEventListener("input", searchUsers);
  addButton.addEventListener("click", addFriend);
});