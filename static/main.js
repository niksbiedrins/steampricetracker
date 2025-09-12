const trackGamesDiv = document.querySelector(".tracked_games");
const gameCards = trackGamesDiv.querySelectorAll(".game_card");

gameCards.forEach(card => {
    const cardButton = card.querySelector(".delete")

    cardButton.addEventListener("click", () => {
        const appID = card.dataset.appid
        const gamename = card.querySelector("strong").innerText
        const priceText = gameInfo.innerText;
        const priceMatch = priceText.match(/£\d+(\.\d+)?/);
        const price = priceMatch ? priceMatch[0] : null;
        const imageUrl = card.querySelector(".game_icon").src;

        fetch("/untrack", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({appid: appID, gamename: gamename, price: price, icon: imageUrl})
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                card.remove();
            } else {
                console.error("Failed to untrack game.");
            }
        })
        .catch(err => console.error(err));
    });
});