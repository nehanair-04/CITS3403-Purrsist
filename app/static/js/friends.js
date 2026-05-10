$(document).ready(function () {
  const $input = $("#friend-search-input");
  const $addButton = $("#add-friend-btn");
  const $message = $("#friend-message");
  const $resultsBox = $("#friend-search-results");
  const $friendsList = $("#friends-list");

  if (
    !$input.length ||
    !$addButton.length ||
    !$message.length ||
    !$resultsBox.length ||
    !$friendsList.length
  ) {
    return;
  }

  let selectedUser = null;

  function showMessage(text, isError = true) {
    $message
      .text(text)
      .css("display", "block")
      .css("color", isError ? "#c0392b" : "#5e4b43");
  }

  function clearMessage() {
    $message.text("").hide();
  }

  function clearResults() {
    $resultsBox.empty();
  }

  function renderResults(users) {
    clearResults();

    if (users.length === 0) {
      selectedUser = null;
      showMessage("User not found.");
      return;
    }

    users.forEach(function (user) {
      const $result = $("<button>")
        .attr("type", "button")
        .addClass("friend-search-result")
        .text(
          user.already_friend
            ? `${user.username} (already added)`
            : user.username
        );

      if (user.already_friend) {
        $result.prop("disabled", true);
      }

      $result.on("click", function () {
        selectedUser = user;
        $input.val(user.username);
        clearResults();
        clearMessage();

        if (user.already_friend) {
          showMessage("This user is already your friend.");
        }
      });

      $resultsBox.append($result);
    });
  }

  function searchUsers() {
    const query = $input.val().trim();

    selectedUser = null;
    clearMessage();

    if (!query) {
      clearResults();
      return;
    }

    $.ajax({
      url: "/friends/search",
      method: "GET",
      data: { q: query },
      success: function (users) {
        renderResults(users);
      },
      error: function () {
        showMessage("Could not search users. Please try again.");
      },
    });
  }

  function addFriend() {
    const query = $input.val().trim();

    if (!query) {
      showMessage("Please enter a username.");
      return;
    }

    function sendAddRequest(user) {
      $.ajax({
        url: "/friends/add",
        method: "POST",
        data: { friend_id: user.id },
        success: function (data) {
          if (!data.success) {
            showMessage(data.message || "Could not add friend.");
            return;
          }

          showMessage("Friend added.", false);
          $addButton.text("Added");

          const friend = data.friend;

          const $friendItem = $("<a>")
            .attr("href", `/profile/${friend.id}`)
            .addClass("friend-item");

          const $avatar = $("<div>").addClass("avatar");
          const $image = $("<img>")
            .attr(
              "src",
              `/static/${friend.profile_image || "images/default-profile.jpg"}`
            )
            .attr("alt", `${friend.username} profile picture`);

          const $name = $("<span>")
            .addClass("friend-name")
            .text(friend.username);

          $avatar.append($image);
          $friendItem.append($avatar, $name);
          $friendsList.append($friendItem);

          $input.val("");
          selectedUser = null;
          clearResults();

          setTimeout(function () {
            $addButton.html('<i class="bi bi-person-plus"></i> Add');
          }, 1200);
        },
        error: function (xhr) {
          const response = xhr.responseJSON;
          showMessage(
            response && response.message
              ? response.message
              : "Could not add friend."
          );
        },
      });
    }

    if (selectedUser) {
      sendAddRequest(selectedUser);
      return;
    }

    $.ajax({
      url: "/friends/search",
      method: "GET",
      data: { q: query },
      success: function (users) {
        if (users.length === 0) {
          showMessage("User not found.");
          return;
        }

        selectedUser = users[0];
        sendAddRequest(selectedUser);
      },
      error: function () {
        showMessage("Could not search users. Please try again.");
      },
    });
  }

  $input.on("input", searchUsers);
  $addButton.on("click", addFriend);
});